"""Tests for the Roadie Labs coaching page + coaching apply page generators.

Coaching page rewritten 2026-07-18 into "The Dossier" structure: hero →
terms → tiers → fit → results → faq → final-cta (replacing the old band
sequence hero → problem → deliverables → how-it-works → tiers →
testimonials → honest-check → faq → final-cta). This suite describes the
page as it now ships, not the old one — no skipped/xfailed placeholders
for deleted sections.

Modeled on gravel-race-automation/tests/test_coaching.py (the approved
rebuild's test suite), adapted for Roadie Labs: rl- class prefix, road
URLs, GA4 property G-WQ7W8XN11N, and no wordpress/slop_rules module on
road (assertions are written directly instead of via slop_rules.check_text).
"""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

import pytest

# Add wordpress/ to path so we can import the generators
WORDPRESS_DIR = Path(__file__).parent.parent / "wordpress"
sys.path.insert(0, str(WORDPRESS_DIR))

from generate_coaching import (
    QUESTIONNAIRE_URL,
    build_nav,
    build_hero,
    build_terms,
    build_tiers,
    build_honest_check,
    build_faq,
    build_application_close,
    build_footer,
    build_mobile_sticky_cta,
    build_coaching_css,
    build_coaching_js,
    build_jsonld,
    generate_coaching_page,
)
from generate_coaching_apply import (
    FORMSUBMIT_URL,
    build_apply_css,
    build_apply_js,
    generate_apply_page,
)
from generate_neo_brutalist import SITE_BASE_URL, write_shared_assets

OUTPUT_DIR = WORDPRESS_DIR / "output"


# ── Fixtures ─────────────────────────────────────────────────


@pytest.fixture(scope="module")
def coaching_html():
    return generate_coaching_page()


@pytest.fixture(scope="module")
def coaching_css():
    return build_coaching_css()


@pytest.fixture(scope="module")
def coaching_js():
    return build_coaching_js()


@pytest.fixture(scope="module")
def apply_html():
    return generate_apply_page()


@pytest.fixture(scope="module")
def apply_js():
    return build_apply_js()


# ── Page Generation ──────────────────────────────────────────


class TestPageGeneration:
    def test_returns_html(self, coaching_html):
        assert isinstance(coaching_html, str)
        assert "<!DOCTYPE html>" in coaching_html

    def test_has_canonical(self, coaching_html):
        assert 'rel="canonical"' in coaching_html
        assert "/coaching/" in coaching_html

    def test_has_ga4(self, coaching_html):
        assert "G-WQ7W8XN11N" in coaching_html
        assert "googletagmanager.com" in coaching_html

    def test_has_ab_snippet(self, coaching_html):
        assert "dataLayer" in coaching_html

    def test_has_jsonld(self, coaching_html):
        assert 'application/ld+json' in coaching_html
        assert '"@type":"WebPage"' in coaching_html
        assert '"@type":"Service"' in coaching_html

    def test_has_meta_robots(self, coaching_html):
        assert 'name="robots"' in coaching_html
        assert 'content="index, follow"' in coaching_html

    def test_has_meta_description(self, coaching_html):
        assert 'name="description"' in coaching_html

    def test_has_og_tags(self, coaching_html):
        assert 'og:title' in coaching_html
        assert 'og:description' in coaching_html

    def test_has_title(self, coaching_html):
        assert "<title>" in coaching_html
        assert "Coaching" in coaching_html


# ── Nav ──────────────────────────────────────────────────────


class TestNav:
    def test_nav_links(self, coaching_html):
        assert "/coaching/" in coaching_html
        assert "/about/" in coaching_html
        assert ">SERVICES</a>" in coaching_html
        assert ">ABOUT</a>" in coaching_html

    def test_breadcrumb(self, coaching_html):
        assert "rl-breadcrumb" in coaching_html
        assert "Coaching" in coaching_html

    def test_current_page_marker(self, coaching_html):
        assert 'aria-current="page"' in coaching_html
        assert 'aria-current="page">SERVICES</a>' in coaching_html


# ── Hero — "The Dossier" hero with corner CTA ───────────────


