#!/usr/bin/env python3
"""
Generate the Roadie Labs Coaching landing page — "The Dossier".

Clinical prestige register: terms-of-work framing, deadpan verdict voice,
strict monochrome, luxury through precision (whitespace + hairlines) rather
than cards/shadows/borders. Full-bleed band layout: section backgrounds span
the viewport, content sits in a 1200px measure, prose capped at a readable
width.

Rebuilt 2026-07-18 from the original "band sequence" layout (hero → problem
→ deliverables → how-it-works → tiers → testimonials → honest-check → faq →
final-cta) into the Dossier structure (hero → terms → tiers → fit → faq → final-cta). Owner-approved copy and structure — see the "Direction
C — The Dossier" mock this rebuild matches.

Uses brand tokens exclusively — zero hardcoded hex, no border-radius, no
box-shadow, no bounce easing, no entrance animations — the Dossier is a still document.

Usage:
    python generate_coaching.py
    python generate_coaching.py --output-dir ./output
"""

import argparse
import html
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

OUTPUT_DIR = Path(__file__).parent / "output"
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# ── Constants ─────────────────────────────────────────────────

QUESTIONNAIRE_URL = f"{SITE_BASE_URL}/coaching/apply/"

# Curated for the coaching page: concrete result, concrete constraint,
# concrete rider. The full set stays on /about/. These are Gravel God
# athletes (Roadie Labs has no finishers yet) — the provenance line below
# the cards says so.

def esc(text) -> str:
    """HTML-escape a string."""
    return html.escape(str(text)) if text else ""


