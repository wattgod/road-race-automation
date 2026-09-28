"""Guard: no unsourced social proof on Roadie Labs' pages.

Until 2026-09-28 roadielabs.com showed 53 testimonials credited to "Gravel God
athletes" (50 on /about/, 3 on /training-plans/). They were placeholder text
written by Claude sessions in Feb 2026, not real people. The site also claimed
"100+ athletes coached / 1,000+ plans sold" (unverified) and ran a
`coaching_scarcity` A/B test ("Limited spots.", "20 athletes/month.").

Receipts spec (wattgod/gravel-race-automation
docs/specs/receipts-social-proof-2026.md, section 4): nothing renders unless it
traces to a real person, a source, and written approval of the exact text.
The same rules run in gravel-race-automation's copy of this file; keep the
two in step.

Pages come in two kinds:
  - commercial: homepage, about, training plans, coaching, coaching apply,
    consulting, consult intake, questionnaire, courses, methodology, race
    training-plan pages, success pages. Coach/product proof would live here.
  - editorial: race profiles. They quote riders (YouTube channel <cite>s),
    and race descriptions legitimately say things like "limited spots via
    reservation" or "Book early - limited spots."

Every page fails on:
  - a class token that starts with a legacy testimonial class, or contains
    "testimonial" at all (bar the coaching-band wrapper);
  - `aggregateRating` whose ratingCount doesn't trace to real Racer Ratings
    (3+) for that race; commercial pages have no rating source, so any;
  - a quote attribution that names a person, outside an element carrying
    data-receipt-id. Attributions are <cite>, a <footer> (the deleted
    /about/ card: <footer><strong>Firstname L.</strong>...), a <figcaption>,
    or a dash-led line ("<p>&mdash; Firstname L.</p>"). A publication or
    organisation ("— The Guardian", "Gravel Cyclist · 1.9K views") is not a
    person;
  - a data-receipt-id that does not resolve to an approved receipt.

Commercial pages also fail on:
  - any <cite> outside a receipt (a press quote is proof too);
  - scarcity ("Limited spots", "Next window", "athletes/month"), the
    borrowed "same coach, same plan engine" caption, rating claims
    ("Rated 4.9/5", "4.8★", "★★★★★ (123 reviews)") and coach counts
    ("100+ athletes coached", "Plans sold 1,000+").
On editorial pages those claim checks run only inside commercial elements
(data-ab, data-cta, or a class token containing "coaching" or "cta"), so a
coaching CTA on a race page is still covered.

<blockquote> itself is not banned: the homepage quotes race taglines, and
race pages quote YouTube riders with a channel <cite>.
"""

from __future__ import annotations

import functools
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
import generate_neo_brutalist  # noqa: E402
import generate_questionnaire  # noqa: E402
import generate_success_pages  # noqa: E402
import generate_training_plan_pages  # noqa: E402
import generate_training_plans  # noqa: E402
from brand_tokens import RACER_RATING_THRESHOLD  # noqa: E402

COMMERCIAL = "commercial"
EDITORIAL = "editorial"

# Card-level classes the placeholder quotes rendered with, in this repo's
# history, plus Gravel God's (the fork source) so a copy-over is caught too.
# Matched as prefixes.
LEGACY_TESTIMONIAL_CLASSES = (
    "rl-about-testimonial",    # /about/ carousel (50 placeholders)
    "rl-about-carousel",
    "rl-tp-testimonial",       # /training-plans/ (3 placeholders)
    "rl-coach-testimonial",    # /coaching/ band sequence
    "rl-hp-test-card",         # homepage quote cards
    "rl-hp-test-quote",
    "rl-hp-test-grid",
    "rl-hp-test-name",
    "rl-hp-test-attr",
    "gg-about-testimonial",    # Gravel God's copies
    "gg-tp-testimonial",
    "gg-coach-testimonial",
    "gg-consult-testimonial",
    "gg-hp-test-quote",
    "gg-hp-test-card",
    "gg-trust-quote",
    "tp-testimonial",
)

