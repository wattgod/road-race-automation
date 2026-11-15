#!/usr/bin/env python3
"""
Generate Open Graph social preview images for Roadie Labs race landing pages.

Produces 1200x630 neo-brutalist styled JPEG images optimized for social sharing:
  - Dark background for feed contrast (stops the scroll)
  - Race name as dominant visual element (64px bold)
  - Tagline hook text (the curiosity-gap copy)
  - Score badge with arc progress (the numerical hook)
  - Location + stats as supporting info (truncated for clarity)
  - Strong brand bar with ROADIE LABS identity
  - Subtle topo-line texture for visual depth
  - Optimized for thumbnail legibility (~200-400px wide in feeds)

Usage:
    python scripts/generate_og_images.py paris-brest-paris
    python scripts/generate_og_images.py --site       # /og/homepage.jpg only
    python scripts/generate_og_images.py --all        # homepage.jpg + every race
    python scripts/generate_og_images.py --all --output-dir wordpress/output/og

--all writes every /og/*.jpg a page generator references (see
push_wordpress.expected_og_filenames). Then deploy with
`scripts/push_wordpress.py --sync-og`, which refuses to upload a partial set.
Brand fonts are required; a missing font is an error, never a substitute.
"""

import argparse
import json
import math
import random
import re
import sys
import zlib
from pathlib import Path

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    print("ERROR: Pillow required. Install with: pip install Pillow")
    sys.exit(1)

# ── Constants ──────────────────────────────────────────────────

W, H = 1200, 630

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from wordpress.brand_tokens import COLORS


def _rgb(color_key: str) -> tuple:
    """Convert a canonical brand_tokens.COLORS entry to an RGB tuple."""
    return tuple(bytes.fromhex(COLORS[color_key].lstrip('#')))


# Timing Slip palette (Nov 2026) — all values from wordpress/brand_tokens.py.
# A results sheet on paper: ink on paper, graphite secondary text, and role
# colours that each mean one thing (red = the Lab Score, gold = Tier 1 fill).
INK = _rgb("ink")                   # #202322
PAPER = _rgb("paper")               # #fafaf8
GRAPHITE = _rgb("graphite")         # #555555
WELL = _rgb("well")                 # #efefea (sunken score area)
ZEBRA = _rgb("zebra")               # #f2f2ed (topo texture)
SILVER = _rgb("silver")             # #d0d0c8 (dividers)
STEEL = _rgb("steel")               # #999999
SCORE_RED = _rgb("score")           # #b3302a Maillot Red — the Lab Score only
TIER_GOLD = _rgb("tier_gold")       # #d99a1e Jersey Gold — Tier 1 fill only
WHITE = _rgb("white")

# Tier pill: T1 gold fill with ink text, T2 ink outline, T3 thin steel
# outline, T4 plain graphite text (brand-and-trust skill).
TIER_PILL = {
    1: {"fill": TIER_GOLD, "outline": TIER_GOLD, "width": 0, "text": INK},
    2: {"fill": None, "outline": INK, "width": 2, "text": INK},
    3: {"fill": None, "outline": STEEL, "width": 1, "text": INK},
    4: {"fill": None, "outline": None, "width": 0, "text": GRAPHITE},
}

DIMENSIONS_CONFIG = REPO_ROOT / "config" / "dimensions.json"


def load_dimension_keys(path: Path = DIMENSIONS_CONFIG) -> list:
    """Load the canonical ordered scoring keys from config/dimensions.json."""
    return [d["key"] for d in json.loads(path.read_text())["dimensions"]]


ALL_DIMS = load_dimension_keys()

# Brand font paths — Sometype Mono (data) + Source Serif 4 (editorial)
# TODO: temporary cross-repo dependency until road-labs-brand vendors its own
# copies of the shared image-generator TTF files. Resolved from the main
# checkout (REPO_ROOT.parent); pass --font-dir when running from a worktree.
DEFAULT_FONT_DIR = REPO_ROOT.parent / "gravel-race-automation" / "guide" / "fonts"
FONT_FILES = {
    "editorial": "SourceSerif4-Variable.ttf",
    "data": "SometypeMono-Regular.ttf",
    "data_bold": "SometypeMono-Bold.ttf",
}
FONT_DIR = DEFAULT_FONT_DIR


class FontMissingError(RuntimeError):
    """A brand font file is missing. OG images are never rendered with a
    substitute font."""


_FONT_CACHE = {}


def set_font_dir(font_dir: Path) -> None:
    """Point the generator at a font directory, failing if any brand font is
    missing there."""
    global FONT_DIR
    font_dir = Path(font_dir)
    missing = [name for name in FONT_FILES.values() if not (font_dir / name).is_file()]
    if missing:
        raise FontMissingError(
            f"brand fonts missing in {font_dir}: {', '.join(missing)}. "
            "Run from the main checkout (sibling gravel-race-automation repo) "
            "or pass --font-dir."
        )
    FONT_DIR = font_dir
    _FONT_CACHE.clear()


