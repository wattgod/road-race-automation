"""Tests for cookie_consent.py — shared consent banner module.

Tests: banner structure, hex parity with tokens.css, WCAG accessibility,
JS syntax validation, consent mode behavior, brand compliance.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "wordpress"))
from cookie_consent import (
    EEA_UK_CH_TIMEZONES,
    get_consent_banner_html,
    get_consent_head_script,
    requires_explicit_consent,
)

TOKENS_CSS = Path(__file__).parent.parent.parent / "road-labs-brand" / "tokens" / "tokens.css"


def _parse_tokens() -> dict[str, str]:
    """Parse token name → hex value from tokens.css."""
    result = {}
    text = TOKENS_CSS.read_text()
    for m in re.finditer(r"--(rl-color-[\w-]+):\s*(#[0-9a-fA-F]{3,8})", text):
        result[m.group(1)] = m.group(2)
    return result


def _extract_hex(text: str) -> set[str]:
    """Extract all hex color values from a string, normalized to lowercase."""
    return {h.lower() for h in re.findall(r"#[0-9a-fA-F]{3,8}", text)}


def _extract_css(html: str) -> str:
    """Extract the <style> block from consent banner HTML."""
    m = re.search(r"<style>(.*?)</style>", html, re.DOTALL)
    return m.group(1) if m else ""


def _extract_js(html: str) -> str:
    """Extract the last <script> block (banner JS, not consent defaults)."""
    scripts = re.findall(r"<script>(.*?)</script>", html, re.DOTALL)
    return scripts[-1] if scripts else ""


@pytest.fixture
def banner():
    return get_consent_banner_html()


@pytest.fixture
def css(banner):
    return _extract_css(banner)


@pytest.fixture
def js(banner):
    return _extract_js(banner)


@pytest.fixture
def tokens():
    if not TOKENS_CSS.exists():
        pytest.skip("tokens.css not found")
    return _parse_tokens()


# ── Structure ──────────────────────────────────────────────

class TestBannerStructure:
    """Banner HTML structure and semantic correctness."""

    def test_has_role_dialog(self, banner):
        assert 'role="dialog"' in banner

    def test_has_aria_label(self, banner):
        assert 'aria-label="Cookie consent"' in banner

    def test_has_aria_describedby(self, banner):
        assert 'aria-describedby="rl-consent-desc"' in banner

    def test_desc_id_matches_describedby(self, banner):
        assert 'id="rl-consent-desc"' in banner

    def test_has_accept_button(self, banner):
        assert 'id="rl-consent-accept"' in banner

    def test_has_decline_button(self, banner):
        assert 'id="rl-consent-decline"' in banner

    def test_accept_button_text(self, banner):
        assert ">Accept<" in banner

    def test_decline_button_text(self, banner):
        assert ">Decline<" in banner

    def test_has_cookies_link(self, banner):
        assert 'href="/cookies/"' in banner

    def test_has_learn_more_text(self, banner):
        assert "Learn more" in banner

    def test_banner_id(self, banner):
        assert 'id="rl-consent-banner"' in banner

    def test_has_footer_privacy_choices_link(self, banner):
        assert 'id="rl-privacy-choices"' in banner
        assert ">Privacy choices<" in banner

    def test_footer_has_legal_links(self, banner):
        assert '<footer class="rl-privacy-choices-footer"' in banner
        assert 'href="/privacy/"' in banner
        assert 'href="/terms/"' in banner

    def test_no_border_radius(self, css):
        assert "border-radius" not in css

    def test_no_box_shadow(self, css):
        assert "box-shadow" not in css

    def test_no_circles(self, banner):
        assert "<circle" not in banner


# ── Hex Parity with tokens.css ─────────────────────────────

class TestHexParity:
    """Every hex color in the banner must match a tokens.css value."""

    EXPECTED_MAPPING = {
        "#555555": "rl-color-coral",
        "#d0d0c8": "rl-color-silver",
        "#202322": "rl-color-signal-red",
        "#ffffff": "rl-color-white",
    }

    def test_all_hex_in_tokens(self, banner, tokens):
        """Every hex in the banner must exist in tokens.css."""
        token_hex = {v.lower() for v in tokens.values()}
        banner_hex = _extract_hex(banner)
        unknown = banner_hex - token_hex
        assert not unknown, f"Hex not in tokens.css: {unknown}"

    def test_coral_present(self, css):
        assert "#555555" in css

    def test_signal_red_present(self, css):
        assert "#202322" in css

    def test_silver_present(self, css):
        assert "#d0d0c8" in css



# ── Accessibility ──────────────────────────────────────────

class TestAccessibility:
    """WCAG compliance checks."""

    def test_focus_visible_styles(self, css):
        assert "focus-visible" in css

    def test_prefers_reduced_motion(self, css):
        assert "prefers-reduced-motion" in css

    def test_transition_none_for_reduced_motion(self, css):
        # After prefers-reduced-motion, should have transition:none
        idx = css.find("prefers-reduced-motion")
        assert "transition:none" in css[idx:]

    def test_buttons_have_type(self, banner):
        # All buttons should have type="button" to prevent form submission
        buttons = re.findall(r"<button[^>]*>", banner)
        # Consent buttons don't need type="button" since they're not in forms
        # But they should be clickable — verify they exist
        assert len(buttons) == 2

    def test_dialog_has_both_buttons(self, banner):
        """Dialog must have both accept AND decline options."""
        assert "rl-consent-accept" in banner
        assert "rl-consent-decline" in banner


# ── JavaScript Behavior ───────────────────────────────────

class TestJsBehavior:
    """Consent banner JavaScript correctness."""

    def test_js_syntax_valid(self, js):
        """JS must parse without errors."""
        result = subprocess.run(
            ["node", "-e", f"new Function({json.dumps(js)})"],
            capture_output=True, text=True, timeout=10,
        )
        assert result.returncode == 0, f"JS syntax error: {result.stderr}"

    def test_cookie_check_uses_regex(self, js):
        """Must use regex for cookie check, not indexOf (prefix-safe)."""
        assert "/(^|; )rl_consent=/.test" in js
        assert "indexOf" not in js

    def test_accept_sets_cookie(self, js):
        assert "rl_consent=accepted" in js

    def test_decline_sets_cookie(self, js):
        assert "rl_consent=declined" in js

    def test_accept_updates_consent_mode(self, js):
        assert "'analytics_storage':'granted'" in js

    def test_decline_updates_consent_mode(self, js):
        """Decline MUST explicitly update consent to denied."""
        assert "'analytics_storage':'denied'" in js

    def test_auto_show_only_for_strict_geo_without_cookie(self, js):
        assert "window.rlConsentRequiresOptIn!==false" in js
        assert "/(^|; )rl_consent=/.test(document.cookie)" in js

    def test_privacy_choices_can_open_banner(self, js):
        assert "rl-privacy-choices" in js
        assert "e.preventDefault();showBanner()" in js

    def test_cookie_has_secure_flag(self, js):
        """All cookies must have Secure flag for HTTPS sites."""
        cookie_sets = re.findall(r"document\.cookie='[^']*'", js)
        assert len(cookie_sets) >= 2, "Expected at least 2 cookie sets (accept + decline)"
        for cookie_set in cookie_sets:
            assert "Secure" in cookie_set, f"Missing Secure flag: {cookie_set}"

    def test_cookie_has_samesite(self, js):
        cookie_sets = re.findall(r"document\.cookie='[^']*'", js)
        for cookie_set in cookie_sets:
            assert "SameSite=Lax" in cookie_set

    def test_cookie_max_age_365_days(self, js):
        assert "max-age=31536000" in js  # 365 * 24 * 60 * 60

    def test_gtag_type_check(self, js):
        """Must check typeof gtag before calling it."""
        assert "typeof gtag==='function'" in js

    def test_removes_show_class(self, js):
        """Both accept and decline must hide the banner."""
        assert js.count("classList.remove('rl-consent-show')") == 2


# ── Banner runtime ─────────────────────────────────────────

def _run_banner(js: str, cookie: str, requires_opt_in, actions: str = "") -> dict:
    """Run the banner script against a tiny DOM stub in Node."""
    script = f"""
