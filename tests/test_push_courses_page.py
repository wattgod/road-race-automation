"""--sync-courses-page: the /courses/ catalog page's only deploy path.

Before this flag the generated wordpress/output/courses/index.html could not
reach /courses/: --sync-courses ships /course/ (the course pages) and
--sync-pages copies subdirectories under /race/. Region-aware consent changed
every page's head, so /courses/ needs a real push like the rest.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import push_wordpress  # noqa: E402


@pytest.fixture
def staged(tmp_path):
    page = tmp_path / "courses" / "index.html"
    page.parent.mkdir()
    page.write_text("<html></html>", encoding="utf-8")
    assets = tmp_path / "assets"
    assets.mkdir()
    (assets / "rl-styles.abc123.css").write_text("x", encoding="utf-8")
    (assets / "rl-scripts.abc123.js").write_text("x", encoding="utf-8")
    return page


@pytest.fixture
def ssh(monkeypatch):
    calls = []
    monkeypatch.setattr(push_wordpress, "get_ssh_credentials",
                        lambda: ("host.example", "deploy", "18765"))
    monkeypatch.setattr(push_wordpress, "REMOTE_BASE", "/srv/public_html")
    monkeypatch.setattr(push_wordpress.subprocess, "run",
                        lambda cmd, **kw: calls.append(cmd))
    return calls


def test_uploads_page_to_courses_and_assets_to_race_assets(staged, ssh):
    url = push_wordpress.sync_courses_page(str(staged))
    assert url == "https://roadielabs.com/courses/"
    targets = [cmd[-1] for cmd in ssh if cmd[0] == "scp"]
    assert "deploy@host.example:/srv/public_html/courses/index.html" in targets
    assert "deploy@host.example:/srv/public_html/race/assets/rl-styles.abc123.css" in targets
    assert "deploy@host.example:/srv/public_html/race/assets/rl-scripts.abc123.js" in targets
    assert not any("wp-content" in part for cmd in ssh for part in cmd)


def test_missing_assets_refuse_before_any_remote_call(staged, ssh):
    for asset in (staged.parent.parent / "assets").iterdir():
        asset.unlink()
    assert push_wordpress.sync_courses_page(str(staged)) is None
    assert ssh == []


def test_missing_page_refuses_before_any_remote_call(tmp_path, ssh):
    assert push_wordpress.sync_courses_page(str(tmp_path / "courses" / "index.html")) is None
    assert ssh == []


def test_failed_upload_is_reported_not_success(staged, monkeypatch):
    monkeypatch.setattr(push_wordpress, "get_ssh_credentials",
                        lambda: ("host.example", "deploy", "18765"))

    def fail_scp(cmd, **kw):
        if cmd[0] == "scp":
            raise subprocess.CalledProcessError(1, cmd, stderr="denied")

    monkeypatch.setattr(push_wordpress.subprocess, "run", fail_scp)
    assert push_wordpress.sync_courses_page(str(staged)) is None


def test_flag_is_wired_into_cli_and_deploy_all():
    source = (Path(push_wordpress.__file__)).read_text(encoding="utf-8")
    assert '"--sync-courses-page"' in source
    assert "args.sync_courses_page = True" in source
    assert "sync_courses_page(args.courses_page_file)" in source