# The homepage coaching band wrapper. It renders a sentence and a CTA, no
# quotes (owner ruling 2026-07-18: no homepage testimonials).
ALLOWED_TESTIMONIAL_CLASS_TOKENS = frozenset({"gg-hp-testimonials", "rl-hp-testimonials"})

# ── Claims nobody can check (commercial copy only) ──────────────────────

SCARCITY_STRINGS = (
    "Stars from",
    "athletes/month",
    "Next window",
    "Limited spots",
    "same coach, same plan engine",  # borrowed Gravel God caption
)

RATING_CLAIM_PATTERNS = (
    r"\brated\s+\d(?:\.\d+)?\s*(?:/|out\s+of)\s*\d+",       # Rated 4.9/5
    r"\b\d\.\d\s*/\s*5\b",                                   # 4.9/5
    r"\b\d(?:\.\d+)?\s+out\s+of\s+5\s+stars?\b",             # 4.9 out of 5 stars
    r"\b\d(?:\.\d+)?\s*[★⭐]",                                # 4.8★
    r"[★⭐]\s*\d\.\d",                                        # ★ 4.8
    r"[★⭐]{3,}",                                             # ★★★★★
    r"\(\s*\d[\d,]*\+?\s+(?:reviews?|ratings?)\s*\)",         # (123 reviews)
    r"\b\d[\d,]*\+?\s+(?:five|5)[-\s]?star\s+(?:reviews?|ratings?)\b",
)

COUNT_PATTERNS = (
    r"\b\d[\d,]*\+?\s+(?:athletes|riders|clients)\s+coached\b",
    r"\bcoached\s+(?:over\s+|more\s+than\s+)?\d[\d,]*\+?\s+(?:athletes|riders|clients)\b",
    r"\b\d[\d,]*\+?\s+(?:training\s+)?plans\s+sold\b",
    r"\bsold\s+(?:over\s+|more\s+than\s+)?\d[\d,]*\+?\s+(?:training\s+)?plans\b",
    r"\b(?:athletes|clients)\s+coached\s*:?\s*\d",
    r"\bplans\s+sold\s*:?\s*\d",
)

# ── Who counts as a person in an attribution ────────────────────────────

# A word in the name slot that marks a publication, organisation or
# platform, not a person: "— The Guardian", "— Cycling Weekly",
# "Life Time Grand Prix · 232K views".
ORG_WORDS = frozenset({
    "the", "weekly", "magazine", "mag", "news", "newspaper", "times",
    "guardian", "journal", "post", "daily", "tribune", "herald", "gazette",
    "review", "reviews", "press", "media", "radio", "podcast", "tv",
    "channel", "show", "cycling", "cyclist", "cyclists", "bicycling", "bike",
    "bikes", "biking", "velo", "velonews", "gravel", "outside", "club",
    "team", "racing", "race", "races", "events", "event", "series",
    "official", "organizers", "organisers", "organizer", "organiser",
    "promoter", "promoters", "staff", "editors", "editor", "editorial",
    "desk", "collective", "company", "co", "inc", "llc", "ltd",
    "foundation", "association", "federation", "committee", "council",
    "society", "productions", "studio", "studios", "online", "blog",
    "report", "wire", "network", "grand", "prix", "tour", "gp",
    "institute", "university", "group", "labs", "lab", "god", "strava",
    "reddit", "youtube", "instagram", "facebook", "twitter", "tiktok",
    "substack", "wikipedia", "uci", "usac",
})
NAME_PARTICLES = frozenset({"van", "von", "de", "del", "della", "da", "di", "du", "la", "le"})

_HARD, _SOFT = "\x1f", "\x1e"  # element boundaries inside collected text
_INLINE = frozenset({"a", "abbr", "b", "em", "i", "mark", "small", "span", "strong", "time", "u"})
_DASH_LINE_TAGS = frozenset({"p", "div", "span", "small", "li", "dd", "strong", "b", "em", "i"})
_VOID = frozenset({"area", "base", "br", "col", "embed", "hr", "img", "input", "link",
                   "meta", "param", "source", "track", "wbr"})
