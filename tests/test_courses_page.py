"""Tests for the Roadie Labs /courses/ cross-sell page generator."""
from __future__ import annotations

import re
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "wordpress"))

from generate_courses_page import (
    BUNDLE_PRICE,
    BUNDLE_URL,
    DIRT_CRAFT_PRICE,
    DIRT_CRAFT_URL,
    HYDRATION_PRICE,
    HYDRATION_URL,
    build_bundle_strip,
    build_course_cards,
    build_courses_css,
    build_courses_js,
    build_faq,
    build_frame,
    build_hero,
    build_jsonld,
    build_nav,
    generate_courses_page,
)
from brand_tokens import GA_MEASUREMENT_ID


@pytest.fixture(scope="module")
def page_html():
    return generate_courses_page()


# ── Page generation ───────────────────────────────────────────


class TestPageGenerates:
    def test_page_is_nonempty_html(self, page_html):
        assert page_html.startswith("<!DOCTYPE html>")
        assert len(page_html) > 10_000

    def test_title_present(self, page_html):
        assert "<title>Courses" in page_html

    def test_canonical_url(self, page_html):
        assert '<link rel="canonical" href="https://roadielabs.com/courses/">' in page_html

    def test_meta_description(self, page_html):
        assert '<meta name="description"' in page_html

    def test_indexable(self, page_html):
        assert '<meta name="robots" content="index, follow">' in page_html

    def test_jsonld_present(self, page_html):
        assert 'application/ld+json' in page_html
        assert '"FAQPage"' in page_html

    def test_consent_banner_present(self, page_html):
        assert "rl_consent" in page_html


# ── Analytics ─────────────────────────────────────────────────


class TestAnalytics:
    def test_ga4_snippet_present(self, page_html):
        assert GA_MEASUREMENT_ID in page_html
        assert "googletagmanager.com/gtag/js" in page_html

    def test_crosssell_event_wired(self, page_html):
        assert "course_crosssell_click" in page_html
        assert "course_id" in page_html

    def test_event_uses_addeventlistener(self):
        js = build_courses_js()
        assert "addEventListener" in js
        assert "course_crosssell_click" in js

    def test_cta_data_attributes(self, page_html):
        for course_id in ["hydration_mastery", "dirt_craft", "bundle"]:
            assert f'data-course-cta="{course_id}"' in page_html

    def test_gtag_guarded(self):
        js = build_courses_js()
        # gtag must be feature-checked, never assumed
        assert "typeof gtag === 'function'" in js


# ── No inline handlers ────────────────────────────────────────


class TestNoInlineHandlers:
    def test_no_inline_event_handlers(self, page_html):
        matches = re.findall(r'\son(click|load|mouseover|submit|change|toggle|error)\s*=', page_html)
        assert matches == [], f"Inline event handlers found: {matches}"

    def test_no_javascript_urls(self, page_html):
        assert "javascript:" not in page_html


# ── Brand / styling ───────────────────────────────────────────


class TestBrandCompliance:
    def test_no_raw_hex_in_courses_css(self):
        css = build_courses_css()
        css_no_comments = re.sub(r'/\*.*?\*/', '', css)
        hex_matches = re.findall(r'#[0-9a-fA-F]{3,8}\b', css_no_comments)
        assert hex_matches == [], f"Raw hex found in courses CSS: {hex_matches}"

    def test_no_border_radius(self):
        css = build_courses_css()
        assert "border-radius" not in css

    def test_no_box_shadow(self):
        css = build_courses_css()
        assert "box-shadow" not in css

    def test_uses_rl_tokens(self):
        css = build_courses_css()
        assert "var(--rl-color-" in css
        assert "var(--rl-font-data)" in css
        assert "var(--rl-font-editorial)" in css

    def test_fonts_present(self, page_html):
        # Standalone build embeds full page CSS with @font-face declarations
        assert "Sometype Mono" in page_html
        assert "Source Serif 4" in page_html

    def test_header_present(self, page_html):
        assert 'class="rl-site-header"' in page_html

    def test_courses_nav_item_active(self, page_html):
        assert 'aria-current="page">COURSES</a>' in page_html

    def test_footer_present(self, page_html):
        assert 'class="rl-mega-footer"' in page_html

    def test_responsive_breakpoint(self):
        css = build_courses_css()
        assert "@media (max-width: 768px)" in css


# ── Cross-sell content ────────────────────────────────────────


class TestCrossSellContent:
    def test_hydration_cta_url(self, page_html):
        assert HYDRATION_URL == "https://gravelgodcycling.com/course/gravel-hydration-mastery/"
        assert HYDRATION_URL in page_html

    def test_dirt_craft_cta_url(self, page_html):
        assert DIRT_CRAFT_URL == "https://gravelgodcycling.com/course/dirt-craft/"
        assert DIRT_CRAFT_URL in page_html

    def test_bundle_cta_url(self, page_html):
        assert BUNDLE_URL == "https://gravelgodcycling.com/course/"
        assert BUNDLE_URL in page_html

    def test_prices(self, page_html):
        assert HYDRATION_PRICE == 19
        assert DIRT_CRAFT_PRICE == 29
        assert BUNDLE_PRICE == 39
        assert "$19" in page_html
        assert "$29" in page_html
        assert "$39" in page_html

    def test_lesson_counts(self, page_html):
        assert "8 interactive lessons" in page_html
        assert "12 lessons + 4 module quizzes" in page_html

    def test_sister_brand_disclosure(self, page_html):
        # Honest cross-brand framing must be present
        assert "Gravel God Cycling" in page_html
        assert "sister brand" in page_html

    def test_no_defensive_messaging(self, page_html):
        # Never plant doubt with "no sponsors / no affiliates" framing
        lowered = page_html.lower()
        assert "no sponsors" not in lowered
        assert "no affiliates" not in lowered
        assert "not an affiliate" not in lowered

    def test_no_exclamation_marks_in_copy(self):
        # Brand voice: dry, editorial, no hype. Check copy-bearing builders.
        for builder in [build_hero, build_frame, build_course_cards, build_bundle_strip, build_faq]:
            assert "!" not in builder(), f"Exclamation mark in {builder.__name__}"

    def test_faq_three_items(self, page_html):
        assert page_html.count('class="rl-courses-faq-item"') == 3

    def test_faq_content(self, page_html):
        assert "lifetime access" in page_html
        assert "30-day money-back" in page_html
        assert "gravel bike" in page_html


# ── Structure ─────────────────────────────────────────────────


class TestStructure:
    def test_breadcrumb(self):
        nav = build_nav()
        assert "rl-breadcrumb" in nav
        assert "Courses" in nav

    def test_hero_kicker(self):
        hero = build_hero()
        assert ">COURSES</div>" in hero

    def test_two_course_cards(self, page_html):
        assert page_html.count('class="rl-course-card"') == 2

    def test_bundle_strip(self, page_html):
        assert 'class="rl-courses-bundle"' in page_html

    def test_jsonld_valid_json(self):
        import json as _json

        jsonld = build_jsonld()
        blocks = re.findall(
            r'<script type="application/ld\+json">(.*?)</script>', jsonld, re.DOTALL
        )
        assert len(blocks) == 2
        for block in blocks:
            _json.loads(block)
