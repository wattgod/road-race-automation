#!/usr/bin/env python3
"""
Generate the Roadie Labs Coaching landing page.

Consolidates both service tiers (Custom Training Plans + 1:1 Coaching) into
a single page at /coaching/. Full-bleed band layout: section backgrounds span
the viewport, content sits in a 1200px measure, prose capped at a readable
width. Register is understated — the page asserts, it doesn't perform.

Ported from gravel-race-automation/wordpress/generate_coaching.py (the
approved rebuild) — structure and register are the source of truth; copy
and tokens are adapted for Roadie Labs.

Uses brand tokens exclusively — zero hardcoded hex, no border-radius, no
box-shadow, no bounce easing, no entrance animations.

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
from generate_about import _testimonial_data
from scroll_animations import get_scroll_animation_css, get_scroll_animation_js

OUTPUT_DIR = Path(__file__).parent / "output"
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# ── Constants ─────────────────────────────────────────────────

QUESTIONNAIRE_URL = f"{SITE_BASE_URL}/coaching/apply/"

# Curated for the coaching page: concrete result, concrete constraint,
# concrete rider. The full set stays on /about/. These are Gravel God
# athletes (Roadie Labs has no finishers yet) — the provenance line below
# the cards says so.
FEATURED_TESTIMONIAL_NAMES = ("Tony V.", "Laura M.", "Rob L.")


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


def build_hero() -> str:
    return f'''<section class="rl-coach-band rl-coach-hero" id="hero">
    <div class="rl-coach-inner">
      <p class="rl-coach-kicker">Coaching</p>
      <h1>Fitness is common. Preparation is rare.</h1>
      <p class="rl-coach-tagline">You can get fit on your own. The hard part is matching the training to the course, the calendar, and the rest of your life. That&#39;s the work I do.</p>
      <div class="rl-coach-hero-cta">
        <a href="{QUESTIONNAIRE_URL}" class="rl-coach-btn" data-cta="hero_apply">Apply</a>
        <a href="#how-it-works" class="rl-coach-btn rl-coach-btn--secondary" data-cta="hero_how_it_works">How it works</a>
      </div>
      <p class="rl-coach-stat-line">427 road courses analyzed. One coach.</p>
    </div>
  </section>'''


def build_problem() -> str:
    return f'''<section class="rl-coach-band" id="problem">
    <div class="rl-coach-inner">
      {_sec_head("01", "The gap")}
      <div class="rl-coach-prose">
        <p>Most riders who come to me are already fit. They train ten or twelve hours a week, read more about training than most coaches write, and still come apart at the same point in the same kind of event &mdash; the third hour of a gran fondo, the fourth time the road tilts up. That isn&#39;t a fitness problem. It&#39;s a planning problem &mdash; the training never quite matched the course, the calendar, or the job.</p>
        <p>An app can make you fitter. It can&#39;t study your race&#39;s course profile, cross it with your data, and tell you which climb will end your day if your pacing doesn&#39;t change by week eleven. That&#39;s what I do.</p>
      </div>
    </div>
  </section>'''


def build_deliverables() -> str:
    items = [
        (
            "Every file, read by a person",
            "I look at your ride data, not a dashboard summary of it. Software flags a number. I notice the interval you bailed on and ask why.",
        ),
        (
            "A plan that moves when your life does",
            "Sick kid, work trip, tender knee &mdash; the week adjusts that week, not after three missed targets teach an algorithm what I&#39;d have seen on Tuesday.",
        ),
        (
            "Honest feedback",
            "Sometimes that&#39;s &ldquo;you&#39;re sandbagging.&rdquo; Sometimes it&#39;s &ldquo;you need a rest week, and you won&#39;t take one unless it&#39;s on the calendar.&rdquo;",
        ),
        (
            "Race strategy from course data",
            "I&#39;ve analyzed 427 road courses &mdash; terrain, altitude, where events actually break apart. Your race-day plan is built from that record, not from a template.",
        ),
    ]
    cards = "\n        ".join(
        f'<div class="rl-coach-deliverable"><h3>{t}</h3><p>{d}</p></div>'
        for t, d in items
    )
    return f'''<section class="rl-coach-band" id="deliverables">
    <div class="rl-coach-inner">
      {_sec_head("02", "What you get")}
      <div class="rl-coach-deliverables" data-animate="fade-stagger">
        {cards}
      </div>
    </div>
  </section>'''


def build_how_it_works() -> str:
    steps = [
        (
            "Fill out the intake",
            "Twelve sections: your race, your hours, your history, your constraints. Honest answers make a better plan.",
        ),
        (
            "I build your first block",
            "I study your intake against the demands of your race and build the opening four weeks. You&#39;ll hear from me within 48 hours &mdash; including if I don&#39;t think coaching is what you need.",
        ),
        (
            "We train",
            "Weekly review, adjustments as they&#39;re needed, direct access when something comes up.",
        ),
        (
            "We sharpen toward race day",
            "Every four weeks we reassess. Fitness moves, schedules shrink, plans follow.",
        ),
    ]
    rows = "\n        ".join(
        f'<div class="rl-coach-step">'
        f'<div class="rl-coach-step-num">{i:02d}</div>'
        f'<div class="rl-coach-step-body"><h3>{t}</h3><p>{d}</p></div>'
        f'</div>'
        for i, (t, d) in enumerate(steps, start=1)
    )
    return f'''<section class="rl-coach-band" id="how-it-works">
    <div class="rl-coach-inner">
      {_sec_head("03", "How it works")}
      <div class="rl-coach-steps" data-animate="fade-stagger">
        {rows}
      </div>
      <div class="rl-coach-band-cta">
        <a href="{QUESTIONNAIRE_URL}" class="rl-coach-btn" data-cta="how_it_works_cta">Start the intake</a>
      </div>
    </div>
  </section>'''


def build_service_tiers() -> str:
    return f'''<section class="rl-coach-band rl-coach-band--sand" id="tiers">
    <div class="rl-coach-inner">
      {_sec_head("04", "Same coach. Three levels of involvement.")}
      <div class="rl-coach-tiers" data-animate="fade-stagger">
        <div class="rl-coach-tier-card">
          <h3>Min</h3>
          <div class="rl-coach-tier-header">$199<span class="rl-coach-tier-interval">/4 WK</span></div>
          <p class="rl-coach-tier-desc">The plan, plus a weekly check of your training. For athletes who execute on their own and want the thinking done right.</p>
          <ul class="rl-coach-tier-list">
            <li>Weekly training review</li>
            <li>File analysis</li>
            <li>Quarterly strategy calls</li>
            <li>Structured workouts for your trainer or head unit</li>
            <li>Race-day nutrition plan</li>
            <li>Custom training guide</li>
          </ul>
          <a href="{QUESTIONNAIRE_URL}?tier=min" class="rl-coach-btn rl-coach-btn--secondary" data-cta="tier_min">Get started</a>
        </div>
        <div class="rl-coach-tier-card rl-coach-tier-card--featured">
          <h3>Mid</h3>
          <div class="rl-coach-tier-header">$299<span class="rl-coach-tier-interval">/4 WK</span></div>
          <p class="rl-coach-tier-desc">The plan, watched. Someone reads the data between sessions and adjusts the same week life changes. Most athletes belong here.</p>
          <ul class="rl-coach-tier-list">
            <li>Everything in Min</li>
            <li>Detailed power-file analysis</li>
            <li>Every-4-week strategy calls</li>
            <li>Weekly plan adjustments</li>
            <li>Direct message access</li>
            <li>Blindspot detection</li>
          </ul>
          <a href="{QUESTIONNAIRE_URL}?tier=mid" class="rl-coach-btn" data-cta="tier_mid">Get started</a>
        </div>
        <div class="rl-coach-tier-card">
          <h3>Max</h3>
          <div class="rl-coach-tier-header">$1,200<span class="rl-coach-tier-interval">/4 WK</span></div>
          <p class="rl-coach-tier-desc">Everything, daily. For the race where you want nothing left to chance.</p>
          <ul class="rl-coach-tier-list">
            <li>Everything in Mid</li>
            <li>Daily file review</li>
            <li>On-demand calls</li>
            <li>Race-week strategy</li>
            <li>Multi-race season planning</li>
            <li>Priority response</li>
          </ul>
          <a href="{QUESTIONNAIRE_URL}?tier=max" class="rl-coach-btn rl-coach-btn--secondary" data-cta="tier_max">Get started</a>
        </div>
      </div>
      <p class="rl-coach-tier-disclaimer">Coaching doesn&#39;t fix skipped workouts or feedback you don&#39;t act on. If this isn&#39;t a fit, I&#39;ll tell you within 24 hours.</p>
      <p class="rl-coach-tier-setup-fee">All tiers include a one-time $99 setup fee: intake analysis, training-history review, and your first plan build.</p>
    </div>
  </section>'''


def build_testimonials() -> str:
    by_name = {name: (name, quote, meta) for name, quote, meta in _testimonial_data()}
    featured = [by_name[n] for n in FEATURED_TESTIMONIAL_NAMES if n in by_name]
    if len(featured) < 3:
        featured = _testimonial_data()[:3]
    cards = "\n        ".join(
        f'<blockquote class="rl-coach-testimonial">'
        f'<p>{esc(quote)}</p>'
        f'<footer><strong>{esc(name)}</strong>'
        f'<span class="rl-coach-testimonial-meta">{meta}</span>'
        f'</footer></blockquote>'
        for name, quote, meta in featured
    )
    return f'''<section class="rl-coach-band" id="results">
    <div class="rl-coach-inner">
      {_sec_head("05", "What athletes say")}
      <div class="rl-coach-testimonials">
        {cards}
      </div>
      <p class="rl-coach-testimonials-provenance">Gravel God athletes &mdash; same coach, same plan engine, different surface. Roadie Labs is new. Road finishers take this section over as the reports come in.</p>
      <p class="rl-coach-testimonials-more"><a href="{SITE_BASE_URL}/about/">More, from fifty athletes &rarr;</a></p>
    </div>
  </section>'''


def build_honest_check() -> str:
    return f'''<section class="rl-coach-band" id="honest-check">
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


def build_final_cta() -> str:
    return f'''<section class="rl-coach-band rl-coach-band--dark" id="final-cta">
    <div class="rl-coach-inner">
      <div class="rl-coach-final-cta">
        <p class="rl-coach-final-hook">If you have a race and a reason, start with the intake.</p>
        <p class="rl-coach-final-sub">It takes about ten minutes, and I read every one myself. You&#39;ll hear from me within 48 hours &mdash; including if I don&#39;t think coaching is what you need.</p>
        <div class="rl-coach-final-buttons">
          <a href="{QUESTIONNAIRE_URL}" class="rl-coach-btn rl-coach-btn--light" data-cta="final_fill_intake">Start the intake</a>
        </div>
        <p class="rl-coach-final-contact">Questions first? <a href="mailto:coach@roadielabs.com">coach@roadielabs.com</a> &mdash; I answer myself, usually within a day.</p>
      </div>
    </div>
  </section>'''


def build_footer() -> str:
    return get_mega_footer_html()


def build_mobile_sticky_cta() -> str:
    return f'''<div class="rl-coach-sticky-cta">
    <a href="{QUESTIONNAIRE_URL}" data-cta="sticky_cta">Apply for coaching</a>
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
.rl-coach-band--sand {
  background: var(--rl-color-silver);
  border-top: 1px solid var(--rl-color-light-steel);
  border-bottom: 1px solid var(--rl-color-light-steel);
}
.rl-coach-band--dark {
  background: var(--rl-color-dark-navy);
}
.rl-coach-band-cta {
  margin-top: var(--rl-spacing-lg);
}

/* ── Section heads — quiet numeral, serif title ──── */
.rl-coach-sec-head {
  display: flex;
  align-items: baseline;
  gap: var(--rl-spacing-md);
  border-bottom: 1px solid var(--rl-color-light-steel);
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

/* ── Hero ────────────────────────────────────────── */
.rl-coach-hero {
  padding-top: var(--rl-spacing-2xl);
  padding-bottom: var(--rl-spacing-2xl);
  border-bottom: 1px solid var(--rl-color-light-steel);
}
.rl-coach-kicker {
  font-family: var(--rl-font-data);
  font-size: var(--rl-font-size-2xs);
  text-transform: uppercase;
  letter-spacing: var(--rl-letter-spacing-extreme);
  color: var(--rl-color-steel);
  margin: 0 0 var(--rl-spacing-md) 0;
}
.rl-coach-hero h1 {
  font-family: var(--rl-font-editorial);
  font-size: var(--rl-font-size-4xl);
  font-weight: var(--rl-font-weight-bold);
  color: var(--rl-color-dark-navy);
  line-height: var(--rl-line-height-tight);
  margin: 0;
  max-width: 18ch;
}
.rl-coach-tagline {
  font-family: var(--rl-font-editorial);
  font-size: var(--rl-font-size-md);
  line-height: var(--rl-line-height-relaxed);
  color: var(--rl-color-steel);
  max-width: 56ch;
  margin: var(--rl-spacing-lg) 0 0 0;
}
.rl-coach-hero-cta {
  display: flex;
  gap: var(--rl-spacing-md);
  margin-top: var(--rl-spacing-xl);
  flex-wrap: wrap;
}
.rl-coach-stat-line {
  font-family: var(--rl-font-data);
  font-size: var(--rl-font-size-2xs);
  text-transform: uppercase;
  letter-spacing: var(--rl-letter-spacing-wider);
  color: var(--rl-color-steel);
  margin: var(--rl-spacing-xl) 0 0 0;
}

/* ── Buttons ─────────────────────────────────────── */
.rl-coach-btn {
  display: inline-block;
  background: var(--rl-color-dark-navy);
  color: var(--rl-color-cool-white);
  font-family: var(--rl-font-data);
  font-size: var(--rl-font-size-2xs);
  font-weight: var(--rl-font-weight-bold);
  letter-spacing: var(--rl-letter-spacing-wide);
  text-transform: uppercase;
  padding: var(--rl-spacing-sm) var(--rl-spacing-lg);
  border: 2px solid var(--rl-color-dark-navy);
  text-decoration: none;
  text-align: center;
  cursor: pointer;
  transition: background-color var(--rl-transition-hover),
              border-color var(--rl-transition-hover),
              color var(--rl-transition-hover);
}
.rl-coach-btn:hover {
  background-color: var(--rl-color-near-black);
  border-color: var(--rl-color-near-black);
}
.rl-coach-btn--secondary {
  background: transparent;
  color: var(--rl-color-dark-navy);
}
.rl-coach-btn--secondary:hover {
  background-color: var(--rl-color-dark-navy);
  color: var(--rl-color-cool-white);
}
.rl-coach-btn--light {
  background: var(--rl-color-cool-white);
  color: var(--rl-color-dark-navy);
  border-color: var(--rl-color-cool-white);
}
.rl-coach-btn--light:hover {
  background-color: var(--rl-color-silver);
  border-color: var(--rl-color-silver);
  color: var(--rl-color-dark-navy);
}

/* ── Prose ───────────────────────────────────────── */
.rl-coach-prose p {
  font-family: var(--rl-font-editorial);
  font-size: var(--rl-font-size-base);
  line-height: var(--rl-line-height-prose);
  color: var(--rl-color-dark-navy);
  max-width: 68ch;
  margin: 0 0 var(--rl-spacing-md) 0;
}
.rl-coach-prose p:last-child {
  margin-bottom: 0;
}

/* ── Deliverables — 2×2, sentence-case serif heads ── */
.rl-coach-deliverables {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--rl-spacing-xl) var(--rl-spacing-2xl);
}
.rl-coach-deliverable h3 {
  font-family: var(--rl-font-editorial);
  font-size: var(--rl-font-size-md);
  font-weight: var(--rl-font-weight-semibold);
  color: var(--rl-color-dark-navy);
  margin: 0 0 var(--rl-spacing-xs) 0;
  line-height: var(--rl-line-height-tight);
}
.rl-coach-deliverable p {
  font-family: var(--rl-font-editorial);
  font-size: var(--rl-font-size-sm);
  line-height: var(--rl-line-height-prose);
  color: var(--rl-color-steel);
  margin: 0;
  max-width: 52ch;
}

/* ── How it works steps ──────────────────────────── */
.rl-coach-steps {
  display: flex;
  flex-direction: column;
  gap: 0;
  max-width: 720px;
}
.rl-coach-step {
  display: grid;
  grid-template-columns: 48px 1fr;
  gap: var(--rl-spacing-md);
  padding: var(--rl-spacing-md) 0;
  border-bottom: 1px solid var(--rl-color-light-steel);
}
.rl-coach-step:last-child {
  border-bottom: none;
}
.rl-coach-step-num {
  font-family: var(--rl-font-data);
  font-size: var(--rl-font-size-xs);
  color: var(--rl-color-steel);
  text-align: right;
  padding-top: 4px;
  letter-spacing: var(--rl-letter-spacing-wide);
}
.rl-coach-step-body h3 {
  font-family: var(--rl-font-editorial);
  font-size: var(--rl-font-size-base);
  font-weight: var(--rl-font-weight-semibold);
  color: var(--rl-color-dark-navy);
  margin: 0 0 var(--rl-spacing-2xs) 0;
}
.rl-coach-step-body p {
  font-family: var(--rl-font-editorial);
  font-size: var(--rl-font-size-sm);
  line-height: var(--rl-line-height-prose);
  color: var(--rl-color-steel);
  margin: 0;
  max-width: 60ch;
}

/* ── Service tiers ───────────────────────────────── */
.rl-coach-tiers {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: var(--rl-spacing-md);
}
.rl-coach-tier-card {
  border: 1px solid var(--rl-color-light-steel);
  padding: var(--rl-spacing-lg);
  background: var(--rl-color-cool-white);
  display: flex;
  flex-direction: column;
}
.rl-coach-tier-card--featured {
  border-top: 3px solid var(--rl-color-orange);
}
.rl-coach-tier-card h3 {
  font-family: var(--rl-font-editorial);
  font-size: var(--rl-font-size-lg);
  font-weight: var(--rl-font-weight-bold);
  color: var(--rl-color-dark-navy);
  margin: 0 0 var(--rl-spacing-2xs) 0;
  line-height: var(--rl-line-height-tight);
}
.rl-coach-tier-header {
  font-family: var(--rl-font-data);
  font-size: var(--rl-font-size-sm);
  font-weight: var(--rl-font-weight-bold);
  letter-spacing: var(--rl-letter-spacing-wide);
  color: var(--rl-color-steel);
  margin-bottom: var(--rl-spacing-sm);
}
.rl-coach-tier-interval {
  font-size: var(--rl-font-size-2xs);
  font-weight: var(--rl-font-weight-regular);
  letter-spacing: var(--rl-letter-spacing-normal);
}
.rl-coach-tier-desc {
  font-family: var(--rl-font-editorial);
  font-size: var(--rl-font-size-sm);
  line-height: var(--rl-line-height-relaxed);
  color: var(--rl-color-dark-navy);
  margin: 0 0 var(--rl-spacing-md) 0;
}
.rl-coach-tier-list {
  list-style: none;
  padding: 0;
  margin: 0 0 var(--rl-spacing-lg) 0;
  flex: 1;
}
.rl-coach-tier-list li {
  padding: var(--rl-spacing-xs) 0;
  font-family: var(--rl-font-data);
  font-size: var(--rl-font-size-xs);
  color: var(--rl-color-dark-navy);
  border-bottom: 1px solid var(--rl-color-light-steel);
  line-height: var(--rl-line-height-normal);
}
.rl-coach-tier-list li:last-child {
  border-bottom: none;
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

/* ── Testimonials — static, curated ──────────────── */
.rl-coach-testimonials {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: var(--rl-spacing-md);
}
.rl-coach-testimonial {
  background: var(--rl-color-cool-white);
  border: 1px solid var(--rl-color-light-steel);
  padding: var(--rl-spacing-lg);
  margin: 0;
  display: flex;
  flex-direction: column;
}
.rl-coach-testimonial p {
  font-family: var(--rl-font-editorial);
  font-size: var(--rl-font-size-sm);
  font-style: italic;
  line-height: var(--rl-line-height-prose);
  color: var(--rl-color-dark-navy);
  margin: 0 0 var(--rl-spacing-md) 0;
  flex: 1;
}
.rl-coach-testimonial footer {
  display: flex;
  flex-direction: column;
  gap: var(--rl-spacing-2xs);
  border-top: 1px solid var(--rl-color-light-steel);
  padding-top: var(--rl-spacing-sm);
}
.rl-coach-testimonial footer strong {
  font-family: var(--rl-font-data);
  font-size: var(--rl-font-size-xs);
  font-weight: var(--rl-font-weight-bold);
  color: var(--rl-color-dark-navy);
  letter-spacing: var(--rl-letter-spacing-wide);
}
.rl-coach-testimonial-meta {
  font-family: var(--rl-font-data);
  font-size: var(--rl-font-size-2xs);
  color: var(--rl-color-steel);
  letter-spacing: var(--rl-letter-spacing-wide);
}
.rl-coach-testimonials-provenance {
  margin: var(--rl-spacing-md) 0 0 0;
  font-family: var(--rl-font-data);
  font-size: var(--rl-font-size-2xs);
  color: var(--rl-color-steel);
  letter-spacing: var(--rl-letter-spacing-normal);
  max-width: 68ch;
}
.rl-coach-testimonials-more {
  margin: var(--rl-spacing-sm) 0 0 0;
  font-family: var(--rl-font-editorial);
  font-size: var(--rl-font-size-sm);
}
.rl-coach-testimonials-more a {
  color: var(--rl-color-steel);
  text-decoration: none;
  border-bottom: 1px solid var(--rl-color-light-steel);
  transition: color var(--rl-transition-hover),
              border-color var(--rl-transition-hover);
}
.rl-coach-testimonials-more a:hover {
  color: var(--rl-color-dark-navy);
  border-color: var(--rl-color-orange);
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
  border-bottom: 1px solid var(--rl-color-light-steel);
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
  border-bottom: 1px solid var(--rl-color-light-steel);
}
.rl-coach-faq-item:first-child {
  border-top: 1px solid var(--rl-color-light-steel);
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

/* ── Final CTA — dark band ───────────────────────── */
.rl-coach-final-cta {
  text-align: center;
  padding: var(--rl-spacing-xl) 0;
}
.rl-coach-final-hook {
  font-family: var(--rl-font-editorial);
  font-size: var(--rl-font-size-2xl);
  font-weight: var(--rl-font-weight-semibold);
  color: var(--rl-color-cool-white);
  margin: 0 0 var(--rl-spacing-sm) 0;
  line-height: var(--rl-line-height-tight);
}
.rl-coach-final-sub {
  font-family: var(--rl-font-editorial);
  font-size: var(--rl-font-size-base);
  color: var(--rl-color-light-steel);
  line-height: var(--rl-line-height-relaxed);
  margin: 0 auto var(--rl-spacing-lg);
  max-width: 56ch;
}
.rl-coach-final-buttons {
  display: flex;
  gap: var(--rl-spacing-md);
  justify-content: center;
  flex-wrap: wrap;
}
.rl-coach-final-contact {
  font-family: var(--rl-font-editorial);
  font-size: var(--rl-font-size-sm);
  color: var(--rl-color-light-steel);
  margin-top: var(--rl-spacing-lg);
  text-align: center;
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
  .rl-coach-hero h1 {
    font-size: var(--rl-font-size-2xl);
  }
  .rl-coach-deliverables {
    grid-template-columns: 1fr;
    gap: var(--rl-spacing-lg);
  }
  .rl-coach-tiers {
    grid-template-columns: 1fr;
  }
  .rl-coach-testimonials {
    grid-template-columns: 1fr;
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
''' + get_scroll_animation_css(["fade-stagger"]) + '\n</style>'


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
    { id: 'problem', label: '12_problem' },
    { id: 'deliverables', label: '25_deliverables' },
    { id: 'how-it-works', label: '37_how_it_works' },
    { id: 'tiers', label: '50_tiers' },
    { id: 'results', label: '62_results' },
    { id: 'honest-check', label: '75_honest_check' },
    { id: 'faq', label: '87_faq' },
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
''' + get_scroll_animation_js() + '\n</script>'


# ── JSON-LD ───────────────────────────────────────────────────


def build_jsonld() -> str:
    webpage = {
        "@context": "https://schema.org",
        "@type": "WebPage",
        "name": "Coaching | Roadie Labs",
        "description": "Road cycling coaching from the coach behind 427 course profiles. Three tiers of involvement, built around your race and your schedule.",
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
        "description": "Road cycling coaching: three tiers of involvement from weekly review to daily high-touch support. Built around your race, your schedule, and your training history.",
    }
    wp_tag = f'<script type="application/ld+json">{_safe_json_for_script(webpage, separators=(",", ":"))}</script>'
    svc_tag = f'<script type="application/ld+json">{_safe_json_for_script(service, separators=(",", ":"))}</script>'
    return f'{wp_tag}\n  {svc_tag}'


# ── Assemble page ─────────────────────────────────────────────


def generate_coaching_page(external_assets: dict = None) -> str:
    canonical_url = f"{SITE_BASE_URL}/coaching/"

    nav = build_nav()
    hero = build_hero()
    problem = build_problem()
    deliverables = build_deliverables()
    how = build_how_it_works()
    tiers = build_service_tiers()
    testimonials = build_testimonials()
    honest = build_honest_check()
    faq = build_faq()
    final_cta = build_final_cta()
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

  {problem}

  {deliverables}

  {how}

  {tiers}

  {testimonials}

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
