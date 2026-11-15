"""Coaching fit check: three questions above the tier columns that
recommend a tier (RL-10). Ported with the generator code from Gravel God
(gravel-race-automation tests/test_coaching.py, TestFitCheck); same copy,
same scoring, Roadie Labs tokens.
"""
from __future__ import annotations

import html
import re
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "wordpress"))

from generate_coaching import (  # noqa: E402
    QUESTIONNAIRE_URL,
    TIERS,
    build_coaching_css,
    build_coaching_js,
    build_fit_check,
    build_tiers,
    generate_coaching_page,
)


@pytest.fixture(scope="module")
def coaching_html():
    return generate_coaching_page()


@pytest.fixture(scope="module")
def coaching_css():
    return build_coaching_css()


@pytest.fixture(scope="module")
def coaching_js():
    return build_coaching_js()


# ── Fit check — three-question tier recommender ─────────────


def _fit_score_tier(q1: int, q2: int, q3) -> str:
    """Spec scoring, written independently of the page JS."""
    score = q1 + q2 + (1 if q3 == 2 else 0)
    if score <= 1:
        return "min"
    if score <= 3:
        return "mid"
    return "max"


def _ancestor_classes(fragment: str, target_class: str) -> list:
    """Class names of every ancestor of the first element carrying
    target_class in an HTML fragment."""
    from html.parser import HTMLParser

    class _Walk(HTMLParser):
        def __init__(self):
            super().__init__()
            self.stack, self.found = [], None

        def handle_starttag(self, tag, attrs):
            cls = dict(attrs).get("class") or ""
            if self.found is None and target_class in cls.split():
                self.found = [c for _, c in self.stack]
            self.stack.append((tag, cls))

        def handle_endtag(self, tag):
            while self.stack:
                if self.stack.pop()[0] == tag:
                    break

    walker = _Walk()
    walker.feed(fragment)
    assert walker.found is not None, target_class
    return " ".join(walker.found).split()


def _fitcheck_js_iife(coaching_js: str) -> str:
    start = coaching_js.index("/* Fit check")
    end = coaching_js.index("/* Scroll depth tracking */")
    return coaching_js[start:end]


