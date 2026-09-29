"""roadielabs.com/race-debrief/ in a real browser on a 390px phone.

Opens the page the way a plan's note links to it, answers every question the
way a rider would (the 0-10 scale by keyboard only), submits with the worker
intercepted, and checks the body the worker received, what GA4 was told,
what the rider saw, and that nothing threw. The body is the one
gravel-race-automation's chain test carries through the worker and Mission
Control (its tests/fixtures/race_debrief_submission_roadie.json). Skipped
without Playwright or its Chromium (Run Tests installs it).
"""
from __future__ import annotations

import html
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "wordpress"))

from generate_race_debrief import (  # noqa: E402
    LEAD_WORKER_URL,
    SECTIONS,
    SUCCESS,
    generate_race_debrief_page,
)

try:
    from playwright.sync_api import sync_playwright
except ImportError:  # pragma: no cover
    sync_playwright = None


def _has_chromium() -> bool:
    """The package alone is not enough: the browser is a separate install
    (`python -m playwright install chromium`, which Run Tests does)."""
    if sync_playwright is None:
        return False
    try:
        with sync_playwright() as pw:
            return Path(pw.chromium.executable_path).exists()
    except Exception:  # noqa: BLE001
        return False


pytestmark = pytest.mark.skipif(not _has_chromium(), reason="playwright or its Chromium not installed")

FIXTURE = json.loads((ROOT / "tests" / "fixtures" / "race_debrief_submission.json").read_text(encoding="utf-8"))
PAGE_URL = "https://roadielabs.com/race-debrief/"
GTAG_URL = "https://www.googletagmanager.com/gtag/js"
NOTE_LINK = "?plan=654321&utm_source=trainingpeaks&utm_medium=plan_note#top"
CORS = {
    "Access-Control-Allow-Origin": "https://roadielabs.com",
    "Access-Control-Allow-Methods": "POST, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type, Accept",
}
EVENTS_JS = """() => (window.dataLayer || [])
  .map((a) => Array.prototype.slice.call(a))
  .filter((a) => a[0] === 'event')
  .map((a) => [a[1], a[2] || {}])"""
LAYOUT_JS = """() => {
  const rects = (sel) => [...document.querySelectorAll(sel)].map((el) => el.getBoundingClientRect());
  const scale = rects('.rl-debrief-scale-option');
  const picked = document.querySelector('input[name="recommend"]:checked');
  return {
    innerWidth: window.innerWidth,
    scrollWidth: document.documentElement.scrollWidth,
    scaleCount: scale.length,
    scaleTops: scale.map((r) => Math.round(r.top)),
    scaleRight: Math.max(...scale.map((r) => r.right)),
    scaleMinWidth: Math.min(...scale.map((r) => r.width)),
    scaleMinHeight: Math.min(...scale.map((r) => r.height)),
    recommendPicked: picked ? picked.value : null,
  };
}"""


def _fields():
    out = []
    for sec in SECTIONS:
        for f in sec["fields"]:
            out.extend(f["fields"] if f["kind"] == "pair" else [f])
    return out


def _fill(page, answers):
    for field in _fields():
        name, kind = field.get("name"), field["kind"]
        if kind in ("hidden", "note") or name in ("name", "email"):
            continue
        if kind == "checks":
            for key, _ in field["options"]:
                if answers.get(key) == "yes":
                    page.click(f'label.rl-apply-checkbox-option:has(input[name="{key}"])')
            continue
        value = answers.get(name)
        if value is None:
            continue
        if kind == "scale":
            page.focus(f'input[name="{name}"][value="0"]')
            for _ in range(int(value)):
                page.keyboard.press("ArrowRight")
        elif kind == "radio":
            page.click(f'label.rl-apply-radio-option:has(input[name="{name}"][value="{value}"])')
        elif kind == "select":
            page.select_option(f"#{name}", value)
        else:
            page.fill(f"#{name}", value)


