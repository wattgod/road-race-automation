#!/usr/bin/env python3
"""
Inline SVG/HTML infographic renderers for the Roadie Labs Training Guide.

Ported/adapted from gravel-race-automation's guide_infographics.py, cut down
to the renderers the road guide actually uses, plus three road-specific
builds (event-demand matrix, build curves, echelon diagram).

All interactivity is via data-* attributes — the JS handlers and CSS already
live in generate_guide.py (they survived the generator port):
- Expandable timelines (data-interactive="timeline")
- Traffic-light cycling (data-interactive="traffic-light")
- Fade stagger (data-animate="fade-stagger")
- Line draw (data-animate="line")

All colors use CSS custom properties via var(--rl-color-*) — the palette is
monochrome, so renderers encode meaning with value (light→dark), not hue.
"""

import html as _html
import json as _json
from pathlib import Path

_RACE_INDEX_PATH = Path(__file__).parent.parent / "web" / "race-index.json"
_RACE_INDEX_CACHE = None


def _load_race_index() -> list:
    """Load and cache web/race-index.json (the same index the site renders)."""
    global _RACE_INDEX_CACHE
    if _RACE_INDEX_CACHE is None:
        _RACE_INDEX_CACHE = _json.loads(_RACE_INDEX_PATH.read_text())
    return _RACE_INDEX_CACHE


# ── Helpers ─────────────────────────────────────────────────


def _esc(text) -> str:
    """HTML-escape a string."""
    return _html.escape(str(text)) if text else ""


def _svg_open(width: int, height: int, cls: str = "") -> str:
    """Open an SVG tag with viewBox for fluid scaling."""
    c = f' class="{cls}"' if cls else ""
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}"'
        f'{c} role="img" aria-hidden="true"'
        f' style="width:100%;height:auto;display:block">'
    )


def _svg_close() -> str:
    return "</svg>"


def _svg_rect(x, y, w, h, fill="", stroke="", stroke_width=0, rx=0, extra="") -> str:
    """Render an SVG <rect>. rx=0 enforced (brand: no border-radius)."""
    parts = [f'<rect x="{x}" y="{y}" width="{w}" height="{h}"']
    if fill:
        parts.append(f' fill="{fill}"')
    if stroke:
        parts.append(f' stroke="{stroke}" stroke-width="{stroke_width}"')
    if extra:
        parts.append(f" {extra}")
    parts.append("/>")
    return "".join(parts)


def _svg_text(x, y, text, font_size=14, fill="", anchor="start",
              weight="", family="", extra="") -> str:
    """Render an SVG <text> element.

    font-family is set via style="" attribute (not presentation attribute)
    so that CSS custom properties like var(--rl-font-data) can resolve.
    """
    parts = [f'<text x="{x}" y="{y}" font-size="{font_size}"']
    if fill:
        parts.append(f' fill="{fill}"')
    if anchor != "start":
        parts.append(f' text-anchor="{anchor}"')
    if weight:
        parts.append(f' font-weight="{weight}"')
    if family:
        parts.append(f' style="font-family:{family}"')
    if extra:
        parts.append(f" {extra}")
    parts.append(f">{_esc(text)}</text>")
    return "".join(parts)


def _svg_line(x1, y1, x2, y2, stroke="", stroke_width=2, extra="") -> str:
    parts = [f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}"']
    if stroke:
        parts.append(f' stroke="{stroke}"')
    parts.append(f' stroke-width="{stroke_width}"')
    if extra:
        parts.append(f" {extra}")
    parts.append("/>")
    return "".join(parts)


def _svg_path(d: str, stroke="", stroke_width=2, fill="none", extra="") -> str:
    parts = [f'<path d="{d}"']
    if stroke:
        parts.append(f' stroke="{stroke}"')
    parts.append(f' stroke-width="{stroke_width}" fill="{fill}"')
    if extra:
        parts.append(f" {extra}")
    parts.append("/>")
    return "".join(parts)


def _cubic_bezier_path(points: list[tuple[float, float]]) -> str:
    """Convert (x, y) points to a smooth SVG path (Catmull-Rom → cubic Bezier)."""
    if len(points) < 2:
        return ""
    if len(points) == 2:
        return f"M {points[0][0]},{points[0][1]} L {points[1][0]},{points[1][1]}"

    tension = 0.3
    segments = []
    n = len(points)
    for i in range(n - 1):
        p0 = points[max(i - 1, 0)]
        p1 = points[i]
        p2 = points[min(i + 1, n - 1)]
        p3 = points[min(i + 2, n - 1)]
        cp1x = p1[0] + (p2[0] - p0[0]) * tension
        cp1y = p1[1] + (p2[1] - p0[1]) * tension
        cp2x = p2[0] - (p3[0] - p1[0]) * tension
        cp2y = p2[1] - (p3[1] - p1[1]) * tension
        if i == 0:
            segments.append(f"M {p1[0]:.1f},{p1[1]:.1f}")
        segments.append(
            f"C {cp1x:.1f},{cp1y:.1f} {cp2x:.1f},{cp2y:.1f} {p2[0]:.1f},{p2[1]:.1f}"
        )
    return " ".join(segments)


def _figure_wrap(inner: str, caption: str, layout: str = "inline",
                 asset_id: str = "", alt: str = "",
                 title: str = "", takeaway: str = "") -> str:
    """Wrap content in a <figure> with optional title bar, takeaway, caption."""
    cls = "rl-infographic"
    if layout and layout != "inline":
        cls += f" rl-infographic--{layout}"
    aid = f' data-asset-id="{_esc(asset_id)}"' if asset_id else ""
    aria = f' aria-label="{_esc(alt)}"' if alt else ""
    role = ' role="figure"' if alt else ""
    title_html = (
        f'<div class="rl-infographic-title">{_esc(title)}</div>'
        if title else ""
    )
    takeaway_html = (
        f'<div class="rl-infographic-takeaway">{_esc(takeaway)}</div>'
        if takeaway else ""
    )
    cap = (
        f'<figcaption class="rl-infographic-caption">{_esc(caption)}</figcaption>'
        if caption else ""
    )
    return f'<figure class="{cls}"{aid}{role}{aria}>{title_html}{inner}{takeaway_html}{cap}</figure>'


# ══════════════════════════════════════════════════════════════
# Road-specific renderers
# ══════════════════════════════════════════════════════════════


# Demand weight → monochrome fill. Meaning is encoded in value, not hue.
_DEMAND_FILLS = {
    0: "var(--rl-color-cool-white)",
    1: "var(--rl-color-silver)",
    2: "var(--rl-color-steel)",
    3: "var(--rl-color-near-black)",
}

_DEMAND_LEGEND = ["Marginal", "Present", "Important", "Decisive"]

# Event rows: (label, [endurance, threshold, anaerobic, pack skills, logistics])
# The numbers restate chapters 1-2 in one glance: what each event is decided by.
_EVENT_DEMANDS = [
    ("Criterium", [1, 2, 3, 3, 0]),
    ("Time trial", [1, 3, 1, 0, 1]),
    ("Hillclimb", [1, 3, 1, 0, 0]),
    ("Road race (cat)", [2, 2, 3, 3, 1]),
    ("Flat fondo / century", [3, 1, 1, 2, 2]),
    ("Mountain fondo", [3, 3, 1, 1, 2]),
    ("Multi-stage", [3, 2, 2, 2, 3]),
    ("Randonn\u00e9e", [3, 1, 0, 1, 3]),
]

_DEMAND_COLS = ["Endurance", "Threshold", "Anaerobic", "Pack skills", "Logistics"]


def render_event_demand_matrix(block: dict) -> str:
    """Event types × physiological/skill demands as a shaded matrix.

    The one-glance version of the guide's demand mapping: find your event's
    row, and the dark cells are what your training has to buy.
    """
    label_w = 250
    header_h = 56
    cell_w = 176
    cell_h = 58
    gap = 4
    n_rows = len(_EVENT_DEMANDS)
    n_cols = len(_DEMAND_COLS)
    legend_h = 70
    vb_w = label_w + n_cols * (cell_w + gap) + 20
    vb_h = header_h + n_rows * (cell_h + gap) + legend_h

    svg = [_svg_open(vb_w, vb_h, "rl-infographic-svg")]

    # Column headers
    for c, col in enumerate(_DEMAND_COLS):
        x = label_w + c * (cell_w + gap) + cell_w / 2
        svg.append(_svg_text(
            x, header_h - 20, col.upper(),
            font_size=15, fill="var(--rl-color-near-black)",
            anchor="middle", weight="700", family="var(--rl-font-data)",
            extra='letter-spacing="2"'
        ))

    # Rows
    for r, (event, weights) in enumerate(_EVENT_DEMANDS):
        y = header_h + r * (cell_h + gap)
        svg.append(_svg_text(
            label_w - 16, y + cell_h / 2 + 6, event,
            font_size=17, fill="var(--rl-color-near-black)",
            anchor="end", weight="700", family="var(--rl-font-editorial)"
        ))
        for c, w in enumerate(weights):
            x = label_w + c * (cell_w + gap)
            svg.append(_svg_rect(
                x, y, cell_w, cell_h,
                fill=_DEMAND_FILLS[w],
                stroke="var(--rl-color-near-black)",
                stroke_width=2 if w == 0 else 0,
            ))

    # Legend
    ly = header_h + n_rows * (cell_h + gap) + 28
    lx = label_w
    for i, label in enumerate(_DEMAND_LEGEND):
        svg.append(_svg_rect(
            lx, ly, 22, 22,
            fill=_DEMAND_FILLS[i],
            stroke="var(--rl-color-near-black)",
            stroke_width=2 if i == 0 else 0,
        ))
        svg.append(_svg_text(
            lx + 30, ly + 16, label,
            font_size=14, fill="var(--rl-color-secondary-blue)",
            family="var(--rl-font-data)"
        ))
        lx += 30 + len(label) * 9 + 60

    svg.append(_svg_close())
    return _figure_wrap(
        "".join(svg), block.get("caption", ""), block.get("layout", "inline"),
        block.get("asset_id", ""), block.get("alt", ""),
        title="What Each Event Is Actually Decided By",
        takeaway="Find your event's row. The dark cells are what your training has to buy — everything else is garnish.",
    )


