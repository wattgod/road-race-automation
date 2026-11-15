"""RL-03: Terms and Privacy name the real seller, and every refund promise a
sales page makes is the rule the Terms state for that product.

If a sales page starts promising a refund it doesn't promise today, or the
Terms change a product's rule, these tests fail until both say the same thing.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "wordpress"))

from generate_legal_pages import (  # noqa: E402
    SELLER_ADDRESS,
    SELLER_NAME,
    get_privacy_content,
    get_terms_content,
)
from plan_offer import REFUND_WINDOW_DAYS  # noqa: E402

LLC = "Gravel God Cycling LLC"
ADDRESS = "2183 Lombardy St, Longmont, CO 80503"
REFUND_WORDS = re.compile(r"refund|money-back|money back|guarantee", re.I)


@pytest.fixture(scope="module")
def terms():
    return get_terms_content()


@pytest.fixture(scope="module")
def privacy():
    return get_privacy_content()


def _refund_rule(terms: str, product: str) -> str:
    m = re.search(rf'<li id="refund-{product}">(.*?)</li>', terms, re.S)
    assert m, f"Terms have no refund rule for {product}"
    return m.group(1)


def _visible_text(html: str) -> str:
    html = re.sub(r"<(script|style)\b.*?</\1>", " ", html, flags=re.S | re.I)
    return re.sub(r"<[^>]+>", " ", html)


# ── Seller identity ───────────────────────────────────────────


class TestSeller:
    def test_constants_are_the_llc(self):
        assert SELLER_NAME == LLC
        assert SELLER_ADDRESS == ADDRESS

    def test_terms_name_llc_and_address(self, terms):
        assert LLC in terms
        assert ADDRESS in terms

    def test_privacy_names_llc_as_controller(self, privacy):
        assert ADDRESS in privacy
        assert f"{LLC} is the controller" in privacy

    def test_no_sole_proprietor(self, terms, privacy):
        for text in (terms, privacy):
            assert "sole proprietor" not in text.lower()


# ── One refund rule per product, matching its sales page ──────


class TestTrainingPlanRefund:
    def test_sales_pages_promise_the_window(self):
        from generate_training_plans import FAQ_ITEMS, build_pricing
        from generate_training_plan_pages import build_cta

        promise = f"Within {REFUND_WINDOW_DAYS} days of your first payment"
        assert promise in build_pricing()
        assert any(promise in a for _, a in FAQ_ITEMS)
        cta = build_cta({"name": "Test Race", "slug": "test-race"})
        assert f"within {REFUND_WINDOW_DAYS} days of your first payment" in cta
        assert "full refund" in cta

    def test_terms_rule_matches(self, terms):
        rule = _refund_rule(terms, "training-plans")
        assert f"Full refund of your first payment within {REFUND_WINDOW_DAYS} days" in rule
        assert "later payments aren&rsquo;t refunded" in rule
        # No second, different window anywhere in the plan terms.
        plan_terms = re.search(r"<li><strong>Training plans</strong>(.*?)</li>", terms, re.S).group(1)
        windows = set(re.findall(r"(\d+) days", plan_terms + rule))
        assert windows == {str(REFUND_WINDOW_DAYS)}


class TestCourseRefund:
    def test_sales_page_promise_is_the_terms_rule(self, terms):
        from generate_courses_page import COURSE_REFUND_LINE, build_faq

        assert COURSE_REFUND_LINE == "30-day money-back guarantee on both courses."
        assert COURSE_REFUND_LINE in build_faq()
        assert COURSE_REFUND_LINE in _refund_rule(terms, "courses")


class TestProductsWhoseSalesPagePromisesNoRefund:
    """Coaching and consulting sales pages make no refund promise. The Terms
    keep their existing rule (an open decision for Matti, not a new policy).
    If either page starts promising one, update the Terms rule with it."""

    def test_coaching_page_promises_no_refund(self):
        from generate_coaching import generate_coaching_page

        assert not REFUND_WORDS.search(_visible_text(generate_coaching_page()))

    def test_consulting_page_promises_no_refund(self):
        from generate_consulting import generate_consulting_page

        assert not REFUND_WORDS.search(_visible_text(generate_consulting_page()))

    def test_terms_keep_existing_rules(self, terms):
        assert "No refunds are issued for partially completed billing cycles." in _refund_rule(terms, "coaching")
        assert "case-by-case" in _refund_rule(terms, "consulting")

    def test_every_product_has_exactly_one_rule(self, terms):
        ids = re.findall(r'<li id="refund-([a-z-]+)">', terms)
        assert sorted(ids) == ["coaching", "consulting", "courses", "training-plans"]
