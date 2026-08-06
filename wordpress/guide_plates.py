#!/usr/bin/env python3
"""Inline SVG survey plates for guide chapter heroes."""

from __future__ import annotations

import html
import json
import math
from collections import Counter
from pathlib import Path
from typing import Any


RACE_INDEX_PATH = Path(__file__).parent.parent / "web" / "race-index.json"


def _esc(value: Any) -> str:
    return html.escape(str(value), quote=True)


def _race_rows(data: dict | None) -> list[dict]:
    races = (data or {}).get("race_index")
    if isinstance(races, dict):
        return list(races.values())
    if isinstance(races, list):
        return races
    try:
        loaded = json.loads(RACE_INDEX_PATH.read_text(encoding="utf-8"))
    except OSError:
        return []
    return loaded if isinstance(loaded, list) else []


def _tier_distribution(data: dict | None) -> tuple[int, dict[int, int]]:
    rows = _race_rows(data)
    counts = Counter()
    for race in rows:
        try:
            tier = int(race.get("tier"))
        except (TypeError, ValueError):
            continue
        if 1 <= tier <= 4:
            counts[tier] += 1
    return len(rows), {tier: counts.get(tier, 0) for tier in range(1, 5)}


def _tier_bars(data: dict | None) -> str:
    total, counts = _tier_distribution(data)
    max_count = max(counts.values()) if counts else 1
    label = f"{total} RACES, RANKED"
    rows = [f'<text class="rl-plate-label rl-plate-label-strong" x="610" y="148">{_esc(label)}</text>']
    y = 184
    for tier in range(1, 5):
        count = counts[tier]
        width = 260 * (count / max_count) if max_count else 0
        rows.append(
            f'<text class="rl-plate-label" x="610" y="{y + 7}">T{tier}</text>'
            f'<rect class="rl-plate-bar-track" x="652" y="{y - 8}" width="276" height="16"></rect>'
            f'<rect class="rl-plate-bar-fill rl-plate-tier-{tier}" x="652" y="{y - 8}" width="{width:.1f}" height="16"></rect>'
            f'<text class="rl-plate-label" x="946" y="{y + 7}">{count}</text>'
        )
        y += 38
    return "\n".join(rows)


def _motif(chapter_number: int, data: dict | None) -> str:
    motifs = {
        1: (
            f'<path class="rl-plate-line rl-plate-line-soft" d="{_ridge_path(584, 934, 300, 30, 1.3, 0.3)}"></path>\n'
            f'<path class="rl-plate-line" d="{_ridge_path(604, 962, 344, 26, 1.1, 2.1)}"></path>\n'
            f'<path class="rl-plate-line rl-plate-line-soft" d="{_ridge_path(628, 906, 402, 16, 0.9, 4.2)}"></path>\n'
        ),
        2: _tier_bars(data),
        3: '''
<line class="rl-plate-line" x1="610" y1="300" x2="950" y2="300"></line>
<rect class="rl-plate-zone rl-plate-zone-1" x="610" y="264" width="68" height="72"></rect>
<rect class="rl-plate-zone rl-plate-zone-2" x="678" y="264" width="68" height="72"></rect>
<rect class="rl-plate-zone rl-plate-zone-3" x="746" y="264" width="68" height="72"></rect>
<rect class="rl-plate-zone rl-plate-zone-4" x="814" y="264" width="68" height="72"></rect>
<rect class="rl-plate-zone rl-plate-zone-5" x="882" y="264" width="68" height="72"></rect>
<text class="rl-plate-label" x="630" y="358">Z1</text><text class="rl-plate-label" x="698" y="358">Z2</text><text class="rl-plate-label" x="766" y="358">Z3</text><text class="rl-plate-label" x="834" y="358">Z4</text><text class="rl-plate-label" x="902" y="358">Z5</text>
''',
        4: (
            '<rect class="rl-plate-signal rl-plate-signal-red" x="628" y="252" width="84" height="84"></rect>\n'
            '<rect class="rl-plate-signal rl-plate-signal-gold" x="748" y="252" width="84" height="84"></rect>\n'
            '<rect class="rl-plate-signal rl-plate-signal-teal" x="868" y="252" width="84" height="84"></rect>\n'
            f"{_pixel_check(645, 276)}\n"
            f"{_pixel_check(765, 276)}\n"
            f"{_pixel_check(885, 276)}\n"
        ),
        5: '''
<line class="rl-plate-line" x1="610" y1="302" x2="952" y2="302"></line>
<line class="rl-plate-line" x1="650" y1="270" x2="650" y2="334"></line>
<line class="rl-plate-line" x1="780" y1="270" x2="780" y2="334"></line>
<line class="rl-plate-line" x1="910" y1="270" x2="910" y2="334"></line>
<text class="rl-plate-label rl-plate-label-strong" x="622" y="358">30g/hr</text>
<text class="rl-plate-label rl-plate-label-strong" x="752" y="358">60g/hr</text>
<text class="rl-plate-label rl-plate-label-strong" x="882" y="358">90g/hr</text>
''',
        6: (
            f'<path class="rl-plate-line" d="{_stepped_path([(610, 356), (660, 262), (710, 268), (760, 330), (816, 368), (880, 330), (944, 250)])}"></path>\n'
            '<rect class="rl-plate-dot" x="645" y="283" width="10" height="10"></rect>\n'
            '<rect class="rl-plate-dot" x="755" y="325" width="10" height="10"></rect>\n'
            '<rect class="rl-plate-dot" x="887" y="295" width="10" height="10"></rect>\n'
            '<text class="rl-plate-label" x="626" y="246">SURGE</text>\n'
            '<text class="rl-plate-label" x="730" y="392">SETTLE</text>\n'
            '<text class="rl-plate-label" x="850" y="256">SELECT</text>\n'
        ),
        7: '''
<line class="rl-plate-line" x1="612" y1="304" x2="952" y2="304"></line>
<line class="rl-plate-line" x1="632" y1="270" x2="632" y2="338"></line>
<line class="rl-plate-line" x1="732" y1="270" x2="732" y2="338"></line>
<line class="rl-plate-line" x1="832" y1="270" x2="832" y2="338"></line>
<line class="rl-plate-line" x1="932" y1="270" x2="932" y2="338"></line>
<text class="rl-plate-label" x="612" y="362">-7D</text><text class="rl-plate-label" x="712" y="362">-3D</text><text class="rl-plate-label" x="812" y="362">-1D</text><text class="rl-plate-label" x="912" y="362">RACE</text>
''',
        8: (
            f'<path class="rl-plate-line rl-plate-line-soft" d="{_stepped_path([(610, 294), (686, 296), (712, 412), (768, 396), (826, 268), (944, 244)])}"></path>\n'
            '<line class="rl-plate-line" x1="610" y1="338" x2="952" y2="338"></line>\n'
            '<rect class="rl-plate-dot" x="753" y="333" width="10" height="10"></rect>\n'
            '<rect class="rl-plate-dot" x="881" y="253" width="10" height="10"></rect>\n'
            '<text class="rl-plate-label" x="716" y="432">RECOVER</text>\n'
            '<text class="rl-plate-label" x="834" y="232">ADAPT</text>\n'
        ),
    }
    return motifs.get(chapter_number, motifs[1])


