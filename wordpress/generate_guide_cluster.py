#!/usr/bin/env python3
"""
Generate the Roadie Labs Training Guide as a topic cluster (hub-and-spoke).

Splits the monolithic guide into 9 pages:
  - 1 pillar page (/guide/) with chapter overview and navigation
  - 8 chapter pages (/guide/{chapter-slug}/) with full content

Reuses all block renderers from generate_guide.py and all infographic
renderers from guide_infographics.py. Follows the same output pattern
as generate_prep_kit.py — writes {slug}/index.html per page.

Usage:
    python wordpress/generate_guide_cluster.py
    python wordpress/generate_guide_cluster.py --inline
    python wordpress/generate_guide_cluster.py --output-dir /tmp/guide
"""

import argparse
import hashlib
import html
import json
import re
import sys
from datetime import datetime
from pathlib import Path

# Import shared constants
sys.path.insert(0, str(Path(__file__).parent))
from generate_neo_brutalist import (
    SITE_BASE_URL,
    SUBSTACK_EMBED,
    SUBSTACK_URL,
    COACHING_URL,
    TRAINING_PLANS_URL,
)

from guide_infographics import INFOGRAPHIC_RENDERERS
from guide_plates import render_chapter_plate
from shared_header import get_site_header_css, get_site_header_html, get_site_header_js
from shared_footer import get_mega_footer_css, get_mega_footer_html
from cookie_consent import get_consent_banner_html
from brand_tokens import (
    get_ga4_head_snippet,
    get_tokens_css,
    get_font_face_css,
    get_preload_hints,
)
from guide_configs import (
    ROAD_CHAPTER_META,
    ROAD_GUIDE,
    GUIDE_CONFIGS,
    GateEndpointMode,
    GuideConfig,
)

# Reuse ALL block renderers + helpers from existing guide generator
import generate_guide
generate_guide._GLOSSARY = None  # Will be set during generation
from generate_guide import (
    BLOCK_RENDERERS,
    render_block,
    build_guide_css,
    build_guide_js,
    build_rider_selector,
    build_cta_newsletter,
    build_cta_training,
    build_cta_coaching,
    build_cta_finale,
    build_chapter_email_capture,
    CTA_BUILDERS,
    esc,
    _md_inline,
    _safe_json_for_script,
)


# ── Constants ──────────────────────────────────────────────────

# Backwards-compatible public aliases for the road guide. New guide
# behavior must receive a GuideConfig instead of reading these module globals.
CONTENT_JSON = ROAD_GUIDE.content_path
OUTPUT_DIR = ROAD_GUIDE.output_dir

# Chapter URL slugs — maps chapter id to URL slug
# (chapter ids in JSON already match desired URL slugs)

# Chapters 1-3 are free, 4-8 are gated
FREE_CHAPTERS = {1, 2, 3}
GATED_CHAPTERS = {4, 5, 6, 7, 8}

# SEO keyword targets per chapter
CHAPTER_META = ROAD_CHAPTER_META

# ── Content Loading ────────────────────────────────────────────


def _guide_url(config: GuideConfig, chapter_id: str = "") -> str:
    """Return a guide-relative URL while preserving the trailing-slash contract."""
    base = config.url_base.rstrip("/")
    return f"{base}/{chapter_id.strip('/')}/" if chapter_id else f"{base}/"


def load_content(config: GuideConfig = ROAD_GUIDE) -> dict:
    """Load and return guide content JSON."""
    return json.loads(config.content_path.read_text(encoding="utf-8"))


# ── Pillar Page Builders ───────────────────────────────────────


def build_pillar_hero(content: dict) -> str:
    """Build the hero section for the pillar page."""
    title = esc(content["title"])
    subtitle = esc(content["subtitle"])
    return f'''<div class="rl-hero">
    <div class="rl-hero-tier" style="background:var(--rl-color-signal-red)">FREE GUIDE</div>
    <h1>{title}</h1>
    <p class="rl-hero-tagline">{subtitle}</p>
  </div>'''


def _estimate_read_time(chapter: dict) -> int:
    """Estimate reading time in minutes based on block content length."""
    total_chars = 0
    for section in chapter.get("sections", []):
        for block in section.get("blocks", []):
            if block.get("type") == "prose":
                total_chars += len(block.get("content", ""))
            elif block.get("type") == "callout":
                total_chars += len(block.get("content", ""))
            elif block.get("type") == "tabs":
                for tab in block.get("tabs", []):
                    total_chars += len(tab.get("content", ""))
    # ~200 words/min, ~5 chars/word, plus time for infographics/interactive
    words = total_chars / 5
    minutes = words / 200
    # Add 1 min per infographic/interactive block
    for section in chapter.get("sections", []):
        for block in section.get("blocks", []):
            if block.get("type") in ("image", "calculator", "knowledge_check",
                                      "scenario", "flashcard", "zone_visualizer"):
                minutes += 1
    return max(3, round(minutes))


def build_chapter_grid(chapters: list, config: GuideConfig = ROAD_GUIDE) -> str:
    """Build the 8-card chapter grid for the pillar page."""
    cards = []
    for ch in chapters:
        num = ch["number"]
        ch_id = ch["id"]
        title = esc(ch["title"])
        subtitle = esc(ch.get("subtitle", ""))
        gated = ch.get("gated", False)
        read_time = _estimate_read_time(ch)

        lock_icon = '<span class="rl-cluster-card-lock" aria-hidden="true">&#128274;</span>' if gated else ''
        lock_class = ' rl-cluster-card--locked' if gated else ''
        badge = '<span class="rl-cluster-card-badge">FREE</span>' if not gated else '<span class="rl-cluster-card-badge rl-cluster-card-badge--locked">SUBSCRIBER</span>'

        desc_text = subtitle if subtitle else title
        colors = ['var(--rl-color-primary-navy)', 'var(--rl-color-near-black)',
                  'var(--rl-color-signal-red)', 'var(--rl-color-primary-navy)',
                  'var(--rl-color-near-black)', 'var(--rl-color-signal-red)',
                  'var(--rl-color-primary-navy)', 'var(--rl-color-near-black)']
        bg = colors[(num - 1) % len(colors)]

        cards.append(f'''<a href="{_guide_url(config, esc(ch_id))}" class="rl-cluster-card{lock_class}" data-chapter="{num}">
      <div class="rl-cluster-card-header" style="background:{bg}">
        <span class="rl-cluster-card-num">CHAPTER {num:02d}</span>
        {lock_icon}
      </div>
      <div class="rl-cluster-card-body">
        <h3 class="rl-cluster-card-title">{title}</h3>
        <p class="rl-cluster-card-desc">{desc_text}</p>
        <div class="rl-cluster-card-meta">
          {badge}
          <span class="rl-cluster-card-time">{read_time} min read</span>
        </div>
      </div>
    </a>''')

    # Add configurator card as a full-width "bonus" card
    cfg_card = f'''<a href="{_guide_url(config, 'race-prep-configurator')}" class="rl-cluster-card rl-cluster-card--configurator" data-configurator="true" style="grid-column:1/-1">
      <div class="rl-cluster-card-header" style="background:var(--rl-color-signal-red)">
        <span class="rl-cluster-card-num">INTERACTIVE TOOL</span>
      </div>
      <div class="rl-cluster-card-body">
        <h3 class="rl-cluster-card-title">Race Prep Configurator</h3>
        <p class="rl-cluster-card-desc">Select your race, rider type, and timeline. Get a personalized prep plan covering training, nutrition, hydration, gear, and mental preparation.</p>
        <div class="rl-cluster-card-meta">
          <span class="rl-cluster-card-badge rl-cluster-card-badge--locked">SUBSCRIBER</span>
          <span class="rl-cluster-card-time">Interactive</span>
        </div>
      </div>
    </a>'''

    return f'''<div class="rl-cluster-grid" id="rl-cluster-grid">
    {"".join(cards)}
    {cfg_card if config.include_configurator else ''}
  </div>'''


def _build_config_ctas(config: GuideConfig, blocks: tuple[str, ...]) -> str:
    """Render configured conversion blocks; legacy builders keep gravel exact."""
    legacy_builders = {
        "newsletter": build_cta_newsletter,
        "training_plans": build_cta_training,
        "coaching": build_cta_coaching,
    }
    rendered = []
    for block in blocks:
        if block in legacy_builders:
            rendered.append(legacy_builders[block]())
            continue
        raise ValueError(f"Unknown CTA block '{block}' for guide '{config.key}'")
    return "\n  ".join(rendered)


def build_pillar_cta_section(config: GuideConfig = ROAD_GUIDE) -> str:
    """Build the CTA section interspersed in the pillar page."""
    return _build_config_ctas(config, config.cta_set.pillar_blocks)


def build_pillar_jsonld(content: dict, config: GuideConfig = ROAD_GUIDE) -> str:
    """Build Course + BreadcrumbList JSON-LD for the pillar page."""
    canonical = f"{SITE_BASE_URL}{_guide_url(config)}"
    date_modified = config.date_modified
    if not date_modified:
        try:
            mtime = config.content_path.stat().st_mtime
            date_modified = datetime.fromtimestamp(mtime).strftime("%Y-%m-%d")
        except OSError:
            date_modified = datetime.now().strftime("%Y-%m-%d")
    og_image = f"{SITE_BASE_URL}/og/homepage.jpg"

    course = {
        "@context": "https://schema.org",
        "@type": "Course",
        "name": content["title"],
        "description": content["meta_description"],
        "url": canonical,
        "provider": {
            "@type": "Organization",
            "name": "Roadie Labs",
            "url": SITE_BASE_URL,
        },
        "hasCourseInstance": {
            "@type": "CourseInstance",
            "courseMode": "online",
        },
        "courseWorkload": "PT4H",
        "isAccessibleForFree": True,
        "datePublished": config.date_published,
        "dateModified": date_modified,
        "image": og_image,
    }

    breadcrumb = {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {
                "@type": "ListItem",
                "position": 1,
                "name": "Home",
                "item": SITE_BASE_URL,
            },
            {
                "@type": "ListItem",
                "position": 2,
                "name": config.guide_label,
                "item": canonical,
            },
        ],
    }

    return (
        f'<script type="application/ld+json">{_safe_json_for_script(course, separators=(",", ":"))}</script>\n'
        f'<script type="application/ld+json">{_safe_json_for_script(breadcrumb, separators=(",", ":"))}</script>'
    )


# ── Chapter Page Builders ──────────────────────────────────────


def build_chapter_breadcrumb(chapter: dict, config: GuideConfig = ROAD_GUIDE) -> str:
    """Build 3-item breadcrumb: Home > Training Guide > Chapter Title."""
    title = esc(chapter["title"])
    return f'''<div class="rl-breadcrumb">
    <a href="{SITE_BASE_URL}/">Home</a>
    <span class="rl-breadcrumb-sep">&rsaquo;</span>
    <a href="{_guide_url(config)}">{esc(config.guide_label)}</a>
    <span class="rl-breadcrumb-sep">&rsaquo;</span>
    <span class="rl-breadcrumb-current">{title}</span>
  </div>'''


