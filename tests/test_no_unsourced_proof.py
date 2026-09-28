"""Guard: no unsourced social proof on Roadie Labs' commercial pages.

Until 2026-09-28 roadielabs.com showed 53 testimonials credited to "Gravel God
athletes" (50 on /about/, 3 on /training-plans/). They were placeholder text
written by Claude sessions in Feb 2026, not real people. The site also claimed
"100+ athletes coached / 1,000+ plans sold" (unverified) and ran a
`coaching_scarcity` A/B test ("Limited spots.", "20 athletes/month.").

Receipts spec (wattgod/gravel-race-automation
docs/specs/receipts-social-proof-2026.md, section 4): nothing renders unless it
traces to a real person, a source, and written approval of the exact text.
This guard renders the pages where coach proof would live and fails on:

- any legacy testimonial class (Roadie's and Gravel God's card classes);
- `aggregateRating`, "Stars from", "athletes/month", "Next window",
  "Limited spots", or the borrowed "same coach, same plan engine" caption;
- athlete / plan-sold counts ("100+ athletes coached", "Plans sold 1,000+");
- a `<cite>` that is not inside an element carrying `data-receipt-id`;
- a `data-receipt-id` that does not resolve to an approved receipt.

It does not ban `<blockquote>`: the homepage quotes race taglines, and race
pages quote YouTube riders with a channel `<cite>`. Race pages are out of
scope here; their `aggregateRating` comes only from `racer_rating` data with
3+ ratings (generate_neo_brutalist.py).
"""

from __future__ import annotations

import html as html_lib
import json
import re
import sys
from html.parser import HTMLParser
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
WORDPRESS_DIR = PROJECT_ROOT / "wordpress"
if str(WORDPRESS_DIR) not in sys.path:
    sys.path.insert(0, str(WORDPRESS_DIR))

import ab_experiments  # noqa: E402
import generate_about  # noqa: E402
import generate_coaching  # noqa: E402
import generate_coaching_apply  # noqa: E402
import generate_consult_intake  # noqa: E402
import generate_consulting  # noqa: E402
import generate_courses_page  # noqa: E402
import generate_homepage  # noqa: E402
import generate_methodology  # noqa: E402
import generate_questionnaire  # noqa: E402
import generate_success_pages  # noqa: E402
import generate_training_plan_pages  # noqa: E402
import generate_training_plans  # noqa: E402


# Card-level classes the placeholder quotes rendered with, in this repo's
# history, plus Gravel God's (the fork source) so a copy-over is caught too.
LEGACY_TESTIMONIAL_CLASSES = frozenset({
    "rl-about-testimonial", "rl-about-testimonial-meta",
    "rl-about-testimonial-provenance", "rl-about-carousel",
    "rl-tp-testimonial", "rl-tp-testimonials", "rl-tp-testimonial-provenance",
    "rl-coach-testimonial", "rl-coach-testimonials",
    "rl-coach-testimonial-meta", "rl-coach-testimonials-more",
    "rl-coach-testimonials-provenance",
    "rl-hp-test-card", "rl-hp-test-quote", "rl-hp-test-grid",
    "rl-hp-test-name", "rl-hp-test-attr",
    "gg-about-testimonial", "gg-tp-testimonial", "gg-coach-testimonial",
    "gg-consult-testimonial",
})

# The homepage coaching band still uses this wrapper class. It renders a
# sentence and a CTA, no quotes (owner ruling 2026-07-18: no homepage
# testimonials), so it is the one allowed class token containing "testimonial".
ALLOWED_TESTIMONIAL_CLASS_TOKENS = frozenset({"rl-hp-testimonials"})

BANNED_STRINGS = (
    "aggregateRating",
    "Stars from",
    "athletes/month",
    "Next window",
    "Limited spots",
    "same coach, same plan engine",
)

COUNT_PATTERNS = (
    r"\b\d[\d,]*\+?\s+(?:athletes|riders|clients)\s+coached\b",
    r"\bcoached\s+(?:over\s+|more\s+than\s+)?\d[\d,]*\+?\s+(?:athletes|riders|clients)\b",
    r"\b\d[\d,]*\+?\s+(?:training\s+)?plans\s+sold\b",
    r"\bsold\s+(?:over\s+|more\s+than\s+)?\d[\d,]*\+?\s+(?:training\s+)?plans\b",
    r"\b(?:athletes|clients)\s+coached\s*:?\s*\d",
    r"\bplans\s+sold\s*:?\s*\d",
)

