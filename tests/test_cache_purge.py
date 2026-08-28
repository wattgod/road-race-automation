"""Regression guard for static-site cache invalidation."""

import sys
from pathlib import Path
from unittest.mock import Mock


SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

import push_wordpress  # noqa: E402


def test_purge_cache_uses_site_tools_client(monkeypatch) -> None:
    monkeypatch.setattr(push_wordpress, "get_ssh_credentials", lambda: ("host", "user", "18765"))
    completed = Mock(returncode=0, stdout="id=roadielabs.com flush_cache=1 msg=OK", stderr="")
    run = Mock(return_value=completed)
    monkeypatch.setattr(push_wordpress.subprocess, "run", run)

    assert push_wordpress.purge_cache() is True
    command = run.call_args.args[0]
    assert command[-1] == "site-tools-client domain update id=1 flush_cache=1 2>&1"


def test_purge_cache_fails_closed_without_ok_receipt(monkeypatch) -> None:
    monkeypatch.setattr(push_wordpress, "get_ssh_credentials", lambda: ("host", "user", "18765"))
    completed = Mock(returncode=0, stdout="unexpected response", stderr="")
    monkeypatch.setattr(push_wordpress.subprocess, "run", Mock(return_value=completed))

    assert push_wordpress.purge_cache() is False