def build_chapter_hero(chapter: dict) -> str:
    """Build the hero section for a chapter page."""
    num = chapter["number"]
    title = esc(chapter["title"])
    subtitle = esc(chapter.get("subtitle", ""))
    subtitle_html = f'<p class="rl-guide-chapter-subtitle">{subtitle}</p>' if subtitle else ''
    variant = "dark" if num in {2, 4, 6, 8} else "light"
    plate = render_chapter_plate(num, {"race_index": generate_guide._RACE_INDEX})

    return f'''<div class="rl-guide-chapter-hero rl-guide-chapter-hero--{variant}">
      {plate}
      <div class="rl-guide-chapter-title-block">
        <span class="rl-guide-chapter-num">CHAPTER {num:02d}</span>
        <h2 class="rl-guide-chapter-title">{title}</h2>
        {subtitle_html}
      </div>
    </div>'''


def build_chapter_content(chapter: dict) -> str:
    """Build the content body for a chapter page (all sections + blocks)."""
    sections_html = []
    for section in chapter["sections"]:
        sec_title = section.get("title", "")
        sec_title_html = f'<h3 class="rl-guide-section-title">{esc(sec_title)}</h3>' if sec_title else ''
        block_parts = []
        for b in section["blocks"]:
            rendered = render_block(b)
            block_parts.append(rendered)
        blocks_html = '\n'.join(block_parts)
        sections_html.append(f'''<div class="rl-guide-section" id="{esc(section["id"])}">
        {sec_title_html}
        {blocks_html}
      </div>''')

    return f'''<div class="rl-guide-chapter-body">
      {"".join(sections_html)}
    </div>'''


def build_chapter_progress(chapter: dict, chapters: list) -> str:
    """Build a progress indicator showing current chapter position."""
    num = chapter["number"]
    total = len(chapters)
    pct = round((num / total) * 100)
    return f'''<div class="rl-cluster-progress">
    <div class="rl-cluster-progress-label">Chapter {num} of {total}</div>
    <div class="rl-cluster-progress-bar" role="progressbar"
         aria-valuenow="{pct}" aria-valuemin="0" aria-valuemax="100"
         aria-label="Chapter {num} of {total}">
      <div class="rl-cluster-progress-fill" style="width:{pct}%"></div>
    </div>
  </div>'''


def build_prev_next_nav(chapter: dict, chapters: list,
                        config: GuideConfig = ROAD_GUIDE) -> str:
    """Build prev/next chapter navigation at bottom of chapter page."""
    num = chapter["number"]
    prev_ch = None
    next_ch = None
    for ch in chapters:
        if ch["number"] == num - 1:
            prev_ch = ch
        if ch["number"] == num + 1:
            next_ch = ch

    parts = []

    if prev_ch:
        prev_title = esc(prev_ch["title"])
        prev_slug = esc(prev_ch["id"])
        parts.append(
            f'<a href="{_guide_url(config, prev_slug)}" class="rl-cluster-nav-prev">'
            f'<span class="rl-cluster-nav-dir">&larr; PREVIOUS</span>'
            f'<span class="rl-cluster-nav-title">Ch {prev_ch["number"]}: {prev_title}</span>'
            f'</a>'
        )
    else:
        parts.append('<div class="rl-cluster-nav-spacer"></div>')

    if next_ch:
        next_title = esc(next_ch["title"])
        next_slug = esc(next_ch["id"])
        lock = ''
        if next_ch.get("gated"):
            lock = ' <span class="rl-cluster-nav-lock" aria-hidden="true">&#128274;</span>'
        parts.append(
            f'<a href="{_guide_url(config, next_slug)}" class="rl-cluster-nav-next">'
            f'<span class="rl-cluster-nav-dir">NEXT &rarr;{lock}</span>'
            f'<span class="rl-cluster-nav-title">Ch {next_ch["number"]}: {next_title}</span>'
            f'</a>'
        )
    else:
        parts.append('<div class="rl-cluster-nav-spacer"></div>')

    return f'''<nav class="rl-cluster-nav" aria-label="Chapter navigation">
    {"".join(parts)}
  </nav>'''


def build_chapter_gate(chapter: dict, config: GuideConfig = ROAD_GUIDE) -> str:
    """Build the gate overlay for gated chapter pages."""
    title = esc(chapter["title"])
    if config.gate_form.endpoint_mode is GateEndpointMode.WORKER_FIRST:
        # JavaScript posts to the worker and unlocks only on success; on worker
        # failure it submits the native FormSubmit action, whose _next redirect
        # returns with ?unlocked=1 so the capture is never silently dropped.
        return f'''<div class="rl-guide-gate rl-cluster-gate" id="rl-guide-gate">
    <div class="rl-guide-gate-inner">
      <span class="rl-guide-gate-kicker">THIS CHAPTER IS LOCKED</span>
      <h2>Unlock {title}</h2>
      <p>Subscribe to unlock all premium chapters instantly.</p>
      <form action="{esc(config.gate_form.formsubmit_endpoint)}" method="POST" class="rl-cluster-gate-form" id="rl-cluster-gate-form" data-chapter="{title}">
        <input type="hidden" name="_subject" value="{esc(config.gate_form.subject_label)}: {title}">
        <input type="hidden" name="_template" value="table">
        <input type="hidden" name="_captcha" value="false">
        <input type="hidden" name="_next" value="{SITE_BASE_URL}{_guide_url(config, chapter['id'])}?unlocked=1">
        <input type="hidden" name="source" value="{esc(config.gate_form.worker_source_value)}">
        <input type="text" name="website" value="" tabindex="-1" autocomplete="off" aria-hidden="true" class="rl-visually-hidden">
        <input type="email" name="email" placeholder="your@email.com" required class="rl-cluster-gate-email" aria-label="Email address">
        <button type="submit" class="rl-guide-btn rl-guide-btn--primary">UNLOCK FREE</button>
      </form>
      <button class="rl-guide-gate-bypass" id="rl-guide-gate-bypass">I already subscribed &mdash; unlock</button>
    </div>
  </div>'''

    # Legacy FormSubmit mode (no road config uses it; kept for enum completeness).
    return f'''<div class="rl-guide-gate rl-cluster-gate" id="rl-guide-gate">
    <div class="rl-guide-gate-inner">
      <span class="rl-guide-gate-kicker">THIS CHAPTER IS LOCKED</span>
      <h2>Unlock {title}</h2>
      <p>Subscribe to unlock all premium chapters instantly.</p>
      <form action="{esc(config.gate_form.formsubmit_endpoint)}" method="POST" class="rl-cluster-gate-form" id="rl-cluster-gate-form">
        <input type="hidden" name="_subject" value="{esc(config.gate_form.subject_label)}: {title}">
        <input type="hidden" name="_template" value="table">
        <input type="hidden" name="_captcha" value="false">
        <input type="hidden" name="_next" value="{SITE_BASE_URL}{_guide_url(config, esc(chapter['id']))}?unlocked=1">
        <input type="email" name="email" placeholder="your@email.com" required class="rl-cluster-gate-email" aria-label="Email address">
        <button type="submit" class="rl-guide-btn rl-guide-btn--primary">UNLOCK FREE</button>
      </form>
      <button class="rl-guide-gate-bypass" id="rl-guide-gate-bypass">I already subscribed &mdash; unlock</button>
    </div>
  </div>'''


def build_chapter_jsonld(chapter: dict, content: dict,
                         config: GuideConfig = ROAD_GUIDE) -> str:
    """Build Article + BreadcrumbList JSON-LD for a chapter page."""
    ch_id = chapter["id"]
    canonical = f"{SITE_BASE_URL}{_guide_url(config, ch_id)}"
    date_modified = config.date_modified
    if not date_modified:
        try:
            mtime = config.content_path.stat().st_mtime
            date_modified = datetime.fromtimestamp(mtime).strftime("%Y-%m-%d")
        except OSError:
            date_modified = datetime.now().strftime("%Y-%m-%d")
    og_image = f"{SITE_BASE_URL}/og/homepage.jpg"

    meta = config.chapter_meta.get(ch_id, {})
    description = meta.get("description", content.get("meta_description", ""))

    article = {
        "@context": "https://schema.org",
        "@type": "Article",
        "headline": f"Chapter {chapter['number']}: {chapter['title']}",
        "description": description,
        "url": canonical,
        "datePublished": config.date_published,
        "dateModified": date_modified,
        "image": og_image,
        "author": {
            "@type": "Organization",
            "name": "Roadie Labs",
            "url": SITE_BASE_URL,
        },
        "publisher": {
            "@type": "Organization",
            "name": "Roadie Labs",
            "url": SITE_BASE_URL,
        },
        "isPartOf": {
            "@type": "Course",
            "name": content["title"],
            "url": f"{SITE_BASE_URL}{_guide_url(config)}",
        },
    }

    breadcrumb = {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {
                "@type": "ListItem",
                "position": 1,
                "name": "Home",
                "item": SITE_BASE_URL,
            },
            {
                "@type": "ListItem",
                "position": 2,
                "name": config.guide_label,
                "item": f"{SITE_BASE_URL}{_guide_url(config)}",
            },
            {
                "@type": "ListItem",
                "position": 3,
                "name": chapter["title"],
                "item": canonical,
            },
        ],
    }

    # No HowTo schema: chapters are editorial articles, not procedures, and
    # marking section headings as HowToSteps mislabels the content type.
    parts = [
        f'<script type="application/ld+json">{_safe_json_for_script(article, separators=(",", ":"))}</script>',
        f'<script type="application/ld+json">{_safe_json_for_script(breadcrumb, separators=(",", ":"))}</script>',
    ]

    return '\n'.join(parts)


# ── Cluster-Specific CSS ──────────────────────────────────────