def render_build_curves(block: dict) -> str:
    """16-week build: fondo volume curve vs crit/TT volume + intensity.

    The visual argument for chapter 2's hours-pick-the-event claim: the fondo
    build is a volume ramp; the crit/TT build holds hours flat and buys
    sharpness with intensity instead.
    """
    vb_w, vb_h = 1200, 620
    margin_l, margin_r = 90, 40
    chart_top = 70
    chart_bot = 480
    chart_w = vb_w - margin_l - margin_r
    chart_h = chart_bot - chart_top
    max_hours = 12.0

    def x_at(week):  # weeks 1..16
        return margin_l + (week - 1) / 15 * chart_w

    def y_at(hours):
        return chart_bot - (hours / max_hours) * chart_h

    # Weekly hours, weeks 1-16. Fondo: ramp with recovery dips, then taper.
    fondo = [6, 6.5, 7, 5.5, 7.5, 8, 8.5, 6, 9, 9.5, 10, 6.5, 10.5, 11, 7, 4.5]
    # Crit/TT: hours stay flat; the race-week dip is the whole taper.
    crit = [5, 5, 5, 4.5, 5, 5, 5, 4.5, 5, 5, 5, 4.5, 5, 5, 5, 4]
    # Crit intensity, plotted on the same axis as a relative curve (dashed).
    crit_intensity = [3, 3.2, 3.4, 3, 3.8, 4.2, 4.6, 4, 5.2, 5.8, 6.4, 5.5, 7.2, 7.8, 8.2, 6]

    svg = [_svg_open(vb_w, vb_h, "rl-infographic-svg")]

    # Phase bands: Base 1-8, Build 9-14, Taper 15-16
    phases = [(1, 8, "BASE"), (9, 14, "BUILD"), (15, 16, "TAPER")]
    for i, (w1, w2, name) in enumerate(phases):
        x1 = x_at(w1)
        x2 = x_at(w2) + (chart_w / 15 if w2 < 16 else 0)
        if i % 2 == 1:
            svg.append(_svg_rect(x1, chart_top, x2 - x1, chart_h,
                                 fill="var(--rl-color-silver)", extra='opacity="0.35"'))
        svg.append(_svg_text(
            (x1 + x2) / 2, chart_top - 16, name,
            font_size=14, fill="var(--rl-color-secondary-blue)",
            anchor="middle", weight="700", family="var(--rl-font-data)",
            extra='letter-spacing="3"'
        ))

    # Axes
    svg.append(_svg_line(margin_l, chart_top, margin_l, chart_bot,
                         stroke="var(--rl-color-near-black)", stroke_width=3))
    svg.append(_svg_line(margin_l, chart_bot, margin_l + chart_w, chart_bot,
                         stroke="var(--rl-color-near-black)", stroke_width=3))
    for h in (4, 8, 12):
        svg.append(_svg_line(margin_l - 6, y_at(h), margin_l + chart_w, y_at(h),
                             stroke="var(--rl-color-light-steel)", stroke_width=1,
                             extra='stroke-dasharray="4 6"'))
        svg.append(_svg_text(margin_l - 14, y_at(h) + 5, f"{h}h",
                             font_size=13, fill="var(--rl-color-secondary-blue)",
                             anchor="end", family="var(--rl-font-data)"))
    for wk in (1, 4, 8, 12, 16):
        svg.append(_svg_text(x_at(wk), chart_bot + 26, f"WK {wk}",
                             font_size=12, fill="var(--rl-color-secondary-blue)",
                             anchor="middle", family="var(--rl-font-data)"))

    # Curves
    fondo_pts = [(x_at(i + 1), y_at(h)) for i, h in enumerate(fondo)]
    crit_pts = [(x_at(i + 1), y_at(h)) for i, h in enumerate(crit)]
    intensity_pts = [(x_at(i + 1), y_at(h)) for i, h in enumerate(crit_intensity)]

    svg.append(_svg_path(_cubic_bezier_path(fondo_pts),
                         stroke="var(--rl-color-near-black)", stroke_width=4,
                         extra='stroke-linecap="square"'))
    svg.append(_svg_path(_cubic_bezier_path(crit_pts),
                         stroke="var(--rl-color-steel)", stroke_width=4,
                         extra='stroke-linecap="square"'))
    svg.append(_svg_path(_cubic_bezier_path(intensity_pts),
                         stroke="var(--rl-color-secondary-blue)", stroke_width=3,
                         extra='stroke-dasharray="10 7"'))

    # Curve labels
    svg.append(_svg_text(x_at(13.5), y_at(11.4), "Fondo build: hours ramp",
                         font_size=16, fill="var(--rl-color-near-black)",
                         anchor="end", weight="700", family="var(--rl-font-editorial)"))
    svg.append(_svg_text(x_at(9), y_at(5) - 14, "Crit/TT build: hours stay flat",
                         font_size=16, fill="var(--rl-color-secondary-blue)",
                         anchor="middle", weight="700", family="var(--rl-font-editorial)"))
    svg.append(_svg_text(x_at(14.2), y_at(8.4), "\u2026intensity ramps instead",
                         font_size=15, fill="var(--rl-color-secondary-blue)",
                         anchor="end", weight="700", family="var(--rl-font-editorial)",
                         extra='font-style="italic"'))

    # Recovery-week markers on the fondo line
    for wk in (4, 8, 12):
        svg.append(_svg_rect(x_at(wk) - 4, y_at(fondo[wk - 1]) - 4, 8, 8,
                             fill="var(--rl-color-cool-white)",
                             stroke="var(--rl-color-near-black)", stroke_width=2))
    svg.append(_svg_text(x_at(4), y_at(fondo[3]) + 28, "recovery weeks",
                         font_size=12, fill="var(--rl-color-secondary-blue)",
                         anchor="middle", family="var(--rl-font-data)"))

    # Footer strip
    svg.append(_svg_rect(margin_l, chart_bot + 46, chart_w, 50,
                         fill="none", stroke="var(--rl-color-steel)", stroke_width=2))
    svg.append(_svg_text(
        vb_w / 2, chart_bot + 77,
        "Same 16 weeks, two different purchases: the fondo buys durability with hours, the crit buys sharpness without them.",
        font_size=15, fill="var(--rl-color-near-black)",
        anchor="middle", weight="600", family="var(--rl-font-editorial)"
    ))

    svg.append(_svg_close())
    return _figure_wrap(
        "".join(svg), block.get("caption", ""), block.get("layout", "inline"),
        block.get("asset_id", ""), block.get("alt", ""),
        title="Two Builds, One Calendar",
        takeaway="If your hours are capped, pick the event whose build fits them \u2014 don't ride a starved version of the wrong one.",
    )


def render_echelon_diagram(block: dict) -> str:
    """Top-down crosswind diagram: the echelon vs the gutter.

    Chapter 6's most spatial idea, drawn: a diagonal echelon fills the road,
    seats are finite, and the queue in the gutter gets zero shelter.
    """
    vb_w, vb_h = 1200, 640
    road_top, road_bot = 170, 470
    road_left, road_right = 60, 1140

    svg = [_svg_open(vb_w, vb_h, "rl-infographic-svg")]

    # Wind arrows (crosswind from top of frame = rider's left)
    for i in range(5):
        ax = 180 + i * 200
        svg.append(_svg_line(ax, 40, ax, 120,
                             stroke="var(--rl-color-steel)", stroke_width=4))
        svg.append(_svg_path(f"M {ax - 10},{104} L {ax},{124} L {ax + 10},{104}",
                             stroke="var(--rl-color-steel)", stroke_width=4))
    svg.append(_svg_text(600, 30, "CROSSWIND",
                         font_size=16, fill="var(--rl-color-secondary-blue)",
                         anchor="middle", weight="700", family="var(--rl-font-data)",
                         extra='letter-spacing="4"'))

    # Road surface
    svg.append(_svg_rect(road_left, road_top, road_right - road_left,
                         road_bot - road_top,
                         fill="var(--rl-color-silver)",
                         stroke="var(--rl-color-near-black)", stroke_width=3))
    # Center line
    svg.append(_svg_line(road_left, (road_top + road_bot) / 2, road_right,
                         (road_top + road_bot) / 2,
                         stroke="var(--rl-color-cool-white)", stroke_width=3,
                         extra='stroke-dasharray="26 20"'))
    # Direction of travel
    svg.append(_svg_text(road_left + 8, road_top - 12, "\u2190 DIRECTION OF RACE",
                         font_size=13, fill="var(--rl-color-secondary-blue)",
                         weight="700", family="var(--rl-font-data)",
                         extra='letter-spacing="2"'))

    def rider(x, y, dark=True):
        fill = "var(--rl-color-near-black)" if dark else "var(--rl-color-secondary-blue)"
        return _svg_rect(x, y, 20, 44, fill=fill,
                         stroke="var(--rl-color-cool-white)", stroke_width=2)

    # The echelon: diagonal line of riders, front-left (upwind) to rear-right
    ex, ey = 150, 200
    for i in range(7):
        svg.append(rider(ex + i * 78, ey + i * 32))

    # The gutter: single file pressed against the downwind (bottom) edge
    for i in range(6):
        svg.append(rider(790 + i * 56, road_bot - 52, dark=False))

    # Labels with leader lines
    svg.append(_svg_line(420, 320, 560, 540, stroke="var(--rl-color-near-black)",
                         stroke_width=2))
    svg.append(_svg_text(565, 548, "The echelon: each rider shelters diagonally behind the last. Seats are finite.",
                         font_size=16, fill="var(--rl-color-near-black)",
                         weight="700", family="var(--rl-font-editorial)"))

    svg.append(_svg_line(1000, 445, 1020, 590, stroke="var(--rl-color-secondary-blue)",
                         stroke_width=2))
    svg.append(_svg_text(1015, 612, "The gutter: single file, zero shelter, full wind bill.",
                         font_size=16, fill="var(--rl-color-secondary-blue)",
                         anchor="end", weight="700", family="var(--rl-font-editorial)"))

    svg.append(_svg_close())
    return _figure_wrap(
        "".join(svg), block.get("caption", ""), block.get("layout", "inline"),
        block.get("asset_id", ""), block.get("alt", ""),
        title="Crosswind Geometry: Echelon vs Gutter",
        takeaway="An echelon has a fixed number of seats. Be in it before the road turns \u2014 or organize the next one. Never just queue.",
    )


