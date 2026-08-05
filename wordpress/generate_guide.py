#!/usr/bin/env python3
"""
Generate the Roadie Labs Interactive Training Guide page (MONOLITH — DEPRECATED).

DEPRECATED: This generator produces a single-page monolith (/guide/). The new
topic-cluster generator (generate_guide_cluster.py) produces 9 pages (1 pillar +
8 chapters) and should be used for all new deployments. This file is retained
because its block renderers, CSS builders, and JS builders are imported by the
cluster generator.

Reads structured content from guide/road-guide-content.json and produces
a standalone HTML page with interactive blocks (accordions, tabs, timelines,
process lists, data tables, callouts, knowledge checks), a content gate
after Chapter 3, and CTAs for Substack, training plans, and coaching.

Follows the same pattern as generate_methodology.py — imports shared constants,
defines page-specific builders, outputs standalone HTML.

Usage:
    python generate_guide.py              # Still works but deprecated
    python generate_guide.py --inline
    python generate_guide.py --output-dir ./output

See generate_guide_cluster.py for the replacement.
"""

import argparse
import hashlib
import html
import json
import random
import re
import sys
from datetime import datetime
from pathlib import Path

# Import shared constants from the race page generator
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
from cookie_consent import get_consent_banner_html
from brand_tokens import get_ga4_head_snippet


GUIDE_DIR = Path(__file__).parent.parent / "guide"
CONTENT_JSON = GUIDE_DIR / "road-guide-content.json"
OUTPUT_DIR = Path(__file__).parent / "output"


def esc(text) -> str:
    """HTML-escape a string. Handles 0/False correctly (only skips None/'')."""
    if text is None or text == "":
        return ""
    return html.escape(str(text))


def _safe_json_for_script(obj, **kwargs) -> str:
    """Serialize obj to JSON safe for embedding inside <script> tags.

    json.dumps does NOT escape '</' sequences, so a string containing
    '</script>' would prematurely close the <script> element, breaking
    the page and potentially enabling XSS. We replace '</' with '<\\/'
    which is semantically identical in JSON/JS but prevents the HTML
    parser from seeing an end tag.
    """
    raw = json.dumps(obj, **kwargs)
    return raw.replace("</", "<\\/")


# ── Content Loading ──────────────────────────────────────────


def load_content() -> dict:
    """Load and return guide content JSON."""
    return json.loads(CONTENT_JSON.read_text(encoding="utf-8"))


def load_race_index() -> dict:
    """Load race-index.json and return slug → race dict mapping."""
    index_path = Path(__file__).parent.parent / "web" / "race-index.json"
    races = json.loads(index_path.read_text(encoding="utf-8"))
    return {r["slug"]: r for r in races}


# ── Markdown helpers ─────────────────────────────────────────

# Module-level glossary dict, set during generation so all render functions
# that call _md_inline() automatically resolve tooltip markers.
_GLOSSARY = None  # dict or None — set during generation for tooltip resolution
_RIDER_TYPES = None  # list[str] or None — valid rider-type ids from content personalization
_RACE_INDEX = None  # dict or None — slug → race data, set during generation for race blocks
_CURRENT_LESSON_ID = None  # str or None — set by course generator for deterministic
                           # per-lesson seeds (matching shuffle, gate hashes)


def set_lesson_context(lesson_id):
    """Set the current lesson id so renderers that need a stable per-lesson
    seed (matching knowledge checks, continue gates) produce deterministic
    HTML. Course generators call this before rendering a lesson's blocks."""
    global _CURRENT_LESSON_ID
    _CURRENT_LESSON_ID = lesson_id


def _md_inline(text: str) -> str:
    """Apply markdown-lite inline formatting (bold, italic, links, tooltips, counters)."""
    # Tooltip pattern: {{TERM}} → tooltip span (starts with letter; road glossary
    # includes multiword terms like "broom wagon", so spaces/hyphens are allowed)
    if _GLOSSARY:
        def _tooltip_repl(m):
            term = m.group(1)
            defn = _GLOSSARY.get(term, "")
            if defn:
                return (f'<span class="rl-tooltip-trigger" tabindex="0">{esc(term)}'
                        f'<span class="rl-tooltip">{esc(defn)}</span></span>')
            return term  # no definition found, render plain
        text = re.sub(r'\{\{([A-Za-z][A-Za-z0-9_/ -]*)\}\}', _tooltip_repl, text)
    # Counter pattern: {{123}} → counter span (max 7 digits + 2 decimals)
    text = re.sub(
        r'\{\{(\d{1,7}(?:\.\d{1,2})?)\}\}',
        r'<span class="rl-guide-counter">\1</span>',
        text,
    )
    text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
    text = re.sub(r'\*(.+?)\*', r'<em>\1</em>', text)
    text = re.sub(r'\[(.+?)\]\((.+?)\)', r'<a href="\2">\1</a>', text)
    return text


def _md_block(content: str) -> str:
    """Convert escaped content into HTML paragraphs and lists."""
    content = _md_inline(content)
    lines = content.split('\n')
    result = []
    in_list = False
    list_type = None  # 'ul' or 'ol'
    for line in lines:
        stripped = line.strip()
        if stripped.startswith('- '):
            if in_list and list_type != 'ul':
                result.append(f'</{list_type}>')
                in_list = False
            if not in_list:
                result.append('<ul class="rl-guide-list">')
                in_list = True
                list_type = 'ul'
            result.append(f'<li>{stripped[2:]}</li>')
        elif re.match(r'^\d+\.\s', stripped):
            if in_list and list_type != 'ol':
                result.append(f'</{list_type}>')
                in_list = False
            if not in_list:
                result.append('<ol class="rl-guide-list">')
                in_list = True
                list_type = 'ol'
            # Strip the number prefix (e.g. "1. ", "12. ")
            li_text = re.sub(r'^\d+\.\s', '', stripped)
            result.append(f'<li>{li_text}</li>')
        elif stripped.startswith('### '):
            if in_list:
                result.append(f'</{list_type}>')
                in_list = False
                list_type = None
            result.append(f'<h4 class="rl-guide-prose-h">{stripped[4:]}</h4>')
        else:
            if in_list:
                result.append(f'</{list_type}>')
                in_list = False
                list_type = None
            if stripped:
                result.append(f'<p>{stripped}</p>')
    if in_list:
        result.append(f'</{list_type}>')
    return '\n'.join(result)


# ── Block Renderers ──────────────────────────────────────────


def render_prose(block: dict) -> str:
    """Render a prose block — paragraphs with markdown-lite formatting."""
    return _md_block(esc(block["content"]))


def render_data_table(block: dict) -> str:
    """Render a data table block."""
    caption = esc(block.get("caption", ""))
    headers = block["headers"]
    rows = block["rows"]

    header_cells = ''.join(f'<th>{esc(h)}</th>' for h in headers)
    body_rows = []
    for row in rows:
        cells = ''.join(f'<td>{esc(c)}</td>' for c in row)
        body_rows.append(f'<tr>{cells}</tr>')

    caption_html = f'<caption>{caption}</caption>' if caption else ''
    return f'''<div class="rl-guide-table-wrap">
      <table class="rl-guide-table">
        {caption_html}
        <thead><tr>{header_cells}</tr></thead>
        <tbody>{''.join(body_rows)}</tbody>
      </table>
    </div>'''


def render_accordion(block: dict) -> str:
    """Render an accordion block with collapsible items."""
    items_html = []
    for idx, item in enumerate(block["items"]):
        title = esc(item["title"])
        if "blocks" in item:
            # Nested blocks (e.g. data_table + callout inside an accordion panel)
            content_html = "\n".join(render_block(b) for b in item["blocks"])
        else:
            content_html = _md_block(esc(item["content"]))
        panel_id = f"accordion-panel-{hashlib.md5(title.encode()).hexdigest()[:8]}-{idx}"

        items_html.append(f'''<div class="rl-guide-accordion-item">
        <button class="rl-guide-accordion-trigger" aria-expanded="false" aria-controls="{panel_id}">
          <span>{title}</span>
          <span class="rl-guide-accordion-icon" aria-hidden="true">+</span>
        </button>
        <div class="rl-guide-accordion-body" id="{panel_id}">{content_html}</div>
      </div>''')
    return '\n'.join(items_html)


def render_tabs(block: dict) -> str:
    """Render a tabbed content block."""
    tabs = block["tabs"]
    tab_id = f"tabs-{hashlib.md5(tabs[0]['label'].encode()).hexdigest()[:8]}"

    # Rider-typed tab groups default to the same rider as personalized_content
    # blocks (finisher), so a fresh visit shows one consistent athlete.
    default_idx = 0
    for i, tab in enumerate(tabs):
        if tab.get("rider_type") == "finisher":
            default_idx = i
            break

    tab_buttons = []
    tab_panels = []
    for i, tab in enumerate(tabs):
        active = ' rl-guide-tab--active' if i == default_idx else ''
        hidden = '' if i == default_idx else ' style="display:none"'
        selected = 'true' if i == default_idx else 'false'
        label = esc(tab["label"])
        title = esc(tab.get("title", tab["label"]))
        content_html = _md_block(esc(tab["content"]))
        panel_id = f"{tab_id}-{i}"
        btn_id = f"{tab_id}-btn-{i}"

        rider_attr = f' data-rider-type="{esc(tab["rider_type"])}"' if "rider_type" in tab else ''
        tab_buttons.append(
            f'<button class="rl-guide-tab{active}" role="tab" '
            f'aria-selected="{selected}" aria-controls="{panel_id}" '
            f'id="{btn_id}" data-tab="{panel_id}"{rider_attr}>{label}</button>'
        )
        tab_panels.append(
            f'<div class="rl-guide-tab-panel" role="tabpanel" '
            f'aria-labelledby="{btn_id}" id="{panel_id}"{hidden}>'
            f'<h4 class="rl-guide-tab-title">{title}</h4>'
            f'{content_html}</div>'
        )

    return f'''<div class="rl-guide-tabs" data-tabgroup="{tab_id}">
      <div class="rl-guide-tab-bar" role="tablist">{''.join(tab_buttons)}</div>
      <div class="rl-guide-tab-content">{''.join(tab_panels)}</div>
    </div>'''


def render_timeline(block: dict) -> str:
    """Render a timeline block."""
    title = esc(block.get("title", ""))
    steps = block["steps"]
    steps_html = []
    for i, step in enumerate(steps):
        label = esc(step["label"])
        content = _md_inline(esc(step["content"]))
        paras = [f'<p>{p.strip()}</p>' for p in content.split('\n') if p.strip()]
        steps_html.append(f'''<div class="rl-guide-timeline-step">
        <div class="rl-guide-timeline-marker">{i + 1}</div>
        <div class="rl-guide-timeline-content">
          <h4 class="rl-guide-timeline-label">{label}</h4>
          {''.join(paras)}
        </div>
      </div>''')

    title_html = f'<h3 class="rl-guide-timeline-title">{title}</h3>' if title else ''
    return f'''<div class="rl-guide-timeline">
      {title_html}
      {''.join(steps_html)}
    </div>'''


def render_process_list(block: dict) -> str:
    """Render a numbered process list with labels, details, and animated bars."""
    items = block["items"]
    items_html = []
    for i, item in enumerate(items):
        label = esc(item["label"])
        detail = _md_inline(esc(item["detail"]))
        pct = item.get("percentage")
        if pct is not None:
            pct_html = (
                f'<div class="rl-guide-process-bar-wrap">'
                f'<div class="rl-guide-process-bar" style="width:{pct}%"></div>'
                f'<span class="rl-guide-process-pct">{pct}%</span>'
                f'</div>'
            )
        else:
            pct_html = ''
        items_html.append(f'''<div class="rl-guide-process-item">
        <div class="rl-guide-process-num">{i + 1}</div>
        <div class="rl-guide-process-body">
          <span class="rl-guide-process-label">{label}</span>
          {pct_html}
          <p class="rl-guide-process-detail">{detail}</p>
        </div>
      </div>''')
    return f'<div class="rl-guide-process-list">{chr(10).join(items_html)}</div>'


def render_callout(block: dict) -> str:
    """Render a callout/quote block."""
    style = block.get("style", "highlight")
    content = _md_inline(esc(block["content"]))
    paras = [f'<p>{p.strip()}</p>' for p in content.split('\n') if p.strip()]
    return f'<div class="rl-guide-callout rl-guide-callout--{esc(style)}">{"".join(paras)}</div>'


def render_knowledge_check(block: dict, label: str = "KNOWLEDGE CHECK") -> str:
    """Render a knowledge check mini-quiz.

    Options support an optional per-choice "feedback" field (Rise-style
    "by choice" feedback). When present, the lesson JS reveals the matching
    feedback for the selected option instead of the block-level explanation.
    Pages without that JS still show the default explanation (feedback divs
    stay hidden).

    Supports "format" variants: "multiple_choice" (default), "fill_blank"
    (text input + CHECK button) and "matching" (tap-to-pair, right column
    shuffled server-side with a stable per-lesson seed)."""
    fmt = block.get("format", "multiple_choice")
    if fmt == "fill_blank":
        return _render_kc_fill_blank(block, label)
    if fmt == "matching":
        return _render_kc_matching(block, label)
    question = esc(block["question"])
    explanation = esc(block["explanation"])

    # Generate a unique hash for XP tracking (first 8 chars of SHA-256)
    hash_input = block["question"] + json.dumps(
        [opt["text"] for opt in block["options"]], ensure_ascii=False
    )
    question_hash = hashlib.sha256(hash_input.encode("utf-8")).hexdigest()[:8]

    options_html = []
    feedback_html = []
    for i, opt in enumerate(block["options"]):
        text = esc(opt["text"])
        correct = "true" if opt["correct"] else "false"
        options_html.append(
            f'<button class="rl-guide-kc-option" data-correct="{correct}" data-index="{i}">{text}</button>'
        )
        if opt.get("feedback"):
            feedback_html.append(
                f'<div class="rl-guide-kc-feedback" data-feedback-index="{i}" '
                f'style="display:none"><p>{esc(opt["feedback"])}</p></div>'
            )
    return f'''<div class="rl-guide-knowledge-check" data-question-hash="{question_hash}">
      <div class="rl-guide-kc-label">{esc(label)}</div>
      <p class="rl-guide-kc-question">{question}</p>
      <div class="rl-guide-kc-options">{"".join(options_html)}</div>
      <div class="rl-guide-kc-explanation" style="display:none">
        {"".join(feedback_html)}<p class="rl-guide-kc-explanation-default">{explanation}</p>
      </div>
    </div>'''


def _render_kc_fill_blank(block: dict, label: str) -> str:
    """Render a fill-in-the-blank knowledge check.

    Schema: {"format": "fill_blank", "question": "...",
             "accept": ["answer a", "answer b"], "case_sensitive": false,
             "explanation": "..."}.
    JS trims whitespace and compares case-insensitively unless
    case_sensitive is true. No-JS fallback: the input renders but the
    check requires JS — content (question + explanation markup) is never
    hidden by CSS alone."""
    question = esc(block["question"])
    explanation = esc(block.get("explanation", ""))
    accept = block["accept"]
    if not isinstance(accept, list) or not accept:
        raise ValueError("fill_blank knowledge check requires a non-empty 'accept' list")
    case_sensitive = "true" if block.get("case_sensitive") else "false"
    hash_input = block["question"] + json.dumps(accept, ensure_ascii=False)
    question_hash = hashlib.sha256(hash_input.encode("utf-8")).hexdigest()[:8]
    accept_attr = esc(json.dumps(accept, ensure_ascii=False))
    input_id = f"rl-fib-{question_hash}"
    return f'''<div class="rl-guide-knowledge-check rl-guide-kc--fill-blank" data-question-hash="{question_hash}" data-kc-format="fill_blank">
      <div class="rl-guide-kc-label">{esc(label)}</div>
      <p class="rl-guide-kc-question">{question}</p>
      <div class="rl-guide-kc-fib" data-accept="{accept_attr}" data-case-sensitive="{case_sensitive}">
        <label class="rl-vh" for="{input_id}">Your answer</label>
        <input type="text" id="{input_id}" class="rl-guide-kc-fib-input" autocomplete="off" autocapitalize="off" spellcheck="false">
        <button type="button" class="rl-guide-kc-fib-check">CHECK</button>
      </div>
      <div class="rl-guide-kc-fib-status" aria-live="polite"></div>
      <div class="rl-guide-kc-explanation" style="display:none">
        <p class="rl-guide-kc-explanation-default">{explanation}</p>
      </div>
    </div>'''


def _render_kc_matching(block: dict, label: str) -> str:
    """Render a matching knowledge check (tap-to-pair).

    Schema: {"format": "matching", "question": "...",
             "pairs": [{"left": "...", "right": "..."}], "explanation": "..."}.
    Left column keeps author order; the right column is shuffled ONCE at
    render time with a deterministic seed (lesson id + content hash) so the
    generated HTML is stable across runs."""
    pairs = block["pairs"]
    if not isinstance(pairs, list) or len(pairs) < 2:
        raise ValueError("matching knowledge check requires at least 2 pairs")
    question = esc(block.get("question", "Match each item on the left to its pair on the right."))
    explanation = esc(block.get("explanation", ""))
    hash_input = json.dumps([[p["left"], p["right"]] for p in pairs], ensure_ascii=False)
    question_hash = hashlib.sha256(hash_input.encode("utf-8")).hexdigest()[:8]
    # Deterministic shuffle: seed on lesson id + content hash so HTML is
    # stable for tests and across regenerations.
    rng = random.Random(f"{_CURRENT_LESSON_ID or 'guide'}:{question_hash}")
    order = list(range(len(pairs)))
    rng.shuffle(order)
    if order == list(range(len(pairs))):
        # Never serve the answers in natural order — rotate by one.
        order = order[1:] + order[:1]
    left_html = "".join(
        f'<button type="button" class="rl-guide-kc-match-left" data-pair="{i}">{esc(p["left"])}</button>'
        for i, p in enumerate(pairs)
    )
    right_html = "".join(
        f'<button type="button" class="rl-guide-kc-match-right" data-match="{j}">{esc(pairs[j]["right"])}</button>'
        for j in order
    )
    explanation_html = (
        f'<div class="rl-guide-kc-explanation" style="display:none">'
        f'<p class="rl-guide-kc-explanation-default">{explanation}</p></div>'
        if explanation else ''
    )
    return f'''<div class="rl-guide-knowledge-check rl-guide-kc--matching" data-question-hash="{question_hash}" data-kc-format="matching">
      <div class="rl-guide-kc-label">{esc(label)}</div>
      <p class="rl-guide-kc-question">{question}</p>
      <p class="rl-guide-kc-match-hint">Tap an item on the left, then tap its match on the right.</p>
      <div class="rl-guide-kc-match">
        <div class="rl-guide-kc-match-col">{left_html}</div>
        <div class="rl-guide-kc-match-col">{right_html}</div>
      </div>
      {explanation_html}
    </div>'''


def render_labeled_graphic(block: dict) -> str:
    """Render a labeled graphic (Rise-style hotspot block).

    Schema: {"type": "labeled_graphic", "src": "...", "alt": "...",
             "markers": [{"x": 42.5, "y": 31.0, "label": "1",
                          "title": "...", "content": "...",
                          "feedback_detail": "..."}]}.
    x/y are percentages (0-100). Markers render as absolutely positioned
    buttons; the popover is built by JS with textContent (no innerHTML).
    No-JS fallback: marker content renders as a numbered list below the
    image (markers hidden, list visible — JS flips both via .rl-lg-ready)."""
    src = esc(block["src"])
    alt = esc(block.get("alt", ""))
    caption = block.get("caption", "")
    markers = block.get("markers", [])
    if not markers:
        raise ValueError("labeled_graphic requires at least one marker")
    fig_hash = hashlib.sha256(
        (block["src"] + json.dumps([m.get("title", "") for m in markers],
                                   ensure_ascii=False)).encode("utf-8")
    ).hexdigest()[:8]
    markers_html = []
    fallback_html = []
    for i, m in enumerate(markers):
        x = float(m["x"])
        y = float(m["y"])
        if not (0 <= x <= 100) or not (0 <= y <= 100):
            raise ValueError(
                f"labeled_graphic marker {i} out of bounds: x={x}, y={y} "
                f"(both must be 0-100 percentages)")
        mlabel = esc(m.get("label", str(i + 1)))
        title = esc(m["title"])
        item_id = f"rl-lg-{fig_hash}-{i}"
        markers_html.append(
            f'<button type="button" class="rl-guide-lg-marker" '
            f'style="left:{x}%;top:{y}%" data-lg-index="{i}" '
            f'aria-expanded="false" aria-controls="{item_id}" '
            f'aria-label="Marker {mlabel}: {title}">{mlabel}</button>'
        )
        detail = m.get("feedback_detail", "")
        detail_html = (f' <span class="rl-guide-lg-item-detail">{esc(detail)}</span>'
                       if detail else '')
        fallback_html.append(
            f'<li class="rl-guide-lg-item" id="{item_id}" data-lg-index="{i}">'
            f'<strong class="rl-guide-lg-item-title">{title}</strong> '
            f'<span class="rl-guide-lg-item-content">{esc(m["content"])}</span>'
            f'{detail_html}</li>'
        )
    cap = (f'<figcaption class="rl-guide-img-caption">{_md_inline(esc(caption))}</figcaption>'
           if caption else '')
    return f'''<figure class="rl-guide-labeled-graphic" data-lg-id="{fig_hash}">
      <div class="rl-guide-lg-stage">
        <img src="{src}" alt="{alt}" loading="lazy" decoding="async" class="rl-guide-lg-img">
        {''.join(markers_html)}
      </div>
      {cap}
      <ol class="rl-guide-lg-fallback">{''.join(fallback_html)}</ol>
    </figure>'''


def render_sorting_activity(block: dict) -> str:
    """Render a sorting activity (Rise-style, tap-to-sort — no drag).

    Schema: {"type": "sorting_activity", "title": "...",
             "instructions": "...",
             "categories": [{"id": "front", "label": "Front brake"}],
             "items": [{"text": "...", "category": "front"}]}.
    Constraints: at most 4 categories, text-only cards, every item's
    category must exist. One prompt card at a time + big tappable category
    buttons. No-JS fallback: all cards render visible as a list; category
    buttons stay hidden until JS adds .rl-sorting-ready."""
    title = esc(block.get("title", ""))
    instructions = esc(block.get("instructions", ""))
    categories = block["categories"]
    items = block["items"]
    if len(categories) > 4:
        raise ValueError(
            f"sorting_activity supports at most 4 categories, got {len(categories)}")
    if len(categories) < 2:
        raise ValueError("sorting_activity requires at least 2 categories")
    if not items:
        raise ValueError("sorting_activity requires at least one item")
    cat_ids = {c["id"] for c in categories}
    for i, it in enumerate(items):
        if it["category"] not in cat_ids:
            raise ValueError(
                f"sorting_activity item {i} references unknown category "
                f"'{it['category']}' (known: {sorted(cat_ids)})")
    hash_input = block.get("title", "") + json.dumps(
        [it["text"] for it in items], ensure_ascii=False)
    sort_hash = hashlib.sha256(hash_input.encode("utf-8")).hexdigest()[:8]
    cats_html = "".join(
        f'<button type="button" class="rl-guide-sorting-cat" data-category="{esc(c["id"])}">'
        f'<span class="rl-guide-sorting-cat-label">{esc(c["label"])}</span>'
        f'<span class="rl-guide-sorting-cat-count">0</span></button>'
        for c in categories
    )
    cards_html = "".join(
        f'<div class="rl-guide-sorting-card" data-category="{esc(it["category"])}">'
        f'<p>{esc(it["text"])}</p></div>'
        for it in items
    )
    title_html = f'<p class="rl-guide-sorting-title">{title}</p>' if title else ''
    instr_html = (f'<p class="rl-guide-sorting-instructions">{instructions}</p>'
                  if instructions else '')
    return f'''<div class="rl-guide-sorting" data-sorting-hash="{sort_hash}" data-sorting-total="{len(items)}">
      <div class="rl-guide-sorting-label">SORTING ACTIVITY</div>
      {title_html}
      {instr_html}
      <div class="rl-guide-sorting-stack">{cards_html}</div>
      <div class="rl-guide-sorting-cats">{cats_html}</div>
      <div class="rl-guide-sorting-progress" aria-live="polite"></div>
      <div class="rl-guide-sorting-done" hidden></div>
    </div>'''


# Valid continue_gate modes (Rise-style continue block)
_GATE_MODES = {"none", "block_above", "all_above"}


def render_continue_gate(block: dict) -> str:
    """Render a continue gate (Rise-style continue block).

    Schema: {"type": "continue_gate", "label": "...",
             "mode": "none"|"block_above"|"all_above"}.
    Renders a full-width button above a thin rule. CRITICAL progressive
    enhancement: the markup hides NOTHING — content after the gate is only
    wrapped/hidden by JS (build_course_js), so with JS off everything stays
    visible. Passed gates persist in the localStorage course state."""
    label = esc(block.get("label", "CONTINUE"))
    mode = block.get("mode", "none")
    if mode not in _GATE_MODES:
        raise ValueError(
            f"continue_gate mode must be one of {sorted(_GATE_MODES)}, got '{mode}'")
    hash_input = f"{_CURRENT_LESSON_ID or 'guide'}:{block.get('label', '')}:{mode}"
    gate_hash = hashlib.sha256(hash_input.encode("utf-8")).hexdigest()[:8]
    return f'''<div class="rl-guide-continue-gate" data-gate-mode="{esc(mode)}" data-gate-hash="{gate_hash}">
      <button type="button" class="rl-guide-continue-btn">{label}</button>
      <p class="rl-guide-continue-hint" hidden></p>
    </div>'''


def render_flashcard(block: dict) -> str:
    """Render a set of flip-cards for memorization."""
    title = esc(block.get("title", ""))
    cards_html = []
    for i, card in enumerate(block["cards"]):
        front = _md_inline(esc(card["front"]))
        back = _md_inline(esc(card["back"]))
        card_id = f"fc-{hashlib.md5(front.encode()).hexdigest()[:8]}-{i}"
        cards_html.append(
            f'<div class="rl-guide-flashcard" id="{card_id}" role="button" tabindex="0" aria-label="Flashcard: {esc(card["front"])}">'
            f'<div class="rl-guide-flashcard-inner">'
            f'<div class="rl-guide-flashcard-front"><p>{front}</p></div>'
            f'<div class="rl-guide-flashcard-back"><p>{back}</p></div>'
            f'</div></div>'
        )
    title_html = f'<div class="rl-guide-flashcard-label">{esc(title)}</div>' if title else ''
    return f'<div class="rl-guide-flashcard-deck">{title_html}<div class="rl-guide-flashcard-grid">{"".join(cards_html)}</div><p class="rl-guide-flashcard-hint">Click a card to flip</p></div>'


