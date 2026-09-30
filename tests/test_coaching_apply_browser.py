"""Browser run of /coaching/apply/ against an intercepted coaching-intake Worker.

Serves the generated page at its real origin (https://roadielabs.com) inside
headless Chromium at a 390px phone viewport. Nothing leaves the machine: the
Worker is fulfilled (or failed) by a Playwright route and every other request
is aborted, so no real onboarding case is ever created. Covers:

  - the payload the Worker receives (contract fields + questionnaire),
  - Worker success -> success message, draft + submission id cleared,
    apply_form_submitted / coaching_apply_submitted,
  - Worker rejection / network error -> error message, submission id kept for
    an idempotent retry, apply_form_error / coaching_apply_error,
  - no request to formsubmit.co, ever,
  - a missing tier blocks before any request,
  - the tapped-label checkbox regression (hotfixed live 2026-09-30),
  - zero page errors throughout.

Skips (does not fail) when Playwright or a launchable Chromium is missing —
CI installs the Python package but no browser.
"""
from __future__ import annotations

import functools
import json
import re
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "wordpress"))

from generate_coaching_apply import (  # noqa: E402
    COACHING_INTAKE_WORKER_URL,
    generate_apply_page,
)

PAGE_ORIGIN = "https://roadielabs.com"
PAGE_URL = f"{PAGE_ORIGIN}/coaching/apply/"
UUID_RE = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$")


@functools.lru_cache(maxsize=1)
def _has_chromium() -> bool:
    """True only if Chromium actually launches (import alone is not enough:
    CI has the playwright package but no browser binaries)."""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        return False
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            browser.close()
        return True
    except Exception:  # noqa: BLE001 — any launch failure means "no browser"
        return False


pytestmark = pytest.mark.skipif(
    not _has_chromium(), reason="Playwright Chromium not installed/launchable")


@pytest.fixture(scope="module")
def page_html() -> str:
    return generate_apply_page()


@pytest.fixture(scope="module")
def browser():
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        b = p.chromium.launch()
        yield b
        b.close()


