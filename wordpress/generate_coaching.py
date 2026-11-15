#!/usr/bin/env python3
"""
Generate the Roadie Labs Coaching landing page: "Field Notes".

The page reads like the file I keep on a racer: ruled paper, JetBrains Mono
labels, red section marks, an ID card with my photo that crossfades into the
v6.7 character in the Roadie kit doing the same thing, a "week with me"
chart built only from the real inclusions, and the prices on a paper ledger
in an ink band (tabs on phone).

Rebuilt 2026-11-15 from the "Dossier" (hero → terms → tiers → fit → faq →
final-cta) to match the Gravel God sibling page Matti picked (mock "Opus C,
field notes" with the "Astra B" photo card). Same structure and section ids
as gravel-race-automation/wordpress/generate_coaching.py, road copy.
Section order: hero (H1 + ID card) → fit → terms (what you get) → week →
how-it-works → tiers (levels ledger + 3-question picker) → faq → final-cta.

Not built, on purpose (no stand-ins): an athlete-words proof section, a
capacity line, and close art (there is no v6.7 Roadie-kit scene to use yet;
the close runs without a picture rather than borrowing Gravel God art).

Uses brand tokens exclusively: zero hardcoded hex, no border-radius, no
box-shadow, no bounce easing.

Usage:
    python generate_coaching.py
    python generate_coaching.py --output-dir ./output
"""

import argparse
import html
import json
import shutil
from pathlib import Path

from generate_neo_brutalist import (
    SITE_BASE_URL,
    get_page_css,
    build_inline_js,
    write_shared_assets,
    _safe_json_for_script,
)
from brand_tokens import get_ab_head_snippet, get_ga4_head_snippet, get_preload_hints
from shared_footer import get_mega_footer_html
from shared_header import get_site_header_html, get_site_header_js
from cookie_consent import get_consent_banner_html
from live_head_patches import apply_live_head_patches

OUTPUT_DIR = Path(__file__).parent / "output"
PROJECT_ROOT = Path(__file__).resolve().parent.parent
RACE_INDEX_JSON = PROJECT_ROOT / "web" / "race-index.json"


def load_race_count() -> int:
    """Race count from race-index.json — never hardcode (stale-count trap, see ab_experiments.py)."""
    if not RACE_INDEX_JSON.exists():
        raise RuntimeError(
            f"Required race index is missing: {RACE_INDEX_JSON}. "
            "Run python3 scripts/generate_index.py before generating coaching."
        )
    return len(json.loads(RACE_INDEX_JSON.read_text(encoding="utf-8")))


# Images the page needs. main() copies them next to coaching.html under
# coaching-img/, and push_wordpress.sync_coaching uploads that folder to
# /coaching/img/ before the page. A missing file stops the build: no
# stand-in picture.
IMG_SRC_DIR = Path(__file__).parent / "assets" / "coaching"
IMG_URL_BASE = "/coaching/img"
IMAGES = {
    # Real photo: grocery aisle, felt hat, frozen pizza.
    "photo": ("matti-pizza.webp", 720, 960),
    # v6.7 character (gravel-god-character rig, roadie outfit) in the same pose.
    "cartoon": ("matti-pizza-v67-roadie.webp", 720, 960),
}
IMG_OUTPUT_SUBDIR = "coaching-img"

# ── Constants ─────────────────────────────────────────────────

QUESTIONNAIRE_URL = f"{SITE_BASE_URL}/coaching/apply/"
CONTACT_EMAIL = "coach@roadielabs.com"

# Tier identity: the single source for name and price. The ledger head and
# the picker result both render from this, so a price can't drift.
TIERS = (
    ("min", "Min", "$199"),
    ("mid", "Mid", "$299"),
    ("max", "Max", "$1,200"),
)
TIER_INTERVAL = "every 4 weeks"
TIER_BLURBS = {
    "min": "You race, you train on your own, and you want a racer checking the work every week.",
    "mid": "Between races and sessions I&#39;m in your files, and the plan follows what I see.",
    "max": "Same-day file review, on-demand calls and race-week strategy for the race you&#39;ve built the year around.",
}

# The ID card under my photo. Matti's own bio line, verbatim, and a
# self-deprecating road resume of public facts (about page): very few have
# gotten farther on less talent.
ID_BIO = "I&#39;m Matti Rowe. Peddler of bikes and hot takes, and really fast clients."
ID_ROWS = (
    ("Category", "Cat 1. Raced the NRC with Cat 5 handling skills."),
    ("Team", "Rio Grande Elite, right up until it folded. My third kid showed up that same year."),
    ("Day job", "Twelve years at TrainingPeaks teaching coaches and athletes. Promoted twice."),
    ("Talent", "In short supply. Very few people have gotten farther on less."),
)

# Picker: three questions, answers 1-3, the rounded mean marks a tier.
PICKER_INTRO = "Answer three questions and I&#39;ll mark the one I&#39;d pick."
PICKER_QUESTIONS = (
    ("How often do you want me in your files?", (
        "Weekly is enough",
        "Between races and sessions",
        "Every file, same day",
    )),
    ("A week goes sideways. When should the plan react?", (
        "At the weekly review",
        "Before the next workout",
        "Today, on a call",
    )),
    ("What&#39;s the season built around?", (
        "One A race, my own way",
        "One A race, done right",
        "A full calendar, planned as one season",
    )),
)
PICKER_EMPTY = "Answer all three and I&#39;ll mark my pick."

# Ledger rows: (label, min, mid, max). True = included, False = not,
# a string = the value for that tier.
LEDGER_GROUPS = (
    ("Every level", (
        ("Weekly training review", True, True, True),
        ("File analysis", True, True, True),
        ("Structured workouts for your trainer or head unit", True, True, True),
        ("Race-day nutrition plan", True, True, True),
        ("Custom training guide", True, True, True),
        ("TrainingPeaks Premium", True, True, True),
        ("Strategy calls", "Quarterly", "Every 4 weeks", "Every 4 weeks + on demand"),
    )),
    ("Mid and Max", (
        ("Detailed power-file analysis", False, True, True),
        ("Weekly plan adjustments", False, True, True),
        ("Direct message access", False, True, True),
        ("Blindspot detection", False, True, True),
    )),
    ("Max only", (
        ("Daily file review", False, False, True),
        ("Race-week strategy", False, False, True),
        ("Multi-race season planning", False, False, True),
        ("Priority response", False, False, True),
    )),
)


def esc(text) -> str:
    """HTML-escape a string."""
    return html.escape(str(text)) if text else ""


def _img(key: str) -> tuple:
    name, w, h = IMAGES[key]
    return f"{IMG_URL_BASE}/{name}", w, h


def _sec_head(num: str, label: str, title: str, sub: str = "") -> str:
    sub_html = f'<p>{sub}</p>' if sub else ''
    return (
        f'<div class="rl-coach-sec-head">'
        f'<p class="rl-coach-label rl-coach-sec-num">{num} / {label}</p>'
        f'<div><h2 class="rl-coach-sec-title">{title}</h2>{sub_html}</div>'
        f'</div>'
    )


# ── Page sections ─────────────────────────────────────────────


def build_nav() -> str:
    return get_site_header_html(active="services") + f'''
  <div class="rl-breadcrumb">
    <a href="{SITE_BASE_URL}/">Home</a>
    <span class="rl-breadcrumb-sep">&rsaquo;</span>
    <span class="rl-breadcrumb-current">Coaching</span>
  </div>'''


def build_id_card() -> str:
    photo, pw, ph = _img("photo")
    toon, tw, th = _img("cartoon")
    rows = "\n          ".join(
        f'<div><span>{label}</span>{value}</div>' for label, value in ID_ROWS
    )
    return f'''<aside class="rl-coach-id" aria-label="Who I am">
        <div class="rl-coach-id-head"><span>Licence: Matti Rowe</span><span>RL-01</span></div>
        <figure class="rl-coach-id-photo">
          <img class="rl-coach-id-real" src="{photo}" alt="Me in a felt hat in the grocery aisle, grinning, holding a frozen pizza." width="{pw}" height="{ph}">
          <img class="rl-coach-id-toon" src="{toon}" alt="" aria-hidden="true" width="{tw}" height="{th}" loading="lazy">
        </figure>
        <p class="rl-coach-id-bio">{ID_BIO}</p>
        <div class="rl-coach-id-rows">
          {rows}
        </div>
      </aside>'''