class TestHero:
    def test_hero_id(self):
        assert 'id="hero"' in build_hero()

    def test_hero_has_corner_cta(self):
        """Owner revision 2026-07-18: an obvious CTA on arrival, no scroll
        required. One link, the corner imperative."""
        hero = build_hero()
        assert 'class="rl-coach-hero-cta"' in hero
        assert 'data-cta="hero_apply"' in hero
        assert "GET ME IN YOUR CORNER" in hero

    def test_no_file_strip(self):
        """Owner revision 2026-07-18: file strip removed, not replaced."""
        hero = build_hero()
        assert "rl-coach-file-strip" not in hero
        assert "TERMS OF WORK" not in hero
        assert "COURSES ON FILE" not in hero


    def test_headline(self):
        hero = build_hero()
        assert "You could be better than you think." in hero
        assert "That is not encouragement &mdash;" in hero
        assert "it&#39;s an observation about people who train alone." in hero

    def test_subhead(self):
        hero = build_hero()
        assert "The fix is a human in your corner." in hero
        assert "Not an AI, not a dashboard, not a coach who reads you like a spreadsheet." in hero
        assert "The terms are below." in hero


# ── Terms — five numbered clauses ───────────────────────────


class TestTerms:
    def test_terms_id(self):
        assert 'id="terms"' in build_terms()

    def test_five_clauses(self):
        t = build_terms()
        assert t.count('class="rl-coach-term"') == 5

    def test_clause_numbers(self):
        t = build_terms()
        for n in ("01", "02", "03", "04", "05"):
            assert f'<div class="rl-coach-term-num">{n}</div>' in t

    def test_clause_titles(self):
        t = build_terms()
        for title in (
            "Every file, read by a person",
            "The patterns you can&#39;t see",
            "The plan moves when your life does",
            "The truth, on schedule",
            "Involvement is the only variable",
        ):
            assert title in t

    def test_clause_bodies(self):
        t = build_terms()
        assert "I notice the interval you bailed on and ask why." in t
        assert "Knowledge isn&#39;t the limiter &mdash; application is." in t
        assert "the week adjusts that week" in t
        assert "&ldquo;You&#39;re sandbagging&rdquo; and &ldquo;take the rest week&rdquo;" in t
        assert "Same coach, same standards." in t

    def test_last_clause_no_bottom_border(self, coaching_css):
        """Clause 05 has no border-bottom — tiers render immediately after
        with no visual gap, so the terms list must not double-close."""
        assert ".rl-coach-term:last-child" in coaching_css


# ── Full-Bleed Layout ────────────────────────────────────────


class TestFullBleedLayout:
    def test_container_override(self, coaching_css):
        assert "max-width: none" in coaching_css

    def test_inner_measure(self, coaching_css):
        assert "rl-coach-inner" in coaching_css
        assert "max-width: 1200px" in coaching_css

    def test_bands_present(self, coaching_html):
        assert 'class="rl-coach-band' in coaching_html
        assert "rl-coach-band--dark" in coaching_html

    def test_no_sand_band_anywhere(self, coaching_html, coaching_css):
        """rl-coach-band--sand is fully removed — tiers no longer sit on a
        sand background, they sit on the same paper as terms."""
        assert "rl-coach-band--sand" not in coaching_html
        assert "rl-coach-band--sand" not in coaching_css

    def test_all_sections_use_inner_wrapper(self, coaching_html):
        bands = coaching_html.count('<section class="rl-coach-band')
        inners = coaching_html.count('class="rl-coach-inner"')
        assert bands == inners == 6

    def test_terms_tiers_seamless(self, coaching_css):
        """Terms section has zero bottom padding, tiers section has zero
        top padding — the two must read as one continuous document, not
        two visually separated bands."""
        assert ".rl-coach-terms {\n  padding-bottom: 0;\n}" in coaching_css
        assert ".rl-coach-tiers-section {\n  padding-top: 0;\n}" in coaching_css

    def test_consent_banner_rendered(self, coaching_html):
        """Regression: an unescaped template tail would leave the literal
        placeholder string in the shipped HTML instead of the banner."""
        assert "{get_consent_banner_html()}" not in coaching_html


# ── Service Tiers ────────────────────────────────────────────