def build_cluster_css() -> str:
    """Return CSS additions for the cluster layout (pillar grid, nav, gate form)."""
    return '''
/* ── Cluster Chapter Grid ── */
.rl-cluster-grid{display:grid;grid-template-columns:repeat(2,1fr);gap:0;margin:0 0 40px}
.rl-cluster-card{text-decoration:none;color:inherit;border:1px solid var(--rl-hairline,rgba(0,0,0,0.06));border-radius:8px;overflow:hidden;background:var(--rl-surface,#fff);box-shadow:var(--rl-shadow-card,0 2px 4px rgba(0,0,0,0.06));display:flex;flex-direction:column;transition:box-shadow 0.2s,transform 0.2s}
.rl-cluster-card:hover{box-shadow:var(--rl-shadow-card-hover,0 4px 12px rgba(0,0,0,0.10));transform:translateY(-2px)}
.rl-cluster-card+.rl-cluster-card{margin-top:-3px}
.rl-cluster-card:nth-child(odd){border-right:none}
.rl-cluster-card:nth-child(n+3){margin-top:-3px}
.rl-cluster-card-header{padding:16px 20px;display:flex;justify-content:space-between;align-items:center}
.rl-cluster-card-num{font-family:var(--rl-font-data);font-size:10px;font-weight:700;letter-spacing:3px;color:rgba(255,255,255,0.85)}
.rl-cluster-card-lock{font-size:12px;opacity:0.6}
.rl-cluster-card-body{padding:16px 20px;flex:1;display:flex;flex-direction:column}
.rl-cluster-card-title{font-family:var(--rl-font-editorial);font-size:16px;font-weight:700;text-transform:uppercase;letter-spacing:1px;color:var(--rl-color-primary-navy);margin:0 0 6px}
.rl-cluster-card-desc{font-family:var(--rl-font-editorial);font-size:12px;color:var(--rl-color-secondary-blue);line-height:1.5;margin:0 0 auto;flex:1}
.rl-cluster-card-meta{display:flex;justify-content:space-between;align-items:center;margin-top:12px}
.rl-cluster-card-badge{font-family:var(--rl-font-data);font-size:9px;font-weight:700;letter-spacing:2px;color:var(--rl-color-signal-red);text-transform:uppercase}
.rl-cluster-card-badge--locked{color:var(--rl-color-secondary-blue)}
.rl-cluster-card-time{font-family:var(--rl-font-data);font-size:10px;color:var(--rl-color-secondary-blue)}

/* ── Cluster Progress ── */
.rl-cluster-progress{padding:12px 24px;background:var(--rl-color-silver);display:flex;align-items:center;gap:12px}
.rl-cluster-progress-label{font-family:var(--rl-font-data);font-size:11px;font-weight:700;letter-spacing:1px;color:var(--rl-color-secondary-blue);white-space:nowrap}
.rl-cluster-progress-bar{flex:1;height:6px;background:var(--rl-color-light-steel)}
.rl-cluster-progress-fill{height:100%;background:var(--rl-color-signal-red)}

/* ── Cluster Prev/Next Nav ── */
.rl-cluster-nav{display:grid;grid-template-columns:1fr 1fr;gap:12px;margin:40px 0 0;border-top:1px solid var(--rl-hairline-strong,rgba(0,0,0,0.12));padding-top:16px}
.rl-cluster-nav-prev,.rl-cluster-nav-next{display:flex;flex-direction:column;gap:4px;padding:20px 24px;text-decoration:none;color:inherit;border:1px solid var(--rl-hairline,rgba(0,0,0,0.06));border-radius:8px;background:var(--rl-surface,#fff);box-shadow:0 1px 2px rgba(0,0,0,0.04);transition:background 0.2s}
.rl-cluster-nav-prev{border-right:none}
.rl-cluster-nav-prev:hover,.rl-cluster-nav-next:hover{background:var(--rl-color-silver)}
.rl-cluster-nav-next{text-align:right}
.rl-cluster-nav-dir{font-family:var(--rl-font-data);font-size:10px;font-weight:700;letter-spacing:2px;color:var(--rl-color-secondary-blue)}
.rl-cluster-nav-title{font-family:var(--rl-font-editorial);font-size:14px;font-weight:700;color:var(--rl-color-primary-navy)}
.rl-cluster-nav-lock{font-size:10px;opacity:0.5}
.rl-cluster-nav-spacer{border:none}

/* ── Gate Form (formsubmit.co) ── */
.rl-cluster-gate-form{display:flex;gap:0;max-width:500px;margin:16px auto 0}
.rl-cluster-gate-email{flex:1;padding:12px 16px;border:1px solid var(--rl-hairline-strong,rgba(0,0,0,0.12));border-radius:4px;font-family:var(--rl-font-data);font-size:13px;background:var(--rl-color-cool-white);color:var(--rl-color-near-black)}
.rl-visually-hidden{position:absolute !important;width:1px;height:1px;margin:-1px;padding:0;border:0;clip:rect(0 0 0 0);clip-path:inset(50%);overflow:hidden;white-space:nowrap}
.rl-cluster-gate-email::placeholder{color:var(--rl-color-secondary-blue)}
.rl-cluster-gate-form .rl-guide-btn{border-left:none}

/* ── Cluster Gating (per-page) ── */
.rl-cluster-gated-content{display:none}
.rl-guide-unlocked .rl-cluster-gated-content{display:block}
.rl-guide-unlocked .rl-cluster-gate{display:none}

/* ── End-of-chapter email capture ── */
.rl-guide-email-capture{border-radius:8px;background:var(--rl-surface,#fff);box-shadow:var(--rl-shadow-card,0 2px 4px rgba(0,0,0,0.06));padding:24px;margin:40px 0 0;text-align:center}
.rl-guide-email-capture-text{font-family:var(--rl-font-editorial);font-size:14px;color:var(--rl-color-primary-navy);line-height:1.6;margin:0 0 16px}
.rl-guide-email-capture-form{display:flex;gap:0;max-width:420px;margin:0 auto}
.rl-guide-email-capture-input{flex:1;font-family:var(--rl-font-data);font-size:13px;padding:12px 14px;border:1px solid var(--rl-hairline-strong,rgba(0,0,0,0.12));border-radius:4px 0 0 4px;border-right:none;background:var(--rl-color-white);color:var(--rl-color-near-black);min-width:0}
.rl-guide-email-capture-input:focus{outline:none;border-color:var(--rl-color-signal-red)}
.rl-guide-email-capture-btn{font-family:var(--rl-font-data);font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:2px;padding:12px 18px;background:var(--rl-color-signal-red);color:var(--rl-color-white);border:2px solid var(--rl-color-signal-red);cursor:pointer;white-space:nowrap}
.rl-guide-email-capture-btn:hover{background:var(--rl-color-light-orange)}
.rl-guide-email-capture-success{font-family:var(--rl-font-data);font-size:13px;font-weight:700;color:var(--rl-color-light-orange);margin:16px 0 0}
.rl-guide-email-capture-error{font-family:var(--rl-font-data);font-size:11px;font-weight:700;color:var(--rl-color-error);margin:8px 0 0}

/* ── Persona Quiz (pillar) ── */
.rl-guide-quiz{border-radius:12px;background:var(--rl-surface,#fff);box-shadow:var(--rl-shadow-card,0 2px 4px rgba(0,0,0,0.06));padding:28px;margin:0 0 40px}
.rl-guide-quiz-kicker{font-family:var(--rl-font-data);font-size:10px;font-weight:700;letter-spacing:3px;color:var(--rl-color-signal-red)}
.rl-guide-quiz-title{font-family:var(--rl-font-editorial);font-size:20px;font-weight:700;color:var(--rl-color-primary-navy);margin:8px 0 20px}
.rl-guide-quiz-q{margin:0 0 18px}
.rl-guide-quiz-q-label{font-family:var(--rl-font-data);font-size:12px;font-weight:700;letter-spacing:1px;text-transform:uppercase;color:var(--rl-color-near-black);margin:0 0 10px}
.rl-guide-quiz-options{display:flex;flex-wrap:wrap;gap:8px}
.rl-guide-quiz-opt{font-family:var(--rl-font-data);font-size:12px;padding:10px 16px;background:var(--rl-surface,#fff);color:var(--rl-color-near-black);border:1px solid var(--rl-hairline-strong,rgba(0,0,0,0.12));border-radius:6px;box-shadow:0 1px 2px rgba(0,0,0,0.05);cursor:pointer}
.rl-guide-quiz-opt:hover{background:var(--rl-color-silver)}
.rl-guide-quiz-opt--active{background:var(--rl-cobalt-tint,rgba(74,120,176,0.08));border-color:var(--rl-cobalt,#4a78b0);color:var(--rl-cobalt-deep,#2a4a78)}
.rl-guide-quiz-result{border-top:1px solid var(--rl-hairline-strong,rgba(0,0,0,0.12));margin-top:20px;padding-top:20px}
.rl-guide-quiz-result-kicker{font-family:var(--rl-font-data);font-size:10px;font-weight:700;letter-spacing:3px;color:var(--rl-color-signal-red)}
.rl-guide-quiz-result-title{font-family:var(--rl-font-editorial);font-size:22px;font-weight:700;color:var(--rl-color-primary-navy);margin:6px 0 8px}
.rl-guide-quiz-result-text{font-family:var(--rl-font-editorial);font-size:14px;line-height:1.6;color:var(--rl-color-secondary-blue);margin:0 0 16px}
.rl-guide-quiz-skip{font-family:var(--rl-font-data);font-size:11px;color:var(--rl-color-secondary-blue);margin:16px 0 0}
.rl-guide-quiz-skip a{color:var(--rl-color-near-black);font-weight:700}

/* ── Rider Track pages ── */
.rl-guide-track-back{margin:32px 0 0}
.rl-guide-track-back a{font-family:var(--rl-font-data);font-size:12px;font-weight:700;letter-spacing:1px;text-transform:uppercase;color:var(--rl-color-near-black);text-decoration:none;border-bottom:1px solid var(--rl-cobalt,#4a78b0)}
.rl-guide-track-back a:hover{color:var(--rl-color-signal-red);border-color:var(--rl-color-signal-red)}

/* ── Responsive ── */
@media(max-width:768px){
.rl-cluster-grid{grid-template-columns:1fr}

.rl-cluster-nav{grid-template-columns:1fr}

.rl-cluster-nav-next{text-align:left}
.rl-cluster-gate-form{flex-direction:column}

.rl-guide-email-capture-form{flex-direction:column}
.rl-guide-email-capture-input{border-right:1px solid var(--rl-hairline-strong,rgba(0,0,0,0.12));border-radius:4px}
.rl-guide-quiz-options{flex-direction:column}
.rl-guide-quiz-opt{text-align:left}
}
'''


# ── Cluster JS ─────────────────────────────────────────────────