class Harness:
    """One phone-sized page with the Worker intercepted."""

    def __init__(self, browser, html, *, worker, query="?tier=mid"):
        self.worker_mode = worker
        self.worker_requests = []
        self.formsubmit_requests = []
        self.page_errors = []
        self.context = browser.new_context(viewport={"width": 390, "height": 844})
        self.page = self.context.new_page()
        self.page.on("pageerror", lambda exc: self.page_errors.append(str(exc)))
        self._html = html
        self.page.route("**/*", self._route)
        self.page.goto(PAGE_URL + query, wait_until="domcontentloaded")

    @staticmethod
    def _cors():
        return {
            "Access-Control-Allow-Origin": PAGE_ORIGIN,
            "Access-Control-Allow-Methods": "POST, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type",
        }

    def _route(self, route):
        request = route.request
        url = request.url
        if url.split("?")[0] == PAGE_URL and request.resource_type == "document":
            return route.fulfill(status=200, content_type="text/html; charset=utf-8",
                                 body=self._html)
        if url.rstrip("/") == COACHING_INTAKE_WORKER_URL.rstrip("/"):
            if request.method == "OPTIONS":
                return route.fulfill(status=204, headers=self._cors())
            self.worker_requests.append({
                "headers": request.headers,
                "body": request.post_data,
            })
            if self.worker_mode == "success":
                return route.fulfill(
                    status=201, headers=self._cors(), content_type="application/json",
                    body=json.dumps({"success": True, "case_id": "case-1",
                                     "state": "FIT_REVIEW", "receipt_sent": True,
                                     "duplicate": False}))
            if self.worker_mode == "rejected":
                return route.fulfill(
                    status=502, headers=self._cors(), content_type="application/json",
                    body=json.dumps({"error": "Could not submit. Please try again."}))
            return route.abort("failed")  # network error
        if "formsubmit.co" in url:
            self.formsubmit_requests.append(url)
        return route.abort()

    # ── Form filling through the real UI ──────────────────────────
    def fill_valid_application(self):
        page = self.page
        page.fill("#name", "Test Rider")
        page.fill("#email", "test.rider+apply@example.com")
        page.select_option("#sex", "female")
        page.fill("#age", "34")
        page.fill("#weight", "140")
        page.fill("#height_ft", "5")
        page.fill("#height_in", "6")
        page.fill("#rhr_baseline", "52")
        page.fill("#sleep_hours_baseline", "7.5")
        for select_id in ("years_cycling", "sleep_quality", "training_platform",
                          "trainer_access", "hours_per_week", "life_stress",
                          "checkin_frequency", "feedback_detail"):
            first_value = page.eval_on_selector(
                f"#{select_id}",
                "el => [...el.options].map(o => o.value).find(v => v)")
            page.select_option(f"#{select_id}", first_value)
        self.tap_radio("primary_goal", "specific_race")
        page.fill("#race_list", "Example Gran Fondo (June 2027) - A priority")
        page.fill("#success_definition", "Finish the long route with the front group")
        self.tap_radio("longest_ride", "4-6")
        self.tap_radio("recovery_speed", "normal")
        self.tap_radio("strength_current", "occasional")
        self.tap_radio("autonomy", "guided")
        self.tap_radio("missed_workout_response", "move_on")
        self.tap_option_label("long_ride_days", "saturday")
        self.tap_option_label("interval_days", "tuesday")
        self.tap_option_label("interval_days", "thursday")
        page.fill("#injuries", "Left knee, resolved")

    def tap_radio(self, name, value):
        self.page.click(f'.rl-apply-radio-option:has(input[name="{name}"][value="{value}"])')

    def tap_option_label(self, name, value):
        """Tap the option box away from the tiny checkbox — what a thumb does."""
        selector = f'.rl-apply-checkbox-option:has(input[name="{name}"][value="{value}"])'
        point = self.page.eval_on_selector(selector, """label => {
          const box = label.getBoundingClientRect();
          const input = label.querySelector('input').getBoundingClientRect();
          // Right-hand edge of the label unless the checkbox sits there.
          const x = (input.right < box.right - 4) ? box.width - 3 : 3;
          return {x: x, y: box.height / 2};
        }""")
        self.page.click(selector, position=point)

    def checked(self, name, value):
        return self.page.eval_on_selector(
            f'input[name="{name}"][value="{value}"]', "el => el.checked")

    def submit(self):
        self.page.click("#submit-btn")
        self.page.wait_for_function(
            "() => { const m = document.getElementById('message');"
            " return m && (m.classList.contains('success') || m.classList.contains('error')); }",
            timeout=10000)

    def message(self):
        return self.page.eval_on_selector(
            "#message", "el => ({cls: el.className, text: el.textContent})")

    def ga4_events(self):
        return self.page.evaluate(
            "() => (window.dataLayer || []).filter(a => a && a[0] === 'event')"
            ".map(a => a[1])")

    def storage(self, key):
        return self.page.evaluate(f"() => localStorage.getItem({json.dumps(key)})")

    def overflow_px(self):
        return self.page.evaluate(
            "() => document.documentElement.scrollWidth - window.innerWidth")

    def close(self):
        self.context.close()


@pytest.fixture
def harness(browser, page_html):
    made = []

    def make(**kwargs):
        h = Harness(browser, page_html, **kwargs)
        made.append(h)
        return h

    yield make
    for h in made:
        h.close()