def render_scenario(block: dict) -> str:
    """Render an interactive branching scenario."""
    prompt_text = esc(block["prompt"])
    options_html = []
    for i, opt in enumerate(block["options"]):
        label = esc(opt["label"])
        result = _md_inline(esc(opt["result"]))
        is_best = ' data-best="true"' if opt.get("best") else ''
        options_html.append(
            f'<button class="rl-guide-scenario-option"{is_best} data-index="{i}">'
            f'<span class="rl-guide-scenario-option-label">{label}</span>'
            f'<span class="rl-guide-scenario-option-result">{result}</span>'
            f'</button>'
        )
    return f'''<div class="rl-guide-scenario">
      <div class="rl-guide-scenario-label">RACE SCENARIO</div>
      <p class="rl-guide-scenario-prompt">{prompt_text}</p>
      <div class="rl-guide-scenario-options">{"".join(options_html)}</div>
    </div>'''


def render_calculator(block: dict) -> str:
    """Render an interactive calculator block (FTP zones, nutrition, fueling)."""
    calc_id = esc(block["calculator_id"])
    title = esc(block.get("title", "Calculator"))
    desc = _md_inline(esc(block.get("description", "")))

    inputs_html = []
    for inp in block["inputs"]:
        inp_id = esc(inp["id"])
        label = esc(inp["label"])
        inp_type = inp.get("type", "number")
        placeholder = esc(inp.get("placeholder", ""))
        optional = ' (optional)' if inp.get("optional") else ''
        transform = f' data-transform="{esc(inp["transform"])}"' if inp.get("transform") else ''
        min_attr = f' min="{inp["min"]}"' if "min" in inp else ''
        max_attr = f' max="{inp["max"]}"' if "max" in inp else ''

        if inp_type == "select":
            options_html = ''.join(
                f'<option value="{esc(opt["value"])}">{esc(opt["label"])}</option>'
                for opt in inp["options"]
            )
            inputs_html.append(
                f'<div class="rl-guide-calc-field">'
                f'<label for="rl-calc-{inp_id}">{label}{optional}</label>'
                f'<select id="rl-calc-{inp_id}" class="rl-guide-calc-select">{options_html}</select>'
                f'</div>'
            )
        elif inp_type == "toggle":
            btns = ''.join(
                f'<button class="rl-guide-calc-toggle-btn{" rl-guide-calc-toggle-btn--active" if i == 0 else ""}" '
                f'data-value="{esc(opt["value"])}">{esc(opt["label"])}</button>'
                for i, opt in enumerate(inp["options"])
            )
            inputs_html.append(
                f'<div class="rl-guide-calc-field">'
                f'<label>{label}</label>'
                f'<div class="rl-guide-calc-toggle" data-field="{inp_id}">{btns}</div>'
                f'</div>'
            )
        elif inp_type == "text":
            # Plain text input (e.g. optional race-name notes) — never used
            # by the compute functions, which only read manual numeric fields.
            inputs_html.append(
                f'<div class="rl-guide-calc-field">'
                f'<label for="rl-calc-{inp_id}">{label}{optional}</label>'
                f'<input type="text" id="rl-calc-{inp_id}" '
                f'placeholder="{placeholder}" '
                f'class="rl-guide-calc-input">'
                f'</div>'
            )
        else:
            inputs_html.append(
                f'<div class="rl-guide-calc-field">'
                f'<label for="rl-calc-{inp_id}">{label}{optional}</label>'
                f'<input type="number" id="rl-calc-{inp_id}" inputmode="numeric" '
                f'placeholder="{placeholder}"{min_attr}{max_attr}{transform} '
                f'class="rl-guide-calc-input">'
                f'</div>'
            )

    # Build zone bars for FTP calculator
    zones_html = ''
    if "zones" in block:
        bars = []
        for z in block["zones"]:
            name = esc(z["name"])
            color = esc(z.get("color", "#333333"))
            hr_attrs = ''
            if "hr_min_pct" in z:
                hr_attrs = f' data-hr-min="{z["hr_min_pct"]}" data-hr-max="{z["hr_max_pct"]}"'
            bars.append(
                f'<div class="rl-guide-calc-zone" data-min="{z["min_pct"]}" data-max="{z["max_pct"]}"{hr_attrs}>'
                f'<span class="rl-guide-calc-zone-name">{name}</span>'
                f'<div class="rl-guide-calc-zone-track">'
                f'<div class="rl-guide-calc-zone-fill" style="background:{color};width:0%"></div>'
                f'</div>'
                f'<span class="rl-guide-calc-zone-range"></span>'
                f'<span class="rl-guide-calc-zone-hr"></span>'
                f'</div>'
            )
        zones_html = f'<div class="rl-guide-calc-zones">{"".join(bars)}</div>'

    # Build output area for nutrition calculators
    output_html = ''
    if "output_fields" in block:
        fields = []
        for f_def in block["output_fields"]:
            fid = esc(f_def["id"])
            flabel = esc(f_def["label"])
            fields.append(
                f'<div class="rl-guide-calc-result-item">'
                f'<span class="rl-guide-calc-result-label">{flabel}</span>'
                f'<span class="rl-guide-calc-result-value" id="rl-calc-out-{fid}">—</span>'
                f'</div>'
            )
        output_html = f'<div class="rl-guide-calc-results">{"".join(fields)}</div>'

    return f'''<div class="rl-guide-calculator" data-calc-type="{calc_id}">
      <div class="rl-guide-calc-label">{title}</div>
      <p class="rl-guide-calc-desc">{desc}</p>
      <div class="rl-guide-calc-inputs">{"".join(inputs_html)}</div>
      <div class="rl-guide-calc-error" style="display:none"></div>
      <button class="rl-guide-calc-btn">CALCULATE</button>
      <div class="rl-guide-calc-output" aria-live="polite" style="display:none">
        <div class="rl-guide-calc-ftp-display"></div>
        {zones_html}
        {output_html}
      </div>
    </div>'''


def render_image(block: dict) -> str:
    """Render an image block with optional caption and layout variants.
    Infographic asset_ids are dispatched to inline SVG/HTML renderers;
    hero photos fall through to <img> tags.

    Course-local images use a direct "src" path instead of an asset_id
    (e.g. {"type": "image", "src": "/course/dirt-craft/assets/x.webp"})."""
    if "src" in block:
        src = esc(block["src"])
        alt = esc(block.get("alt", ""))
        caption = block.get("caption", "")
        layout = block.get("layout", "inline")
        cls = f" rl-guide-img--{layout}" if layout != "inline" else ""
        cap = (f'<figcaption class="rl-guide-img-caption">{_md_inline(esc(caption))}</figcaption>'
               if caption else '')
        return (f'<figure class="rl-guide-img{cls}">'
                f'<img src="{src}" alt="{alt}" loading="lazy" decoding="async" '
                f'class="rl-guide-img-el">{cap}</figure>')
    infographic_renderer = INFOGRAPHIC_RENDERERS.get(block["asset_id"])
    if infographic_renderer:
        return infographic_renderer(block)
    asset_id = esc(block["asset_id"])
    alt = esc(block.get("alt", ""))
    caption = block.get("caption", "")
    layout = block.get("layout", "inline")
    cls = f" rl-guide-img--{layout}" if layout != "inline" else ""
    src = f"/guide/media/{asset_id}-1x.webp"
    src2 = f"/guide/media/{asset_id}-2x.webp"
    onerror = 'this.onerror=null;this.style.display=&quot;none&quot;;this.parentElement.classList.add(&quot;rl-guide-img--missing&quot;)'
    placeholder = f'<div class="rl-guide-img-placeholder">{alt or asset_id}</div>'
    cap = f'<figcaption class="rl-guide-img-caption">{_md_inline(esc(caption))}</figcaption>' if caption else ''
    return f'<figure class="rl-guide-img{cls}"><img src="{src}" srcset="{src} 1x, {src2} 2x" alt="{alt}" loading="lazy" decoding="async" class="rl-guide-img-el" onerror="{onerror}">{placeholder}{cap}</figure>'


def render_video(block: dict) -> str:
    """Render a video block. Two shapes:
    - YouTube embed: {"id", "title"?, "channel"?, "caption"?, "start"?, "mtb_demo"?}
    - Self-hosted asset: {"asset_id", "poster"?, "alt"?, "caption"?}
    """
    caption = block.get("caption", "")
    cap = f'<figcaption class="rl-guide-img-caption">{_md_inline(esc(caption))}</figcaption>' if caption else ''

    # YouTube embed (Dirt Craft-style). Detected by "id" (a YouTube video id).
    if block.get("id"):
        vid = esc(block["id"])
        src = f'https://www.youtube.com/embed/{vid}'
        start = block.get("start")
        if start:
            src += f'?start={int(start)}'
        title = esc(block.get("title", ""))
        channel = esc(block.get("channel", ""))
        meta_bits = ['<span class="rl-guide-video-kicker">Watch</span>']
        if title:
            meta_bits.append(f'<span class="rl-guide-video-title">{title}</span>')
        if channel:
            meta_bits.append(f'<span class="rl-guide-video-channel">{channel}</span>')
        if block.get("mtb_demo"):
            meta_bits.append('<span class="rl-guide-video-mtb">MTB demo &middot; transfers to the road</span>')
        meta = f'<div class="rl-guide-video-meta">{"".join(meta_bits)}</div>'
        return (
            '<figure class="rl-guide-video rl-guide-video--embed">'
            f'<div class="rl-guide-video-frame"><iframe src="{src}" title="{title}" '
            'loading="lazy" allowfullscreen referrerpolicy="strict-origin-when-cross-origin" '
            'allow="accelerometer; encrypted-media; picture-in-picture"></iframe></div>'
            f'{meta}{cap}</figure>'
        )

    # Self-hosted asset (existing behavior).
    asset_id = esc(block["asset_id"])
    poster_id = block.get("poster", "")
    alt = esc(block.get("alt", ""))
    poster = f' poster="/guide/media/{esc(poster_id)}-1x.webp"' if poster_id else ''
    return f'<figure class="rl-guide-img rl-guide-video"><video src="/guide/media/{asset_id}.mp4"{poster} controls preload="none" class="rl-guide-img-el">{alt}</video>{cap}</figure>'


def render_zone_visualizer(block: dict) -> str:
    """Render an HTML/CSS zone intensity visualizer with animated bars."""
    zones = block["zones"]
    title = esc(block.get("title", "Zone Intensity Spectrum"))
    max_pct = max(z["max_pct"] for z in zones)

    rows_html = []
    for i, z in enumerate(zones):
        name = esc(z["name"])
        color = esc(z.get("color", "#333333"))
        pct_label = esc(z.get("label", f'{z["max_pct"]}%'))
        data_pct = round((z["max_pct"] / max_pct) * 100, 1)

        rows_html.append(
            f'<div class="rl-guide-viz-row">'
            f'<span class="rl-guide-viz-name">{name}</span>'
            f'<div class="rl-guide-viz-track">'
            f'<div class="rl-guide-viz-fill" style="background:{color};width:{data_pct}%"></div>'
            f'</div>'
            f'<span class="rl-guide-viz-pct">{pct_label}</span>'
            f'</div>'
        )

    return f'''<div class="rl-guide-zone-viz">
      <h3 class="rl-guide-section-title">{title}</h3>
      <div class="rl-guide-viz-bars" role="img" aria-label="Zone intensity spectrum">
        {"".join(rows_html)}
      </div>
    </div>'''


def render_hero_stat(block: dict) -> str:
    """Render a hero stat callout — big number with optional unit and context."""
    value = esc(block["value"])
    unit = esc(block.get("unit", ""))
    context = esc(block.get("context", ""))
    unit_html = f'<span class="rl-guide-hero-stat__unit">{unit}</span>' if unit else ''
    ctx_html = f'<div class="rl-guide-hero-stat__context">{context}</div>' if context else ''
    return f'<div class="rl-guide-hero-stat"><div class="rl-guide-hero-stat__value">{value}{unit_html}</div>{ctx_html}</div>'


# ── Dirt Craft Course Block Renderers ───────────────────────


def render_quiz(block: dict) -> str:
    """Render a quiz block — same schema as knowledge_check, different label.

    Used by module stack-check lessons. Shares the knowledge-check XP
    interaction JS (same rl-guide-kc-* classes and question hash)."""
    return render_knowledge_check(block, label="QUIZ")


def render_black_box(block: dict) -> str:
    """Render a black box / incident report — ominous dark crash-analysis block.

    Schema: {title, content} — content uses \\n\\n paragraph separators.
    The final paragraph is emphasized (the conclusion of the report)."""
    title = esc(block.get("title", "Incident Report"))
    paras = [p.strip() for p in block.get("content", "").split("\n\n") if p.strip()]
    paras_html = "".join(f'<p>{_md_inline(esc(p))}</p>' for p in paras)
    return f'''<div class="rl-guide-blackbox">
      <div class="rl-guide-blackbox-label">{title}</div>
      <div class="rl-guide-blackbox-body">{paras_html}</div>
    </div>'''


def render_sensation_target(block: dict) -> str:
    """Render a sensation target — the feel the rider is hunting for.

    Schema: {label, content} — content uses \\n\\n paragraph separators."""
    label = esc(block.get("label", ""))
    content_html = _md_block(esc(block.get("content", "")))
    return f'''<div class="rl-guide-sensation">
      <div class="rl-guide-sensation-kicker">SENSATION TARGET</div>
      <div class="rl-guide-sensation-label">{label}</div>
      <div class="rl-guide-sensation-body">{content_html}</div>
    </div>'''


def render_process(block: dict) -> str:
    """Render a named-tool protocol — numbered steps with action + detail.

    Schema: {title, description, steps: [{step, action, detail}]}.
    These are the course's "named tools" — visually distinct from
    process_list (which is a generic numbered list with percentage bars)."""
    title = esc(block.get("title", ""))
    desc = _md_inline(esc(block.get("description", "")))
    steps_html = []
    for s in block.get("steps", []):
        num = esc(s.get("step", ""))
        action = _md_inline(esc(s.get("action", "")))
        detail = _md_inline(esc(s.get("detail", "")))
        steps_html.append(
            f'<div class="rl-guide-tool-step">'
            f'<div class="rl-guide-tool-step-num">{num}</div>'
            f'<div class="rl-guide-tool-step-body">'
            f'<div class="rl-guide-tool-step-action">{action}</div>'
            f'<div class="rl-guide-tool-step-detail">{detail}</div>'
            f'</div></div>'
        )
    desc_html = f'<div class="rl-guide-tool-desc">{desc}</div>' if desc else ''
    return f'''<div class="rl-guide-tool">
      <div class="rl-guide-tool-header">
        <div class="rl-guide-tool-kicker">NAMED TOOL</div>
        <div class="rl-guide-tool-title">{title}</div>
      </div>
      {desc_html}
      <div class="rl-guide-tool-steps">{"".join(steps_html)}</div>
    </div>'''


# Drill level → CSS modifier (whitelist; unknown levels fall back to neutral)
_DRILL_LEVELS = {"beginner", "intermediate", "race-pace"}


def render_drill(block: dict) -> str:
    """Render a field drill with level variants and an optional proof gate.

    Schema: {title, time_minutes, description,
             variants: [{level, label, steps: [str]}],
             proof_gate: {description, metric, target}}."""
    title = esc(block.get("title", ""))
    desc = _md_inline(esc(block.get("description", "")))
    time_min = block.get("time_minutes")
    time_html = (f'<span class="rl-guide-drill-time">{esc(time_min)} MIN</span>'
                 if time_min is not None and time_min != "" else '')

    variants_html = []
    for v in block.get("variants", []):
        level = str(v.get("level", "")).strip().lower()
        level_cls = f' rl-guide-drill-level--{esc(level)}' if level in _DRILL_LEVELS else ''
        label = _md_inline(esc(v.get("label", "")))
        steps = "".join(f'<li>{_md_inline(esc(s))}</li>' for s in v.get("steps", []))
        variants_html.append(
            f'<div class="rl-guide-drill-variant">'
            f'<span class="rl-guide-drill-level{level_cls}">{esc(level.upper())}</span>'
            f'<div class="rl-guide-drill-variant-label">{label}</div>'
            f'<ol class="rl-guide-drill-steps">{steps}</ol>'
            f'</div>'
        )

    pg = block.get("proof_gate") or {}
    pg_html = ''
    if pg:
        pg_target = _md_inline(esc(pg.get("target", pg.get("description", ""))))
        pg_html = (f'<div class="rl-guide-drill-gate">'
                   f'<div class="rl-guide-drill-gate-label">PROOF GATE</div>'
                   f'<div class="rl-guide-drill-gate-target">{pg_target}</div>'
                   f'</div>')

    desc_html = f'<div class="rl-guide-drill-desc">{desc}</div>' if desc else ''
    return f'''<div class="rl-guide-drill">
      <div class="rl-guide-drill-header">
        <div class="rl-guide-drill-kicker">FIELD DRILL {time_html}</div>
        <div class="rl-guide-drill-title">{title}</div>
      </div>
      {desc_html}
      {"".join(variants_html)}
      {pg_html}
    </div>'''


def render_recovery_protocol(block: dict) -> str:
    """Render a recovery protocol — accordion of when-it-goes-wrong scenarios.

    Schema: {title, scenarios: [{label, situation, steps: [str]}]}.
    Reuses rl-guide-accordion-trigger/-body classes so the existing
    accordion JS handles expand/collapse."""
    title = esc(block.get("title", "When Prevention Fails"))
    items_html = []
    for idx, s in enumerate(block.get("scenarios", [])):
        label = esc(s.get("label", ""))
        situation = _md_inline(esc(s.get("situation", "")))
        steps = "".join(f'<li>{_md_inline(esc(st))}</li>' for st in s.get("steps", []))
        panel_id = f"recovery-panel-{hashlib.md5(label.encode()).hexdigest()[:8]}-{idx}"
        items_html.append(
            f'<div class="rl-guide-accordion-item rl-guide-recovery-item">'
            f'<button class="rl-guide-accordion-trigger" aria-expanded="false" aria-controls="{panel_id}">'
            f'<span>{label}</span>'
            f'<span class="rl-guide-accordion-icon" aria-hidden="true">+</span>'
            f'</button>'
            f'<div class="rl-guide-accordion-body" id="{panel_id}">'
            f'<p class="rl-guide-recovery-situation">{situation}</p>'
            f'<ol class="rl-guide-recovery-steps">{steps}</ol>'
            f'</div></div>'
        )
    return f'''<div class="rl-guide-recovery">
      <div class="rl-guide-recovery-label">{title}</div>
      {"".join(items_html)}
    </div>'''


def render_commitment(block: dict) -> str:
    """Render a closing commitment callout — the rider's homework contract.

    Schema: {content}."""
    content_html = _md_block(esc(block.get("content", "")))
    return f'''<div class="rl-guide-commitment">
      <div class="rl-guide-commitment-kicker">YOUR COMMITMENT</div>
      <div class="rl-guide-commitment-body">{content_html}</div>
    </div>'''


# ── Race-Connected Block Renderers ──────────────────────────


def render_race_reference(block: dict) -> str:
    """Render an inline race mention with a live stat from the race database.

    Input: {"type": "race_reference", "slug": "unbound-200", "context": "elevation"}
    Output: Linked race name with relevant stat, e.g. "Unbound 200 (9,200ft gain, Tier 1)"
    """
    slug = block.get("slug", "")
    context_dim = block.get("context", "")
    if not _RACE_INDEX or slug not in _RACE_INDEX:
        return f'<!-- race not found: {esc(slug)} -->'
    race = _RACE_INDEX[slug]
    name = esc(race["name"])
    tier = race.get("tier", "")
    profile_url = esc(race.get("profile_url", f"/race/{slug}/"))
    # Build context stat string
    stat_parts = []
    if context_dim == "elevation" and race.get("elevation_ft"):
        stat_parts.append(f'{race["elevation_ft"]:,}ft gain')
    elif context_dim == "distance" and race.get("distance_mi"):
        stat_parts.append(f'{race["distance_mi"]:,} miles')
    elif context_dim == "climate" and race.get("scores", {}).get("climate"):
        score = race["scores"]["climate"]
        labels = {1: "Mild", 2: "Moderate", 3: "Variable", 4: "Challenging", 5: "Extreme"}
        stat_parts.append(f'Climate: {labels.get(score, score)}/5')
    elif context_dim == "technicality" and race.get("scores", {}).get("technicality"):
        score = race["scores"]["technicality"]
        labels = {1: "Smooth tarmac", 2: "Good roads", 3: "Mixed quality", 4: "Rough roads", 5: "Cobbles &amp; dirt"}
        stat_parts.append(f'{labels.get(score, score)}')
    elif context_dim and race.get("scores", {}).get(context_dim):
        stat_parts.append(f'{esc(context_dim.replace("_", " ").title())}: {esc(race["scores"][context_dim])}/5')
    if tier:
        stat_parts.append(f'Tier {esc(tier)}')
    stat_str = f' ({", ".join(stat_parts)})' if stat_parts else ''
    return (f'<a href="{profile_url}" class="rl-race-ref" '
            f'data-slug="{esc(slug)}">{name}{stat_str}</a>')


def render_race_callout(block: dict) -> str:
    """Render a side-by-side race comparison card.

    Input: {"type": "race_callout", "slugs": ["unbound-200", "mid-south-100"],
            "dimension": "elevation", "caption": "..."}
    Output: Neo-brutalist comparison card showing how two races differ on a dimension.
    """
    slugs = block.get("slugs", [])
    dimension = block.get("dimension", "overall_score")
    caption = block.get("caption", "")
    if not _RACE_INDEX:
        return '<!-- race index not loaded -->'
    if len(slugs) != 2:
        return f'<!-- race callout: expected 2 slugs, got {len(slugs)} -->'
    races = [_RACE_INDEX.get(s) for s in slugs]
    if not all(races):
        missing = [esc(s) for s, r in zip(slugs, races) if not r]
        return f'<!-- race callout: missing slugs {", ".join(missing)} -->'

    def _race_card(race):
        name = esc(race["name"])
        url = esc(race.get("profile_url", f'/race/{race["slug"]}/'))
        tier = race.get("tier", "")
        # Get dimension value
        if dimension == "overall_score":
            val = str(race.get("overall_score", "—"))
            label = "Overall"
        elif dimension in ("distance_mi", "elevation_ft"):
            raw = race.get(dimension, 0)
            val = f'{raw:,}' if raw else "—"
            label = "Distance (mi)" if dimension == "distance_mi" else "Elevation (ft)"
        elif dimension in race.get("scores", {}):
            val = str(race["scores"][dimension])
            label = dimension.replace("_", " ").title()
        else:
            val = "—"
            label = dimension.replace("_", " ").title()
        tier_html = f'<span class="rl-race-callout__tier" data-tier="{esc(tier)}">T{esc(tier)}</span>' if tier else ''
        return (f'<div class="rl-race-callout__race">'
                f'<a href="{url}" class="rl-race-callout__name">{name}</a>{tier_html}'
                f'<div class="rl-race-callout__stat">'
                f'<span class="rl-race-callout__stat-value">{esc(val)}</span>'
                f'<span class="rl-race-callout__stat-label">{esc(label)}</span>'
                f'</div></div>')

    cards = ''.join(_race_card(r) for r in races)
    vs_html = '<span class="rl-race-callout__vs">VS</span>'
    caption_html = f'<p class="rl-race-callout__caption">{_md_inline(esc(caption))}</p>' if caption else ''
    return (f'<div class="rl-race-callout" data-dimension="{esc(dimension)}">'
            f'<div class="rl-race-callout__header">RACE COMPARISON</div>'
            f'<div class="rl-race-callout__grid">{cards}</div>'
            f'{vs_html}{caption_html}</div>')


def render_decision_tree(block: dict) -> str:
    """Render an interactive decision tree for race selection.

    Input: {"type": "decision_tree", "title": "...", "tree": {...}}
    Tree structure: Each node has "question", "options" (list of {text, next|result}).
    Leaf nodes have "result" (slug or text) instead of "next" (node id).
    """
    title = esc(block.get("title", "Find Your Race"))
    tree = block.get("tree", {})
    # Validate that every 'next' reference points to an existing node
    node_ids = set(tree.keys())
    for node_id, node in tree.items():
        for opt in node.get("options", []):
            next_ref = opt.get("next")
            if next_ref and next_ref not in node_ids:
                raise ValueError(
                    f"Decision tree node '{node_id}' has option "
                    f"with next='{next_ref}' but node '{next_ref}' "
                    f"does not exist. Available nodes: {sorted(node_ids)}"
                )
    tree_json = json.dumps(tree, ensure_ascii=False)
    # Build initial question from the root node
    root = tree.get("root", {})
    root_question = esc(root.get("question", ""))
    root_options = root.get("options", [])
    options_html = []
    for opt in root_options:
        text = esc(opt.get("text", ""))
        target = esc(opt.get("next", opt.get("result", "")))
        is_result = "result" in opt
        options_html.append(
            f'<button class="rl-decision-tree__option" '
            f'data-target="{target}" data-is-result="{str(is_result).lower()}">'
            f'{text}</button>'
        )
    return (f'<div class="rl-decision-tree" data-tree=\'{esc(tree_json)}\'>'
            f'<div class="rl-decision-tree__header">{title}</div>'
            f'<div class="rl-decision-tree__body">'
            f'<p class="rl-decision-tree__question">{root_question}</p>'
            f'<div class="rl-decision-tree__options">{"".join(options_html)}</div>'
            f'</div>'
            f'<div class="rl-decision-tree__result" style="display:none"></div>'
            f'<button class="rl-decision-tree__restart" style="display:none">Start Over</button>'
            f'</div>')


