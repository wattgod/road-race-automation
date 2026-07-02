"""Tests for the shared site header module."""
from __future__ import annotations

import re
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "wordpress"))
from shared_header import get_site_header_css, get_site_header_html


class TestHeaderHTML:
    """Tests for get_site_header_html()."""

    def test_six_nav_items(self):
        html = get_site_header_html()
        for label in ["RACES", "PRODUCTS", "COURSES", "SERVICES", "ARTICLES", "ABOUT"]:
            assert f">{label}</a>" in html

    def test_two_dropdown_containers(self):
        # RACES + PRODUCTS keep dropdowns; SERVICES/ARTICLES became plain
        # links in the Jul 2026 whoops audit (their dropdown targets 404'd).
        html = get_site_header_html()
        assert html.count('class="rl-site-header-item"') == 2

    def test_two_dropdowns(self):
        html = get_site_header_html()
        assert html.count('class="rl-site-header-dropdown"') == 2

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
        ]
        for label in expected:
            assert label in html, f"missing dropdown link {label}"


    def test_four_sub_links(self):
        html = get_site_header_html()
        dropdowns = re.findall(
            r'class="rl-site-header-dropdown">(.*?)</div>', html, re.DOTALL)
        assert sum(d.count("<a ") for d in dropdowns) == 4


    def test_logo_present(self):
        html = get_site_header_html()
        assert 'alt="Roadie Labs"' in html  # TODO: update to road-labs-logo when asset exists
        assert 'class="rl-site-header-logo"' in html

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
        for key in ["races", "products", "courses", "services", "articles", "about"]:
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

    def test_external_links_have_target_blank(self):
        html = get_site_header_html()
        # Substack link should have target and rel
        assert 'target="_blank"' in html
        assert 'rel="noopener"' in html

    def test_substack_url(self):
        html = get_site_header_html()
        assert "gravelgodcycling.substack.com" in html  # TODO: update when newsletter URL exists

    def test_correct_urls(self):
        html = get_site_header_html()
        assert "/road-races/" in html
        assert "/race/methodology/" in html
        assert "/products/training-plans/" in html
        assert "/coaching/" in html
        # Dead URLs must NOT be in the nav (whoops audit, Jul 2026)
        for dead in ("/guide/", "/consulting/", "/articles/",
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

    def test_no_border_radius(self):
        css = get_site_header_css()
        assert "border-radius" not in css

    def test_no_box_shadow(self):
        css = get_site_header_css()
        assert "box-shadow" not in css

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

    def test_mobile_hides_dropdowns(self):
        css = get_site_header_css()
        assert "max-width: 600px" in css
        assert "display: none !important" in css

    def test_responsive_breakpoint(self):
        css = get_site_header_css()
        assert "@media" in css

    def test_max_width_960(self):
        css = get_site_header_css()
        assert "max-width: 960px" in css

    def test_dropdown_border(self):
        css = get_site_header_css()
        assert "2px solid" in css

    def test_cool_white_background(self):
        css = get_site_header_css()
        assert "var(--rl-color-cool-white)" in css