# Python's \s matches the boundary characters, so spell whitespace out.
_WS = "[ \t\n\r\f\v\u00a0\u2009\u202f]"
# A dash, then the name with nothing but whitespace or an inline tag between.
_LEAD_DASH_RE = re.compile(
    rf"^(?:{_WS}|[\x1e\x1f])*(?:[—–―]|-(?={_WS}))(?:{_WS}|\x1e)*(?![\x1e\x1f]|{_WS}|$)"
)
_NAME_SPLIT_RE = re.compile(rf"[\x1e\x1f,·•|(/;:]|{_WS}[-–—―]{_WS}")
_INITIAL_RE = re.compile(r"(?:[A-Z]\.){1,3}")
_COMMERCIAL_CLASS_RE = re.compile(r"coaching|(?:^|[-_])cta(?:$|[-_])")
_JSONLD_RE = re.compile(
    r'<script[^>]*type=["\']application/ld\+json["\'][^>]*>(.*?)</script>',
    re.DOTALL | re.IGNORECASE,
)

# Approved receipt ids. Empty: no consented receipts exist yet. When the
# receipts ledger loader lands (Receipts spec PR-4), resolve against it here.
KNOWN_RECEIPT_IDS: frozenset = frozenset()


def _plain(text: str) -> str:
    return " ".join(text.replace(_HARD, " ").replace(_SOFT, " ").split())


def _visible_text(markup: str) -> str:
    return " ".join(html_lib.unescape(re.sub(r"<[^>]+>", " ", markup)).split())


def find_unsupported_claims(text: str) -> list[str]:
    """Scarcity, rating and coach-count claims in copy (markup or text)."""
    findings = []
    lowered = text.lower()
    for s in SCARCITY_STRINGS:
        if s.lower() in lowered:
            findings.append(f"banned string {s!r}")
    for pattern in RATING_CLAIM_PATTERNS:
        m = re.search(pattern, text, re.IGNORECASE)
        if m:
            findings.append(f"rating claim {m.group(0)!r}")
    for pattern in COUNT_PATTERNS:
        m = re.search(pattern, text, re.IGNORECASE)
        if m:
            findings.append(f"unverified count {m.group(0)!r}")
    return findings


def _is_name_word(token: str) -> bool:
    core = re.sub(r"['’-]", "", token.rstrip("."))
    return (len(core) >= 2 and core.isalpha() and token[0].isupper()
            and any(c.islower() for c in core))


def person_in_attribution(text: str, *, structural: bool = False) -> str | None:
    """The person an attribution names, or None.

    `text` is the attribution's text; element boundaries inside it act as
    separators, so <footer><strong>Pat Q.</strong><span>Unbound</span>
    reads as "Pat Q." then "Unbound". A person is:
      - a name with an initial ("Pat Q.", "Test Rider A"), anywhere;
      - "First Last" after a leading dash, or in a structural slot
        (<footer>/<figcaption> of a quote);
      - a lone first name after a dash with context ("— Pat · Unbound 2025").
    Any publication/organisation word in the name slot means not a person.
    An undashed <cite> is a source title ("Drew Dillman · 35.8K views",
    a YouTube channel), not a testimonial byline.
    """
    m = _LEAD_DASH_RE.match(text)
    body = text[m.end():] if m else text
    pieces = [" ".join(p.split()) for p in _NAME_SPLIT_RE.split(body)]
    first = next((i for i, p in enumerate(pieces) if p), None)
    if first is None:
        return None
    name = pieces[first]
    has_context = any(pieces[first + 1:])
    tokens = name.split()
    if any(t.lower().strip(".'’") in ORG_WORDS for t in tokens):
        return None
    words = [t for t in tokens if t.lower() not in NAME_PARTICLES]
    if not words or len(words) > 3:
        return None
    initials = [
        t for i, t in enumerate(words)
        if _INITIAL_RE.fullmatch(t) or (len(t) == 1 and t.isupper() and i == len(words) - 1)
    ]
    full = [t for t in words if _is_name_word(t)]
    if not full or len(initials) + len(full) != len(words):
        return None
    if initials:
        return name
    if len(full) >= 2 and (m or structural):
        return name
    if len(full) == 1 and m and has_context:
        return name
    return None