def render_personalized_content(block: dict) -> str:
    """Render rider-type-personalized content with 4 variants.

    Input: {"type": "personalized_content", "variants": {
        "ayahuasca": {"content": "..."},
        "finisher": {"content": "..."},
        "competitor": {"content": "..."},
        "podium": {"content": "..."}
    }}
    Each variant is rendered in a div with data-rider-type. The finisher variant
    is visible by default; JS swaps on rider type selection.
    """
    variants = block.get("variants", {})
    rider_order = _RIDER_TYPES or ["ayahuasca", "finisher", "competitor", "podium"]
    # Warn about unknown variant keys (catches misspelled rider types)
    unknown = set(variants.keys()) - set(rider_order)
    if unknown:
        raise ValueError(
            f"personalized_content block has unknown rider types: "
            f"{sorted(unknown)}. Valid types: {rider_order}"
        )
    parts = []
    for rider in rider_order:
        v = variants.get(rider)
        if not v:
            continue
        content = _md_inline(esc(v.get("content", "")))
        paras = [f'<p>{p.strip()}</p>' for p in content.split('\n') if p.strip()]
        # finisher is visible by default (CSS uses opacity/visibility via --active class)
        active = ' rl-personalized--active' if rider == 'finisher' else ''
        parts.append(
            f'<div class="rl-personalized__variant{active}" '
            f'data-rider-type="{esc(rider)}">'
            f'{"".join(paras)}</div>'
        )
    return f'<div class="rl-personalized">{"".join(parts)}</div>'


# Block type -> renderer dispatch
BLOCK_RENDERERS = {
    "prose": render_prose,
    "data_table": render_data_table,
    "accordion": render_accordion,
    "tabs": render_tabs,
    "timeline": render_timeline,
    "process_list": render_process_list,
    "callout": render_callout,
    "knowledge_check": render_knowledge_check,
    "labeled_graphic": render_labeled_graphic,
    "sorting_activity": render_sorting_activity,
    "continue_gate": render_continue_gate,
    "flashcard": render_flashcard,
    "scenario": render_scenario,
    "calculator": render_calculator,
    "zone_visualizer": render_zone_visualizer,
    "image": render_image,
    "video": render_video,
    "hero_stat": render_hero_stat,
    "quiz": render_quiz,
    "black_box": render_black_box,
    "sensation_target": render_sensation_target,
    "process": render_process,
    "drill": render_drill,
    "recovery_protocol": render_recovery_protocol,
    "commitment": render_commitment,
    "race_reference": render_race_reference,
    "race_callout": render_race_callout,
    "decision_tree": render_decision_tree,
    "personalized_content": render_personalized_content,
}


def render_block(block: dict) -> str:
    """Route a block to its renderer."""
    renderer = BLOCK_RENDERERS.get(block["type"])
    if not renderer:
        print(f"  WARNING: Unknown block type '{block['type']}' — skipped", file=sys.stderr)
        return f'<!-- unknown block type: {esc(block["type"])} -->'
    return renderer(block)


# ── Page Sections ────────────────────────────────────────────


def build_nav() -> str:
    return get_site_header_html(active="products") + f'''
  <div class="rl-breadcrumb">
    <a href="{SITE_BASE_URL}/">Home</a>
    <span class="rl-breadcrumb-sep">&rsaquo;</span>
    <span class="rl-breadcrumb-current">Training Guide</span>
  </div>'''


def build_hero(content: dict) -> str:
    title = esc(content["title"])
    subtitle = esc(content["subtitle"])
    return f'''<div class="rl-hero">
    <div class="rl-hero-tier" style="background:#333333">FREE GUIDE</div>
    <h1>{title}</h1>
    <p class="rl-hero-tagline">{subtitle}</p>
  </div>'''


def build_progress_bar() -> str:
    return '<div class="rl-guide-progress" id="rl-guide-progress"><div class="rl-guide-progress-bar" role="progressbar" aria-valuenow="0" aria-valuemin="0" aria-valuemax="100" aria-label="Reading progress"></div></div>'


def build_chapter_nav(chapters: list) -> str:
    items = []
    for ch in chapters:
        num = f'{ch["number"]:02d}'
        lock = ' rl-guide-chapnav-item--locked' if ch["gated"] else ''
        icon = '<span class="rl-guide-chapnav-lock" aria-hidden="true">&#333333;</span>' if ch["gated"] else ''
        items.append(
            f'<a href="#{esc(ch["id"])}" class="rl-guide-chapnav-item{lock}" '
            f'data-chapter="{esc(ch["id"])}" '
            f'aria-label="Chapter {ch["number"]}: {esc(ch["title"])}">'
            f'{num}{icon}</a>'
        )
    return f'''<nav class="rl-guide-chapnav" id="rl-guide-chapnav" role="navigation" aria-label="Chapter navigation">
    {"".join(items)}
  </nav>'''


def build_chapter(chapter: dict) -> str:
    """Build a full chapter section."""
    num = chapter["number"]
    ch_id = chapter["id"]
    title = esc(chapter["title"])
    subtitle = esc(chapter.get("subtitle", ""))
    gated_class = ' rl-guide-gated' if chapter["gated"] else ''

    subtitle_html = f'<p class="rl-guide-chapter-subtitle">{subtitle}</p>' if subtitle else ''

    variant = "dark" if num in {2, 4, 6, 8} else "light"
    plate = render_chapter_plate(num, {"race_index": _RACE_INDEX})

    sections_html = []
    for section in chapter["sections"]:
        sec_title = section.get("title", "")
        sec_title_html = f'<h3 class="rl-guide-section-title">{esc(sec_title)}</h3>' if sec_title else ''
        block_parts = []
        for idx, b in enumerate(section["blocks"]):
            rendered = render_block(b)
            block_parts.append(rendered)
        blocks_html = '\n'.join(block_parts)
        sections_html.append(f'''<div class="rl-guide-section" id="{esc(section["id"])}">
        {sec_title_html}
        {blocks_html}
      </div>''')

    return f'''<div class="rl-guide-chapter{gated_class}" id="{esc(ch_id)}" data-chapter="{num}">
    <div class="rl-guide-chapter-hero rl-guide-chapter-hero--{variant}">
      {plate}
      <div class="rl-guide-chapter-title-block">
        <span class="rl-guide-chapter-num">CHAPTER {num:02d}</span>
        <h2 class="rl-guide-chapter-title">{title}</h2>
        {subtitle_html}
      </div>
    </div>
    <div class="rl-guide-chapter-body">
      {"".join(sections_html)}
    </div>
  </div>'''


def build_rider_selector(content: dict) -> str:
    """Build the rider type selector bar and floating badge."""
    personalization = content.get("personalization")
    if not personalization:
        return ''
    rider_types = personalization.get("rider_types", [])
    if not rider_types:
        return ''

    rider_ids = [rt["id"] for rt in rider_types]
    default_rider = "finisher" if "finisher" in rider_ids else rider_ids[0]

    btns = []
    for rt in rider_types:
        rid = esc(rt["id"])
        label = esc(rt["label"])
        hours = esc(rt.get("hours", ""))
        is_default = rt["id"] == default_rider
        checked = "true" if is_default else "false"
        active_cls = " rl-guide-rider-btn--active" if is_default else ""
        btns.append(
            f'<button class="rl-guide-rider-btn{active_cls}" role="radio" aria-checked="{checked}" '
            f'data-rider="{rid}" data-ftp="{rt.get("default_ftp", 200)}">'
            f'<span class="rl-guide-rider-btn-label">{label}</span>'
            f'<span class="rl-guide-rider-btn-hours">{hours}</span>'
            f'</button>'
        )

    return f'''<div class="rl-guide-rider-selector" id="rl-guide-rider-selector" role="radiogroup" aria-label="Select your rider type">
    <span class="rl-guide-rider-prompt">I AM A:</span>
    {"".join(btns)}
  </div>
  <div class="rl-guide-rider-badge" id="rl-guide-rider-badge" style="display:none">
    <span class="rl-guide-rider-badge-type" id="rl-guide-rider-badge-type"></span>
    <button class="rl-guide-rider-badge-change" id="rl-guide-rider-badge-change">CHANGE</button>
  </div>'''


def build_cta_newsletter() -> str:
    return f'''<div class="rl-guide-cta rl-guide-cta--newsletter">
    <div class="rl-guide-cta-inner">
      <span class="rl-guide-cta-kicker">STAY IN THE LOOP</span>
      <h3>Get Race Intel, Training Tips & New Guides</h3>
      <p>Join the Roadie Labs newsletter. No spam. Just useful road racing content.</p>
      <iframe src="{SUBSTACK_EMBED}" width="100%" height="150" style="border:none;background:transparent" frameborder="0" scrolling="no" loading="lazy"></iframe>
    </div>
  </div>'''


def build_cta_training() -> str:
    return f'''<div class="rl-guide-cta rl-guide-cta--training">
    <div class="rl-guide-cta-inner">
      <span class="rl-guide-cta-kicker">READY TO TRAIN?</span>
      <h3>Custom Road Training Plan</h3>
      <p>Race-specific. Built for you by a coach. $15/week, capped at $249.</p>
      <ul>
        <li>Structured workouts pushed to your device</li>
        <li>30+ page custom training guide</li>
        <li>Heat &amp; altitude protocols</li>
        <li>Nutrition plan</li>
        <li>Strength training</li>
      </ul>
      <a href="{TRAINING_PLANS_URL}" class="rl-guide-btn rl-guide-btn--primary">BUILD MY PLAN</a>
    </div>
  </div>'''


def build_cta_coaching() -> str:
    return f'''<div class="rl-guide-cta rl-guide-cta--coaching">
    <div class="rl-guide-cta-inner">
      <span class="rl-guide-cta-kicker">NEXT LEVEL</span>
      <h3>1:1 Road Coaching</h3>
      <p>For athletes who want individualized programming, weekly check-ins, and race-specific preparation. Limited spots available.</p>
      <a href="{COACHING_URL}" class="rl-guide-btn rl-guide-btn--secondary">APPLY FOR COACHING</a>
    </div>
  </div>'''


def build_cta_finale() -> str:
    """Build the 3-CTA finale grid after the final chapter."""
    return f'''<div class="rl-guide-finale" id="rl-guide-finale">
    <h2 class="rl-guide-finale-title">What's Your Next Move?</h2>
    <div class="rl-guide-finale-grid">
      <div class="rl-guide-finale-card rl-guide-finale-card--newsletter">
        <span class="rl-guide-finale-kicker">STAY CONNECTED</span>
        <h3>Newsletter</h3>
        <p>Race intel, training tips, and new guides.</p>
        <a href="{SUBSTACK_URL}" class="rl-guide-btn rl-guide-btn--primary" target="_blank">SUBSCRIBE FREE</a>
      </div>
      <div class="rl-guide-finale-card rl-guide-finale-card--training">
        <span class="rl-guide-finale-kicker">READY TO TRAIN</span>
        <h3>Training Plan</h3>
        <p>Custom plans built for your race and ability.</p>
        <a href="{TRAINING_PLANS_URL}" class="rl-guide-btn rl-guide-btn--primary">BUILD MY PLAN</a>
      </div>
      <div class="rl-guide-finale-card rl-guide-finale-card--coaching">
        <span class="rl-guide-finale-kicker">GO FURTHER</span>
        <h3>1:1 Coaching</h3>
        <p>Individualized programming and race prep.</p>
        <a href="{COACHING_URL}" class="rl-guide-btn rl-guide-btn--secondary">APPLY</a>
      </div>
    </div>
  </div>'''


def build_chapter_email_capture(chapter: dict) -> str:
    """Build the quiet end-of-chapter email capture block.

    docs/specs/friend-first-sequences.md §4.2-4.3 — the guide currently has
    no capture point of its own. This is a single email field, no gate (the
    guide stays free), posted directly to the fueling-lead-intake worker
    with this chapter's title as guide_chapter so the welcome sequence can
    branch on it. Imported by generate_guide_cluster.py and rendered once
    per chapter page; the submit handler lives in build_cluster_js().
    """
    ch_id = esc(chapter["id"])
    title = esc(chapter["title"])
    form_id = f"rl-guide-capture-{ch_id}"
    return f'''<div class="rl-guide-email-capture" id="{form_id}-block">
    <p class="rl-guide-email-capture-text">Training for something? Leave your email — then reply to the welcome note and tell me the race. I'll help.</p>
    <form class="rl-guide-email-capture-form" id="{form_id}" autocomplete="off">
      <input type="hidden" name="guide_chapter" value="{title}">
      <input type="hidden" name="website" value="">
      <input type="email" name="email" required placeholder="your@email.com" class="rl-guide-email-capture-input" aria-label="Email address">
      <button type="submit" class="rl-guide-email-capture-btn">SEND</button>
    </form>
    <p class="rl-guide-email-capture-success" id="{form_id}-success" style="display:none">&#10003; Got it &mdash; hit reply anytime.</p>
  </div>'''


def build_gate() -> str:
    """Build the content gate overlay between Ch 3 and Ch 4."""
    return f'''<div class="rl-guide-gate" id="rl-guide-gate">
    <div class="rl-guide-gate-inner">
      <span class="rl-guide-gate-kicker">CHAPTERS 4-8 ARE LOCKED</span>
      <h2>Unlock the Full Guide</h2>
      <p>You've read the free chapters. The remaining 5 chapters cover workout execution, fueling, pack skills &amp; tactics, race week protocol, and recovery.</p>
      <p>Subscribe to the Roadie Labs newsletter to unlock everything instantly.</p>
      <iframe src="{SUBSTACK_EMBED}" width="100%" height="150" style="border:none;background:transparent" frameborder="0" scrolling="no" loading="lazy"></iframe>
      <button class="rl-guide-gate-bypass" id="rl-guide-gate-bypass">I already subscribed &mdash; unlock</button>
    </div>
  </div>'''


def build_footer() -> str:
    year = datetime.now().year
    return f'''<div class="rl-footer">
    <p class="rl-footer-disclaimer">This guide represents our editorial views on road racing training. Consult a physician before starting any exercise program. We are not affiliated with any race organizer, governing body, or equipment manufacturer. Training plans and coaching are separate paid services.</p>
    <p style="margin-top:12px;font-size:11px;color:#555555">&copy; {year} Roadie Labs. All rights reserved.</p>
  </div>'''


CTA_BUILDERS = {
    "newsletter": build_cta_newsletter,
    "training_plans": build_cta_training,
    "coaching": build_cta_coaching,
    "finale": build_cta_finale,
}


def build_jsonld(content: dict) -> str:
    """Build Article + BreadcrumbList JSON-LD."""
    canonical = f"{SITE_BASE_URL}/guide/"
    # Use file mtime for dateModified, current date for datePublished
    try:
        mtime = CONTENT_JSON.stat().st_mtime
        date_modified = datetime.fromtimestamp(mtime).strftime("%Y-%m-%d")
    except OSError:
        date_modified = datetime.now().strftime("%Y-%m-%d")
    date_published = "2025-06-01"
    og_image = f"{SITE_BASE_URL}/og/homepage.jpg"

    article = {
        "@context": "https://schema.org",
        "@type": "Article",
        "headline": content["title"],
        "description": content["meta_description"],
        "url": canonical,
        "datePublished": date_published,
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
            "@type": "WebSite",
            "name": "Roadie Labs",
            "url": SITE_BASE_URL,
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
                "name": "Training Guide",
                "item": canonical,
            },
        ],
    }
    # Course schema
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
    }

    # HowTo schema for training methodology
    howto_steps = []
    for ch in content["chapters"]:
        howto_steps.append({
            "@type": "HowToStep",
            "name": f"Chapter {ch['number']}: {ch['title']}",
            "text": ch.get("subtitle", ch["title"]),
            "url": f"{canonical}#{ch['id']}",
        })
    howto = {
        "@context": "https://schema.org",
        "@type": "HowTo",
        "name": "How to Train for a Road Race",
        "description": "A complete guide to road race training: fundamentals, workout execution, fueling, pack skills, and recovery.",
        "totalTime": "PT84D",
        "step": howto_steps,
    }

    parts = [
        f'<script type="application/ld+json">{_safe_json_for_script(article, separators=(",",":"))}</script>',
        f'<script type="application/ld+json">{_safe_json_for_script(breadcrumb, separators=(",",":"))}</script>',
        f'<script type="application/ld+json">{_safe_json_for_script(course, separators=(",",":"))}</script>',
        f'<script type="application/ld+json">{_safe_json_for_script(howto, separators=(",",":"))}</script>',
    ]
    return '\n'.join(parts)


# ── CSS ──────────────────────────────────────────────────────


