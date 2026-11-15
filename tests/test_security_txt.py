"""ALL-09: /.well-known/security.txt (RFC 9116) ships with --sync-llms-txt."""
from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import generate_security_txt as sec  # noqa: E402
import push_wordpress  # noqa: E402


def _fields(text):
    return dict(line.split(": ", 1) for line in text.strip().splitlines())


def test_required_fields_and_expiry_one_year_out():
    fields = _fields(sec.build_security_txt(date(2026, 11, 15)))
    assert fields == {
        "Contact": "mailto:gravelgodcoaching@gmail.com",
        "Expires": "2027-11-15T00:00:00Z",
        "Preferred-Languages": "en",
        "Canonical": "https://roadielabs.com/.well-known/security.txt",
    }


def test_leap_day_expiry():
    assert _fields(sec.build_security_txt(date(2028, 2, 29)))["Expires"] == "2029-02-28T00:00:00Z"


def test_tracked_copy_is_well_formed():
    fields = _fields((ROOT / "web" / ".well-known" / "security.txt").read_text())
    assert set(fields) == {"Contact", "Expires", "Preferred-Languages", "Canonical"}


def test_sync_llms_txt_uploads_security_txt(monkeypatch, tmp_path):
    calls = []
    out = tmp_path / ".well-known" / "security.txt"
    monkeypatch.setattr(push_wordpress, "get_ssh_credentials",
                        lambda: ("host.example", "deploy", "18765"))
    monkeypatch.setattr(push_wordpress, "REMOTE_BASE", "/srv/public_html")
    monkeypatch.setattr(push_wordpress.subprocess, "run",
                        lambda cmd, **kw: calls.append(cmd))
    monkeypatch.setattr(sec, "write_security_txt",
                        lambda: (out.parent.mkdir(parents=True, exist_ok=True),
                                 out.write_text(sec.build_security_txt(date(2026, 11, 15))),
                                 out)[-1])
    monkeypatch.chdir(ROOT)
    push_wordpress.sync_llms_txt()
    scp_calls = [c for c in calls if c and c[0] == "scp"]
    assert any(c[-1] == "deploy@host.example:/srv/public_html/.well-known/security.txt"
               and c[-2] == str(out) for c in scp_calls)


def test_failed_regeneration_uploads_nothing(monkeypatch):
    calls = []
    monkeypatch.setattr(push_wordpress, "REMOTE_BASE", "/srv/public_html")
    monkeypatch.setattr(push_wordpress.subprocess, "run",
                        lambda cmd, **kw: calls.append(cmd))

    def boom(*a, **kw):
        raise OSError("disk full")
    monkeypatch.setattr(sec, "write_security_txt", boom)
    assert push_wordpress.sync_security_txt("host.example", "deploy", "18765") is None
    assert calls == []