class TestServiceTiers:
    def test_tiers_id(self):
        assert 'id="tiers"' in build_tiers()

    def test_three_tier_columns(self):
        tiers = build_tiers()
        assert tiers.count('class="rl-coach-tier-col"') == 3
        assert "Min" in tiers
        assert "Mid" in tiers
        assert "Max" in tiers

    def test_prices(self):
        tiers = build_tiers()
        assert "$199" in tiers
        assert "$299" in tiers
        assert "$1,200" in tiers
        assert "/ 4 WEEKS" in tiers

    def test_get_started_links(self):
        tiers = build_tiers()
        assert tiers.count("GET STARTED") == 3
        assert 'data-cta="tier_min"' in tiers
        assert 'data-cta="tier_mid"' in tiers
        assert 'data-cta="tier_max"' in tiers
        assert f"{QUESTIONNAIRE_URL}?tier=min" in tiers
        assert f"{QUESTIONNAIRE_URL}?tier=mid" in tiers
        assert f"{QUESTIONNAIRE_URL}?tier=max" in tiers

    def test_setup_fee(self):
        tiers = build_tiers()
        assert "$99 setup fee" in tiers

    def test_disclaimer(self):
        tiers = build_tiers()
        assert "skipped workouts" in tiers
        assert "24 hours" in tiers

    def test_feature_lists_verbatim(self):
        tiers = build_tiers()
        for item in (
            "Weekly training review", "File analysis", "Quarterly strategy calls",
            "Structured workouts for your trainer or head unit",
            "Race-day nutrition plan", "Custom training guide",
            "Everything in Min", "Detailed power-file analysis",
            "Every-4-week strategy calls", "Weekly plan adjustments",
            "Direct message access", "Blindspot detection",
            "Everything in Mid", "Daily file review", "On-demand calls",
            "Race-week strategy", "Multi-race season planning", "Priority response",
        ):
            assert item in tiers, f"Missing tier feature: {item}"

    def test_no_normie_jargon(self):
        """No raw jargon in tier feature lists (WKO, TSB, TSS, CTL)."""
        tiers = build_tiers()
        for term in ("WKO", "TSB", "TSS", "CTL"):
            assert term not in tiers, f"Raw jargon in tiers: {term}"

    def test_fade_stagger_on_tiers(self):
        assert 'data-animate="fade-stagger"' in build_tiers()


# ── A fit, or not ─────────────────────────────────────────────


class TestFit:
    def test_fit_id(self):
        assert 'id="fit"' in build_honest_check()

    def test_yes_no_columns(self):
        h = build_honest_check()
        assert "Coaching is for you if:" in h
        assert "It isn&#39;t:" in h

    def test_eight_list_items(self):
        h = build_honest_check()
        assert h.count("<li>") == 8

    def test_no_sand_bg(self):
        assert "rl-coach-band--sand" not in build_honest_check()



# ── FAQ ──────────────────────────────────────────────────────


class TestFAQ:
    def test_faq_id(self):
        assert 'id="faq"' in build_faq()

    def test_eight_questions(self):
        f = build_faq()
        assert f.count('class="rl-coach-faq-item"') == 8

    def test_accordion_toggle(self):
        f = build_faq()
        assert "rl-coach-faq-toggle" in f
        assert "rl-coach-faq-q" in f

    def test_setup_fee_faq(self):
        f = build_faq()
        assert "$99 setup fee" in f

    def test_has_aria(self):
        f = build_faq()
        assert 'aria-expanded' in f
        assert 'role="button"' in f


# ── Application close ────────────────────────────────────────


class TestApplicationClose:
    def test_final_cta_id(self):
        assert 'id="final-cta"' in build_application_close()

    def test_dark_band(self):
        assert "rl-coach-band--dark" in build_application_close()

    def test_kicker(self):
        assert "APPLICATION" in build_application_close()

    def test_line_copy(self):
        c = build_application_close()
        assert "Ten minutes of honest answers. I read every one myself." in c
        assert "You&#39;ll hear from me within 48 hours &mdash; including if I don&#39;t think coaching is what you need." in c

    def test_cta_link(self):
        c = build_application_close()
        assert "GET ME IN YOUR CORNER &rarr;" in c
        assert f'href="{QUESTIONNAIRE_URL}"' in c
        assert 'data-cta="final_fill_intake"' in c

    def test_cta_border_is_paper_toned(self, coaching_css):
        assert "border: 1px solid var(--rl-color-cool-white);" in coaching_css

    def test_contact_line(self):
        c = build_application_close()
        assert 'href="mailto:coach@roadielabs.com"' in c
        assert "I answer myself, usually within a day." in c


