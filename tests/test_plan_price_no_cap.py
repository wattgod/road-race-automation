"""The training plan has no price cap.

$15 for every week until the race, 4-week minimum, no cap (Matti,
2026-10-23). The checkout server (athlete-custom-training-plan-pipeline
webhook/app.py compute_plan_price) charges exactly that, so any "$249" cap in
copy or a calculator shows a long-plan buyer less than Stripe charges them.
Mirrors gravel-race-automation tests/test_pricing_single_source.py.
"""

import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))
sys.path.insert(0, str(PROJECT_ROOT / "wordpress"))

import preflight_quality  # noqa: E402
import generate_training_plans as tp  # noqa: E402


def _expected_price(weeks: int) -> int:
    """The server formula, frozen here: $15/week, 4-week minimum, no cap."""
    return max(4, weeks) * 15


def test_no_cap_copy_or_calculator_anywhere():
    hits = preflight_quality.find_plan_cap_mentions()
    assert hits == [], "Retired $249 cap is back:\n" + "\n".join(hits)


@pytest.mark.parametrize("line", [
    "$15/week, capped at $249.",
    "Delivery within 24 hours. $249 cap.",
    "var price = Math.min(weeks * 15, 249);",
    "PRICE_CAP = 300",
])
def test_scanner_catches_cap_copy(line):
    assert any(p.search(line) for p in preflight_quality.PLAN_CAP_PATTERNS)


def test_jsonld_has_no_fake_high_price():
    ld = tp.build_jsonld()
    data = json.loads(re.search(r'<script type="application/ld\+json">(.*)</script>',
                                ld, re.DOTALL).group(1))
    offers = data["offers"]
    assert "highPrice" not in offers
    assert "offerCount" not in offers
    assert offers["lowPrice"] == str(_expected_price(1))


def test_faq_prices_match_the_formula():
    faq = dict(tp.FAQ_ITEMS)["How is the price calculated?"]
    for weeks in (6, 12, 20):
        assert f"${_expected_price(weeks)}" in faq
    assert "cap" not in faq.lower()


@pytest.mark.skipif(shutil.which("node") is None, reason="node not installed")
@pytest.mark.parametrize("weeks", [1, 4, 16, 17, 20, 40])
def test_questionnaire_form_js_charges_every_week(weeks):
    js = (PROJECT_ROOT / "web" / "training-plans-form.js").read_text()
    m = re.search(r"var PRICE_PER_WEEK = (\d+);.*?var MIN_WEEKS = (\d+);", js, re.DOTALL)
    assert m, "pricing constants missing from training-plans-form.js"
    body = re.search(r"function computePrice\(raceDateStr\) \{.*?\n  \}", js, re.DOTALL)
    assert body, "computePrice missing from training-plans-form.js"
    script = (
        f"var PRICE_PER_WEEK = {m.group(1)}; var MIN_WEEKS = {m.group(2)};\n"
        + body.group(0)
        + "\nvar t = new Date(); t.setHours(0,0,0,0);"
        + f"\nvar d = new Date(t.getTime() + {weeks} * 7 * 86400000);"
        + "\nvar s = d.getFullYear() + '-' + String(d.getMonth()+1).padStart(2,'0')"
        + " + '-' + String(d.getDate()).padStart(2,'0');"
        + "\nconsole.log(JSON.stringify(computePrice(s)));"
    )
    out = subprocess.run(["node", "-e", script], capture_output=True, text=True, timeout=10)
    assert out.returncode == 0, out.stderr
    result = json.loads(out.stdout)
    assert result["weeks"] == max(4, weeks)
    assert result["price"] == _expected_price(weeks)


# --- Calendar days, not elapsed hours (Astra review on PR #109) -------------
# The server counts calendar days: (race_date - date.today()).days. Browsers
# that diff local midnights pick up an extra hour across the autumn clock
# change, and Math.ceil turned that hour into one more billable week (Denver,
# Jun 15 -> Nov 2 2026: 140 days on the server, 141 in the browser, $300 vs
# $315). Each calculator below runs for real in node with "today" frozen.

_DST_CASES = [
    # (today, race) pairs that straddle a clock change and land on whole weeks
    ("2026-06-15", "2026-11-02"),  # US fall back Nov 1
    ("2026-02-02", "2026-03-16"),  # US spring forward Mar 8
    ("2026-09-07", "2026-11-02"),  # EU fall back Oct 25
    ("2026-03-02", "2026-04-06"),  # EU spring forward Mar 29
    ("2026-06-15", "2026-11-03"),  # one day past whole weeks
]
_TIMEZONES = ["America/Denver", "Europe/London", "Australia/Sydney", "UTC"]

_FREEZE_DATE = """
var __RealDate = Date;
var __frozen = new __RealDate(%TODAY% + 'T09:30:00');
Date = function(a) {
  if (arguments.length === 0) return new __RealDate(__frozen.getTime());
  return new __RealDate(a);
};
Date.UTC = __RealDate.UTC; Date.now = function() { return __frozen.getTime(); };
"""