# ══════════════════════════════════════════════════════════════
# Ported renderers (gravel → road tokens, road numbers)
# ══════════════════════════════════════════════════════════════


def render_supercompensation(block: dict) -> str:
    """Supercompensation curve: stress → fatigue → recovery → adaptation overshoot."""
    vb_w, vb_h = 1200, 600
    margin_l, margin_r = 80, 60
    chart_bot = 500
    chart_w = vb_w - margin_l - margin_r
    baseline_y = chart_bot - 200

    curve_pts = [
        (0.00, 0), (0.05, 5), (0.10, -10), (0.15, -80), (0.20, -120),
        (0.25, -100), (0.30, -60), (0.35, -20), (0.40, 0), (0.45, 30),
        (0.50, 55), (0.55, 70), (0.60, 65), (0.65, 50), (0.70, 30),
        (0.75, 15), (0.80, 5), (0.85, 0), (0.90, -5), (0.95, -8), (1.00, -10),
    ]
    points = [
        (margin_l + frac * chart_w, baseline_y - offset)
        for frac, offset in curve_pts
    ]

    svg = [_svg_open(vb_w, vb_h, "rl-infographic-svg")]

    svg.append(_svg_line(margin_l, baseline_y, margin_l + chart_w, baseline_y,
                         stroke="var(--rl-color-light-steel)", stroke_width=2,
                         extra='stroke-dasharray="8 4"'))
    svg.append(_svg_text(
        margin_l - 10, baseline_y + 5, "Baseline",
        font_size=12, fill="var(--rl-color-secondary-blue)",
        anchor="end", family="var(--rl-font-data)"
    ))

    svg.append(_svg_path(
        _cubic_bezier_path(points),
        stroke="var(--rl-color-near-black)", stroke_width=3,
        extra='stroke-linecap="round" data-animate="line"'
              ' class="rl-line-chart__path"'
    ))

    key_pts = [(0.20, -120, "Nadir"), (0.55, 70, "Peak")]
    for frac, offset, _label in key_pts:
        mx = margin_l + frac * chart_w
        my = baseline_y - offset
        svg.append(_svg_rect(
            mx - 4, my - 4, 8, 8,
            fill="var(--rl-color-near-black)",
            stroke="var(--rl-color-cool-white)", stroke_width=2,
            extra='class="rl-line-chart__marker"'
        ))

    phase_labels = [
        (0.12, -140, "Training\nStress", "var(--rl-color-error)",
         "The workout itself \u2014 muscle fiber damage and glycogen depletion"),
        (0.22, -150, "Fatigue", "var(--rl-color-error)",
         "Performance dips below baseline as the body repairs damage"),
        (0.35, 10, "Recovery", "var(--rl-color-secondary-blue)",
         "Repair and adaptation \u2014 sleep, food, and easy days"),
        (0.55, 95, "Supercompensation", "var(--rl-color-near-black)",
         "The window where fitness exceeds the old baseline \u2014 train again here"),
        (0.80, 25, "Detraining", "var(--rl-color-secondary-blue)",
         "Wait too long and the adaptation quietly leaves"),
    ]
    for idx, (frac, y_off, label, color, tip) in enumerate(phase_labels):
        x = margin_l + frac * chart_w
        y = baseline_y - y_off
        delay_ms = 2500 + idx * 300
        svg.append(f'<g class="rl-line-chart__annotation" style="--delay:{delay_ms}ms">')
        for j, line in enumerate(label.split("\n")):
            extra_attr = f'data-tooltip="{_esc(tip)}" tabindex="0"' if j == 0 else ""
            svg.append(_svg_text(
                x, y + j * 18, line,
                font_size=14, fill=color,
                anchor="middle", weight="700",
                family="var(--rl-font-editorial)",
                extra=extra_attr
            ))
        svg.append("</g>")

    svg.append(_svg_rect(margin_l, chart_bot + 20, chart_w, 50,
                         fill="none",
                         stroke="var(--rl-color-steel)", stroke_width=2))
    svg.append(_svg_text(
        vb_w / 2, chart_bot + 50,
        "Train hard enough to trigger adaptation, then rest long enough to collect it.",
        font_size=14, fill="var(--rl-color-near-black)",
        anchor="middle", weight="600",
        family="var(--rl-font-editorial)"
    ))

    svg.append(_svg_close())
    return _figure_wrap(
        "".join(svg), block.get("caption", ""), block.get("layout", "inline"),
        block.get("asset_id", ""), block.get("alt", ""),
        title="Supercompensation: Why Rest Makes You Faster",
        takeaway="You don\u2019t get faster during the workout \u2014 you get faster during the recovery you keep skipping.",
    )


def render_traffic_light(block: dict) -> str:
    """Green/Yellow/Red autoregulation — click-to-cycle states.

    Text mirrors chapter 4's Green/Yellow/Red prose so the graphic and the
    paragraph never disagree.
    """
    signals = [
        {
            "state": "go",
            "label": "GREEN \u2014 Execute",
            "criteria": "Slept fine, legs normal, motivation ordinary or better",
            "action": "Do the session as written. Full targets.",
        },
        {
            "state": "caution",
            "label": "YELLOW \u2014 Adjust",
            "criteria": "One system complaining: short sleep, heavy legs, or elevated stress",
            "action": "Start the session, reassess after rep one. Dropping the last rep or 5-10 watts is honest, not soft.",
        },
        {
            "state": "stop",
            "label": "RED \u2014 Swap",
            "criteria": "Multiple signals at once: bad sleep and elevated resting HR and dread at the sight of the bike",
            "action": "Easy endurance or rest. The workout still exists on Thursday.",
        },
    ]

    indicator_svg = (
        '<svg viewBox="0 0 32 32" width="32" height="32" aria-hidden="true">'
        '<rect x="0" y="0" width="32" height="32"/></svg>'
    )
    rows = []
    for s in signals:
        rows.append(
            f'<div class="rl-infographic-signal-row" data-state="{s["state"]}"'
            f' tabindex="0" role="button"'
            f' aria-label="{_esc(s["label"])}: {_esc(s["criteria"])}">'
            f'<div class="rl-infographic-signal-indicator">{indicator_svg}</div>'
            f'<div class="rl-infographic-signal-body">'
            f'<div class="rl-infographic-signal-label">{_esc(s["label"])}</div>'
            f'<div class="rl-infographic-signal-criteria">{_esc(s["criteria"])}</div>'
            f'<div class="rl-infographic-signal-action">{_esc(s["action"])}</div>'
            f'</div>'
            f'</div>'
        )

    inner = (
        f'<div class="rl-infographic-traffic-light"'
        f' data-interactive="traffic-light" data-state="go">'
        f'{"".join(rows)}'
        f'</div>'
    )
    return _figure_wrap(
        inner, block.get("caption", ""), block.get("layout", "inline"),
        block.get("asset_id", ""), block.get("alt", ""),
        title="Green, Yellow, Red: The Pre-Session Check",
        takeaway="Neither soft-pedal every hard day nor bulldoze real warning signs. Two or more red signals means the smart ride is the easy one.",
    )