# Hero copy approved by Matti 2026-11-15 (one plain line that says what the
# product is). Say what I do, never what I'm not:
# tests/test_no_ai_positioning.py enforces it.
def build_hero() -> str:
    return f'''<section class="rl-coach-band rl-coach-hero" id="hero">
    <div class="rl-coach-inner rl-coach-hero-grid">
      <div>
        <div class="rl-coach-hero-file"><span>File: Coaching</span><span>One-on-one</span><span>Road</span></div>
        <h1>One-on-one coaching for road racers, from <mark>Tuesday-night crits</mark> to <mark>the long road race.</mark></h1>
        <p class="rl-coach-tagline">I raced Cat 1 and on the NRC. Now I plan your season around your races and read your files to see how they went. Coaching runs <strong>$199, $299 or $1,200</strong> every 4 weeks.</p>
        <div class="rl-coach-hero-actions">
          <a href="{QUESTIONNAIRE_URL}" class="rl-coach-btn rl-coach-hero-cta" data-cta="hero_apply">START YOUR APPLICATION &rarr;</a>
          <span class="rl-coach-fine">Ten minutes of questions. I reply inside two business days.</span>
        </div>
      </div>
      {build_id_card()}
    </div>
  </section>'''


def build_honest_check() -> str:
    yes = (
        "You have races on the calendar and want to finish them closer to the front.",
        "You&#39;ll upload every ride and race, and tell me what happened in the bunch.",
        "You can hear &ldquo;you went too early&rdquo; without taking it personally.",
    )
    no = (
        "You want a fix for Saturday&#39;s race.",
        "You&#39;re coming back from a crash and need rehab. That&#39;s a physio&#39;s job.",
        "You&#39;d rather ride by feel and never look at a file.",
    )
    li = lambda items: "\n            ".join(
        f'<li><span class="rl-coach-box" aria-hidden="true"></span><span>{t}</span></li>' for t in items
    )
    return f'''<section class="rl-coach-band rl-coach-band--dark rl-coach-fit" id="fit">
    <div class="rl-coach-inner">
      {_sec_head("01", "Fit check", "Read this before you sign on.")}
      <div class="rl-coach-fit-grid">
        <div class="rl-coach-fit-yes">
          <h3>Coaching fits if</h3>
          <ul>
            {li(yes)}
          </ul>
        </div>
        <div class="rl-coach-fit-no">
          <h3>Probably not a fit if</h3>
          <ul>
            {li(no)}
          </ul>
        </div>
      </div>
    </div>
  </section>'''


def build_terms() -> str:
    items = (
        ("Your race files, read.",
         "I look at where the race went hard and what you did there, from the surge you closed to the gap you let go on the last lap."),
        ("Training for how road races are decided.",
         "Repeated surges, climbs at threshold, a sprint after two hours in the bunch. The workouts aim at what your races ask of you."),
        ("A season around your A race.",
         "B races and crits fit around it, and we talk strategy every quarter at Min and every 4 weeks at Mid and Max."),
        ("Plans that bend.",
         "At Mid and Max, a missed day or a hard week at work changes the next workout, so you don&#39;t chase the old plan."),
        ("Honest reads.",
         "When you&#39;re racing yourself out of form, I&#39;ll tell you. When you can handle more, I&#39;ll tell you that too."),
    )
    rows = "\n        ".join(
        f'<li><p class="rl-coach-label">Item {i:02d}</p><h3>{t}</h3><p>{b}</p></li>'
        for i, (t, b) in enumerate(items, start=1)
    )
    return f'''<section class="rl-coach-band" id="terms">
    <div class="rl-coach-inner">
      {_sec_head("02", "What you get", "Your races read, and a season built around the one that counts.")}
      <ol class="rl-coach-get">
        {rows}
      </ol>
    </div>
  </section>'''


def build_week() -> str:
    rows = (
        ("Each ride", ("off", "Read at the weekly review"), ("on", "In your files between races and sessions"), ("on", "Same-day file review")),
        ("Each week", ("on", "Weekly training review and file analysis"), ("on", "Plan adjusted weekly, detailed power-file analysis, blindspot detection"), ("on", "Everything in Mid")),
        ("Life happens", ("off", "Sorted at the weekly review"), ("on", "Message me; the next workout changes"), ("on", "On-demand calls, priority response")),
        None,
        ("Strategy calls", ("on", "Quarterly"), ("on", "Every 4 weeks"), ("on", "Every 4 weeks, plus on demand")),
        ("Race week", ("on", "Race-day nutrition plan"), ("on", "Race-day nutrition plan"), ("on", "Race-week strategy and nutrition plan")),
        ("The season", ("on", "Custom training guide"), ("on", "Custom training guide"), ("on", "Multi-race season planning")),
    )
    body = []
    for row in rows:
        if row is None:
            body.append('<tr class="rl-coach-cad-note"><td colspan="4"><span class="rl-coach-note">A late night at work, a missed day, a sick kid. This row is where the levels split.</span></td></tr>')
            continue
        when, *cells = row
        tds = "".join(
            f'<td class="rl-coach-cad-{state}" data-t="{name.upper()}">{text}</td>'
            for (key, name, _p), (state, text) in zip(TIERS, cells)
        )
        body.append(f'<tr><th scope="row">{when}</th>{tds}</tr>')
    body_html = "\n          ".join(body)
    return f'''<section class="rl-coach-band rl-coach-band--sand" id="week">
    <div class="rl-coach-inner">
      {_sec_head("03", "A week with me", "How a week with me looks at each level.", "Same races, same calendar. What changes is how often I&#39;m in your files and how fast the plan reacts.")}
      <table class="rl-coach-cad">
        <thead><tr><th>When</th><th>Min</th><th>Mid</th><th>Max</th></tr></thead>
        <tbody>
          {body_html}
        </tbody>
      </table>
    </div>
  </section>'''


def build_how_it_works() -> str:
    steps = (
        ("About 10 min", "You apply.", "Your racing, your category, your calendar and your week."),
        ("2 business days", "I get back to you.", "Even when coaching isn&#39;t what you need."),
        ("If it&#39;s a fit", "Agreement, then checkout.", "A short agreement and consent, then a checkout link for your first 4 weeks and the $99 setup fee."),
        ("Setup", "Your first block.", "I get you set up on TrainingPeaks and build the first plan from your intake."),
        ("Every week after", "Your level&#39;s rhythm.", "What the chart above shows, at the level you chose."),
    )
    rows = "\n        ".join(
        f'<li><span class="rl-coach-label">{when}</span><div><h3>{t}</h3><p>{b}</p></div></li>'
        for when, t, b in steps
    )
    return f'''<section class="rl-coach-band" id="how-it-works">
    <div class="rl-coach-inner">
      {_sec_head("04", "How it works", "What happens once you hit apply.")}
      <ol class="rl-coach-steps">
        {rows}
      </ol>
    </div>
  </section>'''


def build_fit_check() -> str:
    """Three-question picker. Rendered `hidden`; build_coaching_js() shows
    it, so without JS the ledger stands alone."""
    sets = []
    for qi, (text, options) in enumerate(PICKER_QUESTIONS, start=1):
        labels = "\n          ".join(
            f'<label><input type="radio" name="rl-coach-q{qi}" value="{ai}"><span>{opt}</span></label>'
            for ai, opt in enumerate(options, start=1)
        )
        sets.append(f'''<fieldset><legend>Q{qi}</legend><p>{text}</p>
          {labels}</fieldset>''')
    fieldsets = "\n        ".join(sets)
    return f'''<form class="rl-coach-picker" id="rl-coach-picker" aria-label="Three questions to pick a level" hidden>
        {fieldsets}
      </form>
      <p class="rl-coach-picker-out" id="rl-coach-picker-out" aria-live="polite" hidden>{PICKER_EMPTY}</p>'''


def _ledger_cell(key: str, value) -> str:
    if value is True:
        inner = '<span class="rl-coach-y" role="img" aria-label="Included"></span>'
    elif value is False:
        inner = '<span class="rl-coach-n" role="img" aria-label="Not included"></span>'
    else:
        inner = value
    return f'<td class="rl-coach-t-{key}">{inner}</td>'


