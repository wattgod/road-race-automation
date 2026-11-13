"""The custom plan billed every 4 weeks (race_plan_4weekly) on roadielabs.com.

Guards three things:

1. Price math parity. The checkout server has no quote endpoint, so every
   payment count and total the site shows must use the server's exact math
   (athlete-custom-training-plan-pipeline webhook/race_plan_subscription.py).
   Fixed cases from the design (SUBSCRIPTION_DESIGN.md §8.3) are pinned here,
   and the browser copy is run in Node against the Python.
2. The questionnaire checks out the new product, never the retired one-off.
3. No retired one-off terms ("$249", "One-time payment", "/mo", "monthly",
   "7-day") survive near the custom plan offer on any generated page.
"""

import json
import re
import shutil
import subprocess
import sys
from datetime import date, timedelta
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "wordpress"))

import plan_offer  # noqa: E402
from plan_offer import (  # noqa: E402
    BLOCK_PRICE_CENTS, WEEK_PRICE_CENTS, REFUND_WINDOW_DAYS, money,
    payment_plan, plan_quote_js, plan_summary, weeks_until,
)

FORM_JS = ROOT / "web" / "training-plans-form.js"

# (weeks to race, payment count, total cents): SUBSCRIPTION_DESIGN.md §8.3
FIXED_CASES = [
    (1, 1, 1250),
    (4, 1, 4999),
    (5, 2, 6249),
    (6, 2, 7499),
    (8, 2, 9998),
    (17, 5, 21246),
    (30, 8, 37493),
    (52, 13, 64987),
]


class TestServerParity:
    def test_constants_match_server(self):
        assert BLOCK_PRICE_CENTS == 4999
        assert WEEK_PRICE_CENTS == 1250
        assert REFUND_WINDOW_DAYS == 14
        assert plan_offer.CHECKOUT_PRODUCT == "race_plan_4weekly"

    @pytest.mark.parametrize("weeks,count,total", FIXED_CASES)
    def test_fixed_cases(self, weeks, count, total):
        plan = payment_plan(weeks)
        assert plan["payment_count"] == count
        assert plan["total_cents"] == total
        assert plan["total_display"] == money(total)

    def test_named_cases(self):
        assert payment_plan(4)["payments_cents"] == [4999]
        assert payment_plan(6)["payments_cents"] == [4999, 2500]
        assert payment_plan(8)["payments_cents"] == [4999, 4999]
        assert payment_plan(30)["payments_cents"] == [4999] * 7 + [2500]
        assert plan_summary(30) == "8 payments, $374.93 in all"
        assert plan_summary(4) == "1 payment, $49.99 in all"

    def test_weeks_until_counts_part_week_as_one(self):
        today = date(2030, 1, 15)
        assert weeks_until(today + timedelta(days=1), today) == 1
        assert weeks_until(today + timedelta(days=7), today) == 1
        assert weeks_until(today + timedelta(days=8), today) == 2
        with pytest.raises(ValueError):
            weeks_until(today, today)

    def test_no_minimum_and_no_cap(self):
        assert payment_plan(1)["first_payment_cents"] == 1250
        assert payment_plan(104)["total_cents"] == 26 * 4999


def _run_node(script: str) -> str:
    result = subprocess.run(["node", "-e", script], capture_output=True,
                            text=True, timeout=20)
    assert result.returncode == 0, result.stderr
    return result.stdout.strip()


