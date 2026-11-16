"""/plan/manage on roadielabs.com sends riders to the plan manage page.

The page is served by the training-plan pipeline on Railway. It reads its #t=
token from the URL fragment (kept across a redirect) and posts to relative
/api/race-plan/* paths, so only a redirect works here.
"""
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import push_wordpress as pw  # noqa: E402

TARGET = "https://athlete-custom-training-plan-pipeline-production.up.railway.app/plan/manage"
RULE = re.compile(r"^RewriteRule (\S+) (\S+) \[([^\]]+)\]$", re.M)


def _first_rule_for(path):
    for pattern, target, flags in RULE.findall(pw.build_redirect_block()):
        if re.search(pattern, path):
            return target, flags
    return None


def test_both_spellings_redirect_to_the_manage_page():
    for path in ("plan/manage", "plan/manage/"):
        assert _first_rule_for(path) == (TARGET, "R=302,L"), path


def test_nothing_else_under_plan_is_caught():
    for path in ("plan/manage/extra", "plan/", "plan/managed", "xplan/manage"):
        hit = _first_rule_for(path)
        assert hit is None or hit[0] != TARGET, path


def _fake_ssh(monkeypatch, read_rc, read_out):
    monkeypatch.setattr(pw, "get_ssh_credentials", lambda: ("h", "u", "22"))
    calls = []

    def fake_run(cmd, *a, **kw):
        remote = cmd[-1]
        calls.append(remote)
        if remote.startswith("cat ") and not remote.startswith("cat >"):
            return subprocess.CompletedProcess(cmd, read_rc, read_out, "")
        return subprocess.CompletedProcess(cmd, 0, "", "")

    monkeypatch.setattr(pw.subprocess, "run", fake_run)
    return calls


def test_failed_read_never_writes(monkeypatch):
    calls = _fake_ssh(monkeypatch, 255, "")
    assert pw.sync_redirects() is False
    assert not any(c.startswith("cat >") for c in calls)


def test_unrecognized_content_never_writes(monkeypatch):
    calls = _fake_ssh(monkeypatch, 0, "hello\n")
    assert pw.sync_redirects() is False
    assert not any(c.startswith("cat >") for c in calls)


def test_good_read_backs_up_then_writes(monkeypatch):
    calls = _fake_ssh(monkeypatch, 0, "RewriteEngine On\nErrorDocument 404 /404.html\n")
    assert pw.sync_redirects() is True
    backup = next(i for i, c in enumerate(calls) if c.startswith("cp "))
    write = next(i for i, c in enumerate(calls) if c.startswith("cat >"))
    assert backup < write



def test_refused_sync_fails_the_run(tmp_path):
    """No SSH credentials: sync_redirects refuses, so the script exits 1."""
    import os
    env = {k: v for k, v in os.environ.items() if "SSH" not in k}
    env["HOME"] = str(tmp_path)  # no ~/.ssh/roadlabs_key either
    run = subprocess.run([sys.executable, str(ROOT / "scripts" / "push_wordpress.py"),
                          "--sync-redirects"], cwd=tmp_path, env=env,
                         capture_output=True, text=True, timeout=60)
    assert "SSH credentials not set" in run.stdout, run.stdout + run.stderr
    assert run.returncode == 1, run.stdout + run.stderr