# ── Mobile sticky CTA ────────────────────────────────────────


class TestMobileStickyCTA:
    def test_label_updated(self):
        sticky = build_mobile_sticky_cta()
        assert "GET ME IN YOUR CORNER &rarr;" in sticky
        assert "Apply for coaching" not in sticky

    def test_data_cta_and_href(self):
        sticky = build_mobile_sticky_cta()
        assert 'data-cta="sticky_cta"' in sticky
        assert f'href="{QUESTIONNAIRE_URL}"' in sticky


# ── Brand Compliance ─────────────────────────────────────────


class TestBrandCompliance:
    def test_no_hardcoded_hex_in_coaching_css(self, coaching_css):
        css = re.sub(r'/\*.*?\*/', '', coaching_css, flags=re.DOTALL)
        hex_colors = re.findall(r'#[0-9a-fA-F]{3,8}\b', css)
        assert len(hex_colors) == 0, f"Found hardcoded hex in coaching CSS: {hex_colors[:5]}"

    def test_no_hardcoded_hex_in_apply_css(self):
        css = re.sub(r'/\*.*?\*/', '', build_apply_css(), flags=re.DOTALL)
        hex_colors = re.findall(r'#[0-9a-fA-F]{3,8}\b', css)
        assert len(hex_colors) == 0, f"Found hardcoded hex in apply CSS: {hex_colors[:5]}"

    def test_no_border_radius(self, coaching_css):
        assert "border-radius" not in coaching_css

    def test_no_box_shadow(self, coaching_css):
        assert "box-shadow" not in coaching_css

    def test_uses_brand_tokens(self, coaching_css):
        assert "var(--rl-color-" in coaching_css
        assert "var(--rl-font-" in coaching_css

    def test_no_bounce_easing(self, coaching_css):
        assert "cubic-bezier(0.34, 1.56" not in coaching_css

    def test_correct_class_prefix(self, coaching_css):
        allowed_roots = (
            'rl-coach-', 'rl-neo-brutalist', 'rl-site-header', 'rl-hero',
            'rl-section', 'rl-breadcrumb', 'rl-footer', 'rl-mega-footer',
            'rl-has-js', 'rl-in-view',
        )
        classes = set(re.findall(r'\.([a-zA-Z][\w-]*)', coaching_css))
        for cls in classes:
            assert cls.startswith(allowed_roots), (
                f"Non-prefixed class in coaching CSS: .{cls}"
            )


class TestTokenValidation:
    @pytest.fixture(scope="class")
    def defined_tokens(self):
        tokens_path = Path(__file__).parent.parent.parent / "road-labs-brand" / "tokens" / "tokens.css"
        if not tokens_path.exists():
            pytest.skip("tokens.css not found")
        content = tokens_path.read_text()
        return set(re.findall(r'(--rl-[\w-]+)\s*:', content))

    def test_coaching_css_all_var_refs_defined(self, coaching_css, defined_tokens):
        used = set(re.findall(r'var\((--rl-[\w-]+)\)', coaching_css))
        undefined = used - defined_tokens
        assert not undefined, f"Undefined CSS tokens in coaching CSS: {undefined}"

    def test_apply_css_all_var_refs_defined(self, defined_tokens):
        used = set(re.findall(r'var\((--rl-[\w-]+)\)', build_apply_css()))
        undefined = used - defined_tokens
        assert not undefined, f"Undefined CSS tokens in apply CSS: {undefined}"


# ── GA4 Events ───────────────────────────────────────────────