class _Frame:
    __slots__ = ("tag", "in_receipt", "in_quote", "in_commercial", "commercial_root",
                 "parts", "has_quote", "captions")

    def __init__(self, tag, parent, *, receipt, commercial):
        self.tag = tag
        self.in_receipt = receipt or bool(parent and parent.in_receipt)
        self.in_quote = tag in ("blockquote", "q") or bool(parent and parent.in_quote)
        self.commercial_root = commercial and not (parent and parent.in_commercial)
        self.in_commercial = commercial or bool(parent and parent.in_commercial)
        self.parts: list[str] = []
        self.has_quote = False
        self.captions: list[str] = []


class _ProofScanner(HTMLParser):
    def __init__(self, page_kind: str, known_receipt_ids: frozenset):
        super().__init__(convert_charrefs=True)
        self.page_kind = page_kind
        self.known = known_receipt_ids
        self.findings: list[str] = []
        self._stack: list[_Frame] = []

    def _flag(self, finding: str) -> None:
        if finding not in self.findings:
            self.findings.append(finding)

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        classes = (a.get("class") or "").split()
        for cls in classes:
            if cls in ALLOWED_TESTIMONIAL_CLASS_TOKENS:
                continue
            if cls.startswith(LEGACY_TESTIMONIAL_CLASSES) or "testimonial" in cls:
                self._flag(f"testimonial class .{cls} on <{tag}>")
        if "data-receipt-id" in a and a["data-receipt-id"] not in self.known:
            self._flag(f"data-receipt-id={a['data-receipt-id']!r} does not resolve "
                       "in the receipts ledger")
        if tag in _VOID:
            if self._stack:  # <br> separates "Pat Q." from "Unbound 2025"
                self._stack[-1].parts.append(_HARD)
            return
        commercial = ("data-ab" in a or "data-cta" in a
                      or any(_COMMERCIAL_CLASS_RE.search(c) for c in classes))
        parent = self._stack[-1] if self._stack else None
        if tag in ("blockquote", "q"):
            for frame in self._stack:
                if frame.tag == "figure":
                    frame.has_quote = True
        self._stack.append(_Frame(tag, parent, receipt="data-receipt-id" in a,
                                  commercial=commercial))

    def handle_endtag(self, tag):
        for i in range(len(self._stack) - 1, -1, -1):
            if self._stack[i].tag == tag:
                while len(self._stack) > i:
                    self._close(self._stack.pop())
                return

    def handle_data(self, data):
        if self._stack:
            self._stack[-1].parts.append(data)

    def finish(self) -> list[str]:
        self.close()
        while self._stack:
            self._close(self._stack.pop())
        return self.findings

    def _attribution(self, slot: str, text: str, *, structural: bool) -> bool:
        name = person_in_attribution(text, structural=structural)
        if name:
            self._flag(f"person-attributed {slot} outside a receipt: {name!r} "
                       f"(in {_plain(text)!r})")
        return bool(name)

    def _close(self, frame: _Frame) -> None:
        text = "".join(frame.parts)
        if self._stack:
            edge = _SOFT if frame.tag in _INLINE else _HARD
            self._stack[-1].parts.append(edge + text + edge)
        if frame.commercial_root and self.page_kind == EDITORIAL:
            for claim in find_unsupported_claims(_plain(text)):
                self._flag(f"{claim} in a commercial element")
        if frame.in_receipt:
            return
        if frame.tag == "cite":
            named = self._attribution("<cite>", text, structural=False)
            if not named and self.page_kind == COMMERCIAL:
                self._flag(f"<cite> outside a data-receipt-id element: {_plain(text)!r}")
        elif frame.tag == "footer":
            self._attribution("<footer>", text, structural=frame.in_quote)
        elif frame.tag == "figcaption":
            figure = next((f for f in reversed(self._stack) if f.tag == "figure"), None)
            if figure is not None:
                figure.captions.append(text)  # judged when the figure closes
            else:
                self._attribution("<figcaption>", text, structural=False)
        elif frame.tag == "figure":
            for caption in frame.captions:
                self._attribution("<figcaption>", caption, structural=frame.has_quote)
        if frame.tag in _DASH_LINE_TAGS and _LEAD_DASH_RE.match(text):
            self._attribution("dash line", text, structural=False)