def render_fueling_timeline(block: dict) -> str:
    """Race-day fueling as an expandable timeline (numbers match chapter 5)."""
    markers = [
        ("T-3 HRS", "Pre-race breakfast",
         "Carb-heavy, low fiber, tested weeks ago",
         "The breakfast you practiced on long-ride mornings \u2014 nothing interesting, nothing new. Roughly three hours out so it's digested by the gun."),
        ("T-20 MIN", "Top off",
         "One gel or half a bottle of mix, 20-30g carbs",
         "A small deposit right before the start. Caffeine here if it's part of your tested plan."),
        ("MIN 15-20", "Start the clock",
         "First intake early \u2014 hunger is a lagging indicator",
         "Set a timer. Fueling fails on a 45-90 minute delay: by the time you feel the hole, you dug it an hour ago."),
        ("EVERY 20 MIN", "Steady drip",
         "60-90g carbs/hr, trained gut up to 90+",
         "Mix sources \u2014 drink mix, gels, chews. Race-effort days sit at the top of the range, but only if you rehearsed it in training (see gut training, above)."),
        ("ONGOING", "Hydration + sodium",
         "Bottles to your sweat rate, sodium on hot days",
         "You measured your sweat rate in training; race day just executes it. Dehydration and bonking impersonate each other \u2014 the carb clock tells you which one you're in."),
    ]

    nodes = []
    for i, (tag, label, summary, detail) in enumerate(markers):
        nodes.append(
            f'<div class="rl-infographic-timeline-node" style="--delay:{i * 80}ms">'
            f'<div class="rl-infographic-timeline-header" tabindex="0" role="button"'
            f' aria-expanded="false">'
            f'<span class="rl-infographic-timeline-tag">{_esc(tag)}</span>'
            f'<span class="rl-infographic-timeline-label">{_esc(label)}</span>'
            f'<span class="rl-infographic-timeline-expand" aria-hidden="true">+</span>'
            f'</div>'
            f'<div class="rl-infographic-timeline-summary">{_esc(summary)}</div>'
            f'<div class="rl-infographic-timeline-detail">{_esc(detail)}</div>'
            f'</div>'
        )

    inner = (
        f'<div class="rl-infographic-timeline" data-interactive="timeline"'
        f' data-animate="fade-stagger">{"".join(nodes)}</div>'
    )
    return _figure_wrap(
        inner, block.get("caption", ""), block.get("layout", "inline"),
        block.get("asset_id", ""), block.get("alt", ""),
        title="Race-Day Fueling, Hour by Hour",
        takeaway="Start eating in the first 20 minutes, not when you're hungry. Hunger is the bill arriving, not the reminder.",
    )


# ── Data-driven renderers (computed from web/race-index.json) ─


# Tier → point fill. Value encodes prestige: darker = higher tier.
_TIER_FILLS = {
    1: "var(--rl-color-near-black)",
    2: "var(--rl-color-steel)",
    3: "var(--rl-color-silver)",
    4: "var(--rl-color-silver)",
}

# Slug → (label, dx, dy) for annotated points. Offsets hand-tuned so labels
# don't collide in the dense 100-200km band.
_SCATTER_CALLOUTS = {
    "letape-du-tour": ("L'\u00c9tape du Tour", 14, -14),
    "maratona-dles-dolomites": ("Maratona dles Dolomites", 14, 22),
    "tour-of-flanders-sportive": ("Tour of Flanders", 10, -16),
    "paris-roubaix-challenge": ("Paris-Roubaix Challenge", 10, 26),
    "mallorca-312": ("Mallorca 312", -14, -16),
}

_SCATTER_MAX_KM = 350
_SCATTER_MAX_DENSITY = 40.0

# Rider-type training envelopes: (max distance km, max climbing density m/km).
# Prototype heuristics matched to the personalization hour bands; the point is
# the *shape* of the split, not clinical precision. Stretch = within 30%.
_RIDER_ENVELOPES = {
    "autobus": ("Autobus \u00b7 0-5 hrs/wk", 130, 18.0),
    "finisher": ("Finisher \u00b7 5-12 hrs/wk", 190, 26.0),
    "sharp-end": ("Sharp End \u00b7 12-18 hrs/wk", 260, 34.0),
    "racer": ("Racer \u00b7 18+ hrs/wk", None, None),
}
_ENVELOPE_STRETCH = 1.3


def _classify_envelope(rider: str, km: float, density: float) -> str:
    """Classify a race against a rider envelope: 'in', 'st' (stretch), 'out'."""
    _, max_km, max_dens = _RIDER_ENVELOPES[rider]
    if max_km is None:
        return "in"
    if km <= max_km and density <= max_dens:
        return "in"
    if km <= max_km * _ENVELOPE_STRETCH and density <= max_dens * _ENVELOPE_STRETCH:
        return "st"
    return "out"


def render_race_scatter(block: dict) -> str:
    """Scatter of every rated single-day race: distance vs climbing density.

    Computed at build time from web/race-index.json, so the chart is always
    in sync with the database. Races over 350 km (randonn\u00e9es, multi-day
    totals) are outside the guide's scope and excluded; hillclimbs steeper
    than 40 m/km are clipped to the top edge.

    Personalization layer ("find yourself in the data"): every point carries
    per-rider envelope classifications baked in at build time. The JS envelope
    handler reads the reader's rider type (set by the pillar quiz / rider
    selector) and dims what's out of reach \u2014 no clicking required, which
    matters because only ~10-15% of readers ever interact (Aisch, NYT).
    """
    races = [
        r for r in _load_race_index()
        if r.get("distance_km") and r.get("elevation_m") is not None
        and r["distance_km"] <= _SCATTER_MAX_KM
    ]
    n_total = len(_load_race_index())

    vb_w, vb_h = 1400, 640
    margin_l, margin_r, chart_top, chart_bot = 90, 40, 50, 540
    chart_w = vb_w - margin_l - margin_r
    chart_h = chart_bot - chart_top

    def _to_xy(km, density):
        x = margin_l + (km / _SCATTER_MAX_KM) * chart_w
        y = chart_bot - (min(density, _SCATTER_MAX_DENSITY) / _SCATTER_MAX_DENSITY) * chart_h
        return x, y

    svg = [_svg_open(vb_w, vb_h, "rl-infographic-svg")]

    # Grid + axis labels
    for dens_mark in range(0, 41, 10):
        _, y = _to_xy(0, dens_mark)
        svg.append(_svg_line(margin_l, y, margin_l + chart_w, y,
                             stroke="var(--rl-color-silver)", stroke_width=1,
                             extra='stroke-dasharray="4 4"'))
        svg.append(_svg_text(margin_l - 10, y + 5, f"{dens_mark}",
                             font_size=13, fill="var(--rl-color-steel)",
                             anchor="end", family="var(--rl-font-data)"))
    for km_mark in range(0, _SCATTER_MAX_KM + 1, 50):
        x, _ = _to_xy(km_mark, 0)
        svg.append(_svg_text(x, chart_bot + 26, f"{km_mark}km",
                             font_size=13, fill="var(--rl-color-steel)",
                             anchor="middle", family="var(--rl-font-data)"))
    svg.append(_svg_text(margin_l - 60, chart_top - 18, "CLIMBING DENSITY (M/KM)",
                         font_size=13, fill="var(--rl-color-near-black)",
                         weight="700", family="var(--rl-font-data)",
                         extra='letter-spacing="2"'))

    # Points — tier 2-4 first (light), tier 1 on top (dark, larger).
    # Each point carries its envelope class per rider type so CSS can dim
    # out-of-reach races the moment the reader's rider type is known.
    def _point(r):
        density = r["elevation_m"] / r["distance_km"]
        x, y = _to_xy(r["distance_km"], density)
        tier = r.get("tier", 3)
        size = 13 if tier == 1 else 9
        tip = (f"{r['name']}: {r['distance_km']:.0f}km, "
               f"{r['elevation_m']:.0f}m ({density:.1f} m/km), Tier {tier}")
        env_attrs = " ".join(
            f'data-env-{rid}="{_classify_envelope(rid, r["distance_km"], density)}"'
            for rid in _RIDER_ENVELOPES
        )
        return _svg_rect(
            x - size / 2, y - size / 2, size, size,
            fill=_TIER_FILLS.get(tier, "var(--rl-color-silver)"),
            stroke="var(--rl-color-cool-white)" if tier == 1 else "",
            stroke_width=1.5 if tier == 1 else 0,
            extra=f'class="rl-ig-env-dot" {env_attrs} data-tooltip="{_esc(tip)}" tabindex="0"',
        )

    for r in races:
        if r.get("tier", 3) != 1:
            svg.append(_point(r))
    for r in races:
        if r.get("tier", 3) == 1:
            svg.append(_point(r))

    # Callout labels for the monuments the chapters discuss
    by_slug = {r["slug"]: r for r in races}
    for slug, (label, dx, dy) in _SCATTER_CALLOUTS.items():
        r = by_slug.get(slug)
        if not r:
            continue
        density = r["elevation_m"] / r["distance_km"]
        x, y = _to_xy(r["distance_km"], density)
        anchor = "end" if dx < 0 else "start"
        svg.append(_svg_text(
            x + dx, y + dy, label,
            font_size=15, fill="var(--rl-color-near-black)",
            anchor=anchor, weight="700", family="var(--rl-font-editorial)"
        ))

    # Legend
    ly = chart_bot + 58
    lx = margin_l
    for tier, label in [(1, "Tier 1"), (2, "Tier 2"), (3, "Tier 3-4")]:
        size = 13 if tier == 1 else 9
        svg.append(_svg_rect(lx, ly - size / 2, size, size,
                             fill=_TIER_FILLS[tier]))
        svg.append(_svg_text(lx + size + 10, ly + 5, label,
                             font_size=14, fill="var(--rl-color-near-black)",
                             family="var(--rl-font-data)"))
        lx += 130
    svg.append(_svg_text(
        lx + 20, ly + 5,
        f"{len(races)} of {n_total} rated races (single-day, \u2264{_SCATTER_MAX_KM}km)",
        font_size=13, fill="var(--rl-color-steel)", family="var(--rl-font-data)"
    ))

    # Envelope boundary lines, one per rider type (CSS shows only the active one)
    for rid, (_label, max_km, max_dens) in _RIDER_ENVELOPES.items():
        if max_km is None:
            continue
        bx, by = _to_xy(max_km, max_dens)
        svg.append(_svg_path(
            f"M {margin_l},{by} L {bx},{by} L {bx},{chart_bot}",
            stroke="var(--rl-color-signal-red)", stroke_width=3,
            extra=f'stroke-dasharray="10 7" class="rl-ig-env-line" data-for="{rid}"',
        ))

    svg.append(_svg_close())

    # Per-rider summary strip (only the active rider's line is shown)
    strips = []
    for rid, (label, max_km, max_dens) in _RIDER_ENVELOPES.items():
        counts = {"in": 0, "st": 0, "out": 0}
        for r in races:
            counts[_classify_envelope(rid, r["distance_km"],
                                      r["elevation_m"] / r["distance_km"])] += 1
        if max_km is None:
            text = (f"{label}: all {counts['in']} races are inside your envelope. "
                    "Pick on ambition, not arithmetic.")
        else:
            text = (f"{label}: {counts['in']} races inside your envelope, "
                    f"{counts['st']} more within a focused-block stretch, "
                    f"{counts['out']} that want a different season.")
        strips.append(
            f'<div class="rl-ig-env-strip" data-for="{rid}">{_esc(text)}</div>'
        )
    strips_html = "".join(strips)
    hint = ('<div class="rl-ig-env-hint">Pick your rider type above and the map '
            'redraws around your hours \u2014 the dashed line is your envelope.</div>')

    inner = (
        f'<div data-interactive="envelope" data-rider="">'
        f'{"".join(svg)}{hint}{strips_html}</div>'
    )
    return _figure_wrap(
        inner, block.get("caption", ""), block.get("layout", "full-width"),
        block.get("asset_id", ""), block.get("alt", ""),
        title="Every Rated Race: Distance vs Climbing Density",
        takeaway=(
            "Height decides the training, not width. The Maratona is 100km "
            "shorter than Flanders and three times harder per kilometre."
        ),
    )