_ROMAN = {1: "I", 2: "II", 3: "III", 4: "IV", 5: "V", 6: "VI", 7: "VII", 8: "VIII"}

_PLATE_TITLES = {
    1: "LA COURSE SUR ROUTE",
    2: "CHOISIR SON OBJECTIF",
    3: "LES FONDATIONS",
    4: "LE PLAN DE 16 SEMAINES",
    5: "LE RAVITAILLEMENT",
    6: "L'ART DU PELOTON",
    7: "LA SEMAINE DE COURSE",
    8: "APRÈS LA LIGNE",
}


def _quant(v: float, q: float) -> float:
    return round(v / q) * q


def _stepped_path(pts: list[tuple[float, float]], step: float = 16.0, quant: float = 6.0) -> str:
    """Linear-interpolate keypoints, then quantize into a stepped pixel path.

    Vertical/horizontal moves only — the pixel-planche drawing rule.
    """
    def y_at(x: float) -> float:
        for i in range(1, len(pts)):
            x0, y0 = pts[i - 1]
            x1, y1 = pts[i]
            if x0 <= x <= x1:
                t = (x - x0) / (x1 - x0)
                return y0 + (y1 - y0) * t
        return pts[-1][1]

    x0, x1 = pts[0][0], pts[-1][0]
    d = ""
    y_prev: float | None = None
    x = x0
    while x < x1:
        seg_end = min(x + step, x1)
        y = _quant(y_at(x + step / 2), quant)
        if y_prev is None:
            d = f"M {x:.0f} {y:.0f}"
        elif y != y_prev:
            d += f" V {y:.0f}"
        d += f" H {seg_end:.0f}"
        y_prev = y
        x += step
    return d


def _ridge_path(x0: float, x1: float, base: float, amp: float,
                cycles: float, phase: float) -> str:
    """A stepped sine ridge — the pixel replacement for engraved curve motifs."""
    n = 24
    pts = [
        (x0 + (x1 - x0) * i / n,
         base + amp * math.sin((i / n) * cycles * math.tau + phase))
        for i in range(n + 1)
    ]
    return _stepped_path(pts)


_CHECK_CELLS = [(0, 2), (1, 3), (2, 4), (3, 3), (4, 2), (5, 1), (6, 0)]


