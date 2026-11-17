"""Browser run of the /road-races/ race cards (#198, Astra review on PR #199).

Serves the built search page and the real web/ assets at roadielabs.com inside
headless Chromium; every other request is aborted. The race index is the real
one, with the first race given a very long name and a series pill so wrapping
and the pill's own link are exercised. At 1440 and 390 it checks:

  - a real mouse click on the card body (meta line) opens the race,
  - compare, favourite, series pill and score bar each receive their own click
    (hit-tested with elementFromPoint, then clicked for real),
  - Tab reaches the score bar; Enter opens, Space closes, aria-expanded synced,
  - no title/badge overlap, no title under 100px, no horizontal scroll,
  - zero page errors.

Skips (does not fail) when Playwright or a launchable Chromium is missing.
"""
from __future__ import annotations

import functools
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

ORIGIN = "https://roadielabs.com"
LONG_NAME = "Gran Fondo Internazionale Campionissimo Fausto Coppi Cuneo Extraordinarily Long Edition"


@functools.lru_cache(maxsize=1)
def _has_chromium() -> bool:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        return False
    try:
        with sync_playwright() as p:
            p.chromium.launch().close()
        return True
    except Exception:  # noqa: BLE001 — any launch failure means "no browser"
        return False


pytestmark = pytest.mark.skipif(
    not _has_chromium(), reason="Playwright Chromium not installed/launchable")


@pytest.fixture(scope="module")
def site():
    from build_search_page import build_page, race_count
    fragment = (ROOT / "web" / "road-labs-search.html").read_text(encoding="utf-8")
    races = json.loads((ROOT / "web" / "race-index.json").read_text(encoding="utf-8"))
    races.sort(key=lambda r: -(r.get("overall_score") or 0))
    races[0] = dict(races[0], name=LONG_NAME, series_name="Campionissimo Series",
                    series_id="campionissimo")
    return {
        f"{ORIGIN}/road-races/": ("text/html; charset=utf-8", build_page(fragment, race_count())),
        f"{ORIGIN}/search/road-labs-search.js": (
            "application/javascript", (ROOT / "web" / "road-labs-search.js").read_text()),
        f"{ORIGIN}/search/rl-search.css": (
            "text/css", (ROOT / "web" / "rl-search.css").read_text()),
        f"{ORIGIN}/search/race-index.json": ("application/json", json.dumps(races)),
    }


@pytest.fixture(scope="module")
def browser():
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        b = p.chromium.launch()
        yield b
        b.close()


def _open(browser, site, width):
    ctx = browser.new_context(viewport={"width": width, "height": 900})
    page = ctx.new_page()
    errors = []
    page.on("pageerror", lambda exc: errors.append(str(exc)))
    navigations = []

    def route(r):
        url = r.request.url.split("?")[0]
        if url in site:
            ctype, body = site[url]
            return r.fulfill(status=200, content_type=ctype, body=body)
        if url.startswith(f"{ORIGIN}/race/") and r.request.resource_type == "document":
            navigations.append(url)
            return r.fulfill(status=200, content_type="text/html", body="<p>race</p>")
        return r.abort()

    page.route("**/*", route)
    page.goto(f"{ORIGIN}/road-races/", wait_until="domcontentloaded")
    page.wait_for_selector(".rl-card-linked")
    return ctx, page, errors, navigations


def _mouse(page, loc):
    loc.evaluate("e => e.scrollIntoView({block: 'center'})")
    box = loc.bounding_box()
    page.mouse.click(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)


