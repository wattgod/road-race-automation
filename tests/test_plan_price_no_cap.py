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