def build_guide_css() -> str:
    """Return all guide-specific CSS."""
    return ''':root{
--rl-color-near-black:#1a1a1a;
--rl-color-primary-navy:#1a1a1a;
--rl-color-secondary-blue:#555555;
--rl-color-coral:#999999;
--rl-color-light-steel:#d0d0c8;
--rl-color-silver:#d0d0c8;
--rl-color-cool-white:#f5f5f0;
--rl-color-orange:#555555;
--rl-color-light-gold:#555555;
--rl-color-signal-red:#333333;
--rl-color-light-orange:#b8b8b0;
--rl-color-near-black:#1a1a1a;
--rl-color-white:#ffffff;
--rl-color-error:#8b1a1a;
--rl-color-tier-1:#1a1a1a;
--rl-color-tier-2:#555555;
--rl-color-tier-3:#666666;
--rl-color-tier-4:#666666;
--rl-font-data:'Sometype Mono',monospace;
--rl-font-editorial:'Source Serif 4',Georgia,serif
}

/* ── Guide Progress Bar ── */
.rl-guide-progress{position:fixed;top:0;left:0;width:100%;height:3px;z-index:1001;background:transparent}
.rl-guide-progress-bar{height:100%;width:0%;background:#333333}

/* ── Chapter Nav ── */
.rl-guide-chapnav{position:sticky;top:3px;z-index:1000;background:#1a1a1a;display:flex;justify-content:center;gap:0;border:3px solid #1a1a1a;margin-bottom:32px}
.rl-guide-chapnav-item{color:#999999;text-decoration:none;font-size:12px;font-weight:700;letter-spacing:1px;padding:10px 16px;display:flex;align-items:center;gap:4px;border-right:1px solid #1a1a1a;border-bottom:3px solid transparent}
.rl-guide-chapnav-item:last-child{border-right:none}
.rl-guide-chapnav-item:hover{color:#d0d0c8;background:transparent}
.rl-guide-chapnav-item--active{color:#fff;border-bottom-color:#555555;background:transparent}
.rl-guide-chapnav-item--locked .rl-guide-chapnav-lock{font-size:9px;opacity:0.5}
.rl-guide-chapnav-item--unlocked .rl-guide-chapnav-lock{display:none}

/* ── Chapter ── */
.rl-guide-chapter{margin-bottom:40px;border:3px solid #1a1a1a;background:#f5f5f0}
.rl-guide-chapter-hero{min-height:312px;padding:48px 32px;position:relative;overflow:hidden;background:var(--rl-color-cool-white);display:flex;align-items:flex-end}
.rl-guide-chapter-hero--dark{background:var(--rl-color-near-black)}
.rl-guide-plate{position:absolute;inset:0;width:100%;height:100%;display:block}
.rl-guide-chapter-title-block{position:relative;z-index:1;max-width:460px}
.rl-guide-chapter-num{display:block;font-size:11px;font-weight:700;letter-spacing:3px;text-transform:uppercase;color:var(--rl-color-secondary-blue);margin-bottom:8px}
.rl-guide-chapter-title{font-family:'Source Serif 4',Georgia,serif;font-size:32px;font-weight:700;text-transform:uppercase;letter-spacing:2px;line-height:1.1;margin:0;color:var(--rl-color-near-black)}
.rl-guide-chapter-subtitle{font-family:'Source Serif 4',Georgia,serif;font-size:14px;color:var(--rl-color-primary-navy);margin-top:8px}
.rl-guide-chapter-hero--dark .rl-guide-chapter-num{color:var(--rl-color-light-steel)}
.rl-guide-chapter-hero--dark .rl-guide-chapter-title{color:var(--rl-color-white)}
.rl-guide-chapter-hero--dark .rl-guide-chapter-subtitle{color:var(--rl-color-silver)}
.rl-guide-chapter-body{padding:40px 48px}

/* ── Gating ── */
.rl-guide-gated{display:none}
.rl-guide-unlocked .rl-guide-gated{display:block}
.rl-guide-unlocked .rl-guide-gate{display:none}
.rl-guide-unlocked .rl-guide-chapnav-item--locked .rl-guide-chapnav-lock{display:none}

/* ── Gate Overlay ── */
.rl-guide-gate{background:#1a1a1a;color:#fff;padding:48px 32px;border:3px solid #1a1a1a;margin-bottom:40px;text-align:center}
.rl-guide-gate-inner{max-width:600px;margin:0 auto}
.rl-guide-gate-kicker{display:inline-block;background:#1a1a1a;color:#fff;padding:4px 12px;font-size:10px;font-weight:700;letter-spacing:3px;margin-bottom:16px}
.rl-guide-gate h2{font-size:28px;text-transform:uppercase;letter-spacing:2px;margin:12px 0}
.rl-guide-gate p{font-size:13px;color:#f5f5f0;line-height:1.6;margin-bottom:16px}
.rl-guide-gate-bypass{background:none;border:none;color:#b8b8b0;font-size:12px;cursor:pointer;text-decoration:underline;margin-top:16px;font-family:'Sometype Mono',monospace}
.rl-guide-gate-bypass:hover{color:#d0d0c8}

/* ── Section ── */
.rl-guide-section{margin-bottom:32px}
.rl-guide-section-title{font-family:'Source Serif 4',Georgia,serif;font-size:18px;font-weight:700;text-transform:uppercase;letter-spacing:1.5px;margin:0 0 16px;padding-bottom:8px;border-bottom:4px double #1a1a1a;color:#1a1a1a}

/* ── Prose ── */
.rl-guide-chapter-body p{font-family:'Source Serif 4',Georgia,serif;font-size:14px;line-height:1.75;margin:0 0 14px;color:#1a1a1a}
.rl-guide-chapter-body strong{font-weight:700}
.rl-guide-list{font-family:'Source Serif 4',Georgia,serif;padding-left:20px;margin:0 0 16px;font-size:14px;line-height:1.75}
.rl-guide-list li{margin-bottom:6px}

/* ── Data Table ── */
.rl-guide-table-wrap{overflow-x:auto;margin:0 0 20px}
.rl-guide-table{width:100%;border-collapse:collapse;font-size:12px;border:2px solid #1a1a1a}
.rl-guide-table caption{text-align:left;font-size:11px;font-weight:700;letter-spacing:2px;text-transform:uppercase;padding:8px 12px;background:#f5f5f0;border:2px solid #1a1a1a;border-bottom:none;color:#1a1a1a}
.rl-guide-table th{background:#1a1a1a;color:#fff;padding:8px 12px;text-align:left;font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:1px;border:1px solid #1a1a1a}
.rl-guide-table thead{border-bottom:4px double #1a1a1a}
.rl-guide-table td{padding:8px 12px;border:1px solid #d0d0c8;vertical-align:top}
.rl-guide-table tbody tr:nth-child(even){background:#f5f5f0}

/* ── Accordion ── */
.rl-guide-accordion-item{border:2px solid #1a1a1a;margin-bottom:8px}
.rl-guide-accordion-trigger{display:flex;justify-content:space-between;align-items:center;width:100%;padding:12px 16px;background:#f5f5f0;border:none;cursor:pointer;font-family:'Sometype Mono',monospace;font-size:13px;font-weight:700;text-align:left;color:#1a1a1a}
.rl-guide-accordion-trigger:hover{background:#d0d0c8}
.rl-guide-accordion-icon{font-size:18px;font-weight:700}
.rl-guide-accordion-trigger[aria-expanded="true"] .rl-guide-accordion-icon{transform:rotate(45deg)}
.rl-guide-accordion-body{display:none;padding:16px;border-top:2px solid #1a1a1a}
.rl-guide-accordion-trigger[aria-expanded="true"]+.rl-guide-accordion-body{display:block}

/* ── Tabs ── */
.rl-guide-tabs{border:2px solid #1a1a1a;margin:0 0 20px}
.rl-guide-tab-bar{display:flex;flex-wrap:wrap;background:#1a1a1a;gap:0;border-bottom:4px double #1a1a1a}
.rl-guide-tab{padding:10px 16px;background:transparent;color:#999999;border:none;border-bottom:3px solid transparent;cursor:pointer;font-family:'Sometype Mono',monospace;font-size:11px;font-weight:700;letter-spacing:1px;text-transform:uppercase}
.rl-guide-tab:hover{background:transparent;color:#d0d0c8}
.rl-guide-tab--active{color:#fff;border-bottom-color:#555555;background:transparent}
.rl-guide-tab-panel{padding:24px 32px}
.rl-guide-tab-title{font-size:15px;font-weight:700;margin:0 0 12px;color:#1a1a1a;text-transform:uppercase;letter-spacing:1px}

/* ── Timeline ── */
.rl-guide-timeline{margin:0 0 24px;padding-left:20px}
.rl-guide-timeline-title{font-size:14px;font-weight:700;text-transform:uppercase;letter-spacing:2px;margin:0 0 16px;color:#1a1a1a}
.rl-guide-timeline-step{display:flex;gap:16px;margin-bottom:20px;position:relative}
.rl-guide-timeline-step:not(:last-child)::before{content:'';position:absolute;left:15px;top:32px;bottom:-20px;width:2px;background:#d0d0c8}
.rl-guide-timeline-marker{width:32px;height:32px;min-width:32px;background:#333333;color:#fff;font-size:13px;font-weight:700;display:flex;align-items:center;justify-content:center;position:relative;z-index:1}
.rl-guide-timeline-content{flex:1}
.rl-guide-timeline-label{font-size:14px;font-weight:700;margin:0 0 6px;text-transform:uppercase;letter-spacing:1px;color:#1a1a1a}
.rl-guide-timeline-content p{font-family:'Source Serif 4',Georgia,serif;font-size:13px;line-height:1.6;margin:0;color:#1a1a1a}

/* ── Process List ── */
.rl-guide-process-list{margin:0 0 20px}
.rl-guide-process-item{display:flex;gap:14px;margin-bottom:16px;padding:12px;border:2px solid #1a1a1a;background:#f5f5f0}
.rl-guide-process-num{width:32px;height:32px;min-width:32px;background:#1a1a1a;color:#fff;font-size:14px;font-weight:700;display:flex;align-items:center;justify-content:center}
.rl-guide-process-body{flex:1}
.rl-guide-process-label{font-weight:700;font-size:14px;color:#1a1a1a}
.rl-guide-process-pct{display:inline-block;background:#555555;color:#fff;font-size:10px;font-weight:700;padding:2px 6px;margin-left:8px;letter-spacing:1px}
.rl-guide-process-detail{font-size:13px;color:#1a1a1a;margin:4px 0 0;line-height:1.5}

/* ── Callout ── */
.rl-guide-callout{padding:20px 24px;margin:0 0 20px;border-left:6px solid #333333;background:#f5f5f0}
.rl-guide-callout--quote{border-left-color:#555555;font-style:italic;background:rgba(183,149,11,0.04)}
.rl-guide-callout--highlight{border-left-color:#555555}
.rl-guide-callout--traffic_light{border-left-color:#555555}
.rl-guide-callout p{font-family:'Source Serif 4',Georgia,serif;font-size:13px;line-height:1.7;margin:0 0 8px;color:#1a1a1a}
.rl-guide-callout p:last-child{margin-bottom:0}

/* ── Knowledge Check ── */
.rl-guide-knowledge-check{border:3px solid #1a1a1a;margin:0 0 24px;background:#f5f5f0}
.rl-guide-kc-label{background:#1a1a1a;color:#f5f5f0;padding:8px 16px;font-size:10px;font-weight:700;letter-spacing:3px;text-transform:uppercase}
.rl-guide-kc-question{font-family:'Source Serif 4',Georgia,serif;padding:16px 20px 8px;font-size:14px;font-weight:700;color:#1a1a1a;margin:0}
.rl-guide-kc-options{padding:8px 20px 16px;display:flex;flex-direction:column;gap:8px}
.rl-guide-kc-option{padding:10px 16px;background:#f5f5f0;border:2px solid #1a1a1a;cursor:pointer;font-family:'Sometype Mono',monospace;font-size:12px;text-align:left}
.rl-guide-kc-option:hover{background:#d0d0c8}
.rl-guide-kc-option--correct{background:#333333 !important;color:#fff !important;border-color:#333333 !important}
.rl-guide-kc-option--incorrect{background:#8b1a1a !important;color:#fff !important;border-color:#8b1a1a !important}
.rl-guide-kc-option--disabled{pointer-events:none;opacity:0.6}
.rl-guide-kc-explanation{padding:12px 20px 16px;background:#f5f5f0;border-top:2px solid #333333}
.rl-guide-kc-explanation p{font-size:13px;line-height:1.6;margin:0;color:#1a1a1a}

/* ── Flashcards ── */
.rl-guide-flashcard-deck{margin:0 0 24px}
.rl-guide-flashcard-label{background:#333333;color:#fff;padding:8px 16px;font-size:10px;font-weight:700;letter-spacing:3px;text-transform:uppercase;display:inline-block;margin-bottom:12px}
.rl-guide-flashcard-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(200px,1fr));gap:12px}
.rl-guide-flashcard{cursor:pointer;height:140px;position:relative}
.rl-guide-flashcard-inner{position:relative;width:100%;height:100%}
.rl-guide-flashcard-front,.rl-guide-flashcard-back{position:absolute;inset:0;display:flex;align-items:center;justify-content:center;padding:16px;border:2px solid #1a1a1a;font-size:13px;text-align:center;transition:border-color 300ms cubic-bezier(0.4,0,0.2,1)}
.rl-guide-flashcard-front{background:#f5f5f0;font-weight:700;color:#1a1a1a}
.rl-guide-flashcard-back{background:#333333;color:#fff;display:none}
.rl-guide-flashcard--flipped .rl-guide-flashcard-front{display:none}
.rl-guide-flashcard--flipped .rl-guide-flashcard-back{display:block}
.rl-guide-flashcard-back p,.rl-guide-flashcard-front p{font-family:'Source Serif 4',Georgia,serif;margin:0;line-height:1.4}
.rl-guide-flashcard-hint{font-size:11px;color:#555555;text-align:center;margin:8px 0 0}

/* ── Scenario ── */
.rl-guide-scenario{border:3px solid #1a1a1a;margin:0 0 24px;background:#f5f5f0}
.rl-guide-scenario-label{background:#1a1a1a;color:#fff;padding:8px 16px;font-size:10px;font-weight:700;letter-spacing:3px;text-transform:uppercase}
.rl-guide-scenario-prompt{font-family:'Source Serif 4',Georgia,serif;padding:16px 20px 8px;font-size:14px;font-weight:700;color:#1a1a1a;margin:0}
.rl-guide-scenario-options{padding:8px 20px 16px;display:flex;flex-direction:column;gap:8px}
.rl-guide-scenario-option{padding:12px 16px;background:#f5f5f0;border:2px solid #1a1a1a;cursor:pointer;font-family:'Sometype Mono',monospace;font-size:12px;text-align:left}
.rl-guide-scenario-option:hover{background:#d0d0c8}
.rl-guide-scenario-option-result{display:none;margin-top:8px;font-size:12px;color:#1a1a1a;font-weight:400;line-height:1.5}
.rl-guide-scenario-option--selected .rl-guide-scenario-option-result{display:block}
.rl-guide-scenario-option--selected{border-color:#1a1a1a;background:#f5f5f0}
.rl-guide-scenario-option--selected[data-best="true"]{border-color:#333333;background:#f5f5f0}
.rl-guide-scenario-option--disabled{pointer-events:none;opacity:0.6}

/* ── CTA Blocks ── */
.rl-guide-cta{margin:0 0 40px;border:3px solid #1a1a1a;padding:40px 32px;text-align:center}
.rl-guide-cta-inner{max-width:600px;margin:0 auto}
.rl-guide-cta-kicker{display:inline-block;font-size:10px;font-weight:700;letter-spacing:3px;text-transform:uppercase;margin-bottom:12px}
.rl-guide-cta h3{font-family:'Source Serif 4',Georgia,serif;font-size:22px;font-weight:700;text-transform:uppercase;letter-spacing:2px;margin:0 0 12px}
.rl-guide-cta p{font-family:'Source Serif 4',Georgia,serif;font-size:13px;line-height:1.6;margin:0 0 16px}
.rl-guide-cta ul{text-align:left;font-size:13px;line-height:1.8;padding-left:20px;margin:0 0 20px}
.rl-guide-cta--newsletter{background:#1a1a1a;color:#fff}
.rl-guide-cta--newsletter .rl-guide-cta-kicker{color:#d0d0c8}
.rl-guide-cta--newsletter p{color:#d0d0c8}
.rl-guide-cta--training{background:#1a1a1a;color:#fff}
.rl-guide-cta--training .rl-guide-cta-kicker{color:#555555}
.rl-guide-cta--training p,.rl-guide-cta--training ul{color:#d0d0c8}
.rl-guide-cta--coaching{background:#333333;color:#fff}
.rl-guide-cta--coaching .rl-guide-cta-kicker{color:rgba(255,255,255,0.7)}

/* ── Buttons ── */
.rl-guide-btn{display:inline-block;padding:12px 24px;font-family:'Sometype Mono',monospace;font-size:13px;font-weight:700;letter-spacing:2px;text-transform:uppercase;text-decoration:none;cursor:pointer;border:3px solid #1a1a1a}
.rl-guide-btn--primary{background:#1a1a1a;color:#fff;border-color:#1a1a1a}
.rl-guide-btn--primary:hover{background:#333333;border-color:#333333}
.rl-guide-btn--secondary{background:#333333;color:#fff;border-color:#333333}
.rl-guide-btn--secondary:hover{background:#b8b8b0;border-color:#b8b8b0}

/* ── Finale Grid ── */
.rl-guide-finale{margin:0 0 40px;text-align:center}
.rl-guide-finale-title{font-size:24px;font-weight:700;text-transform:uppercase;letter-spacing:2px;margin:0 0 24px;color:#1a1a1a}
.rl-guide-finale-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:0}
.rl-guide-finale-card{padding:32px 20px;border:3px solid #1a1a1a;text-align:center}
.rl-guide-finale-card+.rl-guide-finale-card{border-left:none}
.rl-guide-finale-kicker{display:block;font-size:10px;font-weight:700;letter-spacing:3px;margin-bottom:8px}
.rl-guide-finale-card h3{font-family:'Source Serif 4',Georgia,serif;font-size:18px;font-weight:700;text-transform:uppercase;margin:0 0 8px}
.rl-guide-finale-card p{font-family:'Source Serif 4',Georgia,serif;font-size:12px;line-height:1.5;margin:0 0 16px}
.rl-guide-finale-card--newsletter{background:#1a1a1a;color:#fff}
.rl-guide-finale-card--newsletter .rl-guide-finale-kicker{color:#d0d0c8}
.rl-guide-finale-card--newsletter p{color:#d0d0c8}
.rl-guide-finale-card--training{background:#1a1a1a;color:#fff}
.rl-guide-finale-card--training .rl-guide-finale-kicker{color:#555555}
.rl-guide-finale-card--training p{color:#d0d0c8}
.rl-guide-finale-card--coaching{background:#333333;color:#fff}
.rl-guide-finale-card--coaching .rl-guide-finale-kicker{color:rgba(255,255,255,0.7)}

/* ── Animated Process Bars ── */
.rl-guide-process-bar-wrap{display:flex;align-items:center;gap:8px;margin-top:4px;margin-bottom:4px}
.rl-guide-process-bar{height:8px;background:#333333;border:1px solid #1a1a1a}
.rl-guide-process-pct{font-size:11px;font-weight:700;color:#333333;min-width:36px}

/* ── Calculator ── */
.rl-guide-calculator{border:3px solid #1a1a1a;margin:0 0 24px;background:#f5f5f0}
.rl-guide-calc-label{background:#333333;color:#fff;padding:8px 16px;font-size:10px;font-weight:700;letter-spacing:3px;text-transform:uppercase}
.rl-guide-calc-desc{padding:12px 20px 4px;font-size:13px;color:#1a1a1a;margin:0}
.rl-guide-calc-inputs{padding:8px 20px;display:flex;flex-wrap:wrap;gap:12px}
.rl-guide-calc-field{display:flex;flex-direction:column;gap:4px;min-width:140px;flex:1}
.rl-guide-calc-field label{font-size:11px;font-weight:700;color:#1a1a1a;text-transform:uppercase;letter-spacing:1px}
.rl-guide-calc-input,.rl-guide-calc-select{padding:8px 12px;border:2px solid #1a1a1a;font-family:'Sometype Mono',monospace;font-size:13px;background:#f5f5f0}
.rl-guide-calc-input:focus,.rl-guide-calc-select:focus{outline:3px solid #555555;outline-offset:2px}
.rl-guide-calc-toggle{display:flex;gap:0}
.rl-guide-calc-toggle-btn{padding:8px 16px;border:2px solid #1a1a1a;background:#f5f5f0;font-family:'Sometype Mono',monospace;font-size:12px;font-weight:700;cursor:pointer}
.rl-guide-calc-toggle-btn+.rl-guide-calc-toggle-btn{border-left:none}
.rl-guide-calc-toggle-btn--active{background:#333333;color:#fff;border-color:#333333}
.rl-guide-calc-btn{display:block;margin:8px 20px 16px;padding:10px 24px;background:#1a1a1a;color:#fff;border:3px solid #1a1a1a;font-family:'Sometype Mono',monospace;font-size:12px;font-weight:700;letter-spacing:2px;text-transform:uppercase;cursor:pointer}
.rl-guide-calc-btn:hover{background:#555555}
.rl-guide-calc-output{padding:16px 20px}
.rl-guide-calc-ftp-display{font-size:14px;font-weight:700;margin-bottom:12px;color:#1a1a1a}
.rl-guide-calc-zones{display:flex;flex-direction:column;gap:8px}
.rl-guide-calc-zone{display:grid;grid-template-columns:160px 1fr 80px 80px;align-items:center;gap:8px;font-size:12px}
.rl-guide-calc-zone-name{font-weight:700;font-size:11px;color:#1a1a1a}
.rl-guide-calc-zone-track{height:20px;background:#f5f5f0;border:1px solid #d0d0c8;position:relative}
.rl-guide-calc-zone-fill{height:100%;width:0%}
.rl-guide-calc-zone-range{font-size:11px;color:#1a1a1a;font-weight:700}
.rl-guide-calc-zone-hr{font-size:10px;color:#555555}
.rl-guide-calc-results{display:grid;grid-template-columns:repeat(auto-fill,minmax(180px,1fr));gap:12px;margin-top:12px}
.rl-guide-calc-result-item{padding:12px;border:2px solid #1a1a1a;background:#f5f5f0;text-align:center}
.rl-guide-calc-result-label{display:block;font-size:10px;font-weight:700;letter-spacing:2px;text-transform:uppercase;color:#1a1a1a;margin-bottom:4px}
.rl-guide-calc-result-value{display:block;font-size:18px;font-weight:700;color:#333333}
.rl-guide-calc-input--error{border-color:#8b1a1a}
.rl-guide-calc-error{color:#8b1a1a;font-size:11px;padding:0 20px 8px;display:none}

/* ── Zone Visualizer ── */
.rl-guide-zone-viz{margin:0 0 24px}
.rl-guide-viz-bars{display:flex;flex-direction:column;gap:8px}
.rl-guide-viz-row{display:grid;grid-template-columns:140px 1fr 50px;align-items:center;gap:8px;font-size:12px}
.rl-guide-viz-name{font-weight:700;font-size:11px;color:#1a1a1a}
.rl-guide-viz-track{height:24px;background:#f5f5f0;border:1px solid #d0d0c8;position:relative}
.rl-guide-viz-fill{height:100%;width:0%}
.rl-guide-viz-pct{font-size:11px;color:#555555;font-weight:700}

/* ── Rider Selector ── */
.rl-guide-rider-selector{display:flex;align-items:center;gap:0;background:#1a1a1a;border:3px solid #1a1a1a;border-top:none;flex-wrap:wrap}
.rl-guide-rider-prompt{color:#d0d0c8;font-size:10px;font-weight:700;letter-spacing:3px;padding:10px 16px}
.rl-guide-rider-btn{padding:10px 16px;background:transparent;color:#999999;border:none;border-right:1px solid #1a1a1a;border-bottom:3px solid transparent;cursor:pointer;font-family:'Sometype Mono',monospace;font-size:11px;font-weight:700;text-transform:uppercase;display:flex;flex-direction:column;gap:2px}
.rl-guide-rider-btn:last-child{border-right:none}
.rl-guide-rider-btn:hover{color:#d0d0c8;background:transparent}
.rl-guide-rider-btn--active{background:#1a1a1a;color:#fff;border-bottom:3px solid #555555}
.rl-guide-rider-btn-hours{font-size:9px;font-weight:400;opacity:0.7}
.rl-guide-rider-badge{position:fixed;bottom:20px;right:20px;z-index:999;background:#1a1a1a;border:3px solid #333333;padding:8px 14px;display:flex;align-items:center;gap:10px}
.rl-guide-rider-badge-type{color:#fff;font-size:11px;font-weight:700;letter-spacing:1px}
.rl-guide-rider-badge-change{background:none;border:none;color:#333333;font-family:'Sometype Mono',monospace;font-size:10px;font-weight:700;cursor:pointer;text-decoration:underline;letter-spacing:1px}

/* ── Counter ── */
.rl-guide-counter{font-weight:700;color:#333333}

/* ── Footer ── */
.rl-guide-chapter-body .rl-footer{border:3px solid #1a1a1a;border-top:4px double #1a1a1a;background:#1a1a1a;color:#d0d0c8;margin:0;padding:24px 0 0}

/* ── Focus Styles ── */
.rl-guide-chapnav-item:focus-visible,.rl-guide-accordion-trigger:focus-visible,.rl-guide-tab:focus-visible,.rl-guide-kc-option:focus-visible,.rl-guide-scenario-option:focus-visible,.rl-guide-flashcard:focus-visible,.rl-guide-btn:focus-visible,.rl-guide-gate-bypass:focus-visible{outline:3px solid #555555;outline-offset:2px}

/* ── Reduced Motion ── */
@media(prefers-reduced-motion: no-preference){
  .rl-guide-progress-bar{transition:width 0.15s linear}
  .rl-guide-chapnav-item{transition:color 300ms cubic-bezier(0.4,0,0.2,1),border-color 300ms cubic-bezier(0.4,0,0.2,1)}
  .rl-guide-accordion-icon{transition:transform 0.2s}
  .rl-guide-tab{transition:color 300ms cubic-bezier(0.4,0,0.2,1),border-color 300ms cubic-bezier(0.4,0,0.2,1)}
  .rl-guide-kc-option{transition:background-color 150ms cubic-bezier(0.4,0,0.2,1),border-color 150ms cubic-bezier(0.4,0,0.2,1)}
  .rl-guide-scenario-option{transition:background-color 150ms cubic-bezier(0.4,0,0.2,1),border-color 150ms cubic-bezier(0.4,0,0.2,1)}
  .rl-guide-btn{transition:background 150ms,color 150ms,border-color 150ms}
  .rl-guide-calc-zone-fill{transition:width 0.6s cubic-bezier(0.25,0.46,0.45,0.94)}
  .rl-guide-table tbody tr:hover{background:rgba(183,149,11,0.06)}
}

/* ── Responsive ── */
@media(max-width:768px){
  .rl-guide-chapnav{flex-wrap:wrap}
  .rl-guide-chapnav-item{padding:8px 10px;font-size:11px}
  .rl-guide-chapter-hero{padding:32px 20px}
  .rl-guide-chapter-title{font-size:24px}
  .rl-guide-chapter-body{padding:24px 16px}
  .rl-guide-finale-grid{grid-template-columns:1fr}
  .rl-guide-finale-card+.rl-guide-finale-card{border-left:3px solid #1a1a1a;border-top:none}
  .rl-guide-cta{padding:32px 20px}
  .rl-guide-tab-bar{flex-direction:column}
  .rl-guide-tab{border-bottom:1px solid #1a1a1a}
  .rl-guide-process-item{flex-direction:column;gap:8px}
  .rl-guide-timeline-step{gap:12px}
  .rl-guide-table{font-size:11px}
  .rl-guide-table th,.rl-guide-table td{padding:6px 8px}
  .rl-guide-flashcard-grid{grid-template-columns:repeat(auto-fill,minmax(150px,1fr))}
  .rl-guide-flashcard{height:120px}
  .rl-guide-calc-zone{grid-template-columns:1fr;gap:2px}
  .rl-guide-viz-row{grid-template-columns:1fr;gap:2px}
  .rl-guide-calc-inputs{flex-direction:column}
  .rl-guide-rider-selector{justify-content:center}
  .rl-guide-rider-badge{bottom:10px;right:10px}
  .rl-guide-img--full-width{margin-left:-16px;margin-right:-16px}
  .rl-guide-img--half-width{float:none;width:100%;margin:0 0 16px 0}
}

/* ── Image / Video Blocks ── */
.rl-guide-img{margin:0 0 20px;line-height:0}
.rl-guide-img-el{width:100%;height:auto;display:block;border:3px solid #1a1a1a}
.rl-guide-img-caption{font-size:11px;color:#d0d0c8;padding:8px 12px;line-height:1.5;font-family:'Sometype Mono',monospace;font-style:normal;letter-spacing:0.5px;background:#1a1a1a;border:3px solid #1a1a1a;border-top:4px double #1a1a1a;margin-top:0}
.rl-guide-img--full-width{margin-left:-24px;margin-right:-24px}
.rl-guide-img--half-width{float:right;width:50%;margin:0 0 16px 20px}
.rl-guide-img-placeholder{display:none;padding:32px 24px;background:#1a1a1a;color:#d0d0c8;font-family:'Sometype Mono',monospace;font-size:12px;letter-spacing:1px;text-align:center;border:3px solid #1a1a1a;min-height:120px;align-items:center;justify-content:center}
.rl-guide-img--missing .rl-guide-img-placeholder{display:flex}
.rl-guide-video--embed{margin:0 0 20px}
.rl-guide-video-frame{position:relative;width:100%;aspect-ratio:16/9;border:3px solid #1a1a1a;background:#1a1a1a;line-height:0}
.rl-guide-video-frame iframe{position:absolute;inset:0;width:100%;height:100%;border:0}
.rl-guide-video-meta{display:flex;gap:10px;align-items:baseline;flex-wrap:wrap;background:#1a1a1a;border:3px solid #1a1a1a;border-top:0;padding:8px 12px}
.rl-guide-video-kicker{font-family:'Sometype Mono',monospace;font-size:10px;font-weight:700;letter-spacing:2px;text-transform:uppercase;color:#555555}
.rl-guide-video-title{font-family:'Source Serif 4',Georgia,serif;font-weight:700;font-size:14px;color:#f5f5f0}
.rl-guide-video-channel{font-family:'Sometype Mono',monospace;font-size:11px;color:#d0d0c8}
.rl-guide-video-mtb{font-family:'Sometype Mono',monospace;font-size:9px;letter-spacing:1px;text-transform:uppercase;color:#b8b8b0;border:2px solid #333333;padding:1px 6px}

/* ── Tooltips ── */
.rl-tooltip-trigger{position:relative;cursor:help;border-bottom:2px dotted #555555;text-decoration:none}
.rl-tooltip{position:absolute;bottom:calc(100% + 10px);left:50%;transform:translateX(-50%);z-index:1000;background:#1a1a1a;color:#f5f5f0;border:3px solid #555555;padding:8px 12px;font-family:'Sometype Mono',monospace;font-size:10px;line-height:1.5;letter-spacing:1px;max-width:280px;opacity:0;visibility:hidden;transition:opacity 150ms cubic-bezier(0.4,0,0.2,1),visibility 150ms cubic-bezier(0.4,0,0.2,1);pointer-events:none;white-space:normal}
.rl-tooltip::after{content:'';position:absolute;top:100%;left:50%;transform:translateX(-50%);border:6px solid transparent;border-top-color:#555555}
.rl-tooltip-trigger:hover .rl-tooltip,.rl-tooltip-trigger:focus .rl-tooltip{opacity:1;visibility:visible}
@media(max-width:768px){.rl-tooltip{position:fixed;bottom:auto;top:auto;left:16px;right:16px;transform:none;max-width:none}}

/* ── Hero Stat ── */
.rl-guide-hero-stat{text-align:center;padding:var(--rl-spacing-xl) var(--rl-spacing-2xl);background:var(--rl-color-near-black);border:3px solid var(--rl-color-near-black);margin:var(--rl-spacing-lg) 0}
.rl-guide-hero-stat__value{font-family:var(--rl-font-data);font-size:48px;font-weight:700;color:var(--rl-color-cool-white);line-height:1.1}
.rl-guide-hero-stat__unit{font-family:var(--rl-font-data);font-size:20px;font-weight:700;color:var(--rl-color-orange);letter-spacing:2px;text-transform:uppercase;margin-left:4px}
.rl-guide-hero-stat__context{font-family:var(--rl-font-editorial);font-size:14px;color:var(--rl-color-light-steel);margin-top:8px;line-height:1.7}
@media(max-width:768px){.rl-guide-hero-stat{padding:var(--rl-spacing-lg) var(--rl-spacing-md)}.rl-guide-hero-stat__value{font-size:36px}.rl-guide-hero-stat__unit{font-size:16px}}

/* ── Prose Subheading (### in lesson content) ── */
.rl-guide-prose-h{font-family:var(--rl-font-data);font-size:12px;font-weight:700;letter-spacing:2px;text-transform:uppercase;color:var(--rl-color-secondary-blue);margin:28px 0 12px;padding-bottom:6px;border-bottom:2px solid var(--rl-color-light-steel)}

/* ── Black Box (Incident Report) ── */
.rl-guide-blackbox{background:var(--rl-color-near-black);border:3px solid var(--rl-color-near-black);margin:0 0 24px}
.rl-guide-blackbox-label{font-family:var(--rl-font-data);font-size:10px;font-weight:700;letter-spacing:3px;text-transform:uppercase;color:var(--rl-color-error);padding:12px 24px;border-bottom:1px solid var(--rl-color-error)}
.rl-guide-blackbox-body{padding:20px 24px}
.rl-guide-blackbox-body p{font-family:var(--rl-font-data);font-size:12px;line-height:1.8;color:var(--rl-color-light-steel);margin:0 0 14px;opacity:0.75}
.rl-guide-blackbox-body p:last-child{margin-bottom:0;opacity:1;font-weight:700;color:var(--rl-color-cool-white)}

/* ── Sensation Target ── */
.rl-guide-sensation{border-left:6px solid var(--rl-color-signal-red);border-top:1px solid var(--rl-color-light-steel);border-right:1px solid var(--rl-color-light-steel);border-bottom:1px solid var(--rl-color-light-steel);background:var(--rl-color-cool-white);padding:20px 24px;margin:0 0 24px}
.rl-guide-sensation-kicker{font-family:var(--rl-font-data);font-size:10px;font-weight:700;letter-spacing:3px;text-transform:uppercase;color:var(--rl-color-signal-red);margin-bottom:4px}
.rl-guide-sensation-label{font-family:var(--rl-font-editorial);font-size:18px;font-weight:700;color:var(--rl-color-near-black);margin-bottom:10px}
.rl-guide-sensation-body p{font-family:var(--rl-font-editorial);font-size:13px;line-height:1.7;color:var(--rl-color-primary-navy);margin:0 0 10px}
.rl-guide-sensation-body p:last-child{margin-bottom:0}

/* ── Named Tool (process) ── */
.rl-guide-tool{border:3px solid var(--rl-color-near-black);background:var(--rl-color-cool-white);margin:0 0 24px}
.rl-guide-tool-header{background:var(--rl-color-signal-red);padding:12px 20px}
.rl-guide-tool-kicker{font-family:var(--rl-font-data);font-size:10px;font-weight:700;letter-spacing:3px;text-transform:uppercase;color:var(--rl-color-cool-white);opacity:0.85;margin-bottom:2px}
.rl-guide-tool-title{font-family:var(--rl-font-data);font-size:16px;font-weight:700;letter-spacing:1px;text-transform:uppercase;color:var(--rl-color-white)}
.rl-guide-tool-desc{font-family:var(--rl-font-editorial);font-style:italic;font-size:13px;color:var(--rl-color-secondary-blue);padding:12px 20px;border-bottom:2px solid var(--rl-color-light-steel)}
.rl-guide-tool-step{display:flex;gap:16px;padding:14px 20px;border-bottom:1px solid var(--rl-color-light-steel)}
.rl-guide-tool-step:last-child{border-bottom:none}
.rl-guide-tool-step-num{font-family:var(--rl-font-data);font-size:22px;font-weight:700;color:var(--rl-color-signal-red);min-width:28px;line-height:1.2}
.rl-guide-tool-step-action{font-family:var(--rl-font-data);font-size:13px;font-weight:700;color:var(--rl-color-near-black)}
.rl-guide-tool-step-detail{font-family:var(--rl-font-editorial);font-size:13px;line-height:1.6;color:var(--rl-color-primary-navy);margin-top:2px}

/* ── Field Drill ── */
.rl-guide-drill{border:3px solid var(--rl-color-near-black);background:var(--rl-color-cool-white);margin:0 0 24px}
.rl-guide-drill-header{background:var(--rl-color-orange);padding:12px 20px}
.rl-guide-drill-kicker{font-family:var(--rl-font-data);font-size:10px;font-weight:700;letter-spacing:3px;text-transform:uppercase;color:var(--rl-color-near-black);display:flex;align-items:center;gap:10px;margin-bottom:2px}
.rl-guide-drill-time{background:var(--rl-color-near-black);color:var(--rl-color-cool-white);padding:2px 8px;font-size:9px;letter-spacing:2px}
.rl-guide-drill-title{font-family:var(--rl-font-editorial);font-size:17px;font-weight:700;color:var(--rl-color-near-black)}
.rl-guide-drill-desc{font-family:var(--rl-font-editorial);font-style:italic;font-size:13px;color:var(--rl-color-secondary-blue);padding:12px 20px;border-bottom:2px solid var(--rl-color-light-steel)}
.rl-guide-drill-variant{padding:16px 20px;border-bottom:1px solid var(--rl-color-light-steel)}
.rl-guide-drill-variant:last-of-type{border-bottom:none}
.rl-guide-drill-level{display:inline-block;font-family:var(--rl-font-data);font-size:9px;font-weight:700;letter-spacing:2px;text-transform:uppercase;padding:3px 10px;border:2px solid var(--rl-color-secondary-blue);color:var(--rl-color-secondary-blue);margin-bottom:6px}
.rl-guide-drill-level--beginner{border-color:var(--rl-color-signal-red);color:var(--rl-color-signal-red)}
.rl-guide-drill-level--intermediate{border-color:var(--rl-color-orange);color:var(--rl-color-orange)}
.rl-guide-drill-level--race-pace{border-color:var(--rl-color-error);color:var(--rl-color-error)}
.rl-guide-drill-variant-label{font-family:var(--rl-font-editorial);font-style:italic;font-size:13px;color:var(--rl-color-secondary-blue);margin-bottom:8px}
.rl-guide-drill-steps{font-family:var(--rl-font-editorial);font-size:13px;line-height:1.7;color:var(--rl-color-near-black);padding-left:20px;margin:0}
.rl-guide-drill-steps li{margin-bottom:6px}
.rl-guide-drill-gate{border-top:3px solid var(--rl-color-signal-red);padding:14px 20px;background:var(--rl-color-silver)}
.rl-guide-drill-gate-label{font-family:var(--rl-font-data);font-size:10px;font-weight:700;letter-spacing:3px;text-transform:uppercase;color:var(--rl-color-signal-red);margin-bottom:4px}
.rl-guide-drill-gate-target{font-family:var(--rl-font-data);font-size:12px;line-height:1.6;color:var(--rl-color-near-black)}

/* ── Recovery Protocol ── */
.rl-guide-recovery{border:3px solid var(--rl-color-near-black);background:var(--rl-color-cool-white);margin:0 0 24px}
.rl-guide-recovery-label{background:var(--rl-color-error);color:var(--rl-color-white);padding:10px 20px;font-family:var(--rl-font-data);font-size:10px;font-weight:700;letter-spacing:3px;text-transform:uppercase}
.rl-guide-recovery .rl-guide-accordion-item{border:none;border-bottom:1px solid var(--rl-color-light-steel);margin-bottom:0}
.rl-guide-recovery .rl-guide-accordion-item:last-child{border-bottom:none}
.rl-guide-recovery .rl-guide-accordion-body{border-top:1px solid var(--rl-color-light-steel)}
.rl-guide-recovery-situation{font-family:var(--rl-font-editorial);font-style:italic;font-size:13px;color:var(--rl-color-secondary-blue);margin:0 0 10px}
.rl-guide-recovery-steps{font-family:var(--rl-font-editorial);font-size:13px;line-height:1.7;color:var(--rl-color-near-black);padding-left:20px;margin:0}
.rl-guide-recovery-steps li{margin-bottom:5px}

/* ── Commitment ── */
.rl-guide-commitment{border:3px solid var(--rl-color-orange);border-left-width:8px;background:var(--rl-color-cool-white);padding:18px 24px;margin:0 0 24px}
.rl-guide-commitment-kicker{font-family:var(--rl-font-data);font-size:10px;font-weight:700;letter-spacing:3px;text-transform:uppercase;color:var(--rl-color-orange);margin-bottom:8px}
.rl-guide-commitment-body p{font-family:var(--rl-font-editorial);font-size:14px;line-height:1.7;font-weight:700;color:var(--rl-color-near-black);margin:0 0 8px}
.rl-guide-commitment-body p:last-child{margin-bottom:0}

/* ── New Block Responsive ── */
@media(max-width:768px){
  .rl-guide-blackbox-body{padding:16px}
  .rl-guide-blackbox-label{padding:10px 16px}
  .rl-guide-sensation{padding:16px}
  .rl-guide-tool-step{gap:10px;padding:12px 14px}
  .rl-guide-tool-header,.rl-guide-drill-header{padding:10px 14px}
  .rl-guide-tool-desc,.rl-guide-drill-desc,.rl-guide-drill-variant,.rl-guide-drill-gate{padding-left:14px;padding-right:14px}
  .rl-guide-commitment{padding:14px 16px}
}

/* ── Visually hidden utility ── */
.rl-vh{position:absolute;width:1px;height:1px;padding:0;margin:-1px;overflow:hidden;clip:rect(0,0,0,0);white-space:nowrap;border:0}

/* ── Labeled Graphic (hotspot block) ──
   Progressive enhancement: markers hidden + fallback list visible by
   default. JS adds .rl-lg-ready to flip both. Content is never hidden
   without JS. */
.rl-guide-labeled-graphic{margin:0 0 24px;border:3px solid var(--rl-color-near-black);background:var(--rl-color-cool-white)}
.rl-guide-lg-stage{position:relative;line-height:0}
.rl-guide-lg-img{width:100%;height:auto;display:block}
.rl-guide-lg-marker{display:none;position:absolute;transform:translate(-50%,-50%);width:32px;height:32px;min-width:32px;min-height:32px;border:3px solid var(--rl-color-cool-white);background:var(--rl-color-signal-red);color:var(--rl-color-white);font-family:var(--rl-font-data);font-size:14px;font-weight:700;line-height:1;cursor:pointer;align-items:center;justify-content:center;padding:0;z-index:2}
.rl-lg-ready .rl-guide-lg-marker{display:flex}
.rl-guide-lg-marker:hover,.rl-guide-lg-marker[aria-expanded="true"]{background:var(--rl-color-near-black)}
.rl-guide-lg-marker:focus-visible{outline:3px solid var(--rl-color-orange);outline-offset:2px}
.rl-guide-lg-popover{position:absolute;z-index:3;width:min(280px,72%);max-height:94%;overflow-y:auto;background:var(--rl-color-cool-white);border:3px solid var(--rl-color-near-black);padding:14px 16px;line-height:1.5;text-align:left}
.rl-guide-lg-pop-title{font-family:var(--rl-font-data);font-size:12px;font-weight:700;letter-spacing:1px;text-transform:uppercase;color:var(--rl-color-signal-red);margin:0 28px 6px 0}
.rl-guide-lg-pop-body{font-family:var(--rl-font-editorial);font-size:13px;color:var(--rl-color-near-black);margin:0}
.rl-guide-lg-pop-detail{font-family:var(--rl-font-editorial);font-size:12px;color:var(--rl-color-secondary-blue);margin:8px 0 0}
.rl-guide-lg-pop-close{position:absolute;top:4px;right:4px;width:28px;height:28px;border:2px solid var(--rl-color-near-black);background:var(--rl-color-cool-white);color:var(--rl-color-near-black);font-size:16px;line-height:1;cursor:pointer;font-family:var(--rl-font-data);padding:0}
.rl-guide-lg-pop-close:hover{border-color:var(--rl-color-signal-red);color:var(--rl-color-signal-red)}
.rl-guide-lg-fallback{list-style:decimal;margin:0;padding:16px 16px 16px 40px;border-top:3px solid var(--rl-color-near-black);line-height:1.6}
.rl-guide-lg-item{font-family:var(--rl-font-editorial);font-size:13px;color:var(--rl-color-primary-navy);margin-bottom:8px}
.rl-guide-lg-item-title{color:var(--rl-color-near-black)}
.rl-guide-lg-item-detail{color:var(--rl-color-secondary-blue)}
.rl-lg-ready .rl-guide-lg-fallback{position:absolute;width:1px;height:1px;padding:0;margin:-1px;overflow:hidden;clip:rect(0,0,0,0);white-space:nowrap;border:0}
@media(prefers-reduced-motion:no-preference){
.rl-guide-lg-marker{animation:rl-lg-pulse 2.4s ease-in-out infinite}
.rl-guide-lg-marker[aria-expanded="true"],.rl-guide-lg-marker:focus-visible{animation:none}
@keyframes rl-lg-pulse{0%,100%{transform:translate(-50%,-50%) scale(1)}50%{transform:translate(-50%,-50%) scale(1.12)}}
}

/* ── Sorting Activity ── */
.rl-guide-sorting{border:3px solid var(--rl-color-near-black);background:var(--rl-color-cool-white);margin:0 0 24px}
.rl-guide-sorting-label{background:var(--rl-color-signal-red);color:var(--rl-color-white);padding:8px 16px;font-family:var(--rl-font-data);font-size:10px;font-weight:700;letter-spacing:3px;text-transform:uppercase}
.rl-guide-sorting-title{font-family:var(--rl-font-editorial);font-size:16px;font-weight:700;color:var(--rl-color-near-black);margin:0;padding:16px 20px 0}
.rl-guide-sorting-instructions{font-family:var(--rl-font-editorial);font-size:13px;color:var(--rl-color-secondary-blue);margin:0;padding:6px 20px 0}
.rl-guide-sorting-stack{padding:16px 20px 8px}
.rl-guide-sorting-card{border:2px solid var(--rl-color-near-black);background:var(--rl-color-silver);padding:14px 16px;margin-bottom:8px}
.rl-guide-sorting-card p{font-family:var(--rl-font-editorial);font-size:14px;color:var(--rl-color-near-black);margin:0;line-height:1.5}
.rl-sorting-ready .rl-guide-sorting-card{display:none;margin-bottom:0}
.rl-sorting-ready .rl-guide-sorting-card.rl-sorting-current{display:block}
.rl-guide-sorting-card.rl-sorting-correct,.rl-guide-sorting-card.rl-sorting-fly{border-color:var(--rl-color-signal-red)}
.rl-guide-sorting-card.rl-sorting-correct p::after,.rl-guide-sorting-card.rl-sorting-fly p::after{content:' \\2713';color:var(--rl-color-signal-red);font-weight:700;font-family:var(--rl-font-data)}
.rl-guide-sorting-card.rl-sorting-wrong{border-color:var(--rl-color-error)}
.rl-guide-sorting-cats{display:none;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:10px;padding:0 20px 16px}
.rl-sorting-ready .rl-guide-sorting-cats{display:grid}
.rl-guide-sorting-cat{border:3px solid var(--rl-color-near-black);background:var(--rl-color-cool-white);min-height:56px;cursor:pointer;font-family:var(--rl-font-data);font-size:12px;font-weight:700;letter-spacing:1px;text-transform:uppercase;color:var(--rl-color-near-black);display:flex;align-items:center;justify-content:space-between;gap:8px;padding:10px 14px;text-align:left}
.rl-guide-sorting-cat:hover{border-color:var(--rl-color-signal-red);color:var(--rl-color-signal-red)}
.rl-guide-sorting-cat:disabled{opacity:.6;cursor:default}
.rl-guide-sorting-cat:focus-visible{outline:3px solid var(--rl-color-orange);outline-offset:2px}
.rl-guide-sorting-cat.rl-sorting-cat-hit{border-color:var(--rl-color-signal-red);color:var(--rl-color-signal-red)}
.rl-guide-sorting-cat-count{border:2px solid currentColor;min-width:26px;text-align:center;padding:2px 4px}
.rl-guide-sorting-progress{font-family:var(--rl-font-data);font-size:11px;letter-spacing:1px;color:var(--rl-color-secondary-blue);padding:0 20px 16px}
.rl-guide-sorting-progress:empty{padding:0}
.rl-guide-sorting-done{font-family:var(--rl-font-data);font-size:13px;font-weight:700;letter-spacing:1px;color:var(--rl-color-signal-red);padding:0 20px 16px}
@media(prefers-reduced-motion:no-preference){
.rl-guide-sorting-card.rl-sorting-fly{animation:rl-sorting-fly .45s ease-in forwards}
@keyframes rl-sorting-fly{0%{opacity:1;transform:translateY(0) scale(1)}100%{opacity:0;transform:translateY(46px) scale(.85)}}
.rl-guide-sorting-card.rl-sorting-shake{animation:rl-sorting-shake .35s ease-in-out}
@keyframes rl-sorting-shake{0%,100%{transform:translateX(0)}25%{transform:translateX(-6px)}75%{transform:translateX(6px)}}
}

/* ── Continue Gate ──
   Progressive enhancement contract: this markup hides NOTHING. The
   .rl-gate-closed class below only ever appears on a wrapper div that JS
   creates — with JS off, no wrapper exists and all content is visible. */
.rl-guide-continue-gate{margin:0 0 24px;border-top:3px solid var(--rl-color-near-black);padding-top:16px}
.rl-guide-continue-btn{display:block;width:100%;background:var(--rl-color-signal-red);color:var(--rl-color-white);border:3px solid var(--rl-color-near-black);font-family:var(--rl-font-data);font-size:13px;font-weight:700;letter-spacing:2px;text-transform:uppercase;padding:14px 16px;cursor:pointer}
.rl-guide-continue-btn:hover{background:var(--rl-color-near-black)}
.rl-guide-continue-btn:disabled{background:var(--rl-color-cool-white);color:var(--rl-color-secondary-blue);cursor:not-allowed}
.rl-guide-continue-btn:focus-visible{outline:3px solid var(--rl-color-orange);outline-offset:2px}
.rl-guide-continue-gate.rl-gate-passed .rl-guide-continue-btn{background:var(--rl-color-cool-white);color:var(--rl-color-signal-red);cursor:default}
.rl-guide-continue-hint{font-family:var(--rl-font-data);font-size:11px;letter-spacing:1px;color:var(--rl-color-secondary-blue);margin:8px 0 0;text-align:center}
.rl-gate-wrap.rl-gate-closed{max-height:0;overflow:hidden}
.rl-gate-wrap.rl-gate-opening{overflow:hidden}
@media(prefers-reduced-motion:no-preference){
.rl-gate-wrap.rl-gate-opening{transition:max-height .45s ease-out}
}

/* ── Knowledge Check: fill-in-the-blank ── */
.rl-guide-kc-fib{display:flex;gap:8px;padding:8px 20px;flex-wrap:wrap}
.rl-guide-kc-fib-input{flex:1;min-width:180px;border:2px solid var(--rl-color-near-black);background:var(--rl-color-white);font-family:var(--rl-font-data);font-size:13px;padding:10px 12px}
.rl-guide-kc-fib-input.rl-kc-fib-correct{border-color:var(--rl-color-signal-red)}
.rl-guide-kc-fib-input.rl-kc-fib-wrong{border-color:var(--rl-color-error)}
.rl-guide-kc-fib-check{border:2px solid var(--rl-color-near-black);background:var(--rl-color-signal-red);color:var(--rl-color-white);font-family:var(--rl-font-data);font-size:12px;font-weight:700;letter-spacing:1.5px;text-transform:uppercase;padding:10px 20px;cursor:pointer}
.rl-guide-kc-fib-check:hover{background:var(--rl-color-near-black)}
.rl-guide-kc-fib-check:disabled{opacity:.6;cursor:default}
.rl-guide-kc-fib-status{font-family:var(--rl-font-data);font-size:11px;letter-spacing:1px;color:var(--rl-color-secondary-blue);padding:0 20px 12px}
.rl-guide-kc-fib-status:empty{padding:0}

/* ── Knowledge Check: matching ── */
.rl-guide-kc-match-hint{font-family:var(--rl-font-data);font-size:11px;letter-spacing:1px;color:var(--rl-color-secondary-blue);margin:0;padding:0 20px 8px}
.rl-guide-kc-match{display:grid;grid-template-columns:1fr 1fr;gap:8px;padding:8px 20px 16px}
.rl-guide-kc-match-col{display:flex;flex-direction:column;gap:8px}
.rl-guide-kc-match-left,.rl-guide-kc-match-right{padding:10px 14px;background:var(--rl-color-cool-white);border:2px solid var(--rl-color-near-black);cursor:pointer;font-family:var(--rl-font-data);font-size:12px;text-align:left;color:var(--rl-color-near-black)}
.rl-guide-kc-match-left:focus-visible,.rl-guide-kc-match-right:focus-visible{outline:3px solid var(--rl-color-orange);outline-offset:2px}
.rl-guide-kc-match-left.rl-kc-match-selected{border-color:var(--rl-color-signal-red);background:var(--rl-color-silver)}
.rl-kc-match-locked{border-color:var(--rl-color-signal-red);color:var(--rl-color-signal-red);cursor:default}
.rl-kc-match-wrong{border-color:var(--rl-color-error)}

/* ── Inline Infographics ── */
.rl-infographic{margin:0 0 20px;line-height:1.4}
.rl-infographic--full-width{margin-left:-24px;margin-right:-24px}
.rl-infographic-caption{font-size:11px;color:var(--rl-color-light-steel);padding:8px 12px;line-height:1.5;font-family:var(--rl-font-data);letter-spacing:0.5px;background:var(--rl-color-near-black);border:3px solid var(--rl-color-near-black);border-top:4px double var(--rl-color-near-black);margin-top:0}
.rl-infographic-svg{display:block;width:100%;height:auto}
.rl-infographic-card{border:3px solid var(--rl-color-near-black);padding:16px;background:var(--rl-color-cool-white)}
.rl-infographic-card-icon{margin-bottom:8px}
.rl-infographic-card-title{font-family:var(--rl-font-editorial);font-size:15px;font-weight:700;text-transform:uppercase;letter-spacing:1px;color:var(--rl-color-primary-navy);margin-bottom:4px;border-bottom:2px solid var(--rl-color-orange);padding-bottom:4px}
.rl-infographic-card-desc{font-family:var(--rl-font-editorial);font-size:12px;line-height:1.6;color:var(--rl-color-near-black)}
.rl-infographic-gear-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:12px}
.rl-infographic-rider-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:12px}
.rl-infographic-rider-card{border:3px solid var(--rl-color-near-black);padding:16px;background:var(--rl-color-cool-white)}
.rl-infographic-rider-name{font-family:var(--rl-font-editorial);font-size:18px;font-weight:700;text-transform:uppercase;letter-spacing:1px;color:var(--rl-color-primary-navy);margin-bottom:4px;border-bottom:2px solid var(--rl-color-orange);padding-bottom:4px}
.rl-infographic-rider-hours{font-family:var(--rl-font-data);font-size:13px;color:var(--rl-color-secondary-blue);margin-bottom:8px}
.rl-infographic-rider-bar-wrap{height:8px;background:var(--rl-color-light-steel);margin-bottom:4px}
.rl-infographic-rider-bar{height:100%;background:var(--rl-color-signal-red)}
.rl-infographic-rider-ftp{font-family:var(--rl-font-data);font-size:12px;font-weight:700;color:var(--rl-color-near-black);margin-bottom:8px}
.rl-infographic-rider-meta{font-family:var(--rl-font-data);font-size:11px;color:var(--rl-color-secondary-blue);display:flex;flex-direction:column;gap:2px}
.rl-infographic-week-grid{display:grid;grid-template-columns:repeat(7,1fr);gap:8px}
.rl-infographic-day-card{border:3px solid var(--rl-color-near-black);padding:12px 8px;background:var(--rl-color-cool-white);text-align:center}
.rl-infographic-day-card--race{background:var(--rl-color-signal-red);border-color:var(--rl-color-signal-red)}
.rl-infographic-day-card--race .rl-infographic-day-abbr,.rl-infographic-day-card--race .rl-infographic-day-task,.rl-infographic-day-card--race .rl-infographic-day-note{color:var(--rl-color-cool-white)}
.rl-infographic-day-abbr{font-family:var(--rl-font-data);font-size:11px;font-weight:700;letter-spacing:2px;color:var(--rl-color-secondary-blue);margin-bottom:4px}
.rl-infographic-day-task{font-family:var(--rl-font-editorial);font-size:13px;font-weight:700;color:var(--rl-color-primary-navy);margin-bottom:4px}
.rl-infographic-day-note{font-family:var(--rl-font-data);font-size:10px;color:var(--rl-color-secondary-blue);line-height:1.4}
.rl-infographic-traffic-light{display:flex;flex-direction:column;gap:12px}
.rl-infographic-signal-row{display:flex;gap:16px;border:3px solid var(--rl-color-near-black);padding:16px;background:var(--rl-color-cool-white);align-items:flex-start}
.rl-infographic-signal-indicator{width:32px;height:32px;flex-shrink:0}
.rl-infographic-signal-label{font-family:var(--rl-font-data);font-size:14px;font-weight:700;letter-spacing:2px;color:var(--rl-color-near-black);margin-bottom:4px}
.rl-infographic-signal-criteria{font-family:var(--rl-font-editorial);font-size:12px;color:var(--rl-color-secondary-blue);margin-bottom:4px}
.rl-infographic-signal-action{font-family:var(--rl-font-editorial);font-size:13px;font-weight:700;color:var(--rl-color-near-black)}
.rl-infographic-three-acts{display:grid;grid-template-columns:repeat(3,1fr);gap:12px}
.rl-infographic-act-panel{border:3px solid var(--rl-color-near-black);padding:16px;background:var(--rl-color-cool-white)}
.rl-infographic-act-num{font-family:var(--rl-font-data);font-size:10px;font-weight:700;letter-spacing:3px;color:var(--rl-color-secondary-blue);margin-bottom:2px}
.rl-infographic-act-title{font-family:var(--rl-font-editorial);font-size:20px;font-weight:700;text-transform:uppercase;letter-spacing:1px;color:var(--rl-color-primary-navy);border-bottom:2px solid var(--rl-color-orange);padding-bottom:4px;margin-bottom:4px}
.rl-infographic-act-range{font-family:var(--rl-font-data);font-size:12px;color:var(--rl-color-signal-red);font-weight:700;margin-bottom:8px}
.rl-infographic-act-list{font-family:var(--rl-font-editorial);font-size:12px;line-height:1.6;color:var(--rl-color-near-black);padding-left:16px;margin:0}
.rl-infographic-act-list li{margin-bottom:4px}
.rl-infographic-bonk-math{text-align:center;padding:24px;border:3px solid var(--rl-color-near-black);background:var(--rl-color-cool-white)}
.rl-infographic-bonk-equation{display:flex;align-items:baseline;justify-content:center;gap:12px;margin-bottom:8px}
.rl-infographic-bonk-num{font-family:var(--rl-font-data);font-size:48px;font-weight:700;color:var(--rl-color-primary-navy)}
.rl-infographic-bonk-op{font-family:var(--rl-font-data);font-size:32px;color:var(--rl-color-secondary-blue)}
.rl-infographic-bonk-total{font-family:var(--rl-font-data);font-size:56px;font-weight:700;color:var(--rl-color-signal-red)}
.rl-infographic-bonk-subtitle{font-family:var(--rl-font-editorial);font-size:14px;color:var(--rl-color-secondary-blue);margin-bottom:20px}
.rl-infographic-bonk-grid{display:grid;grid-template-columns:repeat(12,1fr);gap:4px;max-width:480px;margin:0 auto 8px}
.rl-infographic-bonk-gel{height:24px;background:var(--rl-color-orange);border:2px solid var(--rl-color-near-black)}
.rl-infographic-bonk-label{font-family:var(--rl-font-data);font-size:12px;color:var(--rl-color-secondary-blue);letter-spacing:1px}

/* ── Flip Cards ── */
.rl-infographic-card--flip{cursor:pointer;min-height:160px;position:relative}
.rl-infographic-card--flip .rl-infographic-card-front,.rl-infographic-card--flip .rl-infographic-card-back{padding:16px}
.rl-infographic-card--flip .rl-infographic-card-back{display:none;background:var(--rl-color-near-black);color:var(--rl-color-cool-white)}
.rl-infographic-card--flip.flipped .rl-infographic-card-front{display:none}
.rl-infographic-card--flip.flipped .rl-infographic-card-back{display:block}
.rl-infographic-card-back .rl-infographic-card-title{color:var(--rl-color-cool-white);border-bottom-color:var(--rl-color-orange)}
.rl-infographic-card-back .rl-infographic-card-desc{color:var(--rl-color-light-steel)}
.rl-infographic-card-flip-hint{font-family:var(--rl-font-data);font-size:10px;color:var(--rl-color-secondary-blue);letter-spacing:1px;text-align:center;margin-top:8px}

/* ── Infographic Accordion ── */
.rl-infographic-accordion{display:flex;flex-direction:column;gap:8px}
.rl-infographic-accordion-item{border:3px solid var(--rl-color-near-black);background:var(--rl-color-cool-white)}
.rl-infographic-accordion-header{display:flex;justify-content:space-between;align-items:center;padding:14px 16px;cursor:pointer;border:none;width:100%;background:var(--rl-color-cool-white);font-family:var(--rl-font-editorial);font-size:14px;font-weight:700;color:var(--rl-color-primary-navy);text-align:left}
.rl-infographic-accordion-header:hover{background:var(--rl-color-silver)}
.rl-infographic-accordion-icon{font-size:18px;font-weight:700;color:var(--rl-color-signal-red)}
.rl-infographic-accordion-body{display:none;padding:16px;border-top:2px solid var(--rl-color-near-black)}
.rl-infographic-accordion-item.open .rl-infographic-accordion-body{display:block}
.rl-infographic-accordion-item.open .rl-infographic-accordion-icon{color:var(--rl-color-orange)}
.rl-infographic-accordion-sparkline{display:block;margin-bottom:8px}

/* ── Traffic Light States ── */
.rl-infographic-signal-row[data-state]{cursor:pointer}
.rl-infographic-signal-row[data-state="go"] .rl-infographic-signal-indicator rect{fill:var(--rl-color-signal-red)}
.rl-infographic-signal-row[data-state="caution"] .rl-infographic-signal-indicator rect{fill:var(--rl-color-orange)}
.rl-infographic-signal-row[data-state="stop"] .rl-infographic-signal-indicator rect{fill:var(--rl-color-error)}

/* ── Timeline Nodes ── */
.rl-infographic-timeline{display:flex;flex-direction:column;gap:0}
.rl-infographic-timeline-node{border:3px solid var(--rl-color-near-black);padding:16px;background:var(--rl-color-cool-white);position:relative;margin-bottom:-3px}
.rl-infographic-timeline-node--highlight{background:var(--rl-color-signal-red);border-color:var(--rl-color-signal-red)}
.rl-infographic-timeline-node--highlight .rl-infographic-timeline-label,.rl-infographic-timeline-node--highlight .rl-infographic-timeline-summary,.rl-infographic-timeline-node--highlight .rl-infographic-timeline-tag{color:var(--rl-color-cool-white)}
.rl-infographic-timeline-header{display:flex;justify-content:space-between;align-items:center;cursor:pointer}
.rl-infographic-timeline-label{font-family:var(--rl-font-editorial);font-size:15px;font-weight:700;color:var(--rl-color-primary-navy)}
.rl-infographic-timeline-tag{font-family:var(--rl-font-data);font-size:11px;font-weight:700;letter-spacing:2px;color:var(--rl-color-secondary-blue)}
.rl-infographic-timeline-summary{font-family:var(--rl-font-editorial);font-size:12px;color:var(--rl-color-secondary-blue);margin-top:4px}
.rl-infographic-timeline-detail{display:none;padding-top:12px;border-top:2px solid var(--rl-color-light-steel);margin-top:12px;font-family:var(--rl-font-editorial);font-size:13px;color:var(--rl-color-near-black);line-height:1.6}
.rl-infographic-timeline-node.open .rl-infographic-timeline-detail{display:block}
.rl-infographic-timeline-expand{font-family:var(--rl-font-data);font-size:14px;font-weight:700;color:var(--rl-color-signal-red);cursor:pointer;background:none;border:none;padding:0}

/* ── Pyramid Bars ── */
.rl-infographic-pyramid{display:flex;flex-direction:column;align-items:center;gap:4px}
.rl-infographic-pyramid-row{display:flex;align-items:center;gap:12px}
.rl-infographic-pyramid-bar{height:28px;display:flex;align-items:center;justify-content:flex-end;padding-right:8px;border:2px solid var(--rl-color-near-black)}
.rl-infographic-pyramid-label{font-family:var(--rl-font-data);font-size:12px;font-weight:700;color:var(--rl-color-near-black);min-width:40px;text-align:right}
.rl-infographic-pyramid-value{font-family:var(--rl-font-data);font-size:11px;font-weight:700;color:var(--rl-color-cool-white);letter-spacing:1px}

/* ── Heatmap Grid ── */
.rl-infographic-heatmap{display:grid;gap:2px}
.rl-infographic-heatmap-cell{padding:8px;text-align:center;border:2px solid var(--rl-color-near-black);font-family:var(--rl-font-data);font-size:11px;font-weight:700}
.rl-infographic-heatmap-cell[data-v="1"]{background:var(--rl-color-silver);color:var(--rl-color-near-black)}
.rl-infographic-heatmap-cell[data-v="2"]{background:var(--rl-color-light-steel);color:var(--rl-color-near-black)}
.rl-infographic-heatmap-cell[data-v="3"]{background:var(--rl-color-orange);color:var(--rl-color-cool-white)}
.rl-infographic-heatmap-cell[data-v="4"]{background:var(--rl-color-signal-red);color:var(--rl-color-cool-white)}
.rl-infographic-heatmap-cell[data-v="5"]{background:var(--rl-color-near-black);color:var(--rl-color-cool-white)}
.rl-infographic-heatmap-header{font-family:var(--rl-font-data);font-size:10px;font-weight:700;letter-spacing:2px;color:var(--rl-color-secondary-blue);text-align:center;padding:6px 4px}

/* ── Sortable Table ── */
.rl-infographic-sortable th{cursor:pointer;user-select:none}
.rl-infographic-sortable th:hover{background:var(--rl-color-signal-red);color:var(--rl-color-cool-white)}
.rl-infographic-sort-indicator{font-size:10px;margin-left:4px}

/* ── Gauge ── */
.rl-gauge{text-align:center}
.rl-gauge--sm{max-width:120px}
.rl-gauge__fill{transition:stroke-dashoffset 1.5s cubic-bezier(0.25,0.46,0.45,0.94)}
.rl-gauge__value{font-family:var(--rl-font-data);font-size:20px;font-weight:700;color:var(--rl-color-primary-navy);margin-top:4px}
.rl-gauge__label{font-family:var(--rl-font-data);font-size:11px;color:var(--rl-color-secondary-blue);letter-spacing:1px}

/* ── Glycogen Compare ── */
.rl-infographic-glycogen-compare{display:grid;grid-template-columns:1fr 1fr;gap:16px}
.rl-infographic-glycogen-panel{border:3px solid var(--rl-color-near-black);padding:16px;background:var(--rl-color-cool-white)}
.rl-infographic-glycogen-title{font-family:var(--rl-font-editorial);font-size:14px;font-weight:700;color:var(--rl-color-primary-navy);margin-bottom:12px;border-bottom:2px solid var(--rl-color-orange);padding-bottom:4px}
.rl-infographic-glycogen-gauges{display:grid;grid-template-columns:repeat(4,1fr);gap:8px;margin-bottom:12px}
.rl-infographic-glycogen-summary{font-family:var(--rl-font-editorial);font-size:12px;color:var(--rl-color-secondary-blue);font-style:italic}

/* ── Macro Split Progress ── */
.rl-infographic-macro-grid{display:flex;flex-direction:column;gap:12px}
.rl-infographic-macro-row{display:flex;align-items:center;gap:12px}
.rl-infographic-macro-label{font-family:var(--rl-font-editorial);font-size:13px;font-weight:700;color:var(--rl-color-primary-navy);min-width:80px}
.rl-infographic-macro-track{flex:1;height:24px;background:var(--rl-color-silver);border:2px solid var(--rl-color-near-black);position:relative;overflow:hidden}
.rl-infographic-macro-fill{height:100%;display:flex;align-items:center;justify-content:flex-end;padding-right:8px;position:relative;overflow:hidden}
.rl-infographic-macro-fill::before{content:"";position:absolute;top:0;left:-100%;width:100%;height:100%;background:linear-gradient(90deg,transparent 0%,color-mix(in srgb,var(--rl-color-white) 25%,transparent) 50%,transparent 100%)}
.rl-infographic-macro-value{font-family:var(--rl-font-data);font-size:11px;font-weight:700;color:var(--rl-color-cool-white);letter-spacing:1px}

/* ── Calorie Waterfall ── */
.rl-infographic-waterfall{display:flex;align-items:flex-end;gap:4px;height:200px;padding:16px;border:3px solid var(--rl-color-near-black);background:var(--rl-color-cool-white)}
.rl-infographic-waterfall-col{flex:1;display:flex;flex-direction:column;align-items:center;gap:4px}
.rl-infographic-waterfall-bar{width:100%;border:2px solid var(--rl-color-near-black)}
.rl-infographic-waterfall-label{font-family:var(--rl-font-data);font-size:10px;color:var(--rl-color-secondary-blue);letter-spacing:1px}
.rl-infographic-waterfall-val{font-family:var(--rl-font-data);font-size:11px;font-weight:700;color:var(--rl-color-primary-navy)}

/* ── Recovery Dash ── */
.rl-infographic-recovery-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:16px}
.rl-infographic-recovery-card{border:3px solid var(--rl-color-near-black);padding:16px;background:var(--rl-color-cool-white);text-align:center}
.rl-infographic-recovery-title{font-family:var(--rl-font-editorial);font-size:14px;font-weight:700;color:var(--rl-color-primary-navy);margin-bottom:8px}
.rl-infographic-recovery-status{font-family:var(--rl-font-data);font-size:11px;font-weight:700;letter-spacing:1px;margin-top:8px}

/* ── Sleep Tracker ── */
.rl-sleep-tracker{border:3px solid var(--rl-color-near-black);background:var(--rl-color-cool-white)}
.rl-sleep-tracker__header{background:var(--rl-color-near-black);padding:8px 16px}
.rl-sleep-tracker__title{font-family:var(--rl-font-editorial);font-size:13px;font-weight:700;color:var(--rl-color-light-steel);letter-spacing:2px;text-transform:uppercase}
.rl-sleep-tracker__body{padding:16px}
.rl-sleep-tracker__grid{display:grid;grid-template-columns:repeat(7,1fr);gap:8px;margin-bottom:16px}
.rl-sleep-tracker__day{border:2px solid var(--rl-color-near-black);padding:12px 8px;text-align:center;background:var(--rl-color-cool-white)}
.rl-sleep-tracker__day--deficit{border-color:var(--rl-color-error)}
.rl-sleep-tracker__day--surplus{border-color:var(--rl-color-signal-red)}
.rl-sleep-tracker__day-name{font-family:var(--rl-font-data);font-size:10px;font-weight:700;letter-spacing:2px;color:var(--rl-color-secondary-blue);margin-bottom:4px}
.rl-sleep-tracker__day-hrs{font-family:var(--rl-font-data);font-size:20px;font-weight:700;color:var(--rl-color-primary-navy)}
.rl-sleep-tracker__day-unit{font-family:var(--rl-font-data);font-size:10px;color:var(--rl-color-secondary-blue)}
.rl-sleep-tracker__day-need{font-family:var(--rl-font-data);font-size:10px;color:var(--rl-color-secondary-blue);margin-top:4px}
.rl-sleep-tracker__debt{display:flex;align-items:baseline;justify-content:center;gap:8px;padding:12px;border:3px solid var(--rl-color-error);background:var(--rl-color-cool-white)}
.rl-sleep-tracker__debt-label{font-family:var(--rl-font-editorial);font-size:13px;font-weight:700;color:var(--rl-color-primary-navy)}
.rl-sleep-tracker__debt-num{font-family:var(--rl-font-data);font-size:32px;font-weight:700;color:var(--rl-color-error)}
.rl-sleep-tracker__debt-unit{font-family:var(--rl-font-data);font-size:13px;color:var(--rl-color-secondary-blue)}

/* ── Gear Weight Toggle ── */
.rl-infographic-gear-toggle{display:flex;flex-direction:column;gap:8px}
.rl-infographic-gear-item{display:flex;align-items:center;gap:12px;padding:10px 14px;border:2px solid var(--rl-color-near-black);background:var(--rl-color-cool-white);cursor:pointer}
.rl-infographic-gear-item.active{border-color:var(--rl-color-signal-red)}
.rl-infographic-gear-item-name{font-family:var(--rl-font-editorial);font-size:13px;font-weight:700;color:var(--rl-color-primary-navy);flex:1}
.rl-infographic-gear-item-weight{font-family:var(--rl-font-data);font-size:12px;font-weight:700;color:var(--rl-color-signal-red)}
.rl-infographic-gear-item-toggle{width:20px;height:20px;border:2px solid var(--rl-color-near-black);background:var(--rl-color-silver);display:flex;align-items:center;justify-content:center;font-size:14px;font-weight:700}
.rl-infographic-gear-item.active .rl-infographic-gear-item-toggle{background:var(--rl-color-signal-red);color:var(--rl-color-cool-white);border-color:var(--rl-color-signal-red)}
.rl-infographic-gear-total{display:flex;justify-content:space-between;padding:12px 14px;border:3px solid var(--rl-color-near-black);background:var(--rl-color-near-black)}
.rl-infographic-gear-total-label{font-family:var(--rl-font-editorial);font-size:14px;font-weight:700;color:var(--rl-color-light-steel)}
.rl-infographic-gear-total-value{font-family:var(--rl-font-data);font-size:18px;font-weight:700;color:var(--rl-color-orange)}
.rl-infographic-gear-bar-track{height:12px;background:var(--rl-color-silver);border:2px solid var(--rl-color-near-black);margin-top:8px}
.rl-infographic-gear-bar-fill{height:100%;background:var(--rl-color-signal-red)}

/* ── Digit Roller ── */
.rl-infographic-digit-roller{display:flex;justify-content:center;gap:2px;overflow:hidden;height:56px}
.rl-infographic-digit{width:36px;height:56px;overflow:hidden;border:2px solid var(--rl-color-near-black);background:var(--rl-color-cool-white)}
.rl-infographic-digit-strip{display:flex;flex-direction:column}
.rl-infographic-digit-strip span{height:56px;display:flex;align-items:center;justify-content:center;font-family:var(--rl-font-data);font-size:32px;font-weight:700;color:var(--rl-color-primary-navy)}

/* ── Range Calculator ── */
.rl-infographic-range-calc{border:3px solid var(--rl-color-near-black);background:var(--rl-color-cool-white)}
.rl-infographic-range-calc__header{background:var(--rl-color-near-black);padding:8px 16px}
.rl-infographic-range-calc__title{font-family:var(--rl-font-editorial);font-size:13px;font-weight:700;color:var(--rl-color-light-steel);letter-spacing:2px;text-transform:uppercase}
.rl-infographic-range-calc__body{padding:16px}
.rl-infographic-range-slider{display:flex;flex-direction:column;gap:4px;margin-bottom:12px}
.rl-infographic-range-slider label{font-family:var(--rl-font-data);font-size:11px;font-weight:700;color:var(--rl-color-primary-navy);letter-spacing:1px}
.rl-infographic-range-slider input[type="range"]{width:100%;accent-color:var(--rl-color-signal-red);height:8px}
.rl-infographic-range-slider output{font-family:var(--rl-font-data);font-size:13px;font-weight:700;color:var(--rl-color-signal-red)}
.rl-infographic-range-calc__output{display:grid;grid-template-columns:repeat(auto-fill,minmax(160px,1fr));gap:12px;padding-top:12px;border-top:2px solid var(--rl-color-near-black)}
.rl-infographic-range-calc__result{padding:12px;border:2px solid var(--rl-color-near-black);text-align:center}
.rl-infographic-range-calc__result-label{font-family:var(--rl-font-data);font-size:10px;font-weight:700;letter-spacing:2px;color:var(--rl-color-secondary-blue);margin-bottom:4px}
.rl-infographic-range-calc__result-value{font-family:var(--rl-font-data);font-size:22px;font-weight:700;color:var(--rl-color-signal-red)}

/* ── Before/After ── */
.rl-infographic-before-after{position:relative;border:3px solid var(--rl-color-near-black);overflow:hidden;cursor:col-resize;user-select:none}
.rl-infographic-ba-side{padding:20px}
.rl-infographic-ba-label{font-family:var(--rl-font-data);font-size:11px;font-weight:700;letter-spacing:2px;color:var(--rl-color-secondary-blue);margin-bottom:8px}
.rl-infographic-ba-divider{position:absolute;top:0;bottom:0;width:4px;background:var(--rl-color-orange);cursor:col-resize;z-index:2}
.rl-infographic-ba-handle{position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);width:24px;height:24px;background:var(--rl-color-orange);border:2px solid var(--rl-color-near-black);display:flex;align-items:center;justify-content:center;font-family:var(--rl-font-data);font-size:12px;font-weight:700;color:var(--rl-color-near-black)}

/* ── Gantt Chart ── */
.rl-infographic-gantt{border:3px solid var(--rl-color-near-black);background:var(--rl-color-cool-white)}
.rl-infographic-gantt__header{background:var(--rl-color-near-black);padding:8px 16px}
.rl-infographic-gantt__title{font-family:var(--rl-font-editorial);font-size:13px;font-weight:700;color:var(--rl-color-light-steel);letter-spacing:2px;text-transform:uppercase}
.rl-infographic-gantt__body{padding:16px}
.rl-infographic-gantt__row{display:flex;align-items:center;gap:8px;margin-bottom:6px}
.rl-infographic-gantt__label{font-family:var(--rl-font-data);font-size:11px;font-weight:700;color:var(--rl-color-primary-navy);min-width:80px;text-align:right}
.rl-infographic-gantt__track{flex:1;height:20px;background:var(--rl-color-silver);border:1px solid var(--rl-color-light-steel);position:relative}
.rl-infographic-gantt__bar{height:100%;position:absolute;top:0}

/* ── Weather Matrix ── */
.rl-infographic-weather-matrix{border:3px solid var(--rl-color-near-black);background:var(--rl-color-cool-white);padding:16px}
.rl-infographic-weather-title{font-family:var(--rl-font-editorial);font-size:14px;font-weight:700;color:var(--rl-color-primary-navy);margin-bottom:12px;text-align:center}

/* ── Radar Chart ── */
.rl-infographic-radar{text-align:center}
.rl-infographic-radar-controls{display:flex;justify-content:center;gap:8px;margin-top:12px}
.rl-infographic-radar-btn{padding:6px 14px;border:2px solid var(--rl-color-near-black);background:var(--rl-color-cool-white);font-family:var(--rl-font-data);font-size:11px;font-weight:700;cursor:pointer;letter-spacing:1px}
.rl-infographic-radar-btn:hover{border-color:var(--rl-color-signal-red)}
.rl-infographic-radar-btn.active{background:var(--rl-color-signal-red);color:var(--rl-color-cool-white);border-color:var(--rl-color-signal-red)}

/* ── Infographic Editorial Framing ── */
.rl-infographic-title{font-family:var(--rl-font-editorial);font-size:1.25rem;font-weight:700;color:var(--rl-color-near-black);border-bottom:3px solid var(--rl-color-orange);padding:0 0 0.5rem 0;margin:0 0 1rem 0}
.rl-infographic-takeaway{border-left:4px solid var(--rl-color-signal-red);padding:0.75rem 1rem;margin:1.25rem 0 0 0;font-family:var(--rl-font-editorial);font-style:italic;font-size:0.95rem;color:var(--rl-color-secondary-blue)}

/* ── Infographic Tooltips ── */
.rl-infographic-tooltip{position:absolute;z-index:1000;background:var(--rl-color-near-black);color:var(--rl-color-cool-white);border:3px solid var(--rl-color-orange);padding:8px 12px;font-family:var(--rl-font-data);font-size:11px;line-height:1.5;letter-spacing:0.5px;max-width:260px;pointer-events:none;display:none}
.rl-infographic-tooltip--visible{display:block}

/* ── Infographic Card Hover ── */
.rl-infographic-card:hover,.rl-infographic-rider-card:hover,.rl-infographic-day-card:hover,.rl-infographic-signal-row:hover,.rl-infographic-act-panel:hover{border-color:var(--rl-color-orange)}

/* ── Infographic Scroll Animations ── */
/* .rl-has-js guard: without JS, elements render statically (no hidden initial state) */
@media(prefers-reduced-motion:no-preference){
.rl-has-js .rl-infographic-card{transform:translateY(20px);transition:transform 0.5s cubic-bezier(0.25,0.46,0.45,0.94),border-color 0.3s}
.rl-in-view .rl-infographic-card{transform:translateY(0)}
.rl-in-view .rl-infographic-card:nth-child(2){transition-delay:0.1s}
.rl-in-view .rl-infographic-card:nth-child(3){transition-delay:0.2s}
.rl-in-view .rl-infographic-card:nth-child(4){transition-delay:0.3s}
.rl-in-view .rl-infographic-card:nth-child(5){transition-delay:0.4s}
.rl-in-view .rl-infographic-card:nth-child(6){transition-delay:0.5s}
.rl-in-view .rl-infographic-card:nth-child(7){transition-delay:0.6s}
.rl-has-js .rl-infographic-rider-card{transform:translateY(20px);transition:transform 0.5s cubic-bezier(0.25,0.46,0.45,0.94),border-color 0.3s}
.rl-in-view .rl-infographic-rider-card{transform:translateY(0)}
.rl-in-view .rl-infographic-rider-card:nth-child(2){transition-delay:0.1s}
.rl-in-view .rl-infographic-rider-card:nth-child(3){transition-delay:0.2s}
.rl-in-view .rl-infographic-rider-card:nth-child(4){transition-delay:0.3s}
.rl-has-js .rl-infographic-day-card{transform:translateY(16px);transition:transform 0.4s cubic-bezier(0.25,0.46,0.45,0.94),border-color 0.3s}
.rl-in-view .rl-infographic-day-card{transform:translateY(0)}
.rl-in-view .rl-infographic-day-card:nth-child(2){transition-delay:0.07s}
.rl-in-view .rl-infographic-day-card:nth-child(3){transition-delay:0.14s}
.rl-in-view .rl-infographic-day-card:nth-child(4){transition-delay:0.21s}
.rl-in-view .rl-infographic-day-card:nth-child(5){transition-delay:0.28s}
.rl-in-view .rl-infographic-day-card:nth-child(6){transition-delay:0.35s}
.rl-in-view .rl-infographic-day-card:nth-child(7){transition-delay:0.42s}
.rl-has-js .rl-infographic-signal-row{transform:translateY(16px);transition:transform 0.5s cubic-bezier(0.25,0.46,0.45,0.94),border-color 0.3s}
.rl-in-view .rl-infographic-signal-row{transform:translateY(0)}
.rl-in-view .rl-infographic-signal-row:nth-child(2){transition-delay:0.15s}
.rl-in-view .rl-infographic-signal-row:nth-child(3){transition-delay:0.3s}
.rl-has-js .rl-infographic-act-panel{transform:translateY(16px);transition:transform 0.5s cubic-bezier(0.25,0.46,0.45,0.94),border-color 0.3s}
.rl-in-view .rl-infographic-act-panel{transform:translateY(0)}
.rl-in-view .rl-infographic-act-panel:nth-child(2){transition-delay:0.15s}
.rl-in-view .rl-infographic-act-panel:nth-child(3){transition-delay:0.3s}
.rl-has-js .rl-infographic-bonk-gel{transform:scale(0);transition:transform 0.3s cubic-bezier(0.25,0.46,0.45,0.94)}
.rl-in-view .rl-infographic-bonk-gel{transform:scale(1)}
.rl-in-view .rl-infographic-bonk-gel:nth-child(2){transition-delay:0.03s}
.rl-in-view .rl-infographic-bonk-gel:nth-child(3){transition-delay:0.06s}
.rl-in-view .rl-infographic-bonk-gel:nth-child(4){transition-delay:0.09s}
.rl-in-view .rl-infographic-bonk-gel:nth-child(5){transition-delay:0.12s}
.rl-in-view .rl-infographic-bonk-gel:nth-child(6){transition-delay:0.15s}
.rl-in-view .rl-infographic-bonk-gel:nth-child(7){transition-delay:0.18s}
.rl-in-view .rl-infographic-bonk-gel:nth-child(8){transition-delay:0.21s}
.rl-in-view .rl-infographic-bonk-gel:nth-child(9){transition-delay:0.24s}
.rl-in-view .rl-infographic-bonk-gel:nth-child(10){transition-delay:0.27s}
.rl-in-view .rl-infographic-bonk-gel:nth-child(11){transition-delay:0.3s}
.rl-in-view .rl-infographic-bonk-gel:nth-child(12){transition-delay:0.33s}
[data-animate="bar"]{transition:width 0.8s cubic-bezier(0.25,0.46,0.45,0.94),height 0.8s cubic-bezier(0.25,0.46,0.45,0.94)}
[data-animate="line"]{transition:stroke-dashoffset 1.5s cubic-bezier(0.25,0.46,0.45,0.94)}
/* Flip card transition */
.rl-infographic-card--flip{transition:border-color 0.3s}
/* Accordion body slide */
.rl-infographic-accordion-icon{transition:color 0.2s}
/* Timeline expand */
.rl-infographic-timeline-node{transition:border-color 0.3s}
/* Pyramid bar growth */
.rl-has-js [data-animate="pyramid"] .rl-infographic-pyramid-bar{width:0;transition:width 0.8s cubic-bezier(0.25,0.46,0.45,0.94)}
.rl-in-view [data-animate="pyramid"] .rl-infographic-pyramid-bar,.rl-in-view[data-animate="pyramid"] .rl-infographic-pyramid-bar{width:var(--w)}
/* Gantt bar growth */
.rl-has-js [data-animate="gantt"] .rl-infographic-gantt__bar{width:0 !important;transition:width 1s cubic-bezier(0.25,0.46,0.45,0.94)}
.rl-in-view [data-animate="gantt"] .rl-infographic-gantt__bar,.rl-in-view[data-animate="gantt"] .rl-infographic-gantt__bar{width:var(--w) !important}
/* Scatter fade-in markers */
.rl-has-js [data-animate="scatter"] .rl-line-chart__marker{fill-opacity:0;transition:fill-opacity 0.4s cubic-bezier(0.25,0.46,0.45,0.94)}
.rl-in-view [data-animate="scatter"] .rl-line-chart__marker,.rl-in-view[data-animate="scatter"] .rl-line-chart__marker{fill-opacity:1;transition-delay:var(--delay,0ms)}
/* Fade-stagger for grid items */
.rl-has-js [data-animate="fade-stagger"] > *{transform:translateY(16px);transition:transform 0.5s cubic-bezier(0.25,0.46,0.45,0.94),border-color 0.3s}
.rl-in-view [data-animate="fade-stagger"] > *,.rl-in-view[data-animate="fade-stagger"] > *{transform:translateY(0)}
.rl-in-view [data-animate="fade-stagger"] > :nth-child(2),.rl-in-view[data-animate="fade-stagger"] > :nth-child(2){transition-delay:0.08s}
.rl-in-view [data-animate="fade-stagger"] > :nth-child(3),.rl-in-view[data-animate="fade-stagger"] > :nth-child(3){transition-delay:0.16s}
.rl-in-view [data-animate="fade-stagger"] > :nth-child(4),.rl-in-view[data-animate="fade-stagger"] > :nth-child(4){transition-delay:0.24s}
.rl-in-view [data-animate="fade-stagger"] > :nth-child(5),.rl-in-view[data-animate="fade-stagger"] > :nth-child(5){transition-delay:0.32s}
.rl-in-view [data-animate="fade-stagger"] > :nth-child(6),.rl-in-view[data-animate="fade-stagger"] > :nth-child(6){transition-delay:0.40s}
.rl-in-view [data-animate="fade-stagger"] > :nth-child(7),.rl-in-view[data-animate="fade-stagger"] > :nth-child(7){transition-delay:0.48s}
/* Progress bar growth */
.rl-has-js [data-animate="progress"] .rl-infographic-macro-fill{width:0;transition:width 1s cubic-bezier(0.25,0.46,0.45,0.94)}
.rl-in-view [data-animate="progress"] .rl-infographic-macro-fill,.rl-in-view[data-animate="progress"] .rl-infographic-macro-fill{width:var(--w)}
.rl-in-view [data-animate="progress"] .rl-infographic-macro-fill::before,.rl-in-view[data-animate="progress"] .rl-infographic-macro-fill::before{left:100%;transition:left 0.6s ease-out;transition-delay:1.2s}
/* Gauge stroke */
.rl-has-js [data-animate="stroke"] .rl-gauge__fill{stroke-dashoffset:var(--gauge-perimeter);transition:stroke-dashoffset 1.5s cubic-bezier(0.25,0.46,0.45,0.94)}
.rl-in-view [data-animate="stroke"] .rl-gauge__fill,.rl-in-view[data-animate="stroke"] .rl-gauge__fill{stroke-dashoffset:calc(var(--gauge-perimeter) - var(--gauge-target))}
/* Counter animation — JS drives the number increment */
/* Profile / course draw — uses same stroke-dashoffset as "line" */
[data-animate="profile"] path{transition:stroke-dashoffset 2s cubic-bezier(0.25,0.46,0.45,0.94)}
/* Digit roller transition */
.rl-infographic-digit-strip{transition:transform 1.5s cubic-bezier(0.25,0.46,0.45,0.94)}
/* Shimmer sweep in bar fills */
.rl-infographic-macro-fill::before{transition:left 0.6s ease-out}
/* Gear bar fill */
.rl-infographic-gear-bar-fill{transition:width 0.6s cubic-bezier(0.25,0.46,0.45,0.94)}
}

@media(max-width:768px){
.rl-infographic--full-width{margin-left:-16px;margin-right:-16px}
.rl-infographic-gear-grid{grid-template-columns:1fr 1fr}
.rl-infographic-rider-grid{grid-template-columns:1fr 1fr}
.rl-infographic-week-grid{grid-template-columns:repeat(4,1fr)}
.rl-infographic-three-acts{grid-template-columns:1fr}
.rl-infographic-bonk-equation{flex-wrap:wrap}
.rl-infographic-bonk-num{font-size:36px}
.rl-infographic-bonk-total{font-size:42px}
.rl-infographic-bonk-grid{grid-template-columns:repeat(8,1fr)}
.rl-infographic-glycogen-compare{grid-template-columns:1fr}
.rl-infographic-glycogen-gauges{grid-template-columns:repeat(2,1fr)}
.rl-infographic-recovery-grid{grid-template-columns:1fr}
.rl-sleep-tracker__grid{grid-template-columns:repeat(4,1fr)}
.rl-sleep-tracker__day-hrs{font-size:16px}
.rl-infographic-before-after{flex-direction:column}
.rl-infographic-heatmap{font-size:9px}
.rl-infographic-heatmap-cell{padding:4px 2px}
.rl-infographic-radar-controls{flex-wrap:wrap}
.rl-infographic-range-calc__output{grid-template-columns:1fr 1fr}
.rl-infographic-gantt__label{min-width:60px;font-size:10px}
.rl-infographic-digit{width:28px;height:44px}
.rl-infographic-digit-strip span{height:44px;font-size:24px}
}

/* ── Race Reference (inline link) ── */
.rl-race-ref{color:var(--rl-color-signal-red);text-decoration:underline;text-underline-offset:2px;font-family:var(--rl-font-data)}
.rl-race-ref:hover{color:var(--rl-color-primary-navy)}

/* ── Race Callout (comparison card) ── */
.rl-race-callout{border:2px solid var(--rl-color-primary-navy);padding:0;margin:24px 0;background:var(--rl-color-cool-white)}
.rl-race-callout__header{background:var(--rl-color-primary-navy);color:var(--rl-color-cool-white);padding:8px 16px;font-family:var(--rl-font-data);font-size:11px;letter-spacing:0.1em;text-transform:uppercase}
.rl-race-callout__grid{display:grid;grid-template-columns:1fr 1fr;gap:0}
.rl-race-callout__race{padding:16px;text-align:center;border-bottom:1px solid var(--rl-color-light-steel)}
.rl-race-callout__race:first-child{border-right:2px solid var(--rl-color-primary-navy)}
.rl-race-callout__name{color:var(--rl-color-signal-red);font-family:var(--rl-font-editorial);font-weight:600;text-decoration:none;font-size:16px}
.rl-race-callout__name:hover{text-decoration:underline}
.rl-race-callout__tier{display:inline-block;margin-left:8px;font-family:var(--rl-font-data);font-size:11px;padding:2px 6px;border:1px solid currentColor}
.rl-race-callout__tier[data-tier="1"]{color:var(--rl-color-primary-navy)}
.rl-race-callout__tier[data-tier="2"]{color:var(--rl-color-secondary-blue)}
.rl-race-callout__tier[data-tier="3"]{color:var(--rl-color-tier-3)}
.rl-race-callout__tier[data-tier="4"]{color:var(--rl-color-tier-4)}
.rl-race-callout__stat{margin-top:12px}
.rl-race-callout__stat-value{display:block;font-family:var(--rl-font-data);font-size:28px;font-weight:700;color:var(--rl-color-primary-navy)}
.rl-race-callout__stat-label{display:block;font-family:var(--rl-font-data);font-size:11px;color:var(--rl-color-secondary-blue);text-transform:uppercase;letter-spacing:0.05em;margin-top:4px}
.rl-race-callout__vs{display:block;text-align:center;font-family:var(--rl-font-data);font-size:12px;color:var(--rl-color-secondary-blue);padding:4px 0;letter-spacing:0.15em}
.rl-race-callout__caption{padding:12px 16px;margin:0;font-family:var(--rl-font-editorial);font-size:14px;color:var(--rl-color-secondary-blue);border-top:1px solid var(--rl-color-light-steel)}
@media(max-width:768px){
.rl-race-callout__grid{grid-template-columns:1fr}
.rl-race-callout__race:first-child{border-right:none;border-bottom:2px solid var(--rl-color-primary-navy)}
.rl-race-callout__stat-value{font-size:22px}
}

/* ── Decision Tree (interactive race finder) ── */
.rl-decision-tree{border:2px solid var(--rl-color-primary-navy);margin:24px 0;background:var(--rl-color-cool-white)}
.rl-decision-tree__header{background:var(--rl-color-primary-navy);color:var(--rl-color-cool-white);padding:10px 16px;font-family:var(--rl-font-data);font-size:13px;letter-spacing:0.1em;text-transform:uppercase}
.rl-decision-tree__body{padding:24px 16px}
.rl-decision-tree__question{font-family:var(--rl-font-editorial);font-size:18px;font-weight:600;color:var(--rl-color-primary-navy);margin:0 0 16px}
.rl-decision-tree__options{display:flex;flex-direction:column;gap:8px}
.rl-decision-tree__option{display:block;width:100%;padding:12px 16px;border:2px solid var(--rl-color-light-steel);background:var(--rl-color-silver);font-family:var(--rl-font-editorial);font-size:15px;color:var(--rl-color-primary-navy);cursor:pointer;text-align:left;transition:border-color 0.15s,background 0.15s}
.rl-decision-tree__option:hover{border-color:var(--rl-color-signal-red);background:var(--rl-color-cool-white)}
.rl-decision-tree__result{padding:24px 16px;text-align:center}
.rl-decision-tree__result-title{font-family:var(--rl-font-data);font-size:11px;text-transform:uppercase;letter-spacing:0.1em;color:var(--rl-color-secondary-blue);margin-bottom:8px}
.rl-decision-tree__result-race{font-family:var(--rl-font-editorial);font-size:22px;font-weight:700}
.rl-decision-tree__result-race a{color:var(--rl-color-signal-red);text-decoration:underline}
.rl-decision-tree__restart{display:block;width:100%;padding:10px;border:2px solid var(--rl-color-primary-navy);background:var(--rl-color-cool-white);font-family:var(--rl-font-data);font-size:12px;text-transform:uppercase;letter-spacing:0.1em;cursor:pointer;color:var(--rl-color-primary-navy)}
.rl-decision-tree__restart:hover{background:var(--rl-color-silver)}
@media(max-width:768px){
.rl-decision-tree__question{font-size:16px}
.rl-decision-tree__option{font-size:14px;padding:10px 12px}
}

/* ── Personalized Content (rider-type variants) ── */
.rl-personalized{margin:16px 0;position:relative}
.rl-personalized__variant{border-left:3px solid var(--rl-color-signal-red);padding:12px 16px;background:var(--rl-color-silver);opacity:0;visibility:hidden;position:absolute;width:100%;transition:opacity 0.3s ease}
.rl-personalized__variant.rl-personalized--active{opacity:1;visibility:visible;position:relative}
.rl-personalized__variant p{margin:0 0 8px;font-family:var(--rl-font-editorial);font-size:15px;color:var(--rl-color-primary-navy);line-height:1.6}
.rl-personalized__variant p:last-child{margin-bottom:0}
@media(prefers-reduced-motion:reduce){
.rl-personalized__variant{transition:none}
}
'''