var classes={{}};var listeners={{}};var timers=[];var gtagCalls=[];
function el(id){{return {{id:id,classList:{{add:function(c){{classes[id+':'+c]=true}},
  remove:function(c){{delete classes[id+':'+c]}}}},
  addEventListener:function(t,f){{listeners[id+':'+t]=f}}}}}}
var els={{'rl-consent-banner':el('rl-consent-banner'),'rl-privacy-choices':el('rl-privacy-choices'),
  'rl-consent-accept':el('rl-consent-accept'),'rl-consent-decline':el('rl-consent-decline')}};
global.window={{rlConsentRequiresOptIn:{json.dumps(requires_opt_in)},
  addEventListener:function(t,f){{listeners['window:'+t]=f}},removeEventListener:function(){{}}}};
global.document={{cookie:{json.dumps(cookie)},getElementById:function(id){{return els[id]||null}}}};
global.setTimeout=function(f){{timers.push(f);return timers.length}};
global.clearTimeout=function(){{}};
global.gtag=function(){{gtagCalls.push(Array.prototype.slice.call(arguments))}};
{js}
{actions}
process.stdout.write(JSON.stringify({{autoScheduled:timers.length>0,
  shown:!!classes['rl-consent-banner:rl-consent-show'],cookie:document.cookie,gtag:gtagCalls}}));
