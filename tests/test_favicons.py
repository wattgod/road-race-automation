"""ALL-07: root favicon files exist, are declared, and ship to the site root."""
from __future__ import annotations

import shutil
import sys
from pathlib import Path

import pytest
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import push_wordpress  # noqa: E402

SVG_ICON_LINK = '<link rel="icon" type="image/svg+xml" href="/race/assets/rl-icon.svg?v=siped-1">'
REQUIRED_LINKS = (
    '<link rel="icon" href="/favicon.ico" sizes="32x32">',
    '<link rel="icon" type="image/png" sizes="32x32" href="/favicon-32x32.png">',
    '<link rel="apple-touch-icon" href="/apple-touch-icon.png">',
)


def test_icon_files_have_expected_sizes():
    with Image.open(ROOT / "web" / "favicon.ico") as ico:
        assert ico.info["sizes"] == {(16, 16), (32, 32)}
    with Image.open(ROOT / "web" / "favicon-32x32.png") as png:
        assert png.size == (32, 32)
    with Image.open(ROOT / "web" / "apple-touch-icon.png") as touch:
        assert touch.size == (180, 180)
        assert touch.mode == "RGB"  # iOS shows transparency as black


def test_every_page_head_declaring_the_svg_icon_declares_the_raster_icons():
    generators = [p for p in (ROOT / "wordpress").glob("generate_*.py")
                  if SVG_ICON_LINK in p.read_text(encoding="utf-8")]
    assert len(generators) >= 10
    for path in generators:
        src = path.read_text(encoding="utf-8")
        for tag in REQUIRED_LINKS:
            assert src.count(tag) == src.count(SVG_ICON_LINK), (path.name, tag)


@pytest.mark.skipif(not shutil.which("rsvg-convert"), reason="needs librsvg")
def test_generator_rebuilds_from_the_logo_svg(tmp_path):
    from scripts import generate_favicons
    paths = generate_favicons.build(out_dir=tmp_path)
    assert [p.name for p in paths] == list(generate_favicons.FAVICON_FILES)
    with Image.open(tmp_path / "apple-touch-icon.png") as im:
        assert im.size == (180, 180)


def test_sync_favicons_refuses_when_files_missing(tmp_path, monkeypatch):
    calls = []
    monkeypatch.setattr(push_wordpress.subprocess, "run", lambda cmd, **kw: calls.append(cmd))
    assert push_wordpress.sync_favicons(str(tmp_path)) is None
    assert calls == []


def test_sync_favicons_uploads_to_site_root(monkeypatch):
    calls = []
    monkeypatch.setattr(push_wordpress, "get_ssh_credentials",
                        lambda: ("host.example", "deploy", "18765"))
    monkeypatch.setattr(push_wordpress, "REMOTE_BASE", "/srv/public_html")
    monkeypatch.setattr(push_wordpress.subprocess, "run", lambda cmd, **kw: calls.append(cmd))
    monkeypatch.chdir(ROOT)
    result = push_wordpress.sync_favicons()
    scp = calls[0]
    assert scp[0] == "scp" and scp[-1] == "deploy@host.example:/srv/public_html/"
    assert {Path(a).name for a in scp[5:-1]} == set(push_wordpress.FAVICON_FILES)
    assert result[-1].endswith("/apple-touch-icon.png")


def test_sync_favicons_flag_is_wired():
    src = (ROOT / "scripts" / "push_wordpress.py").read_text(encoding="utf-8")
    assert '"--sync-favicons", action="store_true"' in src
    assert "args.sync_favicons," in src
    assert "if args.sync_favicons:\n        sync_favicons()" in src