def render_tier_distribution(block: dict) -> str:
    """Horizontal bar chart of races per tier, computed live from the index.

    This is the graphic behind the chapter's scarcity claim: the count and
    percentage are derived at build time, so they can never drift from the
    database the way hardcoded prose can.
    """
    idx = _load_race_index()
    counts = {t: 0 for t in (1, 2, 3, 4)}
    for r in idx:
        counts[r.get("tier", 3)] = counts.get(r.get("tier", 3), 0) + 1
    total = len(idx)
    t1_pct = counts[1] / total * 100

    tier_meta = [
        (1, "Tier 1 \u00b7 Monuments", "var(--rl-color-near-black)"),
        (2, "Tier 2 \u00b7 Contenders", "var(--rl-color-steel)"),
        (3, "Tier 3 \u00b7 Regional", "var(--rl-color-silver)"),
        (4, "Tier 4 \u00b7 Local", "var(--rl-color-silver)"),
    ]

    vb_w = 1400
    label_w = 300
    bar_max_w = 900
    bar_h = 64
    gap = 18
    top = 30
    vb_h = top + len(tier_meta) * (bar_h + gap) + 20
    max_count = max(counts.values())

    svg = [_svg_open(vb_w, vb_h, "rl-infographic-svg")]
    for i, (tier, label, fill) in enumerate(tier_meta):
        y = top + i * (bar_h + gap)
        count = counts[tier]
        w = max((count / max_count) * bar_max_w, 6)
        pct = count / total * 100
        svg.append(_svg_text(
            label_w - 16, y + bar_h / 2 + 6, label,
            font_size=17, fill="var(--rl-color-near-black)",
            anchor="end", weight="700", family="var(--rl-font-editorial)"
        ))
        svg.append(_svg_rect(
            label_w, y, w, bar_h, fill=fill,
            extra=f'data-tooltip="{_esc(f"{count} races \u00b7 {pct:.1f}% of {total}")}" tabindex="0"',
        ))
        count_label = f"{count} ({pct:.1f}%)"
        # Inside the bar if it fits, outside otherwise
        if w > 150:
            svg.append(_svg_text(
                label_w + w - 14, y + bar_h / 2 + 6, count_label,
                font_size=16, fill="var(--rl-color-cool-white)",
                anchor="end", weight="700", family="var(--rl-font-data)"
            ))
        else:
            svg.append(_svg_text(
                label_w + w + 14, y + bar_h / 2 + 6, count_label,
                font_size=16, fill="var(--rl-color-near-black)",
                weight="700", family="var(--rl-font-data)"
            ))

    svg.append(_svg_close())
    return _figure_wrap(
        "".join(svg), block.get("caption", ""), block.get("layout", "inline"),
        block.get("asset_id", ""), block.get("alt", ""),
        title=f"How the {total} Rated Races Break Down",
        takeaway=(
            f"Only {t1_pct:.1f}% of rated events earn Tier 1. If your target "
            "is one of them, the field, the speed, and the stakes all scale up."
        ),
    )


_MONTH_ORDER = ["January", "February", "March", "April", "May", "June",
                "July", "August", "September", "October", "November", "December"]


def render_race_calendar(block: dict) -> str:
    """Races per month, computed live from the index — the season's shape.

    The build-backwards argument drawn: if the season's spine is June, a
    16-week build means base training starts in February.
    """
    idx = _load_race_index()
    counts = {m: 0 for m in _MONTH_ORDER}
    for r in idx:
        m = r.get("month")
        if m in counts:
            counts[m] += 1
    peak_month = max(counts, key=lambda m: counts[m])
    max_count = max(counts.values()) or 1

    vb_w, vb_h = 1400, 560
    margin_l, margin_r, chart_top, chart_bot = 70, 40, 60, 440
    chart_w = vb_w - margin_l - margin_r
    chart_h = chart_bot - chart_top
    bar_gap = 14
    bar_w = (chart_w - bar_gap * 11) / 12

    svg = [_svg_open(vb_w, vb_h, "rl-infographic-svg")]

    # Baseline
    svg.append(_svg_line(margin_l, chart_bot, margin_l + chart_w, chart_bot,
                         stroke="var(--rl-color-near-black)", stroke_width=3))

    for i, m in enumerate(_MONTH_ORDER):
        c = counts[m]
        h = (c / max_count) * chart_h
        x = margin_l + i * (bar_w + bar_gap)
        y = chart_bot - h
        is_peak = m == peak_month
        fill = "var(--rl-color-near-black)" if is_peak else "var(--rl-color-steel)"
        svg.append(_svg_rect(
            x, y, bar_w, max(h, 3), fill=fill,
            extra=(f'data-animate="bar" data-target-height="{max(h, 3):.0f}"'
                   f' data-tooltip="{_esc(f"{m}: {c} rated races")}" tabindex="0"'),
        ))
        svg.append(_svg_text(x + bar_w / 2, y - 10, str(c),
                             font_size=15, fill="var(--rl-color-near-black)",
                             anchor="middle", weight="700",
                             family="var(--rl-font-data)"))
        svg.append(_svg_text(x + bar_w / 2, chart_bot + 26, m[:3].upper(),
                             font_size=13, fill="var(--rl-color-secondary-blue)",
                             anchor="middle", family="var(--rl-font-data)",
                             extra='letter-spacing="1"'))

    # Build-backwards bracket: 16 weeks before the peak month (~4 months)
    peak_i = _MONTH_ORDER.index(peak_month)
    base_i = (peak_i - 4) % 12
    bx1 = margin_l + base_i * (bar_w + bar_gap)
    bx2 = margin_l + peak_i * (bar_w + bar_gap) + bar_w
    by = chart_bot + 56
    svg.append(_svg_line(bx1, by, bx2, by,
                         stroke="var(--rl-color-signal-red)", stroke_width=3))
    svg.append(_svg_line(bx1, by - 8, bx1, by + 8,
                         stroke="var(--rl-color-signal-red)", stroke_width=3))
    svg.append(_svg_line(bx2, by - 8, bx2, by + 8,
                         stroke="var(--rl-color-signal-red)", stroke_width=3))
    svg.append(_svg_text(
        (bx1 + bx2) / 2, by + 30,
        f"a 16-week build for a {peak_month} target starts back here",
        font_size=15, fill="var(--rl-color-signal-red)",
        anchor="middle", weight="700", family="var(--rl-font-editorial)"))

    svg.append(_svg_close())
    return _figure_wrap(
        "".join(svg), block.get("caption", ""), block.get("layout", "inline"),
        block.get("asset_id", ""), block.get("alt", ""),
        title="When the Season Actually Happens",
        takeaway=(
            f"{peak_month} is the spine of the calendar "
            f"({counts[peak_month]} rated races). Your target's date sets your "
            "build backwards \u2014 the start line is months before the start line."
        ),
    )


