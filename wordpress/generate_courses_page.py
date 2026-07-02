#!/usr/bin/env python3
"""
Generate the Roadie Labs /courses/ page in neo-brutalist style.

Cross-sells two self-paced courses sold on Gravel God Cycling, Roadie Labs'
sister brand (same coach): Gravel Hydration Mastery ($19) and Dirt Craft:
Technical Gravel Mastery ($29), plus the two-course bundle ($39). Reuses
CSS/style patterns from generate_neo_brutalist.py and the about page
component library (hero, section headers, cards, FAQ).

Usage:
    python generate_courses_page.py
    python generate_courses_page.py --output-dir ./output
"""

import argparse
import html
import json
from pathlib import Path

from generate_neo_brutalist import (
    SITE_BASE_URL,
    get_page_css,
    build_inline_js,
    write_shared_assets,
)
from brand_tokens import get_ga4_head_snippet, get_preload_hints
from shared_footer import get_mega_footer_html
from shared_header import get_site_header_html
from cookie_consent import get_consent_banner_html

OUTPUT_DIR = Path(__file__).parent / "output"

# ── Course catalog (sold on the sister brand) ─────────────────
GRAVEL_GOD_BASE_URL = "https://gravelgodcycling.com"
HYDRATION_URL = f"{GRAVEL_GOD_BASE_URL}/course/gravel-hydration-mastery/"
DIRT_CRAFT_URL = f"{GRAVEL_GOD_BASE_URL}/course/dirt-craft/"
BUNDLE_URL = f"{GRAVEL_GOD_BASE_URL}/course/"

HYDRATION_PRICE = 19
DIRT_CRAFT_PRICE = 29
BUNDLE_PRICE = 39


def esc(text) -> str:
    """HTML-escape a string."""
    return html.escape(str(text)) if text else ""


# ── Page sections ─────────────────────────────────────────────


def build_nav() -> str:
    return get_site_header_html(active="courses") + f'''
  <div class="rl-breadcrumb">
    <a href="{SITE_BASE_URL}/">Home</a>
    <span class="rl-breadcrumb-sep">&rsaquo;</span>
    <span class="rl-breadcrumb-current">Courses</span>
  </div>'''


def build_hero() -> str:
    return '''<div class="rl-hero rl-courses-hero">
    <div class="rl-hero-tier" style="background:var(--rl-color-orange)">COURSES</div>
    <h1 data-text="Two Courses. 20 Lessons. Same Coach.">Two Courses. 20 Lessons. Same Coach.</h1>
    <p class="rl-hero-tagline">Both courses are built and sold by Gravel God Cycling, Roadie Labs&#39; sister brand &mdash; same coach behind both sites, Matti Rowe. They&#39;re listed here because the material keeps coming up with road athletes.</p>
  </div>'''


def build_frame() -> str:
    return '''<div class="rl-section" id="why-here">
    <div class="rl-section-header">
      <span class="rl-section-kicker">01</span>
      <h2 class="rl-section-title">Why a Road Site Lists Gravel Courses</h2>
    </div>
    <div class="rl-section-body">
      <p class="rl-courses-prose">Two reasons. First, hydration physiology doesn&#39;t check what tires you&#39;re running &mdash; sweat rate, sodium, heat adaptation, and race-day execution work the same in a seven-hour gran fondo as they do in a 200K gravel race. Second, most road racers now ride at least one gravel event a year, and road handling instincts are exactly the ones that go wrong on loose surfaces.</p>
      <div class="rl-courses-highlight">
        <p>Full transparency: buying either course pays the same coach who built this site. The courses live on gravelgodcycling.com because that&#39;s where they were built first.</p>
      </div>
    </div>
  </div>'''