def run(query: str, answers: dict, *, worker_status: int = 200, identity_in_link: bool = False) -> dict:
    doc = generate_race_debrief_page()
    captured = {"worker": None, "other": []}

    def handle(route):
        req = route.request
        if req.url.startswith(PAGE_URL):
            return route.fulfill(status=200, content_type="text/html; charset=utf-8", body=doc)
        if req.url.startswith(GTAG_URL):
            return route.fulfill(status=200, content_type="text/javascript",
                                 body="window.__gaPageLocation = window.location.href;")
        if req.url.startswith(LEAD_WORKER_URL):
            if req.method == "OPTIONS":
                return route.fulfill(status=204, headers=CORS)
            captured["worker"] = json.loads(req.post_data)
            return route.fulfill(status=worker_status, headers={**CORS, "Content-Type": "application/json"},
                                 body=json.dumps({"success": worker_status == 200}))
        captured["other"].append(req.url)
        return route.abort()

    link = PAGE_URL + query
    if identity_in_link:
        sep = "&" if "?" in query else "?"
        base, _, frag = link.partition("#")
        link = f"{base}{sep}name=Test+Rider+C&email=test.rider.c%40example.com" + (f"#{frag}" if frag else "")
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        try:
            page = browser.new_page(viewport={"width": 390, "height": 844})
            errors = []
            page.on("pageerror", lambda exc: errors.append(str(exc)))
            page.route("**/*", handle)
            page.goto(link)
            page.wait_for_function("() => window.__gaPageLocation !== undefined", timeout=10000)
            ga_location = page.evaluate("() => window.__gaPageLocation")
            hidden = page.evaluate("() => ({plan: document.getElementById('plan').value,"
                                   " ref: document.getElementById('ref').value})")
            prefilled = {k: page.input_value(f"#{k}") for k in ("name", "email")}
            if not identity_in_link:
                page.fill("#name", FIXTURE["name"])
                page.fill("#email", FIXTURE["email"])
            page.fill("#last_word", "x" * 4100)
            capped = len(page.input_value("#last_word"))
            page.fill("#last_word", "")
            _fill(page, answers)
            layout = page.evaluate(LAYOUT_JS)
            page.click("#debrief-submit")
            page.wait_for_function(
                "() => { const m = document.getElementById('message');"
                " return m.classList.contains('success') || m.classList.contains('error'); }", timeout=15000)
            result = {
                "worker": captured["worker"], "errors": errors, "hidden": hidden, "layout": layout,
                "capped": capped, "prefilled": prefilled, "ga_location": ga_location,
                "href": page.evaluate("() => window.location.href"),
                "message": page.inner_text("#message"), "message_class": page.get_attribute("#message", "class"),
                "rating": page.evaluate("() => ({hidden: document.getElementById('tp-rating').hidden,"
                                        " href: document.getElementById('tp-rating-link').getAttribute('href'),"
                                        " text: document.getElementById('tp-rating').textContent})"),
                "events": page.evaluate(EVENTS_JS),
            }
        finally:
            browser.close()
    return result


@pytest.fixture(scope="module")
def full():
    return run(NOTE_LINK, FIXTURE["goal_answers"])


def _named(events, name):
    return [p for n, p in events if n == name]


def test_zero_page_errors(full):
    assert full["errors"] == []


def test_the_worker_gets_the_body_the_shared_pipeline_expects(full):
    body = full["worker"]
    assert body == {"source": "plan_debrief", "brand": "roadielabs", "email": FIXTURE["email"],
                    "name": FIXTURE["name"], "goal_answers": FIXTURE["goal_answers"], "website": "",
                    "plan": "654321"}
    assert all(isinstance(v, str) for v in body["goal_answers"].values())


def test_the_plan_stays_in_the_address(full):
    assert full["hidden"] == {"plan": "654321", "ref": ""}
    assert full["href"] == PAGE_URL + NOTE_LINK


def test_success_line_and_the_rating_link(full):
    assert "success" in full["message_class"]
    assert full["message"] == html.unescape(SUCCESS)
    assert full["rating"]["hidden"] is False
    assert full["rating"]["href"] == "https://www.trainingpeaks.com/training-plans/cycling/tp-654321"
    assert full["rating"]["text"] == "If you have a minute, rate the plan on TrainingPeaks, whatever score you'd give it."


def test_ga4_start_and_submit_with_presence_not_values(full):
    starts, submits = _named(full["events"], "debrief_start"), _named(full["events"], "debrief_submit")
    assert len(starts) == 1 and len(submits) == 1
    for params in starts + submits:
        assert (params["has_plan"], params["has_ref"], params["variant"]) == ("yes", "no", "race_debrief")
    assert "654321" not in json.dumps(full["events"])


def test_layout_at_390(full):
    layout = full["layout"]
    assert layout["innerWidth"] == 390 and layout["scrollWidth"] <= 390
    assert layout["scaleCount"] == 11 and len(set(layout["scaleTops"])) == 1
    assert layout["scaleRight"] <= 390
    assert layout["scaleMinWidth"] >= 24 and layout["scaleMinHeight"] >= 44
    assert layout["recommendPicked"] == "9"


def test_typing_stops_at_the_stored_length(full):
    assert full["capped"] == 4000


def test_a_personal_link_prefills_and_never_reaches_ga4():
    seen = run("?plan=654321", {"raced": "finished"}, identity_in_link=True)
    assert seen["errors"] == []
    assert seen["prefilled"] == {"name": "Test Rider C", "email": "test.rider.c@example.com"}
    assert seen["ga_location"] == PAGE_URL + "?plan=654321"
    assert seen["worker"]["email"] == "test.rider.c@example.com"


def test_a_custom_plan_ref_and_no_rating_line():
    seen = run("?ref=test-ref-0001", {"raced": "dnf"})
    assert seen["worker"]["ref"] == "test-ref-0001" and "plan" not in seen["worker"]
    assert seen["rating"]["hidden"] is True
    assert _named(seen["events"], "debrief_submit")[0]["has_ref"] == "yes"


@pytest.mark.parametrize("query", ["?plan=12ab34&ref=bad", "?plan=%20654321&ref=test-ref-0001%0A"])
def test_malformed_params_are_never_sent(query):
    seen = run(query, {"raced": "later"})
    assert seen["errors"] == []
    assert seen["hidden"] == {"plan": "", "ref": ""}
    assert "plan" not in seen["worker"] and "ref" not in seen["worker"]
    assert seen["rating"]["hidden"] is True


def test_a_failed_store_shows_the_error_and_no_rating_line():
    seen = run(NOTE_LINK, {"raced": "finished"}, worker_status=503)
    assert "error" in seen["message_class"] and "coach@roadielabs.com" in seen["message"]
    assert seen["rating"]["hidden"] is True
    assert _named(seen["events"], "debrief_submit") == []