AUDIT = """() => {
  const cards = [...document.querySelectorAll('#rl-race-search .rl-card')].slice(0, 40);
  let dead = 0, stray = 0, overlaps = 0, narrow = 0; const ctrlMiss = [];
  for (const c of cards) {
    c.scrollIntoView({block: 'center'});
    const r = c.getBoundingClientRect(), title = c.querySelector('a.rl-card-name');
    for (const fx of [0.1, 0.5, 0.9]) for (const fy of [0.3, 0.6, 0.95]) {
      const el = document.elementFromPoint(r.left + r.width * fx, r.top + r.height * fy);
      const hit = el && el.closest('a,button,label,input');
      if (!hit) dead++;
      else if (hit !== title && !hit.matches('.rl-series-badge,.rl-fav-btn,.rl-score-bar,.rl-compare-check')) stray++;
    }
    for (const sel of ['.rl-compare-check', '.rl-fav-btn', '.rl-series-badge', 'button.rl-score-bar']) {
      const k = c.querySelector(sel); if (!k) continue;
      const b = k.getBoundingClientRect();
      const el = document.elementFromPoint(b.left + b.width / 2, b.top + b.height / 2);
      if (!(el && k.contains(el))) ctrlMiss.push(sel);
    }
    const t = title.getBoundingClientRect();
    if (t.width < 100) narrow++;
    for (const b of c.querySelectorAll('.rl-card-badges > *')) {
      const q = b.getBoundingClientRect();
      if (q.width && !(q.right <= t.left || q.left >= t.right || q.bottom <= t.top || q.top >= t.bottom)) { overlaps++; break; }
    }
  }
  return {cards: cards.length, dead, stray, overlaps, narrow, ctrlMiss,
          hscroll: document.documentElement.scrollWidth > innerWidth};
}"""


@pytest.mark.parametrize("width", [1440, 390])
def test_cards_hit_test_and_layout(browser, site, width):
    ctx, page, errors, _ = _open(browser, site, width)
    try:
        audit = page.evaluate(AUDIT)
        assert audit["cards"] == 40
        assert audit == dict(audit, dead=0, stray=0, overlaps=0, narrow=0, ctrlMiss=[], hscroll=False)
        long_title = page.locator("a.rl-card-name", has_text=LONG_NAME)
        assert long_title.count() == 1
        assert errors == []
    finally:
        ctx.close()


@pytest.mark.parametrize("width", [1440, 390])
def test_card_body_click_opens_race(browser, site, width):
    ctx, page, errors, navigations = _open(browser, site, width)
    try:
        card = page.locator(".rl-card-linked").nth(1)
        href = card.locator("a.rl-card-name").get_attribute("href")
        with page.expect_navigation():
            _mouse(page, card.locator(".rl-card-meta"))
        assert page.url.split("?")[0] == ORIGIN + href
        assert errors == []
    finally:
        ctx.close()


@pytest.mark.parametrize("width", [1440, 390])
def test_secondary_controls_keep_their_own_clicks(browser, site, width):
    ctx, page, errors, navigations = _open(browser, site, width)
    try:
        card = page.locator(".rl-card-linked").first
        _mouse(page, card.locator(".rl-fav-btn"))
        assert "rl-fav-active" in card.locator(".rl-fav-btn").get_attribute("class")
        _mouse(page, card.locator(".rl-compare-check"))
        assert card.locator(".rl-compare-check input").is_checked()
        sb = card.locator("button.rl-score-bar")
        _mouse(page, sb)
        assert sb.get_attribute("aria-expanded") == "true"
        assert card.locator(".rl-score-breakdown").is_visible()
        _mouse(page, sb)
        assert sb.get_attribute("aria-expanded") == "false"
        assert navigations == []
        with page.expect_navigation():
            _mouse(page, card.locator(".rl-series-badge"))
        assert page.url.split("?")[0] == f"{ORIGIN}/race/series/campionissimo/"
        assert errors == []
    finally:
        ctx.close()


@pytest.mark.parametrize("width", [1440, 390])
def test_score_bar_keyboard(browser, site, width):
    ctx, page, errors, navigations = _open(browser, site, width)
    try:
        card = page.locator(".rl-card-linked").nth(1)
        sb = card.locator("button.rl-score-bar")
        card.locator(".rl-fav-btn").focus()
        for _ in range(4):
            if sb.evaluate("b => b === document.activeElement"):
                break
            page.keyboard.press("Tab")
        assert sb.evaluate("b => b === document.activeElement")
        assert sb.evaluate("b => getComputedStyle(b).outlineStyle") == "solid"
        assert sb.bounding_box()["height"] >= 24
        page.keyboard.press("Enter")
        assert sb.get_attribute("aria-expanded") == "true"
        assert card.locator(".rl-score-breakdown").is_visible()
        page.keyboard.press("Space")
        assert sb.get_attribute("aria-expanded") == "false"
        assert not card.locator(".rl-score-breakdown").is_visible()
        assert navigations == [] and errors == []
    finally:
        ctx.close()