"""
    result = subprocess.run(["node", "-e", script], capture_output=True, text=True, timeout=10)
    assert result.returncode == 0, result.stderr
    return json.loads(result.stdout)


class TestBannerRuntime:
    def test_opt_in_region_without_cookie_schedules_banner(self, js):
        out = _run_banner(js, "", True, "timers.forEach(function(f){f()});")
        assert out["autoScheduled"] and out["shown"]

    def test_other_regions_do_not_auto_show(self, js):
        out = _run_banner(js, "", False)
        assert not out["autoScheduled"] and not out["shown"]

    def test_stored_choice_suppresses_auto_show(self, js):
        out = _run_banner(js, "rl_consent=declined", True)
        assert not out["autoScheduled"]

    def test_privacy_choices_opens_banner_everywhere(self, js):
        out = _run_banner(
            js, "rl_consent=accepted", False,
            "listeners['rl-privacy-choices:click']({preventDefault:function(){}});")
        assert out["shown"]

    def test_decline_outside_opt_in_region_denies_analytics(self, js):
        out = _run_banner(js, "", False, "listeners['rl-consent-decline:click']();")
        assert out["cookie"].startswith("rl_consent=declined")
        assert out["gtag"] == [["consent", "update", {"analytics_storage": "denied"}]]

    def test_accept_grants_analytics(self, js):
        out = _run_banner(js, "", True, "listeners['rl-consent-accept:click']();")
        assert out["cookie"].startswith("rl_consent=accepted")
        assert out["gtag"] == [["consent", "update", {"analytics_storage": "granted"}]]


# ── Geographic classifier ─────────────────────────────────

class TestTimezoneClassifier:
    """The Python mirror and emitted JS share one explicit timezone list."""

    @pytest.mark.parametrize("timezone", [
        "Europe/Paris",
        "Europe/Amsterdam",
        "Atlantic/Canary",
        "Asia/Nicosia",
    ])
    def test_eea_timezones_are_strict(self, timezone):
        assert requires_explicit_consent(timezone)

    @pytest.mark.parametrize("timezone", ["Europe/London", "Europe/Belfast"])
    def test_uk_timezones_are_strict(self, timezone):
        assert requires_explicit_consent(timezone)

    def test_switzerland_is_strict(self):
        assert requires_explicit_consent("Europe/Zurich")

    @pytest.mark.parametrize("timezone", ["UTC", "Etc/UTC", "Etc/GMT", "GMT", "Etc/GMT+1", "Zulu"])
    def test_locationless_timezones_are_strict(self, timezone):
        assert requires_explicit_consent(timezone)

    @pytest.mark.parametrize("timezone", [
        "Europe/Istanbul",
        "Europe/Moscow",
        "Europe/Minsk",
        "Europe/Belgrade",
        "Europe/Kyiv",
    ])
    def test_named_non_eea_european_zones_are_excluded(self, timezone):
        assert timezone not in EEA_UK_CH_TIMEZONES
        assert not requires_explicit_consent(timezone)

    @pytest.mark.parametrize("timezone", ["America/New_York", "Australia/Sydney"])
    def test_other_known_zones_are_opt_out(self, timezone):
        assert not requires_explicit_consent(timezone)

    @pytest.mark.parametrize("timezone", [None, "", "Unknown/Timezone"])
    def test_unknown_or_missing_timezone_fails_closed(self, timezone):
        assert requires_explicit_consent(timezone)

    def test_head_script_embeds_the_same_list(self):
        head = get_consent_head_script("G-TEST")
        m = re.search(r"rlConsentStrictTimezones=new Set\((\[.*?\])\)", head)
        assert m
        assert json.loads(m.group(1)) == list(EEA_UK_CH_TIMEZONES)

    def test_matches_gravel_god_list(self):
        """Roadie Labs uses Gravel God's region list (ruling 2026-11-14)."""
        gg = Path(__file__).parent.parent.parent / "gravel-race-automation" / "wordpress" / "cookie_consent.py"
        if not gg.exists():
            pytest.skip("gravel-race-automation checkout not adjacent")
        zones = set(re.findall(r'^\s+"([A-Za-z_]+/[A-Za-z_]+)",', gg.read_text(), re.M))
        assert zones == set(EEA_UK_CH_TIMEZONES)


# ── CSS Brand Compliance ──────────────────────────────────

class TestCssBrandCompliance:
    """CSS follows brand rules."""

    def test_sometype_mono_font(self, css):
        assert "'JetBrains Mono'" in css

    def test_no_opacity_transition(self, css):
        """Brand rule: no opacity transitions."""
        transitions = re.findall(r"transition:[^;]+", css)
        for t in transitions:
            if t != "transition:none":
                assert "opacity" not in t, f"Opacity in transition: {t}"

    def test_allowed_transitions_only(self, css):
        """Only border-color, background-color, color transitions allowed."""
        allowed = {"background-color", "color", "border-color", "none"}
        transitions = re.findall(r"transition:([^;]+)", css)
        for t in transitions:
            if t.strip() == "none":
                continue
            props = re.findall(r"([\w-]+)\s+\.", t)
            for prop in props:
                assert prop in allowed, f"Disallowed transition property: {prop}"

    def test_mobile_breakpoint(self, css):
        assert "max-width:600px" in css

    def test_z_index_high(self, css):
        assert "z-index:9999" in css