def build_tiers() -> str:
    heads = "\n            ".join(
        f'<th class="rl-coach-t-{key}" data-tier="{key}" scope="col">'
        f'<span class="rl-coach-tname">{name} <span class="rl-coach-tpick">My pick</span></span>'
        f'<span class="rl-coach-tprice">{price}</span>'
        f'<span class="rl-coach-tper">{TIER_INTERVAL}</span>'
        f'<span class="rl-coach-tblurb">{TIER_BLURBS[key]}</span></th>'
        for key, name, price in TIERS
    )
    body = []
    for group, rows in LEDGER_GROUPS:
        body.append(f'<tr class="rl-coach-grp"><th colspan="4" scope="colgroup">{group}</th></tr>')
        for label, *vals in rows:
            cells = "".join(_ledger_cell(key, v) for (key, _n, _p), v in zip(TIERS, vals))
            body.append(f'<tr><th scope="row">{label}</th>{cells}</tr>')
    body_html = "\n            ".join(body)
    foot = "\n            ".join(
        f'<td class="rl-coach-t-{key}"><a href="{QUESTIONNAIRE_URL}?tier={key}" class="rl-coach-btn rl-coach-tier-cta" data-cta="tier_{key}">START WITH {name.upper()}</a></td>'
        for key, name, _p in TIERS
    )
    tabs = "\n        ".join(
        f'<button type="button" role="tab" data-tab="{key}" aria-selected="{"true" if key == "mid" else "false"}">{name}</button>'
        for key, name, _p in TIERS
    )
    return f'''<section class="rl-coach-band rl-coach-band--brown" id="tiers">
    <div class="rl-coach-inner">
      {_sec_head("05", "Levels &amp; prices", "Pick how close I sit on your wheel.", "Every level bills every 4 weeks and comes with TrainingPeaks Premium. " + PICKER_INTRO)}
      {build_fit_check()}
      <div class="rl-coach-tabs" role="tablist" aria-label="Levels">
        {tabs}
      </div>
      <table class="rl-coach-ledger" id="rl-coach-ledger" data-show="mid">
        <colgroup><col class="rl-coach-c0"><col><col><col></colgroup>
        <thead>
          <tr>
            <th scope="col">Level</th>
            {heads}
          </tr>
        </thead>
        <tbody>
            {body_html}
        </tbody>
        <tfoot>
          <tr><td></td>
            {foot}
          </tr>
        </tfoot>
      </table>
      <div class="rl-coach-tier-setup-fee rl-coach-fine">
        <p><strong>$99 one-time setup fee</strong> on every level. It pays for the intake analysis, a look through your training history and the first plan build. Any waiver is offered privately, case by case.</p>
        <p>Renews every 4 weeks. Cancel any time before the next renewal; you keep coaching through what you&#39;ve paid for, and there&#39;s no cancellation fee.</p>
      </div>
    </div>
  </section>'''


FAQS = (
    ("What happens after I apply?",
     "You&#39;ll hear back from me within two business days. If coaching isn&#39;t what you need, I&#39;ll say that too."),
    ("How often will I hear from you?",
     "Weekly, and more once racing starts. Mid and Max get direct messages."),
    ("Do I need a power meter?",
     "It helps most in road racing, where surges are short and heart rate lags behind them. Without one, you train to effort and heart rate."),
    ("I race crits and road races. Can you plan both?",
     "Yes. We pick the A race and fit the rest around it."),
    ("What if I miss workouts?",
     "Tell me. At Mid and Max I move things that week, and at Min we sort it out in the weekly review. Don&#39;t make up a missed interval session by skipping recovery."),
    ("How will I know it&#39;s working?",
     "We test at intake and retest through the season."),
    ("What&#39;s the $99 setup fee?",
     "It covers intake analysis, training-history review, and building your first plan. It&#39;s a one-time charge on top of your first billing cycle."),
    ("Can I cancel anytime?",
     "Yes. There is no long-term commitment. Coaching renews every four weeks; cancel before the next renewal and your access continues through the paid cycle. There is no cancellation fee."),
)


def build_faq() -> str:
    items = "\n        ".join(
        f'<details class="rl-coach-faq-item"><summary><span class="rl-coach-label">Q{i:02d}</span>'
        f'<span class="rl-coach-faq-q">{q}</span></summary><p>{a}</p></details>'
        for i, (q, a) in enumerate(FAQS, start=1)
    )
    return f'''<section class="rl-coach-band rl-coach-faq" id="faq">
    <div class="rl-coach-inner">
      {_sec_head("06", "Questions", "What racers ask before they apply.")}
      <div class="rl-coach-faq-list">
        {items}
      </div>
    </div>
  </section>'''


def build_application_close() -> str:
    return f'''<section class="rl-coach-band rl-coach-close" id="final-cta">
    <div class="rl-coach-inner">
      <div class="rl-coach-close-copy">
        <p class="rl-coach-label">07 / Application</p>
        <h2>Get on the start list.</h2>
        <p class="rl-coach-final-hook">Ten minutes on your racing, your category, your calendar and your week. You hear back within two business days.</p>
        <a href="{QUESTIONNAIRE_URL}" class="rl-coach-btn rl-coach-btn--gold" data-cta="final_fill_intake">START YOUR APPLICATION &rarr;</a>
        <p class="rl-coach-fine rl-coach-final-contact">Email me at <a href="mailto:{CONTACT_EMAIL}">{CONTACT_EMAIL}</a> if you want to ask something before you apply.<br>One-time $99 setup. Renews every 4 weeks, cancel before the next one, no fee.</p>
      </div>
    </div>
  </section>'''


def build_footer() -> str:
    return get_mega_footer_html()


def build_mobile_sticky_cta() -> str:
    return f'''<div class="rl-coach-sticky-cta">
    <a href="{QUESTIONNAIRE_URL}" data-cta="sticky_cta">START YOUR APPLICATION &rarr;</a>
  </div>'''


# ── CSS ───────────────────────────────────────────────────────