@pytest.mark.skipif(shutil.which("node") is None, reason="node not installed")
class TestBrowserParity:
    def test_js_quote_matches_python(self):
        today = date(2030, 1, 15)
        offsets = [1, 3, 7, 8, 27, 28, 29, 41, 42, 56, 120, 205, 210, 364]
        dates = [(today + timedelta(days=d)).isoformat() for d in offsets]
        script = plan_quote_js() + (
            f"var dates={json.dumps(dates)};"
            f"console.log(JSON.stringify(dates.map(function(d){{return rlPlanQuote(d,{json.dumps(today.isoformat())});}})));"
        )
        quotes = json.loads(_run_node(script))
        for d, q in zip(dates, quotes):
            weeks = weeks_until(date.fromisoformat(d), today)
            plan = payment_plan(weeks)
            assert q["weeks"] == weeks, d
            assert q["payments"] == plan["payment_count"], d
            assert q["totalCents"] == plan["total_cents"], d
            assert q["firstCents"] == plan["first_payment_cents"], d
            assert q["total"] == plan["total_display"], d
            assert q["summary"] == plan_summary(weeks), d

    def test_js_quote_refuses_past_and_bad_dates(self):
        script = plan_quote_js() + (
            "console.log(JSON.stringify(["
            "rlPlanQuote('2030-01-15','2030-01-15'),"
            "rlPlanQuote('2029-12-01','2030-01-15'),"
            "rlPlanQuote('','2030-01-15'),"
            "rlPlanQuote('not-a-date','2030-01-15')]));"
        )
        assert json.loads(_run_node(script)) == [None, None, None, None]

    def test_form_js_parses(self):
        _run_node(f"new Function({json.dumps(FORM_JS.read_text())});")


@pytest.fixture(scope="module")
def js():
    return FORM_JS.read_text(encoding="utf-8")


class TestQuestionnaireCheckout:
    def test_form_carries_generated_quote_block(self, js):
        start = js.index(plan_offer.JS_BEGIN_MARKER) + len(plan_offer.JS_BEGIN_MARKER)
        end = js.index(plan_offer.JS_END_MARKER)
        block = "\n".join(line.strip() for line in js[start:end].strip().splitlines())
        expected = "\n".join(line.strip() for line in plan_quote_js().strip().splitlines())
        assert block == expected

    def test_form_checks_out_the_4_weekly_plan(self, js):
        assert "var CHECKOUT_PRODUCT = 'race_plan_4weekly';" in js
        assert "workerData.product = CHECKOUT_PRODUCT;" in js
        assert "intake_flow" not in js

    def test_form_has_no_one_off_pricing(self, js):
        for stale in ("PRICE_PER_WEEK", "PRICE_CAP", "MIN_WEEKS", "249"):
            assert stale not in js, stale


# ── Retired one-off terms near the custom plan offer ──────────────────

FORBIDDEN = [
    (re.compile(r"\$249"), "$249"),
    (re.compile(r"one[- ]time (payment|purchase)", re.I), "one-time payment"),
    (re.compile(r"no subscription", re.I), "no subscription"),
    (re.compile(r"/\s*mo\b", re.I), "/mo"),
    (re.compile(r"\bmonthly\b", re.I), "monthly"),
    # The old plan's refund window. Not every "7 days": the site footer's
    # Endure trial ("Try Endure for 7 days") and course advice ("arrive 5-7
    # days early") are not plan terms.
    (re.compile(r"\b7[- ]day (full )?(refund|money|guarantee)", re.I), "7-day refund"),
    (re.compile(r"within 7 days", re.I), "within 7 days"),
    (re.compile(r"\$15\s*(/|a |per )\s*w", re.I), "$15 a week"),
    (re.compile(r"\$2/day", re.I), "$2/day"),
    (re.compile(r"capped at", re.I), "capped at"),
]


def assert_clean(text: str, where: str):
    hits = [label for pattern, label in FORBIDDEN if pattern.search(text)]
    assert not hits, f"{where}: retired one-off terms {hits}"


def _section(html: str, start_marker: str, end_marker: str) -> str:
    start = html.index(start_marker)
    end = html.index(end_marker, start + len(start_marker))
    return html[start:end]


@pytest.fixture(scope="module")
def race():
    from generate_neo_brutalist import normalize_race_data
    raw = json.loads((ROOT / "race-data" / "maratona-dles-dolomites.json").read_text())
    return normalize_race_data(raw)