def render_polarized_guess(block: dict) -> str:
    """Guess-before-reveal: what share of elite endurance training is easy?

    Belief elicitation (the NYT 'You Draw It' pattern, button-sized): making
    the reader commit to a guess before the reveal measurably improves recall
    (Kim, Reinecke & Hullman 2017). Without JS the answer is simply visible.
    """
    options = [
        ("50", "About half"),
        ("65", "Around two-thirds"),
        ("80", "Around 80%"),
    ]
    btns = "".join(
        f'<button type="button" class="rl-ig-guess-btn" data-guess="{v}"'
        f' data-correct="{"1" if v == "80" else "0"}">{_esc(label)}<span'
        f' class="rl-ig-guess-pct">{v}%</span></button>'
        for v, label in options
    )

    # Reveal panel: 80/20 bar + explanation
    bar = (
        '<div class="rl-ig-guess-bar" role="img"'
        ' aria-label="Bar showing roughly 80% of elite training time is easy'
        ' and 20% is hard">'
        '<div class="rl-ig-guess-bar-easy" style="width:80%">~80% EASY</div>'
        '<div class="rl-ig-guess-bar-hard" style="width:20%">~20%</div>'
        '</div>'
    )
    reveal = (
        f'<div class="rl-ig-guess-reveal">'
        f'<div class="rl-ig-guess-verdict" data-when="right">Correct \u2014 and most people guess low.</div>'
        f'<div class="rl-ig-guess-verdict" data-when="wrong">Most people guess low. The real number surprises almost everyone.</div>'
        f'{bar}'
        f'<p class="rl-ig-guess-explain">Across elite endurance sport, roughly 80% of '
        f'training time sits at conversational intensity and only ~20% is genuinely hard '
        f'(Seiler\u2019s intensity-distribution analyses). The time-crunched rider\u2019s '
        f'instinct \u2014 make every short session hard \u2014 drifts in exactly the wrong '
        f'direction: the easy hours are what the hard days are built on.</p>'
        f'</div>'
    )

    inner = (
        f'<div data-interactive="guess-reveal">'
        f'<div class="rl-ig-guess-question">Elite endurance athletes \u2014 the people '
        f'with the most time to train hard \u2014 spend what share of their training '
        f'time going <em>easy</em>?</div>'
        f'<div class="rl-ig-guess-options">{btns}</div>'
        f'{reveal}'
        f'</div>'
    )
    return _figure_wrap(
        inner, block.get("caption", ""), block.get("layout", "inline"),
        block.get("asset_id", ""), block.get("alt", ""),
        title="Commit to a Guess First",
        takeaway="If you guessed low, your training probably runs too hard on easy days \u2014 the most common self-coached error in the book.",
    )


# Phase → weekly hours by intensity bucket. Two builds on one calendar:
# the fondo grows the stack, the crit re-colors it.
_PHASE_LABELS = ["BASE\nwk 1-6", "BUILD\nwk 7-12", "SHARPEN\nwk 13-15", "RACE\nwk 16+"]
_PHASE_MIX = {
    "fondo": {
        "label": "Fondo / century build \u2014 the stack grows",
        "endurance": [7.0, 7.5, 8.5, 4.0],
        "tempo": [1.0, 2.0, 2.5, 1.0],
        "vo2": [0.0, 0.5, 0.75, 0.5],
        "anaerobic": [0.0, 0.0, 0.25, 0.0],
    },
    "crit": {
        "label": "Crit / TT build \u2014 the stack re-colors",
        "endurance": [3.5, 2.75, 2.5, 3.0],
        "tempo": [1.0, 1.0, 0.5, 0.0],
        "vo2": [0.0, 1.0, 0.75, 0.5],
        "anaerobic": [0.5, 0.25, 1.25, 1.5],
    },
}
# Zone-semantic fills: each bucket wears its training-zone color, cool to
# hot, so the stack "re-colors" claim in the crit view is literally visible.
_MIX_BUCKETS = [
    ("endurance", "Endurance (Z1-2)", "var(--rl-zone-2)"),
    ("tempo", "Tempo / Threshold (Z3-4)", "var(--rl-zone-4)"),
    ("vo2", "VO2max (Z5)", "var(--rl-zone-5)"),
    ("anaerobic", "Anaerobic / sprint (Z6+)", "var(--rl-zone-6)"),
]


def render_phase_shift(block: dict) -> str:
    """The same 16 weeks, two different shapes: fondo vs crit intensity mix.

    Toggleable stacked bars; the default view follows the reader's persona
    from the pillar quiz (crit-racer/tester \u2192 crit view), so most readers
    land on their own build without touching anything.
    """
    vb_w, vb_h = 1400, 620
    margin_l, chart_top, chart_bot = 90, 60, 480
    chart_w = vb_w - margin_l - 60
    chart_h = chart_bot - chart_top
    max_hours = 12.0
    n = len(_PHASE_LABELS)
    bar_w = 150
    slot_w = chart_w / n

    def bars_for(view: str) -> str:
        mix = _PHASE_MIX[view]
        parts = [f'<g class="rl-ig-view rl-ig-view-{view}">']
        for i in range(n):
            x = margin_l + i * slot_w + (slot_w - bar_w) / 2
            y = chart_bot
            total = 0.0
            for key, _label, fill in _MIX_BUCKETS:
                v = mix[key][i]
                total += v
                if v <= 0:
                    continue
                h = (v / max_hours) * chart_h
                y -= h
                parts.append(_svg_rect(
                    x, y, bar_w, h - 2, fill=fill,
                    extra=f'data-tooltip="{_esc(f"{_label}: {v:g}h/wk")}" tabindex="0"',
                ))
            parts.append(_svg_text(
                x + bar_w / 2, y - 12, f"{total:g}h",
                font_size=17, fill="var(--rl-color-near-black)",
                anchor="middle", weight="700", family="var(--rl-font-data)"))
        parts.append(_svg_text(
            margin_l + chart_w, chart_top - 26, mix["label"],
            font_size=17, fill="var(--rl-color-near-black)",
            anchor="end", weight="700", family="var(--rl-font-editorial)"))
        parts.append("</g>")
        return "".join(parts)

    svg = [_svg_open(vb_w, vb_h, "rl-infographic-svg")]
    svg.append(_svg_line(margin_l, chart_bot, margin_l + chart_w, chart_bot,
                         stroke="var(--rl-color-near-black)", stroke_width=3))
    for h in (4, 8, 12):
        y = chart_bot - (h / max_hours) * chart_h
        svg.append(_svg_line(margin_l, y, margin_l + chart_w, y,
                             stroke="var(--rl-color-light-steel)", stroke_width=1,
                             extra='stroke-dasharray="4 6"'))
        svg.append(_svg_text(margin_l - 12, y + 5, f"{h}h",
                             font_size=13, fill="var(--rl-color-secondary-blue)",
                             anchor="end", family="var(--rl-font-data)"))
    for i, label in enumerate(_PHASE_LABELS):
        x = margin_l + i * slot_w + slot_w / 2
        for j, line in enumerate(label.split("\n")):
            svg.append(_svg_text(x, chart_bot + 28 + j * 20, line,
                                 font_size=14 if j == 0 else 12,
                                 fill="var(--rl-color-near-black)" if j == 0
                                 else "var(--rl-color-secondary-blue)",
                                 anchor="middle", weight="700" if j == 0 else "",
                                 family="var(--rl-font-data)",
                                 extra='letter-spacing="2"' if j == 0 else ""))
    svg.append(bars_for("fondo"))
    svg.append(bars_for("crit"))

    # Legend
    lx = margin_l
    ly = chart_bot + 84
    for _key, label, fill in _MIX_BUCKETS:
        svg.append(_svg_rect(lx, ly, 20, 20, fill=fill))
        svg.append(_svg_text(lx + 28, ly + 15, label, font_size=13,
                             fill="var(--rl-color-near-black)",
                             family="var(--rl-font-data)"))
        lx += 28 + len(label) * 8 + 48
    svg.append(_svg_close())

    toggle = (
        '<div class="rl-ig-view-toggle" role="group" aria-label="Choose which build to show">'
        '<button type="button" class="rl-ig-view-btn" data-view="fondo" aria-pressed="true">FONDO BUILD</button>'
        '<button type="button" class="rl-ig-view-btn" data-view="crit" aria-pressed="false">CRIT / TT BUILD</button>'
        '</div>'
    )
    inner = (
        f'<div data-interactive="view-toggle" data-view="fondo" '
        f'data-persona-views="crit-racer:crit,tester:crit">'
        f'{toggle}{"".join(svg)}</div>'
    )
    return _figure_wrap(
        inner, block.get("caption", ""), block.get("layout", "inline"),
        block.get("asset_id", ""), block.get("alt", ""),
        title="The Same 16 Weeks, Two Different Shapes",
        takeaway="The fondo build buys durability by growing the stack. The crit build keeps the stack flat and changes what it's made of.",
    )


