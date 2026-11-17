#!/usr/bin/env python3
"""Stop hook: run the Roadie review checklist only when this turn edited Roadie files.

The turn starts at the last genuine user message in the transcript. A turn
counts as a Roadie edit when, after that point:

- an Edit/Write/MultiEdit/NotebookEdit targeted a path inside a
  road-race-automation checkout, or
- a road-race-automation checkout the turn worked in (the session folder, or a
  folder a Bash command cd'd into) gained a HEAD reflog entry (commit, merge,
  checkout, reset) or a changed/untracked file modified since the turn began.

Work in other repos (gravel-race-automation, xc-ski-labs, ...) never fires it.
It blocks at most once per stop: when stop_hook_active is set, Claude is already
answering the checklist, so the hook lets it stop. A hook error blocks once with
the error rather than passing silently.
"""
import json
import os
import re
import shlex
import subprocess
import sys
from datetime import datetime

ROADIE_RE = re.compile(r"/road-race-automation(/|$)")
EDIT_TOOLS = {"Edit", "Write", "MultiEdit", "NotebookEdit"}
CD_RE = re.compile(r"(?:^|[;&|(\n])\s*cd\s+(\"[^\"]+\"|'[^']+'|[^\s;&|)]+)")
PATH_RE = re.compile(r"(?:~|/)[^\s'\";&|)]*/road-race-automation(?:/[^\s'\";&|)]*)?")

CHECKLIST = """Roadie review: this turn changed files in road-race-automation:
{files}

Answer every applicable check for those changes, citing file:line, and fix any failure before stopping.

Brand identity
1. gravel_god_rating anywhere? Roadie uses d['race']['fondo_rating'].
2. --gg- CSS prefix? Roadie uses --rl-.
3. Hardcoded hex? Source of truth is wordpress/brand_tokens.py.
4. Scoring dimensions hardcoded? config/dimensions.json only.
5. Code copied from gravel-race-automation that does not match its source exactly (the inline demand analyzer diverged on climbing/threshold formulas)?

Data integrity
6. Score or claim added without a citation? Run scripts/audit_fabricated_claims.py after profile batches.
7. Falsiness on values that can be 0? Use `is None or == ""`, never `not val`.
8. int(raw) instead of _parse_score()?
9. Cached data returned without copy.deepcopy()?

Security and HTML
10. innerHTML with data-derived values?
11. json.dumps inside <script> without _safe_json_for_script()?
12. SVG attributes using var()/color-mix()?
13. backdrop-filter without an @supports fallback and prefers-reduced-motion?

Pipeline
14. Generator edited but output not regenerated?
15. Tier/score logic touched without scripts/recalculate_tiers.py --dry-run?
16. Tests run (python3 -m pytest tests/)? New behaviour without a test?
17. Deploy or index change without scripts/preflight_quality.py?

Calibration: the demand-analyzer drift, 53 fabricated testimonials, and the heat keyword "temperature" matching Leadville cold warnings all passed happy-path review."""


def _ts(value):
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).timestamp()
    except (AttributeError, ValueError):
        return None


def _is_genuine_user(entry):
    if entry.get("type") != "user" or entry.get("isMeta") or entry.get("isCompactSummary"):
        return False
    content = (entry.get("message") or {}).get("content")
    if isinstance(content, str):
        return True
    if isinstance(content, list):
        return not any(isinstance(b, dict) and b.get("type") == "tool_result" for b in content)
    return False


def current_turn(entries):
    """Entries after the last genuine user message, and that message's time."""
    start = 0
    for i, entry in enumerate(entries):
        if _is_genuine_user(entry):
            start = i
    started_at = _ts(entries[start].get("timestamp", "")) if entries else None
    return entries[start + 1:], started_at


def _tool_uses(entries):
    for entry in entries:
        if entry.get("type") != "assistant":
            continue
        content = (entry.get("message") or {}).get("content")
        if not isinstance(content, list):
            continue
        for block in content:
            if isinstance(block, dict) and block.get("type") == "tool_use":
                yield entry, block.get("name"), block.get("input") or {}