def _aggregate_ratings(node):
    if isinstance(node, dict):
        for key, value in node.items():
            if key == "aggregateRating" and isinstance(value, dict):
                yield value
            yield from _aggregate_ratings(value)
    elif isinstance(node, list):
        for item in node:
            yield from _aggregate_ratings(item)


def find_unsourced_proof(
    html: str,
    *,
    page_kind: str = COMMERCIAL,
    sourced_rating_counts: frozenset = frozenset(),
    known_receipt_ids: frozenset = KNOWN_RECEIPT_IDS,
) -> list[str]:
    """Return every unsourced-proof finding in an HTML string (empty = clean).

    page_kind: COMMERCIAL (default, strictest) or EDITORIAL (race profiles,
    Gravel Weekly); see the module docstring.
    sourced_rating_counts: ratingCount values that trace to real Racer
    Ratings for this page (race pages only). Every other aggregateRating,
    and any that isn't in parseable JSON-LD, is a finding.
    """
    assert page_kind in (COMMERCIAL, EDITORIAL), page_kind
    findings = []
    if page_kind == COMMERCIAL:
        findings += find_unsupported_claims(html + "\n" + _visible_text(html))

    total = html.count("aggregateRating")
    if total:
        sourced = 0
        for block in _JSONLD_RE.findall(html):
            try:
                data = json.loads(block)
            except json.JSONDecodeError:
                continue
            for agg in _aggregate_ratings(data):
                if str(agg.get("ratingCount")) in sourced_rating_counts:
                    sourced += 1
        if total > sourced:
            findings.append(
                f"aggregateRating without a real rating source ({total - sourced} of {total})"
            )

    scanner = _ProofScanner(page_kind, known_receipt_ids)
    scanner.feed(html)
    return findings + scanner.finish()


# Placeholder names that were live on roadielabs.com. They are invented, not
# people; listed so a restore from git history fails loudly.
PLACEHOLDER_NAMES = (
    "Sarah K.", "Greg F.", "Stephanie H.", "Chris M.", "Megan T.",
    "Jason R.", "Sarah M.", "Mark D.",
)

SAMPLE_RACE = "maratona-dles-dolomites"
# Race descriptions that legitimately say registration/lodging has limited spots.
LIMITED_SPOTS_RACES = ("midnight-sun-randonnee", "granfondo-belgium")


def _sourced_rating_counts(slug: str) -> frozenset:
    """Racer Rating counts that may appear in a race page's JSON-LD."""
    d = json.loads((PROJECT_ROOT / "race-data" / f"{slug}.json").read_text())
    rr = d.get("race", d).get("racer_rating") or {}
    total = rr.get("total_ratings") or 0
    if total >= RACER_RATING_THRESHOLD and rr.get("star_average"):
        return frozenset({str(total)})
    return frozenset()


@functools.lru_cache(maxsize=None)
def _race_index() -> list:
    return json.loads((PROJECT_ROOT / "web" / "race-index.json").read_text())


@functools.lru_cache(maxsize=None)
def _race_page(slug: str) -> str:
    rd = generate_neo_brutalist.load_race_data(PROJECT_ROOT / "race-data" / f"{slug}.json")
    return generate_neo_brutalist.generate_page(rd, _race_index())


# ── Rendered pages ──────────────────────────────────────────────