def test_worker_success_posts_a_valid_payload(harness):
    h = harness(worker="success")
    assert h.page.eval_on_selector("#coaching_tier", "el => el.value") == "mid"
    assert h.overflow_px() <= 0, "layout must not scroll sideways at 390px"
    h.fill_valid_application()
    h.submit()

    msg = h.message()
    assert "success" in msg["cls"], msg
    assert "Application submitted." in msg["text"]
    assert h.page.eval_on_selector("#submit-btn", "el => el.textContent.trim()") == "Submitted"

    # Exactly one JSON post to the Worker, from the site's own Origin.
    assert len(h.worker_requests) == 1
    request = h.worker_requests[0]
    assert request["headers"].get("content-type", "").startswith("application/json")
    assert request["headers"].get("origin") == PAGE_ORIGIN
    body = json.loads(request["body"])
    assert body["tier"] == "mid"
    assert body["name"] == "Test Rider"
    assert body["email"] == "test.rider+apply@example.com"
    assert body["website"] == ""
    assert UUID_RE.match(body["submission_id"]), body["submission_id"]
    assert body["analytics_consent"] == "denied"
    assert body["home_timezone"], "timezone is filled from the browser"
    # The questionnaire the Worker forwards is every other answer.
    assert body["primary_goal"] == "specific_race"
    assert body["race_list"].startswith("Example Gran Fondo")
    assert body["long_ride_days"] == ["saturday"]
    assert body["interval_days"] == ["tuesday", "thursday"]
    assert body["injuries"] == "Left knee, resolved"
    assert body["age"] == "34"

    events = h.ga4_events()
    assert "apply_form_submitted" in events
    assert "coaching_apply_submitted" in events
    assert "apply_form_error" not in events
    assert h.storage("athlete_questionnaire_progress") is None
    assert h.storage("coaching_intake_submission_id") is None
    assert h.formsubmit_requests == []
    assert h.page_errors == []


@pytest.mark.parametrize("worker_mode", ["rejected", "network_error"])
def test_worker_failure_is_reported_and_retry_reuses_the_id(harness, worker_mode):
    h = harness(worker=worker_mode)
    h.fill_valid_application()
    h.submit()

    msg = h.message()
    assert "error" in msg["cls"], msg
    assert "couldn" in msg["text"]
    assert not h.page.eval_on_selector("#submit-btn", "el => el.disabled")

    events = h.ga4_events()
    assert "apply_form_error" in events
    assert "coaching_apply_error" in events
    assert "apply_form_submitted" not in events

    submission_id = h.storage("coaching_intake_submission_id")
    assert submission_id == json.loads(h.worker_requests[0]["body"])["submission_id"]
    h.page.click("#submit-btn")
    h.page.wait_for_function(
        "() => !document.getElementById('submit-btn').disabled", timeout=10000)
    assert len(h.worker_requests) == 2
    assert json.loads(h.worker_requests[1]["body"])["submission_id"] == submission_id
    assert h.formsubmit_requests == []
    assert h.page_errors == []


def test_missing_tier_blocks_before_any_request(harness):
    h = harness(worker="success", query="")
    assert h.page.eval_on_selector("#coaching_tier", "el => el.value") == ""
    h.fill_valid_application()
    h.page.click("#submit-btn")
    h.page.wait_for_timeout(300)
    assert h.worker_requests == []
    assert h.page.eval_on_selector("#coaching_tier", "el => el.validity.valueMissing")
    assert h.page_errors == []


def test_tapping_a_checkbox_label_checks_it_once(harness):
    h = harness(worker="success")
    h.tap_option_label("long_ride_days", "sunday")
    assert h.checked("long_ride_days", "sunday")
    h.tap_option_label("long_ride_days", "sunday")
    assert not h.checked("long_ride_days", "sunday")
    # Tapping the box itself still works.
    h.page.click('input[name="off_days"][value="monday"]')
    assert h.checked("off_days", "monday")
    # Device options (a vertical list) behave the same.
    h.tap_option_label("devices", "garmin")
    assert h.checked("devices", "garmin")
    # "Flexible" still clears specific days.
    h.tap_option_label("interval_days", "tuesday")
    h.tap_option_label("interval_days", "flexible")
    assert h.checked("interval_days", "flexible")
    assert not h.checked("interval_days", "tuesday")
    assert h.page_errors == []