def _bash_dirs(command, cwd):
    """Folders a Bash command may write in: its cwd, every cd target, and any
    road-race-automation path it names (git -C, redirects, script paths)."""
    folders = [cwd]
    for raw in CD_RE.findall(command or ""):
        target = os.path.expanduser(shlex.split(raw)[0] if raw[0] in "\"'" else raw)
        folders.append(target if os.path.isabs(target) else os.path.join(cwd or "", target))
    folders.extend(os.path.expanduser(p) for p in PATH_RE.findall(command or ""))
    return [f for f in folders if f]


def _roadie(path):
    return bool(path) and bool(ROADIE_RE.search(os.path.abspath(os.path.expanduser(path))))


def _git(root, *args):
    return subprocess.run(["git", "-C", root, *args], capture_output=True, text=True, timeout=20)


def _toplevel(path):
    probe = path
    while probe and not os.path.isdir(probe):
        parent = os.path.dirname(probe)
        if parent == probe:
            return None
        probe = parent
    out = _git(probe, "rev-parse", "--show-toplevel")
    return out.stdout.strip() if out.returncode == 0 else None


def git_changes(root, since):
    """Files changed in a checkout since `since`, plus a note for new HEAD moves."""
    since = int(since)  # reflog and mtimes compare at whole-second resolution
    changed = []
    reflog = _git(root, "reflog", "-n", "50", "--date=unix", "--format=%gd %gs")
    for line in reflog.stdout.splitlines():
        stamp = re.search(r"@\{(\d+)\}", line)
        if stamp and int(stamp.group(1)) >= since:
            changed.append(f"{root} (git: {line.split(' ', 1)[1] if ' ' in line else line})")
    status = _git(root, "status", "--porcelain", "-z", "--untracked-files=all")
    for record in status.stdout.split("\0"):
        if len(record) < 4:
            continue
        path = os.path.join(root, record[3:])
        try:
            if os.path.getmtime(path) >= since:
                changed.append(path)
        except OSError:
            # A deleted file has no mtime; its folder's mtime moves when it goes.
            folder = os.path.dirname(path)
            while not os.path.isdir(folder):
                folder = os.path.dirname(folder)
            if record[:2].strip() == "D" and os.path.getmtime(folder) >= since:
                changed.append(path)
    return changed


def roadie_changes(entries, session_cwd, since):
    files, roots = [], set()
    if _roadie(session_cwd):
        roots.add(session_cwd)
    for entry, name, args in _tool_uses(entries):
        if name in EDIT_TOOLS:
            path = args.get("file_path") or args.get("notebook_path")
            if _roadie(path):
                files.append(path)
        elif name == "Bash":
            for folder in _bash_dirs(args.get("command", ""), entry.get("cwd") or session_cwd):
                if _roadie(folder):
                    roots.add(folder)
    if since is not None:
        tops = {t for t in (_toplevel(r) for r in roots) if t and _roadie(t)}
        for top in sorted(tops):
            files.extend(git_changes(top, since))
    return list(dict.fromkeys(files))


def read_transcript(path):
    entries = []
    with open(path, encoding="utf-8") as handle:
        for line in handle:
            try:
                entries.append(json.loads(line))
            except ValueError:
                continue
    return entries


def main(payload):
    if payload.get("stop_hook_active"):
        return 0
    entries, since = current_turn(read_transcript(payload["transcript_path"]))
    files = roadie_changes(entries, payload.get("cwd"), since)
    if files:
        reason = CHECKLIST.format(files="\n".join(f"- {f}" for f in files[:40]))
        print(json.dumps({"decision": "block", "reason": reason}))
    return 0


if __name__ == "__main__":
    payload = {}
    try:
        payload = json.load(sys.stdin)
        sys.exit(main(payload))
    except Exception as exc:  # surface the failure once instead of passing silently
        if payload.get("stop_hook_active"):
            sys.exit(0)
        print(json.dumps({"decision": "block",
                          "reason": f"Roadie stop hook failed ({type(exc).__name__}: {exc}); "
                                    "review Roadie edits by hand and report the hook error."}))
        sys.exit(0)