def build_coaching_css() -> str:
    """Coaching-page-specific CSS. All rl-coach-* prefix. Brand tokens only."""
    return '''<style>
/* ── Skip link ──────────────────────────────────── */
.rl-coach-skip-link {
  position: absolute;
  left: -9999px;
  top: 0;
  z-index: 1001;
  padding: var(--rl-spacing-xs) var(--rl-spacing-md);
  background: var(--rl-color-near-black);
  color: var(--rl-color-cool-white);
  font-family: var(--rl-font-data);
  font-size: var(--rl-font-size-sm);
  text-decoration: none;
}
.rl-coach-skip-link:focus {
  left: 0;
}

/* ── Full-bleed layout override ──────────────────
   The shared container caps every neo-brutalist page at 960px.
   Here the container goes full-width; each band paints the whole
   viewport and constrains its own content to the 1200px measure. */
.rl-neo-brutalist-page {
  max-width: none;
  padding: 0;
}
.rl-coach-inner {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 var(--rl-spacing-lg);
}
.rl-neo-brutalist-page .rl-site-header {
  padding-left: var(--rl-spacing-lg);
  padding-right: var(--rl-spacing-lg);
}
.rl-neo-brutalist-page .rl-site-header-inner {
  max-width: 1200px;
}
.rl-neo-brutalist-page .rl-breadcrumb {
  max-width: 1200px;
  margin: 0 auto;
  padding-left: var(--rl-spacing-lg);
  padding-right: var(--rl-spacing-lg);
  background: transparent;
}
.rl-neo-brutalist-page .rl-mega-footer-grid,
.rl-neo-brutalist-page .rl-mega-footer-legal,
.rl-neo-brutalist-page .rl-mega-footer-disclaimer {
  max-width: 1200px;
}
.rl-neo-brutalist-page .rl-mega-footer {
  margin-top: 0;
}

/* ── Ground: graph paper ─────────────────────────── */
.rl-neo-brutalist-page {
  background-color: var(--rl-color-paper);
  background-image:
    repeating-linear-gradient(0deg, var(--rl-color-well) 0 1px, transparent 1px 24px),
    repeating-linear-gradient(90deg, var(--rl-color-well) 0 1px, transparent 1px 24px);
}
.rl-coach-band { padding: var(--rl-spacing-4xl) 0; color: var(--rl-color-dark-navy); }
.rl-coach-band--dark { background: var(--rl-color-near-black); color: var(--rl-color-paper); }
.rl-coach-band--brown { background: var(--rl-color-dark-navy); color: var(--rl-color-paper); }
.rl-coach-band--sand { background: var(--rl-color-well); border-top: var(--rl-border-width-standard) solid var(--rl-color-dark-navy); border-bottom: var(--rl-border-width-standard) solid var(--rl-color-dark-navy); }
.rl-coach-label { font-family: var(--rl-font-data); font-size: var(--rl-font-size-xs); letter-spacing: var(--rl-letter-spacing-wider); text-transform: uppercase; font-weight: var(--rl-font-weight-bold); color: var(--rl-color-graphite); margin: 0; }
.rl-coach-note { font-family: var(--rl-font-editorial); font-style: italic; color: var(--rl-color-opinion); font-size: var(--rl-font-size-base); }
.rl-coach-fine { font-family: var(--rl-font-data); font-size: var(--rl-font-size-xs); line-height: var(--rl-line-height-normal); }
.rl-coach-btn { display: inline-block; font-family: var(--rl-font-data); font-weight: var(--rl-font-weight-bold); font-size: var(--rl-font-size-sm); letter-spacing: var(--rl-letter-spacing-wider); text-transform: uppercase; text-decoration: none; padding: var(--rl-spacing-md) var(--rl-spacing-lg); background: var(--rl-color-offer); color: var(--rl-color-white); border: var(--rl-border-width-standard) solid var(--rl-color-offer); transition: background var(--rl-transition-hover), color var(--rl-transition-hover), border-color var(--rl-transition-hover); }
.rl-coach-btn:hover, .rl-coach-btn:focus-visible { background: var(--rl-color-near-black); border-color: var(--rl-color-near-black); color: var(--rl-color-white); }
.rl-coach-btn--gold { background: var(--rl-color-tier-gold); border-color: var(--rl-color-tier-gold); color: var(--rl-color-near-black); }
.rl-coach-btn--gold:hover, .rl-coach-btn--gold:focus-visible { background: var(--rl-color-paper); border-color: var(--rl-color-paper); color: var(--rl-color-near-black); }

/* ── Section heads: mono label on a teal rule ────── */
.rl-coach-sec-head { display: grid; grid-template-columns: 200px 1fr; gap: var(--rl-spacing-xl); margin-bottom: var(--rl-spacing-2xl); }
.rl-coach-sec-num { padding-top: var(--rl-spacing-sm); border-top: var(--rl-border-width-heavy) solid var(--rl-color-score); color: var(--rl-color-score); align-self: start; }
.rl-coach-sec-title { margin: 0; font-family: var(--rl-font-editorial); font-size: clamp(30px, 3.6vw, 46px); line-height: var(--rl-line-height-tight); letter-spacing: var(--rl-letter-spacing-tight); color: var(--rl-color-near-black); }
.rl-coach-sec-head p { margin: var(--rl-spacing-sm) 0 0; max-width: 46em; }
.rl-coach-band--dark .rl-coach-sec-title, .rl-coach-band--brown .rl-coach-sec-title { color: var(--rl-color-paper); }
.rl-coach-band--dark .rl-coach-sec-num { color: var(--rl-color-tier-gold); border-color: var(--rl-color-tier-gold); }
.rl-coach-band--brown .rl-coach-sec-num { color: var(--rl-color-tier-gold); border-color: var(--rl-color-tier-gold); }
.rl-coach-band--brown .rl-coach-sec-head p { color: var(--rl-color-silver); }

/* ── Hero ────────────────────────────────────────── */
.rl-coach-hero { padding: var(--rl-spacing-3xl) 0; }
.rl-coach-hero-grid { display: grid; grid-template-columns: 1fr 360px; gap: var(--rl-spacing-3xl); align-items: start; }
.rl-coach-hero-file { display: flex; gap: var(--rl-spacing-lg); margin-bottom: var(--rl-spacing-lg); flex-wrap: wrap; }
.rl-coach-hero-file span { font-family: var(--rl-font-data); font-size: var(--rl-font-size-xs); letter-spacing: var(--rl-letter-spacing-wide); text-transform: uppercase; border-bottom: var(--rl-border-width-subtle) solid var(--rl-color-dark-navy); padding-bottom: 2px; }
.rl-coach-hero h1 { font-family: var(--rl-font-editorial); font-weight: var(--rl-font-weight-bold); font-size: clamp(34px, 5vw, 66px); line-height: 1.04; letter-spacing: var(--rl-letter-spacing-tight); margin: 0 0 var(--rl-spacing-lg); color: var(--rl-color-near-black); }
.rl-coach-hero h1 mark { background: linear-gradient(transparent 58%, var(--rl-color-tier-gold) 58%, var(--rl-color-tier-gold) 92%, transparent 92%); color: inherit; padding: 0 2px; }
.rl-coach-tagline { font-family: var(--rl-font-editorial); font-size: var(--rl-font-size-lg); margin: 0 0 var(--rl-spacing-xl); max-width: 34em; }
.rl-coach-tagline strong { font-family: var(--rl-font-data); font-size: 0.9em; background: var(--rl-color-dark-navy); color: var(--rl-color-tier-gold); padding: 1px 6px; white-space: nowrap; }
.rl-coach-hero-actions { display: flex; flex-wrap: wrap; align-items: center; gap: var(--rl-spacing-md) var(--rl-spacing-lg); }

/* ── ID card: real photo crossfades to the v6.7 me ── */
.rl-coach-id { background: var(--rl-color-white); border: var(--rl-border-width-standard) solid var(--rl-color-dark-navy); transform: rotate(1.5deg); }
.rl-coach-id-head { background: var(--rl-color-dark-navy); color: var(--rl-color-paper); padding: var(--rl-spacing-xs) var(--rl-spacing-md); display: flex; justify-content: space-between; font-family: var(--rl-font-data); font-size: var(--rl-font-size-2xs); letter-spacing: var(--rl-letter-spacing-wider); text-transform: uppercase; }
.rl-coach-id-photo { position: relative; margin: var(--rl-spacing-md); aspect-ratio: 3 / 4; border: var(--rl-border-width-standard) solid var(--rl-color-tier-gold); background: var(--rl-color-well); overflow: hidden; }
.rl-coach-id-photo img { position: absolute; inset: 0; width: 100%; height: 100%; object-fit: cover; object-position: center 20%; }
.rl-coach-id-toon { opacity: 0; animation: rl-coach-idswap 9s ease-in-out 2s infinite; }
@keyframes rl-coach-idswap { 0%, 38% { opacity: 0; } 50%, 88% { opacity: 1; } 100% { opacity: 0; } }
.rl-coach-id-bio { margin: 0 var(--rl-spacing-md) var(--rl-spacing-md); font-family: var(--rl-font-editorial); font-weight: var(--rl-font-weight-bold); font-size: var(--rl-font-size-lg); line-height: var(--rl-line-height-tight); color: var(--rl-color-near-black); }
.rl-coach-id-rows { border-top: var(--rl-border-width-subtle) solid var(--rl-color-dark-navy); }
.rl-coach-id-rows div { display: grid; grid-template-columns: 76px 1fr; gap: var(--rl-spacing-sm); padding: var(--rl-spacing-xs) var(--rl-spacing-md); border-bottom: 1px solid var(--rl-color-silver); font-family: var(--rl-font-editorial); font-size: var(--rl-font-size-sm); line-height: 1.35; }
.rl-coach-id-rows div:last-child { border-bottom: 0; }
.rl-coach-id-rows span { font-family: var(--rl-font-data); font-size: var(--rl-font-size-2xs); letter-spacing: var(--rl-letter-spacing-wide); text-transform: uppercase; color: var(--rl-color-graphite); padding-top: 2px; }

/* ── Fit check ───────────────────────────────────── */
.rl-coach-fit-grid { display: grid; grid-template-columns: 1fr 1fr; gap: var(--rl-spacing-2xl); }
.rl-coach-fit h3 { font-family: var(--rl-font-data); font-size: var(--rl-font-size-sm); letter-spacing: var(--rl-letter-spacing-wider); text-transform: uppercase; margin: 0 0 var(--rl-spacing-md); }
.rl-coach-fit-yes h3 { color: var(--rl-color-tier-gold); }
.rl-coach-fit-no h3 { color: var(--rl-color-steel); }
.rl-coach-fit ul { list-style: none; margin: 0; padding: 0; }
.rl-coach-fit li { display: grid; grid-template-columns: 28px 1fr; gap: var(--rl-spacing-sm); padding: var(--rl-spacing-md) 0; border-top: 1px solid var(--rl-color-graphite); font-family: var(--rl-font-editorial); font-size: var(--rl-font-size-lg); }
.rl-coach-box { width: 20px; height: 20px; border: var(--rl-border-width-subtle) solid currentColor; margin-top: 4px; position: relative; }
.rl-coach-fit-yes .rl-coach-box { color: var(--rl-color-tier-gold); }
.rl-coach-fit-yes .rl-coach-box::after { content: ""; position: absolute; left: 5px; top: 1px; width: 6px; height: 11px; border: solid var(--rl-color-tier-gold); border-width: 0 3px 3px 0; transform: rotate(45deg); }
.rl-coach-fit-no .rl-coach-box { color: var(--rl-color-steel); }
.rl-coach-fit-no .rl-coach-box::before, .rl-coach-fit-no .rl-coach-box::after { content: ""; position: absolute; left: 7px; top: 1px; width: 3px; height: 14px; background: var(--rl-color-steel); transform: rotate(45deg); }
.rl-coach-fit-no .rl-coach-box::after { transform: rotate(-45deg); }
.rl-coach-fit-no li { color: var(--rl-color-silver); }

/* ── What you get ────────────────────────────────── */
.rl-coach-get { list-style: none; margin: 0; padding: 0; display: grid; grid-template-columns: repeat(2, 1fr); gap: var(--rl-spacing-lg); }
.rl-coach-get li { background: var(--rl-color-paper); border: var(--rl-border-width-subtle) solid var(--rl-color-dark-navy); padding: var(--rl-spacing-lg); }
.rl-coach-get li:first-child { grid-column: 1 / -1; background: var(--rl-color-dark-navy); color: var(--rl-color-paper); }
.rl-coach-get li:first-child h3 { font-size: var(--rl-font-size-3xl); color: var(--rl-color-tier-gold); }
.rl-coach-get li:first-child .rl-coach-label { color: var(--rl-color-tier-gold); }
.rl-coach-get li:first-child p { font-size: var(--rl-font-size-lg); }
.rl-coach-get h3 { margin: var(--rl-spacing-xs) 0 var(--rl-spacing-sm); font-family: var(--rl-font-editorial); font-size: var(--rl-font-size-xl); line-height: var(--rl-line-height-tight); }
.rl-coach-get p { margin: 0; max-width: 68ch; font-family: var(--rl-font-editorial); line-height: var(--rl-line-height-relaxed); }

/* ── A week with me ──────────────────────────────── */
.rl-coach-cad { width: 100%; border-collapse: collapse; background: var(--rl-color-paper); border: var(--rl-border-width-standard) solid var(--rl-color-dark-navy); font-family: var(--rl-font-editorial); }
.rl-coach-cad th, .rl-coach-cad td { text-align: left; vertical-align: top; padding: var(--rl-spacing-md); border-bottom: 1px solid var(--rl-color-silver); }
.rl-coach-cad thead th { background: var(--rl-color-dark-navy); color: var(--rl-color-tier-gold); font-family: var(--rl-font-data); font-size: var(--rl-font-size-xs); letter-spacing: var(--rl-letter-spacing-wider); text-transform: uppercase; border-bottom: 0; width: 28%; }
.rl-coach-cad thead th:first-child { color: var(--rl-color-paper); width: 16%; }
.rl-coach-cad tbody th { font-family: var(--rl-font-data); font-size: var(--rl-font-size-xs); letter-spacing: var(--rl-letter-spacing-wide); text-transform: uppercase; color: var(--rl-color-near-black); border-right: var(--rl-border-width-subtle) solid var(--rl-color-dark-navy); }
.rl-coach-cad td { font-size: var(--rl-font-size-base); }
.rl-coach-cad-off { color: var(--rl-color-steel); }
.rl-coach-cad-on { font-weight: var(--rl-font-weight-semibold); }
.rl-coach-cad-on::before { content: ""; display: inline-block; width: 10px; height: 10px; background: var(--rl-color-offer); margin-right: var(--rl-spacing-xs); }
.rl-coach-cad-note td { border-bottom: var(--rl-border-width-subtle) solid var(--rl-color-dark-navy); padding-top: 0; }

/* ── How it works ────────────────────────────────── */
.rl-coach-steps { list-style: none; margin: 0; padding: 0; counter-reset: rl-step; max-width: 860px; }
.rl-coach-steps li { display: grid; grid-template-columns: 64px 180px 1fr; gap: var(--rl-spacing-lg); padding: var(--rl-spacing-lg) 0; border-top: var(--rl-border-width-subtle) solid var(--rl-color-dark-navy); align-items: baseline; }
.rl-coach-steps li:last-child { border-bottom: var(--rl-border-width-subtle) solid var(--rl-color-dark-navy); }
.rl-coach-steps li::before { counter-increment: rl-step; content: "0" counter(rl-step); font-family: var(--rl-font-data); font-weight: var(--rl-font-weight-bold); font-size: var(--rl-font-size-2xl); color: var(--rl-color-score); }
.rl-coach-steps .rl-coach-label { color: var(--rl-color-opinion); }
.rl-coach-steps h3 { margin: 0 0 var(--rl-spacing-2xs); font-family: var(--rl-font-editorial); font-size: var(--rl-font-size-xl); line-height: var(--rl-line-height-tight); }
.rl-coach-steps p { margin: 0; font-family: var(--rl-font-editorial); }

/* ── Levels: picker + ledger ─────────────────────── */
.rl-coach-picker { display: grid; grid-template-columns: repeat(3, 1fr); gap: var(--rl-spacing-lg); margin-bottom: var(--rl-spacing-lg); }
.rl-coach-picker[hidden], .rl-coach-picker-out[hidden] { display: none; }
.rl-coach-picker fieldset { border: var(--rl-border-width-subtle) solid var(--rl-color-graphite); padding: var(--rl-spacing-md); margin: 0; min-width: 0; }
.rl-coach-picker legend { font-family: var(--rl-font-data); font-size: var(--rl-font-size-2xs); letter-spacing: var(--rl-letter-spacing-wider); text-transform: uppercase; color: var(--rl-color-tier-gold); padding: 0 var(--rl-spacing-xs); }
.rl-coach-picker p { margin: 0 0 var(--rl-spacing-sm); font-family: var(--rl-font-editorial); font-weight: var(--rl-font-weight-semibold); font-size: var(--rl-font-size-base); }
.rl-coach-picker label { display: flex; gap: var(--rl-spacing-sm); align-items: center; font-family: var(--rl-font-data); font-size: var(--rl-font-size-xs); padding: var(--rl-spacing-2xs) 0; cursor: pointer; color: var(--rl-color-silver); }
.rl-coach-picker input { appearance: none; -webkit-appearance: none; width: 16px; height: 16px; border: var(--rl-border-width-subtle) solid var(--rl-color-silver); margin: 0; flex: none; background: transparent; cursor: pointer; }
.rl-coach-picker input:checked { background: var(--rl-color-tier-gold); border-color: var(--rl-color-tier-gold); }
.rl-coach-picker input:checked + span { color: var(--rl-color-paper); font-weight: var(--rl-font-weight-bold); }
.rl-coach-picker input:focus-visible { outline: var(--rl-border-width-subtle) solid var(--rl-color-tier-gold); outline-offset: 2px; }
.rl-coach-picker-out { font-family: var(--rl-font-data); font-size: var(--rl-font-size-sm); letter-spacing: var(--rl-letter-spacing-wide); text-transform: uppercase; color: var(--rl-color-tier-gold); margin: 0 0 var(--rl-spacing-xl); min-height: 1.5em; }
.rl-coach-tabs { display: none; }
.rl-coach-ledger { width: 100%; border-collapse: collapse; background: var(--rl-color-paper); color: var(--rl-color-dark-navy); border: var(--rl-border-width-heavy) solid var(--rl-color-graphite); table-layout: fixed; font-family: var(--rl-font-editorial); }
.rl-coach-ledger th, .rl-coach-ledger td { padding: var(--rl-spacing-sm) var(--rl-spacing-md); border-bottom: 1px solid var(--rl-color-silver); text-align: left; vertical-align: top; }
.rl-coach-ledger col.rl-coach-c0 { width: 31%; }
.rl-coach-ledger thead th { background: var(--rl-color-graphite); color: var(--rl-color-paper); padding: var(--rl-spacing-lg) var(--rl-spacing-md); border-bottom: 0; border-left: 1px solid var(--rl-color-graphite); transition: background var(--rl-transition-hover); }
.rl-coach-ledger thead th:first-child { border-left: 0; vertical-align: bottom; font-family: var(--rl-font-data); font-size: var(--rl-font-size-xs); letter-spacing: var(--rl-letter-spacing-wider); text-transform: uppercase; color: var(--rl-color-steel); }
.rl-coach-tname { display: flex; justify-content: space-between; align-items: center; font-family: var(--rl-font-data); font-size: var(--rl-font-size-sm); letter-spacing: var(--rl-letter-spacing-ultra-wide); text-transform: uppercase; font-weight: var(--rl-font-weight-bold); color: var(--rl-color-tier-gold); }
.rl-coach-tpick { visibility: hidden; font-size: var(--rl-font-size-2xs); letter-spacing: var(--rl-letter-spacing-wide); background: var(--rl-color-tier-gold); color: var(--rl-color-near-black); padding: 2px 6px; }
.rl-coach-tprice { display: block; font-family: var(--rl-font-data); font-weight: var(--rl-font-weight-bold); font-size: clamp(40px, 4.6vw, 60px); line-height: 1; letter-spacing: -1px; margin: var(--rl-spacing-sm) 0 var(--rl-spacing-2xs); color: var(--rl-color-paper); }
.rl-coach-tper { font-family: var(--rl-font-data); font-size: var(--rl-font-size-2xs); letter-spacing: var(--rl-letter-spacing-wider); text-transform: uppercase; color: var(--rl-color-steel); font-weight: var(--rl-font-weight-regular); }
.rl-coach-tblurb { display: block; font-family: var(--rl-font-editorial); font-style: italic; font-weight: var(--rl-font-weight-regular); font-size: var(--rl-font-size-base); color: var(--rl-color-silver); margin-top: var(--rl-spacing-md); line-height: var(--rl-line-height-normal); }
.rl-coach-ledger thead th.rl-coach-is-pick { background: var(--rl-color-offer); }
.rl-coach-ledger thead th.rl-coach-is-pick .rl-coach-tpick { visibility: visible; }
.rl-coach-ledger thead th.rl-coach-is-pick .rl-coach-tname,
.rl-coach-ledger thead th.rl-coach-is-pick .rl-coach-tper,
.rl-coach-ledger thead th.rl-coach-is-pick .rl-coach-tblurb { color: var(--rl-color-white); }
.rl-coach-ledger tbody th { font-weight: var(--rl-font-weight-regular); font-size: var(--rl-font-size-base); }
.rl-coach-ledger tbody td { border-left: 1px solid var(--rl-color-silver); text-align: center; }
.rl-coach-ledger .rl-coach-grp th { font-family: var(--rl-font-data); font-size: var(--rl-font-size-2xs); letter-spacing: var(--rl-letter-spacing-wider); text-transform: uppercase; background: var(--rl-color-well); color: var(--rl-color-graphite); font-weight: var(--rl-font-weight-bold); }
.rl-coach-y, .rl-coach-n { display: inline-block; width: 14px; height: 14px; vertical-align: middle; }
.rl-coach-y { background: var(--rl-color-offer); }
.rl-coach-n { height: 2px; background: var(--rl-color-silver); }
.rl-coach-ledger tfoot td { border-left: 1px solid var(--rl-color-silver); padding: var(--rl-spacing-md); background: var(--rl-color-well); }
.rl-coach-ledger tfoot td:first-child { border-left: 0; }
.rl-coach-ledger tfoot .rl-coach-btn { display: block; text-align: center; padding: var(--rl-spacing-sm) var(--rl-spacing-xs); font-size: var(--rl-font-size-xs); }
.rl-coach-tier-setup-fee { display: grid; grid-template-columns: 1fr 1fr; gap: var(--rl-spacing-xl); margin-top: var(--rl-spacing-lg); color: var(--rl-color-silver); }
.rl-coach-tier-setup-fee p { margin: 0; }
.rl-coach-tier-setup-fee strong { color: var(--rl-color-paper); }

/* ── FAQ ─────────────────────────────────────────── */
.rl-coach-faq { background: var(--rl-color-paper); border-top: var(--rl-border-width-standard) solid var(--rl-color-dark-navy); }
.rl-coach-faq-list { max-width: 860px; }
.rl-coach-faq-item { border-top: var(--rl-border-width-subtle) solid var(--rl-color-dark-navy); }
.rl-coach-faq-item:last-child { border-bottom: var(--rl-border-width-subtle) solid var(--rl-color-dark-navy); }
.rl-coach-faq-item summary { list-style: none; cursor: pointer; display: grid; grid-template-columns: 56px 1fr 24px; gap: var(--rl-spacing-sm); padding: var(--rl-spacing-md) 0; font-family: var(--rl-font-editorial); font-size: var(--rl-font-size-lg); font-weight: var(--rl-font-weight-semibold); align-items: baseline; }
.rl-coach-faq-item summary::-webkit-details-marker { display: none; }
.rl-coach-faq-item summary .rl-coach-label { color: var(--rl-color-score); }
.rl-coach-faq-item summary::after { content: "+"; font-family: var(--rl-font-data); font-size: var(--rl-font-size-xl); color: var(--rl-color-score); }
.rl-coach-faq-item[open] summary::after { content: "\\2212"; }
.rl-coach-faq-item summary:focus-visible { outline: var(--rl-border-width-subtle) solid var(--rl-color-offer); outline-offset: 2px; }
.rl-coach-faq-item p { margin: 0 0 var(--rl-spacing-lg) 68px; max-width: 68ch; font-family: var(--rl-font-editorial); line-height: var(--rl-line-height-relaxed); }

/* ── Application close ───────────────────────────── */
.rl-coach-close { background: var(--rl-color-offer); color: var(--rl-color-white); }
.rl-coach-close-grid { display: grid; grid-template-columns: 1fr 1fr; gap: var(--rl-spacing-3xl); align-items: center; }
.rl-coach-close .rl-coach-label { color: var(--rl-color-white); }
.rl-coach-close h2 { font-family: var(--rl-font-editorial); font-size: clamp(32px, 4vw, 52px); line-height: var(--rl-line-height-tight); margin: var(--rl-spacing-sm) 0 var(--rl-spacing-md); color: var(--rl-color-white); }
.rl-coach-final-hook { margin: 0 0 var(--rl-spacing-lg); font-family: var(--rl-font-editorial); font-size: var(--rl-font-size-lg); }
.rl-coach-final-contact { margin-top: var(--rl-spacing-md); }
.rl-coach-final-contact a { color: var(--rl-color-white); }
.rl-coach-close-img { margin: 0; border: var(--rl-border-width-standard) solid var(--rl-color-near-black); }
.rl-coach-close-img img { display: block; width: 100%; height: auto; }

.rl-coach-close-copy { max-width: 68ch; }

/* ── Mobile sticky CTA ───────────────────────────── */
.rl-coach-sticky-cta {
  display: none;
}
@media (max-width: 768px) {
  .rl-coach-sticky-cta {
    display: block;
    position: fixed;
    bottom: 0;
    left: 0;
    right: 0;
    z-index: 999;
    background: var(--rl-color-near-black);
    padding: var(--rl-spacing-sm) var(--rl-spacing-md);
    text-align: center;
    border-top: 3px solid var(--rl-color-orange);
    visibility: hidden;
    pointer-events: none;
  }
  .rl-coach-sticky-cta.rl-coach-sticky-visible {
    visibility: visible;
    pointer-events: auto;
  }
  .rl-coach-sticky-cta a {
    display: block;
    color: var(--rl-color-silver);
    font-family: var(--rl-font-data);
    font-size: var(--rl-font-size-xs);
    font-weight: var(--rl-font-weight-bold);
    text-transform: uppercase;
    letter-spacing: var(--rl-letter-spacing-wider);
    text-decoration: none;
    padding: var(--rl-spacing-2xs) 0;
  }
}

/* ── Reduced motion: the photo stays, no swap ────── */
@media (prefers-reduced-motion: reduce) {
  .rl-coach-id-toon { animation: none; opacity: 0; }
  .rl-coach-btn, .rl-coach-ledger thead th { transition: none; }
}

/* ── Responsive ──────────────────────────────────── */
@media (max-width: 960px) {
  .rl-coach-hero-grid { grid-template-columns: 1fr; }
  .rl-coach-id { max-width: 420px; }
  .rl-coach-picker { grid-template-columns: 1fr; }
  .rl-coach-close-grid { grid-template-columns: 1fr; }
}
@media (max-width: 768px) {
  .rl-coach-inner { padding: 0 var(--rl-spacing-md); }
  .rl-coach-band { padding: var(--rl-spacing-3xl) 0; }
  .rl-coach-hero { padding: var(--rl-spacing-lg) 0 var(--rl-spacing-2xl); }
  .rl-coach-hero-file { gap: var(--rl-spacing-sm); margin-bottom: var(--rl-spacing-md); }
  .rl-coach-hero-file span { font-size: var(--rl-font-size-2xs); }
  .rl-coach-hero h1 { font-size: 33px; margin-bottom: var(--rl-spacing-md); }
  .rl-coach-tagline { font-size: var(--rl-font-size-base); margin-bottom: var(--rl-spacing-lg); }
  .rl-coach-hero-actions .rl-coach-btn { width: 100%; text-align: center; }
  .rl-coach-id { transform: none; }
  .rl-coach-sec-head { grid-template-columns: 1fr; gap: var(--rl-spacing-sm); margin-bottom: var(--rl-spacing-xl); }
  .rl-coach-sec-num { justify-self: start; }
  .rl-coach-fit-grid { grid-template-columns: 1fr; gap: var(--rl-spacing-xl); }
  .rl-coach-fit li { font-size: var(--rl-font-size-md); }
  .rl-coach-get { grid-template-columns: 1fr; }
  .rl-coach-get li:first-child h3 { font-size: var(--rl-font-size-2xl); }
  .rl-coach-cad, .rl-coach-cad tbody, .rl-coach-cad tr, .rl-coach-cad th, .rl-coach-cad td { display: block; width: 100%; }
  .rl-coach-cad thead { display: none; }
  .rl-coach-cad tr { border-bottom: var(--rl-border-width-subtle) solid var(--rl-color-dark-navy); padding: var(--rl-spacing-sm) 0; }
  .rl-coach-cad tbody th { border-right: 0; border-bottom: 0; padding: var(--rl-spacing-xs) var(--rl-spacing-md); color: var(--rl-color-offer); }
  .rl-coach-cad td { border-bottom: 0; padding: var(--rl-spacing-2xs) var(--rl-spacing-md); display: grid; grid-template-columns: 44px 1fr; gap: var(--rl-spacing-xs); }
  .rl-coach-cad td::before, .rl-coach-cad .rl-coach-cad-on::before { content: attr(data-t); display: block; width: auto; height: auto; background: none; margin: 0; font-family: var(--rl-font-data); font-size: var(--rl-font-size-2xs); letter-spacing: var(--rl-letter-spacing-wide); color: var(--rl-color-graphite); font-weight: var(--rl-font-weight-bold); padding-top: 4px; }
  .rl-coach-cad .rl-coach-cad-note td { display: block; }
  .rl-coach-cad .rl-coach-cad-note td::before { content: none; }
  .rl-coach-steps li { grid-template-columns: 44px 1fr; gap: var(--rl-spacing-2xs) var(--rl-spacing-sm); }
  .rl-coach-steps li::before { grid-row: span 2; font-size: var(--rl-font-size-xl); }
  .rl-coach-tabs { display: grid; grid-template-columns: repeat(3, 1fr); }
  .rl-coach-tabs button { font-family: var(--rl-font-data); font-size: var(--rl-font-size-sm); letter-spacing: var(--rl-letter-spacing-wider); text-transform: uppercase; font-weight: var(--rl-font-weight-bold); padding: var(--rl-spacing-sm) 0; background: var(--rl-color-graphite); color: var(--rl-color-silver); border: 0; border-bottom: var(--rl-border-width-heavy) solid var(--rl-color-near-black); cursor: pointer; }
  .rl-coach-tabs button[aria-selected="true"] { background: var(--rl-color-near-black); color: var(--rl-color-tier-gold); }
  .rl-coach-ledger, .rl-coach-ledger tbody { display: block; border-top: 0; }
  .rl-coach-ledger colgroup { display: none; }
  .rl-coach-ledger tbody tr { display: grid; grid-template-columns: 1fr 34%; }
  .rl-coach-ledger tbody tr.rl-coach-grp { grid-template-columns: 1fr; }
  .rl-coach-ledger tbody tr > * { display: block; }
  .rl-coach-ledger thead, .rl-coach-ledger thead tr, .rl-coach-ledger thead th, .rl-coach-ledger tfoot, .rl-coach-ledger tfoot tr, .rl-coach-ledger tfoot td { display: block; width: 100%; }
  .rl-coach-ledger tbody td { font-size: var(--rl-font-size-sm); }
  .rl-coach-ledger[data-show="min"] .rl-coach-t-mid, .rl-coach-ledger[data-show="min"] .rl-coach-t-max,
  .rl-coach-ledger[data-show="mid"] .rl-coach-t-min, .rl-coach-ledger[data-show="mid"] .rl-coach-t-max,
  .rl-coach-ledger[data-show="max"] .rl-coach-t-min, .rl-coach-ledger[data-show="max"] .rl-coach-t-mid { display: none; }
  .rl-coach-ledger thead th:first-child { display: none; }
  .rl-coach-ledger thead th { border-left: 0; }
  .rl-coach-ledger tbody th { font-size: var(--rl-font-size-sm); }
  .rl-coach-ledger tfoot td:first-child { display: none; }
  .rl-coach-ledger tfoot td { border-left: 0; }
  .rl-coach-ledger tfoot .rl-coach-btn { padding: var(--rl-spacing-md); font-size: var(--rl-font-size-sm); }
  .rl-coach-tier-setup-fee { grid-template-columns: 1fr; gap: var(--rl-spacing-sm); }
  .rl-coach-faq-item summary { grid-template-columns: 40px 1fr 20px; font-size: var(--rl-font-size-md); }
  .rl-coach-faq-item p { margin-left: 52px; }
  .rl-coach-close .rl-coach-btn { width: 100%; text-align: center; }
  /* clears the fixed sticky CTA */
  .rl-mega-footer { padding-bottom: 72px; }
}
</style>'''


