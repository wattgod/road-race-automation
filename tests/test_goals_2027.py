"""Tests for the Roadie Labs /goals/ page generator (wordpress/generate_goals_2027.py).

Road build of Gravel God's goal_2027 season-review variant
(gravel-race-automation wordpress/generate_season_review.py +
season_review_variants.py; docs/specs/goals-2027-funnel-spec.md D13). Mirrors
that file's test coverage (tests/test_season_review.py::TestGoalsPage) where
the behaviour is the same; drops what does not apply here — this page has
only one variant (no matti/athlete/five to compare against) and Roadie Labs
sells one plan product (no Season Plan, so no season-cta/token tests).
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "wordpress"))

import generate_goals_2027 as goals  # noqa: E402
from generate_goals_2027 import (  # noqa: E402
    LEAD_BRAND,
    LEAD_SOURCE,
    LEAD_WORKER_URL,
    build_goals_js,
    generate_goals_page,
)


def page() -> str:
    return generate_goals_page()


def core_form() -> str:
    html = page()
    start = html.index('<form id="goals-form"')
    return html[start:html.index('<div class="rl-goals-part">', start)]


def test_has_ga4_and_header_js():
    html = page()
    assert "gtag" in html
    assert "rl-site-header" in html or "hamburger" in html.lower()


def test_indexed_and_findable():
    assert 'content="index, follow"' in page()
    assert 'canonical" href="https://roadielabs.com/goals/"' in page()


def test_honeypot_present():
    assert 'name="website" class="rl-apply-honeypot"' in page()


def test_no_innerhtml_in_js():
    assert "innerHTML" not in build_goals_js()


def test_no_inline_handlers():
    assert not re.search(r'\son(click|submit|change|input)=', page())


def test_no_placeholders_left():
    assert not re.search(r"__[A-Z_]+__", build_goals_js())


def test_poster_colors_come_from_brand_tokens():
    # sol review, 2026-09-27: CLAUDE.md requires generators to source colors
    # from brand_tokens.COLORS, never hand-typed hex.
    import inspect
    import json as _json
    from brand_tokens import COLORS

    src = inspect.getsource(goals)
    assert "COLORS[\"near_black\"]" in src
    assert "COLORS[\"cool_white\"]" in src
    assert "COLORS[\"signal_red\"]" in src
    assert "COLORS[\"secondary_blue\"]" in src

    js = build_goals_js()
    assert _json.dumps(COLORS["near_black"]) in js
    assert _json.dumps(COLORS["cool_white"]) in js
    assert _json.dumps(COLORS["signal_red"]) in js
    assert _json.dumps(COLORS["secondary_blue"]) in js


def test_no_ftp_or_training_number_questions():
    # Matti ruling: training numbers come from data, never a form.
    html = page().lower()
    for banned in ("ftp", "functional threshold", "watts per kilogram"):
        assert banned not in html


def test_no_exclamation_marks_in_visible_copy():
    """House rule (unlike the gravel page): flat deadpan register. The only
    "!" characters allowed are CSS !important and JS operators (!==, !!,
    !x) — never a literal exclamation mark in copy."""
    html = page()
    for m in re.finditer(r".{20}!.{20}", html):
        snippet = m.group(0)
        assert "important" in snippet.lower() or re.search(r"!={1,2}|!!|![a-zA-Z(]", snippet), (
            f"possible exclamation mark in copy: {snippet!r}"
        )


def test_no_descriptive_subtitles_under_section_headings():
    # House rule: no `sub` line under a section title (unlike gravel's
    # version, which sets one on 3 of its 6 sections).
    assert "rl-apply-section-sub" not in page()


def test_posts_to_the_shared_multi_brand_worker_with_roadielabs_brand():
    js = build_goals_js()
    assert LEAD_WORKER_URL in js
    assert f'source: "{LEAD_SOURCE}"' in js
    assert f'brand: "{LEAD_BRAND}"' in js
    assert LEAD_BRAND == "roadielabs"
    assert LEAD_SOURCE == "goal_2027"


def test_results_come_before_the_offer():
    html = page()
    assert html.index('id="poster-canvas"') < html.index("data-offer-variant")


def test_results_start_hidden():
    html = page()
    section = html[html.index('<section id="results"'):html.index("</section>", html.index('<section id="results"'))]
    assert "hidden" in html[html.index('<section id="results"'):html.index('class="rl-goals-results-head"')]
    assert section.count("data-offer-variant") == 3
    assert section.count('class="rl-goals-offer"') == 3


def test_three_offer_variants_to_test():
    js = build_goals_js()
    assert "goal_offer_view" in js and "offer_variant" in js


def test_only_one_plan_product_race_plan_no_season_plan():
    # Roadie Labs has no Season Plan product today (that is a Gravel God
    # ruling, docs/specs/goals-2027-funnel-spec.md D2/D15) — linking one
    # here would be a dead product. Only the real, working /questionnaire/
    # checkout.
    plans = goals.OFFER["plans"]
    keys = [p["key"] for p in plans]
    assert keys == ["race"]
    assert "priced by the week from your race date" in plans[0]["price"]
    assert "$" not in plans[0]["price"]
    assert plans[0]["cta_href"] == "/questionnaire/?src=goals"
    assert "season" not in [p["key"] for p in plans]


def test_offer_html_renders_the_one_plan_cta():
    html = page()
    assert 'data-plan-type="race"' in html
    assert html.count('class="rl-goals-offer-plan"') == 3  # 3 offer variants x 1 plan
    assert 'data-plan-type="season"' not in html


def test_the_funnel_is_measurable():
    js = build_goals_js()
    for event in ("goal_start", "goal_section", "goal_submit", "goal_results_view",
                  "goal_poster_download", "goal_offer_view", "goal_offer_click"):
        assert event in js, event


def test_offer_c_headline_avoids_the_banned_faux_insight_pattern():
    # sol review, 2026-09-27: "the part everyone skips" is the exact
    # faux-insight cliche the pinned no-ai-slop rules ban.
    variant_c = next(v for v in goals.OFFER["variants"] if v["key"] == "C")
    assert "everyone skips" not in variant_c["h"].lower()


def test_offer_terms_has_no_refund_line_and_no_dollar_figure():
    terms = goals.OFFER["terms"]
    assert terms.startswith("I build every plan myself")
    assert "refund" not in terms.lower()
    assert "$" not in terms


def test_goal_section_carries_number_and_is_scroll_triggered():
    js = build_goals_js()
    assert 'ga4("goal_section", { number: Number(n) })' in js
    section_fn = js[js.index("function watchGoalSections"):js.index("watchGoalSections();")]
    assert "IntersectionObserver" in section_fn
    assert "setInterval" not in section_fn and "setTimeout" not in section_fn


def test_goal_section_numbers_rendered_in_html_and_unique():
    html = page()
    nums = re.findall(r'data-section-n="(\d+)"', html)
    assert nums, "no numbered sections found"
    assert len(nums) == len(set(nums))


def test_goal_section_does_not_fire_for_whatever_is_visible_on_load():
    js = build_goals_js()
    assert "watchGoalSections();\n  restore();" not in js
    assert "goalSectionsStarted = true;\n    watchGoalSections();" in js


def test_goal_section_is_deferred_to_a_genuine_pointer_key_or_wheel_event():
    js = build_goals_js()
    assert '["pointerdown", "keydown", "wheel", "touchstart"].forEach(function(evt) {' in js
    assert 'window.addEventListener(evt, startWatchingGoalSectionsOnce, { once: true, passive: true });' in js
    assert 'window.addEventListener("scroll", startWatchingGoalSectionsOnce' not in js


def test_goal_section_ignores_restores_own_programmatic_scroll():
    js = build_goals_js()
    assert "if (goalSectionsStarted || restoringDraft) { return; }" in js
    restore_fn = js[js.index("function restore() {"):js.index("form.querySelectorAll(\".rl-goals-save\")")]
    assert "restoringDraft = true;" in restore_fn
    assert "restoringDraft = false;" in restore_fn


def test_entry_src_and_race_slug_are_validated_before_use():
    js = build_goals_js()
    assert '/^[a-z_]{1,24}$/.test(v)' in js       # ENTRY_SRC
    assert '/^[a-z0-9-]{1,80}$/.test(v)' in js    # RACE_SLUG


def test_goal_hero_click_fires_upstream_not_on_this_page():
    # goal_hero_click fires on the race-page goal card
    # (generate_neo_brutalist.py build_goal_card) — not on /goals/ itself.
    js = build_goals_js()
    assert 'ga4("goal_hero_click"' not in js
    assert "params.src = ENTRY_SRC" in js


def test_worker_payload_carries_entry_attribution():
    js = build_goals_js()
    assert "race_slug: RACE_SLUG" in js
    assert "entry_src: ENTRY_SRC" in js
    assert "goal_type: GOAL_TYPE" in js


def test_goal_type_is_validated_to_the_fixed_set():
    js = build_goals_js()
    assert '/^(finish|beat_time|race_it|same|bigger)$/.test(v)' in js


def test_outcome_goal_is_prefilled_only_when_empty():
    js = build_goals_js()
    assert 'if (goalField && !goalField.value.trim()) {' in js
    assert 'document.getElementById("outcome_goal")' in js


def test_prefill_templates_mirror_the_race_card():
    # Must not drift from generate_neo_brutalist.py's
    # GOAL_CARD_COPY["goal_lines"] (the strings actually shown on the
    # race-page goal card) — the FULL keyed mapping, not just that every
    # value appears somewhere (sol review, 2026-09-27: the looser version
    # would still pass if two goal types' lines were swapped).
    sys.path.insert(0, str(Path(__file__).parent.parent / "wordpress"))
    from generate_neo_brutalist import GOAL_CARD_COPY

    js = build_goals_js()
    block = js[js.index("var goalLineTemplates = {"):js.index("};", js.index("var goalLineTemplates = {"))]
    found = dict(re.findall(r'(\w+):\s*"([^"]*)"', block))
    assert found == GOAL_CARD_COPY["goal_lines"], (
        f"prefill templates drifted from the race card: {found!r} != {GOAL_CARD_COPY['goal_lines']!r}"
    )


def test_offer_cta_carries_variant_and_race_into_the_plan_form_link():
    js = build_goals_js()
    assert 'ctaUrl.searchParams.set("offer_variant", key)' in js
    assert 'ctaUrl.searchParams.set("race", RACE_SLUG)' in js
    assert 'ctaUrl.searchParams.set("src"' not in js


def test_offer_cta_also_carries_the_original_entry_src():
    js = build_goals_js()
    assert 'ctaUrl.searchParams.set("entry_src", ENTRY_SRC)' in js


def test_five_whys_field_kind_renders():
    html = page()
    assert 'id="outcome_why"' in html
    assert 'id="why_2"' in html and 'id="why_5"' in html


def test_no_season_plan_words_anywhere_on_the_page():
    assert "Season Plan" not in page()
    assert "/season-plan/" not in page()


def test_consent_footer_names_roadielabs_contact():
    html = page()
    assert "coach@roadielabs.com" in html
    assert "/privacy/" in html


def test_worker_is_the_only_transport_no_formsubmit_backstop():
    # docs/specs/goals-2027-funnel-spec.md D8: the worker is the record for
    # this lead source — no email backstop, no FormSubmit relay.
    js = build_goals_js()
    assert "formsubmit" not in js.lower()
