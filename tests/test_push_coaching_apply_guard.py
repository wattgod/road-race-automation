"""push_wordpress.sync_coaching_apply refuses to upload an apply page that
would break coaching applications (FormSubmit present, Worker or tier missing).

A stale wordpress/output/coaching-apply.html from before the Worker switch
was FormSubmit-only; `--deploy-all` or `--sync-coaching-apply` would have
scp'd it straight over the working live page. SSH/SCP are mocked here —
nothing touches a server.
"""
from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import Mock

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))
sys.path.insert(0, str(REPO_ROOT / "wordpress"))

import push_wordpress  # noqa: E402
from coaching_apply_contract import (  # noqa: E402
    COACHING_INTAKE_WORKER_URL,
    apply_page_problems,
)
from generate_coaching_apply import generate_apply_page  # noqa: E402

# What main's generator produced before the Worker switch, in miniature.
STALE_FORMSUBMIT_PAGE = """<!DOCTYPE html><html><head></head><body>
<form id="intake-form"><input type="text" name="name"></form>
<script>
var FORMSUBMIT_URL = "https://formsubmit.co/ajax/df9d64ff7bd404311c74f4a4240a1ebd";
fetch(FORMSUBMIT_URL, { method: "POST", body: new FormData() });
</script></body></html>"""


@pytest.fixture
def server(monkeypatch):
    """Mock credentials + ssh/scp; record every command."""
    run = Mock(return_value=Mock(returncode=0, stdout="", stderr=""))
    creds = Mock(return_value=("host.example", "user", "18765"))
    monkeypatch.setattr(push_wordpress.subprocess, "run", run)
    monkeypatch.setattr(push_wordpress, "get_ssh_credentials", creds)
    return run, creds


def test_stale_formsubmit_page_is_refused(tmp_path, server, capsys):
    run, creds = server
    stale = tmp_path / "coaching-apply.html"
    stale.write_text(STALE_FORMSUBMIT_PAGE, encoding="utf-8")

    assert push_wordpress.sync_coaching_apply(str(stale)) is None
    run.assert_not_called()
    creds.assert_not_called()
    out = capsys.readouterr().out
    assert "✗ Refusing to upload" in out
    assert "formsubmit.co" in out
    assert "coaching-intake Worker" in out
    assert 'name="tier"' in out


@pytest.mark.parametrize("mutation, reason", [
    (lambda html: html.replace("</body>", "<!-- https://FormSubmit.co/x --></body>"), "formsubmit.co"),
    (lambda html: html.replace(COACHING_INTAKE_WORKER_URL, "https://example.invalid"), "Worker"),
    (lambda html: html.replace('name="tier"', 'name="plan"'), 'name="tier"'),
])
def test_each_contract_breach_is_refused(tmp_path, server, capsys, mutation, reason):
    run, _ = server
    page = tmp_path / "coaching-apply.html"
    page.write_text(mutation(generate_apply_page()), encoding="utf-8")

    assert push_wordpress.sync_coaching_apply(str(page)) is None
    run.assert_not_called()
    assert reason in capsys.readouterr().out


def test_good_page_uploads_via_scp(tmp_path, server):
    run, _ = server
    # --coaching-apply-file points at an arbitrary path, not wordpress/output.
    page = tmp_path / "custom" / "apply.html"
    page.parent.mkdir()
    page.write_text(generate_apply_page(), encoding="utf-8")
    assert apply_page_problems(page.read_text(encoding="utf-8")) == []

    url = push_wordpress.sync_coaching_apply(str(page))

    assert url and url.endswith("/coaching/apply/")
    commands = [call.args[0] for call in run.call_args_list]
    assert commands[0][0] == "ssh" and "mkdir -p" in commands[0][-1]
    scp = commands[1]
    assert scp[0] == "scp"
    assert str(page) in scp
    assert scp[-1].endswith("/coaching/apply/index.html")


def test_missing_file_is_refused_without_server_contact(tmp_path, server):
    run, creds = server
    assert push_wordpress.sync_coaching_apply(str(tmp_path / "nope.html")) is None
    run.assert_not_called()
    creds.assert_not_called()


def test_cli_exits_nonzero_when_apply_upload_is_refused():
    src = (REPO_ROOT / "scripts" / "push_wordpress.py").read_text(encoding="utf-8")
    assert "coaching_apply_failed = sync_coaching_apply(args.coaching_apply_file) is None" in src
    assert src.rstrip().endswith("sys.exit(1)")