def build_course_cards() -> str:
    return f'''<div class="rl-section" id="courses">
    <div class="rl-section-header">
      <span class="rl-section-kicker">02</span>
      <h2 class="rl-section-title">The Courses</h2>
    </div>
    <div class="rl-section-body">
      <div class="rl-courses-grid">

        <article class="rl-course-card">
          <div class="rl-course-card-kicker">Hydration &middot; Surface-Agnostic</div>
          <h3 class="rl-course-card-title">Gravel Hydration Mastery</h3>
          <div class="rl-course-card-meta">
            <span class="rl-course-card-price">${HYDRATION_PRICE}</span>
            <span class="rl-course-card-lessons">8 interactive lessons</span>
          </div>
          <p class="rl-course-card-pitch">The word gravel is in the title. The physiology isn&#39;t surface-specific. A long road race in July asks the same questions a gravel 200 does &mdash; this course answers them with your numbers instead of generic advice.</p>
          <ul class="rl-course-card-bullets">
            <li>Measure your actual sweat rate with the built-in calculator &mdash; two weigh-ins and a ride, no lab</li>
            <li>Build a sodium plan from your own data instead of the label on the mix</li>
            <li>Heat adaptation protocols sized for a normal training week</li>
            <li>Race hydration planner: an hour-by-hour bottle and electrolyte schedule for your event</li>
            <li>Race-day execution &mdash; what to drink, when, and what to do when the plan breaks</li>
          </ul>
          <a href="{HYDRATION_URL}" class="rl-course-card-btn" data-course-cta="hydration_mastery">GET HYDRATION MASTERY &mdash; ${HYDRATION_PRICE}</a>
        </article>

        <article class="rl-course-card">
          <div class="rl-course-card-kicker">Technique &middot; For Roadies Crossing Over</div>
          <h3 class="rl-course-card-title">Dirt Craft: Technical Gravel Mastery</h3>
          <div class="rl-course-card-meta">
            <span class="rl-course-card-price">${DIRT_CRAFT_PRICE}</span>
            <span class="rl-course-card-lessons">12 lessons + 4 module quizzes</span>
          </div>
          <p class="rl-course-card-pitch">For road riders heading to their first (or fifth) gravel event. Road instincts &mdash; weight forward, brake late, hold your line &mdash; are the ones that put you on the ground when the surface goes loose.</p>
          <ul class="rl-course-card-bullets">
            <li>12 named technique tools covering cornering, braking, descending, and line choice on loose surfaces</li>
            <li>Drills with proof gates &mdash; you demonstrate the skill or you repeat the drill</li>
            <li>4 module quizzes that check the concepts actually landed</li>
            <li>Built for riders with strong fitness and road handling, zero gravel mileage</li>
            <li>Self-paced, ride the drills on your own schedule</li>
          </ul>
          <a href="{DIRT_CRAFT_URL}" class="rl-course-card-btn" data-course-cta="dirt_craft">GET DIRT CRAFT &mdash; ${DIRT_CRAFT_PRICE}</a>
        </article>

      </div>
    </div>
  </div>'''


def build_bundle_strip() -> str:
    savings = HYDRATION_PRICE + DIRT_CRAFT_PRICE - BUNDLE_PRICE
    return f'''<div class="rl-section" id="bundle">
    <div class="rl-section-body">
      <div class="rl-courses-bundle">
        <div class="rl-courses-bundle-text">
          <div class="rl-courses-bundle-kicker">Bundle</div>
          <h3 class="rl-courses-bundle-title">Both Courses &mdash; ${BUNDLE_PRICE}</h3>
          <p>Hydration Mastery (${HYDRATION_PRICE}) + Dirt Craft (${DIRT_CRAFT_PRICE}) together for ${BUNDLE_PRICE}. Saves ${savings}.</p>
        </div>
        <a href="{BUNDLE_URL}" class="rl-course-card-btn rl-courses-bundle-btn" data-course-cta="bundle">GET THE BUNDLE &mdash; ${BUNDLE_PRICE}</a>
      </div>
    </div>
  </div>'''