# Approved receipt ids. Empty: no consented receipts exist yet. When the
# receipts ledger loader lands (Receipts spec PR-4), resolve against it here.
KNOWN_RECEIPT_IDS: frozenset[str] = frozenset()

# Placeholder names that were live on roadielabs.com. They are invented, not
# people; listed so a restore from git history fails loudly.
PLACEHOLDER_NAMES = (
    "Sarah K.", "Greg F.", "Stephanie H.", "Chris M.", "Megan T.",
    "Jason R.", "Sarah M.", "Mark D.",
)


class _ProofScanner(HTMLParser):
    """Collects testimonial classes, receipt ids and unreceipted <cite>s."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.stack: list[tuple[str, bool]] = []  # (tag, carries receipt id)
        self.findings: list[str] = []
        self.receipt_ids: list[str] = []

    def _inside_receipt(self) -> bool:
        return any(has_id for _, has_id in self.stack)

    def handle_starttag(self, tag, attrs):
        attr = dict(attrs)
        for token in (attr.get("class") or "").split():
            if token in LEGACY_TESTIMONIAL_CLASSES or (
                "testimonial" in token and token not in ALLOWED_TESTIMONIAL_CLASS_TOKENS
            ):
                self.findings.append(f'testimonial class "{token}" on <{tag}>')
        receipt_id = attr.get("data-receipt-id")
        if receipt_id is not None:
            self.receipt_ids.append(receipt_id)
        if tag == "cite" and not self._inside_receipt():
            self.findings.append("<cite> outside a data-receipt-id element")
        if tag not in _VOID_TAGS:
            self.stack.append((tag, receipt_id is not None))

    def handle_startendtag(self, tag, attrs):
        # Self-closing tags carry attributes but never wrap a <cite>.
        self.handle_starttag(tag, attrs)
        if tag not in _VOID_TAGS and self.stack and self.stack[-1][0] == tag:
            self.stack.pop()

    def handle_endtag(self, tag):
        for i in range(len(self.stack) - 1, -1, -1):
            if self.stack[i][0] == tag:
                del self.stack[i:]
                return


_VOID_TAGS = frozenset({
    "area", "base", "br", "col", "embed", "hr", "img", "input", "link",
    "meta", "source", "track", "wbr",
})


def _visible_text(markup: str) -> str:
    text = re.sub(r"<[^>]+>", " ", markup)
    return re.sub(r"\s+", " ", html_lib.unescape(text))


def find_banned_copy(markup: str) -> list[str]:
    """Banned proof strings and unverified counts in raw markup or its text."""
    haystack = markup + "\n" + _visible_text(markup)
    findings = [
        f'banned string "{s}"' for s in BANNED_STRINGS
        if s.lower() in haystack.lower()
    ]
    for pattern in COUNT_PATTERNS:
        m = re.search(pattern, haystack, re.IGNORECASE)
        if m:
            findings.append(f'unverified count "{m.group(0)}"')
    return findings


def find_unsourced_proof(markup: str, known_receipt_ids=KNOWN_RECEIPT_IDS) -> list[str]:
    """Every unsourced-proof finding in one rendered page."""
    scanner = _ProofScanner()
    scanner.feed(markup)
    scanner.close()
    findings = list(scanner.findings)
    findings += [
        f'data-receipt-id "{rid}" does not resolve to an approved receipt'
        for rid in scanner.receipt_ids if rid not in known_receipt_ids
    ]
    return findings + find_banned_copy(markup)


# ── Rendered pages ──────────────────────────────────────────────


@pytest.fixture(scope="module")
def rendered_pages():
    original_fetch = generate_homepage.fetch_substack_posts
    generate_homepage.fetch_substack_posts = lambda: []
    try:
        race_index = json.loads((PROJECT_ROOT / "web" / "race-index.json").read_text())
        pages = {
            "homepage": generate_homepage.generate_homepage(
                race_index,
                race_data_dir=PROJECT_ROOT / "race-data",
                guide_path=PROJECT_ROOT / "guide" / "road-guide-content.json",
            ),
        }
    finally:
        generate_homepage.fetch_substack_posts = original_fetch

    slug = "maratona-dles-dolomites"
    race = json.loads((PROJECT_ROOT / "race-data" / f"{slug}.json").read_text())
    race = race.get("race", race)
    race.setdefault("slug", slug)

    pages.update({
        "about": generate_about.generate_about_page(),
        "training-plans": generate_training_plans.generate_training_page(),
        "coaching": generate_coaching.generate_coaching_page(),
        "coaching-apply": generate_coaching_apply.generate_apply_page(),
        "consulting": generate_consulting.generate_consulting_page(),
        "consult-intake": generate_consult_intake.generate_intake_page(),
        "questionnaire": generate_questionnaire.generate_questionnaire_page(),
        "courses": generate_courses_page.generate_courses_page(),
        "methodology": generate_methodology.generate_methodology_page(),
        f"training-plan/{slug}": generate_training_plan_pages.generate_page(
            race, generate_training_plan_pages.load_pack(slug)
        ),
    })
    for key in generate_success_pages.PAGES:
        pages[f"success/{key}"] = generate_success_pages.generate_success_page(key)
    return pages


PAGE_NAMES = (
    "homepage", "about", "training-plans", "coaching", "coaching-apply",
    "consulting", "consult-intake", "questionnaire", "courses", "methodology",
    "training-plan/maratona-dles-dolomites",
)


@pytest.mark.parametrize("page", PAGE_NAMES)
def test_page_carries_no_unsourced_proof(rendered_pages, page):
    findings = find_unsourced_proof(rendered_pages[page])
    assert not findings, f"{page}: " + "; ".join(findings)


def test_success_pages_carry_no_unsourced_proof(rendered_pages):
    success = {k: v for k, v in rendered_pages.items() if k.startswith("success/")}
    assert success, "no success pages rendered"
    for name, markup in success.items():
        findings = find_unsourced_proof(markup)
        assert not findings, f"{name}: " + "; ".join(findings)


def test_placeholder_names_are_gone(rendered_pages):
    for name, markup in rendered_pages.items():
        for placeholder in PLACEHOLDER_NAMES:
            assert placeholder not in markup, f"{name} renders placeholder {placeholder!r}"


def test_about_has_no_athlete_results_section(rendered_pages):
    about = rendered_pages["about"]
    assert 'id="results"' not in about
    assert "Athlete Results" not in about
    assert "rl-testimonial-carousel" not in about


def test_training_plans_has_no_testimonials_section(rendered_pages):
    page = rendered_pages["training-plans"]
    assert 'id="testimonials"' not in page
    assert "Take My Word" not in page


def test_bio_keeps_trainingpeaks_tenure_without_counts(rendered_pages):
    for page in ("about", "consulting"):
        assert "TrainingPeaks" in rendered_pages[page], page
        assert not find_banned_copy(rendered_pages[page]), page


# ── A/B copy is injected at runtime, so check it at the source ──


def _variant_copy(experiments) -> list[tuple[str, str]]:
    return [
        (exp["id"], v["content"])
        for exp in experiments
        for v in exp["variants"]
    ]


def test_ab_source_variants_have_no_scarcity_or_counts():
    for exp_id, content in _variant_copy(ab_experiments.EXPERIMENTS):
        assert not find_banned_copy(content), f"{exp_id}: {content!r}"


def test_exported_experiments_json_has_no_scarcity_or_counts():
    exported = json.loads((PROJECT_ROOT / "web" / "ab" / "experiments.json").read_text())
    ids = {exp["id"] for exp in exported["experiments"]}
    assert "coaching_scarcity" not in ids
    for exp_id, content in _variant_copy(exported["experiments"]):
        assert not find_banned_copy(content), f"{exp_id}: {content!r}"


# ── Planted regressions: the guard must fire ────────────────────


PLANTED = {
    "about card": (
        '<blockquote class="rl-about-testimonial"><p>Best plan ever.</p>'
        '<footer><strong>Test Rider A</strong></footer></blockquote>',
        "rl-about-testimonial",
    ),
    "training-plans card": (
        '<div class="rl-tp-testimonial"><p>Great.</p>'
        '<cite>&mdash; Test Rider B &middot; Some Race</cite></div>',
        "rl-tp-testimonial",
    ),
    "gravel god card": (
        '<div class="gg-coach-testimonial"><p>Great.</p></div>',
        "gg-coach-testimonial",
    ),
    "new testimonial class": (
        '<div class="rl-new-testimonial-card"><p>Great.</p></div>',
        "rl-new-testimonial-card",
    ),
    "bare cite": (
        '<blockquote><p>Great.</p><cite>Test Rider C</cite></blockquote>',
        "<cite> outside",
    ),
    "aggregate rating": (
        '<script type="application/ld+json">{"@type":"Product",'
        '"aggregateRating":{"@type":"AggregateRating","ratingValue":"4.7"}}</script>',
        "aggregateRating",
    ),
    "stars from": ("<p>4.7 Stars from 100+ Reviews</p>", "Stars from"),
    "athletes per month": ("<p>20 athletes/month.</p>", "athletes/month"),
    "next window": ("<p>Next window: April.</p>", "Next window"),
    "limited spots": ("<p>Limited spots &mdash; opens quarterly.</p>", "Limited spots"),
    "borrowed caption": (
        "<p>Gravel God athletes &mdash; same coach, same plan engine, different surface.</p>",
        "same coach, same plan engine",
    ),
    "coached count prose": (
        "<p>I&#39;ve coached 100+ athletes and sold over 1,000 training plans.</p>",
        "coached 100+ athletes",
    ),
    "coached count list": (
        "<p>Twelve years at TrainingPeaks, 100+ athletes coached, 1,000+ training plans sold.</p>",
        "100+ athletes coached",
    ),
    "bio card rows": (
        "<dl><dt>Athletes coached</dt><dd>100+</dd><dt>Plans sold</dt><dd>1,000+</dd></dl>",
        "Athletes coached 1",
    ),
    "unresolved receipt": (
        '<figure data-receipt-id="rcpt-made-up"><blockquote><p>Great.</p></blockquote>'
        "<cite>Test Rider D</cite></figure>",
        "does not resolve",
    ),
}


@pytest.mark.parametrize("case", sorted(PLANTED))
def test_guard_fires_on_planted_regression(case):
    markup, expected = PLANTED[case]
    findings = find_unsourced_proof(f"<html><body>{markup}</body></html>")
    assert any(expected in f for f in findings), (case, findings)


def test_guard_fires_through_the_real_about_generator(monkeypatch):
    """Plant a card inside the real /about/ render, not just a fragment."""
    original = generate_about.build_coaching

    def planted_coaching():
        return original() + (
            '<blockquote class="rl-about-testimonial"><p>Placeholder.</p>'
            "<footer><strong>Test Rider E</strong></footer></blockquote>"
        )

    monkeypatch.setattr(generate_about, "build_coaching", planted_coaching)
    findings = find_unsourced_proof(generate_about.generate_about_page())
    assert any("rl-about-testimonial" in f for f in findings), findings


def test_guard_fires_through_the_real_consulting_generator(monkeypatch):
    original = generate_consulting.build_who

    def planted_who():
        return original().replace(
            "Twelve years at TrainingPeaks.",
            "Twelve years at TrainingPeaks, 100+ athletes coached.",
        )

    monkeypatch.setattr(generate_consulting, "build_who", planted_who)
    findings = find_unsourced_proof(generate_consulting.generate_consulting_page())
    assert any("unverified count" in f for f in findings), findings


# ── And stays quiet on legitimate markup ────────────────────────


def test_race_tagline_blockquote_is_allowed():
    markup = '<blockquote class="rl-hp-bento-quote">&ldquo;The Dolomites, closed to cars.&rdquo;</blockquote>'
    assert find_unsourced_proof(markup) == []


def test_homepage_coaching_band_wrapper_is_allowed():
    markup = '<section class="rl-hp-testimonials" id="testimonials"><p>A human in your corner.</p></section>'
    assert find_unsourced_proof(markup) == []


def test_cite_inside_approved_receipt_is_allowed():
    markup = (
        '<figure data-receipt-id="rcpt-001"><blockquote><p>Approved words.</p>'
        "</blockquote><cite>Test Rider F</cite></figure>"
    )
    assert find_unsourced_proof(markup, known_receipt_ids={"rcpt-001"}) == []


def test_race_field_counts_are_not_mistaken_for_coach_counts():
    markup = "<td>1,000+ riders, significant international draw.</td><p>Twelve years at TrainingPeaks.</p>"
    assert find_unsourced_proof(markup) == []