@pytest.fixture(scope="module")
def rendered_pages():
    original_fetch = generate_homepage.fetch_substack_posts
    generate_homepage.fetch_substack_posts = lambda: []
    try:
        pages = {
            "homepage": generate_homepage.generate_homepage(
                _race_index(),
                race_data_dir=PROJECT_ROOT / "race-data",
                guide_path=PROJECT_ROOT / "guide" / "road-guide-content.json",
            ),
        }
    finally:
        generate_homepage.fetch_substack_posts = original_fetch

    race = json.loads((PROJECT_ROOT / "race-data" / f"{SAMPLE_RACE}.json").read_text())
    race = race.get("race", race)
    race.setdefault("slug", SAMPLE_RACE)

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
        f"training-plan/{SAMPLE_RACE}": generate_training_plan_pages.generate_page(
            race, generate_training_plan_pages.load_pack(SAMPLE_RACE)
        ),
    })
    for key in generate_success_pages.PAGES:
        pages[f"success/{key}"] = generate_success_pages.generate_success_page(key)
    return pages


PAGE_NAMES = (
    "homepage", "about", "training-plans", "coaching", "coaching-apply",
    "consulting", "consult-intake", "questionnaire", "courses", "methodology",
    f"training-plan/{SAMPLE_RACE}",
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


@pytest.mark.parametrize("slug", (SAMPLE_RACE, *LIMITED_SPOTS_RACES))
def test_race_page_carries_no_unsourced_proof(slug):
    findings = find_unsourced_proof(_race_page(slug), page_kind=EDITORIAL,
                                    sourced_rating_counts=_sourced_rating_counts(slug))
    assert not findings, f"race/{slug}: " + "; ".join(findings)


@pytest.mark.parametrize("slug", LIMITED_SPOTS_RACES)
def test_race_description_with_limited_spots_passes(slug):
    """Race copy about the event's own registration isn't coaching scarcity."""
    markup = _race_page(slug)
    assert "limited spots" in markup.lower(), f"{slug} no longer says limited spots; pick another race"
    assert find_unsourced_proof(markup, page_kind=EDITORIAL,
                                sourced_rating_counts=_sourced_rating_counts(slug)) == []


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
        assert not find_unsupported_claims(rendered_pages[page]), page


# ── A/B copy is injected at runtime, so check it at the source ──


def _variant_copy(experiments) -> list[tuple[str, str]]:
    return [
        (exp["id"], v["content"])
        for exp in experiments
        for v in exp["variants"]
    ]


def test_ab_source_variants_have_no_unsourced_proof():
    for exp_id, content in _variant_copy(ab_experiments.EXPERIMENTS):
        assert not find_unsourced_proof(content), f"{exp_id}: {content!r}"


def test_exported_experiments_json_has_no_unsourced_proof():
    exported = json.loads((PROJECT_ROOT / "web" / "ab" / "experiments.json").read_text())
    ids = {exp["id"] for exp in exported["experiments"]}
    assert "coaching_scarcity" not in ids
    for exp_id, content in _variant_copy(exported["experiments"]):
        assert not find_unsourced_proof(content), f"{exp_id}: {content!r}"


# ── Planted regressions: the guard must fire ────────────────────


PLANTED = {
    "about card": (
        '<blockquote class="rl-about-testimonial"><p>Best plan ever.</p>'
        '<footer><strong>Test Rider A</strong></footer></blockquote>',
        "rl-about-testimonial",
    ),
    "about card, new class": (
        # The deleted /about/ card's exact shape under a class the list
        # doesn't know: attribution via <footer><strong>Firstname L.</strong>.
        '<blockquote class="rl-about-voice"><p>Best plan ever.</p>'
        '<footer><strong>Pat Q.</strong><span class="rl-about-voice-meta">'
        "Maratona · 8 hrs/week</span></footer></blockquote>",
        "person-attributed <footer>",
    ),
    "footer full name": (
        '<blockquote class="rl-proof"><p>Great.</p>'
        "<footer><b>Pat Quinn</b><span>Etape finisher</span></footer></blockquote>",
        "person-attributed <footer>",
    ),
    "figcaption": (
        '<figure class="rl-proof-card"><blockquote><p>Great.</p></blockquote>'
        "<figcaption>Test Rider B, Etape 2025</figcaption></figure>",
        "person-attributed <figcaption>",
    ),
    "figcaption dash": (
        "<figure><blockquote><p>Great.</p></blockquote>"
        "<figcaption>&mdash; Pat Q.</figcaption></figure>",
        "person-attributed <figcaption>",
    ),
    "em-dash p": (
        '<div class="rl-about-card"><p>&ldquo;Great.&rdquo;</p><p>&mdash; Test Rider C</p></div>',
        "person-attributed dash line",
    ),
    "em-dash p with context": (
        "<div><p>&ldquo;Great.&rdquo;</p><p>— Pat Q., Etape 2025</p></div>",
        "person-attributed dash line",
    ),
    "em-dash p, strong name": (
        "<div><p>&ldquo;Great.&rdquo;</p><p>&mdash; <strong>Pat Q.</strong></p></div>",
        "person-attributed dash line",
    ),
    "em-dash p, line break": (
        "<div><p>&ldquo;Great.&rdquo;</p><p>&mdash; Pat Q.<br>Etape 2025</p></div>",
        "person-attributed dash line",
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
    "press cite": (
        "<blockquote><p>The best plan.</p><cite>Cycling Weekly</cite></blockquote>",
        "<cite> outside",
    ),
    "aggregate rating": (
        '<script type="application/ld+json">{"@type":"Product",'
        '"aggregateRating":{"@type":"AggregateRating","ratingValue":"4.7"}}</script>',
        "aggregateRating",
    ),
    "stars from": ("<p>4.7 Stars from 100+ Reviews</p>", "Stars from"),
    "rated n of 5": ("<p>Rated 4.9/5 by our athletes</p>", "rating claim"),
    "n out of 5 stars": ("<p>4.9 out of 5 stars</p>", "rating claim"),
    "n star glyph": ("<p>4.8★</p>", "rating claim"),
    "n star entity": ("<p>4.8 &#9733; on Google</p>", "rating claim"),
    "star strip with count": (
        "<p>&#9733;&#9733;&#9733;&#9733;&#9733; (123 reviews)</p>", "rating claim",
    ),
    "five-star count": ("<p>200+ five-star reviews</p>", "rating claim"),
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

# Attribution plants must fire on race pages too, not just sales pages.
PLANTED_ON_EDITORIAL = (
    "about card, new class", "footer full name", "figcaption", "figcaption dash",
    "em-dash p", "em-dash p with context", "em-dash p, strong name",
    "em-dash p, line break",
)


@pytest.mark.parametrize("case", sorted(PLANTED))
def test_guard_fires_on_planted_regression(case):
    markup, expected = PLANTED[case]
    findings = find_unsourced_proof(f"<html><body>{markup}</body></html>")
    assert any(expected in f for f in findings), (case, findings)


@pytest.mark.parametrize("case", PLANTED_ON_EDITORIAL)
def test_guard_fires_on_planted_attribution_on_race_pages(case):
    markup, expected = PLANTED[case]
    findings = find_unsourced_proof(f"<html><body>{markup}</body></html>", page_kind=EDITORIAL)
    assert any(expected in f for f in findings), (case, findings)


@pytest.mark.parametrize("cite", [
    "&mdash; Jason R., Mid-South 2025",
    "&mdash; Sarah K.",
    "&ndash; Firstname Lastname, Etape finisher",
    "&mdash; Name &middot; Maratona 2025",
    "Test Rider A",
])
def test_person_attributed_cite_on_race_pages(cite):
    markup = f"<blockquote><p>Best plan ever.</p><cite>{cite}</cite></blockquote>"
    findings = find_unsourced_proof(markup, page_kind=EDITORIAL)
    assert any("person-attributed <cite>" in f for f in findings), findings


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


def test_old_about_card_under_a_new_class_through_the_real_generator(monkeypatch):
    original = generate_about.build_coaching
    card = ('<blockquote class="rl-about-voice"><p>Placeholder.</p>'
            '<footer><strong>Pat Q.</strong><span class="rl-about-voice-meta">'
            "Maratona · 8 hrs/week</span></footer></blockquote>")
    monkeypatch.setattr(generate_about, "build_coaching", lambda: original() + card)
    findings = find_unsourced_proof(generate_about.generate_about_page())
    assert any("person-attributed <footer>" in f and "Pat Q." in f for f in findings), findings


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


def test_scarcity_in_a_race_page_coaching_cta_is_caught():
    """Race pages are editorial, but the coaching footnote on every one of
    them is sales copy, so scarcity there still fails."""
    markup = _race_page(SAMPLE_RACE)
    cta = 'data-cta="approved_coaching">GET ME IN YOUR CORNER'
    assert cta in markup
    planted = markup.replace(cta, 'data-cta="approved_coaching">1:1 COACHING &mdash; LIMITED SPOTS')
    findings = find_unsourced_proof(planted, page_kind=EDITORIAL,
                                    sourced_rating_counts=_sourced_rating_counts(SAMPLE_RACE))
    assert any("Limited spots" in f and "commercial element" in f for f in findings), findings


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


@pytest.mark.parametrize("cite", [
    "Some Channel &middot; 69K views",
    "Test Channelname &middot; 13.1K views",
])
def test_youtube_channel_cite_on_race_pages(cite):
    markup = (f'<blockquote class="rl-field-quote"><p class="rl-field-quote-text">Brutal climb.</p>'
              f'<cite class="rl-field-quote-cite">{cite}</cite></blockquote>')
    assert find_unsourced_proof(markup, page_kind=EDITORIAL) == []


@pytest.mark.parametrize("attribution", [
    "— The Guardian",
    "&mdash; The Guardian",
    "&mdash; Cycling Weekly, June 2025",
    "&mdash; Velo &middot; 2026",
    "— Outside Magazine",
    "&mdash; Etape du Tour organisers",
    "&mdash; Life Time Grand Prix",
    "Gravel Cyclist &middot; 1.9K views",
    "&mdash; Strava, 2024",
])
@pytest.mark.parametrize("slot", ["cite", "footer", "figcaption", "p"])
def test_publication_and_organisation_attributions(attribution, slot):
    if slot == "figcaption":
        markup = (f"<figure><blockquote><p>Brutal.</p></blockquote>"
                  f"<figcaption>{attribution}</figcaption></figure>")
    else:
        markup = f"<blockquote><p>Brutal.</p><{slot}>{attribution}</{slot}></blockquote>"
    assert find_unsourced_proof(markup, page_kind=EDITORIAL) == []


@pytest.mark.parametrize("markup", [
    '<div class="rl-hero-score"><div class="rl-hero-rider-empty">&mdash;</div>'
    '<a class="rl-hero-score-label" href="#r">RIDER SCORE &middot; RATE IT &rarr;</a></div>',
    '<div class="rl-stat"><div>&mdash;</div><div>Entry Cost</div></div>',
    "<p>&mdash; email me when this entry changes.</p>",
    "<p>The climb isn&#x27;t optional&mdash;it&#x27;s the race.</p>",
    '<figure><img src="x.jpg" alt=""><figcaption>Photo: Test Rider A</figcaption></figure>',
    '<footer class="rl-mega-footer"><div><h3>Races</h3><a href="/">Race Search</a></div></footer>',
])
def test_editorial_markup_that_looks_like_an_attribution(markup):
    assert find_unsourced_proof(markup, page_kind=EDITORIAL) == []


@pytest.mark.parametrize("copy", [
    "30 EUR non-refundable initial fee; limited spots via reservation",
    "The event maintains a 4.6/5 rating from 59 reviews.",
    "Next window for registration is March.",
])
def test_race_editorial_claims_outside_commercial_elements(copy):
    markup = f'<div class="rl-prose"><p>{copy}</p></div>'
    assert find_unsourced_proof(markup, page_kind=EDITORIAL) == []
    assert find_unsourced_proof(markup)  # the same copy on a sales page fails