def _build_worker_first_cluster_js(config: GuideConfig) -> str:
    """Return worker-first gate/capture behavior for new guide configurations."""
    storage_key = f"{config.local_storage_key_prefix}_unlocked"
    event_prefix = config.ga4_event_label_prefix
    worker_url = config.gate_form.worker_endpoint
    source = config.gate_form.worker_source_value
    brand = config.gate_form.worker_brand_value
    return f'''/* ── Guide Cluster Unlock ── */
(function(){{
"use strict";
var STORAGE_KEY="{storage_key}";
var WORKER_URL="{worker_url}";
var SOURCE="{source}";
var BRAND="{brand}";
var PERSONA_KEY="{config.local_storage_key_prefix}_persona";
function getPersona(){{try{{return localStorage.getItem(PERSONA_KEY)||"";}}catch(e){{return "";}}}}
function track(n,p){{if(typeof gtag==="function")gtag("event",n,Object.assign({{transport_type:"beacon"}},p||{{}}));}}
function unlock(method){{
try{{localStorage.setItem(STORAGE_KEY,"1");}}catch(e){{}}
document.documentElement.classList.add("rl-guide-unlocked");
var gatedContent=document.querySelector(".rl-cluster-gated-content");
if(gatedContent)gatedContent.style.display="block";
var gate=document.getElementById("rl-guide-gate");
if(gate)gate.style.display="none";
track("{event_prefix}_gate_unlock",{{method:method||"unknown"}});
}}
if(new URLSearchParams(window.location.search).get("unlocked")==="1")unlock("email_form");
try{{if(localStorage.getItem(STORAGE_KEY)==="1")document.documentElement.classList.add("rl-guide-unlocked");}}catch(e){{}}
var bypassBtn=document.getElementById("rl-guide-gate-bypass");
if(bypassBtn)bypassBtn.addEventListener("click",function(){{unlock("manual_bypass");}});
function postLead(payload){{
return fetch(WORKER_URL,{{method:"POST",headers:{{"Content-Type":"application/json"}},body:JSON.stringify(payload)}})
.then(function(r){{if(!r.ok)throw new Error("bad status");return r;}});
}}
var gateForm=document.getElementById("rl-cluster-gate-form");
if(gateForm)gateForm.addEventListener("submit",function(e){{
e.preventDefault();
if(gateForm.website&&gateForm.website.value)return;
var gateBtn=gateForm.querySelector("button[type=submit]");
if(gateBtn)gateBtn.disabled=true;
var gateChapter=gateForm.getAttribute("data-chapter")||"{config.guide_label}";
postLead({{email:gateForm.email.value.trim(),source:SOURCE,brand:BRAND,guide_chapter:gateChapter,persona:getPersona(),website:""}})
.then(function(){{unlock("email_form");}})
.catch(function(){{gateForm.submit();}});
}});
document.querySelectorAll(".rl-guide-email-capture-form").forEach(function(form){{
form.addEventListener("submit",function(e){{
e.preventDefault();
var email=form.email.value.trim();
if(!email||!/^[^\\s@]+@[^\\s@]+\\.[^\\s@]+$/.test(email)){{alert("Please enter a valid email address.");return;}}
if(form.website&&form.website.value)return;
var errEl=form.querySelector(".rl-guide-email-capture-error");
if(errEl)errEl.style.display="none";
postLead({{email:email,source:SOURCE,brand:BRAND,guide_chapter:form.guide_chapter.value,persona:getPersona(),website:form.website.value}})
.then(function(){{
form.style.display="none";
var success=document.getElementById(form.id+"-success");
if(success)success.style.display="block";
track("{event_prefix}_email_capture",{{chapter:form.guide_chapter.value}});
}})
.catch(function(){{
if(!errEl){{
errEl=document.createElement("p");
errEl.className="rl-guide-email-capture-error";
errEl.setAttribute("role","alert");
form.appendChild(errEl);
}}
errEl.textContent="Something went wrong — please try again.";
errEl.style.display="block";
}});
}});
}});
}})();
'''


def build_cluster_js(config: GuideConfig = ROAD_GUIDE) -> str:
    """Return JS additions for the cluster layout (gate form, unlock persistence)."""
    legacy_js = '''
/* ── Guide Cluster Unlock ── */
(function(){
"use strict";
var STORAGE_KEY="rl_guide_unlocked";
function track(n,p){if(typeof gtag==="function")gtag("event",n,Object.assign({transport_type:"beacon"},p||{}));}
function isUnlocked(){try{return localStorage.getItem(STORAGE_KEY)==="1";}catch(e){return false;}}
function unlock(method){
try{localStorage.setItem(STORAGE_KEY,"1");}catch(e){}
document.documentElement.classList.add("rl-guide-unlocked");
var gatedContent=document.querySelector(".rl-cluster-gated-content");
if(gatedContent)gatedContent.style.display="block";
var gate=document.getElementById("rl-guide-gate");
if(gate)gate.style.display="none";
track("guide_gate_unlock",{method:method||"unknown"});
}

/* Check URL param for post-form-submit unlock */
if(new URLSearchParams(window.location.search).get("unlocked")==="1")unlock("email_form");

/* Check localStorage */
if(isUnlocked()){
document.documentElement.classList.add("rl-guide-unlocked");
}

/* Bypass button */
var bypassBtn=document.getElementById("rl-guide-gate-bypass");
if(bypassBtn)bypassBtn.addEventListener("click",function(){unlock("manual_bypass");});

/* Form intercept — set localStorage before formsubmit.co redirect */
var gateForm=document.getElementById("rl-cluster-gate-form");
if(gateForm){
gateForm.addEventListener("submit",function(){
try{localStorage.setItem(STORAGE_KEY,"1");}catch(e){}
track("guide_gate_unlock",{method:"email_form"});
});
}
})();

/* ── End-of-chapter email capture (friend-first-sequences.md §4.2-4.3) ── */
(function(){
"use strict";
var WORKER_URL="https://fueling-lead-intake.gravelgodcoaching.workers.dev";
var forms=document.querySelectorAll(".rl-guide-email-capture-form");
forms.forEach(function(form){
form.addEventListener("submit",function(e){
e.preventDefault();
var email=form.email.value.trim();
if(!email||!/^[^\\s@]+@[^\\s@]+\\.[^\\s@]+$/.test(email)){
alert("Please enter a valid email address.");
return;
}
if(form.website&&form.website.value)return;
var payload={
email:email,
source:"training_guide",
guide_chapter:form.guide_chapter.value,
website:form.website.value
};
try{
var races=JSON.parse(localStorage.getItem("rl_viewed_races")||"[]");
if(Array.isArray(races)&&races.length){
var names=races.map(function(r){return r&&r.name;}).filter(Boolean);
if(names.length)payload.viewed_races=names.slice(0,5);
}
}catch(e2){}
var errEl=form.querySelector(".rl-guide-email-capture-error");
if(errEl)errEl.style.display="none";
fetch(WORKER_URL,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(payload)})
.then(function(r){
if(!r.ok)throw new Error("bad status");
form.style.display="none";
var success=document.getElementById(form.id+"-success");
if(success)success.style.display="block";
})
.catch(function(){
if(!errEl){
errEl=document.createElement("p");
errEl.className="rl-guide-email-capture-error";
errEl.setAttribute("role","alert");
form.appendChild(errEl);
}
errEl.textContent="Something went wrong — please try again.";
errEl.style.display="block";
});
});
});
})();
'''
    if config.gate_form.endpoint_mode is GateEndpointMode.FORM_SUBMIT:
        return legacy_js
    return _build_worker_first_cluster_js(config)


# ── Page Assembly ──────────────────────────────────────────────


def build_head(title: str, description: str, canonical: str,
               css_html: str, jsonld: str, content: dict,
               prev_url: str = None, next_url: str = None) -> str:
    """Build the <head> section for any cluster page."""
    og_image = f"{SITE_BASE_URL}/og/homepage.jpg"

    prev_link = f'\n  <link rel="prev" href="{esc(prev_url)}">' if prev_url else ''
    next_link = f'\n  <link rel="next" href="{esc(next_url)}">' if next_url else ''

    return f'''<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{esc(title)} — Roadie Labs</title>
  <meta name="description" content="{esc(description)}">
  <link rel="canonical" href="{esc(canonical)}">
  {get_preload_hints()}
  {get_ga4_head_snippet()}
  <meta property="og:title" content="{esc(title)}">
  <meta property="og:description" content="{esc(description)}">
  <meta property="og:type" content="article">
  <meta property="og:url" content="{esc(canonical)}">
  <meta property="og:image" content="{esc(og_image)}">
  <meta property="og:site_name" content="Roadie Labs">
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:title" content="{esc(title)}">
  <meta name="twitter:description" content="{esc(description)}">
  <meta name="twitter:image" content="{esc(og_image)}">
  {jsonld}{prev_link}{next_link}
  <style>
{get_tokens_css()}
{get_font_face_css()}
{get_site_header_css()}
{get_mega_footer_css()}
/* Base shell — iPan: warm paper foundation; radii and layered shadows are
   part of the craft layer, so no brutalist reset here. */
.rl-neo-brutalist-page {{
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 20px;
  font-family: var(--rl-font-data);
  background: var(--rl-color-cool-white, #fafaf8);
  color: var(--rl-color-near-black);
  line-height: 1.7;
}}
.rl-neo-brutalist-page *, .rl-neo-brutalist-page *::before, .rl-neo-brutalist-page *::after {{
  box-sizing: border-box;
}}
.rl-breadcrumb {{ padding: 8px 24px; font-size: 11px; background: var(--rl-color-silver); }}
.rl-breadcrumb a {{ color: var(--rl-color-coral); text-decoration: none; }}
.rl-breadcrumb a:hover {{ color: var(--rl-color-orange); }}
.rl-breadcrumb-sep {{ color: var(--rl-color-secondary-blue); margin: 0 6px; }}
.rl-breadcrumb-current {{ color: var(--rl-color-near-black); }}
/* Hero */
.rl-hero {{ background: var(--rl-color-primary-navy); color: var(--rl-color-white); padding: 60px 40px; border-radius: 0 0 12px 12px; margin-bottom: 0; }}
.rl-hero-tier {{ display: inline-block; background: rgba(255,255,255,0.08); color: var(--rl-color-light-steel); padding: 4px 12px; border-radius: 9999px; font-size: 10px; font-weight: 600; letter-spacing: 0.14em; text-transform: uppercase; margin-bottom: 16px; }}
.rl-hero h1 {{ font-family: var(--rl-font-editorial); font-size: 42px; font-weight: 700; line-height: 1.1; text-transform: uppercase; letter-spacing: -0.5px; margin-bottom: 16px; color: var(--rl-color-white); }}
.rl-hero-tagline {{ font-size: 14px; line-height: 1.6; color: var(--rl-color-light-steel); max-width: 700px; }}
@media(max-width:768px){{
  .rl-hero {{ padding: 40px 20px; }}
  .rl-hero h1 {{ font-size: 26px; }}
  .rl-breadcrumb {{ font-size: 10px; }}
}}
  </style>
  {css_html}
</head>'''