class TestNoRetiredTermsNearOffer:
    def test_race_page_offer(self, race):
        from generate_neo_brutalist import build_custom_plan_offer, generate_page
        offer = build_custom_plan_offer(race)
        assert plan_offer.PRICE_LINE_UPPER in offer
        assert_clean(offer, "race page offer")
        html = generate_page(race)
        assert_clean(_section(html, 'data-measure-section="custom-plan"', "</section>"),
                     "race page offer (rendered)")

    def test_race_page_quote_uses_race_date(self, race):
        from generate_neo_brutalist import build_custom_plan_offer
        offer = build_custom_plan_offer(race)
        assert "data-plan-quote" in offer
        assert "Ends after race week" in offer

    def test_race_page_inline_js(self):
        from generate_neo_brutalist import build_inline_js
        js = build_inline_js()
        assert "function rlPlanQuote" in js
        assert_clean(js, "race page inline JS")

    def test_dormant_race_page_ctas(self, race):
        from generate_neo_brutalist import (
            build_prep_strip, build_sticky_cta, build_training,
            build_train_for_race,
        )
        for name, html in [
            ("sticky", build_sticky_cta(race["name"], race["slug"])),
            ("training", build_training(race)),
            ("prep strip", build_prep_strip(race)),
            ("train for race", build_train_for_race(race, include_commerce=True)),
        ]:
            assert_clean(html, name)

    def test_training_plans_page(self):
        from generate_training_plans import generate_training_page
        html = generate_training_page()
        assert plan_offer.PRICE_LINE in html
        assert f"{REFUND_WINDOW_DAYS} days" in html
        assert_clean(html, "/training-plans/")

    def test_race_training_plan_page(self):
        from generate_training_plan_pages import generate_page, load_pack
        rd = json.loads((ROOT / "race-data" / "maratona-dles-dolomites.json").read_text())
        rd = rd.get("race", rd)
        rd.setdefault("slug", "maratona-dles-dolomites")
        html = generate_page(rd, load_pack("maratona-dles-dolomites"))
        assert_clean(html, "/race/<slug>/training-plan/")

    def test_questionnaire(self):
        from generate_questionnaire import generate_questionnaire_page
        html = generate_questionnaire_page()
        assert 'id="gg-plan-quote"' in html
        assert_clean(html, "/questionnaire/")

    def test_success_page(self):
        from generate_success_pages import build_training_plan_success
        assert_clean(build_training_plan_success(), "/training-plans/success/")

    def test_homepage_and_about_ctas(self):
        from generate_homepage import build_training_cta
        from generate_about import build_ctas
        assert_clean(build_training_cta(), "homepage training CTA")
        assert_clean(_section(build_ctas(), "<h3>Training Plans</h3>", "</div>"),
                     "about training CTA")

    def test_vs_and_state_and_prep_kit_ctas(self, race):
        from generate_vs_pages import build_training_cta
        from generate_prep_kit import build_pk_footer_cta
        assert_clean(build_training_cta(race, race), "vs page CTA")
        assert_clean(build_pk_footer_cta(race), "prep kit footer CTA")
        src = (ROOT / "wordpress" / "generate_state_hubs.py").read_text()
        assert_clean(_section(src, 'class="rl-state-cta"', "</section>"), "state hub CTA")

    def test_goals_offer(self):
        from generate_goals_2027 import OFFER
        for plan in OFFER["plans"]:
            assert_clean(plan["price"], "goals step-two offer")
            assert plan_offer.PRICE_LINE in plan["price"]

    def test_legal_training_plan_terms(self):
        from generate_legal_pages import get_terms_content
        terms = get_terms_content()
        plan_terms = _section(terms, "<li><strong>Training plans</strong>", "</li>")
        assert_clean(plan_terms, "terms: training plans")
        assert "$49.99 every 4 weeks" in plan_terms
        assert "14 days" in plan_terms
        # The 7-day window left in Payments & Refunds is consulting's only.
        refunds = _section(terms, "<h2>Payments &amp; Refunds</h2>", "<h2>Intellectual")
        plan_sentence = next(x for x in refunds.split(". ") if "raining plan" in x)
        assert_clean(plan_sentence, "terms: refunds sentence for training plans")

    def test_ab_experiments_cannot_put_old_prices_back(self):
        from ab_experiments import EXPERIMENTS
        for exp in EXPERIMENTS:
            for variant in exp["variants"]:
                assert_clean(variant["content"], f"A/B {exp['id']}:{variant['id']}")
        exported = (ROOT / "web" / "ab" / "experiments.json").read_text()
        assert_clean(exported, "web/ab/experiments.json")