# ── JS ───────────────────────────────────────────────────────



def build_guide_js() -> str:
    """Return all guide-specific JavaScript as a single IIFE."""
    return '''(function(){
"use strict";
document.documentElement.classList.add("rl-has-js");
function track(n,p){if(typeof gtag==="function")gtag("event",n,Object.assign({transport_type:"beacon"},p||{}));}
var STORAGE_KEY="rl_guide_unlocked";
var page=document.querySelector(".rl-neo-brutalist-page");
function isUnlocked(){try{return localStorage.getItem(STORAGE_KEY)==="1";}catch(e){return false;}}
function unlock(method){
try{localStorage.setItem(STORAGE_KEY,"1");}catch(e){}
if(page)page.classList.add("rl-guide-unlocked");
document.querySelectorAll(".rl-guide-chapnav-item--locked").forEach(function(el){el.classList.add("rl-guide-chapnav-item--unlocked");});
track("guide_unlock",{method:method||"unknown"});
}
if(isUnlocked()){
if(page)page.classList.add("rl-guide-unlocked");
document.querySelectorAll(".rl-guide-chapnav-item--locked").forEach(function(el){el.classList.add("rl-guide-chapnav-item--unlocked");});
track("guide_return_visit",{unlocked:true});
}
window.addEventListener("message",function(e){
if(e.origin&&e.origin.indexOf("substack.com")!==-1){
if(e.data&&(e.data.type==="subscription-created"||e.data==="subscription-created"))unlock("substack_subscribe");
}
});
var bypassBtn=document.getElementById("rl-guide-gate-bypass");
if(bypassBtn)bypassBtn.addEventListener("click",function(){unlock("manual_bypass");});
var scrollMilestones={25:false,50:false,75:false,100:false};
var progressBar=document.querySelector(".rl-guide-progress-bar");
var progressTicking=false;
window.addEventListener("scroll",function(){
if(!progressTicking){
requestAnimationFrame(function(){
var h=document.documentElement.scrollHeight-window.innerHeight;
var pct=h>0?(window.scrollY/h)*100:0;
if(progressBar){progressBar.style.width=Math.min(100,pct)+"%";progressBar.setAttribute("aria-valuenow",Math.round(Math.min(100,pct)));}
[25,50,75,100].forEach(function(m){if(!scrollMilestones[m]&&pct>=m){scrollMilestones[m]=true;track("guide_scroll_depth",{percent:m,unlocked:isUnlocked()});}});
progressTicking=false;
});
progressTicking=true;
}
},{passive:true});
var chapters=document.querySelectorAll(".rl-guide-chapter");
var navItems=document.querySelectorAll(".rl-guide-chapnav-item");
var chaptersRead={};
if(chapters.length&&"IntersectionObserver" in window){
var activeId=null;
var chapterObs=new IntersectionObserver(function(entries){
entries.forEach(function(entry){
if(entry.isIntersecting){
activeId=entry.target.id;
var chNum=entry.target.getAttribute("data-chapter");
navItems.forEach(function(nav){
nav.classList.toggle("rl-guide-chapnav-item--active",nav.getAttribute("data-chapter")===activeId);
});
if(chNum&&!chaptersRead[chNum]){chaptersRead[chNum]=true;track("guide_chapter_view",{chapter_number:parseInt(chNum,10),chapter_id:activeId});}
}
});
},{rootMargin:"-20% 0px -70% 0px",threshold:0});
chapters.forEach(function(ch){chapterObs.observe(ch);});
}
navItems.forEach(function(item){
item.addEventListener("click",function(e){
e.preventDefault();
var chapterId=item.getAttribute("data-chapter");
var target=document.getElementById(chapterId);
if(target&&target.classList.contains("rl-guide-gated")&&!isUnlocked()){
var gateEl=document.getElementById("rl-guide-gate");
if(gateEl)gateEl.scrollIntoView({behavior:"smooth",block:"start"});
}else if(target){target.scrollIntoView({behavior:"smooth",block:"start"});}
track("guide_chapnav_click",{chapter:chapterId});
});
});
var gateEl=document.getElementById("rl-guide-gate");
if(gateEl&&"IntersectionObserver" in window){
var gateTracked=false;
var gateObs=new IntersectionObserver(function(entries){
entries.forEach(function(entry){
if(entry.isIntersecting&&!gateTracked){gateTracked=true;track("guide_gate_impression",{});gateObs.unobserve(gateEl);}
});
},{threshold:0.3});
gateObs.observe(gateEl);
}
document.querySelectorAll(".rl-guide-accordion-trigger").forEach(function(trigger){
trigger.addEventListener("click",function(){
var expanded=trigger.getAttribute("aria-expanded")==="true";
trigger.setAttribute("aria-expanded",expanded?"false":"true");
});
});
document.querySelectorAll(".rl-guide-tabs").forEach(function(tabGroup){
var tabs=tabGroup.querySelectorAll(".rl-guide-tab");
var panels=tabGroup.querySelectorAll(".rl-guide-tab-panel");
tabs.forEach(function(tab){
tab.addEventListener("click",function(){
var targetId=tab.getAttribute("data-tab");
tabs.forEach(function(t){t.classList.remove("rl-guide-tab--active");t.setAttribute("aria-selected","false");});
panels.forEach(function(p){p.style.display="none";});
tab.classList.add("rl-guide-tab--active");
tab.setAttribute("aria-selected","true");
var panel=document.getElementById(targetId);
if(panel)panel.style.display="block";
});
});
});
document.querySelectorAll(".rl-guide-knowledge-check").forEach(function(kc){
var options=kc.querySelectorAll(".rl-guide-kc-option");
var explanation=kc.querySelector(".rl-guide-kc-explanation");
var answered=false;
options.forEach(function(opt){
opt.addEventListener("click",function(){
if(answered)return;
answered=true;
var isCorrect=opt.getAttribute("data-correct")==="true";
opt.classList.add(isCorrect?"rl-guide-kc-option--correct":"rl-guide-kc-option--incorrect");
if(!isCorrect){options.forEach(function(o){if(o.getAttribute("data-correct")==="true")o.classList.add("rl-guide-kc-option--correct");});}
options.forEach(function(o){if(o!==opt&&o.getAttribute("data-correct")!=="true")o.classList.add("rl-guide-kc-option--disabled");o.setAttribute("aria-disabled","true");});
if(explanation)explanation.style.display="block";
track("guide_knowledge_check",{correct:isCorrect});
});
});
});
document.querySelectorAll(".rl-guide-flashcard").forEach(function(card){
function flipCard(){card.classList.toggle("rl-guide-flashcard--flipped");track("guide_flashcard_flip",{card_id:card.id});}
card.addEventListener("click",flipCard);
card.addEventListener("keydown",function(e){if(e.key==="Enter"||e.key===" "){e.preventDefault();flipCard();}});
});
document.querySelectorAll(".rl-guide-scenario").forEach(function(scenario){
var options=scenario.querySelectorAll(".rl-guide-scenario-option");
var answered=false;
options.forEach(function(opt){
opt.addEventListener("click",function(){
if(answered)return;
answered=true;
opt.classList.add("rl-guide-scenario-option--selected");
options.forEach(function(o){if(o!==opt)o.classList.add("rl-guide-scenario-option--disabled");o.setAttribute("aria-disabled","true");});
track("guide_scenario_choice",{best:opt.getAttribute("data-best")==="true"});
});
});
});
document.querySelectorAll(".rl-guide-cta a, .rl-guide-finale-card a").forEach(function(link){
link.addEventListener("click",function(){
var ctaBlock=link.closest(".rl-guide-cta, .rl-guide-finale-card");
var ctaType="unknown";
if(ctaBlock){
if(ctaBlock.classList.contains("rl-guide-cta--newsletter")||ctaBlock.classList.contains("rl-guide-finale-card--newsletter"))ctaType="newsletter";
else if(ctaBlock.classList.contains("rl-guide-cta--training")||ctaBlock.classList.contains("rl-guide-finale-card--training"))ctaType="training_plan";
else if(ctaBlock.classList.contains("rl-guide-cta--coaching")||ctaBlock.classList.contains("rl-guide-finale-card--coaching"))ctaType="coaching";
}
track("guide_cta_click",{cta_type:ctaType,link_url:link.href});
});
});
function clearCalcErrors(calc){
calc.querySelectorAll(".rl-guide-calc-input--error").forEach(function(el){el.classList.remove("rl-guide-calc-input--error");});
var errEl=calc.querySelector(".rl-guide-calc-error");
if(errEl){errEl.style.display="none";errEl.textContent="";}
}
function showCalcError(calc,msg){
var errEl=calc.querySelector(".rl-guide-calc-error");
if(errEl){errEl.textContent=msg;errEl.style.display="block";}
}
document.querySelectorAll(".rl-guide-calculator").forEach(function(calc){
var calcType=calc.getAttribute("data-calc-type");
var btn=calc.querySelector(".rl-guide-calc-btn");
var output=calc.querySelector(".rl-guide-calc-output");
calc.querySelectorAll(".rl-guide-calc-toggle").forEach(function(toggle){
var btns=toggle.querySelectorAll(".rl-guide-calc-toggle-btn");
btns.forEach(function(b){
b.addEventListener("click",function(){
btns.forEach(function(t){t.classList.remove("rl-guide-calc-toggle-btn--active");});
b.classList.add("rl-guide-calc-toggle-btn--active");
});
});
});
if(btn)btn.addEventListener("click",function(){
if(calcType==="ftp-zones")computeFtpZones(calc,output);
else if(calcType==="daily-nutrition")computeDailyNutrition(calc,output);
else if(calcType==="workout-fueling")computeWorkoutFueling(calc,output);
});
});
function computeFtpZones(calc,output){
clearCalcErrors(calc);
var ftpInput=calc.querySelector("#rl-calc-ftp-power");
var testInput=calc.querySelector("#rl-calc-ftp-test");
var lthrInput=calc.querySelector("#rl-calc-ftp-lthr");
var ftp=0;
if(ftpInput&&ftpInput.value)ftp=parseInt(ftpInput.value,10);
if((!ftp||ftp<50)&&testInput&&testInput.value)ftp=Math.round(parseInt(testInput.value,10)*0.95);
if(!ftp||ftp<50||ftp>600){
if(ftpInput)ftpInput.classList.add("rl-guide-calc-input--error");
if(testInput)testInput.classList.add("rl-guide-calc-input--error");
showCalcError(calc,"Enter FTP (50-600w) or a 20-min test power.");
return;
}
var lthr=lthrInput&&lthrInput.value?parseInt(lthrInput.value,10):0;
if(lthr&&(lthr<100||lthr>220))lthr=0;
var ftpDisp=output.querySelector(".rl-guide-calc-ftp-display");
if(ftpDisp)ftpDisp.textContent="Your FTP: "+ftp+" watts"+(lthr?" | Threshold HR: "+lthr+" bpm":"");
output.style.display="block";
var zones=output.querySelectorAll(".rl-guide-calc-zone");
zones.forEach(function(zone,i){
var minPct=parseInt(zone.getAttribute("data-min"),10);
var maxPct=parseInt(zone.getAttribute("data-max"),10);
var minW=Math.round(ftp*minPct/100);
var maxW=Math.round(ftp*maxPct/100);
var range=zone.querySelector(".rl-guide-calc-zone-range");
if(range)range.textContent=minW+"-"+maxW+"w";
var fill=zone.querySelector(".rl-guide-calc-zone-fill");
if(fill)setTimeout(function(){fill.style.width=Math.min(maxPct/2,100)+"%";},i*80);
var hrEl=zone.querySelector(".rl-guide-calc-zone-hr");
if(hrEl&&lthr){
var hrMinPct=zone.getAttribute("data-hr-min");
var hrMaxPct=zone.getAttribute("data-hr-max");
if(hrMinPct!==null&&hrMaxPct){
var hrLo=Math.round(lthr*parseInt(hrMinPct,10)/100);
var hrHi=Math.round(lthr*parseInt(hrMaxPct,10)/100);
hrEl.textContent=(parseInt(hrMinPct,10)===0?"\u2264 "+hrHi:hrLo+"-"+hrHi)+" bpm";
}
}
});
track("guide_calculator_use",{type:"ftp_zones",ftp:ftp,has_hr:lthr>0});
}
function setOut(id,t){var e=document.getElementById("rl-calc-out-"+id);if(e)e.textContent=t;}
function computeDailyNutrition(calc,output){
clearCalcErrors(calc);
var wi=calc.querySelector("#rl-calc-dn-weight");
var w=wi?parseFloat(wi.value):0;
if(!w||w<30||w>500){
if(wi)wi.classList.add("rl-guide-calc-input--error");
showCalcError(calc,"Enter a valid weight (30-500).");
return;
}
var tg=calc.querySelector(".rl-guide-calc-toggle[data-field='dn-unit']");
var u="kg";
if(tg){var a=tg.querySelector(".rl-guide-calc-toggle-btn--active");if(a)u=a.getAttribute("data-value")||"kg";}
var kg=u==="lbs"?w*0.4536:w;
var ds=calc.querySelector("#rl-calc-dn-day");
var d=ds?ds.value:"easy";
var cm={rest:[2,3],hard:[5,7],race:[8,10]}[d]||[3,5];
output.style.display="block";
setOut("protein",Math.round(kg*1.6)+"-"+Math.round(kg*2.2)+"g");
setOut("carbs",Math.round(kg*cm[0])+"-"+Math.round(kg*cm[1])+"g");
setOut("fat",Math.round(kg*0.8)+"-"+Math.round(kg*1.2)+"g");
setOut("calories",Math.round(kg*1.6*4+kg*cm[0]*4+kg*0.8*9)+"-"+Math.round(kg*2.2*4+kg*cm[1]*4+kg*1.2*9)+" kcal");
track("guide_calculator_use",{type:"daily_nutrition",weight_kg:Math.round(kg)});
}
function computeWorkoutFueling(calc,output){
clearCalcErrors(calc);
var di=calc.querySelector("#rl-calc-wf-duration");
var dur=di?parseFloat(di.value):0;
if(!dur||dur<0.5||dur>24){
if(di)di.classList.add("rl-guide-calc-input--error");
showCalcError(calc,"Enter a valid duration (0.5-24 hours).");
return;
}
var ints=calc.querySelector("#rl-calc-wf-intensity");
var rate={z2:50,tempo:65,race:85,high:75}[ints?ints.value:"z2"]||50;
var tc=Math.round(dur*rate),hy=Math.round(dur*500);
output.style.display="block";
setOut("total-carbs",tc+"g");
setOut("fuel-rate",rate+"g/hr");
setOut("hydration",(hy/1000).toFixed(1)+"L ("+Math.round(hy/500)+" bottles)");
setOut("gels",Math.ceil(tc/25)+" gels (or equivalent)");
track("guide_calculator_use",{type:"workout_fueling",duration:dur});
}
var RIDER_STORAGE="rl_guide_rider_type";
var riderSelector=document.getElementById("rl-guide-rider-selector");
var riderBadge=document.getElementById("rl-guide-rider-badge");
var riderBadgeType=document.getElementById("rl-guide-rider-badge-type");
var riderBadgeChange=document.getElementById("rl-guide-rider-badge-change");
function setRider(type){
try{localStorage.setItem(RIDER_STORAGE,type);}catch(e){}
if(!riderSelector)return;
var btns=riderSelector.querySelectorAll(".rl-guide-rider-btn");
var label="";
var ftp=200;
btns.forEach(function(b){
var isMatch=b.getAttribute("data-rider")===type;
b.classList.toggle("rl-guide-rider-btn--active",isMatch);
b.setAttribute("aria-checked",isMatch?"true":"false");
if(isMatch){label=b.querySelector(".rl-guide-rider-btn-label").textContent;ftp=parseInt(b.getAttribute("data-ftp")||"200",10);}
});
if(riderBadge&&label){riderBadge.style.display="flex";if(riderBadgeType)riderBadgeType.textContent=label;}
document.querySelectorAll(".rl-guide-tabs").forEach(function(tabGroup){
var matchTab=tabGroup.querySelector('.rl-guide-tab[data-rider-type="'+type+'"]');
if(matchTab){
var tabs=tabGroup.querySelectorAll(".rl-guide-tab");
var panels=tabGroup.querySelectorAll(".rl-guide-tab-panel");
tabs.forEach(function(t){t.classList.remove("rl-guide-tab--active");t.setAttribute("aria-selected","false");});
panels.forEach(function(p){p.style.display="none";});
matchTab.classList.add("rl-guide-tab--active");
matchTab.setAttribute("aria-selected","true");
var targetId=matchTab.getAttribute("data-tab");
var panel=document.getElementById(targetId);
if(panel)panel.style.display="block";
}
});
var ftpInput=document.getElementById("rl-calc-ftp-power");
if(ftpInput)ftpInput.placeholder="e.g., "+ftp;
/* Personalized content: show matching variant, hide others */
document.querySelectorAll(".rl-personalized").forEach(function(pc){
var variants=pc.querySelectorAll(".rl-personalized__variant");
variants.forEach(function(v){
var isMatch=v.getAttribute("data-rider-type")===type;
v.classList.toggle("rl-personalized--active",isMatch);
});
});
track("guide_rider_select",{rider_type:type});
}
if(riderSelector){
riderSelector.querySelectorAll(".rl-guide-rider-btn").forEach(function(btn){
btn.addEventListener("click",function(){setRider(btn.getAttribute("data-rider"));});
});
}
if(riderBadgeChange){
riderBadgeChange.addEventListener("click",function(){
if(riderSelector)riderSelector.scrollIntoView({behavior:"smooth",block:"start"});
});
}
try{var saved=localStorage.getItem(RIDER_STORAGE);if(saved)setRider(saved);}catch(e){}
var pageStartTime=Date.now();
window.addEventListener("beforeunload",function(){
var seconds=Math.round((Date.now()-pageStartTime)/1000);
track("guide_time_on_page",{seconds:seconds,chapters_read:Object.keys(chaptersRead).length});
});

/* ── Infographic Scroll Animations ── */
if("IntersectionObserver" in window){
var prefersReduced=window.matchMedia("(prefers-reduced-motion:reduce)").matches;
if(!prefersReduced){
var infoFigs=document.querySelectorAll("figure[data-asset-id]");
if(infoFigs.length){
var infoObs=new IntersectionObserver(function(entries,obs){
entries.forEach(function(entry){
if(entry.isIntersecting){
var fig=entry.target;
fig.classList.add("rl-in-view");
/* SVG bar animations: set target dimensions */
fig.querySelectorAll("[data-animate='bar']").forEach(function(el){
var tw=el.getAttribute("data-target-width");
var th=el.getAttribute("data-target-height");
if(tw)el.setAttribute("width",tw);
if(th)el.setAttribute("height",th);
});
/* SVG line-draw animations */
fig.querySelectorAll("[data-animate='line']").forEach(function(el){
var len=el.getTotalLength?el.getTotalLength():0;
if(len){el.style.strokeDasharray=len;el.style.strokeDashoffset="0";}
});
/* Counter animation (countUp) */
fig.querySelectorAll("[data-animate='counter'] [data-target]").forEach(function(el){
var target=parseFloat(el.getAttribute("data-target"));
if(isNaN(target))return;
var start=0;var dur=1200;var t0=performance.now();
function tick(now){
var pct=Math.min((now-t0)/dur,1);
var val=Math.round(start+(target-start)*pct);
el.textContent=val;
if(pct<1)requestAnimationFrame(tick);
}
requestAnimationFrame(tick);
});
/* Stroke gauge animation — CSS handles via .rl-in-view, just trigger class */
/* Pyramid / gantt / progress — CSS handles via .rl-in-view + --w custom property */
/* Profile draw animation */
fig.querySelectorAll("[data-animate='profile'] path").forEach(function(el){
var len=el.getTotalLength?el.getTotalLength():0;
if(len){el.style.strokeDasharray=len;el.style.strokeDashoffset="0";}
});
/* Scatter marker reveal — CSS handles via .rl-in-view + --delay */
/* Digit roller animation */
fig.querySelectorAll("[data-interactive='digit-roller']").forEach(function(roller){
var digits=roller.querySelectorAll(".rl-infographic-digit");
var targetVal=roller.getAttribute("data-value")||"0";
var padded=targetVal.padStart(digits.length,"0");
digits.forEach(function(d,i){
var strip=d.querySelector(".rl-infographic-digit-strip");
if(!strip)return;
var digit=parseInt(padded[i],10)||0;
strip.style.transform="translateY(-"+(digit*56)+"px)";
});
});
obs.unobserve(fig);
track("infographic_view",{asset_id:fig.getAttribute("data-asset-id")});
}
});
},{threshold:0.2});
infoFigs.forEach(function(fig){
/* Pre-set SVG bars to zero width/height */
fig.querySelectorAll("[data-animate='bar']").forEach(function(el){
var tw=el.getAttribute("data-target-width");
var th=el.getAttribute("data-target-height");
if(tw)el.setAttribute("width","0");
if(th)el.setAttribute("height","0");
});
/* Pre-set SVG lines for draw animation */
fig.querySelectorAll("[data-animate='line']").forEach(function(el){
var len=el.getTotalLength?el.getTotalLength():0;
if(len){el.style.strokeDasharray=len;el.style.strokeDashoffset=len;}
});
/* Pre-set profile paths for draw animation */
fig.querySelectorAll("[data-animate='profile'] path").forEach(function(el){
var len=el.getTotalLength?el.getTotalLength():0;
if(len){el.style.strokeDasharray=len;el.style.strokeDashoffset=len;}
});
/* Pre-set gauge strokes — CSS initial state handles via .rl-has-js */
/* Pre-set digit roller to initial position (all zeros visible) */
fig.querySelectorAll("[data-interactive='digit-roller'] .rl-infographic-digit-strip").forEach(function(strip){
strip.style.transform="translateY(0)";
});
infoObs.observe(fig);
});
}
}
}

/* ── Infographic Tooltips ── */
var ttDiv=null;
function showTooltip(el){
var tip=el.getAttribute("data-tooltip");
if(!tip)return;
if(!ttDiv){ttDiv=document.createElement("div");ttDiv.className="rl-infographic-tooltip";document.body.appendChild(ttDiv);}
ttDiv.textContent=tip;
ttDiv.classList.add("rl-infographic-tooltip--visible");
var r=el.getBoundingClientRect();
ttDiv.style.left=Math.max(8,r.left+r.width/2-130)+"px";
ttDiv.style.top=(r.top+window.scrollY-ttDiv.offsetHeight-8)+"px";
track("infographic_tooltip",{text:tip.slice(0,40)});
}
function hideTooltip(){if(ttDiv)ttDiv.classList.remove("rl-infographic-tooltip--visible");}
document.addEventListener("mouseover",function(e){var t=e.target.closest("[data-tooltip]");if(t&&t.closest(".rl-infographic"))showTooltip(t);});
document.addEventListener("mouseout",function(e){var t=e.target.closest("[data-tooltip]");if(t)hideTooltip();});
document.addEventListener("focusin",function(e){var t=e.target.closest("[data-tooltip]");if(t&&t.closest(".rl-infographic"))showTooltip(t);});
document.addEventListener("focusout",function(e){var t=e.target.closest("[data-tooltip]");if(t)hideTooltip();});

/* ── Interactive Handlers (event delegation) ── */
var prefersReduced=window.matchMedia("(prefers-reduced-motion:reduce)").matches;

/* Flip cards */
document.addEventListener("click",function(e){
var card=e.target.closest("[data-interactive='flip']");
if(!card)return;
card.classList.toggle("flipped");
track("infographic_interact",{type:"flip",asset_id:(card.closest("figure[data-asset-id]")||{}).getAttribute("data-asset-id")||""});
});
document.addEventListener("keydown",function(e){
if(e.key!=="Enter"&&e.key!==" ")return;
var card=e.target.closest("[data-interactive='flip']");
if(!card)return;
e.preventDefault();
card.classList.toggle("flipped");
});

/* Traffic light click-to-cycle */
document.addEventListener("click",function(e){
var row=e.target.closest("[data-interactive='traffic-light']");
if(!row)return;
var states=["go","caution","stop"];
var cur=row.getAttribute("data-state")||"go";
var idx=(states.indexOf(cur)+1)%states.length;
row.setAttribute("data-state",states[idx]);
track("infographic_interact",{type:"traffic-light",state:states[idx]});
});

/* Infographic accordion */
document.addEventListener("click",function(e){
var header=e.target.closest("[data-interactive='accordion'] .rl-infographic-accordion-header");
if(!header)return;
var item=header.closest(".rl-infographic-accordion-item");
if(item)item.classList.toggle("open");
track("infographic_interact",{type:"accordion"});
});

/* Radar morph */
document.addEventListener("click",function(e){
var btn=e.target.closest("[data-interactive='radar-morph'] .rl-infographic-radar-btn");
if(!btn)return;
var radar=btn.closest("[data-interactive='radar-morph']");
if(!radar)return;
var polygon=radar.querySelector("polygon.rl-infographic-radar-data");
if(!polygon)return;
var targetPts=btn.getAttribute("data-points");
if(!targetPts)return;
/* Update active button */
radar.querySelectorAll(".rl-infographic-radar-btn").forEach(function(b){b.classList.remove("active");});
btn.classList.add("active");
/* Animate polygon morph with rAF */
if(prefersReduced){polygon.setAttribute("points",targetPts);return;}
var fromPts=polygon.getAttribute("points").split(" ").map(function(p){var xy=p.split(",");return[parseFloat(xy[0]),parseFloat(xy[1])];});
var toPts=targetPts.split(" ").map(function(p){var xy=p.split(",");return[parseFloat(xy[0]),parseFloat(xy[1])];});
if(fromPts.length!==toPts.length){polygon.setAttribute("points",targetPts);return;}
var dur=600;var t0=performance.now();
function morphTick(now){
var pct=Math.min((now-t0)/dur,1);
var ease=pct<0.5?2*pct*pct:1-Math.pow(-2*pct+2,2)/2;
var pts=fromPts.map(function(f,i){return(f[0]+(toPts[i][0]-f[0])*ease).toFixed(1)+","+(f[1]+(toPts[i][1]-f[1])*ease).toFixed(1);}).join(" ");
polygon.setAttribute("points",pts);
if(pct<1)requestAnimationFrame(morphTick);
}
requestAnimationFrame(morphTick);
track("infographic_interact",{type:"radar-morph",race:btn.textContent.trim()});
});

/* Sortable table */
document.addEventListener("click",function(e){
var th=e.target.closest("[data-interactive='sortable-table'] th[data-col]");
if(!th)return;
var table=th.closest("table");
if(!table)return;
var tbody=table.querySelector("tbody");
if(!tbody)return;
var col=parseInt(th.getAttribute("data-col"),10);
var rows=Array.from(tbody.querySelectorAll("tr"));
var asc=th.getAttribute("data-sort-dir")!=="asc";
rows.sort(function(a,b){
var aText=(a.children[col]||{}).textContent||"";
var bText=(b.children[col]||{}).textContent||"";
var aNum=parseFloat(aText.replace(/[^0-9.-]/g,""));
var bNum=parseFloat(bText.replace(/[^0-9.\-]/g,""));
if(!isNaN(aNum)&&!isNaN(bNum))return asc?aNum-bNum:bNum-aNum;
return asc?aText.localeCompare(bText):bText.localeCompare(aText);
});
rows.forEach(function(r){tbody.appendChild(r);});
table.querySelectorAll("th[data-col]").forEach(function(h){h.removeAttribute("data-sort-dir");var ind=h.querySelector(".rl-infographic-sort-indicator");if(ind)ind.textContent="";});
th.setAttribute("data-sort-dir",asc?"asc":"desc");
var indicator=th.querySelector(".rl-infographic-sort-indicator");
if(indicator)indicator.textContent=asc?"\u25b2":"\u25bc";
track("infographic_interact",{type:"sortable-table",column:col,direction:asc?"asc":"desc"});
});

/* Range calculator */
document.querySelectorAll("[data-interactive='range-calculator']").forEach(function(calc){
var sliders=calc.querySelectorAll("input[type='range']");
function updateCalc(){
var vals={};
sliders.forEach(function(s){vals[s.name]=parseFloat(s.value);var out=calc.querySelector("output[for='"+s.id+"']");if(out)out.textContent=s.value+(s.getAttribute("data-unit")||"");});
/* Hydration calc formula */
var dur=vals.duration||4;var temp=vals.temp||70;var intensity=vals.intensity||6;
var baseMl=500*dur;var heatAdj=temp>80?1.3:temp>70?1.1:1.0;
var intAdj=intensity>7?1.2:intensity>5?1.1:1.0;
var totalMl=Math.round(baseMl*heatAdj*intAdj);
var sodiumMg=Math.round(totalMl*0.7);
var outFluid=calc.querySelector("[data-result='fluid']");
var outSodium=calc.querySelector("[data-result='sodium']");
var outRate=calc.querySelector("[data-result='rate']");
if(outFluid)outFluid.textContent=(totalMl/1000).toFixed(1)+"L";
if(outSodium)outSodium.textContent=sodiumMg+"mg";
if(outRate)outRate.textContent=Math.round(totalMl/dur)+"ml/hr";
}
sliders.forEach(function(s){s.addEventListener("input",updateCalc);});
updateCalc();
});

/* Gear weight toggle */
document.addEventListener("click",function(e){
var item=e.target.closest("[data-interactive='gear-toggle'] .rl-infographic-gear-item");
if(!item)return;
item.classList.toggle("active");
var container=item.closest("[data-interactive='gear-toggle']");
if(!container)return;
var total=0;
container.querySelectorAll(".rl-infographic-gear-item.active").forEach(function(it){
total+=parseFloat(it.getAttribute("data-weight")||"0");
});
var valEl=container.querySelector(".rl-infographic-gear-total-value");
if(valEl)valEl.textContent=total.toFixed(1)+"kg";
var fillEl=container.querySelector(".rl-infographic-gear-bar-fill");
var maxW=parseFloat(container.getAttribute("data-max-weight")||"12");
if(fillEl)fillEl.style.width=Math.min(100,total/maxW*100)+"%";
track("infographic_interact",{type:"gear-toggle",total:total.toFixed(1)});
});

/* Before/after drag */
(function(){
var active=null;
function startDrag(e){
var ba=e.target.closest("[data-interactive='before-after']");
if(!ba)return;
active=ba;
e.preventDefault();
}
function moveDrag(e){
if(!active)return;
var rect=active.getBoundingClientRect();
var clientX=e.touches?e.touches[0].clientX:e.clientX;
var pct=Math.max(10,Math.min(90,((clientX-rect.left)/rect.width)*100));
var divider=active.querySelector(".rl-infographic-ba-divider");
var afterSide=active.querySelector(".rl-infographic-ba-side:last-of-type");
if(divider)divider.style.left=pct+"%";
if(afterSide)afterSide.style.clipPath="inset(0 0 0 "+pct+"%)";
}
function stopDrag(){
if(active){track("infographic_interact",{type:"before-after"});active=null;}
}
document.addEventListener("mousedown",startDrag);
document.addEventListener("mousemove",moveDrag);
document.addEventListener("mouseup",stopDrag);
document.addEventListener("touchstart",startDrag,{passive:false});
document.addEventListener("touchmove",moveDrag,{passive:false});
document.addEventListener("touchend",stopDrag);
})();

/* Timeline expand */
document.addEventListener("click",function(e){
var header=e.target.closest("[data-interactive='timeline'] .rl-infographic-timeline-header");
if(!header)return;
var node=header.closest(".rl-infographic-timeline-node");
if(node)node.classList.toggle("open");
var expand=header.querySelector(".rl-infographic-timeline-expand");
if(expand)expand.textContent=node.classList.contains("open")?"\u2212":"+";
track("infographic_interact",{type:"timeline"});
});

/* Decision tree interaction */
document.addEventListener("click",function(e){
var btn=e.target.closest(".rl-decision-tree__option");
if(!btn)return;
var tree=btn.closest(".rl-decision-tree");
if(!tree)return;
var treeData;
try{treeData=JSON.parse(tree.getAttribute("data-tree")||"{}");}catch(ex){return;}
var target=btn.getAttribute("data-target");
var isResult=btn.getAttribute("data-is-result")==="true";
if(isResult){
var resultEl=tree.querySelector(".rl-decision-tree__result");
var bodyEl=tree.querySelector(".rl-decision-tree__body");
var restartEl=tree.querySelector(".rl-decision-tree__restart");
if(bodyEl)bodyEl.style.display="none";
if(resultEl&&/^[a-z0-9-]+$/.test(target)){
resultEl.textContent="";
var titleEl=document.createElement("div");
titleEl.className="rl-decision-tree__result-title";
titleEl.textContent="WE RECOMMEND";
var raceEl=document.createElement("div");
raceEl.className="rl-decision-tree__result-race";
var linkEl=document.createElement("a");
linkEl.href="/race/"+target+"/";
linkEl.textContent=target.split("-").map(function(w){return w.charAt(0).toUpperCase()+w.slice(1);}).join(" ");
raceEl.appendChild(linkEl);
resultEl.appendChild(titleEl);
resultEl.appendChild(raceEl);
resultEl.style.display="block";
}
if(restartEl)restartEl.style.display="block";
track("decision_tree_result",{race:target});
}else{
var node=treeData[target];
if(!node)return;
var qEl=tree.querySelector(".rl-decision-tree__question");
var optsEl=tree.querySelector(".rl-decision-tree__options");
if(qEl)qEl.textContent=node.question||"";
if(optsEl){
optsEl.innerHTML="";
(node.options||[]).forEach(function(opt){
var b=document.createElement("button");
b.className="rl-decision-tree__option";
b.setAttribute("data-target",opt.next||opt.result||"");
b.setAttribute("data-is-result",opt.result?"true":"false");
b.textContent=opt.text||"";
optsEl.appendChild(b);
});
}
track("decision_tree_step",{node:target});
}
});
document.addEventListener("click",function(e){
var btn=e.target.closest(".rl-decision-tree__restart");
if(!btn)return;
var tree=btn.closest(".rl-decision-tree");
if(!tree)return;
var treeData;
try{treeData=JSON.parse(tree.getAttribute("data-tree")||"{}");}catch(ex){return;}
var root=treeData.root;
if(!root)return;
var bodyEl=tree.querySelector(".rl-decision-tree__body");
var resultEl=tree.querySelector(".rl-decision-tree__result");
var qEl=tree.querySelector(".rl-decision-tree__question");
var optsEl=tree.querySelector(".rl-decision-tree__options");
if(bodyEl)bodyEl.style.display="block";
if(resultEl){resultEl.style.display="none";resultEl.innerHTML="";}
btn.style.display="none";
if(qEl)qEl.textContent=root.question||"";
if(optsEl){
optsEl.innerHTML="";
(root.options||[]).forEach(function(opt){
var b=document.createElement("button");
b.className="rl-decision-tree__option";
b.setAttribute("data-target",opt.next||opt.result||"");
b.setAttribute("data-is-result",opt.result?"true":"false");
b.textContent=opt.text||"";
optsEl.appendChild(b);
});
}
track("decision_tree_restart",{});
});

})();'''


