"""Every Cloudflare *.workers.dev URL this repo ships must live on the
gravelgodcoaching account.

The intake edges (coaching-intake, fueling-lead-intake, review-intake) are
deployed from wattgod/gravel-race-automation to the gravelgodcoaching
workers.dev subdomain. A URL on any other account subdomain is either a typo
or a Worker nobody here can deploy, monitor, or rotate secrets for, and every
form posting to it fails silently for real athletes.
"""
from __future__ import annotations

import re
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
ALLOWED_ACCOUNT = "gravelgodcoaching"

# URLs only (scheme or protocol-relative), so prose that names a wrong host as
# a warning — e.g. "fueling-lead-intake.gravelgodcycling.workers.dev does not
# exist" in generate_race_debrief.py — is not mistaken for a live endpoint.
# The label directly before ".workers.dev" is the account subdomain
# (https://<worker>.<account>.workers.dev).
WORKERS_DEV_RE = re.compile(r"(?:https?:)?//(?:[A-Za-z0-9-]+\.)*?([A-Za-z0-9-]+)\.workers\.dev\b")

SKIP_DIRS = {".git", "node_modules", ".venv", "venv", "__pycache__", ".pytest_cache"}


def _tracked_text_files() -> list[Path]:
    try:
        out = subprocess.run(
            ["git", "ls-files", "-z"], cwd=REPO_ROOT, check=True,
            capture_output=True, timeout=60,
        ).stdout
        files = [REPO_ROOT / name for name in out.decode("utf-8", "replace").split("\0") if name]
    except (OSError, subprocess.SubprocessError):
        files = [
            path for path in REPO_ROOT.rglob("*")
            if path.is_file() and not SKIP_DIRS.intersection(path.relative_to(REPO_ROOT).parts)
        ]
    return files


def _workers_dev_hits() -> list[tuple[str, int, str]]:
    hits = []
    for path in _tracked_text_files():
        try:
            data = path.read_bytes()
        except OSError:
            continue
        if b"workers.dev" not in data or b"\0" in data[:8192]:
            continue
        text = data.decode("utf-8", "replace")
        for lineno, line in enumerate(text.splitlines(), 1):
            for match in WORKERS_DEV_RE.finditer(line):
                hits.append((str(path.relative_to(REPO_ROOT)), lineno, match.group(0)))
    return hits


def test_scan_finds_the_known_intake_workers():
    """Guard against a scan that silently matches nothing."""
    accounts = {WORKERS_DEV_RE.search(host).group(1) for _, _, host in _workers_dev_hits()}
    assert "gravelgodcoaching" in accounts


def test_pattern_reads_the_account_label_of_urls_only():
    assert WORKERS_DEV_RE.search("https://coaching-intake.gravelgodcoaching.workers.dev/x").group(1) == "gravelgodcoaching"
    # Built at runtime so this file's own source doesn't trip the repo scan.
    other = "//a.b." + "someone" + ".workers.dev"
    assert WORKERS_DEV_RE.search(f'fetch("{other}")').group(1) == "someone"
    assert WORKERS_DEV_RE.search("the host x.gravelgodcycling.workers.dev does not exist") is None


def test_every_workers_dev_url_is_on_the_gravelgodcoaching_account():
    offenders = [
        f"{path}:{lineno}: {host}"
        for path, lineno, host in _workers_dev_hits()
        if WORKERS_DEV_RE.search(host).group(1) != ALLOWED_ACCOUNT
    ]
    assert not offenders, (
        "workers.dev URL(s) outside the gravelgodcoaching account:\n"
        + "\n".join(offenders)
    )