def build_persona_quiz(content: dict, config: GuideConfig = ROAD_GUIDE) -> str:
    """Build the two-question 'find your track' quiz for the pillar page.

    Two axes, deliberately: the event answer picks the *track* (which arc you
    read), the hours answer picks the *rider type* (which inline variants you
    see). Both persist to localStorage so every chapter page downstream and
    every lead-capture payload knows who it's talking to.
    """
    tracks_by_persona = {
        t.get("persona"): t for t in content.get("tracks", []) if t.get("persona")
    }
    crit_track = tracks_by_persona.get("crit-racer")
    if not crit_track:
        return ""
    track_url = _guide_url(config, crit_track["id"])
    ch1_url = _guide_url(config, "what-is-road-racing")
    ch2_url = _guide_url(config, "choosing-your-race")
    persona_key = f"{config.local_storage_key_prefix}_persona"
    event_prefix = config.ga4_event_label_prefix

    return f'''<div class="rl-guide-quiz" id="rl-guide-quiz">
    <div class="rl-guide-quiz-kicker">FIND YOUR TRACK</div>
    <h3 class="rl-guide-quiz-title">Two questions, then the right way through this guide</h3>
    <div class="rl-guide-quiz-q" data-q="event">
      <div class="rl-guide-quiz-q-label">What are you actually training for?</div>
      <div class="rl-guide-quiz-options">
        <button class="rl-guide-quiz-opt" data-value="crit-racer">Crits or short circuit races</button>
        <button class="rl-guide-quiz-opt" data-value="tester">Time trials or hillclimbs</button>
        <button class="rl-guide-quiz-opt" data-value="fondo">A fondo, century, or sportive</button>
        <button class="rl-guide-quiz-opt" data-value="mountain">A mountain gran fondo</button>
        <button class="rl-guide-quiz-opt" data-value="unsure">Haven't picked yet</button>
      </div>
    </div>
    <div class="rl-guide-quiz-q" data-q="hours">
      <div class="rl-guide-quiz-q-label">How many hours a week can you actually train?</div>
      <div class="rl-guide-quiz-options">
        <button class="rl-guide-quiz-opt" data-value="autobus">0-5</button>
        <button class="rl-guide-quiz-opt" data-value="finisher">5-12</button>
        <button class="rl-guide-quiz-opt" data-value="sharp-end">12-18</button>
        <button class="rl-guide-quiz-opt" data-value="racer">18+</button>
      </div>
    </div>
    <div class="rl-guide-quiz-result" id="rl-guide-quiz-result" style="display:none">
      <div class="rl-guide-quiz-result-kicker">YOUR TRACK</div>
      <div class="rl-guide-quiz-result-title" id="rl-guide-quiz-result-title"></div>
      <p class="rl-guide-quiz-result-text" id="rl-guide-quiz-result-text"></p>
      <a class="rl-guide-btn rl-guide-btn--primary" id="rl-guide-quiz-result-cta" href="{ch1_url}">START</a>
    </div>
    <p class="rl-guide-quiz-skip">Know your answer already? Go straight to <a href="{track_url}">{esc(crit_track["title"])}</a> or <a href="{ch1_url}">Chapter 1</a>.</p>
  </div>
  <script>
  (function(){{
  "use strict";
  var quiz=document.getElementById("rl-guide-quiz");
  if(!quiz)return;
  var PERSONA_KEY="{persona_key}";
  var picks={{event:null,hours:null}};
  var RESULTS={{
  "crit-racer":{{title:"The Crit Racer's Track",text:"Short, anaerobic, decided in corners. You get a different arc through this guide \\u2014 flat hours, sharpened intensity, and pack craft as the main event.",cta:"START YOUR TRACK",url:"{track_url}"}},
  "tester":{{title:"The Crit Racer's Track (tester's fork)",text:"Same short-event build \\u2014 flat hours, sharpened intensity \\u2014 minus the pack craft, double the pacing discipline. The track calls out your fork where it matters.",cta:"START YOUR TRACK",url:"{track_url}"}},
  "fondo":{{title:"The Standard Arc",text:"The guide was built spine-first for your event. Chapters 1 through 8, in order \\u2014 your weekly structure is set below and follows you through every chapter.",cta:"START CHAPTER 1",url:"{ch1_url}"}},
  "mountain":{{title:"The Standard Arc, Climbing Emphasis",text:"Read in order, but linger in chapter 2 (time cuts, altitude) and chapter 3 (power-to-weight). The mountain decides with arithmetic; arrive knowing yours.",cta:"START CHAPTER 1",url:"{ch1_url}"}},
  "unsure":{{title:"Start Where the Guide Starts: Pick the Race",text:"Chapter 2 exists for exactly this \\u2014 394 rated races, your hours, and an honest match between them. Decide the event first; the training writes itself after.",cta:"CHOOSE YOUR RACE",url:"{ch2_url}"}}
  }};
  function track(n,p){{if(typeof gtag==="function")gtag("event",n,Object.assign({{transport_type:"beacon"}},p||{{}}));}}
  function render(){{
  if(!picks.event||!picks.hours)return;
  try{{localStorage.setItem(PERSONA_KEY,picks.event);}}catch(e){{}}
  try{{localStorage.setItem("rl_guide_rider_type",picks.hours);}}catch(e){{}}
  var riderBtn=document.querySelector('.rl-guide-rider-btn[data-rider="'+picks.hours+'"]');
  if(riderBtn)riderBtn.click();
  var r=RESULTS[picks.event]||RESULTS.unsure;
  document.getElementById("rl-guide-quiz-result-title").textContent=r.title;
  document.getElementById("rl-guide-quiz-result-text").textContent=r.text;
  var cta=document.getElementById("rl-guide-quiz-result-cta");
  cta.textContent=r.cta;cta.href=r.url;
  document.getElementById("rl-guide-quiz-result").style.display="block";
  track("{event_prefix}_quiz_complete",{{persona:picks.event,rider:picks.hours}});
  }}
  quiz.querySelectorAll(".rl-guide-quiz-q").forEach(function(q){{
  var axis=q.getAttribute("data-q");
  q.querySelectorAll(".rl-guide-quiz-opt").forEach(function(b){{
  b.addEventListener("click",function(){{
  q.querySelectorAll(".rl-guide-quiz-opt").forEach(function(o){{o.classList.remove("rl-guide-quiz-opt--active");}});
  b.classList.add("rl-guide-quiz-opt--active");
  picks[axis]=b.getAttribute("data-value");
  render();
  }});
  }});
  }});
  }})();
  </script>'''


def build_track_jsonld(track: dict, content: dict,
                       config: GuideConfig = ROAD_GUIDE) -> str:
    """Article + BreadcrumbList JSON-LD for a rider-track page."""
    canonical = f"{SITE_BASE_URL}{_guide_url(config, track['id'])}"
    article = {
        "@context": "https://schema.org",
        "@type": "Article",
        "headline": track["title"],
        "description": track.get("meta_description", content.get("meta_description", "")),
        "url": canonical,
        "isPartOf": {"@type": "WebPage", "url": f"{SITE_BASE_URL}{_guide_url(config)}"},
        "author": {"@type": "Organization", "name": "Roadie Labs"},
        "publisher": {"@type": "Organization", "name": "Roadie Labs"},
    }
    breadcrumb = {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Home", "item": f"{SITE_BASE_URL}/"},
            {"@type": "ListItem", "position": 2, "name": config.guide_label,
             "item": f"{SITE_BASE_URL}{_guide_url(config)}"},
            {"@type": "ListItem", "position": 3, "name": track["title"], "item": canonical},
        ],
    }
    return (
        f'<script type="application/ld+json">{json.dumps(article)}</script>\n'
        f'<script type="application/ld+json">{json.dumps(breadcrumb)}</script>'
    )


def generate_track_page(track: dict, content: dict,
                        guide_css: str, guide_js: str,
                        cluster_css: str, cluster_js: str, inline: bool,
                        config: GuideConfig = ROAD_GUIDE) -> str:
    """Generate a rider-track page: a persona's curated path through the guide.

    Tracks are free (never gated) — they're the personalization layer that
    routes readers into the shared chapters, not premium content themselves.
    """
    canonical = f"{SITE_BASE_URL}{_guide_url(config, track['id'])}"
    css_html = f'<style>{guide_css}\n{cluster_css}</style>'
    js_html = f'<script>{guide_js}\n{cluster_js}</script>'

    nav = get_site_header_html(active="products")
    breadcrumb = build_chapter_breadcrumb(track, config)
    rider_selector = build_rider_selector(content)
    body = build_chapter_content(track)
    email_capture = build_chapter_email_capture(track)
    finale = _build_config_ctas(config, config.cta_set.finale_blocks)
    jsonld = build_track_jsonld(track, content, config)
    footer = get_mega_footer_html()

    subtitle = esc(track.get("subtitle", ""))
    subtitle_html = f'<p class="rl-guide-chapter-subtitle">{subtitle}</p>' if subtitle else ''
    hero = f'''<div class="rl-guide-chapter-hero rl-guide-chapter-hero--dark">
      <div class="rl-guide-chapter-title-block">
        <span class="rl-guide-chapter-num">RIDER TRACK</span>
        <h2 class="rl-guide-chapter-title">{esc(track["title"])}</h2>
        {subtitle_html}
      </div>
    </div>'''

    back_link = f'''<div class="rl-guide-track-back">
      <a href="{_guide_url(config)}">&larr; All chapters &amp; tracks</a>
    </div>'''

    head = build_head(
        title=track.get("seo_title", f"{track['title']} — {config.guide_label}"),
        description=track.get("meta_description", content.get("meta_description", "")),
        canonical=canonical,
        css_html=css_html,
        jsonld=jsonld,
        content=content,
    )

    return f'''<!DOCTYPE html>
<html lang="en">
{head}
<body>

<div class="rl-neo-brutalist-page" id="rl-guide-page">
  {nav}

  {breadcrumb}

  <div class="rl-guide-chapter" data-track="{esc(track["id"])}">
    {hero}

    {rider_selector}

    {body}

    {email_capture}

    {back_link}
  </div>

  {finale}
</div>

{footer}

{js_html}

<script>{get_site_header_js()}</script>

{get_consent_banner_html()}
</body>
</html>'''


def generate_pillar_page(content: dict, guide_css: str, guide_js: str,
                         cluster_css: str, cluster_js: str, inline: bool,
                         config: GuideConfig = ROAD_GUIDE) -> str:
    """Generate the pillar page HTML."""
    canonical = f"{SITE_BASE_URL}{_guide_url(config)}"

    if inline:
        css_html = f'<style>{guide_css}\n{cluster_css}</style>'
        js_html = f'<script>{guide_js}\n{cluster_js}</script>'
    else:
        css_html = f'<style>{guide_css}\n{cluster_css}</style>'
        js_html = f'<script>{guide_js}\n{cluster_js}</script>'

    nav = get_site_header_html(active="products")
    breadcrumb = f'''<div class="rl-breadcrumb">
    <a href="{SITE_BASE_URL}/">Home</a>
    <span class="rl-breadcrumb-sep">&rsaquo;</span>
    <span class="rl-breadcrumb-current">{esc(config.guide_label)}</span>
  </div>'''

    hero = build_pillar_hero(content)
    persona_quiz = build_persona_quiz(content, config)
    rider_selector = build_rider_selector(content)
    chapter_grid = build_chapter_grid(content["chapters"], config)
    ctas = build_pillar_cta_section(config)
    finale = _build_config_ctas(config, config.cta_set.finale_blocks)
    jsonld = build_pillar_jsonld(content, config)
    footer = get_mega_footer_html()

    head = build_head(
        title=content["title"],
        description=content["meta_description"],
        canonical=canonical,
        css_html=css_html,
        jsonld=jsonld,
        content=content,
    )

    return f'''<!DOCTYPE html>
<html lang="en">
{head}
<body>

<div class="rl-neo-brutalist-page" id="rl-guide-page">
  {nav}

  {breadcrumb}

  {hero}

  {persona_quiz}

  {rider_selector}

  {chapter_grid}

  {ctas}

  {finale}
</div>

{footer}

{js_html}

<script>{get_site_header_js()}</script>

{get_consent_banner_html()}
</body>
</html>'''


