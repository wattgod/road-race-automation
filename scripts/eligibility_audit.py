#!/usr/bin/env python3
"""Resumable race-eligibility auditor — Perplexity sonar-pro backend.

Continues the R4 eligibility program (evidence-only): for every profile in
race-data/ WITHOUT a race.eligibility block, asks Perplexity whether the
event still runs, validates the answer, and writes the evidence block.

Anti-fabrication hard rules (the same ones the manual waves enforced):
- status ∈ {active, defunct, cancelled, unknown}; unknown beats a guess.
- The cited source URL must appear in Perplexity's own returned citations
  (search_results) — a URL the model merely *composed* is rejected and the
  race is recorded as unknown with a note.
- Anti-conflation guidance in the prompt (pro race vs mass ride, MTB vs
  road, same-name events elsewhere).
- Evidence-only: writes race.eligibility, touches nothing else.

Resumable by construction: each result is written to disk immediately;
re-running skips everything that already has a block.

Usage:
    python3 scripts/eligibility_audit.py --limit 3 --dry-run   # smoke test
    python3 scripts/eligibility_audit.py --limit 40            # one wave
    python3 scripts/eligibility_audit.py                       # full backlog
"""

from __future__ import annotations

import argparse
import concurrent.futures as cf
import json
import os
import re
import sys
import threading
import urllib.request
from datetime import date
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
RACE_DATA_DIR = PROJECT_ROOT / "race-data"
API_URL = "https://api.perplexity.ai/chat/completions"
MODEL = "sonar-pro"

PROMPT = """You are auditing a road-cycling race database for still-running events.

RACE: {name}
LOCATION: {location}
DATE ON FILE: {our_date}

Determine this event's CURRENT operating status. Rules:
1. status must be exactly one of: active, defunct, cancelled, unknown.
   active = an upcoming edition is announced/registration open, or a 2025-2026
   edition ran with no discontinuation signals. defunct = organizer ended it or
   no edition for 2+ years with no announcement. cancelled = the upcoming
   edition specifically cancelled but the organizer is alive. If evidence is
   thin or ambiguous, say unknown — unknown is ALWAYS better than a guess.
2. Do NOT conflate similarly-named events (pro race vs mass-participation
   ride, MTB vs road, running events, same-name events in other places).
   Verify the location and event type match before concluding.
3. source_url must be a page you actually found in your search results.
4. Note the last edition year you found evidence for, any rebrand, and any
   date conflicting with the date on file.

Answer with ONLY this JSON object, no other text:
{{"status": "...", "source_url": "https://...", "last_edition_evidence": "2026|2025|...|none", "notes": "one short sentence or empty", "confidence": "high|medium|low"}}"""

_print_lock = threading.Lock()


def log(msg: str) -> None:
    with _print_lock:
        print(msg, flush=True)


def load_env_key() -> str:
    key = os.environ.get("PERPLEXITY_API_KEY", "")
    if not key:
        env = PROJECT_ROOT / ".env"
        if env.exists():
            m = re.search(r"^PERPLEXITY_API_KEY=(\S+)$", env.read_text(), re.M)
            if m:
                key = m.group(1)
    if not key.startswith("pplx-"):
        raise SystemExit("No valid PERPLEXITY_API_KEY in env or .env")
    return key


def pending_profiles() -> list[Path]:
    out = []
    for p in sorted(RACE_DATA_DIR.glob("*.json")):
        if p.name == "_schema.json":
            continue
        try:
            race = json.loads(p.read_text()).get("race", {})
        except (OSError, json.JSONDecodeError):
            continue
        if not isinstance(race.get("eligibility"), dict):
            out.append(p)
    return out


