"""Race database score bar opens its breakdown from the keyboard (#198).

The bar is a real <button type="button"> with aria-expanded/aria-controls,
toggled by the delegated click listener (no inline onclick). Races without a
breakdown get a plain, non-interactive bar.
"""
import json
import re
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
JS_PATH = ROOT / "web" / "road-labs-search.js"
JS = JS_PATH.read_text()
CSS = (ROOT / "web" / "rl-search.css").read_text()


def _render_card_src():
    start = JS.index("function renderCard(race)")
    return JS[start:JS.index("// ── Tier grouping", start)]


def test_score_bar_is_a_button_with_state():
    src = _render_card_src()
    assert ('<button type="button" class="rl-score-bar" aria-expanded="false" '
            'aria-controls="\' + breakdownId + \'"') in src
    assert "aria-label=\"Score breakdown, ' + score + ' out of 100\"" in src


def test_no_inline_handlers_anywhere_on_cards():
    assert "onclick" not in _render_card_src()
    assert not re.search(r'rl-score-bar"[^>]*onclick', JS)


def test_breakdown_has_matching_id():
    assert "renderScoreBreakdown(race.scores, breakdownId)" in JS
    assert '<div class="rl-score-breakdown" id="\' + id + \'">' in JS
    assert "var breakdownId = 'rl-score-breakdown-' + escHtml(race.slug);" in JS


def test_button_only_when_breakdown_exists():
    src = _render_card_src()
    assert "if (score && breakdown)" in src
    assert "rl-score-bar rl-score-bar--static" in src


def test_button_reset_and_visible_focus():
    m = re.search(r"#rl-race-search button\.rl-score-bar \{([^}]*)\}", CSS)
    assert m
    body = m.group(1)
    for decl in ("background: transparent !important", "border: 0 !important",
                 "padding: 0 !important", "min-height: 24px"):
        assert decl in body
    assert re.search(r"button\.rl-score-bar:focus-visible \{[^}]*outline: 3px solid var\(--rl-color-ink\)", CSS)


def test_fill_is_block_inside_span_track():
    m = re.search(r"#rl-race-search \.rl-score-fill \{([^}]*)\}", CSS)
    assert "display: block" in m.group(1)


# Load the REAL file into node with a stub DOM, render a card through the
# script's own renderCard (reached via the grid it writes), then dispatch the
# document click listener the script registered at the rendered button.
NODE_HARNESS = r"""
const fs = require('fs');
const src = fs.readFileSync(process.argv[1], 'utf8');
const race = JSON.parse(process.argv[2]);

function classList() { const s = new Set(); return {
  add(c) { s.add(c); }, remove(c) { s.delete(c); },
  toggle(c, f) { const on = f === undefined ? !s.has(c) : f; on ? s.add(c) : s.delete(c); return on; },
  contains(c) { return s.has(c); } }; }

const listeners = {};
const el = () => new Proxy(function () {}, { get: (t, k) => k === Symbol.toPrimitive ? () => '' : el(), apply: () => el() });
const document = new Proxy({}, { get: (t, k) => {
  if (k === 'addEventListener') return (type, fn) => { (listeners[type] = listeners[type] || []).push(fn); };
  if (k === 'readyState') return 'loading';
  if (k === 'getElementById') return (id) => panels[id] || null;
  return el(); } });
const window = {};
const localStorage = { getItem: () => null, setItem: () => {} };
global.fetch = () => new Promise(() => {});

// Expose renderCard: append an export before the IIFE closes.
const patched = src.replace(/\}\)\(\);\s*$/, 'window.__renderCard = renderCard;\n})();');
new Function('window', 'document', 'localStorage', patched)(window, document, localStorage);

const html = window.__renderCard(race);
const btnMatch = html.match(/<button type="button" class="rl-score-bar"([^>]*)>/);
const panelId = (html.match(/<div class="rl-score-breakdown" id="([^"]+)"/) || [])[1];
const panels = {};
if (panelId) panels[panelId] = { classList: classList() };
const out = { onfocus: html.includes('onfocus'), hasButton: !!btnMatch, panelId, static: html.includes('rl-score-bar--static'),
              linked: html.includes('rl-card-linked'), clicks: listeners.click ? listeners.click.length : 0, states: [] };
if (btnMatch) {
  const attrs = {};
  btnMatch[1].replace(/([a-z-]+)="([^"]*)"/g, (_, k, v) => { attrs[k] = v; });
  const btn = { getAttribute: k => attrs[k], setAttribute: (k, v) => { attrs[k] = v; } };
  const target = { closest: sel => (sel === 'button.rl-score-bar' ? btn : null) };
  for (let i = 0; i < 2; i++) {
    listeners.click.forEach(fn => fn({ target }));
    out.states.push([attrs['aria-expanded'], panels[panelId].classList.contains('open')]);
  }
  out.controls = attrs['aria-controls'];
  out.label = attrs['aria-label'];
}
console.log(JSON.stringify(out));
"""

SCORES = {k: 3 for k in ("distance", "climbing", "descent_technicality", "road_surface",
                         "climate_risk", "altitude", "logistics", "prestige", "organization",
                         "scenic_experience", "community_culture", "field_depth", "value", "expenses")}


def _run(race):
    if not shutil.which("node"):
        pytest.skip("node not installed")
    r = subprocess.run(["node", "-e", NODE_HARNESS, str(JS_PATH), json.dumps(race)],
                       capture_output=True, text=True, check=True)
    return json.loads(r.stdout)


def test_rendered_button_toggles_breakdown():
    """Real renderCard + real delegated listener: two clicks open then close
    the panel and keep aria-expanded in sync (Enter/Space reach a native
    <button> as click events)."""
    out = _run({"slug": "etape-test", "name": "Etape Test", "tier": 2, "overall_score": 71,
                "has_profile": True, "profile_url": "/race/etape-test/", "scores": SCORES})
    assert out["hasButton"] and out["linked"]
    assert out["clicks"] == 1
    assert out["controls"] == out["panelId"] == "rl-score-breakdown-etape-test"
    assert out["label"] == "Score breakdown, 71 out of 100"
    assert out["states"] == [["true", True], ["false", False]]


def test_hostile_score_cannot_break_out_of_attributes():
    """overall_score lands in aria-label and style; a non-numeric value from
    the index must not inject markup (Astra review, PR #199)."""
    out = _run({"slug": "x", "name": "X", "tier": 2, "overall_score": '71" onfocus="alert(1)//',
                "has_profile": True, "profile_url": "/race/x/", "scores": SCORES})
    assert not out["onfocus"]
    assert not out["hasButton"] and not out["static"]  # NaN -> no bar
    out = _run({"slug": "y", "name": "Y", "tier": 2, "overall_score": "71.6",
                "has_profile": True, "profile_url": "/race/y/", "scores": SCORES})
    assert out["label"] == "Score breakdown, 72 out of 100"


def test_no_breakdown_renders_static_bar():
    out = _run({"slug": "thin", "name": "Thin", "tier": 4, "overall_score": 40,
                "has_profile": False, "scores": {"distance": 2}})
    assert not out["hasButton"] and out["static"] and not out["linked"]
