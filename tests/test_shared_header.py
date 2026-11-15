"""Tests for the shared site header module."""
from __future__ import annotations

import re
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "wordpress"))
from shared_header import get_site_header_css, get_site_header_html, get_site_header_js


class TestHeaderHTML:
    """Tests for get_site_header_html()."""

    def test_five_nav_items(self):
        html = get_site_header_html()
        for label in ["RACES", "PRODUCTS", "COURSES", "SERVICES", "ABOUT"]:
            assert f">{label}</a>" in html
        # RL-16: ARTICLES linked Gravel God's Substack; removed, no substitute.
        assert "ARTICLES" not in html

    def test_three_dropdown_containers(self):
        # RACES, PRODUCTS and SERVICES have dropdowns. SERVICES lost its
        # dropdown in the Jul 2026 whoops audit (its targets 404'd) and got
        # it back for RL-10 once /consulting/ was live.
        html = get_site_header_html()
        assert html.count('class="rl-site-header-item"') == 3

    def test_three_dropdowns(self):
        html = get_site_header_html()
        assert html.count('class="rl-site-header-dropdown"') == 3

    def test_services_dropdown_links_coaching_and_consulting(self):
        html = get_site_header_html()
        m = re.search(
            r'>SERVICES</a>\s*<div class="rl-site-header-dropdown">(.*?)</div>',
            html, re.DOTALL)
        assert m, "SERVICES has no dropdown"
        assert 'href="https://roadielabs.com/coaching/">Coaching</a>' in m.group(1)
        assert 'href="https://roadielabs.com/consulting/">Consulting</a>' in m.group(1)

    def test_about_has_no_dropdown(self):
        html = get_site_header_html()
        # ABOUT is a plain <a>, not inside a dropdown item
        about_idx = html.index(">ABOUT</a>")
        # Get the 200 chars before ABOUT — should NOT have rl-site-header-item
        context = html[max(0, about_idx - 200) : about_idx]
        last_item = context.rfind("rl-site-header-item")
        last_close = context.rfind("</div>")
        # The dropdown item should be closed before ABOUT
        assert last_close > last_item or last_item == -1

    def test_all_dropdown_links_present(self):
        html = get_site_header_html()
        expected = [
            "All Road Races",
            "How We Rate",
            "Custom Training Plans",
            "Courses",
            "Coaching",
            "Consulting",
        ]
        for label in expected:
            assert label in html, f"missing dropdown link {label}"


    def test_six_sub_links(self):
        html = get_site_header_html()
        dropdowns = re.findall(
            r'class="rl-site-header-dropdown">(.*?)</div>', html, re.DOTALL)
        assert sum(d.count("<a ") for d in dropdowns) == 6


    def test_logo_present(self):
        html = get_site_header_html()
        assert 'aria-label="Roadie Labs"' in html
        assert 'class="rl-site-header-logo"' in html
        assert 'class="rl-site-header-mark"' in html
        assert '<img' in html

    def test_logo_has_legible_wordmark_and_tire_mark(self):
        """The header must identify the brand even at navigation size."""
        html = get_site_header_html()
        assert 'src="/race/assets/rl-logo.svg?v=siped-1"' in html
        assert 'class="rl-site-header-wordmark"' in html
        assert 'ROADIE <span>LABS</span>' in html
        assert 'aria-label="Roadie Labs"' in html

    def test_courses_has_no_dropdown(self):
        html = get_site_header_html()
        # COURSES is a plain <a>, not inside a dropdown item
        courses_idx = html.index(">COURSES</a>")
        context = html[max(0, courses_idx - 200) : courses_idx]
        last_item = context.rfind("rl-site-header-item")
        last_close = context.rfind("</div>")
        # The dropdown item should be closed before COURSES
        assert last_close > last_item or last_item == -1

    def test_aria_current_when_active(self):
        for key in ["races", "products", "courses", "services", "about"]:
            html = get_site_header_html(active=key)
            assert 'aria-current="page"' in html

    def test_no_aria_current_when_no_active(self):
        html = get_site_header_html()
        assert 'aria-current="page"' not in html

    def test_aria_current_on_correct_item(self):
        html = get_site_header_html(active="services")
        # aria-current should be on SERVICES link
        assert 'aria-current="page">SERVICES</a>' in html
        # Not on others
        assert 'aria-current="page">RACES</a>' not in html

    def test_no_external_links(self):
        html = get_site_header_html()
        assert 'target="_blank"' not in html
        assert 'class="rl-external-indicator"' not in html

    def test_no_substack(self):
        html = get_site_header_html()
        assert "substack" not in html.lower()

    def test_correct_urls(self):
        html = get_site_header_html()
        assert "/road-races/" in html
        assert "/race/methodology/" in html
        assert "/training-plans/" in html
        assert "/coaching/" in html
        # Dead URLs must NOT be in the nav (whoops audit, Jul 2026).
        # /consulting/ went live and came back for RL-10 (2026-11-15).
        for dead in ("/guide/", "/articles/",
                     "/insights/", "/fueling-methodology/"):
            assert dead not in html, f"nav links dead URL {dead}"
        assert "/about/" in html
        assert "/courses/" in html


