"""Read scheduled monitoring snapshots without changing the local checkout."""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
STATE_BRANCH = "monitoring-state"
STATE_REF = f"refs/remotes/origin/{STATE_BRANCH}"


def refresh_history(directory_env: str) -> str | None:
    if directory_env in os.environ:
        return None

    git = ["git", "-C", str(REPO_ROOT)]
    try:
        subprocess.run(
            [*git, "fetch", "--no-tags", "origin", f"refs/heads/{STATE_BRANCH}:{STATE_REF}"],
            check=True, capture_output=True, timeout=10,
            env={**os.environ, "GIT_TERMINAL_PROMPT": "0"},
        )
    except (OSError, subprocess.SubprocessError):
        print("Could not refresh scheduled snapshots. Using cached or local history.", file=sys.stderr)

    try:
        return subprocess.check_output(
            [*git, "rev-parse", "--verify", STATE_REF],
            stderr=subprocess.DEVNULL, text=True,
        ).strip()
    except (OSError, subprocess.CalledProcessError):
        return None


def load_snapshot(path: Path, history_commit: str | None) -> dict | None:
    if path.exists():
        return json.loads(path.read_text())
    if history_commit:
        snapshot_object = f"{history_commit}:{path.relative_to(REPO_ROOT).as_posix()}"
        completed = subprocess.run(
            ["git", "-C", str(REPO_ROOT), "show", snapshot_object],
            capture_output=True, text=True,
        )
        if completed.returncode == 0:
            return json.loads(completed.stdout)
    return None


def snapshot_names(directory: Path, history_commit: str | None) -> set[str]:
    names = {path.name for path in directory.glob("*.json")}
    if history_commit:
        history_tree = f"{history_commit}:{directory.relative_to(REPO_ROOT).as_posix()}"
        completed = subprocess.run(
            ["git", "-C", str(REPO_ROOT), "ls-tree", "--name-only", "-z", history_tree],
            capture_output=True, text=True,
        )
        if completed.returncode == 0:
            names.update(name for name in completed.stdout.split("\0") if name.endswith(".json"))
    return names