# ── Page Assembly ────────────────────────────────────────────


def generate_guide_page(content: dict, inline: bool = False, assets_dir: Path = None) -> str:
    """Generate the complete guide HTML page."""
    canonical_url = f"{SITE_BASE_URL}/guide/"
    og_image = f"{SITE_BASE_URL}/og/homepage.jpg"

    # Activate glossary for tooltip resolution in _md_inline()
    global _GLOSSARY, _RACE_INDEX
    _GLOSSARY = content.get("glossary")
    _RACE_INDEX = load_race_index()

    nav = build_nav()
    hero = build_hero(content)
    rider_selector = build_rider_selector(content)
    progress = build_progress_bar()
    chapnav = build_chapter_nav(content["chapters"])
    jsonld = build_jsonld(content)
    footer = build_footer()

    # Build chapters with CTAs
    chapters_html = []
    for ch in content["chapters"]:
        chapters_html.append(build_chapter(ch))
        cta_type = ch.get("cta_after")
        if cta_type == "gate":
            chapters_html.append(build_gate())
        elif cta_type == "finale":
            chapters_html.append(build_cta_finale())
        elif cta_type and cta_type in CTA_BUILDERS:
            chapters_html.append(CTA_BUILDERS[cta_type]())

    # CSS/JS
    guide_css_content = build_guide_css()
    guide_js_content = build_guide_js()

    if inline:
        css_html = f'<style>{guide_css_content}</style>'
        js_html = f'<script>{guide_js_content}</script>'
    else:
        # Write to assets_dir with content hash
        if assets_dir is None:
            assets_dir = OUTPUT_DIR / "guide-assets"
        assets_dir.mkdir(parents=True, exist_ok=True)

        css_hash = hashlib.md5(guide_css_content.encode()).hexdigest()[:8]
        js_hash = hashlib.md5(guide_js_content.encode()).hexdigest()[:8]

        css_file = f"rl-guide-styles.{css_hash}.css"
        js_file = f"rl-guide-scripts.{js_hash}.js"

        # Clean stale asset files before writing new ones
        for old_file in assets_dir.glob("rl-guide-styles.*.css"):
            if old_file.name != css_file:
                old_file.unlink()
                print(f"  Removed stale {old_file.name}")
        for old_file in assets_dir.glob("rl-guide-scripts.*.js"):
            if old_file.name != js_file:
                old_file.unlink()
                print(f"  Removed stale {old_file.name}")

        (assets_dir / css_file).write_text(guide_css_content, encoding="utf-8")
        (assets_dir / js_file).write_text(guide_js_content, encoding="utf-8")

        print(f"  Wrote {assets_dir / css_file} ({len(guide_css_content):,} bytes)")
        print(f"  Wrote {assets_dir / js_file} ({len(guide_js_content):,} bytes)")

        css_html = f'<link rel="stylesheet" href="/guide/guide-assets/{css_file}">'
        js_html = f'<script src="/guide/guide-assets/{js_file}"></script>'

    og_tags = f'''<meta property="og:title" content="{esc(content["title"])}">
  <meta property="og:description" content="{esc(content["meta_description"])}">
  <meta property="og:type" content="article">
  <meta property="og:url" content="{esc(canonical_url)}">
  <meta property="og:image" content="{esc(og_image)}">
  <meta property="og:site_name" content="Roadie Labs">
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:title" content="{esc(content["title"])}">
  <meta name="twitter:description" content="{esc(content["meta_description"])}">
  <meta name="twitter:image" content="{esc(og_image)}">'''

    return f'''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{esc(content["title"])} — Roadie Labs</title>
  <meta name="description" content="{esc(content["meta_description"])}">
  <link rel="canonical" href="{esc(canonical_url)}">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Sometype+Mono:wght@400;700&family=Source+Serif+4:ital,wght@0,400;0,600;0,700;1,400;1,700&display=swap">
  <!-- GA4 -->
  {get_ga4_head_snippet()}
  {og_tags}
  {jsonld}
  <style>
/* Base reset (from neo-brutalist) */
.rl-neo-brutalist-page {{
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 20px;
  font-family: 'Sometype Mono', monospace;
  background: #d0d0c8;
  color: #1a1a1a;
  line-height: 1.7;
}}
.rl-neo-brutalist-page *, .rl-neo-brutalist-page *::before, .rl-neo-brutalist-page *::after {{
  border-radius: 0 !important;
  box-shadow: none !important;
  font-family: 'Sometype Mono', monospace;
  box-sizing: border-box;
}}
{get_site_header_css()}
.rl-neo-brutalist-page .rl-breadcrumb {{ padding: 8px 24px; font-size: 11px; background: var(--rl-color-silver); }}
.rl-neo-brutalist-page .rl-breadcrumb a {{ color: var(--rl-color-coral); text-decoration: none; }}
.rl-neo-brutalist-page .rl-breadcrumb a:hover {{ color: var(--rl-color-orange); }}
.rl-neo-brutalist-page .rl-breadcrumb-sep {{ color: var(--rl-color-secondary-blue); margin: 0 6px; }}
.rl-neo-brutalist-page .rl-breadcrumb-current {{ color: var(--rl-color-near-black); }}
/* Hero */
.rl-neo-brutalist-page .rl-hero {{ background: #1a1a1a; color: #fff; padding: 60px 40px; border: 3px solid #1a1a1a; border-top: none; border-bottom: 4px double rgba(255,255,255,0.15); margin-bottom: 0; position: relative; overflow: hidden; }}
.rl-neo-brutalist-page .rl-hero-tier {{ display: inline-block; background: #1a1a1a; color: #fff; padding: 4px 12px; font-size: 12px; font-weight: 700; letter-spacing: 3px; text-transform: uppercase; margin-bottom: 16px; }}
.rl-neo-brutalist-page .rl-hero h1 {{ font-family: 'Source Serif 4', Georgia, serif; font-size: 42px; font-weight: 700; line-height: 1.1; text-transform: uppercase; letter-spacing: -0.5px; margin-bottom: 16px; color: #fff; }}
.rl-neo-brutalist-page .rl-hero-tagline {{ font-size: 14px; line-height: 1.6; color: #d0d0c8; max-width: 700px; }}
/* Footer */
.rl-neo-brutalist-page .rl-footer {{ padding: 24px 20px; border: 3px solid #1a1a1a; border-top: 4px double #1a1a1a; background: #1a1a1a; color: #d0d0c8; margin-top: 0; }}
.rl-neo-brutalist-page .rl-footer a {{ color: #f5f5f0; }}
.rl-neo-brutalist-page .rl-footer a:hover {{ color: #555555; }}
.rl-neo-brutalist-page .rl-footer-disclaimer {{ font-size: 11px; color: #555555; line-height: 1.6; }}
@media(max-width:768px){{
  .rl-neo-brutalist-page .rl-hero {{ padding: 40px 20px; }}
  .rl-neo-brutalist-page .rl-hero h1 {{ font-size: 26px; }}
  .rl-neo-brutalist-page .rl-breadcrumb {{ font-size: 10px; }}
}}
  </style>
  {css_html}
</head>
<body>

{progress}

<div class="rl-neo-brutalist-page" id="rl-guide-page">
  {nav}

  {hero}

  {rider_selector}

  {chapnav}

  {"".join(chapters_html)}

  {footer}
</div>

{js_html}

<script>{get_site_header_js()}</script>

{get_consent_banner_html()}
</body>
</html>'''


def main():
    parser = argparse.ArgumentParser(description="Generate Roadie Labs Training Guide page")
    parser.add_argument("--output-dir", default=str(OUTPUT_DIR), help="Output directory")
    parser.add_argument("--inline", action="store_true", help="Inline CSS/JS for local preview")
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    content = load_content()
    print(f"Loaded {len(content['chapters'])} chapters from {CONTENT_JSON}")

    if args.inline:
        html_content = generate_guide_page(content, inline=True)
        output_file = output_dir / "guide.html"
    else:
        assets_dir = output_dir / "guide-assets"
        html_content = generate_guide_page(content, inline=False, assets_dir=assets_dir)
        output_file = output_dir / "guide.html"

    output_file.write_text(html_content, encoding="utf-8")
    print(f"Generated {output_file} ({len(html_content):,} bytes)")


if __name__ == "__main__":
    main()
