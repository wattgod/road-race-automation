"""Every browser plan quote counts calendar days, so a clock change can't add a week.

The checkout server counts whole days between two dates
(athlete-custom-training-plan-pipeline webhook/race_plan_subscription.py
weeks_until). Browser code that diffs local midnights picks up an extra hour
across the autumn clock change, and Math.ceil turns that hour into one more
week (Denver, Jun 15 -> Nov 2 2026: 140 days on the server, 141 in the
browser), which shows the rider one more payment than Stripe takes. Each
calculator runs for real in node with "today" frozen, in four time zones,
and is compared with wordpress/plan_offer.py.
"""

import json
import os
import re
import shutil
import subprocess
import sys
from datetime import date
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "wordpress"))

import plan_offer  # noqa: E402

needs_node = pytest.mark.skipif(shutil.which("node") is None, reason="node not installed")

_DST_CASES = [
    # (today, race) pairs that straddle a clock change
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


def _expected(today: str, race: str) -> tuple:
    weeks = plan_offer.weeks_until(date.fromisoformat(race), date.fromisoformat(today))
    return weeks, plan_offer.plan_summary(weeks)


def _run_node(script: str, tz: str) -> str:
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


@needs_node
@pytest.mark.parametrize("tz", _TIMEZONES)
@pytest.mark.parametrize("today,race", _DST_CASES)
def test_questionnaire_quote_counts_calendar_days(today, race, tz):
    js = (PROJECT_ROOT / "web" / "training-plans-form.js").read_text()
    start = js.index(plan_offer.JS_BEGIN_MARKER)
    end = js.index(plan_offer.JS_END_MARKER)
    script = (
        _FREEZE_DATE.replace("%TODAY%", json.dumps(today))
        + js[start:end]
        + f"\nconsole.log(JSON.stringify(rlPlanQuote('{race}')));"
    )
    result = json.loads(_run_node(script, tz))
    weeks, summary = _expected(today, race)
    assert (result["weeks"], result["summary"]) == (weeks, summary)


@needs_node
@pytest.mark.parametrize("tz", _TIMEZONES)
@pytest.mark.parametrize("today,race", _DST_CASES)
def test_race_page_prep_strip_counts_calendar_days(today, race, tz):
    from generate_neo_brutalist import build_inline_js
    js = build_inline_js()
    m = re.search(r"\(function\(\) \{\n  var strip = document\.getElementById\('prep-strip'\);.*?\n\}\)\(\);",
                  js, re.DOTALL)
    assert m, "prep strip calculator missing"
    script = (
        _FREEZE_DATE.replace("%TODAY%", json.dumps(today))
        + plan_offer.plan_quote_js()
        + _dom_stub("prep-strip", race, ["rl-prep-countdown", "rl-prep-cta"])
        + m.group(0)
        + "\nconsole.log(__els['rl-prep-cta'].textContent);"
    )
    weeks, summary = _expected(today, race)
    assert _run_node(script, tz) == f"BUILD MY {weeks}-WEEK PLAN — {summary.upper()}"


@needs_node
@pytest.mark.parametrize("tz", _TIMEZONES)
@pytest.mark.parametrize("today,race", _DST_CASES)
def test_training_plan_page_counts_calendar_days(today, race, tz):
    from generate_training_plan_pages import build_js
    m = re.search(r"\(function\(\) \{\n  var hero = document\.getElementById\('tpp-hero'\);.*?\n\}\)\(\);",
                  build_js(), re.DOTALL)
    assert m, "training-plan page calculator missing"
    script = (
        _FREEZE_DATE.replace("%TODAY%", json.dumps(today))
        + plan_offer.plan_quote_js()
        + _dom_stub("tpp-hero", race, ["rl-tpp-countdown", "rl-tpp-hero-cta",
                                        "rl-tpp-footer-cta", "rl-tpp-plan-quote"])
        + m.group(0)
        + "\nconsole.log(__els['rl-tpp-hero-cta'].textContent + '|' + __els['rl-tpp-plan-quote'].textContent);"
    )
    weeks, summary = _expected(today, race)
    assert _run_node(script, tz) == f"BUILD MY {weeks}-WEEK PLAN|For this date: {summary}."


def test_plan_preview_does_not_diff_local_midnights():
    """The plan-preview calculator sits inside a click handler; guard its source."""
    src = (PROJECT_ROOT / "wordpress" / "generate_neo_brutalist.py").read_text()
    m = re.search(r"var raceDate = new Date\(raceDateStr \+ 'T00:00:00Z?'\);.*?var weeksRaw = [^\n]*",
                  src, re.DOTALL)
    assert m, "plan preview calculator missing"
    assert "T00:00:00Z" in m.group(0) and "Date.UTC(" in m.group(0)
    assert "setHours(0, 0, 0, 0)" not in m.group(0)