def generate_chapter_page(chapter: dict, chapters: list, content: dict,
                          guide_css: str, guide_js: str,
                          cluster_css: str, cluster_js: str, inline: bool,
                          config: GuideConfig = ROAD_GUIDE) -> str:
    """Generate a single chapter page HTML."""
    ch_id = chapter["id"]
    canonical = f"{SITE_BASE_URL}{_guide_url(config, ch_id)}"
    num = chapter["number"]

    meta = config.chapter_meta.get(ch_id, {})
    title = meta.get("title_suffix", f"Chapter {num}: {chapter['title']}")
    description = meta.get("description", content.get("meta_description", ""))

    if inline:
        css_html = f'<style>{guide_css}\n{cluster_css}</style>'
        js_html = f'<script>{guide_js}\n{cluster_js}</script>'
    else:
        css_html = f'<style>{guide_css}\n{cluster_css}</style>'
        js_html = f'<script>{guide_js}\n{cluster_js}</script>'

    # Prev/next URLs
    prev_url = None
    next_url = None
    for ch in chapters:
        if ch["number"] == num - 1:
            prev_url = f"{SITE_BASE_URL}{_guide_url(config, ch['id'])}"
        if ch["number"] == num + 1:
            next_url = f"{SITE_BASE_URL}{_guide_url(config, ch['id'])}"

    nav = get_site_header_html(active="products")
    breadcrumb = build_chapter_breadcrumb(chapter, config)
    progress = build_chapter_progress(chapter, chapters)
    hero = build_chapter_hero(chapter)
    rider_selector = build_rider_selector(content)
    chapter_content = build_chapter_content(chapter)
    email_capture = build_chapter_email_capture(chapter)
    prev_next = build_prev_next_nav(chapter, chapters, config)
    jsonld = build_chapter_jsonld(chapter, content, config)
    footer = get_mega_footer_html()

    head = build_head(
        title=title,
        description=description,
        canonical=canonical,
        css_html=css_html,
        jsonld=jsonld,
        content=content,
        prev_url=prev_url,
        next_url=next_url,
    )

    # Gated chapters wrap content behind gate
    is_gated = chapter.get("gated", False)
    if is_gated:
        gate_html = build_chapter_gate(chapter, config)
        body_content = f'''
  {gate_html}
  <div class="rl-cluster-gated-content">
    {chapter_content}

    {email_capture}

    {prev_next}
  </div>'''
    else:
        body_content = f'''
    {chapter_content}

    {email_capture}

    {prev_next}'''

    # CTA after chapter, from the configured, truth-preserving CTA inventory.
    cta_html = ''
    cta_type = chapter.get("cta_after")
    if cta_type == "finale":
        cta_html = _build_config_ctas(config, config.cta_set.finale_blocks)
    elif cta_type and cta_type != "gate" and cta_type in config.cta_set.pillar_blocks:
        cta_html = _build_config_ctas(config, (cta_type,))

    return f'''<!DOCTYPE html>
<html lang="en">
{head}
<body>

<div class="rl-neo-brutalist-page" id="rl-guide-page">
  {nav}

  {breadcrumb}

  {progress}

  <div class="rl-guide-chapter" data-chapter="{num}">
    {hero}

    {rider_selector}

    {body_content}
  </div>

  {cta_html}
</div>

{footer}

{js_html}

<script>{get_site_header_js()}</script>

{get_consent_banner_html()}
</body>
</html>'''


# ── Configurator Page ─────────────────────────────────────────


def _race_count() -> int:
    """Return the number of races in the race index."""
    idx = generate_guide._RACE_INDEX
    if idx:
        return len(idx)
    return len(generate_guide.load_race_index())


def build_configurator_race_data() -> str:
    """Build slimmed race data as inline JS variable for the configurator."""
    race_index = generate_guide._RACE_INDEX or generate_guide.load_race_index()
    slim = []
    for slug, r in sorted(race_index.items()):
        slim.append({
            "n": r["name"],
            "s": slug,
            "d": r.get("distance_mi", 0),
            "e": r.get("elevation_ft", 0),
            "t": r.get("tier", 0),
            "m": r.get("month", ""),
            "cl": r.get("scores", {}).get("climate", 0),
            "te": r.get("scores", {}).get("technicality", 0),
            "ad": r.get("scores", {}).get("adventure", 0),
            "pr": r.get("scores", {}).get("prestige", 0),
            "u": r.get("profile_url", f"/race/{slug}/"),
        })
    return f'var GG_RACES={_safe_json_for_script(slim, ensure_ascii=False, separators=(",",":"))};'


def build_configurator_body() -> str:
    """Build the configurator form and output HTML."""
    count = _race_count()
    return f'''
  <div class="rl-configurator" id="rl-configurator">
    <div class="rl-configurator__form">
      <div class="rl-configurator__step">
        <label class="rl-configurator__label" for="rl-cfg-race">1. SELECT YOUR RACE</label>
        <div class="rl-configurator__search-wrap">
          <input type="text" id="rl-cfg-race-search" class="rl-configurator__search"
                 placeholder="Search {count} races..." autocomplete="off"
                 aria-label="Search races">
          <select id="rl-cfg-race" class="rl-configurator__select" aria-label="Select your race">
            <option value="">Choose a race...</option>
          </select>
        </div>
      </div>

      <div class="rl-configurator__step">
        <span class="rl-configurator__label">2. YOUR RIDER TYPE</span>
        <div class="rl-configurator__riders" id="rl-cfg-riders" role="radiogroup" aria-label="Select rider type">
          <button class="rl-configurator__rider-btn" data-rider="ayahuasca" role="radio" aria-checked="false">
            <span class="rl-configurator__rider-name">Ayahuasca</span>
            <span class="rl-configurator__rider-hours">0-5 hrs/wk</span>
          </button>
          <button class="rl-configurator__rider-btn rl-configurator__rider-btn--active" data-rider="finisher" role="radio" aria-checked="true">
            <span class="rl-configurator__rider-name">Finisher</span>
            <span class="rl-configurator__rider-hours">5-8 hrs/wk</span>
          </button>
          <button class="rl-configurator__rider-btn" data-rider="competitor" role="radio" aria-checked="false">
            <span class="rl-configurator__rider-name">Competitor</span>
            <span class="rl-configurator__rider-hours">8-12 hrs/wk</span>
          </button>
          <button class="rl-configurator__rider-btn" data-rider="podium" role="radio" aria-checked="false">
            <span class="rl-configurator__rider-name">Podium</span>
            <span class="rl-configurator__rider-hours">12+ hrs/wk</span>
          </button>
        </div>
      </div>

      <div class="rl-configurator__step">
        <label class="rl-configurator__label" for="rl-cfg-date">3. RACE DATE</label>
        <input type="date" id="rl-cfg-date" class="rl-configurator__date" aria-label="Race date">
      </div>

      <button class="rl-configurator__generate" id="rl-cfg-generate">GENERATE PREP PLAN</button>
    </div>

    <div class="rl-configurator__output" id="rl-cfg-output" style="display:none">
      <div class="rl-configurator__output-header">
        <span class="rl-configurator__output-kicker">YOUR PERSONALIZED PREP PLAN</span>
        <h2 class="rl-configurator__output-race" id="rl-cfg-out-race"></h2>
        <div class="rl-configurator__output-meta" id="rl-cfg-out-meta"></div>
      </div>

      <div class="rl-configurator__cards">
        <div class="rl-configurator__card" id="rl-cfg-card-training">
          <div class="rl-configurator__card-header">TRAINING</div>
          <div class="rl-configurator__card-body" id="rl-cfg-out-training"></div>
        </div>
        <div class="rl-configurator__card" id="rl-cfg-card-nutrition">
          <div class="rl-configurator__card-header">NUTRITION</div>
          <div class="rl-configurator__card-body" id="rl-cfg-out-nutrition"></div>
        </div>
        <div class="rl-configurator__card" id="rl-cfg-card-hydration">
          <div class="rl-configurator__card-header">HYDRATION</div>
          <div class="rl-configurator__card-body" id="rl-cfg-out-hydration"></div>
        </div>
        <div class="rl-configurator__card" id="rl-cfg-card-gear">
          <div class="rl-configurator__card-header">GEAR</div>
          <div class="rl-configurator__card-body" id="rl-cfg-out-gear"></div>
        </div>
        <div class="rl-configurator__card" id="rl-cfg-card-mental">
          <div class="rl-configurator__card-header">MENTAL PREP</div>
          <div class="rl-configurator__card-body" id="rl-cfg-out-mental"></div>
        </div>
      </div>

      <div class="rl-configurator__link" id="rl-cfg-out-link"></div>
    </div>
  </div>'''


def build_configurator_css() -> str:
    """Return CSS for the configurator page."""
    return '''
/* ── Configurator ── */
.rl-configurator{max-width:720px;margin:0 auto 40px;padding:0 16px}
.rl-configurator__form{display:flex;flex-direction:column;gap:24px}
.rl-configurator__step{display:flex;flex-direction:column;gap:8px}
.rl-configurator__label{font-family:var(--rl-font-data);font-size:11px;font-weight:700;letter-spacing:2px;color:var(--rl-color-secondary-blue)}
.rl-configurator__search-wrap{display:flex;flex-direction:column;gap:8px}
.rl-configurator__search,.rl-configurator__select,.rl-configurator__date{padding:12px 16px;border:1px solid var(--rl-hairline-strong,rgba(0,0,0,0.12));border-radius:4px;font-family:var(--rl-font-data);font-size:13px;background:var(--rl-color-cool-white);color:var(--rl-color-near-black);width:100%;box-sizing:border-box}
.rl-configurator__search::placeholder{color:var(--rl-color-secondary-blue)}
.rl-configurator__riders{display:grid;grid-template-columns:repeat(4,1fr);gap:0}
.rl-configurator__rider-btn{padding:12px 8px;border:1px solid var(--rl-hairline-strong,rgba(0,0,0,0.12));border-radius:6px;background:var(--rl-color-cool-white);cursor:pointer;text-align:center;display:flex;flex-direction:column;gap:2px;transition:background 0.15s}
.rl-configurator__rider-btn+.rl-configurator__rider-btn{border-left:none}
.rl-configurator__rider-btn:hover{background:var(--rl-color-silver)}
.rl-configurator__rider-btn--active{background:var(--rl-color-near-black);color:var(--rl-color-cool-white)}
.rl-configurator__rider-btn--active .rl-configurator__rider-name{color:var(--rl-color-cool-white)}
.rl-configurator__rider-btn--active .rl-configurator__rider-hours{color:var(--rl-color-light-steel)}
.rl-configurator__rider-name{font-family:var(--rl-font-data);font-size:11px;font-weight:700;letter-spacing:1px;color:var(--rl-color-primary-navy)}
.rl-configurator__rider-hours{font-family:var(--rl-font-data);font-size:9px;color:var(--rl-color-secondary-blue)}
.rl-configurator__generate{padding:14px 24px;border:none;border-radius:4px;background:var(--rl-cobalt,#4a78b0);color:var(--rl-color-cool-white);font-family:var(--rl-font-data);font-size:13px;font-weight:700;letter-spacing:2px;cursor:pointer;transition:background 0.15s;margin-top:8px}
.rl-configurator__generate:hover{background:var(--rl-color-primary-navy)}

/* Output */
.rl-configurator__output{margin-top:32px;border:1px solid var(--rl-hairline,rgba(0,0,0,0.06));border-radius:8px;overflow:hidden;box-shadow:var(--rl-shadow-card,0 2px 4px rgba(0,0,0,0.06))}
.rl-configurator__output-header{background:var(--rl-color-near-black);padding:20px 24px;color:var(--rl-color-cool-white)}
.rl-configurator__output-kicker{font-family:var(--rl-font-data);font-size:10px;letter-spacing:3px;color:var(--rl-color-signal-red)}
.rl-configurator__output-race{font-family:var(--rl-font-editorial);font-size:24px;font-weight:700;margin:8px 0 4px;color:var(--rl-color-cool-white)}
.rl-configurator__output-meta{font-family:var(--rl-font-data);font-size:11px;color:var(--rl-color-light-steel)}
.rl-configurator__cards{display:grid;grid-template-columns:1fr 1fr;gap:0}
.rl-configurator__card{border-bottom:2px solid var(--rl-color-light-steel);border-right:2px solid var(--rl-color-light-steel)}
.rl-configurator__card:nth-child(even){border-right:none}
.rl-configurator__card:last-child,.rl-configurator__card:nth-last-child(2):nth-child(odd){border-bottom:none}
.rl-configurator__card-header{padding:10px 16px;background:var(--rl-color-silver);font-family:var(--rl-font-data);font-size:10px;font-weight:700;letter-spacing:2px;color:var(--rl-color-secondary-blue);border-bottom:1px solid var(--rl-color-light-steel)}
.rl-configurator__card-body{padding:16px;font-family:var(--rl-font-editorial);font-size:14px;color:var(--rl-color-primary-navy);line-height:1.6}
.rl-configurator__card-body strong{font-family:var(--rl-font-data);font-size:12px;display:block;margin-bottom:4px;color:var(--rl-color-signal-red)}
.rl-configurator__link{padding:16px 24px;text-align:center;background:var(--rl-color-silver);border-top:2px solid var(--rl-color-light-steel)}
.rl-configurator__link a{color:var(--rl-color-signal-red);font-family:var(--rl-font-data);font-size:12px;font-weight:700;letter-spacing:1px}

@media print{
.rl-configurator__form{display:none}
.rl-configurator__output{border:1px solid #333}
}
@media(max-width:768px){
.rl-configurator__riders{grid-template-columns:repeat(2,1fr)}

.rl-configurator__rider-btn:nth-child(n+3){border-top:none}
.rl-configurator__cards{grid-template-columns:1fr}
.rl-configurator__card{border-right:none}
.rl-configurator__output-race{font-size:20px}
}
'''


