"""RL-18: /road-races/ must not scroll sideways on a 375px or 390px phone.

Live measurement before the fix: scrollWidth 393 at both widths, caused by
the methodology link + four .rl-sort-btn buttons sitting in a non-wrapping
inline flex row in the results header.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from build_search_page import build_page  # noqa: E402

FRAGMENT = (ROOT / "web" / "road-labs-search.html").read_text(encoding="utf-8")
CSS = (ROOT / "web" / "rl-search.css").read_text(encoding="utf-8")

try:
    from playwright.sync_api import sync_playwright
except ImportError:  # pragma: no cover
    sync_playwright = None


def _has_chromium():
    if sync_playwright is None:
        return False
    try:
        with sync_playwright() as pw:
            pw.chromium.launch().close()
        return True
    except Exception:  # noqa: BLE001
        return False


def test_sort_row_is_a_wrapping_class_not_an_inline_nowrap_row():
    results_header = FRAGMENT[FRAGMENT.index('<div class="rl-results-header">'):]
    results_header = results_header[:results_header.index('<div id="rl-tier-container">')]
    assert '<div class="rl-sort-row">' in results_header
    assert 'style="display:flex' not in results_header
    rule = re.search(r"#rl-race-search \.rl-sort-row \{([^}]*)\}", CSS)
    assert rule and "flex-wrap: wrap" in rule.group(1)


@pytest.mark.skipif(not _has_chromium(), reason="playwright or Chromium not installed")
@pytest.mark.parametrize("width", [375, 390])
def test_road_races_page_has_no_horizontal_overflow(width):
    page_html = build_page(FRAGMENT)

    def handle(route):
        url = route.request.url
        if url.startswith("https://roadielabs.com/road-races/"):
            return route.fulfill(status=200, content_type="text/html", body=page_html)
        if url.startswith("https://roadielabs.com/search/rl-search.css"):
            return route.fulfill(status=200, content_type="text/css", body=CSS)
        return route.abort()

    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        page = browser.new_page(viewport={"width": width, "height": 800})
        page.route("**/*", handle)
        page.goto("https://roadielabs.com/road-races/", wait_until="load")
        result = page.evaluate("""() => {
          const w = document.documentElement.clientWidth;
          const sortRight = Math.max(...[...document.querySelectorAll('.rl-sort-btn')]
            .map(b => b.getBoundingClientRect().right));
          return {scroll: document.documentElement.scrollWidth, w, sortRight};
        }""")
        browser.close()
    assert result["sortRight"] <= result["w"], result
    assert result["scroll"] <= result["w"], result