def build_coaching_js() -> str:
    """Interactive JS: tier tabs, picker, FAQ + scroll-depth + CTA events, sticky CTA."""
    tier_labels = {key: f"Marked: {name}, {price} every 4 weeks." for key, name, price in TIERS}
    labels_js = _safe_json_for_script(tier_labels, separators=(",", ":"))
    return '''<script>
/* Levels: phone tabs + three-question picker. The picker is rendered
   hidden and only shown here, so without JS the ledger stands alone. */
(function() {
  var ledger = document.getElementById('rl-coach-ledger');
  if (!ledger) return;
  var tabs = document.querySelectorAll('.rl-coach-tabs button');
  function show(tier) {
    ledger.setAttribute('data-show', tier);
    tabs.forEach(function(b) { b.setAttribute('aria-selected', b.getAttribute('data-tab') === tier ? 'true' : 'false'); });
  }
  tabs.forEach(function(b) { b.addEventListener('click', function() { show(b.getAttribute('data-tab')); }); });

  var form = document.getElementById('rl-coach-picker');
  var out = document.getElementById('rl-coach-picker-out');
  if (!form || !out) return;
  var names = { 1: 'min', 2: 'mid', 3: 'max' };
  var labels = ''' + labels_js + ''';
  var current = null;
  form.addEventListener('change', function(e) {
    if (e.target && e.target.name && typeof gtag === 'function') gtag('event', 'coaching_fitcheck_answer', { question: e.target.name.slice(-1), answer: e.target.value });
    var v = [1, 2, 3].map(function(q) { var c = form.querySelector('input[name=rl-coach-q' + q + ']:checked'); return c ? +c.value : 0; });
    if (v.indexOf(0) !== -1) return;
    var tier = names[Math.round((v[0] + v[1] + v[2]) / 3)];
    out.textContent = labels[tier];
    ledger.querySelectorAll('thead th[data-tier]').forEach(function(th) { th.classList.toggle('rl-coach-is-pick', th.getAttribute('data-tier') === tier); });
    show(tier);
    if (tier !== current && typeof gtag === 'function') gtag('event', 'coaching_fitcheck_result', { tier: tier });
    current = tier;
  });
  form.hidden = false;
  out.hidden = false;
})();

/* FAQ: log opens */
document.querySelectorAll('.rl-coach-faq-item').forEach(function(d) {
  d.addEventListener('toggle', function() {
    if (d.open && typeof gtag === 'function') gtag('event', 'coaching_faq_open', { question: d.querySelector('.rl-coach-faq-q').textContent.trim().slice(0, 60) });
  });
});

/* Scroll depth tracking */
(function() {
  if (typeof gtag !== 'function' || !('IntersectionObserver' in window)) return;
  var sections = [
    { id: 'hero', label: '0_hero' },
    { id: 'fit', label: '10_fit' },
    { id: 'terms', label: '20_terms' },
    { id: 'week', label: '35_week' },
    { id: 'how-it-works', label: '45_how' },
    { id: 'tiers', label: '60_tiers' },
    { id: 'faq', label: '85_faq' },
    { id: 'final-cta', label: '100_final_cta' }
  ];
  sections.forEach(function(s) {
    var el = document.getElementById(s.id);
    if (!el) return;
    new IntersectionObserver(function(entries, obs) {
      if (entries[0].isIntersecting) {
        gtag('event', 'coaching_scroll_depth', { section: s.label });
        obs.unobserve(el);
      }
    }, { threshold: 0.3 }).observe(el);
  });
})();

/* CTA click attribution */
document.querySelectorAll('[data-cta]').forEach(function(el) {
  el.addEventListener('click', function() {
    if (typeof gtag === 'function') gtag('event', 'coaching_cta_click', { cta_name: el.getAttribute('data-cta') });
  });
});

/* Page view event */
if (typeof gtag === 'function') gtag('event', 'coaching_page_view');

/* Mobile sticky CTA: show after scrolling past hero */
(function() {
  var sticky = document.querySelector('.rl-coach-sticky-cta');
  var hero = document.getElementById('hero');
  if (!sticky || !hero || !('IntersectionObserver' in window)) return;
  new IntersectionObserver(function(entries) {
    if (entries[0].isIntersecting) {
      sticky.classList.remove('rl-coach-sticky-visible');
    } else {
      sticky.classList.add('rl-coach-sticky-visible');
    }
  }, { threshold: 0 }).observe(hero);
})();
''' + '\n</script>'