def _pixel_check(x: float, y: float, cell: float = 7.0) -> str:
    """Chunky pixel checkmark, sprite-style."""
    rects = "".join(
        f'<rect x="{x + cx * cell:.0f}" y="{y + cy * cell:.0f}" width="{cell:.0f}" height="{cell:.0f}"></rect>'
        for cx, cy in _CHECK_CELLS
    )
    return f'<g class="rl-plate-check-px">{rects}</g>'


def _pixel_skyline(chapter_number: int) -> tuple[str, tuple[float, float]]:
    """Deterministic stage profile quantized to a step grid.

    Returns (stepped_path_d, (peak_x, peak_y)). Same elevation function as
    the engraved pass — only the rendering resolution changed.
    """
    base_y = 116.0
    step = 20.0
    quant = 6.0
    seed = chapter_number * 1.7

    def elev(x: float) -> float:
        t = (x - 20) / 960
        h = (
            22 * math.sin(t * 6.1 + seed)
            + 14 * math.sin(t * 13.7 + seed * 2.3)
            + 8 * math.sin(t * 23.9 + seed * 4.1)
        )
        return max(6.0, 32 + h)

    d = f"M 20 {base_y:.0f}"
    y_prev: float | None = None
    peak = (20.0, base_y)
    x = 20.0
    while x < 980:
        seg_end = min(x + step, 980)
        y = _quant(base_y - elev(x + step / 2), quant)
        if y_prev is None or y != y_prev:
            d += f" V {y:.0f}"
        d += f" H {seg_end:.0f}"
        if y < peak[1]:
            peak = (x, y)
        y_prev = y
        x += step
    d += f" V {base_y:.0f} Z"
    return d, peak


