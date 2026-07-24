#!/usr/bin/env python3
"""Live training-guide inventory for the AEO markdown mirrors.

The generator must never claim a training guide exists unless the page is
live on SiteGround — repo output directories are add-only and go stale.
This asks the server directly (same discipline as gravel's
training_plan_inventory.py, adapted to this repo's static-site layout).
"""

from __future__ import annotations

import os
import re
import subprocess
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
REMOTE_GLOB = "~/www/roadielabs.com/public_html/race/*/training-plan/index.html"
SLUG_RE = re.compile(r"/race/([^/]+)/training-plan/index\.html$")
SSH_KEY = Path.home() / ".ssh" / "roadlabs_key"


def fetch_live_training_plan_slugs(timeout: int = 60) -> set[str]:
    """Fetch SiteGround once and return the live per-race training-guide slugs."""
    load_dotenv(PROJECT_ROOT / ".env")
    host = os.environ.get("SSH_HOST", "")
    user = os.environ.get("SSH_USER", "")
    port = os.environ.get("SSH_PORT", "18765")
    if not host or not user:
        raise RuntimeError("SSH_HOST/SSH_USER not set (.env)")
    result = subprocess.run(
        ["ssh", "-i", str(SSH_KEY), "-p", port,
         "-o", "ConnectTimeout=15", "-o", "BatchMode=yes",
         f"{user}@{host}", f"ls -d {REMOTE_GLOB} 2>/dev/null"],
        capture_output=True, text=True, timeout=timeout)
    if result.returncode not in (0, 2):  # 2 = glob matched nothing
        raise RuntimeError(f"ssh inventory failed: {result.stderr.strip()[:200]}")
    return {
        m.group(1)
        for line in result.stdout.splitlines()
        if (m := SLUG_RE.search(line.strip()))
    }