class TestGA4Events:
    def test_all_events_present(self, coaching_js):
        events = [
            "coaching_faq_open",
            "coaching_scroll_depth",
            "coaching_cta_click",
            "coaching_page_view",
        ]
        for event in events:
            assert event in coaching_js, f"Missing GA4 event: {event}"

    def test_no_carousel_events(self, coaching_js):
        assert "coaching_carousel" not in coaching_js

    def test_ga4_present_in_both_outputs(self, coaching_html, apply_html):
        for html_doc in (coaching_html, apply_html):
            assert "G-WQ7W8XN11N" in html_doc
            assert "googletagmanager.com" in html_doc

    def test_scroll_depth_section_ids_match_real_sections(self, coaching_js, coaching_html):
        """Every id referenced by the scroll-depth IIFE must exist in the
        shipped HTML, and the set must be exactly the seven real content
        sections — no dead ids, no missing sections."""
        section_ids = re.findall(r"id:\s*'([\w-]+)'", coaching_js)
        assert set(section_ids) == {
            "hero", "terms", "tiers", "fit", "faq", "final-cta",
        }
        for sid in section_ids:
            assert f'id="{sid}"' in coaching_html, f"Dead section id in scroll-depth JS: {sid}"

    def test_old_section_labels_removed(self, coaching_js):
        for old_id in ("'problem'", "'deliverables'", "'how-it-works'", "'honest-check'"):
            assert old_id not in coaching_js, f"Stale scroll-depth id still present: {old_id}"


# ── JS Syntax ────────────────────────────────────────────────