def render_chapter_plate(chapter_number: int, data: dict | None) -> str:
    """Return the inline SVG pixel-planche plate for a guide chapter hero."""
    roman = _ROMAN.get(chapter_number, str(chapter_number))
    plate_title = _PLATE_TITLES.get(chapter_number, "")
    skyline, (peak_x, peak_y) = _pixel_skyline(chapter_number)
    dither_id = f"rl-dither-ch{chapter_number}"
    return f'''<svg class="rl-guide-plate rl-guide-plate--light" viewBox="0 0 1000 520" role="img" aria-label="Chapter {chapter_number} pixel planche plate" focusable="false" xmlns="http://www.w3.org/2000/svg">
  <style>
    .rl-guide-plate .rl-plate-bg{{fill:var(--rl-plate-paper,#f4eed9)}}
    .rl-guide-plate .rl-plate-frame{{fill:none;stroke:var(--rl-plate-ink,#1b1712);stroke-width:1.6}}
    .rl-guide-plate .rl-plate-frame-inner{{fill:none;stroke:var(--rl-plate-ink,#1b1712);stroke-width:.5;opacity:.75}}
    .rl-guide-plate .rl-plate-tick{{fill:none;stroke:var(--rl-plate-ink,#1b1712);stroke-width:1.4}}
    .rl-guide-plate .rl-plate-px{{shape-rendering:crispEdges}}
    .rl-guide-plate .rl-plate-skyline{{fill:none;stroke:var(--rl-plate-ink,#1b1712);stroke-width:3;shape-rendering:crispEdges}}
    .rl-guide-plate .rl-plate-flag{{fill:var(--rl-garnish,#a8781f);shape-rendering:crispEdges}}
    .rl-guide-plate .rl-plate-flag-pole{{fill:var(--rl-plate-ink,#1b1712);shape-rendering:crispEdges}}
    .rl-guide-plate .rl-plate-check-px{{fill:var(--rl-garnish,#a8781f);shape-rendering:crispEdges}}
    .rl-guide-plate .rl-plate-cartouche{{fill:var(--rl-plate-paper,#f4eed9);stroke:var(--rl-plate-ink,#1b1712);stroke-width:1.2}}
    .rl-guide-plate .rl-plate-cartouche-inner{{fill:none;stroke:var(--rl-garnish,#a8781f);stroke-width:.8}}
    .rl-guide-plate .rl-plate-cart-title{{font-family:var(--rl-font-editorial);font-size:19px;font-weight:700;letter-spacing:4px;fill:var(--rl-plate-ink,#1b1712);text-anchor:middle}}
    .rl-guide-plate .rl-plate-cart-sub{{font-family:var(--rl-font-data);font-size:10px;font-weight:500;letter-spacing:3px;fill:var(--rl-garnish-deep,#7d5a17);text-anchor:middle}}
    .rl-guide-plate .rl-plate-rule,.rl-guide-plate .rl-plate-line{{fill:none;stroke:var(--rl-plate-ink,#1b1712);stroke-width:2.6;stroke-linecap:square;stroke-linejoin:miter;shape-rendering:crispEdges}}
    .rl-guide-plate .rl-plate-rule{{stroke-width:1.8}}
    .rl-guide-plate .rl-plate-rule-soft,.rl-guide-plate .rl-plate-line-soft{{stroke:var(--rl-plate-ink,#1b1712);opacity:.34;stroke-width:2}}
    .rl-guide-plate .rl-plate-numeral{{font-family:var(--rl-font-editorial);font-size:230px;font-weight:700;fill:var(--rl-plate-ink,#1b1712);opacity:.07;text-anchor:middle}}
    .rl-guide-plate .rl-plate-label{{font-family:var(--rl-font-data);font-size:15px;font-weight:600;letter-spacing:2px;fill:var(--rl-plate-ink,#1b1712)}}
    .rl-guide-plate .rl-plate-label-strong{{fill:var(--rl-plate-ink,#1b1712);font-weight:700}}
    .rl-guide-plate .rl-plate-dot{{fill:var(--rl-garnish,#a8781f)}}
    .rl-guide-plate .rl-plate-bar-track{{fill:none;stroke:var(--rl-plate-ink,#1b1712);stroke-width:.7;opacity:.55}}
    .rl-guide-plate .rl-plate-bar-fill{{fill:var(--rl-plate-ink,#1b1712)}}
    .rl-guide-plate .rl-plate-tier-1{{fill:var(--rl-plate-ink,#1b1712)}}
    .rl-guide-plate .rl-plate-tier-2{{fill:var(--rl-garnish,#a8781f)}}
    .rl-guide-plate .rl-plate-tier-3{{fill:var(--rl-plate-ink,#1b1712);opacity:.55}}
    .rl-guide-plate .rl-plate-tier-4{{fill:var(--rl-plate-ink,#1b1712);opacity:.3}}
    .rl-guide-plate .rl-plate-signal{{fill:none;stroke:var(--rl-plate-ink,#1b1712);stroke-width:1.6;shape-rendering:crispEdges}}
    .rl-guide-plate .rl-plate-zone-1{{fill:var(--rl-zone-1,#c0c0bc)}}.rl-guide-plate .rl-plate-zone-2{{fill:var(--rl-zone-2,#4a78b0)}}.rl-guide-plate .rl-plate-zone-3{{fill:var(--rl-zone-3,#4a8860)}}.rl-guide-plate .rl-plate-zone-4{{fill:var(--rl-zone-4,#a88850)}}.rl-guide-plate .rl-plate-zone-5{{fill:var(--rl-zone-5,#b07858)}}
  </style>
  <defs>
    <pattern id="{dither_id}" width="8" height="8" patternUnits="userSpaceOnUse">
      <rect width="8" height="8" fill="var(--rl-plate-paper,#f4eed9)"></rect>
      <rect width="4" height="4" fill="var(--rl-plate-ink,#1b1712)" opacity="0.4"></rect>
      <rect x="4" y="4" width="4" height="4" fill="var(--rl-plate-ink,#1b1712)" opacity="0.4"></rect>
    </pattern>
  </defs>
  <rect class="rl-plate-bg" x="0" y="0" width="1000" height="520"></rect>
  <rect class="rl-plate-frame" x="14" y="14" width="972" height="492"></rect>
  <rect class="rl-plate-frame-inner" x="21" y="21" width="958" height="478"></rect>
  <path class="rl-plate-tick" d="M14 40 h12 M40 14 v12 M986 40 h-12 M960 14 v12 M14 480 h12 M40 506 v-12 M986 480 h-12 M960 506 v-12"></path>
  <path class="rl-plate-px" d="{skyline}" fill="url(#{dither_id})"></path>
  <path class="rl-plate-skyline" d="{skyline}"></path>
  <rect class="rl-plate-flag-pole" x="{peak_x + 8:.0f}" y="{peak_y - 24:.0f}" width="4" height="24"></rect>
  <rect class="rl-plate-flag" x="{peak_x + 12:.0f}" y="{peak_y - 24:.0f}" width="14" height="6"></rect>
  <rect class="rl-plate-flag" x="{peak_x + 12:.0f}" y="{peak_y - 18:.0f}" width="10" height="4"></rect>
  <rect class="rl-plate-cartouche" x="370" y="34" width="260" height="58"></rect>
  <rect class="rl-plate-cartouche-inner" x="375" y="39" width="250" height="48"></rect>
  <text class="rl-plate-cart-title" x="500" y="60">PLANCHE {roman}</text>
  <text class="rl-plate-cart-sub" x="500" y="78">{_esc(plate_title)}</text>
  <text class="rl-plate-numeral" x="770" y="360">{roman}</text>
  <path class="rl-plate-rule rl-plate-rule-soft" d="M560 150 H960 M560 430 H960"></path>
  {_motif(chapter_number, data)}
</svg>'''