class TestHeaderCSS:
    """Tests for get_site_header_css()."""

    def test_no_raw_hex(self):
        css = get_site_header_css()
        # Remove comments before checking
        css_no_comments = re.sub(r'/\*.*?\*/', '', css)
        hex_matches = re.findall(r'#[0-9a-fA-F]{3,8}\b', css_no_comments)
        assert hex_matches == [], f"Raw hex found in CSS: {hex_matches}"

    @staticmethod
    def _rules_using(css, prop):
        return [
            (sel.strip(), body)
            for sel, body in re.findall(r'([^{}]+)\{([^}]*)\}', css)
            if prop in body
        ]

    def test_border_radius_only_on_glyph_tile(self):
        """Timing Slip: depth lives on the logo tile and its dot, nowhere else."""
        css = get_site_header_css()
        rules = self._rules_using(css, "border-radius")
        assert {sel for sel, _ in rules} == {".rl-site-header-tile", ".rl-site-header-dot"}
        for _, body in rules:
            value = re.search(r'border-radius:\s*([^;]+)', body).group(1)
            assert value.startswith("var(--rl-radius-") or value == "50%"

    def test_box_shadow_only_on_glyph_tile(self):
        css = get_site_header_css()
        rules = self._rules_using(css, "box-shadow")
        assert {sel for sel, _ in rules} == {".rl-site-header-tile", ".rl-site-header-dot"}
        for _, body in rules:
            assert "var(--rl-" in re.search(r'box-shadow:\s*([^;]+)', body).group(1)

    def test_dropdown_position_absolute(self):
        css = get_site_header_css()
        assert "position: absolute" in css

    def test_dropdown_z_index(self):
        css = get_site_header_css()
        assert "z-index" in css

    def test_uses_var_tokens(self):
        css = get_site_header_css()
        assert "var(--rl-color-" in css
        assert "var(--rl-font-data)" in css

    def test_hover_shows_dropdown(self):
        css = get_site_header_css()
        assert ":hover .rl-site-header-dropdown" in css

    def test_focus_within_shows_dropdown(self):
        css = get_site_header_css()
        assert ":focus-within .rl-site-header-dropdown" in css

    def test_mobile_uses_hamburger_nav(self):
        css = get_site_header_css()
        assert "max-width: 600px" in css
        assert ".rl-site-header-toggle" in css
        assert "width: 44px" in css
        assert "height: 44px" in css
        assert ".rl-site-header-nav.is-open" in css

    def test_header_js_uses_event_listener(self):
        js = get_site_header_js()
        assert "addEventListener('click'" in js
        assert "onclick" not in js

    def test_responsive_breakpoint(self):
        css = get_site_header_css()
        assert "@media" in css

    def test_max_width_1200(self):
        css = get_site_header_css()
        assert "max-width: 1200px" in css

    def test_dropdown_border(self):
        css = get_site_header_css()
        assert "2px solid" in css

    def test_cool_white_background(self):
        css = get_site_header_css()
        assert "var(--rl-color-cool-white)" in css


class TestMenuIcon:
    """The phone menu button must draw three visible lines (Nov 2026: it
    rendered as an empty box because flex-shrink squeezed the lines to 0px)."""

    @staticmethod
    def _rule(css: str, selector: str) -> str:
        m = re.search(re.escape(selector) + r"\s*\{([^}]*)\}", css)
        assert m, f"missing rule {selector}"
        return m.group(1)

    @staticmethod
    def _px(rule: str, prop: str) -> int:
        m = re.search(r"(?:^|;)\s*" + prop + r":\s*(\d+)px", rule)
        assert m, f"missing {prop}"
        return int(m.group(1))

    def test_toggle_has_three_line_spans(self):
        html = get_site_header_html()
        m = re.search(r'<button class="rl-site-header-toggle"[^>]*>(.*?)</button>', html, re.S)
        assert m
        assert m.group(1).count("<span></span>") == 3

    def test_lines_are_drawn_and_never_shrink(self):
        line = self._rule(get_site_header_css(), ".rl-site-header-toggle span")
        assert "flex: none" in line
        assert self._px(line, "height") >= 2
        assert self._px(line, "width") > 0
        assert "background: var(--rl-color-dark-navy)" in line

    def test_lines_fit_inside_the_button(self):
        css = get_site_header_css()
        base = self._rule(css, ".rl-site-header-toggle")
        line = self._rule(css, ".rl-site-header-toggle span")
        phone = css.split("@media (max-width: 600px)", 1)[1]
        phone_toggle = self._rule(phone, ".rl-site-header-toggle")
        content = self._px(base, "height") - 2 * self._px(base, "padding") - 2 * 2  # 2px border
        stack = 3 * self._px(line, "height") + 2 * self._px(phone_toggle, "gap")
        assert stack <= content
        assert "display: inline-flex" in phone_toggle

    def test_tap_opens_the_nav(self):
        js = get_site_header_js()
        assert "classList.toggle('is-open'" in js
        assert "aria-expanded" in js