# Minimal DOM for the fit-check IIFE: just enough surface (hidden,
# attributes, classList, click listeners, the selectors the IIFE uses) to
# run the real script in Node and read back what it rendered.
_FITCHECK_DOM_HARNESS = r"""
const iife = process.argv[1];
const plan = JSON.parse(process.argv[2]);
const narrow = process.argv[3] === 'mobile';
global.window = { matchMedia: function(q) { return { matches: q === '(max-width: 768px)' && narrow }; } };
function el(attrs, hidden) {
  const cls = new Set();
  return {
    hidden: !!hidden, attrs: Object.assign({}, attrs), listeners: [],
    getAttribute(n) { return n in this.attrs ? String(this.attrs[n]) : null; },
    setAttribute(n, v) { this.attrs[n] = String(v); },
    addEventListener(t, f) { if (t === 'click') this.listeners.push(f); },
    click() { this.listeners.forEach(function(f) { f(); }); },
    classList: {
      toggle(n, on) { if (on) cls.add(n); else cls.delete(n); },
      contains(n) { return cls.has(n); },
    },
  };
}
function run(clicks) {
  const events = [];
  global.gtag = function(kind, name, params) { events.push([name, params]); };
  const empty = el({}, false), answer = el({}, true), tight = el({}, true);
  const scrolls = [];
  const result = el({});
  result.scrollIntoView = function(opts) { scrolls.push(opts); };
  const fits = [];
  ['min', 'mid', 'max'].forEach(function(t) { fits.push(el({'data-fit': t, kind: 'rec'}, true)); });
  ['min', 'mid', 'max'].forEach(function(t) { fits.push(el({'data-fit': t, kind: 'cta'}, true)); });
  const buttons = [];
  [1, 2, 3].forEach(function(q) {
    const group = [0, 1, 2].map(function(a) { return el({'data-q': q, 'data-a': a, 'aria-pressed': 'false'}); });
    const parent = { querySelectorAll: function() { return group; } };
    group.forEach(function(b) { b.parentNode = parent; buttons.push(b); });
  });
  const box = el({}, true);
  box.querySelector = function(sel) {
    return { '.rl-coach-fitcheck-empty': empty, '.rl-coach-fitcheck-answer': answer,
             '.rl-coach-fitcheck-tight': tight, '.rl-coach-fitcheck-result': result }[sel];
  };
  box.querySelectorAll = function(sel) {
    if (sel === '[data-fit]') return fits;
    if (sel === '.rl-coach-fitcheck-opt') return buttons;
    throw new Error('unexpected selector ' + sel);
  };
  const cols = ['min', 'mid', 'max'].map(function(t) {
    const c = el({'data-tier': t});
    const label = el({}, true);
    c.querySelector = function() { return label; };
    c.label = label;
    return c;
  });
  global.document = {
    getElementById: function(id) { return id === 'rl-coach-fitcheck' ? box : null; },
    querySelectorAll: function(sel) {
      if (sel === '.rl-coach-tier-col[data-tier]') return cols;
      throw new Error('unexpected selector ' + sel);
    },
  };
  new Function(iife)();
  const boxHiddenAfterInit = box.hidden;
  clicks.forEach(function(qa) {
    buttons.find(function(b) { return b.attrs['data-q'] == qa[0] && b.attrs['data-a'] == qa[1]; }).click();
  });
  return {
    boxHidden: boxHiddenAfterInit,
    emptyHidden: empty.hidden, answerHidden: answer.hidden, tightHidden: tight.hidden,
    recs: fits.filter(function(f) { return f.attrs.kind === 'rec' && !f.hidden; }).map(function(f) { return f.attrs['data-fit']; }),
    ctas: fits.filter(function(f) { return f.attrs.kind === 'cta' && !f.hidden; }).map(function(f) { return f.attrs['data-fit']; }),
    fitCols: cols.filter(function(c) { return c.classList.contains('rl-coach-is-fit'); }).map(function(c) { return c.attrs['data-tier']; }),
    fitLabels: cols.filter(function(c) { return !c.label.hidden; }).map(function(c) { return c.attrs['data-tier']; }),
    pressed: buttons.filter(function(b) { return b.attrs['aria-pressed'] === 'true'; }).map(function(b) { return [Number(b.attrs['data-q']), Number(b.attrs['data-a'])]; }),
    events: events,
    scrolls: scrolls,
  };
}
console.log(JSON.stringify(plan.map(run)));
"""


def _run_fitcheck(coaching_js: str, plans: list, viewport: str = "mobile") -> list:
    import json
    result = subprocess.run(
        ["node", "-e", _FITCHECK_DOM_HARNESS, _fitcheck_js_iife(coaching_js), json.dumps(plans), viewport],
        capture_output=True, text=True, timeout=30,
    )
    assert result.returncode == 0, f"fit-check harness failed: {result.stderr}"
    return json.loads(result.stdout)