class TestJSSyntax:
    def test_coaching_js_parses_via_node(self, coaching_js):
        js_body = coaching_js.replace("<script>", "").replace("</script>", "")
        result = subprocess.run(
            [
                "node", "--input-type=module", "-e",
                "const src = process.argv[1];"
                "new Function(src);"
                "console.log('SYNTAX_OK');",
                js_body,
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert result.returncode == 0, f"JS syntax error: {result.stdout} {result.stderr}"
        assert "SYNTAX_OK" in result.stdout

    def test_apply_js_parses_via_node(self, apply_js):
        js_body = apply_js.replace("<script>", "").replace("</script>", "")
        result = subprocess.run(
            [
                "node", "--input-type=module", "-e",
                "const src = process.argv[1];"
                "new Function(src);"
                "console.log('SYNTAX_OK');",
                js_body,
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert result.returncode == 0, f"JS syntax error: {result.stdout} {result.stderr}"
        assert "SYNTAX_OK" in result.stdout


# ── JSON-LD ──────────────────────────────────────────────────


class TestJSONLD:
    def test_webpage_schema(self):
        ld = build_jsonld()
        assert '"@type":"WebPage"' in ld
        assert "/coaching/" in ld
        assert "Roadie Labs" in ld

    def test_service_schema(self):
        ld = build_jsonld()
        assert '"@type":"Service"' in ld
        assert "Road Cycling Coaching" in ld

    def test_description_reflects_new_hero(self):
        """The old description referenced the removed 'Fitness is common'
        hero — it must be gone, replaced by wording consistent with the
        new one-coach / 427-courses hero."""
        ld = build_jsonld()
        assert "Fitness is common" not in ld
        assert "427 courses on file" in ld

    def test_uses_safe_json_for_script(self):
        """JSON-LD must go through _safe_json_for_script — a '</script>'
        payload should never be able to break out of the <script> tag."""
        from generate_neo_brutalist import _safe_json_for_script
        payload = {"a": "</script><script>alert(1)</script>"}
        safe = _safe_json_for_script(payload)
        assert "</script>" not in safe


# ── Accessibility ────────────────────────────────────────────


class TestAccessibility:
    def test_skip_to_content_link(self, coaching_html):
        assert 'class="rl-coach-skip-link"' in coaching_html
        assert 'Skip to content' in coaching_html

    def test_reduced_motion_css(self, coaching_css):
        assert "prefers-reduced-motion: reduce" in coaching_css

    def test_faq_aria_controls(self, coaching_html):
        assert 'aria-controls="rl-coach-faq-ans-' in coaching_html
        assert 'role="region"' in coaching_html


# ── Scroll Animations ────────────────────────────────────────


class TestScrollAnimations:
    def test_fade_stagger_on_tiers(self):
        html = build_tiers()
        assert 'data-animate="fade-stagger"' in html

    def test_no_animation_on_hero(self):
        html = build_hero()
        assert 'data-animate' not in html

    def test_no_animation_on_terms(self):
        html = build_terms()
        assert 'data-animate' not in html


    def test_css_has_reduced_motion_guard(self, coaching_css):
        assert "prefers-reduced-motion: no-preference" in coaching_css

    def test_css_has_rl_has_js_guard(self, coaching_css):
        assert ".rl-has-js" in coaching_css

    def test_js_has_intersection_observer(self, coaching_js):
        assert "IntersectionObserver" in coaching_js

    def test_js_adds_rl_has_js(self, coaching_js):
        assert "rl-has-js" in coaching_js

    def test_content_visible_without_js(self):
        """Progressive enhancement: no opacity:0 on the section wrapper
        itself outside the has-js gate — only child elements are hidden,
        and only after JS marks the page ready."""
        css = build_coaching_css()
        assert "rl-has-js [data-animate" in css
        assert "rl-in-view[data-animate" in css


# ── Restraint Guard ──────────────────────────────────────────
# The page asserts; it doesn't perform. Banned substrings from the old
# loud template must never come back.


BANNED_SUBSTRINGS = [
    "$14.95",
    "/ride",
    "If you can pedal",
    "blown race",
    "costs you",
    "suffer smarter",
    "Not a Spreadsheet",
    "generated in 2 seconds",
    "Honest Check",
    "Can't Get From a Prompt",
    "328 races",
    "brake pads",
    "Strava KOM",
]

# Checked against VISIBLE TEXT ONLY (script/style stripped, tags stripped) —
# these are generic words that can legitimately appear in class names,
# comments, or CSS without being loud marketing copy on the rendered page.
NEW_BANNED_VISIBLE_TEXT = [
    "unlock",
    "transform",
    "crush",
    "Fitness is common",
]


def _visible_text(html_doc: str) -> str:
    """Strip <script>...</script> and <style>...</style> blocks, then strip
    remaining HTML tags, leaving only what a reader actually sees."""
    no_script = re.sub(r'<script.*?</script>', '', html_doc, flags=re.DOTALL)
    no_style = re.sub(r'<style.*?</style>', '', no_script, flags=re.DOTALL)
    return re.sub(r'<[^>]+>', '', no_style)


class TestRestraintGuard:
    @pytest.mark.parametrize("phrase", BANNED_SUBSTRINGS)
    def test_banned_phrase_absent(self, coaching_html, phrase):
        assert phrase not in coaching_html, f"Banned phrase found in coaching page: {phrase!r}"

    @pytest.mark.parametrize("phrase", NEW_BANNED_VISIBLE_TEXT)
    def test_banned_visible_text_absent(self, coaching_html, phrase):
        visible = _visible_text(coaching_html)
        assert phrase not in visible, f"Banned word found in visible coaching page text: {phrase!r}"

    def test_no_defensive_messaging(self, coaching_html):
        lower = coaching_html.lower()
        assert "no sponsors" not in lower
        assert "not sponsored" not in lower
        assert "no affiliates" not in lower


# ── Required Content ─────────────────────────────────────────


class TestRequiredContent:
    def test_no_visible_course_count(self, coaching_html):
        """Owner revision 2026-07-18: the courses-on-file flex removed from
        visible copy. (JSON-LD metadata may still carry it.)"""
        assert "COURSES ON FILE" not in coaching_html



    def test_link_to_about(self, coaching_html):
        assert f"{SITE_BASE_URL}/about/" in coaching_html

    def test_apply_url_present(self, coaching_html):
        assert QUESTIONNAIRE_URL in coaching_html
        assert QUESTIONNAIRE_URL == f"{SITE_BASE_URL}/coaching/apply/"

    def test_disclaimer_and_setup_fee(self, coaching_html):
        assert "skipped workouts" in coaching_html
        assert "$99 setup fee" in coaching_html

    def test_hero_h1(self, coaching_html):
        assert "You could be better than you think." in coaching_html
        assert "it&#39;s an observation about people who train alone." in coaching_html

    def test_final_contact_line(self, coaching_html):
        assert "coach@roadielabs.com" in coaching_html
        assert 'href="mailto:coach@roadielabs.com"' in coaching_html
        assert "I answer myself, usually within a day." in coaching_html

    def test_how_it_works_removed(self, coaching_html):
        assert 'id="how-it-works"' not in coaching_html
        assert 'id="problem"' not in coaching_html
        assert 'id="deliverables"' not in coaching_html
        assert "How it works" not in coaching_html


# ── Cross-Brand Leakage ──────────────────────────────────────


class TestCrossBrandLeakage:
    def test_coaching_no_gg_classes(self, coaching_html):
        assert 'class="gg-' not in coaching_html

    def test_coaching_no_gravel_domain(self, coaching_html):
        assert "gravelgodcycling.com" not in coaching_html

    def test_apply_no_gg_classes(self, apply_html):
        assert 'class="gg-' not in apply_html

    def test_apply_no_gravel_domain(self, apply_html):
        assert "gravelgodcycling.com" not in apply_html

    def test_no_gravel_god_prose(self, coaching_html):
        """Testimonials + provenance removed 2026-07-18 — nothing on the
        page should reference the sibling brand anymore."""
        assert "Gravel God" not in coaching_html


# ── Apply Page ───────────────────────────────────────────────


class TestApplyPage:
    def test_formsubmit_endpoint(self, apply_html):
        assert "formsubmit.co/ajax/df9d64ff7bd404311c74f4a4240a1ebd" in apply_html
        assert FORMSUBMIT_URL == "https://formsubmit.co/ajax/df9d64ff7bd404311c74f4a4240a1ebd"

    def test_hidden_url_context_param(self, apply_html):
        assert '"_url"' in apply_html
        assert "coaching/apply" in apply_html

    def test_subject_prefix(self, apply_html):
        assert "Roadie Labs Coaching Application" in apply_html

    def test_header_js_present(self, apply_html):
        """Distinctive substring of get_site_header_js() — proves the
        mobile hamburger behavior is wired into the apply page."""
        assert "rl-site-header-toggle" in apply_html
        assert "aria-expanded" in apply_html

    def test_no_auto_mailto_redirect(self, apply_html):
        assert 'window.location.href = "mailto' not in apply_html

    def test_mailto_fallback_link_present(self, apply_html):
        assert 'mailto:coach@roadielabs.com?subject=' in apply_html

    def test_honeypot_field_present(self, apply_html):
        assert 'name="website"' in apply_html
        assert "rl-apply-honeypot" in apply_html

    def test_honeypot_client_check_present(self, apply_html):
        assert "if (data.website)" in apply_html

    def test_confidentiality_footer_email_unchanged(self, apply_html):
        assert "coach@roadielabs.com" in apply_html

    def test_success_requires_explicit_flag(self, apply_html):
        """Bare 2xx is not treated as delivery — the response body must
        be parsed and success === 'true' checked explicitly."""
        assert 'json.success === "true"' in apply_html

    def test_no_innerhtml_with_mailto_data(self, apply_html):
        """The mailto fallback link (which carries the athlete's own name
        in its subject) must be built via the DOM, not innerHTML."""
        assert "mailtoLink" in apply_html
        assert "createElement" in apply_html


# ── Drift Guard ──────────────────────────────────────────────
# Regenerating each page in-memory must equal the checked-in output
# byte-for-byte. A failure here means someone edited the generator
# source without regenerating wordpress/output/*.html.


class TestDriftGuard:
    def test_coaching_html_matches_checked_in_output(self, tmp_path):
        checked_in_path = OUTPUT_DIR / "coaching.html"
        if not checked_in_path.exists():
            pytest.skip("wordpress/output/coaching.html not generated yet")
        assets = write_shared_assets(tmp_path)
        regenerated = generate_coaching_page(external_assets=assets)
        checked_in = checked_in_path.read_text(encoding="utf-8")
        assert regenerated == checked_in, (
            "wordpress/output/coaching.html is stale — run "
            "`python3 wordpress/generate_coaching.py` to regenerate it."
        )

    def test_apply_html_matches_checked_in_output(self, tmp_path):
        checked_in_path = OUTPUT_DIR / "coaching-apply.html"
        if not checked_in_path.exists():
            pytest.skip("wordpress/output/coaching-apply.html not generated yet")
        assets = write_shared_assets(tmp_path)
        regenerated = generate_apply_page(external_assets=assets)
        checked_in = checked_in_path.read_text(encoding="utf-8")
        assert regenerated == checked_in, (
            "wordpress/output/coaching-apply.html is stale — run "
            "`python3 wordpress/generate_coaching_apply.py` to regenerate it."
        )
