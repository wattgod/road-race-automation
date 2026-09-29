"""The Roadie Labs race debrief at /race-debrief/ (wordpress/generate_race_debrief.py).

Road build of Gravel God's race debrief (gravel-race-automation
wordpress/season_review_variants.py RACE_DEBRIEF), the same way
generate_goals_2027.py is the road build of the goals page. The worker and
Mission Control side (source=plan_debrief, brand=roadielabs) is tested in
gravel-race-automation: tests/test_race_debrief_survey.py,
tests/test_fueling_lead_intake.mjs and mission_control/tests/test_plan_debrief.py,
whose Roadie fixture posts exactly the body this page does. These tests pin
this page: same questions and keys as the gravel page, Roadie's house rules,
the ?plan= / ?ref= fields and their validation, GA4, the TP rating line, and
the caps. The browser run is tests/test_race_debrief_playwright.py.
"""
from __future__ import annotations

import html as html_lib
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "wordpress"))

import generate_race_debrief as debrief  # noqa: E402
from generate_race_debrief import (  # noqa: E402
    CONTACT_EMAIL,
    LEAD_BRAND,
    LEAD_SOURCE,
    LEAD_WORKER_URL,
    PLAN_ID_PATTERN,
    PLAN_REF_PATTERN,
    SECTIONS,
    TP_PLAN_URL,
    answer_keys,
    build_debrief_js,
    build_personal_link_js,
    generate_race_debrief_page,
    input_names,
)

# The gravel page's goal_answers keys, in page order (gravel-race-automation
# tests/test_race_debrief_survey.py test_answer_keys). The worker and Mission
# Control are one shared pipeline, so the two pages must post the same keys.
GRAVEL_ANSWER_KEYS = [
    "raced", "result", "result_url", "goal_met", "completion", "load", "fit_week", "worked",
    "change_one", "recommend", "quote", "not_for", "share_as", "age_group", "where_site",
    "where_social", "where_email", "where_tp", "connection", "reference", "next_race",
    "next_want", "last_word",
]
# The worker's DEBRIEF_CHANNEL_LABELS.roadielabs and Mission Control's
# plan_debrief.CHANNEL_LABELS["roadielabs"] (gravel-race-automation).
ROADIE_CHANNELS = {
    "where_site": "roadielabs.com",
    "where_social": "Roadie Labs social posts",
    "where_email": "Emails to riders choosing a plan",
    "where_tp": "The plan's TrainingPeaks page",
}


@pytest.fixture(scope="module")
def page() -> str:
    return generate_race_debrief_page()


@pytest.fixture(scope="module")
def form(page) -> str:
    return page[page.index('<form id="debrief-form"'):page.index("</form>")]


@pytest.fixture(scope="module")
def js() -> str:
    return build_debrief_js()


def _field(name):
    for sec in SECTIONS:
        for f in sec["fields"]:
            for g in f.get("fields", [f]):
                if g.get("name") == name:
                    return g
    raise KeyError(name)


def _group(form_html: str, name: str) -> str:
    start = form_html.index(f'data-radio="{name}"')
    return form_html[form_html.rindex("<div", 0, start):form_html.index("</div></div>", start)]


class TestPlace:
    def test_url_title_and_never_indexed(self, page):
        assert '<link rel="canonical" href="https://roadielabs.com/race-debrief/">' in page
        assert "<title>How Did It Go? | Roadie Labs</title>" in page
        assert '<meta name="robots" content="noindex, nofollow">' in page

    def test_not_in_the_sitemap(self):
        # the sitemap lists its static pages by hand; this one is not among them
        src = (ROOT / "scripts" / "generate_sitemap.py").read_text(encoding="utf-8")
        assert "race-debrief" not in src

    def test_has_ga4_header_js_and_roadie_classes(self, page, form):
        assert "gtag" in page and "rl-neo-brutalist-page" in page
        assert 'class="gg-' not in form and 'class="gg-' not in page[page.index('<div class="rl-apply-container">'):]

    def test_deploy_flag_is_wired_in_all_three_places(self):
        src = (ROOT / "scripts" / "push_wordpress.py").read_text(encoding="utf-8")
        assert '"--sync-race-debrief", action="store_true"' in src
        assert "args.sync_race_debrief," in src
        assert "sync_race_debrief(args.race_debrief_file)" in src
        assert 'remote_base = f"{REMOTE_BASE}/race-debrief"' in src