def ask_perplexity(key: str, race: dict) -> tuple[dict | None, list[str], str]:
    """Returns (parsed_answer, citation_urls, error)."""
    v = race.get("vitals", {})
    prompt = PROMPT.format(
        name=race.get("display_name") or race.get("name", "?"),
        location=v.get("location", "?"),
        our_date=v.get("date_specific") or v.get("date", "?"),
    )
    body = json.dumps({
        "model": MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 300,
        "temperature": 0.1,
    }).encode()
    req = urllib.request.Request(
        API_URL, data=body,
        headers={"Authorization": f"Bearer {key}",
                 "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=90) as resp:
            data = json.loads(resp.read().decode())
    except Exception as e:  # noqa: BLE001
        return None, [], f"api-error: {e}"
    content = data["choices"][0]["message"]["content"]
    cites = [r.get("url", "") for r in data.get("search_results", [])]
    cites += [c for c in data.get("citations", []) if isinstance(c, str)]
    m = re.search(r"\{.*\}", content, re.S)
    if not m:
        return None, cites, f"unparseable: {content[:120]}"
    try:
        ans = json.loads(m.group(0))
    except json.JSONDecodeError:
        return None, cites, f"bad-json: {m.group(0)[:120]}"
    return ans, cites, ""


def _domain(url: str) -> str:
    m = re.match(r"https?://([^/]+)", url or "")
    return m.group(1).lower().removeprefix("www.") if m else ""


def validate(ans: dict, cites: list[str]) -> tuple[dict, str]:
    """Apply hard rules; returns (eligibility_block, downgrade_reason)."""
    status = str(ans.get("status", "")).lower()
    src = str(ans.get("source_url", ""))
    notes = str(ans.get("notes", ""))[:400]
    last = str(ans.get("last_edition_evidence", ""))
    conf = str(ans.get("confidence", ""))
    reason = ""

    if status not in ("active", "defunct", "cancelled", "unknown"):
        status, reason = "unknown", f"invalid status {status!r}"
    # source must be among the API's own citations (same domain is enough —
    # models often cite the homepage of a page the search returned).
    cite_domains = {_domain(c) for c in cites if c}
    if status != "unknown":
        if not src or _domain(src) not in cite_domains:
            reason = "source URL not among API citations — downgraded"
            status, src = "unknown", (cites[0] if cites else "")
    if status != "unknown" and conf == "low":
        reason = "low confidence — downgraded"
        status = "unknown"

    block = {"status": status, "verified": date.today().isoformat(),
             "source": src or (cites[0] if cites else "")}
    note_parts = [notes] if notes else []
    if last and last not in ("none", ""):
        note_parts.append(f"last edition evidenced: {last}")
    if reason:
        note_parts.append(f"[auditor: {reason}]")
    note_parts.append("via sonar-pro eligibility_audit")
    block["notes"] = "; ".join(note_parts)
    return block, reason


def process(path: Path, key: str, dry: bool) -> str:
    d = json.loads(path.read_text())
    race = d["race"]
    ans, cites, err = ask_perplexity(key, race)
    if err or ans is None:
        log(f"  ERR  {path.stem}: {err}")
        return "error"
    block, downgraded = validate(ans, cites)
    if dry:
        log(f"  DRY  {path.stem}: {block['status']}  {block['source'][:60]}")
        return block["status"]
    # re-read to avoid clobbering a parallel writer, then write atomically-ish
    d = json.loads(path.read_text())
    if isinstance(d["race"].get("eligibility"), dict):
        log(f"  SKIP {path.stem}: eligibility appeared concurrently")
        return "skipped"
    d["race"]["eligibility"] = block
    path.write_text(json.dumps(d, indent=2, ensure_ascii=False) + "\n")
    flag = " (downgraded)" if downgraded else ""
    log(f"  OK   {path.stem}: {block['status']}{flag}")
    return block["status"]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0, help="max races this run")
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    key = load_env_key()
    todo = pending_profiles()
    if args.limit:
        todo = todo[:args.limit]
    log(f"eligibility_audit: {len(todo)} races to audit "
        f"({'dry-run' if args.dry_run else 'writing'}), model={MODEL}")

    from collections import Counter
    results: Counter = Counter()
    with cf.ThreadPoolExecutor(max_workers=args.workers) as ex:
        futs = {ex.submit(process, p, key, args.dry_run): p for p in todo}
        for fut in cf.as_completed(futs):
            try:
                results[fut.result()] += 1
            except Exception as e:  # noqa: BLE001
                log(f"  ERR  {futs[fut].stem}: worker crashed: {e}")
                results["error"] += 1
    log(f"done: {dict(results)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
