"""Race database cards open the race from anywhere on the card (#198).

Pattern: the title <a class="rl-card-name"> stays the card's ONE link and its
::after stretches over the card; the compare checkbox, favourite heart,
series pill and score bar sit above it (position:relative; z-index:1) so they
keep their own clicks. The card is never wrapped in <a> (no nested interactive
elements). The title wraps above the badges instead of colliding with them.
"""
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
JS = (ROOT / "web" / "road-labs-search.js").read_text()
CSS = (ROOT / "web" / "rl-search.css").read_text()


def _render_card_src():
    start = JS.index("function renderCard(race)")
    end = JS.index("// ── Tier grouping", start)
    return JS[start:end]


def _rule(selector):
    """Bodies of every rule whose selector list contains `selector`, joined."""
    bodies = []
    for m in re.finditer(r"([^{}]+)\{([^{}]*)\}", CSS):
        head = re.sub(r"/\*.*?\*/", "", m.group(1), flags=re.S)
        sels = [s.strip() for s in head.split(",")]
        if selector in sels:
            bodies.append(m.group(2))
    assert bodies, f"no CSS rule for {selector}"
    return "\n".join(bodies)


class TestCardMarkup:
    def test_linked_card_gets_modifier_only_with_profile(self):
        assert "(race.has_profile ? ' rl-card-linked' : '')" in _render_card_src()

    def test_title_is_the_only_race_link(self):
        src = _render_card_src()
        assert src.count("race.profile_url") == 1
        assert '<a class="rl-card-name" href="' in src

    def test_card_not_wrapped_in_anchor(self):
        src = _render_card_src()
        assert "return '<a" not in src
        assert "return '<div class=\"rl-card " in src

    def test_badges_use_class_not_inline_style(self):
        src = _render_card_src()
        assert '<div class="rl-card-badges">' in src
        assert "display:flex;gap:6px" not in src

    def test_fav_button_does_not_submit(self):
        assert '<button type="button" class="rl-fav-btn' in _render_card_src()


class TestStretchedLinkCss:
    def test_card_is_positioning_context(self):
        assert "position: relative" in _rule("#rl-race-search .rl-card")

    def test_title_after_covers_card(self):
        body = _rule("#rl-race-search .rl-card-linked a.rl-card-name::after")
        assert 'content: ""' in body
        assert "position: absolute" in body
        assert "inset: 0" in body

    @pytest.mark.parametrize("control", [
        "rl-compare-check", "rl-fav-btn", "rl-series-badge",
        "rl-score-bar", "rl-score-breakdown",
    ])
    def test_secondary_controls_sit_above_link(self, control):
        body = _rule(f"#rl-race-search .rl-card-linked .{control}")
        assert "position: relative" in body
        assert "z-index: 1" in body

    def test_no_intermediate_positioning_context(self):
        """A positioned header would trap the ::after inside the header."""
        for sel in ("#rl-race-search a.rl-card-name", "#rl-race-search .rl-card-header",
                    "#rl-race-search .rl-card-badges"):
            body = _rule(sel)
            for prop in ("position", "transform", "filter", "contain"):
                assert prop + ":" not in body, (sel, prop)

    def test_focus_and_hover_signifiers(self):
        focus = _rule("#rl-race-search .rl-card-linked:focus-within")
        assert "outline: 3px solid var(--rl-color-ink)" in focus
        assert "underline" in _rule("#rl-race-search .rl-card-linked:hover a.rl-card-name")

    def test_new_rules_stay_flat_and_tokenised(self):
        start = CSS.index("Whole-card link (stretched title anchor)")
        block = CSS[start:CSS.index("#rl-race-search span.rl-card-name.no-link", start)]
        assert "border-radius" not in block
        assert "box-shadow" not in block
        assert not re.search(r"#[0-9a-fA-F]{3,6}\b", block), "use tokens, not hex"


class TestTitleDoesNotCollideWithBadges:
    def test_header_wraps(self):
        body = _rule("#rl-race-search .rl-card-header")
        assert "flex-wrap: wrap" in body
        assert "gap:" in body
        assert "flex-direction: column" not in CSS.split("#rl-race-search .rl-card-header {")[-1].split("}")[0]

    def test_title_can_shrink_and_wrap(self):
        body = _rule("#rl-race-search a.rl-card-name")
        assert "flex: 1 1 160px" in body
        assert "min-width: 0" in body
        assert "overflow-wrap: anywhere" in body

    def test_badges_wrap(self):
        assert "flex-wrap: wrap" in _rule("#rl-race-search .rl-card-badges")


def test_cache_busters_bumped():
    """Changed JS/CSS must ship under new ?v= so cached copies don't pair old
    markup with new styles."""
    html = (ROOT / "web" / "road-labs-search.html").read_text()
    assert "rl-search.css?v=20261115a" not in html
    assert "road-labs-search.js?v=20261114a" not in html