def _sec_head(num: str, title: str) -> str:
    return (
        f'<div class="rl-coach-sec-head">'
        f'<span class="rl-coach-sec-num">{num}</span>'
        f'<h2 class="rl-coach-sec-title">{title}</h2>'
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


# SANCTIONED EXCEPTION to the anti-defensive-messaging rule (see
# .claude/skills/brand-and-trust/SKILL.md, "Never defensive messaging" —
# phrases naming what something ISN'T are normally banned because they
# plant doubt nobody had). The sub-line below ("Not an AI, not a
# dashboard, not a coach who reads you like a spreadsheet") is an
# explicit, owner-approved exception. Matti sanctioned this specific line
# 2026-07-18 as an aspirational "corner" frame — it names what you're
# getting, not a defensive rebuttal to an objection nobody raised — the
# same precedent class this skill file already reserves for that
# distinction. This is the /coaching/ hero and is itself the
# precedent-setting instance (no prior race-page coaching-footnote
# precedent for this pattern was found in this repo).
def build_hero() -> str:
    return f'''<section class="rl-coach-band rl-coach-hero" id="hero">
    <div class="rl-coach-inner">
      <h1>You could be better than you think. That is not encouragement &mdash; it&#39;s an observation about people who train alone.</h1>
      <p class="rl-coach-tagline">The fix is a human in your corner. Not an AI, not a dashboard, not a coach who reads you like a spreadsheet. The terms are below.</p>
      <a href="{QUESTIONNAIRE_URL}" class="rl-coach-hero-cta" data-cta="hero_apply">GET ME IN YOUR CORNER &rarr;</a>
    </div>
  </section>'''


def build_terms() -> str:
    clauses = [
        (
            "01",
            "Every file, read by a person",
            "Software flags a number. I notice the interval you bailed on and ask why.",
        ),
        (
            "02",
            "The patterns you can&#39;t see",
            "You can know everything about training and still train wrong. Knowledge isn&#39;t the limiter &mdash; application is. Every athlete is their own worst blindspot: too fresh to rest, too stubborn to taper, too close to their own data to see the shape of it. Seeing it is the job.",
        ),
        (
            "03",
            "The plan moves when your life does",
            "Sick kid, work trip, tender knee &mdash; the week adjusts that week, not after three missed targets teach an algorithm what a person would have seen on Tuesday.",
        ),
        (
            "04",
            "The truth, on schedule",
            "&ldquo;You&#39;re sandbagging&rdquo; and &ldquo;take the rest week&rdquo; are both part of the service.",
        ),
        (
            "05",
            "Involvement is the only variable",
            "Same coach, same standards. The difference is how often I&#39;m looking.",
        ),
    ]
    rows = "\n        ".join(
        f'<div class="rl-coach-term">'
        f'<div class="rl-coach-term-num">{num}</div>'
        f'<div class="rl-coach-term-body"><h3>{title}</h3><p>{body}</p></div>'
        f'</div>'
        for num, title, body in clauses
    )
    return f'''<section class="rl-coach-band rl-coach-terms" id="terms">
    <div class="rl-coach-inner">
      <div class="rl-coach-terms-list">
        {rows}
      </div>
    </div>
  </section>'''


def build_tiers() -> str:
    return f'''<section class="rl-coach-band rl-coach-tiers-section" id="tiers">
    <div class="rl-coach-inner">
      <div class="rl-coach-tiers">
        <div class="rl-coach-tier-col">
          <div class="rl-coach-tier-name">Min</div>
          <div class="rl-coach-tier-price">$199<span class="rl-coach-tier-interval">/ 4 WEEKS</span></div>
          <p class="rl-coach-tier-desc">The plan, plus a weekly check of your training. For athletes who execute on their own and want the thinking done right.</p>
          <ul class="rl-coach-tier-list">
            <li>Weekly training review</li>
            <li>File analysis</li>
            <li>Quarterly strategy calls</li>
            <li>Structured workouts for your trainer or head unit</li>
            <li>Race-day nutrition plan</li>
            <li>Custom training guide</li>
          </ul>
          <a href="{QUESTIONNAIRE_URL}?tier=min" class="rl-coach-tier-cta" data-cta="tier_min">GET STARTED</a>
        </div>
        <div class="rl-coach-tier-col">
          <div class="rl-coach-tier-name">Mid</div>
          <div class="rl-coach-tier-price">$299<span class="rl-coach-tier-interval">/ 4 WEEKS</span></div>
          <p class="rl-coach-tier-desc">The plan, watched. Someone reads the data between sessions and adjusts the same week life changes. Most athletes belong here.</p>
          <ul class="rl-coach-tier-list">
            <li>Everything in Min</li>
            <li>Detailed power-file analysis</li>
            <li>Every-4-week strategy calls</li>
            <li>Weekly plan adjustments</li>
            <li>Direct message access</li>
            <li>Blindspot detection</li>
          </ul>
          <a href="{QUESTIONNAIRE_URL}?tier=mid" class="rl-coach-tier-cta" data-cta="tier_mid">GET STARTED</a>
        </div>
        <div class="rl-coach-tier-col">
          <div class="rl-coach-tier-name">Max</div>
          <div class="rl-coach-tier-price">$1,200<span class="rl-coach-tier-interval">/ 4 WEEKS</span></div>
          <p class="rl-coach-tier-desc">Everything, daily. For the race where you want nothing left to chance.</p>
          <ul class="rl-coach-tier-list">
            <li>Everything in Mid</li>
            <li>Daily file review</li>
            <li>On-demand calls</li>
            <li>Race-week strategy</li>
            <li>Multi-race season planning</li>
            <li>Priority response</li>
          </ul>
          <a href="{QUESTIONNAIRE_URL}?tier=max" class="rl-coach-tier-cta" data-cta="tier_max">GET STARTED</a>
        </div>
      </div>
      <p class="rl-coach-tier-disclaimer">Coaching doesn&#39;t fix skipped workouts or feedback you don&#39;t act on. If this isn&#39;t a fit, I&#39;ll tell you within 24 hours.</p>
      <p class="rl-coach-tier-setup-fee">All tiers include a one-time $99 setup fee: intake analysis, training-history review, and your first plan build.</p>
    </div>
  </section>'''



def build_honest_check() -> str:
    return f'''<section class="rl-coach-band" id="fit">
    <div class="rl-coach-inner">
      {_sec_head("06", "A fit, or not")}
      <div class="rl-coach-audience">
        <div class="rl-coach-audience-col">
          <h3 class="rl-coach-audience-heading rl-coach-audience-heading--yes">Coaching is for you if:</h3>
          <ul class="rl-coach-audience-list rl-coach-list--yes">
            <li>You&#39;ll do the training when the thinking is done right</li>
            <li>You have a race and a reason</li>
            <li>You&#39;re ready to be honest about your habits</li>
            <li>You want a plan smarter than the one you&#39;d build alone</li>
          </ul>
        </div>
        <div class="rl-coach-audience-col">
          <h3 class="rl-coach-audience-heading rl-coach-audience-heading--no">It isn&#39;t:</h3>
          <ul class="rl-coach-audience-list rl-coach-list--no">
            <li>Accountability texts when you skip a Tuesday</li>
            <li>Validation dressed up as feedback</li>
            <li>A rescue for a race that&#39;s next week</li>
            <li>A substitute for doing the work</li>
          </ul>
        </div>
      </div>
    </div>
  </section>'''


def build_faq() -> str:
    faqs = [
        (
            "What&#39;s the difference between a plan and coaching?",
            "A plan is a document. Coaching is the relationship that changes the document when your life changes.",
        ),
        (
            "How often will I hear from you?",
            "Weekly at minimum, more near your race. You can message me anytime.",
        ),
        (
            "Do I need a power meter?",
            "Not required &mdash; every workout carries effort-based targets you can train by feel. A power meter removes the guesswork; heart rate sits in between.",
        ),
        (
            "What if I miss workouts?",
            "Life happens. I adjust. The plan serves you, not the other way around.",
        ),
        (
            "How do I know if coaching is working?",
            "We set baselines at intake and measure against them. You&#39;ll know.",
        ),
        (
            "What&#39;s the time commitment?",
            "The training you&#39;re already doing, but smarter. I&#39;m not adding hours &mdash; I&#39;m making the ones you have count.",
        ),
        (
            "What&#39;s the $99 setup fee?",
            "It covers intake analysis, training-history review, and building your first plan. It&#39;s a one-time charge on top of your first billing cycle.",
        ),
        (
            "Can I cancel anytime?",
            "Yes. No contracts, no cancellation fees. Your coaching access continues through the end of your current 4-week cycle.",
        ),
    ]

    items = []
    for idx, (q, a) in enumerate(faqs):
        ans_id = f'rl-coach-faq-ans-{idx}'
        items.append(
            f'<div class="rl-coach-faq-item">'
            f'<div class="rl-coach-faq-q" role="button" tabindex="0" aria-expanded="false" aria-controls="{ans_id}">'
            f'{q}'
            f'<span class="rl-coach-faq-toggle" aria-hidden="true">+</span>'
            f'</div>'
            f'<div class="rl-coach-faq-a" id="{ans_id}" role="region"><p>{a}</p></div>'
            f'</div>'
        )
    inner = "\n      ".join(items)
    return f'''<section class="rl-coach-band" id="faq">
    <div class="rl-coach-inner">
      {_sec_head("07", "FAQ")}
      <div class="rl-coach-faq-list">
      {inner}
      </div>
    </div>
  </section>'''


def build_application_close() -> str:
    return f'''<section class="rl-coach-band rl-coach-band--dark" id="final-cta">
    <div class="rl-coach-inner">
      <div class="rl-coach-final-cta">
        <p class="rl-coach-final-kicker">APPLICATION</p>
        <p class="rl-coach-final-hook">Ten minutes of honest answers. I read every one myself. You&#39;ll hear from me within 48 hours &mdash; including if I don&#39;t think coaching is what you need.</p>
        <a href="{QUESTIONNAIRE_URL}" class="rl-coach-final-cta-link" data-cta="final_fill_intake">GET ME IN YOUR CORNER &rarr;</a>
        <p class="rl-coach-final-contact">Questions first? <a href="mailto:coach@roadielabs.com">coach@roadielabs.com</a> &mdash; I answer myself, usually within a day.</p>
      </div>
    </div>
  </section>'''


def build_footer() -> str:
    return get_mega_footer_html()


def build_mobile_sticky_cta() -> str:
    return f'''<div class="rl-coach-sticky-cta">
    <a href="{QUESTIONNAIRE_URL}" data-cta="sticky_cta">GET ME IN YOUR CORNER &rarr;</a>
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

/* ── Bands ───────────────────────────────────────── */
.rl-coach-band {
  padding: var(--rl-spacing-2xl) 0;
}
.rl-coach-band--dark {
  background: var(--rl-color-dark-navy);
}

/* ── Section heads — quiet numeral, serif title ──── */
.rl-coach-sec-head {
  display: flex;
  align-items: baseline;
  gap: var(--rl-spacing-md);
  border-bottom: 1px solid var(--rl-color-silver);
  padding-bottom: var(--rl-spacing-sm);
  margin-bottom: var(--rl-spacing-xl);
}
.rl-coach-sec-num {
  font-family: var(--rl-font-data);
  font-size: var(--rl-font-size-2xs);
  color: var(--rl-color-steel);
  letter-spacing: var(--rl-letter-spacing-wider);
}
.rl-coach-sec-title {
  font-family: var(--rl-font-editorial);
  font-size: var(--rl-font-size-xl);
  font-weight: var(--rl-font-weight-semibold);
  color: var(--rl-color-dark-navy);
  margin: 0;
  line-height: var(--rl-line-height-tight);
}

/* ── Hero — file strip, deadpan headline ─────────── */
.rl-coach-hero {
  padding-top: var(--rl-spacing-2xl);
  padding-bottom: var(--rl-spacing-2xl);
  border-bottom: 1px solid var(--rl-color-dark-navy);
}
.rl-coach-hero h1 {
  font-family: var(--rl-font-editorial);
  font-size: clamp(30px, 4.6vw, 44px);
  font-weight: var(--rl-font-weight-semibold);
  color: var(--rl-color-dark-navy);
  line-height: var(--rl-line-height-tight);
  margin: 0;
  max-width: 24ch;
}
.rl-coach-tagline {
  font-family: var(--rl-font-editorial);
  font-size: var(--rl-font-size-md);
  line-height: var(--rl-line-height-relaxed);
  color: var(--rl-color-steel);
  max-width: 52ch;
  margin: var(--rl-spacing-lg) 0 0 0;
}
.rl-coach-hero-cta {
  display: inline-block;
  text-decoration: none;
  margin-top: var(--rl-spacing-xl);
  border: 1px solid var(--rl-color-dark-navy);
  padding: 15px 30px;
  font-family: var(--rl-font-data);
  font-size: var(--rl-font-size-xs);
  letter-spacing: var(--rl-letter-spacing-wide);
  color: var(--rl-color-dark-navy);
}

/* ── Terms — numbered clauses ─────────────────────── */
.rl-coach-terms {
  padding-bottom: 0;
}
.rl-coach-term {
  display: grid;
  grid-template-columns: 64px 1fr;
  gap: var(--rl-spacing-lg);
  padding: var(--rl-spacing-lg) 0;
  border-bottom: 1px solid var(--rl-color-silver);
}
.rl-coach-term:last-child {
  border-bottom: none;
}
.rl-coach-term-num {
  font-family: var(--rl-font-data);
  font-size: var(--rl-font-size-xs);
  color: var(--rl-color-steel);
  letter-spacing: var(--rl-letter-spacing-wide);
  padding-top: 4px;
}
.rl-coach-term-body h3 {
  font-family: var(--rl-font-editorial);
  font-size: var(--rl-font-size-md);
  font-weight: var(--rl-font-weight-semibold);
  color: var(--rl-color-dark-navy);
  margin: 0 0 var(--rl-spacing-xs) 0;
  line-height: var(--rl-line-height-tight);
}
.rl-coach-term-body p {
  font-family: var(--rl-font-editorial);
  font-size: var(--rl-font-size-sm);
  line-height: var(--rl-line-height-prose);
  color: var(--rl-color-signal-red);
  margin: 0;
  max-width: 60ch;
}

/* ── Tiers — quiet columns, no cards ──────────────── */
.rl-coach-tiers-section {
  padding-top: 0;
}
.rl-coach-tiers {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 0;
  border-top: 1px solid var(--rl-color-dark-navy);
}
.rl-coach-tier-col {
  padding: var(--rl-spacing-xl) var(--rl-spacing-lg);
  border-right: 1px solid var(--rl-color-silver);
}
.rl-coach-tier-col:first-child {
  padding-left: 0;
}
.rl-coach-tier-col:last-child {
  border-right: none;
  padding-right: 0;
}
.rl-coach-tier-name {
  font-family: var(--rl-font-data);
  font-size: var(--rl-font-size-2xs);
  font-weight: var(--rl-font-weight-bold);
  text-transform: uppercase;
  letter-spacing: var(--rl-letter-spacing-wider);
  color: var(--rl-color-steel);
}
.rl-coach-tier-price {
  font-family: var(--rl-font-editorial);
  font-size: var(--rl-font-size-2xl);
  font-weight: var(--rl-font-weight-semibold);
  color: var(--rl-color-dark-navy);
  margin: var(--rl-spacing-sm) 0 0 0;
}
.rl-coach-tier-interval {
  font-family: var(--rl-font-data);
  font-size: var(--rl-font-size-2xs);
  font-weight: var(--rl-font-weight-regular);
  letter-spacing: var(--rl-letter-spacing-normal);
  color: var(--rl-color-steel);
  margin-left: var(--rl-spacing-2xs);
}
.rl-coach-tier-desc {
  font-family: var(--rl-font-editorial);
  font-size: var(--rl-font-size-sm);
  line-height: var(--rl-line-height-relaxed);
  color: var(--rl-color-signal-red);
  margin: var(--rl-spacing-md) 0 var(--rl-spacing-lg) 0;
}
.rl-coach-tier-list {
  list-style: none;
  padding: 0;
  margin: 0 0 var(--rl-spacing-lg) 0;
}
.rl-coach-tier-list li {
  padding: var(--rl-spacing-xs) 0;
  font-family: var(--rl-font-data);
  font-size: var(--rl-font-size-xs);
  color: var(--rl-color-dark-navy);
  border-bottom: 1px solid var(--rl-color-silver);
  line-height: var(--rl-line-height-normal);
}
.rl-coach-tier-list li:last-child {
  border-bottom: none;
}
.rl-coach-tier-cta {
  display: inline-block;
  font-family: var(--rl-font-data);
  font-size: var(--rl-font-size-2xs);
  font-weight: var(--rl-font-weight-bold);
  letter-spacing: var(--rl-letter-spacing-wide);
  text-transform: uppercase;
  color: var(--rl-color-dark-navy);
  text-decoration: none;
  border-bottom: 1px solid var(--rl-color-dark-navy);
  padding-bottom: 2px;
  transition: color var(--rl-transition-hover),
              border-color var(--rl-transition-hover);
}
.rl-coach-tier-cta:hover {
  color: var(--rl-color-steel);
  border-color: var(--rl-color-steel);
}
.rl-coach-tier-disclaimer {
  font-family: var(--rl-font-editorial);
  font-size: var(--rl-font-size-sm);
  color: var(--rl-color-steel);
  line-height: var(--rl-line-height-relaxed);
  margin-top: var(--rl-spacing-lg);
  max-width: 68ch;
  margin-bottom: 0;
}
.rl-coach-tier-setup-fee {
  font-family: var(--rl-font-editorial);
  font-size: var(--rl-font-size-sm);
  color: var(--rl-color-steel);
  line-height: var(--rl-line-height-relaxed);
  margin-top: var(--rl-spacing-xs);
  max-width: 68ch;
  margin-bottom: 0;
}

/* ── A fit, or not ───────────────────────────────── */
.rl-coach-audience {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--rl-spacing-2xl);
  max-width: 960px;
}
.rl-coach-audience-heading {
  font-family: var(--rl-font-editorial);
  font-size: var(--rl-font-size-base);
  font-weight: var(--rl-font-weight-semibold);
  margin: 0 0 var(--rl-spacing-md) 0;
}
.rl-coach-audience-heading--yes {
  color: var(--rl-color-dark-navy);
}
.rl-coach-audience-heading--no {
  color: var(--rl-color-steel);
}
.rl-coach-audience-list {
  list-style: none;
  padding: 0;
  margin: 0;
}
.rl-coach-audience-list li {
  padding: var(--rl-spacing-sm) 0;
  font-family: var(--rl-font-editorial);
  font-size: var(--rl-font-size-sm);
  color: var(--rl-color-dark-navy);
  border-bottom: 1px solid var(--rl-color-silver);
  line-height: var(--rl-line-height-normal);
}
.rl-coach-audience-list li:last-child {
  border-bottom: none;
}
.rl-coach-list--no li {
  color: var(--rl-color-steel);
}

/* ── FAQ accordion ───────────────────────────────── */
.rl-coach-faq-list {
  max-width: 720px;
}
.rl-coach-faq-item {
  border-bottom: 1px solid var(--rl-color-silver);
}
.rl-coach-faq-item:first-child {
  border-top: 1px solid var(--rl-color-silver);
}
.rl-coach-faq-q {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: var(--rl-spacing-md);
  padding: var(--rl-spacing-sm) 0;
  cursor: pointer;
  font-family: var(--rl-font-editorial);
  font-size: var(--rl-font-size-base);
  font-weight: var(--rl-font-weight-semibold);
  color: var(--rl-color-dark-navy);
  user-select: none;
  transition: color var(--rl-transition-hover);
}
.rl-coach-faq-q:hover {
  color: var(--rl-color-steel);
}
.rl-coach-faq-toggle {
  font-family: var(--rl-font-data);
  font-size: var(--rl-font-size-md);
  font-weight: var(--rl-font-weight-regular);
  line-height: 1;
  color: var(--rl-color-steel);
  transition: color var(--rl-transition-hover);
}
.rl-coach-faq-item.rl-coach-faq-open .rl-coach-faq-toggle {
  color: var(--rl-color-dark-navy);
}
.rl-coach-faq-a {
  max-height: 0;
  overflow: hidden;
  transition: max-height var(--rl-transition-hover);
}
.rl-coach-faq-item.rl-coach-faq-open .rl-coach-faq-a {
  max-height: 500px;
  padding-bottom: var(--rl-spacing-sm);
}
.rl-coach-faq-a p {
  font-family: var(--rl-font-editorial);
  font-size: var(--rl-font-size-sm);
  color: var(--rl-color-steel);
  line-height: var(--rl-line-height-relaxed);
  margin: 0;
  max-width: 60ch;
}

/* ── Application close — dark band ────────────────── */
.rl-coach-final-cta {
  padding: var(--rl-spacing-xl) 0;
  text-align: left;
}
.rl-coach-final-kicker {
  font-family: var(--rl-font-data);
  font-size: var(--rl-font-size-2xs);
  letter-spacing: var(--rl-letter-spacing-wider);
  text-transform: uppercase;
  color: var(--rl-color-steel);
  margin: 0 0 var(--rl-spacing-lg) 0;
}
.rl-coach-final-hook {
  font-family: var(--rl-font-editorial);
  font-size: var(--rl-font-size-2xl);
  line-height: var(--rl-line-height-relaxed);
  color: var(--rl-color-cool-white);
  margin: 0 0 var(--rl-spacing-xl) 0;
  max-width: 26em;
}
.rl-coach-final-cta-link {
  display: inline-block;
  border: 1px solid var(--rl-color-cool-white);
  padding: var(--rl-spacing-sm) var(--rl-spacing-lg);
  font-family: var(--rl-font-data);
  font-size: var(--rl-font-size-2xs);
  font-weight: var(--rl-font-weight-bold);
  letter-spacing: var(--rl-letter-spacing-wide);
  text-transform: uppercase;
  color: var(--rl-color-cool-white);
  text-decoration: none;
  transition: background-color var(--rl-transition-hover),
              color var(--rl-transition-hover);
}
.rl-coach-final-cta-link:hover {
  background-color: var(--rl-color-cool-white);
  color: var(--rl-color-dark-navy);
}
.rl-coach-final-contact {
  font-family: var(--rl-font-editorial);
  font-size: var(--rl-font-size-sm);
  color: var(--rl-color-light-steel);
  margin-top: var(--rl-spacing-lg);
}
.rl-coach-final-contact a {
  color: var(--rl-color-cool-white);
}

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

/* ── Reduced motion ─────────────────────────────── */
@media (prefers-reduced-motion: reduce) {
  .rl-coach-faq-a {
    transition: none;
  }
}

/* ── Responsive ──────────────────────────────────── */
@media (max-width: 768px) {
  .rl-coach-inner {
    padding: 0 var(--rl-spacing-md);
  }
  .rl-coach-band {
    padding: var(--rl-spacing-xl) 0;
  }
  .rl-coach-file-strip {
    flex-direction: column;
    gap: var(--rl-spacing-2xs);
  }
  .rl-coach-hero h1 {
    font-size: var(--rl-font-size-2xl);
  }
  .rl-coach-term {
    grid-template-columns: 1fr;
    gap: var(--rl-spacing-xs);
  }
  .rl-coach-term-num {
    padding-top: 0;
  }
  .rl-coach-tiers {
    grid-template-columns: 1fr;
  }
  .rl-coach-tier-col {
    border-right: none;
    border-bottom: 1px solid var(--rl-color-silver);
    padding: var(--rl-spacing-lg) 0;
  }
  .rl-coach-tier-col:first-child {
    padding-top: 0;
  }
  .rl-coach-tier-col:last-child {
    border-bottom: none;
    padding-bottom: 0;
  }
  .rl-coach-audience {
    grid-template-columns: 1fr;
    gap: var(--rl-spacing-lg);
  }
  .rl-coach-final-hook {
    font-size: var(--rl-font-size-xl);
  }
  .rl-neo-brutalist-page {
    padding-bottom: 60px;
  }
}
''' + '\n</style>'


# ── JS ────────────────────────────────────────────────────────


def build_coaching_js() -> str:
    """Interactive JS for coaching page — FAQ, scroll depth, GA4 events."""
    return '''<script>
/* FAQ accordion — single-open behavior */
(function() {
  var items = document.querySelectorAll('.rl-coach-faq-item');
  items.forEach(function(item) {
    var q = item.querySelector('.rl-coach-faq-q');
    if (!q) return;
    function toggle() {
      var wasOpen = item.classList.contains('rl-coach-faq-open');
      items.forEach(function(i) { i.classList.remove('rl-coach-faq-open'); var iq = i.querySelector('.rl-coach-faq-q'); if (iq) iq.setAttribute('aria-expanded', 'false'); });
      if (!wasOpen) {
        item.classList.add('rl-coach-faq-open');
        q.setAttribute('aria-expanded', 'true');
        if (typeof gtag === 'function') gtag('event', 'coaching_faq_open', { question: q.textContent.trim().slice(0, 60) });
      } else {
        q.setAttribute('aria-expanded', 'false');
      }
    }
    q.addEventListener('click', toggle);
    q.addEventListener('keydown', function(e) { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); toggle(); } });
  });
})();

/* Scroll depth tracking */
(function() {
  if (typeof gtag !== 'function' || !('IntersectionObserver' in window)) return;
  var sections = [
    { id: 'hero', label: '0_hero' },
    { id: 'terms', label: '15_terms' },
    { id: 'tiers', label: '35_tiers' },
    { id: 'fit', label: '55_fit' },
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

/* Smooth scroll for anchor links */
document.querySelectorAll('a[href^="#"]').forEach(function(a) {
  a.addEventListener('click', function(e) {
    var target = document.getElementById(a.getAttribute('href').slice(1));
    if (target) { e.preventDefault(); target.scrollIntoView({ behavior: 'smooth', block: 'start' }); }
  });
});

/* Mobile sticky CTA — show after scrolling past hero */
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
        "description": "Road cycling coaching from one coach, 427 courses on file. A human who reads your training data, adjusts the plan when your life changes, and tells you the truth.",
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

    nav = build_nav()
    hero = build_hero()
    terms = build_terms()
    tiers = build_tiers()
    honest = build_honest_check()
    faq = build_faq()
    final_cta = build_application_close()
    footer = build_footer()
    sticky = build_mobile_sticky_cta()
    coaching_css = build_coaching_css()
    coaching_js = build_coaching_js()
    jsonld = build_jsonld()

    if external_assets:
        page_css = external_assets['css_tag']
        inline_js = external_assets['js_tag']
    else:
        page_css = get_page_css()
        inline_js = build_inline_js()

    meta_desc = "Road cycling coaching built on 427 analyzed courses. A human coach, a plan that adjusts weekly, and honest feedback. From $199 every 4 weeks."

    og_tags = f'''<meta property="og:title" content="Coaching | Roadie Labs">
  <meta property="og:description" content="Coaching built around your race, your hours, and your life. From the coach behind 427 course profiles.">
  <meta property="og:type" content="website">
  <meta property="og:url" content="{esc(canonical_url)}">
  <meta property="og:image" content="{SITE_BASE_URL}/og/homepage.jpg">
  <meta property="og:image:width" content="1200">
  <meta property="og:image:height" content="630">
  <meta property="og:site_name" content="Roadie Labs">
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:title" content="Coaching | Roadie Labs">
  <meta name="twitter:description" content="Coaching built around your race, your hours, and your life. From the coach behind 427 course profiles.">
  <meta name="twitter:image" content="{SITE_BASE_URL}/og/homepage.jpg">'''

    preload = get_preload_hints()

    return f'''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Road Cycling Coaching | Roadie Labs</title>
  <meta name="description" content="{esc(meta_desc)}">
  <meta name="robots" content="index, follow">
  <link rel="canonical" href="{esc(canonical_url)}">
  <link rel="preconnect" href="https://www.googletagmanager.com" crossorigin>
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
  {nav}

  {hero}

  {terms}

  {tiers}

  {honest}


  {faq}

  {final_cta}

  {footer}

  {sticky}
</div>

{inline_js}
{coaching_js}

''' + '<script>' + get_site_header_js() + '</script>' + f'''

{get_consent_banner_html()}
</body>
</html>'''


def main():
    parser = argparse.ArgumentParser(description="Generate Roadie Labs coaching page")
    parser.add_argument("--output-dir", default=str(OUTPUT_DIR), help="Output directory")
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    assets = write_shared_assets(output_dir)

    html_content = generate_coaching_page(external_assets=assets)
    output_file = output_dir / "coaching.html"
    output_file.write_text(html_content, encoding="utf-8")
    print(f"Generated {output_file} ({len(html_content):,} bytes)")


if __name__ == "__main__":
    main()