def build_configurator_js() -> str:
    """Return JS for the configurator page interactivity."""
    return '''
/* ── Race Prep Configurator ── */
(function(){
"use strict";
if(typeof GG_RACES==="undefined")return;
function track(n,p){if(typeof gtag==="function")gtag("event",n,Object.assign({transport_type:"beacon"},p||{}));}
function escHtml(s){var d=document.createElement("div");d.textContent=s;return d.innerHTML;}
function $(id){return document.getElementById(id);}

var raceSelect=$("rl-cfg-race");
var raceSearch=$("rl-cfg-race-search");
var dateInput=$("rl-cfg-date");
var generateBtn=$("rl-cfg-generate");
var output=$("rl-cfg-output");
var riderBtns=document.querySelectorAll(".rl-configurator__rider-btn");
if(!raceSelect||!generateBtn||!output)return;

/* Populate race dropdown */
var allOpts=[];
GG_RACES.forEach(function(r){
var opt=document.createElement("option");
opt.value=r.s;
opt.textContent=r.n+" (T"+r.t+", "+r.d+" mi)";
opt.setAttribute("data-name",r.n.toLowerCase());
raceSelect.appendChild(opt);
allOpts.push(opt);
});

/* Search filter — remove/re-add options for Safari compat (display:none on <option> is non-standard) */
if(raceSearch){
var placeholder=raceSelect.querySelector("option:first-child");
raceSearch.addEventListener("input",function(){
var q=raceSearch.value.toLowerCase();
while(raceSelect.options.length>1)raceSelect.removeChild(raceSelect.lastChild);
allOpts.forEach(function(o){
if(!q||(o.getAttribute("data-name")||"").indexOf(q)>=0)raceSelect.appendChild(o);
});
});
}

/* Rider type buttons */
var validRiders=["ayahuasca","finisher","competitor","podium"];
var selectedRider="finisher";
function setActiveRider(rider){
if(validRiders.indexOf(rider)<0)return;
selectedRider=rider;
riderBtns.forEach(function(b){
var m=b.getAttribute("data-rider")===rider;
b.classList.toggle("rl-configurator__rider-btn--active",m);
b.setAttribute("aria-checked",m?"true":"false");
});
try{localStorage.setItem("rl_guide_rider_type",rider);}catch(e){}
}
riderBtns.forEach(function(btn){
btn.addEventListener("click",function(){setActiveRider(btn.getAttribute("data-rider"));});
});

/* Arrow key navigation for ARIA radiogroup */
var ridersContainer=$("rl-cfg-riders");
if(ridersContainer){
ridersContainer.addEventListener("keydown",function(e){
var btns=Array.prototype.slice.call(riderBtns);
var idx=btns.indexOf(document.activeElement);
if(idx<0)return;
if(e.key==="ArrowRight"||e.key==="ArrowDown"){e.preventDefault();var next=btns[(idx+1)%btns.length];next.focus();setActiveRider(next.getAttribute("data-rider"));}
else if(e.key==="ArrowLeft"||e.key==="ArrowUp"){e.preventDefault();var prev=btns[(idx-1+btns.length)%btns.length];prev.focus();setActiveRider(prev.getAttribute("data-rider"));}
});
}

/* Restore rider type from guide selector */
try{var saved=localStorage.getItem("rl_guide_rider_type");if(saved&&validRiders.indexOf(saved)>=0){setActiveRider(saved);}}catch(e){}

/* Generate plan */
generateBtn.addEventListener("click",function(){
var slug=raceSelect.value;
if(!slug){raceSelect.focus();return;}
var race=GG_RACES.find(function(r){return r.s===slug;});
if(!race)return;

var weeksOut=0;
if(dateInput&&dateInput.value){
var raceDate=new Date(dateInput.value);
var now=new Date();
weeksOut=Math.max(0,Math.round((raceDate-now)/(7*24*60*60*1000)));
}

/* Header */
var outRace=$("rl-cfg-out-race");
var outMeta=$("rl-cfg-out-meta");
if(outRace)outRace.textContent=race.n;
var elev=typeof race.e==="number"?race.e.toLocaleString():String(race.e||0);
var metaParts=["Tier "+race.t,race.d+" miles",elev+"ft elevation"];
if(weeksOut>0)metaParts.push(weeksOut+" weeks out");
if(outMeta)outMeta.textContent=metaParts.join(" \\u00b7 ");

/* Training */
var trainingHtml="";
var phases={ayahuasca:{base:0.5,build:0.3,peak:0.2},finisher:{base:0.4,build:0.35,peak:0.25},competitor:{base:0.35,build:0.35,peak:0.3},podium:{base:0.3,build:0.35,peak:0.35}};
var ph=phases[selectedRider]||phases.finisher;
if(weeksOut>=12){
var bw=Math.round(weeksOut*ph.base),buw=Math.round(weeksOut*ph.build),pw=Math.max(1,weeksOut-bw-buw);
trainingHtml="<strong>Phase Plan ("+weeksOut+" weeks)</strong>Base: "+bw+" weeks \\u2022 Build: "+buw+" weeks \\u2022 Peak/Taper: "+pw+" weeks";
}else if(weeksOut>=4){
trainingHtml="<strong>Compressed Plan ("+weeksOut+" weeks)</strong>Focus on race-specific intensity. Skip extended base phase. Maintain volume, sharpen fitness.";
}else if(weeksOut>0){
trainingHtml="<strong>Taper Mode ("+weeksOut+" weeks)</strong>Reduce volume "+({ayahuasca:"30%",finisher:"40%",competitor:"50%",podium:"60%"}[selectedRider]||"40%")+". Keep 1-2 short openers at race pace.";
}else{
trainingHtml="<strong>Training Recommendation</strong>Set your race date above for a phased training plan tailored to your timeline.";
}
var outTraining=$("rl-cfg-out-training");
if(outTraining)outTraining.innerHTML=trainingHtml;

/* Nutrition */
var carbLo={ayahuasca:30,finisher:40,competitor:60,podium:80};
var carbHi={ayahuasca:40,finisher:60,competitor:90,podium:120};
var lo=carbLo[selectedRider]||40,hi=carbHi[selectedRider]||60;
var estHours=Math.max(1,Math.round(race.d/16+0.5));
if(race.d<=0)estHours=0;
var nutHtml="<strong>Target Fueling</strong>"+lo+"\\u2013"+hi+"g/hr for ~"+estHours+" hours";
nutHtml+="<br><strong>Est. Total Carbs</strong>"+Math.round(lo*estHours)+"\\u2013"+Math.round(hi*estHours)+"g";
var outNutrition=$("rl-cfg-out-nutrition");
if(outNutrition)outNutrition.innerHTML=nutHtml;

/* Hydration */
var climateLabels=["N/A","Mild","Moderate","Variable","Challenging","Extreme"];
var fluidLo={0:500,1:500,2:500,3:600,4:700,5:800};
var fluidHi={0:700,1:700,2:700,3:800,4:1000,5:1200};
var cl=race.cl||0;
var hydHtml="<strong>Climate: "+climateLabels[cl>0?cl:0]+" ("+(cl||"N/A")+"/5)</strong>";
var flo=fluidLo[cl]||500,fhi=fluidHi[cl]||700;
hydHtml+="Target "+flo+"\\u2013"+fhi+"ml/hr with electrolytes";
hydHtml+="<br><strong>Est. Total</strong>"+Math.round(estHours*flo/1000*10)/10+"\\u2013"+Math.round(estHours*fhi/1000*10)/10+"L";
var outHydration=$("rl-cfg-out-hydration");
if(outHydration)outHydration.innerHTML=hydHtml;

/* Gear */
var techLabels=["N/A","Smooth tarmac","Good roads","Mixed quality","Rough roads","Cobbles & dirt"];
var tireRecs={0:"38-42mm all-purpose",1:"32-38mm slick",2:"38-42mm semi-slick",3:"40-45mm mixed tread",4:"42-50mm aggressive tread",5:"45-50mm+ knobby"};
var te=race.te||0;
var gearHtml="<strong>Terrain: "+techLabels[te>0?te:0]+" ("+(te||"N/A")+"/5)</strong>";
gearHtml+="Tire rec: "+(tireRecs[te]||tireRecs[0]);
if(te>=4)gearHtml+="<br>Consider: dropper post, frame bags, extra spares";
if(race.d>150)gearHtml+="<br>Ultra distance: frame/saddle bags, lighting, emergency blanket";
var outGear=$("rl-cfg-out-gear");
if(outGear)outGear.innerHTML=gearHtml;

/* Mental */
var mentalHtml="";
if(race.pr>=4){
mentalHtml="<strong>High Prestige Event ("+race.pr+"/5)</strong>Big stage, big field. Pre-visualize key sections. Have a tactical plan and a backup plan.";
}else{
mentalHtml="<strong>Adventure Score: "+(race.ad||0)+"/5</strong>";
}
if(race.ad>=4)mentalHtml+="<br>Epic adventure race. Focus on the experience, not just the clock. Set process goals alongside time goals.";
if(race.d>200)mentalHtml+="<br><strong>Ultra Mindset</strong>Break into segments. Have mantras for each phase. Plan sleep strategy if overnight.";
else if(race.d>100)mentalHtml+="<br>Long day in the saddle. Negative-split your effort. Save mental energy for the final third.";
else mentalHtml+="<br>Short and sharp. Start controlled, finish strong.";
var outMental=$("rl-cfg-out-mental");
if(outMental)outMental.innerHTML=mentalHtml;

/* Prep kit link — use DOM API instead of innerHTML to prevent XSS from race names */
var outLink=$("rl-cfg-out-link");
if(outLink){
outLink.textContent="";
var a=document.createElement("a");
a.href=race.u;
a.textContent="View full race profile for "+race.n+" \\u2192";
outLink.appendChild(a);
}

output.style.display="block";
output.scrollIntoView({behavior:"smooth",block:"start"});
track("configurator_plan_generated",{race:slug,rider:selectedRider,weeks:weeksOut});
});

raceSelect.addEventListener("change",function(){
track("configurator_race_selected",{race:raceSelect.value});
});
})();
'''


