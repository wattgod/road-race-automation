"""Deploy tarballs never carry macOS AppleDouble ._ files (issue #176).

3,919 ._* files were publicly served on roadielabs.com on 2026-11-15.
"""
from __future__ import annotations

import importlib.util
import io
import os
import re
import shutil
import subprocess
import sys
import tarfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "scripts" / "push_wordpress.py"


def _push():
    spec = importlib.util.spec_from_file_location("push_wordpress_tar", SRC)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_every_tar_call_drops_mac_metadata():
    calls = re.findall(r'\["tar",[^\]]*', SRC.read_text(encoding="utf-8"))
    assert calls, "no tar calls found"
    for call in calls:
        assert "TAR_NO_MAC_METADATA" in call, call


def test_module_disables_copyfile():
    push = _push()
    assert os.environ.get("COPYFILE_DISABLE") == "1"
    assert "--exclude=._*" in push.TAR_NO_MAC_METADATA


@pytest.mark.skipif(sys.platform != "darwin" or not shutil.which("xattr"),
                    reason="AppleDouble files are a macOS tar behaviour")
def test_tar_listing_has_no_appledouble(tmp_path):
    push = _push()
    page = tmp_path / "src" / "slug" / "index.html"
    page.parent.mkdir(parents=True)
    page.write_text("<p>x</p>")
    subprocess.run(["xattr", "-w", "com.apple.provenance", "x", str(page)], check=True)
    (page.parent / "._stale.html").write_text("junk")
    out = subprocess.run(
        ["tar", *push.TAR_NO_MAC_METADATA, "-cf", "-", "-C", str(tmp_path / "src"), "slug"],
        check=True, capture_output=True,
    ).stdout
    # bsdtar folds ._ entries back into their file when listing, so read the
    # archive with tarfile to see what the server's GNU tar would extract.
    names = tarfile.open(fileobj=io.BytesIO(out)).getnames()
    assert "slug/index.html" in names
    assert not [n for n in names if Path(n).name.startswith("._")], names
