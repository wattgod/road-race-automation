"""Generic guide-content render helpers — extracted from
gravel-race-automation/wordpress/generate_guide.py (Sprint 41 fork never
copied the module; the full file carries gravel-brand content we don't want
in this repo). Used by generate_prep_kit.py.

Functions render structured prep-kit JSON (timelines, accordions, process
lists, callouts) to brand-neutral HTML; styling comes from the consuming
page's CSS.
"""

import re

# Glossary tooltips disabled — prep kits don't use them
_GLOSSARY = None


def _md_inline(text: str) -> str:
    """Apply markdown-lite inline formatting (bold, italic, links, tooltips, counters)."""
    # Tooltip pattern: {{TERM}} → tooltip span (alpha/underscore/slash, starts with letter)
    if _GLOSSARY:
        def _tooltip_repl(m):
            term = m.group(1)
            defn = _GLOSSARY.get(term, "")
            if defn:
                return (f'<span class="gg-tooltip-trigger" tabindex="0">{esc(term)}'
                        f'<span class="gg-tooltip">{esc(defn)}</span></span>')
            return term  # no definition found, render plain
        text = re.sub(r'\{\{([A-Za-z][A-Za-z0-9_/]*)\}\}', _tooltip_repl, text)
    # Counter pattern: {{123}} → counter span (max 7 digits + 2 decimals)
    text = re.sub(
        r'\{\{(\d{1,7}(?:\.\d{1,2})?)\}\}',
        r'<span class="gg-guide-counter">\1</span>',
        text,
    )
    text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
    text = re.sub(r'\*(.+?)\*', r'<em>\1</em>', text)
    text = re.sub(r'\[(.+?)\]\((.+?)\)', r'<a href="\2">\1</a>', text)
    return text

def render_accordion(block: dict) -> str:
    """Render an accordion block with collapsible items."""
    items_html = []
    for idx, item in enumerate(block["items"]):
        title = esc(item["title"])
        content_html = _md_block(esc(item["content"]))
        panel_id = f"accordion-panel-{hashlib.md5(title.encode()).hexdigest()[:8]}-{idx}"

        items_html.append(f'''<div class="gg-guide-accordion-item">
        <button class="gg-guide-accordion-trigger" aria-expanded="false" aria-controls="{panel_id}">
          <span>{title}</span>
          <span class="gg-guide-accordion-icon" aria-hidden="true">+</span>
        </button>
        <div class="gg-guide-accordion-body" id="{panel_id}">{content_html}</div>
      </div>''')
    return '\n'.join(items_html)

def render_timeline(block: dict) -> str:
    """Render a timeline block."""
    title = esc(block.get("title", ""))
    steps = block["steps"]
    steps_html = []
    for i, step in enumerate(steps):
        label = esc(step["label"])
        content = _md_inline(esc(step["content"]))
        paras = [f'<p>{p.strip()}</p>' for p in content.split('\n') if p.strip()]
        steps_html.append(f'''<div class="gg-guide-timeline-step">
        <div class="gg-guide-timeline-marker">{i + 1}</div>
        <div class="gg-guide-timeline-content">
          <h4 class="gg-guide-timeline-label">{label}</h4>
          {''.join(paras)}
        </div>
      </div>''')

    title_html = f'<h3 class="gg-guide-timeline-title">{title}</h3>' if title else ''
    return f'''<div class="gg-guide-timeline">
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
                f'<div class="gg-guide-process-bar-wrap">'
                f'<div class="gg-guide-process-bar" style="width:{pct}%"></div>'
                f'<span class="gg-guide-process-pct">{pct}%</span>'
                f'</div>'
            )
        else:
            pct_html = ''
        items_html.append(f'''<div class="gg-guide-process-item">
        <div class="gg-guide-process-num">{i + 1}</div>
        <div class="gg-guide-process-body">
          <span class="gg-guide-process-label">{label}</span>
          {pct_html}
          <p class="gg-guide-process-detail">{detail}</p>
        </div>
      </div>''')
    return f'<div class="gg-guide-process-list">{chr(10).join(items_html)}</div>'

def render_callout(block: dict) -> str:
    """Render a callout/quote block."""
    style = block.get("style", "highlight")
    content = _md_inline(esc(block["content"]))
    paras = [f'<p>{p.strip()}</p>' for p in content.split('\n') if p.strip()]
    return f'<div class="gg-guide-callout gg-guide-callout--{esc(style)}">{"".join(paras)}</div>'