def build_configurator_jsonld(config: GuideConfig = ROAD_GUIDE) -> str:
    """Build JSON-LD for the configurator page."""
    canonical = f"{SITE_BASE_URL}{_guide_url(config, 'race-prep-configurator')}"
    og_image = f"{SITE_BASE_URL}/og/homepage.jpg"

    article = {
        "@context": "https://schema.org",
        "@type": "WebApplication",
        "name": "Road Race Prep Configurator",
        "description": "Generate a personalized race preparation plan based on your target race, rider type, and timeline.",
        "url": canonical,
        "applicationCategory": "SportsApplication",
        "operatingSystem": "Web",
        "provider": {
            "@type": "Organization",
            "name": "Roadie Labs",
            "url": SITE_BASE_URL,
        },
        "image": og_image,
    }

    breadcrumb = {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Home",
             "item": f"{SITE_BASE_URL}/"},
            {"@type": "ListItem", "position": 2, "name": config.guide_label,
             "item": f"{SITE_BASE_URL}{_guide_url(config)}"},
            {"@type": "ListItem", "position": 3, "name": "Race Prep Configurator",
             "item": canonical},
        ]
    }

    return (f'<script type="application/ld+json">{_safe_json_for_script(article, ensure_ascii=False)}</script>\n'
            f'<script type="application/ld+json">{_safe_json_for_script(breadcrumb, ensure_ascii=False)}</script>')


def generate_configurator_page(content: dict, guide_css: str, guide_js: str,
                                cluster_css: str, cluster_js: str, inline: bool,
                                config: GuideConfig = ROAD_GUIDE) -> str:
    """Generate the race prep configurator page HTML."""
    # Ported from the gravel repo but never adapted: the body/JS still use
    # gravel rider ids, gravel demand-score keys (climate/technicality/
    # adventure), and gravel gear recommendations. Blocked until a road
    # version exists so flipping include_configurator can't publish it.
    raise NotImplementedError(
        "The race-prep configurator has not been ported for road: its rider "
        "types, demand scores, and gear logic are still gravel-specific. "
        "Port build_configurator_body/js/race_data before enabling."
    )
    canonical = f"{SITE_BASE_URL}{_guide_url(config, 'race-prep-configurator')}"
    cfg_css = build_configurator_css()
    cfg_js = build_configurator_js()
    race_data_js = build_configurator_race_data()

    css_html = f'<style>{guide_css}\n{cluster_css}\n{cfg_css}</style>'
    js_html = f'<script>{race_data_js}</script>\n<script>{guide_js}\n{cluster_js}\n{cfg_js}</script>'

    nav = get_site_header_html(active="products")
    breadcrumb = f'''<div class="rl-breadcrumb">
    <a href="{SITE_BASE_URL}/">Home</a>
    <span class="rl-breadcrumb-sep">&rsaquo;</span>
    <a href="{SITE_BASE_URL}{_guide_url(config)}">{esc(config.guide_label)}</a>
    <span class="rl-breadcrumb-sep">&rsaquo;</span>
    <span class="rl-breadcrumb-current">Race Prep Configurator</span>
  </div>'''

    hero = f'''<div class="rl-hero" style="text-align:center;padding:40px 24px 24px">
    <h1 style="font-family:var(--rl-font-editorial);font-size:28px;font-weight:700;color:var(--rl-color-primary-navy);margin:0 0 8px">Race Prep Configurator</h1>
    <p style="font-family:var(--rl-font-editorial);font-size:16px;color:var(--rl-color-secondary-blue);margin:0;max-width:560px;display:inline-block">Select your race, rider type, and timeline. Get a personalized preparation plan covering training, nutrition, hydration, gear, and mental prep.</p>
  </div>'''

    body_html = build_configurator_body()
    gate_html = build_chapter_gate(
        {"title": "Race Prep Configurator", "id": "race-prep-configurator"}, config
    )
    jsonld = build_configurator_jsonld(config)
    footer = get_mega_footer_html()

    head = build_head(
        title="Race Prep Configurator — Roadie Labs Training Guide",
        description=f"Generate a personalized road race preparation plan. Select your target race from {_race_count()} scored events, set your rider type and timeline, and get tailored training, nutrition, and gear recommendations.",
        canonical=canonical,
        css_html=css_html,
        jsonld=jsonld,
        content=content,
    )

    return f'''<!DOCTYPE html>
<html lang="en">
{head}
<body>

<div class="rl-neo-brutalist-page" id="rl-guide-page">
  {nav}

  {breadcrumb}

  {hero}

  {gate_html}
  <div class="rl-cluster-gated-content">
    {body_html}
  </div>
</div>

{footer}

{js_html}

<script>{get_site_header_js()}</script>

{get_consent_banner_html()}
</body>
</html>'''


# ── Main ───────────────────────────────────────────────────────


def _guide_js_for_config(config: GuideConfig) -> str:
    """Namespace guide interactions under this guide's storage/analytics prefix."""
    guide_js = build_guide_js()
    return (guide_js
            .replace("rl_guide_unlocked", f"{config.local_storage_key_prefix}_unlocked")
            .replace('"guide_', f'"{config.ga4_event_label_prefix}_'))


def generate_cluster(output_dir: Path = None, inline: bool = False,
                     config: GuideConfig = ROAD_GUIDE) -> bool:
    """Generate one configured guide cluster; skip missing skeleton content clearly."""
    if output_dir is None:
        output_dir = config.output_dir
    if not config.content_path.exists():
        print(f"Skipping guide '{config.key}': content file not found: {config.content_path}")
        return False
    output_dir.mkdir(parents=True, exist_ok=True)

    content = load_content(config)
    chapters = content["chapters"]
    print(f"Loaded {len(chapters)} chapters from {config.content_path}")

    # Activate glossary for tooltip resolution
    if config.glossary_source == config.content_path:
        generate_guide._GLOSSARY = content.get("glossary")
    elif config.glossary_source.exists():
        generate_guide._GLOSSARY = json.loads(
            config.glossary_source.read_text(encoding="utf-8")
        ).get("glossary")
    else:
        print(f"Warning: glossary source not found for guide '{config.key}': {config.glossary_source}")
        generate_guide._GLOSSARY = None
    # Load race index for race-connected block renderers
    generate_guide._RACE_INDEX = generate_guide.load_race_index()
    # Valid rider-type ids come from the content's personalization block
    rider_types = [rt.get("id") for rt in content.get("personalization", {}).get("rider_types", [])]
    generate_guide._RIDER_TYPES = [rt for rt in rider_types if rt] or None

    # Build CSS/JS once
    guide_css = build_guide_css()
    guide_js = _guide_js_for_config(config)
    cluster_css = build_cluster_css()
    cluster_js = build_cluster_js(config)

    # 1. Generate pillar page
    pillar_dir = output_dir
    pillar_dir.mkdir(parents=True, exist_ok=True)
    pillar_html = generate_pillar_page(content, guide_css, guide_js,
                                        cluster_css, cluster_js, inline, config)
    pillar_file = pillar_dir / "index.html"
    pillar_file.write_text(pillar_html, encoding="utf-8")
    print(f"  Pillar: {pillar_file} ({len(pillar_html):,} bytes)")

    # 2. Generate each chapter page
    for chapter in chapters:
        ch_slug = chapter["id"]
        ch_dir = output_dir / ch_slug
        ch_dir.mkdir(parents=True, exist_ok=True)
        ch_html = generate_chapter_page(chapter, chapters, content,
                                         guide_css, guide_js,
                                         cluster_css, cluster_js, inline, config)
        ch_file = ch_dir / "index.html"
        ch_file.write_text(ch_html, encoding="utf-8")
        gated_label = " (gated)" if chapter.get("gated") else " (free)"
        print(f"  Ch {chapter['number']}: {ch_file} ({len(ch_html):,} bytes){gated_label}")

    # 3. Generate rider-track pages (free persona paths through the chapters)
    for track in content.get("tracks", []):
        t_dir = output_dir / track["id"]
        t_dir.mkdir(parents=True, exist_ok=True)
        t_html = generate_track_page(track, content, guide_css, guide_js,
                                     cluster_css, cluster_js, inline, config)
        t_file = t_dir / "index.html"
        t_file.write_text(t_html, encoding="utf-8")
        print(f"  Track: {t_file} ({len(t_html):,} bytes) (free)")

    page_count = 1 + len(chapters) + len(content.get("tracks", []))
    if config.include_configurator:
        cfg_dir = output_dir / "race-prep-configurator"
        cfg_dir.mkdir(parents=True, exist_ok=True)
        cfg_html = generate_configurator_page(content, guide_css, guide_js,
                                               cluster_css, cluster_js, inline, config)
        cfg_file = cfg_dir / "index.html"
        cfg_file.write_text(cfg_html, encoding="utf-8")
        print(f"  Configurator: {cfg_file} ({len(cfg_html):,} bytes) (gated)")
        page_count += 1

    print(f"\nGenerated {page_count} pages in {output_dir}")
    return True


def main():
    parser = argparse.ArgumentParser(description="Generate a configured Roadie Labs guide cluster")
    parser.add_argument("--guide", choices=sorted(GUIDE_CONFIGS), default=ROAD_GUIDE.key,
                        help="Guide configuration to render (default: road)")
    parser.add_argument("--output-dir", default=None,
                        help="Output directory (defaults to the selected guide configuration)")
    parser.add_argument("--inline", action="store_true",
                        help="Inline CSS/JS for local preview")
    args = parser.parse_args()

    generate_cluster(output_dir=Path(args.output_dir) if args.output_dir else None,
                     inline=args.inline, config=GUIDE_CONFIGS[args.guide])


if __name__ == "__main__":
    main()