def load_font(role: str, size: int) -> ImageFont.FreeTypeFont:
    """Load a brand font by role. Raises FontMissingError instead of
    substituting a system or default font."""
    key = (str(FONT_DIR), role, size)
    if key not in _FONT_CACHE:
        path = FONT_DIR / FONT_FILES[role]
        try:
            _FONT_CACHE[key] = ImageFont.truetype(str(path), size)
        except (OSError, IOError) as e:
            raise FontMissingError(f"cannot load brand font {path}: {e}") from e
    return _FONT_CACHE[key]


def tw(draw, text, font):
    """Text width helper."""
    bbox = draw.textbbox((0, 0), text, font=font)
    return bbox[2] - bbox[0]


def th(draw, text, font):
    """Text height helper."""
    bbox = draw.textbbox((0, 0), text, font=font)
    return bbox[3] - bbox[1]


def wrap_text(draw, text, font, max_width):
    words = text.split()
    lines = []
    current = ""
    for word in words:
        test = f"{current} {word}".strip()
        if tw(draw, test, font) <= max_width:
            current = test
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def truncate(text, max_chars=40):
    """Truncate long strings with ellipsis."""
    if len(text) <= max_chars:
        return text
    return text[:max_chars - 1].rstrip() + "\u2026"


def draw_topo_texture(draw, seed=42):
    """Draw subtle topographic-style lines for route-oriented visual depth."""
    rng = random.Random(seed)
    for _ in range(8):
        # Random horizontal wavy lines
        y_base = rng.randint(60, H - 100)
        points = []
        for x in range(0, W + 40, 40):
            y = y_base + rng.randint(-15, 15)
            points.append((x, y))
        if len(points) >= 2:
            draw.line(points, fill=ZEBRA, width=2)


def draw_score_badge(draw, cx, cy, radius, score, tier, font_big, font_label):
    """Draw a neo-brutalist score badge: thick ring with arc progress."""
    accent = SCORE_RED

    # Sunken well with a silver track ring
    ring_w = 5
    draw.ellipse(
        [cx - radius, cy - radius, cx + radius, cy + radius],
        fill=WELL, outline=SILVER, width=ring_w
    )

    # Score arc — thicker, brighter
    arc_r = radius - 1
    arc_extent = int(360 * score / 100)
    draw.arc(
        [cx - arc_r, cy - arc_r, cx + arc_r, cy + arc_r],
        start=-90, end=-90 + arc_extent,  # Start from top
        fill=accent, width=7
    )

    # Score number — large, colored
    # Anchored on the glyph box so "/ 100" sits below the number, not on it.
    draw.text((cx, cy + 6), str(score), fill=accent, font=font_big, anchor="ms")
    draw.text((cx, cy + 20), "/ 100", fill=GRAPHITE, font=font_label, anchor="mt")


LEFT_MARGIN = 56
TOP_BAR_H = 5
BRAND_BAR_H = 66


def draw_brand_bar(draw) -> int:
    """Draw the ink ROADIE LABS bar along the bottom; return its top y."""
    bottom_bar_y = H - BRAND_BAR_H
    draw.rectangle([0, bottom_bar_y, W, H], fill=INK)
    font_brand = load_font('data_bold', 28)
    font_brand_sub = load_font('data', 16)
    draw.text((LEFT_MARGIN, bottom_bar_y + 16), "ROADIE LABS", fill=PAPER, font=font_brand)
    url_text = "roadielabs.com"
    uw = tw(draw, url_text, font_brand_sub)
    draw.text((W - LEFT_MARGIN - uw, bottom_bar_y + 24), url_text, fill=SILVER, font=font_brand_sub)
    return bottom_bar_y


