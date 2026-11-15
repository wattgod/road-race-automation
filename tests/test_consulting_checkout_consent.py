"""Consulting checkout reports the visitor's effective analytics consent.

The fulfilment pipeline sends a server-side GA4 ``purchase`` for every
checkout whose ``analytics_consent`` is not exactly ``denied`` (a missing
field reads as ``unknown``). The consulting checkout used to post no consent
field, so a visitor who clicked Decline still got a purchase recorded.

Two layers:
- Node: the shared ``ANALYTICS_CONSENT_STATE_JS`` rule, and its parity with the
  static plan form's copy (``analyticsConsentGranted``).
- Chromium: the generated /consulting/ page, served at its real origin with
  the pipeline intercepted (nothing leaves the machine), posts the right
  ``analytics_consent`` for a declined, an EEA no-choice, a US no-choice and
  an accepted visitor. Skips when no launchable Chromium is installed.
"""
from __future__ import annotations

import functools
import itertools
import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "wordpress"))

from cookie_consent import ANALYTICS_CONSENT_STATE_JS  # noqa: E402
from generate_consulting import generate_consulting_page  # noqa: E402
from test_region_aware_consent import _extract_function  # noqa: E402

PAGE_ORIGIN = "https://roadielabs.com"
PAGE_URL = f"{PAGE_ORIGIN}/consulting/"
CHECKOUT_API = ("https://athlete-custom-training-plan-pipeline-production.up.railway.app"
                "/api/create-consulting-checkout")

COOKIES = ("", "rl_consent=declined", "rl_consent=accepted",
           "other=1; rl_consent=declined", "other=1; rl_consent=accepted")
FLAGS = (True, False, None)  # None: head script missing, flag never set


def _node(script: str) -> str:
    result = subprocess.run(["node", "-e", script], capture_output=True, text=True, timeout=10)
    assert result.returncode == 0, result.stderr
    return result.stdout


def _env(cookie: str, flag) -> str:
    set_flag = "" if flag is None else f"window.rlConsentRequiresOptIn={json.dumps(flag)};"
    return f"global.window={{}};{set_flag}global.document={{cookie:{json.dumps(cookie)}}};"


class TestSharedRule:
    @pytest.mark.parametrize(
        ("cookie", "requires_opt_in", "expected"),
        [
            ("rl_consent=declined", False, "denied"),  # declined wins outside EEA
            ("rl_consent=declined", True, "denied"),
            ("", True, "denied"),                      # EEA/UK/CH, no choice
            ("", None, "denied"),                      # head script missing
            ("", False, "granted"),                    # outside opt-in regions
            ("rl_consent=accepted", True, "granted"),  # accepted in EEA
        ],
    )
    def test_rule(self, cookie, requires_opt_in, expected):
        out = _node(_env(cookie, requires_opt_in) + ANALYTICS_CONSENT_STATE_JS
                    + "\nprocess.stdout.write(analyticsConsentState());")
        assert out == expected

    def test_plan_form_copy_gives_the_same_answers(self):
        form_fn = _extract_function(
            (ROOT / "web" / "training-plans-form.js").read_text(encoding="utf-8"),
            "analyticsConsentGranted")
        for cookie, flag in itertools.product(COOKIES, FLAGS):
            shared = _node(_env(cookie, flag) + ANALYTICS_CONSENT_STATE_JS
                           + "\nprocess.stdout.write(analyticsConsentState());")
            form = _node(_env(cookie, flag) + form_fn
                         + "\nprocess.stdout.write(analyticsConsentGranted()?'granted':'denied');")
            assert shared == form, (cookie, flag)

    def test_consulting_and_apply_embed_the_shared_rule_once(self):
        from generate_coaching_apply import generate_apply_page

        for html in (generate_consulting_page(), generate_apply_page()):
            assert html.count("function analyticsConsentState") == 1
            assert ANALYTICS_CONSENT_STATE_JS in html

    def test_consulting_checkout_posts_consent(self):
        html = generate_consulting_page()
        assert "analytics_consent:analyticsConsentState()" in html


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


@pytest.fixture(scope="module")
def browser():
    if not _has_chromium():
        pytest.skip("Playwright Chromium not installed/launchable")
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        b = p.chromium.launch()
        yield b
        b.close()


@pytest.fixture(scope="module")
def page_html() -> str:
    return generate_consulting_page()


def _checkout_body(browser, html, *, timezone_id, cookie_value=None) -> dict:
    context = browser.new_context(viewport={"width": 390, "height": 844},
                                  timezone_id=timezone_id)
    if cookie_value:
        context.add_cookies([{"name": "rl_consent", "value": cookie_value,
                              "url": PAGE_ORIGIN}])
    requests, errors = [], []
    page = context.new_page()
    page.on("pageerror", lambda exc: errors.append(str(exc)))

    def route(r):
        req = r.request
        if req.url.split("?")[0] == PAGE_URL and req.resource_type == "document":
            return r.fulfill(status=200, content_type="text/html; charset=utf-8", body=html)
        if req.url == CHECKOUT_API:
            cors = {"Access-Control-Allow-Origin": PAGE_ORIGIN,
                    "Access-Control-Allow-Methods": "POST, OPTIONS",
                    "Access-Control-Allow-Headers": "Content-Type"}
            if req.method == "OPTIONS":
                return r.fulfill(status=204, headers=cors)
            requests.append(req.post_data)
            # No checkout_url: the page shows its error instead of navigating away.
            return r.fulfill(status=200, headers=cors, content_type="application/json",
                             body=json.dumps({"error": "intercepted in test"}))
        return r.abort()

    try:
        page.route("**/*", route)
        page.goto(PAGE_URL, wait_until="domcontentloaded")
        page.fill("#consult-name", "Test Rider")
        page.fill("#consult-email", "test.rider+consult@example.com")
        page.click("#checkout .rl-consult-form-submit")
        page.wait_for_function(
            "() => getComputedStyle(document.querySelector("
            "'#checkout .rl-consult-form-message')).display !== 'none'",
            timeout=10000)
        assert not errors, errors
        assert len(requests) == 1, requests
        return json.loads(requests[0])
    finally:
        context.close()


class TestConsultingCheckoutInBrowser:
    def test_declined_visitor_sends_denied(self, browser, page_html):
        body = _checkout_body(browser, page_html, timezone_id="America/Chicago",
                              cookie_value="declined")
        assert body["analytics_consent"] == "denied"

    def test_eea_visitor_without_a_choice_sends_denied(self, browser, page_html):
        body = _checkout_body(browser, page_html, timezone_id="Europe/Paris")
        assert body["analytics_consent"] == "denied"

    def test_us_visitor_without_a_choice_sends_granted(self, browser, page_html):
        body = _checkout_body(browser, page_html, timezone_id="America/Chicago")
        assert body["analytics_consent"] == "granted"

    def test_accepted_visitor_sends_granted(self, browser, page_html):
        body = _checkout_body(browser, page_html, timezone_id="Europe/Paris",
                              cookie_value="accepted")
        assert body["analytics_consent"] == "granted"
        assert body["hours"] == 1
        assert body["plan_addon"] is False
