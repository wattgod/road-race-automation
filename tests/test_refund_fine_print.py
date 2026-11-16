"""Refund terms are fine print, never part of the pitch (Matti, 2026-11-16)."""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "wordpress"))

from generate_questionnaire import build_form_html  # noqa: E402
from generate_training_plans import build_pricing  # noqa: E402


def test_training_plans_refund_sits_only_in_fine_print():
    section = build_pricing()
    assert "Day Refund" not in section
    fine = re.search(r'<div class="rl-tp-fine">.*?</div>', section, re.S)
    assert fine, "pricing lost its fine-print line"
    assert section.lower().count("refund") == fine.group(0).lower().count("refund")


def test_questionnaire_trust_badges_carry_no_refund():
    html = build_form_html()
    assert "Day Refund" not in html
    badges = re.findall(r'<span class="gg-trust-badge">(.*?)</span>', html)
    assert badges and not [b for b in badges if "refund" in b.lower()]