def generate_og_image(race_data: dict, output_path: Path) -> Path:
    """Generate a single OG image for a race."""

    name = race_data.get('display_name') or race_data.get('name')
    slug = race_data.get('slug')
    if not name or not slug:
        raise ValueError("race profile has no name/slug")
    tagline = race_data.get('tagline', '')
    vitals = race_data.get('vitals', {})
    rating = race_data.get('fondo_rating') or {}

    # Score and tier come from the profile exactly as the race page shows
    # them (tier includes the prestige override). Never recomputed here.
    overall_score = rating.get('overall_score')
    tier = rating.get('tier')
    if overall_score is None or tier not in TIER_PILL:
        raise ValueError(f"{slug}: fondo_rating.overall_score/tier missing")
    overall_score = int(round(float(overall_score)))

    location = truncate(vitals.get('location', ''), 30)
    date_specific = vitals.get('date_specific', '')
    dist_mi = vitals.get('distance_mi')
    elev_ft = vitals.get('elevation_ft')
    distance = f"{dist_mi} mi" if dist_mi else ''
    elevation = f"{elev_ft:,.0f} ft" if isinstance(elev_ft, (int, float)) else ''

    # Parse date — short format only
    short_date = ''
    if date_specific:
        m = re.search(r'(\d{4}):\s*(\w+\s+\d+)', date_specific)
        if m:
            short_date = f"{m.group(2).strip()}, {m.group(1)}"
        else:
            # Fallback: just grab first recognizable date-like chunk
            m2 = re.search(r'(\w+\s+\d{1,2})', date_specific)
            if m2:
                short_date = m2.group(1)

    # ── Create image on paper ─────────────────────────────────

    img = Image.new('RGB', (W, H), PAPER)
    draw = ImageDraw.Draw(img)

    # Subtle topo texture; crc32 keeps each race's pattern stable across runs
    # (str hash() is salted per process).
    draw_topo_texture(draw, seed=zlib.crc32(slug.encode()) % 10000)

    # Load fonts — editorial (Source Serif 4) for name/tagline, data (Sometype Mono) for labels
    font_name = load_font('editorial', 64)          # Race name — editorial serif
    font_tagline = load_font('editorial', 22)       # Tagline — editorial serif
    font_tier = load_font('data_bold', 20)          # Tier pill — data mono bold
    font_score_big = load_font('editorial', 60)     # Score number — editorial serif
    font_score_label = load_font('data', 18)        # Score label — data mono
    font_detail = load_font('data', 22)             # Stats — data mono
    font_detail_bold = load_font('data_bold', 22)   # Location — data mono bold

    # ── Layout ────────────────────────────────────────────────

    left_margin = LEFT_MARGIN
    score_badge_r = 76
    score_cx = W - left_margin - score_badge_r - 6
    score_cy = 260

    draw.rectangle([0, 0, W, TOP_BAR_H], fill=INK)
    bottom_bar_y = draw_brand_bar(draw)

    # ── Content area ──────────────────────────────────────────

    content_top = TOP_BAR_H + 28
    content_bottom = bottom_bar_y - 16
    content_right = score_cx - score_badge_r - 36

    # Tier pill
    pill = TIER_PILL[tier]
    badge_text = f"TIER {tier}"
    badge_bw = tw(draw, badge_text, font_tier) + 20
    badge_bh = th(draw, badge_text, font_tier) + 12
    draw.rectangle(
        [left_margin, content_top, left_margin + badge_bw, content_top + badge_bh],
        fill=pill["fill"], outline=pill["outline"], width=pill["width"]
    )
    draw.text((left_margin + 10, content_top + 4), badge_text, fill=pill["text"], font=font_tier)

    # Race name — large, ink on paper. Max 2 lines.
    name_y = content_top + badge_bh + 14
    name_max_w = content_right - left_margin
    name_lines = wrap_text(draw, name.upper(), font_name, name_max_w)
    line_h = 72
    for i, line in enumerate(name_lines[:2]):
        draw.text((left_margin, name_y + i * line_h), line, fill=INK, font=font_name)
    name_bottom = name_y + min(len(name_lines), 2) * line_h

    # Tagline — graphite secondary text.
    if tagline:
        tag_y = name_bottom + 6
        tag_max_w = content_right - left_margin
        tag_lines = wrap_text(draw, tagline, font_tagline, tag_max_w)
        for i, line in enumerate(tag_lines[:2]):
            draw.text((left_margin, tag_y + i * 28), line, fill=GRAPHITE, font=font_tagline)

    # ── Stats strip ───────────────────────────────────────────

    strip_y = content_bottom - 24
    stats = []
    if location:
        stats.append(location)
    if short_date:
        stats.append(short_date)
    if distance:
        stats.append(distance)
    if elevation:
        stats.append(elevation)

    if stats:
        # Thin separator line
        draw.rectangle([left_margin, strip_y - 10, W - left_margin, strip_y - 9], fill=SILVER)

        stat_x = left_margin
        for j, stat in enumerate(stats):
            if j > 0:
                sep = "  \u00b7  "
                draw.text((stat_x, strip_y), sep, fill=STEEL, font=font_detail)
                stat_x += tw(draw, sep, font_detail)
            f = font_detail_bold if j == 0 else font_detail
            c = INK if j == 0 else GRAPHITE
            draw.text((stat_x, strip_y), stat, fill=c, font=f)
            stat_x += tw(draw, stat, f)

    # ── Score badge ───────────────────────────────────────────

    draw_score_badge(draw, score_cx, score_cy, score_badge_r, overall_score, tier,
                     font_score_big, font_score_label)

    # ── Save ──────────────────────────────────────────────────

    output_path.parent.mkdir(parents=True, exist_ok=True)
    jpeg_path = output_path.with_suffix('.jpg')
    img.save(str(jpeg_path), 'JPEG', quality=88, optimize=True)
    return jpeg_path