def _server_weeks(today: str, race: str) -> int:
    from datetime import date
    import math
    days = (date.fromisoformat(race) - date.fromisoformat(today)).days
    return max(4, math.ceil(days / 7))


def _run_node(script: str, tz: str) -> str:
    import os
    env = dict(os.environ, TZ=tz)
    out = subprocess.run(["node", "-e", script], capture_output=True, text=True,
                         timeout=10, env=env)
    assert out.returncode == 0, out.stderr
    return out.stdout.strip()


def _dom_stub(attr_id: str, race: str, ids: list) -> str:
    els = ", ".join(f"'{i}': {{textContent: ''}}" for i in ids)
    return (
        f"var __els = {{ {els} }};"
        f"__els['{attr_id}'] = {{getAttribute: function() {{ return '{race}'; }}}};"
        "var document = {getElementById: function(id) { return __els[id] || null; }};"
    )


@pytest.mark.skipif(shutil.which("node") is None, reason="node not installed")
@pytest.mark.parametrize("tz", _TIMEZONES)
@pytest.mark.parametrize("today,race", _DST_CASES)
def test_questionnaire_price_counts_calendar_days(today, race, tz):
    js = (PROJECT_ROOT / "web" / "training-plans-form.js").read_text()
    body = re.search(r"function computePrice\(raceDateStr\) \{.*?\n  \}", js, re.DOTALL)
    script = (
        _FREEZE_DATE.replace("%TODAY%", json.dumps(today))
        + "var PRICE_PER_WEEK = 15; var MIN_WEEKS = 4;\n" + body.group(0)
        + f"\nconsole.log(JSON.stringify(computePrice('{race}')));"
    )
    result = json.loads(_run_node(script, tz))
    weeks = _server_weeks(today, race)
    assert result == {"weeks": weeks, "price": weeks * 15}


@pytest.mark.skipif(shutil.which("node") is None, reason="node not installed")
@pytest.mark.parametrize("tz", _TIMEZONES)
@pytest.mark.parametrize("today,race", _DST_CASES)
def test_race_page_prep_strip_counts_calendar_days(today, race, tz):
    sys.path.insert(0, str(PROJECT_ROOT / "wordpress"))
    from generate_neo_brutalist import build_inline_js
    js = build_inline_js()
    m = re.search(r"\(function\(\) \{\n  var strip = document\.getElementById\('prep-strip'\);.*?\n\}\)\(\);",
                  js, re.DOTALL)
    assert m, "prep strip calculator missing"
    script = (
        _FREEZE_DATE.replace("%TODAY%", json.dumps(today))
        + _dom_stub("prep-strip", race, ["rl-prep-countdown", "rl-prep-cta"])
        + m.group(0)
        + "\nconsole.log(__els['rl-prep-cta'].textContent);"
    )
    weeks = _server_weeks(today, race)
    assert _run_node(script, tz) == f"BUILD MY {weeks}-WEEK PLAN — ${weeks * 15}"


@pytest.mark.skipif(shutil.which("node") is None, reason="node not installed")
@pytest.mark.parametrize("tz", _TIMEZONES)
@pytest.mark.parametrize("today,race", _DST_CASES)
def test_training_plan_page_counts_calendar_days(today, race, tz):
    sys.path.insert(0, str(PROJECT_ROOT / "wordpress"))
    from generate_training_plan_pages import build_js
    m = re.search(r"\(function\(\) \{\n  var hero = document\.getElementById\('tpp-hero'\);.*?\n\}\)\(\);",
                  build_js(), re.DOTALL)
    assert m, "training-plan page calculator missing"
    script = (
        _FREEZE_DATE.replace("%TODAY%", json.dumps(today))
        + _dom_stub("tpp-hero", race, ["rl-tpp-countdown", "rl-tpp-hero-cta", "rl-tpp-footer-cta"])
        + m.group(0)
        + "\nconsole.log(__els['rl-tpp-hero-cta'].textContent);"
    )
    weeks = _server_weeks(today, race)
    assert _run_node(script, tz) == f"BUILD MY {weeks}-WEEK PLAN — ${weeks * 15}"


def test_no_calculator_diffs_local_midnights():
    """The plan-preview calculator sits inside a click handler; guard its source."""
    src = (PROJECT_ROOT / "wordpress" / "generate_neo_brutalist.py").read_text()
    m = re.search(r"var raceDate = new Date\(raceDateStr \+ 'T00:00:00Z?'\);.*?var weeksRaw = [^\n]*",
                  src, re.DOTALL)
    assert m, "plan preview calculator missing"
    assert "T00:00:00Z" in m.group(0) and "Date.UTC(" in m.group(0)
    assert "setHours(0, 0, 0, 0)" not in m.group(0)