class TestFitCheck:
    """Tier recommender above the tier columns. Owner-voice copy is pinned
    verbatim; the whole block is JS-revealed so the no-JS page is
    unchanged."""

    @pytest.fixture(scope="class")
    def fit(self):
        return build_fit_check()

    def test_in_tiers_section_directly_above_columns(self):
        tiers = build_tiers()
        start = tiers.index('id="rl-coach-fitcheck"')
        assert tiers.index('id="tiers"') < start < tiers.index('class="rl-coach-tiers"')
        between = tiers[start:tiers.index('class="rl-coach-tiers"')]
        assert "rl-coach-tier-col" not in between

    def test_renders_hidden_for_no_js(self, fit, coaching_html):
        opening = '<div class="rl-coach-fitcheck" id="rl-coach-fitcheck" hidden>'
        assert fit.startswith(opening)
        assert coaching_html.count(opening) == 1

    def test_not_confused_with_fit_section(self, coaching_html):
        """The existing 'A fit, or not' section keeps id="fit"; the fit
        check must not collide with it or the scroll-depth label."""
        assert coaching_html.count('id="fit"') == 1
        assert 'id="rl-coach-fitcheck"' in coaching_html

    def test_three_labelled_groups(self, fit):
        groups = re.findall(r'<div class="rl-coach-fitcheck-opts" role="group" aria-labelledby="([\w-]+)">', fit)
        assert groups == ["rl-coach-fitcheck-q1", "rl-coach-fitcheck-q2", "rl-coach-fitcheck-q3"]
        for gid in groups:
            assert fit.count(f'id="{gid}"') == 1

    def test_nine_real_buttons_unpressed(self, fit):
        buttons = re.findall(r'<button\b[^>]*>', fit)
        assert len(buttons) == 9
        for b in buttons:
            assert 'type="button"' in b
            assert 'aria-pressed="false"' in b
        pairs = set(re.findall(r'data-q="(\d)" data-a="(\d)"', fit))
        assert pairs == {(str(q), str(a)) for q in (1, 2, 3) for a in (0, 1, 2)}

    def test_aria_live_result_region(self, fit):
        assert fit.count('aria-live="polite"') == 1
        assert '<div class="rl-coach-fitcheck-result" aria-live="polite">' in fit

    def test_data_tier_on_all_columns(self):
        tiers = build_tiers()
        for key in ("min", "mid", "max"):
            assert tiers.count(f'class="rl-coach-tier-col" data-tier="{key}"') == 1

    def test_your_fit_labels_prerendered_hidden(self):
        tiers = build_tiers()
        labels = re.findall(r'<span class="rl-coach-tier-fit-label"([^>]*)>YOUR FIT</span>', tiers)
        assert len(labels) == 3
        assert all(attrs.strip() == "hidden" for attrs in labels)

    def test_cta_href_and_tracking(self, fit):
        from urllib.parse import urlsplit, parse_qs
        ctas = re.findall(r'<a href="([^"]+)" class="rl-coach-fitcheck-cta" data-cta="([\w]+)" data-fit="(\w+)" hidden>([^<]+)</a>', fit)
        assert [c[2] for c in ctas] == ["min", "mid", "max"]
        for href, data_cta, key, label in ctas:
            assert href == f"{QUESTIONNAIRE_URL}?tier={key}&amp;src=fitcheck"
            assert data_cta == f"fitcheck_apply_{key}"
            assert label == f"APPLY FOR {key.upper()} &rarr;"
            # The apply page preselects via URLSearchParams.get("tier");
            # the extra src param must not disturb it.
            query = parse_qs(urlsplit(html.unescape(href)).query)
            assert query == {"tier": [key], "src": ["fitcheck"]}

    def test_result_states_all_start_hidden(self, fit):
        assert '<div class="rl-coach-fitcheck-answer" hidden>' in fit
        assert '<p class="rl-coach-fitcheck-tight" hidden>' in fit
        assert len(re.findall(r'data-fit="(?:min|mid|max)" hidden', fit)) == 6

    def test_name_and_price_match_tier_columns(self, fit):
        """Result name/price come from the same TIERS source as the
        columns, so they can't drift."""
        tiers = build_tiers()
        assert [(k, n, p) for k, n, p in TIERS] == [
            ("min", "Min", "$199"), ("mid", "Mid", "$299"), ("max", "Max", "$1,200"),
        ]
        for key, name, price in TIERS:
            assert f'<p class="rl-coach-fitcheck-tier">{name} <span class="rl-coach-fitcheck-price">{price} / 4 WEEKS</span></p>' in fit
            assert f'<div class="rl-coach-tier-name">{name} <span' in tiers
            assert f'<div class="rl-coach-tier-price">{price}<span class="rl-coach-tier-interval">/ 4 WEEKS</span></div>' in tiers

    @pytest.mark.parametrize("copy", [
        "Not sure which tier? Three questions.",
        "When a week goes sideways, you want…",
        "I'll adjust it myself. Check my work weekly.",
        "The plan moved that same week.",
        "Someone on it the same day.",
        "Your ride files should be…",
        "Skimmed. I know what I did.",
        "Read between sessions.",
        "Read every one, every day.",
        "Your A race is…",
        "16+ weeks out",
        "8–16 weeks out",
        "Under 8 weeks",
        "Answer the first two. The race date only changes what I tell you.",
        "YOU PROBABLY WANT",
        "You execute on your own and want the thinking done right. A weekly look is enough.",
        "You want the week to move when life does, not after. That's the whole gap between Min and Mid.",
        "You want every file read the day it lands. Worth it for one race that matters more than the rest.",
        "Under 8 weeks is tight. I'll tell you straight if it's too late to change much.",
        "APPLY FOR MIN →",
        "APPLY FOR MID →",
        "APPLY FOR MAX →",
    ])
    def test_verbatim_copy(self, fit, copy):
        rendered = html.unescape(re.sub(r"<[^>]+>", "\n", fit))
        lines = {line.strip() for line in rendered.splitlines()}
        assert copy in lines, f"Fit-check copy missing or altered: {copy!r}"

    def test_css_hidden_beats_display_rules(self, coaching_css):
        """Toggled elements set their own display (grid, inline-flex,
        inline-block); without this override `hidden` would not hide them
        and the block would show with JS off."""
        assert ".rl-coach-tiers-section [hidden] {\n  display: none;\n}" in coaching_css

    def test_touch_targets(self, coaching_css):
        for selector in (".rl-coach-fitcheck-opt {", ".rl-coach-fitcheck-cta {"):
            block = coaching_css.split(selector, 1)[1].split("}", 1)[0]
            assert "min-height: 44px;" in block, selector

    def test_selected_state_is_solid_inverted(self, coaching_css):
        block = coaching_css.split('.rl-coach-fitcheck-opt[aria-pressed="true"] {', 1)[1].split("}", 1)[0]
        assert "background: var(--rl-color-dark-navy);" in block
        assert "color: var(--rl-color-cool-white);" in block

    def test_mobile_result_clears_sticky_cta(self, coaching_css):
        """The first result is scrolled into view with block 'nearest';
        on mobile the fixed sticky CTA (56px) would cover its bottom
        without a scroll margin."""
        mobile = coaching_css.split("/* ── Responsive", 1)[1]
        block = mobile.split(".rl-coach-fitcheck-result {", 1)[1].split("}", 1)[0]
        margin = re.search(r"scroll-margin-bottom:\s*(\d+)px;", block)
        assert margin and int(margin.group(1)) >= 56

    def test_fit_column_marked(self, coaching_css):
        assert ".rl-coach-tier-col.rl-coach-is-fit {" in coaching_css

    def test_focus_visible_not_suppressed(self, coaching_css):
        """Buttons and links get the shared focus ring
        (.rl-neo-brutalist-page button:focus-visible); nothing here may
        remove it."""
        from generate_neo_brutalist import get_page_css
        assert ".rl-neo-brutalist-page button:focus-visible" in get_page_css()
        assert ".rl-neo-brutalist-page a:focus-visible" in get_page_css()
        assert not re.search(r"outline:\s*(none|0)\b", coaching_css)

    def test_no_persistence(self, coaching_js):
        iife = _fitcheck_js_iife(coaching_js)
        assert "localStorage" not in iife
        assert "sessionStorage" not in iife
        assert "document.cookie" not in iife

    def test_analytics_events(self, coaching_js):
        iife = _fitcheck_js_iife(coaching_js)
        assert "gtag('event', 'coaching_fitcheck_answer', { question: q, answer: a })" in iife
        assert "gtag('event', 'coaching_fitcheck_result', { tier: tier })" in iife
        assert iife.count("typeof gtag === 'function'") == 2

    def test_js_selectors_exist_in_html(self, coaching_js, coaching_html):
        iife = _fitcheck_js_iife(coaching_js)
        for cls in set(re.findall(r"'\.(rl-coach-[\w-]+)", iife)):
            assert f'class="{cls}' in coaching_html or f' {cls}"' in coaching_html, cls

    def test_cta_listener_binds_fitcheck_ctas(self, coaching_js, fit):
        """cta_click binds once at load via querySelectorAll('[data-cta]').
        The fit-check CTAs are pre-rendered (hidden, never created later),
        so they are in the DOM when the listener binds."""
        assert "document.querySelectorAll('[data-cta]').forEach" in coaching_js
        assert "el.getAttribute('data-cta')" in coaching_js
        assert fit.count('data-cta="fitcheck_apply_') == 3
        assert "createElement" not in _fitcheck_js_iife(coaching_js)

    def test_scoring_every_combination(self, coaching_js):
        """Run the real IIFE against a DOM stub for every answer
        combination (Q3 unanswered or 0/1/2) and compare with the spec."""
        plans, expected = [], []
        for q1 in (0, 1, 2):
            for q2 in (0, 1, 2):
                for q3 in (None, 0, 1, 2):
                    clicks = [[1, q1], [2, q2]] + ([[3, q3]] if q3 is not None else [])
                    plans.append(clicks)
                    expected.append((_fit_score_tier(q1, q2, q3), q3 == 2))
        results = _run_fitcheck(coaching_js, plans)
        for clicks, (tier, tight), r in zip(plans, expected, results):
            assert r["boxHidden"] is False, clicks
            assert r["emptyHidden"] is True and r["answerHidden"] is False, clicks
            assert r["recs"] == [tier] and r["ctas"] == [tier], (clicks, r)
            assert r["fitCols"] == [tier] and r["fitLabels"] == [tier], (clicks, r)
            assert r["tightHidden"] is (not tight), clicks
            assert sorted(r["pressed"]) == sorted(clicks), clicks
            assert r["scrolls"] == [{"block": "nearest", "behavior": "instant"}], (clicks, r["scrolls"])

    def test_named_combinations(self, coaching_js):
        cases = [
            ([[1, 0], [2, 0]], "min"),
            ([[1, 1], [2, 1]], "mid"),
            ([[1, 0], [2, 2]], "mid"),
            ([[1, 2], [2, 2]], "max"),
            ([[1, 1], [2, 2], [3, 2]], "max"),
            ([[1, 1], [2, 2]], "mid"),
        ]
        results = _run_fitcheck(coaching_js, [c for c, _ in cases])
        for (clicks, tier), r in zip(cases, results):
            assert r["recs"] == [tier], (clicks, r["recs"])

    def test_waits_for_first_two_answers(self, coaching_js):
        results = _run_fitcheck(coaching_js, [[], [[1, 2]], [[2, 2], [3, 2]]])
        for r in results:
            assert r["emptyHidden"] is False and r["answerHidden"] is True
            assert r["recs"] == [] and r["ctas"] == [] and r["fitCols"] == [] and r["fitLabels"] == []
            assert not [e for e in r["events"] if e[0] == "coaching_fitcheck_result"]
            assert r["scrolls"] == []
        # The tight note lives inside the answer container, so while that
        # is hidden the note can't show, whatever Q3 says.
        assert "rl-coach-fitcheck-answer" in _ancestor_classes(build_fit_check(), "rl-coach-fitcheck-tight")

    def test_answers_change_live_and_result_fires_only_on_change(self, coaching_js):
        clicks = [[1, 0], [2, 0], [2, 0], [3, 0], [2, 2], [3, 2], [1, 2], [1, 0]]
        # min -> (same) -> (same) -> mid -> mid(3) -> max(5) -> mid(3)
        (r,) = _run_fitcheck(coaching_js, [clicks])
        answers = [e[1] for e in r["events"] if e[0] == "coaching_fitcheck_answer"]
        assert answers == [{"question": q, "answer": a} for q, a in clicks]
        tiers = [e[1]["tier"] for e in r["events"] if e[0] == "coaching_fitcheck_result"]
        assert tiers == ["min", "mid", "max", "mid"]
        assert r["recs"] == ["mid"] and r["fitCols"] == ["mid"]
        assert sorted(r["pressed"]) == [[1, 0], [2, 2], [3, 2]]
        # Scrolls once, on the first reveal; later answer changes never do.
        assert r["scrolls"] == [{"block": "nearest", "behavior": "instant"}]

    def test_desktop_never_scrolls(self, coaching_js):
        """Side by side (above the 768px breakpoint) the result is beside
        the questions and there is no sticky bar: the page must not move."""
        plans = [[[1, a], [2, b], [3, 2]] for a in (0, 1, 2) for b in (0, 1, 2)]
        for r in _run_fitcheck(coaching_js, plans, viewport="desktop"):
            assert r["scrolls"] == []
            assert r["recs"] and r["answerHidden"] is False

    def test_scroll_breakpoint_matches_css(self, coaching_js, coaching_css):
        assert "window.matchMedia('(max-width: 768px)')" in _fitcheck_js_iife(coaching_js)
        assert "@media (max-width: 768px)" in coaching_css.split("/* ── Responsive", 1)[1]