# Site-wide card: referenced as /og/homepage.jpg by the homepage, plans,
# vs pages, state hubs, legal, about, coaching and other non-race pages.
SITE_OG_FILENAME = "homepage.jpg"
# Copy lifted from the homepage meta description (generate_homepage.py),
# minus the race count so the image never goes stale between regenerations.
SITE_OG_HEADLINE = "Find your next road race."
SITE_OG_SUBHEAD = ("Gran fondos and sportives worldwide, scored on 14 base "
                   "dimensions plus cultural impact.")


def generate_site_og_image(output_path: Path) -> Path:
    """Generate the site-wide OG card (/og/homepage.jpg)."""
    img = Image.new('RGB', (W, H), PAPER)
    draw = ImageDraw.Draw(img)
    draw_topo_texture(draw, seed=7)

    draw.rectangle([0, 0, W, TOP_BAR_H], fill=INK)
    bottom_bar_y = draw_brand_bar(draw)

    max_w = W - 2 * LEFT_MARGIN
    font_head = load_font('editorial', 76)
    font_sub = load_font('editorial', 30)
    head_lines = wrap_text(draw, SITE_OG_HEADLINE.upper(), font_head, max_w)
    sub_lines = wrap_text(draw, SITE_OG_SUBHEAD, font_sub, max_w)
    head_lh, sub_lh = 88, 40
    block_h = len(head_lines) * head_lh + 24 + len(sub_lines) * sub_lh
    y = TOP_BAR_H + (bottom_bar_y - TOP_BAR_H - block_h) // 2
    for line in head_lines:
        draw.text((LEFT_MARGIN, y), line, fill=INK, font=font_head)
        y += head_lh
    y += 24
    for line in sub_lines:
        draw.text((LEFT_MARGIN, y), line, fill=GRAPHITE, font=font_sub)
        y += sub_lh

    output_path.parent.mkdir(parents=True, exist_ok=True)
    jpeg_path = output_path.with_suffix('.jpg')
    img.save(str(jpeg_path), 'JPEG', quality=88, optimize=True)
    return jpeg_path


def main():
    parser = argparse.ArgumentParser(description='Generate OG images for Roadie Labs race profiles')
    parser.add_argument('slug', nargs='?', help='Race slug (e.g., maratona-dles-dolomites)')
    parser.add_argument('--all', action='store_true',
                        help='Generate the site card (homepage.jpg) and every race image')
    parser.add_argument('--site', action='store_true',
                        help='Generate only the site card (homepage.jpg)')
    parser.add_argument('--data-dir', type=Path, help='Race data directory')
    parser.add_argument('--output-dir', type=Path, help='Output directory for images')
    parser.add_argument('--font-dir', type=Path, default=DEFAULT_FONT_DIR,
                        help=f'Brand TTF directory (default: {DEFAULT_FONT_DIR})')
    args = parser.parse_args()

    if not args.slug and not args.all and not args.site:
        parser.error("Provide a race slug, --site or --all")

    try:
        set_font_dir(args.font_dir)
    except FontMissingError as e:
        print(f"ERROR: {e}")
        sys.exit(1)

    script_dir = Path(__file__).resolve().parent
    project_root = script_dir.parent
    data_dir = args.data_dir or project_root / 'race-data'
    if not data_dir.exists():
        print(f"ERROR: Data directory not found: {data_dir}")
        sys.exit(1)

    output_dir = args.output_dir or project_root / 'wordpress' / 'output' / 'og'

    if args.all:
        slugs = [f.stem for f in sorted(data_dir.glob('*.json'))]
    elif args.slug:
        slugs = [args.slug]
    else:
        slugs = []
    total = len(slugs)
    errors = 0

    if args.all or args.site:
        generate_site_og_image(output_dir / SITE_OG_FILENAME)
        print(f"  Generated {SITE_OG_FILENAME}")

    for i, slug in enumerate(slugs, 1):
        data_file = data_dir / f"{slug}.json"
        if not data_file.exists():
            print(f"  SKIP: {slug} (no data file)")
            errors += 1
            continue
        try:
            with open(data_file) as f:
                raw = json.load(f)
            race = raw.get('race', raw)
            race.setdefault('slug', slug)
            generate_og_image(race, output_dir / f"{slug}.jpg")
            if args.all and i % 50 == 0:
                print(f"  [{i}/{total}] Generated {slug}.jpg")
        except Exception as e:
            print(f"  ERROR: {slug}: {e}")
            errors += 1

    print(f"\nDone. {total - errors}/{total} images generated in {output_dir}/")
    if errors:
        print(f"  {errors} errors")
        sys.exit(1)


if __name__ == '__main__':
    main()