class TestTransport:
    def test_shared_worker_with_the_roadie_brand_and_plan_debrief_source(self, js):
        assert LEAD_WORKER_URL == "https://fueling-lead-intake.gravelgodcycling.workers.dev"
        assert (LEAD_SOURCE, LEAD_BRAND) == ("plan_debrief", "roadielabs")
        assert f'source: "{LEAD_SOURCE}", brand: "{LEAD_BRAND}"' in js
        assert f'fetch("{LEAD_WORKER_URL}"' in js

    def test_no_formsubmit_and_no_lead_context(self, page, js):
        assert "formsubmit" not in page.lower()
        for lead_only in ("race_slug", "offer_variant", "entry_src", "goal_type", "goal_start", "goal_submit"):
            assert lead_only not in js, lead_only

    def test_no_placeholders_left(self, js):
        assert not re.search(r"__[A-Z_]+__", js)


class TestHouseRules:
    def test_no_descriptive_subtitles_under_section_headings(self, page):
        assert "rl-apply-section-sub" not in page
        assert all("sub" not in sec for sec in SECTIONS)

    def test_no_exclamation_marks_in_visible_copy(self, page):
        body = page[page.index('<div class="rl-apply-header">'):page.index("</form>")]
        text = html_lib.unescape(re.sub(r"<[^>]+>", " ", body))
        assert "!" not in text

    def test_no_exclamation_marks_in_js_strings(self, js):
        for s in re.findall(r'"([^"\\]*(?:\\.[^"\\]*)*)"', js):
            if " " in s:  # a sentence, not a selector
                assert "!" not in s, s


class TestSameQuestionsAsGravel:
    def test_answer_keys_match_the_gravel_page(self):
        assert answer_keys() == GRAVEL_ANSWER_KEYS

    def test_sections_in_order(self, form):
        titles = re.findall(r'rl-apply-section-title">([^<]+)</div>', form)
        assert titles == ["1. You", "2. Race Day", "3. The Plan", "4. On the Record", "5. What&#39;s Next"]

    def test_only_the_first_question_is_required(self, form):
        required = set(re.findall(r'name="([a-z_]+)"[^>]*\srequired', form))
        assert required == {"name", "email", "raced"}

    def test_channels_name_roadie_labs(self):
        assert {k: html_lib.unescape(v) for k, v in _field("share_where")["options"]} == ROADIE_CHANNELS

    def test_each_check_is_its_own_input_and_names_are_unique(self, form):
        names = input_names()
        assert len(names) == len(set(names))
        for key in ROADIE_CHANNELS:
            assert form.count(f'name="{key}"') == 1

    def test_long_options_stack_vertically(self, form):
        for name in ("raced", "goal_met", "completion", "share_as", "connection", "next_want"):
            assert "rl-apply-radio-horizontal" not in _group(form, name), name
        for name in ("load", "fit_week", "reference"):
            assert "rl-apply-radio-horizontal" in _group(form, name), name


class TestCopy:
    """DRAFT copy pending Matti's read: the gravel draft, Roadie's rules."""

    def test_draft_marker(self):
        src = (ROOT / "wordpress" / "generate_race_debrief.py").read_text(encoding="utf-8")
        assert "# DRAFT COPY: Matti's read pending before deploy (receipts spec §3.7: Matti writes every ask)." in src

    def test_header_and_buttons(self, page, js):
        assert '<div class="rl-apply-badge">Race Debrief</div>' in page
        assert "<h1>How Did It Go?</h1>" in page
        assert ("Five minutes, less if you&#39;re quick. Apart from your name and email, only the first "
                "question is required. I read every one of these myself. It saves as you go.") in page
        assert ">Send It to Matti</button>" in page
        assert "That&#39;s everything. Send it when you&#39;re ready." in page
        assert 'SUCCESS = "Got it. I\'ll read every word."' in js

    def test_footer_names_the_roadie_address(self, page):
        assert CONTACT_EMAIL == "coach@roadielabs.com"
        footer = page[page.index('<p class="rl-apply-confidential">'):]
        footer = footer[:footer.index("</p>")]
        assert footer == (
            '<p class="rl-apply-confidential">Your answers come straight to me and are stored in my system. '
            "If you said I can share your words, nothing goes up until you&#39;ve approved the exact wording. "
            "Drafts are saved only in this browser until you submit. Questions? Email coach@roadielabs.com"
            ' &middot; <a href="/privacy/">Privacy Policy</a>')

    def test_the_consent_note_is_the_approved_one(self, form):
        assert ('<p class="rl-debrief-note">Before anything goes up, I&#39;ll send you the exact words and how '
                "they&#39;ll look, and nothing runs until you say yes.") in form


