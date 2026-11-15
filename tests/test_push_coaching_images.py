"""push_wordpress.sync_coaching uploads every picture the coaching page
references, before the page, and refuses to deploy when one is missing.
SSH/SCP are mocked; nothing touches a server."""
from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import Mock

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import push_wordpress  # noqa: E402

PAGE = '<img src="/coaching/img/a.webp"><img src="/coaching/img/b.webp"><link href="/coaching/img/a.webp">'


@pytest.fixture
def server(monkeypatch):
    run = Mock(return_value=Mock(returncode=0, stdout="", stderr=""))
    monkeypatch.setattr(push_wordpress.subprocess, "run", run)
    monkeypatch.setattr(push_wordpress, "get_ssh_credentials", Mock(return_value=("host.example", "user", "18765")))
    return run


def _stage(tmp_path, html, images):
    page = tmp_path / "coaching.html"
    page.write_text(html, encoding="utf-8")
    (tmp_path / "coaching-img").mkdir()
    for name in images:
        (tmp_path / "coaching-img" / name).write_bytes(b"RIFF")
    return page


def test_missing_image_blocks_deploy(tmp_path, server, capsys):
    page = _stage(tmp_path, PAGE, ["a.webp"])
    assert push_wordpress.sync_coaching(str(page)) is None
    assert server.call_count == 0
    assert "b.webp" in capsys.readouterr().out


def test_page_without_images_is_refused(tmp_path, server):
    page = _stage(tmp_path, "<p>no pictures</p>", ["a.webp"])
    assert push_wordpress.sync_coaching(str(page)) is None
    assert server.call_count == 0


def test_images_go_up_before_the_page(tmp_path, server):
    page = _stage(tmp_path, PAGE, ["a.webp", "b.webp", "stray.webp"])
    assert push_wordpress.sync_coaching(str(page)) is not None
    cmds = [c.args[0] for c in server.call_args_list]
    scps = [c for c in cmds if c[0] == "scp"]
    img_scp = next(c for c in scps if c[-1].endswith("/img/"))
    assert [Path(x).name for x in img_scp if x.endswith(".webp")] == ["a.webp", "b.webp"]
    assert scps.index(img_scp) < next(i for i, c in enumerate(scps) if c[-1].endswith("/index.html"))