def build_faq() -> str:
    return '''<div class="rl-section" id="faq">
    <div class="rl-section-header">
      <span class="rl-section-kicker">03</span>
      <h2 class="rl-section-title">Questions</h2>
    </div>
    <div class="rl-section-body">
      <details class="rl-courses-faq-item" data-faq="delivery">
        <summary>How are the courses delivered?</summary>
        <p>Self-paced web lessons hosted on gravelgodcycling.com, with lifetime access. The email address you use at checkout unlocks the lessons &mdash; no separate account setup.</p>
      </details>
      <details class="rl-courses-faq-item" data-faq="refunds">
        <summary>What&#39;s the refund policy?</summary>
        <p>30-day money-back guarantee on both courses and the bundle. If it isn&#39;t useful, you get your money back.</p>
      </details>
      <details class="rl-courses-faq-item" data-faq="gravel-bike">
        <summary>Do I need a gravel bike?</summary>
        <p>Not for Hydration Mastery &mdash; it&#39;s physiology and planning, and the surface is irrelevant. For Dirt Craft you&#39;ll want a gravel bike or at least regular access to unpaved roads; the drills are built around loose-surface handling.</p>
      </details>
    </div>
  </div>'''


def build_footer() -> str:
    return get_mega_footer_html()


def build_courses_css() -> str:
    """Additional CSS specific to the courses page — token-driven, no raw hex."""
    return '''<style>
/* ── Courses hero — light override ───────────────── */
.rl-neo-brutalist-page .rl-courses-hero {
  background: var(--rl-color-cool-white);
  border-bottom: 3px double var(--rl-color-dark-navy);
}
.rl-neo-brutalist-page .rl-courses-hero h1 {
  color: var(--rl-color-dark-navy);
}
.rl-neo-brutalist-page .rl-courses-hero .rl-hero-tagline {
  color: var(--rl-color-secondary-blue);
}

/* ── Prose ───────────────────────────────────────── */
.rl-neo-brutalist-page .rl-courses-prose {
  font-family: var(--rl-font-editorial);
  font-size: var(--rl-font-size-base);
  line-height: var(--rl-line-height-prose);
  color: var(--rl-color-dark-navy);
  margin-bottom: var(--rl-spacing-md);
  max-width: 640px;
}

/* ── Highlighted paragraph ───────────────────────── */
.rl-neo-brutalist-page .rl-courses-highlight {
  border-left: 4px solid var(--rl-color-signal-red);
  padding: var(--rl-spacing-md) var(--rl-spacing-lg);
  background: var(--rl-color-silver);
  margin: var(--rl-spacing-lg) 0;
  max-width: 640px;
}
.rl-neo-brutalist-page .rl-courses-highlight p {
  font-family: var(--rl-font-editorial);
  font-size: var(--rl-font-size-md);
  font-weight: var(--rl-font-weight-semibold);
  line-height: var(--rl-line-height-relaxed);
  color: var(--rl-color-dark-navy);
  margin: 0;
}

/* ── Course cards ────────────────────────────────── */
.rl-neo-brutalist-page .rl-courses-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: var(--rl-spacing-lg);
}
.rl-neo-brutalist-page .rl-course-card {
  border: var(--rl-border-standard);
  background: var(--rl-color-cool-white);
  padding: var(--rl-spacing-lg);
  display: flex;
  flex-direction: column;
  transition: border-color var(--rl-transition-hover);
}
.rl-neo-brutalist-page .rl-course-card:hover {
  border-color: var(--rl-color-orange);
}
.rl-neo-brutalist-page .rl-course-card-kicker {
  font-family: var(--rl-font-data);
  font-size: var(--rl-font-size-2xs);
  font-weight: var(--rl-font-weight-bold);
  letter-spacing: var(--rl-letter-spacing-extreme);
  text-transform: uppercase;
  color: var(--rl-color-orange);
  margin-bottom: var(--rl-spacing-sm);
}
.rl-neo-brutalist-page .rl-course-card-title {
  font-family: var(--rl-font-editorial);
  font-size: var(--rl-font-size-xl);
  font-weight: var(--rl-font-weight-bold);
  color: var(--rl-color-dark-navy);
  line-height: var(--rl-line-height-tight);
  margin: 0 0 var(--rl-spacing-sm) 0;
}
.rl-neo-brutalist-page .rl-course-card-meta {
  display: flex;
  align-items: baseline;
  gap: var(--rl-spacing-md);
  border-top: 1px solid var(--rl-color-silver);
  border-bottom: 1px solid var(--rl-color-silver);
  padding: var(--rl-spacing-xs) 0;
  margin-bottom: var(--rl-spacing-md);
}
.rl-neo-brutalist-page .rl-course-card-price {
  font-family: var(--rl-font-data);
  font-size: var(--rl-font-size-2xl);
  font-weight: var(--rl-font-weight-bold);
  color: var(--rl-color-dark-navy);
  letter-spacing: var(--rl-letter-spacing-tight);
}
.rl-neo-brutalist-page .rl-course-card-lessons {
  font-family: var(--rl-font-data);
  font-size: var(--rl-font-size-2xs);
  font-weight: var(--rl-font-weight-bold);
  letter-spacing: var(--rl-letter-spacing-wider);
  text-transform: uppercase;
  color: var(--rl-color-secondary-blue);
}
.rl-neo-brutalist-page .rl-course-card-pitch {
  font-family: var(--rl-font-editorial);
  font-size: var(--rl-font-size-sm);
  line-height: var(--rl-line-height-prose);
  color: var(--rl-color-dark-navy);
  margin: 0 0 var(--rl-spacing-md) 0;
}
.rl-neo-brutalist-page .rl-course-card-bullets {
  list-style: none;
  padding: 0;
  margin: 0 0 var(--rl-spacing-lg) 0;
  flex: 1;
}
.rl-neo-brutalist-page .rl-course-card-bullets li {
  font-family: var(--rl-font-data);
  font-size: var(--rl-font-size-xs);
  line-height: var(--rl-line-height-relaxed);
  color: var(--rl-color-dark-navy);
  padding: var(--rl-spacing-xs) 0 var(--rl-spacing-xs) var(--rl-spacing-lg);
  border-bottom: 1px solid var(--rl-color-silver);
  position: relative;
}
.rl-neo-brutalist-page .rl-course-card-bullets li::before {
  content: "+";
  position: absolute;
  left: 0;
  font-weight: var(--rl-font-weight-bold);
  color: var(--rl-color-orange);
}
.rl-neo-brutalist-page .rl-course-card-bullets li:last-child {
  border-bottom: none;
}
.rl-neo-brutalist-page .rl-course-card-btn {
  display: inline-block;
  background: var(--rl-color-primary-navy);
  color: var(--rl-color-cool-white);
  font-family: var(--rl-font-data);
  font-size: var(--rl-font-size-2xs);
  font-weight: var(--rl-font-weight-bold);
  text-transform: uppercase;
  letter-spacing: var(--rl-letter-spacing-wider);
  padding: var(--rl-spacing-sm) var(--rl-spacing-lg);
  border: 3px solid var(--rl-color-primary-navy);
  text-decoration: none;
  text-align: center;
  transition: background-color var(--rl-transition-hover),
              color var(--rl-transition-hover);
}
.rl-neo-brutalist-page .rl-course-card-btn:hover {
  background-color: var(--rl-color-cool-white);
  color: var(--rl-color-dark-navy);
}

/* ── Bundle strip ────────────────────────────────── */
.rl-neo-brutalist-page .rl-courses-bundle {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--rl-spacing-lg);
  border: var(--rl-border-standard);
  border-top: 3px double var(--rl-color-dark-navy);
  border-bottom: 3px double var(--rl-color-dark-navy);
  background: var(--rl-color-silver);
  padding: var(--rl-spacing-lg);
}
.rl-neo-brutalist-page .rl-courses-bundle-kicker {
  font-family: var(--rl-font-data);
  font-size: var(--rl-font-size-2xs);
  font-weight: var(--rl-font-weight-bold);
  letter-spacing: var(--rl-letter-spacing-extreme);
  text-transform: uppercase;
  color: var(--rl-color-orange);
  margin-bottom: var(--rl-spacing-2xs);
}
.rl-neo-brutalist-page .rl-courses-bundle-title {
  font-family: var(--rl-font-editorial);
  font-size: var(--rl-font-size-lg);
  font-weight: var(--rl-font-weight-bold);
  color: var(--rl-color-dark-navy);
  margin: 0 0 var(--rl-spacing-2xs) 0;
}
.rl-neo-brutalist-page .rl-courses-bundle-text p {
  font-family: var(--rl-font-data);
  font-size: var(--rl-font-size-xs);
  color: var(--rl-color-dark-navy);
  margin: 0;
}
.rl-neo-brutalist-page .rl-courses-bundle-btn {
  flex-shrink: 0;
}

/* ── FAQ ─────────────────────────────────────────── */
.rl-neo-brutalist-page .rl-courses-faq-item {
  border: var(--rl-border-standard);
  background: var(--rl-color-cool-white);
  margin-bottom: var(--rl-spacing-sm);
  max-width: 720px;
}
.rl-neo-brutalist-page .rl-courses-faq-item summary {
  cursor: pointer;
  padding: var(--rl-spacing-md) var(--rl-spacing-lg);
  font-family: var(--rl-font-data);
  font-size: var(--rl-font-size-sm);
  font-weight: var(--rl-font-weight-bold);
  letter-spacing: var(--rl-letter-spacing-wide);
  color: var(--rl-color-dark-navy);
  list-style: none;
  position: relative;
  transition: color var(--rl-transition-hover);
}
.rl-neo-brutalist-page .rl-courses-faq-item summary::-webkit-details-marker {
  display: none;
}
.rl-neo-brutalist-page .rl-courses-faq-item summary::after {
  content: "+";
  position: absolute;
  right: var(--rl-spacing-lg);
  color: var(--rl-color-orange);
  font-weight: var(--rl-font-weight-bold);
}
.rl-neo-brutalist-page .rl-courses-faq-item[open] summary::after {
  content: "\\2212";
}
.rl-neo-brutalist-page .rl-courses-faq-item summary:hover {
  color: var(--rl-color-orange);
}
.rl-neo-brutalist-page .rl-courses-faq-item p {
  font-family: var(--rl-font-editorial);
  font-size: var(--rl-font-size-sm);
  line-height: var(--rl-line-height-prose);
  color: var(--rl-color-dark-navy);
  margin: 0;
  padding: 0 var(--rl-spacing-lg) var(--rl-spacing-md);
}

/* ── Responsive ──────────────────────────────────── */
@media (max-width: 768px) {
  .rl-neo-brutalist-page .rl-courses-grid {
    grid-template-columns: 1fr;
  }
  .rl-neo-brutalist-page .rl-courses-bundle {
    flex-direction: column;
    align-items: flex-start;
  }
}
</style>'''