class TestUrlFields:
    def test_hidden_inputs_carry_their_param_and_pattern(self, form):
        assert (f'<input type="hidden" id="plan" name="plan" data-param="plan" '
                f'data-pattern="{PLAN_ID_PATTERN}">') in form
        assert (f'<input type="hidden" id="ref" name="ref" data-param="ref" '
                f'data-pattern="{PLAN_REF_PATTERN}">') in form
        # the gravel page, the worker and Mission Control use these exact patterns
        assert (PLAN_ID_PATTERN, PLAN_REF_PATTERN) == (r"^[0-9]{1,12}$", r"^[A-Za-z0-9_-]{8,32}$")

    def test_posted_top_level_never_as_answers(self, js):
        assert 'var TOP_LEVEL = ["name", "email", "athlete", "plan", "ref"];' in js
        assert "URL_FIELDS.forEach(function(el) { if (d[el.name]) { body[el.name] = d[el.name]; } });" in js

    def test_personal_params_come_off_the_address_before_ga4_plan_and_ref_stay(self, page):
        strip = build_personal_link_js()
        assert 'var KEYS = ["name", "email", "athlete"]' in strip
        assert page.index("window.rlPersonalLink = found;") < page.index("gtag('config'")
        assert page.index("window.rlPersonalLink = found;") < page.index("googletagmanager.com/gtag/js")

    @pytest.mark.skipif(shutil.which("node") is None, reason="node not installed")
    def test_the_patterns_as_the_browser_runs_them(self):
        values = {"plan": ["123456", "123456789012", "1234567890123", "12a456", " 123456", "123456\n", ""],
                  "ref": ["test-ref-0001", "a" * 32, "a" * 33, "short", "has space1", "test-ref-0001\n"]}
        script = ("const [pp, rp, v] = JSON.parse(require('fs').readFileSync(0, 'utf8'));"
                  "process.stdout.write(JSON.stringify([v.plan.map((x) => new RegExp(pp).test(x)),"
                  " v.ref.map((x) => new RegExp(rp).test(x))]));")
        run = subprocess.run(["node", "-e", script], input=json.dumps([PLAN_ID_PATTERN, PLAN_REF_PATTERN, values]),
                             capture_output=True, text=True, timeout=60, check=True)
        assert json.loads(run.stdout) == [[True, True, False, False, False, False, False],
                                          [True, True, False, False, False, False]]


class TestAnalytics:
    def test_debrief_events_with_presence_only(self, js):
        assert 'ga4("debrief_start", withPresence({ variant: "race_debrief" }))' in js
        assert 'ga4("debrief_submit", withPresence({ variant: "race_debrief" }))' in js
        fn = js[js.index("function withPresence(params) {"):]
        fn = fn[:fn.index("\n  }\n")]
        assert 'params["has_" + el.name] = el.value ? "yes" : "no";' in fn

    def test_no_event_on_load_or_a_timer(self, js):
        assert js.count("ga4(") == 3  # the helper's name inside onEdit, submit, and the definition
        on_edit = js[js.index("function onEdit(e) {"):js.index('form.addEventListener("input", onEdit);')]
        assert "debrief_start" in on_edit
        for timer in re.findall(r"set(?:Timeout|Interval)\(function\(\) \{[^}]*\}", js):
            assert "ga4(" not in timer


class TestRatingLine:
    def test_hidden_until_a_stored_submission_with_a_plan(self, page, js):
        assert ('<p id="tp-rating" class="rl-debrief-rating" hidden>If you have a minute, '
                '<a id="tp-rating-link" href="https://www.trainingpeaks.com/training-plans/" target="_blank" '
                'rel="noopener">rate the plan on TrainingPeaks</a>, whatever score you&#39;d give it.</p>') in page
        submit = js[js.index('form.addEventListener("submit"'):]
        assert submit.index('if (!ok) { throw new Error("worker transport failed"); }') < submit.index("showRating(d);")

    def test_links_the_plans_own_page_and_is_not_gated_on_any_answer(self, js):
        assert TP_PLAN_URL == "https://www.trainingpeaks.com/training-plans/cycling/tp-"
        fn = js[js.index("function showRating(d) {"):js.index('form.addEventListener("submit"')]
        assert 'document.getElementById("tp-rating-link").href = TP_PLAN_URL + d.plan;' in fn
        assert "!matches(plan, d.plan)" in fn
        for answer in ("recommend", "raced", "goal_met", "load", "completion"):
            assert answer not in fn, answer


class TestSafety:
    def test_no_innerhtml_or_inline_handlers(self, page, js):
        assert "innerHTML" not in js
        assert not re.search(r"\son(click|submit|change|input)=", page)

    def test_honeypot_present(self, page):
        assert 'name="website" class="rl-apply-honeypot"' in page

    def test_every_text_and_area_field_is_capped(self, page):
        for tag in re.findall(r"<textarea [^>]*>|<input type=\"text\" [^>]*>", page):
            if 'name="website"' in tag:
                continue
            assert 'maxlength="4000"' in tag, tag

    def test_brand_tokens_only(self):
        css = debrief.build_debrief_css()
        assert not re.search(r"#[0-9a-fA-F]{3,6}\b", css)
        assert "border-radius" not in css and "box-shadow" not in css
        assert "--gg-" not in css