# ── JSON-LD ───────────────────────────────────────────────────


def build_jsonld() -> str:
    webpage = {
        "@context": "https://schema.org",
        "@type": "WebPage",
        "name": "Coaching | Roadie Labs",
        "description": f"Road cycling coaching from one coach, {load_race_count()} courses on file. A human who reads your training data, adjusts the plan when your life changes, and tells you the truth.",
        "url": f"{SITE_BASE_URL}/coaching/",
        "isPartOf": {
            "@type": "WebSite",
            "name": "Roadie Labs",
            "url": SITE_BASE_URL,
        },
    }
    service = {
        "@context": "https://schema.org",
        "@type": "Service",
        "name": "Road Cycling Coaching",
        "provider": {
            "@type": "Organization",
            "name": "Roadie Labs",
            "url": SITE_BASE_URL,
        },
        "description": "Road cycling coaching: three tiers of involvement from weekly review to daily high-touch support. One coach reads every file — built around your race, your schedule, and your training history.",
    }
    wp_tag = f'<script type="application/ld+json">{_safe_json_for_script(webpage, separators=(",", ":"))}</script>'
    svc_tag = f'<script type="application/ld+json">{_safe_json_for_script(service, separators=(",", ":"))}</script>'
    return f'{wp_tag}\n  {svc_tag}'