def render_interval_anatomy(block: dict) -> str:
    """Anatomy of a VO2max session: 4\u00d74 power trace, annotated.

    The chapter 4 execution rules drawn onto one workout: settle into the
    rep instead of sprinting it, keep the float honest, and finish rep four
    at the same power as rep one.
    """
    vb_w, vb_h = 1400, 640
    margin_l, chart_top, chart_bot = 90, 70, 500
    chart_w = vb_w - margin_l - 50
    chart_h = chart_bot - chart_top
    max_pct = 140.0  # y axis: % of FTP

    # (minutes, %FTP) trace: warmup, 4x(4min @ ~115% + 3min float @ ~50%), cooldown
    trace = [(0, 40), (6, 55), (10, 62), (12, 62)]
    t = 12.0
    for rep in range(4):
        spike = 121 if rep == 0 else 118  # slight first-rep overshoot, then settled
        trace += [(t + 0.3, spike), (t + 1.0, 115), (t + 4.0, 114)]
        t += 4.0
        if rep < 3:
            trace += [(t + 0.4, 52), (t + 3.0, 55)]
            t += 3.0
    trace += [(t + 1, 55), (t + 8, 45)]
    total_min = trace[-1][0]

    def xy(minute, pct):
        return (margin_l + minute / total_min * chart_w,
                chart_bot - pct / max_pct * chart_h)

    svg = [_svg_open(vb_w, vb_h, "rl-infographic-svg")]

    # Zone bands: VO2 target band 110-120%, threshold line at 100%
    band_top = chart_bot - 120 / max_pct * chart_h
    band_bot = chart_bot - 110 / max_pct * chart_h
    svg.append(_svg_rect(margin_l, band_top, chart_w, band_bot - band_top,
                         fill="var(--rl-color-silver)", extra='opacity="0.55"'))
    svg.append(_svg_text(margin_l + chart_w - 8, band_top - 8,
                         "TARGET: 110-120% FTP",
                         font_size=13, fill="var(--rl-color-secondary-blue)",
                         anchor="end", weight="700", family="var(--rl-font-data)",
                         extra='letter-spacing="2"'))
    ftp_y = chart_bot - 100 / max_pct * chart_h
    svg.append(_svg_line(margin_l, ftp_y, margin_l + chart_w, ftp_y,
                         stroke="var(--rl-color-steel)", stroke_width=2,
                         extra='stroke-dasharray="8 6"'))
    svg.append(_svg_text(margin_l - 12, ftp_y + 5, "FTP",
                         font_size=13, fill="var(--rl-color-steel)",
                         anchor="end", weight="700", family="var(--rl-font-data)"))

    # Axes
    svg.append(_svg_line(margin_l, chart_bot, margin_l + chart_w, chart_bot,
                         stroke="var(--rl-color-near-black)", stroke_width=3))
    for m in range(0, int(total_min) + 1, 10):
        x, _ = xy(m, 0)
        svg.append(_svg_text(x, chart_bot + 26, f"{m} min",
                             font_size=12, fill="var(--rl-color-secondary-blue)",
                             anchor="middle", family="var(--rl-font-data)"))

    # Power trace
    pts = [xy(m, p) for m, p in trace]
    svg.append(_svg_path(_cubic_bezier_path(pts),
                         stroke="var(--rl-color-near-black)", stroke_width=4,
                         extra='stroke-linecap="square" data-animate="line" class="rl-line-chart__path"'))

    # Annotations
    ax, ay = xy(12.9, 121)
    svg.append(_svg_line(ax, ay - 8, ax + 30, ay - 60, stroke="var(--rl-color-signal-red)", stroke_width=2))
    svg.append(_svg_text(ax + 36, ay - 66, "Don't sprint the start \u2014 settle into the band in ~30 seconds",
                         font_size=15, fill="var(--rl-color-signal-red)",
                         weight="700", family="var(--rl-font-editorial)"))
    fx, fy = xy(17.5, 52)
    svg.append(_svg_line(fx, fy + 8, fx + 20, fy + 60, stroke="var(--rl-color-secondary-blue)", stroke_width=2))
    svg.append(_svg_text(fx + 26, fy + 76, "The float: easy spinning, not freewheeling \u2014 recovery is part of the workout",
                         font_size=15, fill="var(--rl-color-secondary-blue)",
                         weight="700", family="var(--rl-font-editorial)"))
    lx4, ly4 = xy(33, 114)
    svg.append(_svg_line(lx4, ly4 - 8, lx4 - 10, ly4 - 66, stroke="var(--rl-color-near-black)", stroke_width=2))
    svg.append(_svg_text(lx4 - 6, ly4 - 74, "Rep 4 at the same power as rep 1 = executed, not survived",
                         font_size=15, fill="var(--rl-color-near-black)",
                         anchor="end", weight="700", family="var(--rl-font-editorial)"))

    svg.append(_svg_close())
    return _figure_wrap(
        "".join(svg), block.get("caption", ""), block.get("layout", "inline"),
        block.get("asset_id", ""), block.get("alt", ""),
        title="Anatomy of a VO2max Session (4\u00d74)",
        takeaway="If you can't hold the band by rep three, the fix is starting easier \u2014 not digging deeper.",
    )


def render_draft_savings(block: dict) -> str:
    """Aerodynamic cost by pack position, as % of riding solo.

    Numbers from Blocken et al. 2018 (J. Wind Eng. Ind. Aerodyn.): CFD +
    wind-tunnel study of a 121-rider peloton. The mid-pack figure is the
    single most surprising number in cycling.
    """
    positions = [
        ("Riding solo", 100, "Full wind bill \u2014 the reference"),
        ("Second wheel", 60, "One wheel of shelter cuts the bill ~40%"),
        ("Third wheel, single file", 52, "Deeper in the line, deeper discount"),
        ("Fourth wheel, single file", 46, "The discount keeps compounding"),
        ("Belly of the peloton", 8, "5-10% of solo drag \u2014 nearly towed"),
    ]
    vb_w = 1400
    label_w = 340
    bar_max_w = 860
    bar_h = 66
    gap = 20
    top = 40
    vb_h = top + len(positions) * (bar_h + gap) + 30

    svg = [_svg_open(vb_w, vb_h, "rl-infographic-svg")]
    for i, (label, pct, note) in enumerate(positions):
        y = top + i * (bar_h + gap)
        w = pct / 100 * bar_max_w
        is_hero = pct < 20
        fill = "var(--rl-color-signal-red)" if is_hero else (
            "var(--rl-color-near-black)" if pct == 100 else "var(--rl-color-steel)")
        svg.append(_svg_text(label_w - 16, y + 26, label,
                             font_size=17, fill="var(--rl-color-near-black)",
                             anchor="end", weight="700",
                             family="var(--rl-font-editorial)"))
        svg.append(_svg_text(label_w - 16, y + 48, note,
                             font_size=12, fill="var(--rl-color-secondary-blue)",
                             anchor="end", family="var(--rl-font-data)"))
        svg.append(_svg_rect(
            label_w, y, max(w, 8), bar_h, fill=fill,
            extra=(f'data-animate="bar" data-target-width="{max(w, 8):.0f}"'
                   f' data-tooltip="{_esc(f"{label}: ~{pct}% of solo aerodynamic drag")}"'
                   f' tabindex="0"'),
        ))
        pct_label = f"~{pct}%" if pct < 100 else "100%"
        if w > 120:
            svg.append(_svg_text(label_w + w - 14, y + bar_h / 2 + 6, pct_label,
                                 font_size=18, fill="var(--rl-color-cool-white)",
                                 anchor="end", weight="700",
                                 family="var(--rl-font-data)"))
        else:
            svg.append(_svg_text(label_w + max(w, 8) + 14, y + bar_h / 2 + 6, pct_label,
                                 font_size=18, fill="var(--rl-color-signal-red)",
                                 weight="700", family="var(--rl-font-data)"))
    svg.append(_svg_close())
    return _figure_wrap(
        "".join(svg), block.get("caption", ""), block.get("layout", "inline"),
        block.get("asset_id", ""), block.get("alt", ""),
        title="What Position Is Worth (Aerodynamic Drag vs Solo)",
        takeaway="Position is the most powerful equipment you own. No wheel, frame, or skinsuit buys you 90% \u2014 the middle of the pack does.",
    )


def render_taper_curve(block: dict) -> str:
    """The taper, drawn: fitness barely falls, fatigue collapses, form pops.

    A standard impulse-response (CTL/ATL/TSB) picture of the final three
    weeks. The numbers restate chapter 7's argument: you trade 1-2% of
    fitness for a 30-40% fatigue discount.
    """
    vb_w, vb_h = 1400, 620
    margin_l, chart_top, chart_bot = 90, 60, 480
    chart_w = vb_w - margin_l - 60
    chart_h = chart_bot - chart_top

    # Day -21 .. 0 (race day). Values in arbitrary "training load" units,
    # matched to the labeled claims: fitness -1.6%, fatigue -35%.
    days = list(range(-21, 1))
    fitness = [100 - (21 + d) * 0.075 for d in days]          # 98.4 by race day
    fatigue = [100 - 35 * ((21 + d) / 21) ** 2 for d in days]  # eases to 65
    form = [fit - fat for fit, fat in zip(fitness, fatigue)]

    y_min, y_max = 30, 110

    def xy(d, v):
        x = margin_l + (d + 21) / 21 * chart_w
        y = chart_bot - (v - y_min) / (y_max - y_min) * chart_h
        return x, y

    svg = [_svg_open(vb_w, vb_h, "rl-infographic-svg")]
    svg.append(_svg_line(margin_l, chart_bot, margin_l + chart_w, chart_bot,
                         stroke="var(--rl-color-near-black)", stroke_width=3))
    for d in (-21, -14, -7, 0):
        x, _ = xy(d, y_min)
        label = "RACE DAY" if d == 0 else f"{-d} days out"
        svg.append(_svg_text(x, chart_bot + 26, label,
                             font_size=13,
                             fill="var(--rl-color-signal-red)" if d == 0
                             else "var(--rl-color-secondary-blue)",
                             anchor="middle" if d != 0 else "end",
                             weight="700" if d == 0 else "",
                             family="var(--rl-font-data)"))
        if d != -21:
            svg.append(_svg_line(x, chart_top, x, chart_bot,
                                 stroke="var(--rl-color-silver)", stroke_width=1,
                                 extra='stroke-dasharray="4 6"'))

    fit_pts = [xy(d, v) for d, v in zip(days, fitness)]
    fat_pts = [xy(d, v) for d, v in zip(days, fatigue)]
    # Form plotted with its own visual offset/scale so all three read clearly
    # (it ends between the fatigue floor and the fitness ceiling):
    form_scaled = [40 + f * 0.85 for f in form]
    frm_pts = [xy(d, v) for d, v in zip(days, form_scaled)]

    svg.append(_svg_path(_cubic_bezier_path(fit_pts),
                         stroke="var(--rl-color-near-black)", stroke_width=4))
    svg.append(_svg_path(_cubic_bezier_path(fat_pts),
                         stroke="var(--rl-color-steel)", stroke_width=4,
                         extra='stroke-dasharray="12 8"'))
    svg.append(_svg_path(_cubic_bezier_path(frm_pts),
                         stroke="var(--rl-color-signal-red)", stroke_width=4))

    svg.append(_svg_text(*xy(-19, 104), "FITNESS \u2014 barely moves (-1 to -2%)",
                         font_size=15, fill="var(--rl-color-near-black)",
                         weight="700", family="var(--rl-font-editorial)"))
    svg.append(_svg_text(*xy(-10.2, 88), "FATIGUE \u2014 collapses (-30 to -40%)",
                         font_size=15, fill="var(--rl-color-steel)",
                         weight="700", family="var(--rl-font-editorial)"))
    fx, fy = xy(-3, form_scaled[18])
    svg.append(_svg_text(fx, fy + 40, "FORM \u2014 what's left when the fatigue leaves",
                         font_size=15, fill="var(--rl-color-signal-red)",
                         anchor="end", weight="700",
                         family="var(--rl-font-editorial)"))

    svg.append(_svg_close())
    return _figure_wrap(
        "".join(svg), block.get("caption", ""), block.get("layout", "inline"),
        block.get("asset_id", ""), block.get("alt", ""),
        title="The Taper Is a Trade, and It's a Steal",
        takeaway="You cannot gain fitness in the last two weeks. You can only show up owning less fatigue \u2014 that's the entire transaction.",
    )


