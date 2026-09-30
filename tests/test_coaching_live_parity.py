"""Guards that keep a deploy of the coaching pages from main equal to live.

Background (2026-09-30): /coaching/, /coaching/apply/, /coaching/welcome/ and
/privacy/ were live from an unmerged Codex snapshot while main still sent
applications to FormSubmit, which had stopped delivering. A deploy from main
would have broken every Roadie Labs coaching application.
"""
from __future__ import annotations

import hashlib
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
WORDPRESS_DIR = REPO_ROOT / "wordpress"
sys.path.insert(0, str(WORDPRESS_DIR))

import live_head_patches  # noqa: E402
from generate_coaching import generate_coaching_page  # noqa: E402
from generate_coaching_apply import COACHING_INTAKE_WORKER_URL, generate_apply_page  # noqa: E402
from generate_success_pages import PAGES, generate_success_page  # noqa: E402

DESKTOP_SHA = "ce8feba610b58fe1141df1c96a9890f93075a03526bbfabbdcdadc2eca919da0"
LOGO_SHA = "6d67383d320f2625abb62b3ac4f4e5ee91e90342f8eb8a2a0c26630487da532c"


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


# ── Apply-page transport guard ───────────────────────────────


@pytest.fixture(scope="module")
def shipped_apply_html(tmp_path_factory) -> str:
    """The exact file `push_wordpress.py --sync-coaching-apply` uploads:
    generate_coaching_apply.py's own CLI output."""
    out = tmp_path_factory.mktemp("apply-out")
    subprocess.run(
        [sys.executable, str(WORDPRESS_DIR / "generate_coaching_apply.py"),
         "--output-dir", str(out)],
        check=True, capture_output=True, text=True, cwd=REPO_ROOT, timeout=120)
    return (out / "coaching-apply.html").read_text(encoding="utf-8")


def test_shipped_apply_page_posts_to_the_worker(shipped_apply_html):
    assert COACHING_INTAKE_WORKER_URL == "https://coaching-intake.gravelgodcoaching.workers.dev"
    assert f'var COACHING_INTAKE_URL = "{COACHING_INTAKE_WORKER_URL}";' in shipped_apply_html
    assert "fetch(COACHING_INTAKE_URL, {" in shipped_apply_html
    assert 'name="tier"' in shipped_apply_html
    # Tokens athlete-custom-training-plan-pipeline's daily health check requires.
    assert "coaching_intake_submission_id" in shipped_apply_html
    assert "coaching-intake" in shipped_apply_html


def test_shipped_apply_page_has_no_formsubmit(shipped_apply_html):
    assert "formsubmit.co" not in shipped_apply_html.lower()


def test_shipped_apply_page_has_the_checkbox_fix(shipped_apply_html):
    assert 'if (e.target.tagName !== "INPUT") { input.checked = !input.checked; }' not in shipped_apply_html
    assert 'if (this.tagName === "LABEL") { return; }' in shipped_apply_html


# ── Live-only <style> blocks folded into the generators ─────


def test_live_style_blocks_are_verbatim():
    assert _sha(live_head_patches.ROAD_DESKTOP_WIDTH_STYLE) == DESKTOP_SHA
    assert _sha(live_head_patches.ROADIE_APPROVED_LOGO_STYLE) == LOGO_SHA


def _pages_with_both_blocks():
    pages = {
        "coaching": generate_coaching_page(),
        "coaching-apply": generate_apply_page(),
    }
    for key in PAGES:
        pages[f"success:{key}"] = generate_success_page(key)
    return pages


@pytest.mark.parametrize("name,html", list(_pages_with_both_blocks().items()))
def test_page_carries_both_live_blocks_before_head_close(name, html):
    patch = live_head_patches.get_live_head_patches(desktop_width=True)
    assert html.count(live_head_patches.ROAD_DESKTOP_WIDTH_STYLE) == 1, name
    assert html.count(live_head_patches.ROADIE_APPROVED_LOGO_STYLE) == 1, name
    assert patch + "</head>" in html, name


def test_legal_pages_match_live_block_layout(tmp_path):
    subprocess.run(
        [sys.executable, str(WORDPRESS_DIR / "generate_legal_pages.py"),
         "--output-dir", str(tmp_path)],
        check=True, capture_output=True, text=True, cwd=REPO_ROOT, timeout=120)
    for slug in ("privacy", "terms"):
        html = (tmp_path / f"{slug}.html").read_text(encoding="utf-8")
        assert live_head_patches.get_live_head_patches(True) + "</head>" in html, slug
    cookies = (tmp_path / "cookies.html").read_text(encoding="utf-8")
    assert live_head_patches.ROAD_DESKTOP_WIDTH_STYLE not in cookies
    assert live_head_patches.get_live_head_patches(False) + "</head>" in cookies


def test_legal_last_updated_is_pinned_not_generation_date(tmp_path):
    subprocess.run(
        [sys.executable, str(WORDPRESS_DIR / "generate_legal_pages.py"),
         "--output-dir", str(tmp_path)],
        check=True, capture_output=True, text=True, cwd=REPO_ROOT, timeout=120)
    html = (tmp_path / "privacy.html").read_text(encoding="utf-8")
    assert "Last updated: August 2026" in html