# ── Assemble page ─────────────────────────────────────────────


def generate_coaching_page(external_assets: dict = None) -> str:
    canonical_url = f"{SITE_BASE_URL}/coaching/"

    sections = "\n\n  ".join((
        build_nav(),
        build_hero(),
        build_honest_check(),
        build_terms(),
        build_week(),
        build_how_it_works(),
        build_tiers(),
        build_faq(),
        build_application_close(),
        build_footer(),
        build_mobile_sticky_cta(),
    ))
    coaching_css = build_coaching_css()
    coaching_js = build_coaching_js()
    jsonld = build_jsonld()

    if external_assets:
        page_css = external_assets['css_tag']
        inline_js = external_assets['js_tag']
    else:
        page_css = get_page_css()
        inline_js = build_inline_js()

    meta_desc = f"Road cycling coaching built on {load_race_count()} analyzed courses. A human coach, a plan that adjusts weekly, and honest feedback. From $199 every 4 weeks."

    og_tags = f'''<meta property="og:title" content="Coaching | Roadie Labs">
  <meta property="og:description" content="Coaching built around your race, your hours, and your life. From the coach behind {load_race_count()} course profiles.">
  <meta property="og:type" content="website">
  <meta property="og:url" content="{esc(canonical_url)}">
  <meta property="og:image" content="{SITE_BASE_URL}/og/homepage.jpg">
  <meta property="og:image:width" content="1200">
  <meta property="og:image:height" content="630">
  <meta property="og:site_name" content="Roadie Labs">
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:title" content="Coaching | Roadie Labs">
  <meta name="twitter:description" content="Coaching built around your race, your hours, and your life. From the coach behind {load_race_count()} course profiles.">
  <meta name="twitter:image" content="{SITE_BASE_URL}/og/homepage.jpg">'''

    preload = get_preload_hints()
    photo_src = _img("photo")[0]

    return apply_live_head_patches(f'''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Road Cycling Coaching | Roadie Labs</title>
  <meta name="description" content="{esc(meta_desc)}">
  <meta name="robots" content="index, follow">
  <link rel="canonical" href="{esc(canonical_url)}">
  <link rel="preconnect" href="https://www.googletagmanager.com" crossorigin>
  <link rel="preload" as="image" href="{photo_src}">
  {preload}
  {og_tags}
  {jsonld}
  {page_css}
  {coaching_css}
  {get_ga4_head_snippet()}
  {get_ab_head_snippet()}
</head>
<body>

<a href="#hero" class="rl-coach-skip-link">Skip to content</a>
<div class="rl-neo-brutalist-page">
  {sections}
</div>

{inline_js}
{coaching_js}

''' + '<script>' + get_site_header_js() + '</script>' + f'''

{get_consent_banner_html()}
</body>
</html>''')


def write_coaching_images(output_dir: Path) -> Path:
    """Copy the page's images to output_dir/coaching-img/. Raises if one is
    missing: the page never ships with a stand-in picture."""
    dest = output_dir / IMG_OUTPUT_SUBDIR
    dest.mkdir(parents=True, exist_ok=True)
    for name, _w, _h in IMAGES.values():
        src = IMG_SRC_DIR / name
        if not src.is_file():
            raise FileNotFoundError(f"coaching image missing: {src}")
        shutil.copy2(src, dest / name)
    return dest


def main():
    parser = argparse.ArgumentParser(description="Generate Roadie Labs coaching page")
    parser.add_argument("--output-dir", default=str(OUTPUT_DIR), help="Output directory")
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    assets = write_shared_assets(output_dir)
    write_coaching_images(output_dir)

    html_content = generate_coaching_page(external_assets=assets)
    output_file = output_dir / "coaching.html"
    output_file.write_text(html_content, encoding="utf-8")
    print(f"Generated {output_file} ({len(html_content):,} bytes)")


if __name__ == "__main__":
    main()