def build_courses_js() -> str:
    """GA4 event tracking for course cross-sell CTAs and FAQ toggles."""
    return '''<script>
// Course cross-sell CTA click tracking
document.querySelectorAll('[data-course-cta]').forEach(function(el) {
  el.addEventListener('click', function() {
    if (typeof gtag === 'function') gtag('event', 'course_crosssell_click', { course_id: el.getAttribute('data-course-cta') });
  });
});

// FAQ open tracking
document.querySelectorAll('[data-faq]').forEach(function(el) {
  el.addEventListener('toggle', function() {
    if (el.open && typeof gtag === 'function') gtag('event', 'courses_faq_open', { faq_id: el.getAttribute('data-faq') });
  });
});
</script>'''


def build_jsonld() -> str:
    """Build WebPage + FAQPage JSON-LD for the courses page."""
    webpage = {
        "@context": "https://schema.org",
        "@type": "WebPage",
        "name": "Courses — Hydration & Gravel Technique for Road Cyclists",
        "description": "Two self-paced courses from Gravel God Cycling, Roadie Labs' sister brand: Gravel Hydration Mastery ($19, 8 lessons) and Dirt Craft: Technical Gravel Mastery ($29, 12 lessons).",
        "url": f"{SITE_BASE_URL}/courses/",
        "isPartOf": {
            "@type": "WebSite",
            "name": "Roadie Labs",
            "url": SITE_BASE_URL,
        },
    }
    faq = {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": [
            {
                "@type": "Question",
                "name": "How are the courses delivered?",
                "acceptedAnswer": {
                    "@type": "Answer",
                    "text": "Self-paced web lessons hosted on gravelgodcycling.com, with lifetime access. The email address you use at checkout unlocks the lessons.",
                },
            },
            {
                "@type": "Question",
                "name": "What's the refund policy?",
                "acceptedAnswer": {
                    "@type": "Answer",
                    "text": "30-day money-back guarantee on both courses and the bundle.",
                },
            },
            {
                "@type": "Question",
                "name": "Do I need a gravel bike?",
                "acceptedAnswer": {
                    "@type": "Answer",
                    "text": "Not for Hydration Mastery — it's physiology and planning. For Dirt Craft you'll want a gravel bike or regular access to unpaved roads.",
                },
            },
        ],
    }
    wp_tag = f'<script type="application/ld+json">{json.dumps(webpage, separators=(",", ":"))}</script>'
    faq_tag = f'<script type="application/ld+json">{json.dumps(faq, separators=(",", ":"))}</script>'
    return f'{wp_tag}\n  {faq_tag}'