def render_season_arc(block: dict) -> str:
    """A whole season's form curve: builds, peaks, and the load-bearing dip."""
    vb_w, vb_h = 1400, 560
    margin_l, chart_top, chart_bot = 80, 70, 430
    chart_w = vb_w - margin_l - 50
    chart_h = chart_bot - chart_top

    # Month-by-month "form" curve (0-100): winter base, spring build,
    # summer peaks, autumn wind-down, deliberate off-season dip.
    curve = [(0, 38), (1, 42), (2, 50), (3, 58), (4, 66), (5, 80),
             (5.6, 74), (6.4, 86), (7.2, 78), (8, 88), (9, 62),
             (10, 42), (11, 30), (12, 36)]

    def xy(month, v):
        return (margin_l + month / 12 * chart_w,
                chart_bot - v / 100 * chart_h)

    svg = [_svg_open(vb_w, vb_h, "rl-infographic-svg")]
    svg.append(_svg_line(margin_l, chart_bot, margin_l + chart_w, chart_bot,
                         stroke="var(--rl-color-near-black)", stroke_width=3))
    for i, m in enumerate(["JAN", "MAR", "MAY", "JUL", "SEP", "NOV"]):
        x, _ = xy(i * 2, 0)
        svg.append(_svg_text(x, chart_bot + 26, m, font_size=13,
                             fill="var(--rl-color-secondary-blue)",
                             anchor="middle", family="var(--rl-font-data)",
                             extra='letter-spacing="2"'))

    pts = [xy(m, v) for m, v in curve]
    svg.append(_svg_path(_cubic_bezier_path(pts),
                         stroke="var(--rl-color-near-black)", stroke_width=4,
                         extra='data-animate="line" class="rl-line-chart__path"'))

    # Race markers at the two summer peaks + one spring opener
    for month, v, label in [(4, 66, "opener"), (6.4, 86, "A-race #1"), (8, 88, "A-race #2")]:
        x, y = xy(month, v)
        svg.append(_svg_rect(x - 7, y - 7, 14, 14,
                             fill="var(--rl-color-signal-red)",
                             extra=f'data-tooltip="{_esc(label)}" tabindex="0"'))
        svg.append(_svg_text(x, y - 18, label.upper(), font_size=12,
                             fill="var(--rl-color-signal-red)", anchor="middle",
                             weight="700", family="var(--rl-font-data)"))

    # The off-season dip annotation
    dx, dy = xy(11, 30)
    svg.append(_svg_line(dx, dy + 10, dx - 30, dy + 70,
                         stroke="var(--rl-color-secondary-blue)", stroke_width=2))
    svg.append(_svg_text(dx - 36, dy + 88,
                         "The dip is load-bearing \u2014 riders who skip it start next season pre-fatigued",
                         font_size=15, fill="var(--rl-color-secondary-blue)",
                         anchor="end", weight="700", family="var(--rl-font-editorial)"))

    svg.append(_svg_close())
    return _figure_wrap(
        "".join(svg), block.get("caption", ""), block.get("layout", "inline"),
        block.get("asset_id", ""), block.get("alt", ""),
        title="A Season Is a Shape, Not a Straight Line",
        takeaway="Two real peaks a year is what a body gives you. The valley after the last one isn't lost fitness \u2014 it's next year's down payment.",
    )


def _bike_glyph(x: float, y: float, color: str, filled: bool) -> str:
    """Small engraved bicycle pictogram (Isotype unit = one training hour)."""
    wheel_fill = color if filled else "none"
    return (
        f'<g transform="translate({x:.0f},{y:.0f})">'
        f'<circle cx="9" cy="20" r="8" fill="{wheel_fill}" stroke="{color}" stroke-width="1.6"></circle>'
        f'<circle cx="37" cy="20" r="8" fill="{wheel_fill}" stroke="{color}" stroke-width="1.6"></circle>'
        f'<path d="M9 20 L19 6 L31 6 L37 20 M19 6 L17 20 M31 6 L25 20 M17 20 L25 20" '
        f'fill="none" stroke="{color}" stroke-width="1.6" stroke-linejoin="round"></path>'
        f'<line x1="17.5" y1="3" x2="22" y2="3" stroke="{color}" stroke-width="1.6"></line>'
        f'<line x1="30" y1="3" x2="34" y2="6" stroke="{color}" stroke-width="1.6"></line>'
        f'</g>'
    )


def render_week_isotype(block: dict) -> str:
    """Isotype figure: eight weekly training hours as bicycle pictograms.

    Period plate treatment \u2014 cream paper, engraved frame, one bike per
    hour, spot ink on the two hard hours. After Neurath, after Seiler.
    """
    ink = "var(--rl-plate-ink,#1b1712)"
    accent = "var(--rl-garnish,#a8781f)"
    accent_deep = "var(--rl-garnish-deep,#7d5a17)"
    vb_w, vb_h = 1120, 400

    svg = [
        f'<svg viewBox="0 0 {vb_w} {vb_h}" class="rl-infographic-svg rl-infographic-svg--plate" '
        f'xmlns="http://www.w3.org/2000/svg" role="presentation" focusable="false">',
        f'<rect x="0" y="0" width="{vb_w}" height="{vb_h}" fill="var(--rl-plate-paper,#f4eed9)"></rect>',
        f'<rect x="12" y="12" width="{vb_w - 24}" height="{vb_h - 24}" fill="none" stroke="{ink}" stroke-width="1.2"></rect>',
        f'<rect x="19" y="19" width="{vb_w - 38}" height="{vb_h - 38}" fill="none" stroke="{ink}" stroke-width="0.5" opacity="0.7"></rect>',
        f'<text x="56" y="82" font-family="var(--rl-font-editorial)" font-size="30" font-weight="700" '
        f'letter-spacing="6" fill="{ink}">YOUR EIGHT TRAINING HOURS</text>',
        f'<line x1="56" y1="100" x2="{vb_w - 56}" y2="100" stroke="{ink}" stroke-width="1"></line>',
        f'<text x="56" y="152" font-family="var(--rl-font-data)" font-size="17" '
        f'letter-spacing="4" fill="{ink}" opacity="0.85">RIDDEN EASY \u2014 CONVERSATIONAL</text>',
    ]
    for i in range(6):
        svg.append(_bike_glyph(56 + i * 116, 168, ink, filled=False))
    svg.append(
        f'<text x="56" y="282" font-family="var(--rl-font-data)" font-size="17" '
        f'letter-spacing="4" fill="{accent_deep}">RIDDEN HARD \u2014 ON PURPOSE</text>'
    )
    for i in range(2):
        svg.append(_bike_glyph(56 + i * 116, 298, accent, filled=True))
    svg.append(
        f'<text x="{vb_w - 56}" y="{vb_h - 34}" text-anchor="end" font-family="var(--rl-font-data)" '
        f'font-size="14" letter-spacing="3" fill="{ink}" opacity="0.7">'
        f'CHAQUE SYMBOLE = 1 HEURE PAR SEMAINE \u00b7 APR\u00c8S SEILER</text>'
    )
    svg.append("</svg>")
    return _figure_wrap(
        "".join(svg), block.get("caption", ""), block.get("layout", "inline"),
        block.get("asset_id", ""), block.get("alt", ""),
        title="Fig. \u2014 The Week, Counted",
        takeaway="Six of your eight hours should be rides you could narrate. The two hard ones carry the adaptation \u2014 and only if the six stay honest.",
    )


# ── Registry ─────────────────────────────────────────────────

INFOGRAPHIC_RENDERERS = {
    "ch1-event-demand-matrix": render_event_demand_matrix,
    "ch2-build-curves": render_build_curves,
    "ch2-race-scatter": render_race_scatter,
    "ch2-race-calendar": render_race_calendar,
    "ch2-tier-distribution": render_tier_distribution,
    "ch3-supercompensation": render_supercompensation,
    "ch3-polarized-guess": render_polarized_guess,
    "ch3-week-isotype": render_week_isotype,
    "ch3-phase-shift": render_phase_shift,
    "ch4-traffic-light": render_traffic_light,
    "ch4-interval-anatomy": render_interval_anatomy,
    "ch5-fueling-timeline": render_fueling_timeline,
    "ch6-echelon-diagram": render_echelon_diagram,
    "ch6-draft-savings": render_draft_savings,
    "ch7-taper-curve": render_taper_curve,
    "ch8-season-arc": render_season_arc,
}