# ── Assemble page ──────────────────────────────────────────────


def generate_courses_page(external_assets: dict = None) -> str:
    canonical_url = f"{SITE_BASE_URL}/courses/"

    nav = build_nav()
    hero = build_hero()
    frame = build_frame()
    cards = build_course_cards()
    bundle = build_bundle_strip()
    faq = build_faq()
    footer = build_footer()
    courses_css = build_courses_css()
    courses_js = build_courses_js()
    jsonld = build_jsonld()

    if external_assets:
        page_css = external_assets['css_tag']
        inline_js = external_assets['js_tag']
    else:
        page_css = get_page_css()
        inline_js = build_inline_js()

    meta_desc = "Two self-paced courses for road cyclists from Gravel God Cycling, Roadie Labs&#39; sister brand: Gravel Hydration Mastery ($19, 8 interactive lessons) and Dirt Craft: Technical Gravel Mastery ($29, 12 lessons + 4 quizzes)."

    og_tags = f'''<meta property="og:title" content="Courses — Hydration &amp; Gravel Technique for Road Cyclists">
  <meta property="og:description" content="{meta_desc}">
  <meta property="og:type" content="website">
  <meta property="og:url" content="{esc(canonical_url)}">
  <meta property="og:image" content="{SITE_BASE_URL}/og/homepage.jpg">
  <meta property="og:image:width" content="1200">
  <meta property="og:image:height" content="630">
  <meta property="og:site_name" content="Roadie Labs">
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:title" content="Courses — Hydration &amp; Gravel Technique for Road Cyclists">
  <meta name="twitter:description" content="{meta_desc}">
  <meta name="twitter:image" content="{SITE_BASE_URL}/og/homepage.jpg">'''

    preload = get_preload_hints()

    return f'''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Courses — Hydration &amp; Gravel Technique for Road Cyclists | Roadie Labs</title>
  <meta name="description" content="{meta_desc}">
  <meta name="robots" content="index, follow">
  <link rel="canonical" href="{esc(canonical_url)}">
  <link rel="preconnect" href="https://www.googletagmanager.com" crossorigin>
  {preload}
  {og_tags}
  {jsonld}
  {page_css}
  {courses_css}
  {get_ga4_head_snippet()}
</head>
<body>

<div class="rl-neo-brutalist-page">
  {nav}

  {hero}

  {frame}

  {cards}

  {bundle}

  {faq}

  {footer}
</div>

{inline_js}
{courses_js}

{get_consent_banner_html()}
</body>
</html>'''


def main():
    parser = argparse.ArgumentParser(description="Generate Roadie Labs courses page")
    parser.add_argument("--output-dir", default=str(OUTPUT_DIR), help="Output directory")
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    courses_dir = output_dir / "courses"
    courses_dir.mkdir(parents=True, exist_ok=True)

    # Reuse shared assets if they exist, otherwise write them
    assets = write_shared_assets(output_dir)

    html_content = generate_courses_page(external_assets=assets)
    output_file = courses_dir / "index.html"
    output_file.write_text(html_content, encoding="utf-8")
    print(f"Generated {output_file} ({len(html_content):,} bytes)")


if __name__ == "__main__":
    main()
