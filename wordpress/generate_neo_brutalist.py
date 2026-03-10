#!/usr/bin/env python3
"""
Generate neo-brutalist landing page HTML for gravel race profiles.

Reads race data from race-data/*.json (new format) or data/*-data.json (old format),
produces self-contained HTML pages with:
  - Interactive accordion ratings (15 dimensions)
  - Sticky bottom CTA bar
  - Contextual mid-page CTA strips
  - Scroll fade-in animations
  - SportsEvent + FAQ JSON-LD structured data
  - Questionnaire-first training section

Usage:
    python generate_neo_brutalist.py unbound-200
    python generate_neo_brutalist.py unbound-200 --data-dir ../race-data
    python generate_neo_brutalist.py --all --data-dir ../race-data
    python generate_neo_brutalist.py --all --output-dir ./output
"""

import argparse
import hashlib
import html
import json
import logging
import math
import re
import shutil
import sys
from datetime import date, datetime
from pathlib import Path
from typing import Any, Optional

from brand_tokens import (
    BRAND_FONTS_DIR,
    COLORS,
    FONT_FILES,
    RACER_RATING_THRESHOLD,
    get_font_face_css,
    get_preload_hints,
    get_tokens_css,
    get_ga4_head_snippet,
)
from cookie_consent import get_consent_banner_html
from shared_footer import get_mega_footer_css, get_mega_footer_html
from shared_header import get_site_header_css, get_site_header_html

# ── Constants ──────────────────────────────────────────────────

COURSE_DIMS = ['logistics', 'length', 'technicality', 'elevation', 'climate', 'altitude', 'adventure']
OPINION_DIMS = ['prestige', 'race_quality', 'experience', 'community', 'field_depth', 'value', 'expenses']
ALL_DIMS = COURSE_DIMS + OPINION_DIMS

DIM_LABELS = {
    'logistics': 'Logistics',
    'length': 'Length',
    'technicality': 'Technicality',
    'elevation': 'Elevation',
    'climate': 'Climate',
    'altitude': 'Altitude',
    'adventure': 'Adventure',
    'prestige': 'Prestige',
    'race_quality': 'Race Quality',
    'experience': 'Experience',
    'community': 'Community',
    'field_depth': 'Field Depth',
    'value': 'Value',
    'expenses': 'Expenses',
}

# FAQ question templates per dimension
FAQ_TEMPLATES = {
    'climate': 'What is the climate like at {name}?',
    'logistics': 'How are the logistics for {name}?',
    'technicality': 'How technical is {name}?',
    'elevation': 'How much climbing is there at {name}?',
    'adventure': 'How adventurous is {name}?',
    'prestige': 'How prestigious is {name}?',
    'race_quality': 'What is the race quality like at {name}?',
    'experience': 'What is the race experience like at {name}?',
    'community': 'What is the community like at {name}?',
    'field_depth': 'How competitive is the field at {name}?',
    'value': 'Is {name} good value for money?',
    'expenses': 'How expensive is {name}?',
    'length': 'How long is {name}?',
    'altitude': 'What is the altitude at {name}?',
}

# Priority dimensions for FAQ schema (pick top 5 per race)
FAQ_PRIORITY = ['climate', 'logistics', 'adventure', 'prestige', 'technicality',
                'experience', 'race_quality', 'elevation', 'community', 'value']

# Month name → number mapping (shared by JSON-LD and training countdown)
MONTH_NUMBERS = {
    "january": "01", "february": "02", "march": "03", "april": "04",
    "may": "05", "june": "06", "july": "07", "august": "08",
    "september": "09", "october": "10", "november": "11", "december": "12",
}

logger = logging.getLogger(__name__)


def parse_event_dates(date_str: str) -> tuple[str | None, str | None]:
    """Parse a race date string into (startDate, endDate) ISO strings.

    Handles:
      - Single day: "2026: June 15" → ("2026-06-15", "2026-06-15")
      - Same-month range: "2026: August 19-23" → ("2026-08-19", "2026-08-23")
      - Cross-month range: "2026: June 30 - July 2" → ("2026-06-30", "2026-07-02")
      - Day-of-week prefixes: "Friday, June 12th" → stripped
      - Ordinal suffixes: "7th", "1st", "22nd" → stripped

    Returns (None, None) for TBD, empty, or unparseable strings.
    """
    if not date_str:
        logger.debug("Empty date string — skipping")
        return None, None

    # Strip day-of-week and ordinal suffixes
    clean = re.sub(
        r'(?:Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday),?\s*',
        '', date_str)
    clean = re.sub(r'(\d+)(?:st|nd|rd|th)\b', r'\1', clean)

    # Try cross-month first: "2026: June 30 - July 2"
    cross = re.search(
        r'(\d{4}).*?(\w+)\s+(\d+)\s*-\s*(\w+)\s+(\d+)', clean)
    if cross:
        year = cross.group(1)
        start_month = MONTH_NUMBERS.get(cross.group(2).lower())
        start_day = cross.group(3)
        end_month = MONTH_NUMBERS.get(cross.group(4).lower())
        end_day = cross.group(5)
        if start_month and end_month:
            return (
                f"{year}-{start_month}-{int(start_day):02d}",
                f"{year}-{end_month}-{int(end_day):02d}",
            )

    # Fall back to same-month: "2026: June 15" or "2026: August 19-23"
    same = re.search(r'(\d{4}).*?(\w+)\s+(\d+)(?:\s*-\s*(\d+))?', clean)
    if same:
        year = same.group(1)
        month = MONTH_NUMBERS.get(same.group(2).lower())
        if month:
            start_day = same.group(3)
            end_day = same.group(4)
            start = f"{year}-{month}-{int(start_day):02d}"
            end = f"{year}-{month}-{int(end_day):02d}" if end_day else start
            return start, end

    # If the string contains a year but we still couldn't parse it, warn
    if re.search(r'\d{4}', date_str):
        logger.warning("Date contains year but failed to parse: %s", date_str)
    else:
        logger.debug("Unparseable date: %s", date_str)
    return None, None


# US state names and abbreviations for country detection in JSON-LD
US_STATES = {
    'Alabama', 'Alaska', 'Arizona', 'Arkansas', 'California', 'Colorado',
    'Connecticut', 'Delaware', 'Florida', 'Georgia', 'Hawaii', 'Idaho',
    'Illinois', 'Indiana', 'Iowa', 'Kansas', 'Kentucky', 'Louisiana',
    'Maine', 'Maryland', 'Massachusetts', 'Michigan', 'Minnesota',
    'Mississippi', 'Missouri', 'Montana', 'Nebraska', 'Nevada',
    'New Hampshire', 'New Jersey', 'New Mexico', 'New York',
    'North Carolina', 'North Dakota', 'Ohio', 'Oklahoma', 'Oregon',
    'Pennsylvania', 'Rhode Island', 'South Carolina', 'South Dakota',
    'Tennessee', 'Texas', 'Utah', 'Vermont', 'Virginia', 'Washington',
    'West Virginia', 'Wisconsin', 'Wyoming',
    'AL', 'AK', 'AZ', 'AR', 'CA', 'CO', 'CT', 'DE', 'FL', 'GA',
    'HI', 'ID', 'IL', 'IN', 'IA', 'KS', 'KY', 'LA', 'ME', 'MD',
    'MA', 'MI', 'MN', 'MS', 'MO', 'MT', 'NE', 'NV', 'NH', 'NJ',
    'NM', 'NY', 'NC', 'ND', 'OH', 'OK', 'OR', 'PA', 'RI', 'SC',
    'SD', 'TN', 'TX', 'UT', 'VT', 'VA', 'WA', 'WV', 'WI', 'WY',
}

# Country name → ISO 3166-1 alpha-2 code
COUNTRY_CODES = {
    'Canada': 'CA', 'UK': 'GB', 'England': 'GB', 'Scotland': 'GB', 'Wales': 'GB',
    'Australia': 'AU', 'Queensland': 'AU', 'Victoria': 'AU',
    'South Australia': 'AU', 'New South Wales': 'AU', 'Western Australia': 'AU',
    'Italy': 'IT', 'Germany': 'DE', 'France': 'FR', 'Belgium': 'BE',
    'Belgian Ardennes': 'BE', 'Spain': 'ES', 'Switzerland': 'CH',
    'New Zealand': 'NZ', 'Colombia': 'CO', 'Chile': 'CL', 'Brazil': 'BR',
    'Argentina': 'AR', 'Sweden': 'SE', 'Austria': 'AT', 'Greece': 'GR',
    'Poland': 'PL', 'Finland': 'FI', 'Netherlands': 'NL', 'Norway': 'NO',
    'Portugal': 'PT', 'Romania': 'RO', 'South Africa': 'ZA', 'Kenya': 'KE',
    'Thailand': 'TH', 'Japan': 'JP', 'British Columbia': 'CA', 'Ontario': 'CA',
    'Southern Iceland': 'IS', 'Iceland': 'IS',
    'Morocco': 'MA', 'Monaco': 'MC', 'Luxembourg': 'LU',
    'Czech Republic': 'CZ', 'Slovenia': 'SI', 'Croatia': 'HR',
    'Kenya': 'KE', 'Slovakia': 'SK', 'Denmark': 'DK',
    'UAE': 'AE', 'Dubai': 'AE', 'Israel': 'IL',
}


def detect_country(location: str) -> str:
    """Detect ISO country code from location string. Returns 'US' as default."""
    if not location or location == '--':
        return 'US'
    parts = [p.strip() for p in location.split(',')]
    # Check last part first (most specific), then second-to-last
    for part in reversed(parts):
        # Strip parentheticals: "Georgia (North Georgia mountains)" → "Georgia"
        clean = re.sub(r'\s*\(.*\)', '', part).strip()
        if clean in COUNTRY_CODES:
            return COUNTRY_CODES[clean]
        if clean in US_STATES:
            return 'US'
    return 'US'


SITE_BASE_URL = "https://roadlabs.cc"
COACHING_URL = f"{SITE_BASE_URL}/coaching/apply/"
TRAINING_PLANS_URL = f"{SITE_BASE_URL}/questionnaire/"
SUBSTACK_URL = "https://gravelgodcycling.substack.com"
SUBSTACK_EMBED = "https://gravelgodcycling.substack.com/embed"
CURRENT_YEAR = str(datetime.now().year)


def build_seo_title(rd: dict) -> str:
    """Build an SEO-optimized <title> tag.

    Target format: "{Race Name} Review {Year} | {Location} | Road Labs"
    Falls back to shorter forms if title exceeds ~60 chars.
    """
    name = rd['name']
    location = rd['vitals'].get('location', '') or ''
    # Extract just state/country from full location like "Emporia, Kansas"
    loc_short = location.split(',')[-1].strip() if ',' in location else location

    # Try full format first
    full = f"{name} Review {CURRENT_YEAR} | {loc_short} | Road Labs"
    if len(full) <= 62:
        return full

    # Drop location if too long
    medium = f"{name} Review {CURRENT_YEAR} | Road Labs"
    if len(medium) <= 62:
        return medium

    # Minimal
    return f"{name} | Road Labs"


def build_seo_description(rd: dict) -> str:
    """Build an SEO-optimized meta description (120-155 chars target).

    Combines tagline + score/tier + call-to-action suffix.
    """
    tagline = rd.get('tagline', '').rstrip('.')
    score = rd.get('overall_score', 0)
    tier = rd.get('tier', 4)
    tier_label = {1: 'Elite', 2: 'Contender', 3: 'Solid', 4: 'Roster'}.get(tier, f'Tier {tier}')
    location = rd.get('vitals', {}).get('location', '')
    if location == '--':
        location = ''
    # Build suffix with optional location for local SEO
    if location and len(location) <= 30:
        suffix = f" Rated {score}/100 ({tier_label}) in {location}. Course maps, ratings & full breakdown."
    else:
        suffix = f" Rated {score}/100 ({tier_label}). Course maps, ratings & full breakdown."

    if not tagline:
        return suffix.lstrip()
    desc = f"{tagline}.{suffix}"
    if len(desc) <= 160:
        return desc

    # Truncate tagline — prefer breaking at sentence boundary
    max_tagline = 160 - len(suffix) - 1  # 1 for "."
    if max_tagline > 30:
        # Try to break at last complete sentence (period followed by space)
        candidate = tagline[:max_tagline]
        last_period = candidate.rfind('. ')
        if last_period > 30:
            truncated = candidate[:last_period]
        else:
            truncated = candidate.rsplit(' ', 1)[0].rstrip('.,;:—-')
        return f"{truncated}.{suffix}"

    # Fallback: just tagline + score
    return f"{tagline}. Rated {score}/100 ({tier_label}) by Road Labs."


# ── Phase 1: Data Adapter ─────────────────────────────────────

def _merge_youtube_quotes(youtube_data: dict) -> list:
    """Merge curated quotes with rider_intel additional_quotes, capped at 4 total.

    Priority: existing curated quotes first, then additional_quotes from rider_intel.
    """
    curated = [
        q for q in youtube_data.get('quotes', [])
        if q.get('curated')
    ]
    additional = youtube_data.get('rider_intel', {}).get('additional_quotes', [])

    # Start with existing curated quotes
    merged = list(curated)

    # Fill remaining slots with additional quotes (up to 4 total)
    for q in additional:
        if len(merged) >= 4:
            break
        # Avoid duplicate text
        existing_texts = {m.get('text', '').strip().lower() for m in merged}
        if q.get('text', '').strip().lower() not in existing_texts:
            merged.append(q)

    return merged[:4]


def normalize_race_data(data: dict) -> dict:
    """Normalize race data from new-format JSON into a consistent shape
    with all fields the generator expects. Computes derived fields if missing."""
    race = data.get('race', data)
    slug = race.get('slug', '(unknown)')

    rating = race.get('fondo_rating', {})
    bor = race.get('biased_opinion_ratings', {})
    bo_raw = race.get('biased_opinion', {})
    bo = {'summary': bo_raw} if isinstance(bo_raw, str) else bo_raw
    vitals = race.get('vitals', {})
    course = race.get('course_description', {})
    history = race.get('history', {})
    logistics = race.get('logistics', {})
    final_verdict = race.get('final_verdict', {})

    # Warn about missing sections that produce degraded output
    if not vitals:
        logger.warning("[%s] Missing 'vitals' section — page will show placeholder data", slug)
    if not rating:
        logger.warning("[%s] Missing 'fondo_rating' — score will be 0, tier will be T4", slug)
    if not bor:
        logger.warning("[%s] Missing 'biased_opinion_ratings' — accordion scores will all be 0", slug)
    if not course:
        logger.warning("[%s] Missing 'course_description' — course section will be empty", slug)

    # Compute course_profile total if missing
    course_profile = sum(rating.get(d, 0) for d in COURSE_DIMS)
    opinion_total = sum(rating.get(d, 0) for d in OPINION_DIMS)

    # Build explanations dict from biased_opinion_ratings
    explanations = {}
    for dim in ALL_DIMS:
        entry = bor.get(dim, {})
        explanations[dim] = {
            'score': entry.get('score', rating.get(dim, 0)),
            'explanation': entry.get('explanation', ''),
        }

    # Extract date with year from date_specific like "2026: June 6" -> "June 6, 2026"
    date_specific = vitals.get('date_specific', '')
    short_date = date_specific
    date_match = re.search(r'(\d{4}):\s*(.+)', date_specific)
    if date_match:
        year = date_match.group(1)
        date_part = date_match.group(2).strip()
        short_date = f"{date_part}, {year}"

    # Parse entry cost from registration string, then fallback to rating explanations
    reg = vitals.get('registration') or vitals.get('entry_fee') or ''
    entry_cost = None
    cost_match = re.search(r'[\$€£][\d,]+(?:\s*[-–]\s*[\$€£]?[\d,]+)?', str(reg))
    if cost_match:
        entry_cost = cost_match.group(0)
    if not entry_cost:
        # Fallback: scan value/expenses explanations for dollar amounts
        for dim_key in ('value', 'expenses', 'logistics'):
            expl = bor.get(dim_key, {}).get('explanation', '')
            fallback_match = re.search(r'\$[\d,]+', expl)
            if fallback_match:
                entry_cost = fallback_match.group(0)
                break

    # Parse field size into short form
    field_size_raw = vitals.get('field_size', '')
    field_size_short = field_size_raw
    # Try to get just the number part
    fs_match = re.search(r'~?([\d,]+\+?)', str(field_size_raw))
    if fs_match:
        field_size_short = '~' + fs_match.group(1)

    return {
        'name': race.get('display_name') or race.get('name', 'Unknown Race'),
        'slug': race.get('slug', ''),
        'tagline': race.get('tagline', ''),
        'overall_score': rating.get('overall_score', 0),
        'tier': rating.get('tier', 4),
        'tier_label': rating.get('tier_label', f"TIER {rating.get('tier', 4)}"),
        'course_profile': course_profile,
        'opinion_total': opinion_total,
        'rating': rating,
        'explanations': explanations,
        'vitals': {
            'distance': f"{vitals.get('distance_mi', '--')} mi" if vitals.get('distance_mi') else '--',
            'distance_mi': vitals.get('distance_mi', 0),
            'elevation': f"{vitals.get('elevation_ft', '--'):,} ft" if isinstance(vitals.get('elevation_ft'), (int, float)) else str(vitals.get('elevation_ft', '--')),
            'location': vitals.get('location', '--'),
            'location_badge': vitals.get('location_badge', vitals.get('location', '--')),
            'date': short_date or vitals.get('date', '--'),
            'date_specific': date_specific,
            'field_size': field_size_short,
            'field_size_raw': field_size_raw,
            'entry_cost': entry_cost,
            'start_time': vitals.get('start_time', ''),
            'registration': reg,
            'prize_purse': vitals.get('prize_purse', ''),
            'aid_stations': vitals.get('aid_stations', ''),
            'cutoff_time': vitals.get('cutoff_time', ''),
            'terrain_types': vitals.get('terrain_types', []),
        },
        'biased_opinion': {
            'verdict': bo.get('verdict', ''),
            'summary': bo.get('summary', ''),
            'strengths': bo.get('strengths', []),
            'weaknesses': bo.get('weaknesses', []),
            'bottom_line': bo.get('bottom_line', ''),
        },
        'final_verdict': {
            'score': final_verdict.get('score', ''),
            'one_liner': final_verdict.get('one_liner', ''),
            'should_you_race': final_verdict.get('should_you_race', ''),
            'alternatives': final_verdict.get('alternatives', ''),
        },
        'course': {
            'character': course.get('character', ''),
            'suffering_zones': course.get('suffering_zones', []),
            'signature_challenge': course.get('signature_challenge', ''),
            'ridewithgps_id': course.get('ridewithgps_id'),
            'ridewithgps_name': course.get('ridewithgps_name', ''),
            'map_url': course.get('map_url', ''),
        },
        'history': {
            'founded': history.get('founded'),
            'founder': history.get('founder', ''),
            'origin_story': history.get('origin_story', ''),
            'notable_moments': history.get('notable_moments', []),
            'reputation': history.get('reputation', ''),
        },
        'logistics': {
            'airport': logistics.get('airport', ''),
            'lodging_strategy': logistics.get('lodging_strategy', ''),
            'food': logistics.get('food', ''),
            'packet_pickup': logistics.get('packet_pickup', ''),
            'parking': logistics.get('parking', ''),
            'official_site': logistics.get('official_site', ''),
        },
        'youtube_videos': [
            v for v in race.get('youtube_data', {}).get('videos', [])
            if v.get('curated')
        ][:3],
        'youtube_quotes': _merge_youtube_quotes(race.get('youtube_data', {})),
        'rider_intel': race.get('youtube_data', {}).get('rider_intel', {}),
        'series': race.get('series', {}),
        'terrain': race.get('terrain', {}),
        'climate_data': race.get('climate', {}),
        'citations': race.get('citations', []),
        'racer_rating': {
            'would_race_again_pct': race.get('racer_rating', {}).get('would_race_again_pct'),
            'total_ratings': race.get('racer_rating', {}).get('total_ratings', 0),
            'star_average': race.get('racer_rating', {}).get('star_average'),
            'total_reviews': race.get('racer_rating', {}).get('total_reviews', 0),
            'reviews': race.get('racer_rating', {}).get('reviews', []),
        },
        'photos': race.get('photos', []),
        'tire_recommendations': race.get('tire_recommendations', {}),
    }


# ── Phase 2: HTML Builders ─────────────────────────────────────

def esc(text: Any) -> str:
    """HTML-escape a string."""
    return html.escape(str(text)) if text else ''


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



def score_bar_color(score: int) -> str:
    """Return brand-consistent bar color based on score (1-5).
    5: teal, 4: gold, 3: primary brown, 2: secondary brown, 1: tan."""
    return {
        5: COLORS['teal'],
        4: COLORS['gold'],
        3: COLORS['primary_brown'],
        2: COLORS['secondary_brown'],
        1: COLORS['tan'],
    }.get(score, COLORS['tan'])


RADAR_LABELS = {
    'logistics': 'Logistics',
    'length': 'Length',
    'technicality': 'Technical',
    'elevation': 'Elevation',
    'climate': 'Climate',
    'altitude': 'Altitude',
    'adventure': 'Adventure',
    'prestige': 'Prestige',
    'race_quality': 'Quality',
    'experience': 'Experience',
    'community': 'Community',
    'field_depth': 'Field',
    'value': 'Value',
    'expenses': 'Expenses',
}


def _radar_svg(dims: list, explanations: dict, color_fill: str, color_stroke: str,
               label: str, total: int, max_total: int, idx_offset: int = 0) -> str:
    """Generate an SVG radar chart for a set of dimensions."""
    n = len(dims)
    w, h = 440, 380
    cx, cy, r = w // 2, 180, 100
    angle_offset = -math.pi / 2  # start at top
    label_r = r + 28

    def point(angle: float, dist: float) -> tuple:
        return (cx + dist * math.cos(angle), cy + dist * math.sin(angle))

    # Grid rings (1-5)
    grid_lines = []
    for level in range(1, 6):
        frac = level / 5
        pts = ' '.join(f'{point(angle_offset + i * 2 * math.pi / n, r * frac)[0]:.1f},'
                       f'{point(angle_offset + i * 2 * math.pi / n, r * frac)[1]:.1f}'
                       for i in range(n))
        opacity = '0.3' if level < 5 else '0.5'
        grid_lines.append(f'<polygon points="{pts}" fill="none" stroke="{COLORS["secondary_brown"]}" stroke-opacity="{opacity}" stroke-width="0.5"/>')

    # Axis lines
    axis_lines = []
    for i in range(n):
        angle = angle_offset + i * 2 * math.pi / n
        x2, y2 = point(angle, r)
        axis_lines.append(f'<line x1="{cx}" y1="{cy}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="{COLORS["tan"]}" stroke-width="0.5"/>')

    # Data polygon
    scores = []
    for dim in dims:
        entry = explanations.get(dim, {})
        scores.append(entry.get('score', 0))

    data_pts = ' '.join(
        f'{point(angle_offset + i * 2 * math.pi / n, r * s / 5)[0]:.1f},'
        f'{point(angle_offset + i * 2 * math.pi / n, r * s / 5)[1]:.1f}'
        for i, s in enumerate(scores)
    )

    # Score dots — clickable, with hover ring
    dots = []
    for i, s in enumerate(scores):
        angle = angle_offset + i * 2 * math.pi / n
        dx, dy = point(angle, r * s / 5)
        dim_label = RADAR_LABELS.get(dims[i], dims[i].replace('_', ' ').title())
        # Invisible larger hit area + visible dot + hover ring
        dots.append(
            f'<circle cx="{dx:.1f}" cy="{dy:.1f}" r="12" fill="transparent" '
            f'class="rl-radar-hit" data-accordion-idx="{idx_offset + i}" '
            f'data-label="{esc(dim_label)}" data-score="{s}" style="cursor:pointer"/>'
            f'<circle cx="{dx:.1f}" cy="{dy:.1f}" r="5" fill="{color_stroke}" '
            f'stroke="{COLORS["dark_brown"]}" stroke-width="1.5" class="rl-radar-dot" pointer-events="none" opacity="0"/>'
            f'<circle cx="{dx:.1f}" cy="{dy:.1f}" r="10" fill="none" '
            f'stroke="{color_stroke}" stroke-width="1.5" opacity="0" '
            f'class="rl-radar-ring" pointer-events="none"/>'
        )

    # Labels — two lines: name + score
    labels = []
    for i, dim in enumerate(dims):
        angle = angle_offset + i * 2 * math.pi / n
        lx, ly = point(angle, label_r)
        dim_label = RADAR_LABELS.get(dim, dim.replace('_', ' ').title())
        s = scores[i]
        anchor = 'middle'
        if lx < cx - 15:
            anchor = 'end'
        elif lx > cx + 15:
            anchor = 'start'
        labels.append(
            f'<text x="{lx:.1f}" y="{ly - 5:.1f}" text-anchor="{anchor}" '
            f'dominant-baseline="central" font-size="10" font-weight="700" '
            f'fill="{COLORS["dark_brown"]}" font-family="Sometype Mono, monospace" letter-spacing="0.5">'
            f'{esc(dim_label.upper())}</text>'
            f'<text x="{lx:.1f}" y="{ly + 7:.1f}" text-anchor="{anchor}" '
            f'dominant-baseline="central" font-size="10" font-weight="700" '
            f'fill="{color_stroke}" font-family="Sometype Mono, monospace">'
            f'{s}/5</text>'
        )

    # Total in center
    center_label = (
        f'<text x="{cx}" y="{cy - 6}" text-anchor="middle" dominant-baseline="central" '
        f'font-size="22" font-weight="700" fill="{color_stroke}" font-family="Sometype Mono, monospace">'
        f'{total}</text>'
        f'<text x="{cx}" y="{cy + 10}" text-anchor="middle" dominant-baseline="central" '
        f'font-size="9" fill="{COLORS["secondary_brown"]}" font-family="Sometype Mono, monospace" letter-spacing="1">'
        f'/{max_total}</text>'
    )

    return f'''<div class="rl-radar-chart" data-color="{color_stroke}">
    <svg viewBox="0 0 {w} {h}" xmlns="http://www.w3.org/2000/svg" class="rl-radar-svg">
      {''.join(grid_lines)}
      {''.join(axis_lines)}
      <polygon points="{data_pts}" fill="{color_fill}" class="rl-radar-polygon" fill-opacity="0" stroke="{color_stroke}" stroke-width="2.5" stroke-dasharray="1000" stroke-dashoffset="1000"/>
      {''.join(dots)}
      {''.join(labels)}
      {center_label}
      <rect class="rl-radar-tooltip-bg" x="0" y="0" width="0" height="0" fill="{COLORS['near_black']}" rx="0" opacity="0"/>
      <text class="rl-radar-tooltip-text" x="0" y="0" fill="#fff" font-size="10" font-weight="700" font-family="Sometype Mono, monospace" opacity="0"></text>
    </svg>
    <div class="rl-radar-label">{esc(label)}</div>
  </div>'''


def build_radar_charts(explanations: dict, course_total: int, opinion_total: int) -> str:
    """Build side-by-side radar charts for Course Profile and Editorial dimensions."""
    course_chart = _radar_svg(COURSE_DIMS, explanations,
                              COLORS['teal'], COLORS['teal'],
                              'Course Profile', course_total, 35, idx_offset=0)
    editorial_chart = _radar_svg(OPINION_DIMS, explanations,
                                 COLORS['gold'], COLORS['gold'],
                                 'Editorial', opinion_total, 35, idx_offset=7)
    return f'<div class="rl-radar-pair">\n{course_chart}\n{editorial_chart}\n</div>'


def build_accordion_html(dims: list, explanations: dict, idx_offset: int = 0) -> str:
    """Build accordion HTML for a list of dimension keys.
    idx_offset shifts data-idx for tile click targeting (0 for course, 7 for editorial)."""
    items = []
    for i, dim in enumerate(dims):
        entry = explanations.get(dim, {})
        score = entry.get('score', 0)
        explanation = entry.get('explanation', '')
        label = DIM_LABELS.get(dim, dim.replace('_', ' ').title())
        pct = int((score / 5) * 100) if score else 0
        has_content = bool(explanation.strip())
        bar_color = score_bar_color(score)

        trigger_class = 'rl-accordion-trigger'
        arrow = '&#x25B6;' if has_content else ''

        item = f'''<div class="rl-accordion-item" data-accordion-idx="{idx_offset + i}">
  <button class="{trigger_class}" aria-expanded="false"{' data-no-content="true"' if not has_content else ''}>
    <span class="rl-accordion-label">{esc(label)}</span>
    <span class="rl-accordion-bar-track"><span class="rl-accordion-bar-fill" style="width:{pct}%;background:{bar_color}"></span></span>
    <span class="rl-accordion-score">{score}/5</span>
    <span class="rl-accordion-arrow">{arrow}</span>
  </button>'''
        if has_content:
            item += f'''
  <div class="rl-accordion-panel">
    <div class="rl-accordion-content">{esc(explanation)}</div>
  </div>'''
        item += '\n</div>'
        items.append(item)

    return '<div class="rl-accordion">\n' + '\n'.join(items) + '\n</div>'


def build_sticky_cta(race_name: str, slug: str = "") -> str:
    """Build sticky bottom CTA bar HTML."""
    plan_href = f"{TRAINING_PLANS_URL}?race={esc(slug)}" if slug else esc(TRAINING_PLANS_URL)
    return f'''<div class="rl-sticky-cta" id="rl-sticky-cta">
  <div class="rl-sticky-cta-inner">
    <span class="rl-sticky-cta-name">{esc(race_name)}</span>
    <div style="display:flex;align-items:center;gap:12px">
      <a href="{plan_href}" class="rl-btn" id="rl-sticky-cta-link"><span id="rl-sticky-cta-text">BUILD MY PLAN &mdash; $15/WK</span></a>
      <button class="rl-sticky-dismiss" onclick="document.getElementById(\'rl-sticky-cta\').style.display=\'none\';try{{sessionStorage.setItem(\'rl-cta-dismissed\',\'1\')}}catch(e){{}}" aria-label="Dismiss">&times;</button>
    </div>
  </div>
</div>'''


def build_inline_js() -> str:
    """Build the inline JavaScript for all interactive features."""
    return r'''<script>
// Accordion toggle (independent mode — multiple can be open)
document.querySelectorAll('.rl-accordion-trigger').forEach(function(trigger) {
  if (trigger.dataset.noContent) return;
  trigger.addEventListener('click', function() {
    var item = trigger.closest('.rl-accordion-item');
    var expanded = item.classList.toggle('is-open');
    trigger.setAttribute('aria-expanded', expanded);
  });
});

// Race day countdown (HTML shows date for crawlers; JS replaces with day count)
(function() {
  var cd = document.querySelector('.rl-countdown');
  if (!cd) return;
  var dateStr = cd.getAttribute('data-date');
  if (!dateStr) return;
  var raceDate = new Date(dateStr + 'T00:00:00');
  var now = new Date();
  var diff = Math.ceil((raceDate - now) / (1000 * 60 * 60 * 24));
  var el = document.getElementById('rl-days-left');
  if (el && diff > 0) {
    el.textContent = diff;
    // Replace "RACE NAME" with "DAYS UNTIL RACE NAME"
    var textNodes = cd.childNodes;
    for (var i = 0; i < textNodes.length; i++) {
      if (textNodes[i].nodeType === 3 && textNodes[i].textContent.trim()) {
        textNodes[i].textContent = ' DAYS UNTIL' + textNodes[i].textContent;
        break;
      }
    }
  } else if (el && diff <= 0) {
    cd.style.display = 'none';
  }
})();

// Hero score counter animation (starts from 0, real score is in HTML for crawlers)
(function() {
  var el = document.querySelector('.rl-hero-score-number');
  if (!el) return;
  var target = parseInt(el.getAttribute('data-target'), 10);
  if (!target) return;
  el.textContent = '0';
  var duration = 1500;
  var start = null;
  function step(ts) {
    if (!start) start = ts;
    var progress = Math.min((ts - start) / duration, 1);
    var ease = 1 - Math.pow(1 - progress, 3);
    el.textContent = Math.round(ease * target);
    if (progress < 1) requestAnimationFrame(step);
  }
  requestAnimationFrame(step);
})();

// Radar chart interactions
(function() {
  // Draw-in animation on scroll
  if ('IntersectionObserver' in window) {
    var radarObs = new IntersectionObserver(function(entries) {
      entries.forEach(function(entry) {
        if (entry.isIntersecting) {
          entry.target.classList.add('is-drawn');
          // Stagger dot reveal
          var dots = entry.target.querySelectorAll('.rl-radar-dot');
          dots.forEach(function(dot, i) {
            dot.style.transitionDelay = (0.8 + i * 0.08) + 's';
          });
          radarObs.unobserve(entry.target);
        }
      });
    }, { threshold: 0.3 });
    document.querySelectorAll('.rl-radar-chart').forEach(function(chart) {
      radarObs.observe(chart);
    });
  }

  // Click + hover on data points
  document.querySelectorAll('.rl-radar-hit').forEach(function(hit) {
    var svg = hit.closest('svg');
    var ring = hit.nextElementSibling ? hit.nextElementSibling.nextElementSibling : null;
    var tooltipBg = svg.querySelector('.rl-radar-tooltip-bg');
    var tooltipText = svg.querySelector('.rl-radar-tooltip-text');

    hit.addEventListener('mouseenter', function() {
      if (ring) ring.style.opacity = '1';
      // Show tooltip
      var label = hit.getAttribute('data-label');
      var score = hit.getAttribute('data-score');
      var txt = label + ': ' + score + '/5';
      var cx = parseFloat(hit.getAttribute('cx'));
      var cy = parseFloat(hit.getAttribute('cy'));
      tooltipText.textContent = txt;
      var tLen = txt.length * 6.5 + 16;
      tooltipText.setAttribute('x', cx);
      tooltipText.setAttribute('y', cy - 22);
      tooltipText.setAttribute('text-anchor', 'middle');
      tooltipText.style.opacity = '1';
      tooltipBg.setAttribute('x', cx - tLen / 2);
      tooltipBg.setAttribute('y', cy - 34);
      tooltipBg.setAttribute('width', tLen);
      tooltipBg.setAttribute('height', 22);
      tooltipBg.style.opacity = '0.9';
    });

    hit.addEventListener('mouseleave', function() {
      if (ring) ring.style.opacity = '0';
      tooltipText.style.opacity = '0';
      tooltipBg.style.opacity = '0';
    });

    // Click → open accordion and scroll
    hit.addEventListener('click', function() {
      var idx = hit.getAttribute('data-accordion-idx');
      var target = document.querySelector('.rl-accordion-item[data-accordion-idx="' + idx + '"]');
      if (!target) return;
      if (!target.classList.contains('is-open')) {
        target.classList.add('is-open');
        var trigger = target.querySelector('.rl-accordion-trigger');
        if (trigger) trigger.setAttribute('aria-expanded', 'true');
      }
      // Brief highlight
      target.classList.add('is-highlighted');
      setTimeout(function() { target.classList.remove('is-highlighted'); }, 1500);
      target.scrollIntoView({ behavior: 'smooth', block: 'center' });
    });
  });
})();

// Stat card count-up on scroll
(function() {
  if (!('IntersectionObserver' in window)) return;
  var statObs = new IntersectionObserver(function(entries) {
    entries.forEach(function(entry) {
      if (!entry.isIntersecting) return;
      var el = entry.target;
      var text = el.textContent.trim();
      var match = text.match(/^[~$]?([\d,]+)/);
      if (!match) { statObs.unobserve(el); return; }
      var prefix = text.substring(0, text.indexOf(match[1]));
      var suffix = text.substring(text.indexOf(match[1]) + match[1].length);
      var target = parseInt(match[1].replace(/,/g, ''), 10);
      if (!target || target > 100000) { statObs.unobserve(el); return; }
      var duration = 1200;
      var start = null;
      function step(ts) {
        if (!start) start = ts;
        var progress = Math.min((ts - start) / duration, 1);
        var ease = 1 - Math.pow(1 - progress, 3);
        var val = Math.round(ease * target);
        el.textContent = prefix + val.toLocaleString() + suffix;
        if (progress < 1) requestAnimationFrame(step);
      }
      requestAnimationFrame(step);
      statObs.unobserve(el);
    });
  }, { threshold: 0.5 });
  document.querySelectorAll('.rl-stat-countable').forEach(function(el) {
    statObs.observe(el);
  });
})();

// Difficulty gauge fill animation
(function() {
  if (!('IntersectionObserver' in window)) return;
  document.querySelectorAll('.rl-difficulty-fill').forEach(function(el) {
    new IntersectionObserver(function(entries, obs) {
      if (entries[0].isIntersecting) {
        el.style.width = el.getAttribute('data-width') + '%';
        obs.unobserve(el);
      }
    }, { threshold: 0.5 }).observe(el);
  });
})();

// Staggered timeline + suffering zone reveals
(function() {
  if (!('IntersectionObserver' in window)) return;
  function staggerReveal(selector, baseDelay) {
    var items = document.querySelectorAll(selector);
    if (!items.length) return;
    var parent = items[0].closest('.rl-section');
    if (!parent) return;
    new IntersectionObserver(function(entries, obs) {
      if (entries[0].isIntersecting) {
        items.forEach(function(item, i) {
          setTimeout(function() { item.classList.add('is-visible'); }, baseDelay + i * 120);
        });
        obs.unobserve(parent);
      }
    }, { threshold: 0.2 }).observe(parent);
  }
  staggerReveal('.rl-timeline-item', 200);
  staggerReveal('.rl-suffering-zone', 100);
})();

// Sticky CTA + scroll fade-in
if ('IntersectionObserver' in window) {
  var stickyCta = document.getElementById('rl-sticky-cta');
  try { if (sessionStorage.getItem('rl-cta-dismissed')) { if (stickyCta) stickyCta.style.display = 'none'; stickyCta = null; } } catch(e) {}
  var hero = document.querySelector('.rl-hero');
  var training = document.getElementById('training');

  var heroVisible = true;
  var trainingVisible = false;

  function updateSticky() {
    if (!stickyCta) return;
    if (!heroVisible && !trainingVisible) {
      stickyCta.classList.add('is-visible');
    } else {
      stickyCta.classList.remove('is-visible');
    }
  }

  if (hero) {
    new IntersectionObserver(function(entries) {
      heroVisible = entries[0].isIntersecting;
      updateSticky();
    }).observe(hero);
  }
  if (training) {
    new IntersectionObserver(function(entries) {
      trainingVisible = entries[0].isIntersecting;
      updateSticky();
    }).observe(training);
  }

  // Scroll fade-in
  var fadeObserver = new IntersectionObserver(function(entries) {
    entries.forEach(function(entry) {
      if (entry.isIntersecting) {
        entry.target.classList.add('is-visible');
        fadeObserver.unobserve(entry.target);
      }
    });
  }, { threshold: 0.15 });

  document.querySelectorAll('.rl-fade-section').forEach(function(el) {
    fadeObserver.observe(el);
  });

  // Back to top button
  var btt = document.getElementById('rl-back-to-top');
  if (btt && hero) {
    new IntersectionObserver(function(entries) {
      if (entries[0].isIntersecting) {
        btt.classList.remove('is-visible');
      } else {
        btt.classList.add('is-visible');
      }
    }).observe(hero);
    btt.addEventListener('click', function() {
      window.scrollTo({ top: 0, behavior: 'smooth' });
    });
  }
}

// News ticker — multi-source (Google News + Reddit)
(function() {
  var ticker = document.getElementById('rl-news-ticker');
  var feed = document.getElementById('rl-news-feed');
  if (!ticker || !feed) return;
  var query = ticker.getAttribute('data-query');
  if (!query) return;

  function parseItem(item) {
    var title = item.title || '';
    var source = item.author || '';
    var dashIdx = title.lastIndexOf(' - ');
    if (!source && dashIdx > 0) {
      source = title.substring(dashIdx + 3).trim();
      title = title.substring(0, dashIdx).trim();
    }
    return { title: title, link: item.link, source: source, date: new Date(item.pubDate) };
  }

  // Use quoted query for exact match in Google News
  var newsUrl = 'https://api.rss2json.com/v1/api.json?rss_url=' + encodeURIComponent(
    'https://news.google.com/rss/search?q=' + encodeURIComponent('"' + query.replace(/\+/g, ' ') + '"') + '&hl=en-US&gl=US&ceid=US:en');
  var redditUrl = 'https://api.rss2json.com/v1/api.json?rss_url=' + encodeURIComponent(
    'https://www.reddit.com/search.rss?q=' + encodeURIComponent('"' + query.replace(/\+/g, ' ') + '"') + '&sort=new&t=year');

  // Build keywords from race name for relevance filtering
  var nameWords = query.replace(/\+/g, ' ').toLowerCase().split(' ').filter(function(w) { return w.length > 2; });

  // Timeout helper — abort fetch after 6 seconds
  function fetchWithTimeout(url, ms) {
    var controller = new AbortController();
    var timer = setTimeout(function() { controller.abort(); }, ms);
    return fetch(url, { signal: controller.signal })
      .then(function(r) { clearTimeout(timer); return r.json(); })
      .catch(function() { clearTimeout(timer); return { items: [] }; });
  }

  Promise.allSettled([
    fetchWithTimeout(newsUrl, 6000),
    fetchWithTimeout(redditUrl, 6000)
  ]).then(function(results) {
    var all = [];
    results.forEach(function(result) {
      if (result.status === 'fulfilled' && result.value.items) {
        result.value.items.forEach(function(item) {
          var parsed = parseItem(item);
          // Relevance filter: title must contain at least one key word from race name
          var titleLow = parsed.title.toLowerCase();
          var relevant = nameWords.some(function(w) { return titleLow.indexOf(w) !== -1; });
          if (relevant) all.push(parsed);
        });
      }
    });

    // Sort by date descending, take top 8
    all.sort(function(a, b) { return b.date - a.date; });
    all = all.slice(0, 8);

    if (all.length === 0) {
      ticker.style.display = 'none';
      return;
    }

    function buildTickerItems(items) {
      var frag = document.createDocumentFragment();
      items.forEach(function(item, i) {
        if (i > 0) {
          var sep = document.createElement('span');
          sep.className = 'rl-news-ticker-sep';
          sep.textContent = '\u25C6';
          frag.appendChild(sep);
        }
        var span = document.createElement('span');
        span.className = 'rl-news-ticker-item';
        var a = document.createElement('a');
        a.href = item.link;
        a.target = '_blank';
        a.rel = 'noopener';
        a.textContent = item.title;
        span.appendChild(a);
        if (item.source) {
          var src = document.createElement('span');
          src.className = 'rl-news-ticker-source';
          src.textContent = item.source;
          span.appendChild(src);
        }
        frag.appendChild(span);
      });
      return frag;
    }
    feed.innerHTML = '';
    feed.appendChild(buildTickerItems(all));
    ticker.style.display = '';
    // Spacer + duplicate for seamless loop
    var spacer = document.createElement('span');
    spacer.style.padding = '0 80px';
    feed.appendChild(spacer);
    feed.appendChild(buildTickerItems(all));
  });
})();

// FAQ accordion toggle
document.querySelectorAll('.rl-faq-question').forEach(function(q) {
  q.addEventListener('click', function() {
    var item = this.parentElement;
    item.classList.toggle('open');
    this.setAttribute('aria-expanded', item.classList.contains('open'));
  });
  q.addEventListener('keydown', function(e) {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      this.click();
    }
  });
});

// CTA click tracking — GA4
(function() {
  if (typeof gtag !== 'function') return;
  document.querySelectorAll('a.rl-btn, a.rl-btn--outline').forEach(function(link) {
    link.addEventListener('click', function() {
      var text = this.textContent.trim().replace(/\s+/g, ' ');
      var href = this.getAttribute('href') || '';
      var cta_type = 'other';
      if (text.indexOf('BUILD MY PLAN') !== -1) cta_type = 'build_plan';
      else if (text.indexOf('PREP KIT') !== -1) cta_type = 'prep_kit';
      else if (text.indexOf('COACHING') !== -1) cta_type = 'coaching';
      var section = this.closest('.rl-section, .rl-sticky-cta');
      var section_id = section ? (section.id || section.className.split(' ')[0]) : 'unknown';
      gtag('event', 'cta_click', {
        cta_type: cta_type,
        cta_text: text.substring(0, 50),
        cta_section: section_id,
        cta_href: href
      });
    });
  });
})();

// Email capture form — prep kit CTA
(function() {
  var WORKER_URL='https://fueling-lead-intake.gravelgodcoaching.workers.dev';
  var LS_KEY='rl-pk-fueling';
  var EXPIRY_DAYS=90;
  var form=document.getElementById('rl-email-capture-form');
  if(!form) return;

  /* Check if already captured */
  try{
    var cached=JSON.parse(localStorage.getItem(LS_KEY)||'null');
    if(cached&&cached.email&&cached.exp>Date.now()){
      /* Already captured — show success state */
      form.style.display='none';
      var success=document.getElementById('rl-email-capture-success');
      if(success) success.style.display='block';
      return;
    }
  }catch(e){}

  form.addEventListener('submit',function(e){
    e.preventDefault();
    var email=form.email.value.trim();
    if(!email||!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)){
      alert('Please enter a valid email address.');return;
    }
    if(form.website&&form.website.value) return;
    /* Cache email */
    try{
      localStorage.setItem(LS_KEY,JSON.stringify({email:email,exp:Date.now()+EXPIRY_DAYS*86400000}));
    }catch(ex){}
    /* POST to Worker */
    var payload={
      email:email,
      race_slug:form.race_slug.value,
      race_name:form.race_name.value,
      source:form.source.value,
      website:form.website.value
    };
    fetch(WORKER_URL,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)}).catch(function(){});
    /* GA4 */
    if(typeof gtag==='function'){
      gtag('event','email_capture',{race_slug:form.race_slug.value,source:'race_profile'});
    }
    /* Show success state */
    form.style.display='none';
    var success=document.getElementById('rl-email-capture-success');
    if(success) success.style.display='block';
  });
})();

// Inline review form
(function() {
  var WORKER_URL='https://review-intake.gravelgodcoaching.workers.dev';
  var form=document.getElementById('rl-review-form');
  if(!form) return;

  /* Star rating interaction */
  var starBtns=document.querySelectorAll('.rl-review-star-btn');
  var starsInput=document.getElementById('rl-review-stars-val');
  starBtns.forEach(function(btn){
    btn.addEventListener('click',function(){
      var val=parseInt(this.getAttribute('data-star'));
      starsInput.value=val;
      starBtns.forEach(function(b){
        var active=parseInt(b.getAttribute('data-star'))<=val;
        b.classList.toggle('is-active',active);
        b.setAttribute('aria-checked',active?'true':'false');
      });
    });
    btn.addEventListener('mouseenter',function(){
      var val=parseInt(this.getAttribute('data-star'));
      starBtns.forEach(function(b){
        if(parseInt(b.getAttribute('data-star'))<=val) b.style.color='var(--rl-color-gold)';
        else b.style.color='var(--rl-color-tan)';
      });
    });
    btn.addEventListener('mouseleave',function(){
      starBtns.forEach(function(b){b.style.color='';});
    });
  });

  /* Character counts on textareas */
  document.querySelectorAll('.rl-review-charcount').forEach(function(el){
    var ta=document.getElementById(el.getAttribute('data-for'));
    if(ta){ta.addEventListener('input',function(){el.textContent=ta.value.length+'/500';});}
  });

  form.addEventListener('submit',function(e){
    e.preventDefault();
    var email=form.email.value.trim();
    var stars=parseInt(starsInput.value);
    if(!stars||stars<1||stars>5){alert('Please select a star rating.');return;}
    if(!email||!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)){alert('Please enter a valid email.');return;}
    if(form.website&&form.website.value) return;

    var payload={
      email:email,
      source:'race_review',
      race_slug:form.race_slug.value,
      race_name:form.race_name.value,
      stars:stars,
      year_raced:form.year_raced.value,
      would_race_again:form.would_race_again.value,
      finish_position:form.finish_position.value,
      best:form.best.value,
      worst:form.worst.value,
      website:form.website.value
    };
    fetch(WORKER_URL,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)}).catch(function(){});
    if(typeof gtag==='function') gtag('event','review_submit',{race_slug:form.race_slug.value,stars:stars});

    /* Show success, clear char counts */
    document.querySelectorAll('.rl-review-charcount').forEach(function(el){el.textContent='0/500';});
    document.getElementById('rl-review-form-wrap').querySelector('.rl-review-form').style.display='none';
    document.getElementById('rl-review-success').style.display='block';
  });
})();

// Lite-YouTube facade — click to load iframe (zero perf cost until interaction)
document.querySelectorAll('.rl-lite-youtube').forEach(function(el) {
  el.addEventListener('click', function() {
    var id = el.getAttribute('data-videoid');
    if (!id) return;
    var iframe = document.createElement('iframe');
    iframe.src = 'https://www.youtube-nocookie.com/embed/' + id + '?autoplay=1&rel=0';
    iframe.allow = 'accelerometer; autoplay; encrypted-media; gyroscope; picture-in-picture';
    iframe.allowFullscreen = true;
    iframe.loading = 'lazy';
    el.textContent = '';
    el.appendChild(iframe);
  });
});

/* ── Train for Race: Workout panel toggle ── */
(function() {
  var toggleBtn = document.getElementById('rl-pack-toggle-btn');
  var panel = document.getElementById('rl-pack-workouts-panel');
  var toggleText = document.getElementById('rl-pack-toggle-text');
  if (!toggleBtn || !panel) return;
  // Read actual workout count from panel instead of hardcoding
  var workoutCount = panel.querySelectorAll('.rl-pack-workout').length;
  var seeText = 'SEE ' + workoutCount + ' SAMPLE WORKOUTS';
  var hideText = 'HIDE SAMPLE WORKOUTS';
  // Set initial text from actual count (defense against generator/JS mismatch)
  if (toggleText) toggleText.textContent = seeText;
  toggleBtn.addEventListener('click', function() {
    var expanded = toggleBtn.getAttribute('aria-expanded') === 'true';
    if (expanded) {
      panel.style.display = 'none';
      toggleBtn.setAttribute('aria-expanded', 'false');
      if (toggleText) toggleText.textContent = seeText;
      toggleBtn.focus();
    } else {
      panel.style.display = 'block';
      toggleBtn.setAttribute('aria-expanded', 'true');
      if (toggleText) toggleText.textContent = hideText;
      // Move focus to panel for screen readers
      panel.setAttribute('tabindex', '-1');
      panel.focus();
      panel.removeAttribute('tabindex');
      if (typeof gtag === 'function') {
        gtag('event', 'workouts_panel_expand', {
          race_slug: (window.__GG_RACE_DATA__ || {}).slug || '',
          workout_count: workoutCount
        });
      }
    }
  });
})();

/* ── Train for Race: Workout expand/collapse ── */
document.querySelectorAll('.rl-pack-workout').forEach(function(card) {
  card.addEventListener('click', function(e) {
    if (e.target.closest('a')) return;
    var detail = this.querySelector('.rl-pack-workout-detail');
    var wasActive = this.classList.contains('active');
    // Close all others
    document.querySelectorAll('.rl-pack-workout').forEach(function(c) {
      c.classList.remove('active');
      var d = c.querySelector('.rl-pack-workout-detail');
      if (d) d.style.display = 'none';
    });
    if (!wasActive) {
      this.classList.add('active');
      if (detail) detail.style.display = 'block';
    }
  });
});

/* ── Plan Preview Mini-Configurator ── */
(function() {
  var rd = window.__GG_RACE_DATA__;
  if (!rd) return;
  var btn = document.getElementById('rl-cfg-btn');
  var dateInput = document.getElementById('rl-cfg-date');
  if (!btn || !dateInput) return;
  var previewActive = false;

  // Pre-fill race date from date_specific — handles multiple formats:
  //   "2026: June 6"                          → June 6, 2026
  //   "2026: June 6-7"                        → June 6, 2026 (first day)
  //   "July 20, 2026 (subject to ...)"        → July 20, 2026
  //   "2026: September 20 - 21"               → September 20, 2026
  //   "TBD" / "check website"                 → no pre-fill
  function parseRaceDate(ds) {
    if (!ds) return null;
    var parsed = null;
    // Format 1: "YYYY: Month Day..." (most common)
    var m1 = ds.match(/(\d{4}):\s*([A-Za-z]+)\s+(\d{1,2})/);
    if (m1) {
      parsed = new Date(m1[2] + ' ' + m1[3] + ', ' + m1[1]);
      if (!isNaN(parsed.getTime())) return parsed;
    }
    // Format 2: "Month Day, YYYY" anywhere in string
    var m2 = ds.match(/([A-Za-z]+)\s+(\d{1,2}),?\s*(\d{4})/);
    if (m2) {
      parsed = new Date(m2[1] + ' ' + m2[2] + ', ' + m2[3]);
      if (!isNaN(parsed.getTime())) return parsed;
    }
    // Format 3: ISO-ish "YYYY-MM-DD" anywhere
    var m3 = ds.match(/(\d{4})-(\d{2})-(\d{2})/);
    if (m3) {
      parsed = new Date(m3[1] + '-' + m3[2] + '-' + m3[3] + 'T00:00:00');
      if (!isNaN(parsed.getTime())) return parsed;
    }
    return null;
  }
  var raceDateParsed = parseRaceDate(rd.date_specific);
  if (raceDateParsed) {
    var y = raceDateParsed.getFullYear();
    var mo = String(raceDateParsed.getMonth() + 1).padStart(2, '0');
    var da = String(raceDateParsed.getDate()).padStart(2, '0');
    dateInput.value = y + '-' + mo + '-' + da;
  }

  // Level config: VO2 range, threshold range (matches nate_workout_generator.py scaling)
  var LEVELS = {
    beginner:     { vo2: '105\u2013108% FTP', thr: '92\u201396% FTP'  },
    intermediate: { vo2: '108\u2013112% FTP', thr: '96\u2013100% FTP' },
    advanced:     { vo2: '112\u2013118% FTP', thr: '100\u2013105% FTP'},
    elite:        { vo2: '115\u2013120% FTP', thr: '105\u2013108% FTP'}
  };

  // Hours config: quality sessions, endurance rides, avg hours
  var HOURS = {
    '6-8':  { quality: 2, endurance: 2, avg: 7  },
    '8-12': { quality: 3, endurance: 2, avg: 10 },
    '12-16':{ quality: 3, endurance: 3, avg: 14 },
    '16+':  { quality: 4, endurance: 3, avg: 18 }
  };

  // Category to phase mapping — names must match web/race-packs/*.json exactly
  // Source of truth: scripts/generate_race_pack_previews.py weight matrix (19 categories)
  var PHASE_MAP = {
    'Endurance': 'base', 'HVLI_Extended': 'base', 'LT1_MAF': 'base',
    'Tempo': 'base', 'Cadence_Work': 'base',
    'TT_Threshold': 'build', 'Over_Under': 'build', 'Mixed_Climbing': 'build',
    'SFR_Muscle_Force': 'build', 'Blended': 'build', 'G_Spot': 'build',
    'Norwegian_Double': 'build',
    'VO2max': 'peak', 'Durability': 'peak', 'Race_Simulation': 'peak',
    'Gravel_Specific': 'peak', 'Anaerobic_Capacity': 'peak',
    'Critical_Power': 'peak', 'Sprint_Neuromuscular': 'peak'
  };

  var PHASE_LABELS = { base: 'BASE PHASE', build: 'BUILD PHASE', peak: 'PEAK PHASE' };
  var PHASE_CSS = { base: 'rl-cfg-phase-base', build: 'rl-cfg-phase-build', peak: 'rl-cfg-phase-peak' };

  btn.addEventListener('click', function() {
    var level = document.getElementById('rl-cfg-level').value;
    var hours = document.getElementById('rl-cfg-hours').value;
    var raceDateStr = dateInput.value;

    if (!raceDateStr) {
      dateInput.focus();
      return;
    }

    var raceDate = new Date(raceDateStr + 'T00:00:00');
    var today = new Date();
    today.setHours(0, 0, 0, 0);
    var diffMs = raceDate.getTime() - today.getTime();
    var weeksRaw = Math.ceil(diffMs / (7 * 24 * 60 * 60 * 1000));
    var weeks = Math.max(4, weeksRaw);

    // Phase split
    var taper = 1;
    var remaining = weeks - taper;
    var base = Math.round(remaining * 0.4);
    var build = Math.round(remaining * 0.35);
    var peak = remaining - base - build;
    if (peak < 1) { peak = 1; base = Math.max(1, base - 1); }

    // Price
    var price = Math.min(249, Math.max(60, weeks * 15));

    // Session structure
    var hCfg = HOURS[hours] || HOURS['8-12'];
    var lCfg = LEVELS[level] || LEVELS['intermediate'];
    var sessionsPerWeek = hCfg.quality + hCfg.endurance + 1; // +1 for recovery/easy ride
    var totalWorkouts = weeks * sessionsPerWeek;

    // Build summary
    var summaryEl = document.getElementById('rl-cfg-summary');
    var titleEl = document.getElementById('rl-cfg-summary-title');
    var timelineEl = document.getElementById('rl-cfg-timeline');
    var barEl = document.getElementById('rl-cfg-timeline-bar');
    var detailsEl = document.getElementById('rl-cfg-details');

    titleEl.textContent = 'YOUR ' + weeks + '-WEEK ' + rd.race_name.toUpperCase() + ' PLAN';

    // Timeline text
    timelineEl.textContent = '';
    var phases = [
      { name: 'BASE', wk: base },
      { name: 'BUILD', wk: build },
      { name: 'PEAK', wk: peak },
      { name: 'TAPER', wk: taper }
    ];
    phases.forEach(function(p, idx) {
      if (idx > 0) {
        var sep = document.createElement('span');
        sep.className = 'rl-cfg-timeline-sep';
        sep.textContent = '\u25b8';
        timelineEl.appendChild(sep);
      }
      var sp = document.createElement('span');
      sp.textContent = p.name + ' (' + p.wk + 'wk)';
      timelineEl.appendChild(sp);
    });

    // Timeline bar (proportional widths)
    barEl.textContent = '';
    var colors = ['base', 'build', 'peak', 'taper'];
    phases.forEach(function(p, idx) {
      var seg = document.createElement('div');
      seg.className = 'rl-cfg-bar-' + colors[idx];
      seg.style.flex = String(p.wk);
      barEl.appendChild(seg);
    });

    // Details text
    detailsEl.textContent = '';
    var line1 = document.createElement('div');
    line1.textContent = hCfg.quality + ' quality sessions + ' + hCfg.endurance + ' endurance rides/week \u00b7 ' + hCfg.avg + ' hrs/week';
    detailsEl.appendChild(line1);
    var line2 = document.createElement('div');
    line2.textContent = totalWorkouts + ' structured workouts \u00b7 ZWO files for Zwift/Wahoo/Garmin';
    detailsEl.appendChild(line2);

    summaryEl.style.display = 'block';

    // Phase badges on workout cards
    document.querySelectorAll('.rl-pack-workout').forEach(function(card) {
      var cat = card.getAttribute('data-workout-cat') || '';
      var phase = PHASE_MAP[cat] || 'build';
      var badge = card.querySelector('.rl-cfg-phase-badge');
      if (badge) {
        badge.textContent = PHASE_LABELS[phase] || 'BUILD PHASE';
        badge.className = 'rl-cfg-phase-badge ' + (PHASE_CSS[phase] || 'rl-cfg-phase-build');
        badge.style.display = 'block';
      }
      // Level annotation
      var note = card.querySelector('.rl-cfg-level-note');
      if (note) {
        note.textContent = 'YOUR TARGETS: VO2 at ' + lCfg.vo2 + ' \u00b7 Threshold at ' + lCfg.thr;
        note.style.display = 'block';
      }
    });

    // Update default CTA to personalized CTA
    var defaultCta = document.getElementById('rl-pack-cta-default');
    var cfgCta = document.getElementById('rl-cfg-cta');
    var cfgCtaLink = document.getElementById('rl-cfg-cta-link');
    var cfgCtaDetail = document.getElementById('rl-cfg-cta-detail');
    if (defaultCta) {
      defaultCta.style.display = 'none';
      defaultCta.setAttribute('aria-hidden', 'true');
    }
    if (cfgCta && cfgCtaLink && cfgCtaDetail) {
      var ctaText = 'GET YOUR ' + weeks + '-WEEK ' + rd.race_name.toUpperCase() + ' PLAN \u2014 $' + price;
      cfgCtaLink.textContent = ctaText;
      cfgCtaLink.removeAttribute('tabindex');
      // Pass configurator selections to questionnaire for pre-population
      cfgCtaLink.href = '/questionnaire/?race=' + encodeURIComponent(rd.slug) +
        '&level=' + encodeURIComponent(level) +
        '&hours=' + encodeURIComponent(hours) +
        '&weeks=' + weeks;
      cfgCtaDetail.textContent = totalWorkouts + ' workouts \u00b7 ZWO files \u00b7 Phase-periodized for ' + rd.race_name;
      cfgCta.style.display = 'block';
      cfgCta.removeAttribute('aria-hidden');
    }

    // Update sticky CTA
    var stickyText = document.getElementById('rl-sticky-cta-text');
    var stickyLink = document.getElementById('rl-sticky-cta-link');
    if (stickyText) {
      stickyText.textContent = weeks + '-WEEK PLAN \u2014 $' + price;
    }
    if (stickyLink) {
      stickyLink.href = '/questionnaire/?race=' + encodeURIComponent(rd.slug) +
        '&level=' + encodeURIComponent(level) +
        '&hours=' + encodeURIComponent(hours) +
        '&weeks=' + weeks;
    }

    previewActive = true;
    btn.textContent = 'PREVIEW MY PLAN';

    // GA4 events
    if (typeof gtag === 'function') {
      gtag('event', 'configurator_preview', {
        race_slug: rd.slug,
        level: level,
        hours: hours,
        weeks: weeks,
        price: price
      });
    }
  });

  // Track configurator interactions + mark preview stale when inputs change
  ['rl-cfg-level', 'rl-cfg-hours', 'rl-cfg-date'].forEach(function(id) {
    var el = document.getElementById(id);
    if (el) {
      el.addEventListener('change', function() {
        // Mark preview as stale — hide summary and reset badges
        if (previewActive) {
          var sum = document.getElementById('rl-cfg-summary');
          if (sum) sum.style.display = 'none';
          document.querySelectorAll('.rl-cfg-phase-badge').forEach(function(b) { b.style.display = 'none'; });
          document.querySelectorAll('.rl-cfg-level-note').forEach(function(n) { n.style.display = 'none'; });
          var defCta = document.getElementById('rl-pack-cta-default');
          var cfgC = document.getElementById('rl-cfg-cta');
          if (defCta) { defCta.style.display = ''; defCta.removeAttribute('aria-hidden'); }
          if (cfgC) { cfgC.style.display = 'none'; cfgC.setAttribute('aria-hidden', 'true'); }
          var stickyT = document.getElementById('rl-sticky-cta-text');
          if (stickyT) stickyT.textContent = 'BUILD MY PLAN \u2014 $15/WK';
          previewActive = false;
          btn.textContent = 'UPDATE PREVIEW';
        }
        if (typeof gtag === 'function') {
          gtag('event', 'configurator_interact', {
            race_slug: rd.slug,
            field: id.replace('rl-cfg-', ''),
            value: el.value
          });
        }
      });
    }
  });

  // Track personalized CTA clicks
  var cfgCtaLinkEl = document.getElementById('rl-cfg-cta-link');
  if (cfgCtaLinkEl) {
    cfgCtaLinkEl.addEventListener('click', function() {
      if (typeof gtag === 'function') {
        gtag('event', 'configurator_cta_click', {
          race_slug: rd.slug,
          cta_text: cfgCtaLinkEl.textContent
        });
      }
    });
  }
})();
</script>'''


# ── Phase 3D: JSON-LD Schema ──────────────────────────────────

def build_sports_event_jsonld(rd: dict) -> Optional[dict]:
    """Build SportsEvent JSON-LD from normalized race data.

    Returns None when startDate cannot be parsed (TBD, check website, etc.)
    — omitting SportsEvent entirely is better than emitting it without a date,
    which triggers GSC "missing startDate" errors with no rich-result upside.
    """
    # Parse ISO date via shared helper
    date_specific = rd['vitals'].get('date_specific', '')
    start_date, end_date = parse_event_dates(date_specific)

    # No parseable date → skip SportsEvent entirely
    if not start_date:
        return None

    jsonld = {
        "@context": "https://schema.org",
        "@type": "SportsEvent",
        "name": rd['name'],
        "description": rd['tagline'],
        "sport": "Gravel Cycling",
        "eventStatus": "https://schema.org/EventScheduled",
        "eventAttendanceMode": "https://schema.org/OfflineEventAttendanceMode",
        "startDate": start_date,
        "endDate": end_date,
    }

    # Location with PostalAddress — detect country from location string
    location = rd['vitals'].get('location', '')
    if location and location != '--':
        parts = [p.strip() for p in location.split(',')]
        country = detect_country(location)
        place = {"@type": "Place", "name": location}
        if len(parts) >= 2:
            place["address"] = {
                "@type": "PostalAddress",
                "addressLocality": parts[0],
                "addressRegion": parts[1] if len(parts) > 2 else parts[-1],
                "addressCountry": country,
            }
        else:
            # Single-part location — still emit address to satisfy GSC
            place["address"] = {
                "@type": "PostalAddress",
                "addressLocality": parts[0],
                "addressCountry": country,
            }
        jsonld["location"] = place

    # Image array: OG image first, then race photos (not GIFs)
    image_urls = [f"{SITE_BASE_URL}/og/{rd['slug']}.jpg"]
    for photo in rd.get('photos', []):
        photo_url = photo.get('url', '')
        if photo_url and not photo.get('gif'):
            image_urls.append(f"{SITE_BASE_URL}{photo_url}")
    jsonld["image"] = image_urls if len(image_urls) > 1 else image_urls[0]

    # Organizer from history.founder — skip generic stub text
    founder = rd.get('history', {}).get('founder', '')
    official_site = rd['logistics'].get('official_site', '')
    if founder and not founder.endswith('organizers') and founder != 'Unknown':
        org = {"@type": "Person", "name": founder}
        if official_site and official_site.startswith('http'):
            org["url"] = official_site
        jsonld["organizer"] = org

    # Parse price — supports $, €, £ and "NNN EUR/GBP" formats
    reg = rd['vitals'].get('registration', '')
    price_match = re.search(r'\$(\d+)', reg)
    euro_match = re.search(r'€\s*(\d+)', reg)
    gbp_match = re.search(r'£\s*(\d+)', reg)
    eur_text_match = re.search(r'(\d+)\s*EUR', reg)
    gbp_text_match = re.search(r'(\d+)\s*GBP', reg)
    if price_match or euro_match or gbp_match or eur_text_match or gbp_text_match:
        if price_match:
            price, currency = price_match.group(1), "USD"
        elif euro_match:
            price, currency = euro_match.group(1), "EUR"
        elif eur_text_match:
            price, currency = eur_text_match.group(1), "EUR"
        elif gbp_match:
            price, currency = gbp_match.group(1), "GBP"
        else:
            price, currency = gbp_text_match.group(1), "GBP"
        offer = {
            "@type": "Offer",
            "price": price,
            "priceCurrency": currency,
            "availability": "https://schema.org/LimitedAvailability",
        }
        if official_site and official_site.startswith('http'):
            offer["url"] = official_site
        jsonld["offers"] = offer

    # Racer Rating → AggregateRating (only with 3+ ratings)
    racer_rating = rd.get('racer_rating', {})
    if racer_rating.get('total_ratings', 0) >= RACER_RATING_THRESHOLD and racer_rating.get('star_average'):
        agg = {
            "@type": "AggregateRating",
            "ratingValue": str(round(racer_rating['star_average'], 1)),
            "bestRating": "5",
            "worstRating": "1",
            "ratingCount": str(racer_rating['total_ratings']),
        }
        total_reviews = racer_rating.get('total_reviews', 0)
        if total_reviews > 0:
            agg["reviewCount"] = str(total_reviews)
        jsonld["aggregateRating"] = agg

    if official_site and official_site.startswith('http'):
        jsonld["url"] = official_site

    return jsonld


def build_faq_jsonld(rd: dict) -> Optional[dict]:
    """Build FAQPage JSON-LD from top rating explanations + verdict."""
    explanations = rd.get('explanations', {})
    name = rd['name']

    questions = []
    # Pick top 5 dimensions by FAQ_PRIORITY that have explanations
    for dim in FAQ_PRIORITY:
        if len(questions) >= 5:
            break
        entry = explanations.get(dim, {})
        expl = entry.get('explanation', '').strip()
        if not expl:
            continue
        q_template = FAQ_TEMPLATES.get(dim, f'What about {dim} at {{name}}?')
        questions.append({
            "@type": "Question",
            "name": q_template.format(name=name),
            "acceptedAnswer": {
                "@type": "Answer",
                "text": expl,
            }
        })

    # Add verdict question
    should_race = rd['final_verdict'].get('should_you_race', '').strip()
    if should_race:
        questions.append({
            "@type": "Question",
            "name": f"Should I race {name}?",
            "acceptedAnswer": {
                "@type": "Answer",
                "text": should_race,
            }
        })

    if not questions:
        return None

    return {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": questions,
    }


# ── Phase 3: Section Builders ─────────────────────────────────

def build_hero(rd: dict) -> str:
    """Build clean editorial hero — race name + score masthead."""
    score = rd['overall_score']

    series = rd.get('series', {})
    series_badge = ''
    if series.get('id') and series.get('name'):
        series_badge = f' <a href="/race/series/{esc(series["id"])}/" class="rl-series-badge">{esc(series["name"]).upper()} SERIES</a>'

    # Build vitals line: Location · Month · Distance · Elevation
    vitals = rd.get('vitals', {})
    parts = []
    location = vitals.get('location', '')
    if location:
        parts.append(esc(location))
    month = vitals.get('month', '')
    date_specific = vitals.get('date_specific', '')
    if date_specific:
        parts.append(esc(date_specific))
    elif month:
        parts.append(esc(month))
    dist = vitals.get('distance_mi')
    if dist:
        parts.append(f"{dist} mi")
    elev = vitals.get('elevation_ft')
    if elev:
        try:
            parts.append(f"{int(elev):,} ft")
        except (ValueError, TypeError):
            parts.append(f"{elev} ft")
    vitals_line = " &middot; ".join(parts)

    return f'''<section class="rl-hero">
  <div class="rl-hero-content">
    <span class="rl-hero-tier">{esc(rd['tier_label'])}</span>{series_badge}
    <h1>{esc(rd['name'])}</h1>
    <div class="rl-hero-vitals">{vitals_line}</div>
  </div>
  <div class="rl-hero-score">
    <div class="rl-hero-score-number" data-target="{score}">{score}</div>
    <div class="rl-hero-score-label">GG SCORE</div>
  </div>
</section>'''


def build_photos_section(rd: dict) -> str:
    """Build photo gallery section if race has photos."""
    photos = rd.get('photos', [])
    if not photos:
        return ''
    # Exclude primary (already used in hero) and GIFs (shown in Course section)
    gallery = [p for p in photos if not p.get('primary') and not p.get('gif')][:4]
    if not gallery:
        return ''
    items = []
    for p in gallery:
        alt = esc(p.get('alt', rd['name']))
        credit = p.get('credit', '')
        credit_html = f'<span class="rl-photo-credit">Photo: {esc(credit)}</span>' if credit else ''
        items.append(
            f'<figure class="rl-photo-item">'
            f'<img src="{esc(p["url"])}" alt="{alt}" loading="lazy" width="600" height="400">'
            f'{credit_html}'
            f'</figure>'
        )
    return f'''<section class="rl-photos" id="photos">
  <h2 class="rl-section-title">Photos</h2>
  <div class="rl-photo-grid">{"".join(items)}</div>
</section>'''


def build_toc(active_sections=None) -> str:
    """Build table of contents nav.

    If *active_sections* is provided, only show links whose anchor id is
    in the set.  Pass ``None`` to show all links (backward-compatible).
    """
    all_links = [
        ('course', '01 Course Overview'),
        ('history', '02 Facts &amp; History'),
        ('route', '03 The Course'),
        ('from-the-field', '04 From the Field'),
        ('ratings', '05 The Ratings'),
        ('verdict', '06 Final Verdict'),
        ('training', '07 Training'),
        ('train-for-race', '08 Train for This Race'),
        ('logistics', '09 Race Logistics'),
        ('tires', '10 Tire Picks'),
        ('citations', '11 Sources'),
    ]
    links = [(href, label) for href, label in all_links
             if active_sections is None or href in active_sections]
    items = '\n  '.join(f'<a href="#{href}">{label}</a>' for href, label in links)
    return f'<nav class="rl-toc" aria-label="Table of contents">\n  {items}\n</nav>'


def _extract_state(location: str) -> str:
    """Extract state/country from location string like 'Emporia, Kansas'."""
    if not location:
        return ''
    m = re.match(r'.+,\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*|[A-Z]{2})', location)
    return m.group(1) if m else ''


def _build_nearby_races(rd: dict, race_index: list) -> str:
    """Build 'More in [State]' contextual links for in-content SEO."""
    if not race_index:
        return ''
    location = rd['vitals'].get('location', '')
    state = _extract_state(location)
    if not state:
        return ''
    slug = rd['slug']
    # Find other races in same state, prefer higher-tier races
    nearby = []
    for r in race_index:
        if r.get('slug') == slug:
            continue
        r_loc = r.get('location', '')
        if _extract_state(r_loc) == state:
            nearby.append(r)
    if not nearby:
        return ''
    # Sort by score descending, take top 3
    nearby.sort(key=lambda r: r.get('overall_score', 0), reverse=True)
    links = []
    for r in nearby[:3]:
        links.append(f'<a href="/race/{esc(r["slug"])}/">{esc(r["name"])}</a>')
    return f'''<div class="rl-nearby-races">
        <span class="rl-nearby-label">MORE IN {esc(state.upper())}:</span> {" &middot; ".join(links)}
      </div>'''


def build_course_overview(rd: dict, race_index: list = None) -> str:
    """Build [01] Course Overview section — tagline lead + map + stat cards."""
    v = rd['vitals']

    # Tagline — relocated from hero as editorial lead paragraph
    tagline = rd.get('tagline', '').strip()
    tagline_html = ''
    if tagline:
        tagline_html = f'<p class="rl-overview-tagline">{esc(tagline)}</p>'

    # Map embed — prefer explicit ridewithgps_id, fall back to extracting from map_url
    map_html = ''
    rwgps_id = rd['course'].get('ridewithgps_id')
    if not rwgps_id:
        map_url = rd['course'].get('map_url', '') or ''
        m = re.search(r'ridewithgps\.com/routes/(\d+)', map_url)
        if m:
            rwgps_id = m.group(1)
    rwgps_name = rd['course'].get('ridewithgps_name', '')
    if rwgps_id:
        map_html = f'''<div class="rl-map-embed">
        <iframe src="https://ridewithgps.com/embeds?type=route&amp;id={esc(rwgps_id)}&amp;sampleGraph=true&amp;title={esc(rwgps_name)}" title="Course map for {esc(rd['name'])}" allowfullscreen loading="lazy"></iframe>
      </div>'''

    # Stat cards — (value, label, countable) where countable means "animate the number"
    stats = [
        (v.get('distance', '--'), 'Distance', True),
        (v.get('elevation', '--'), 'Elevation', True),
        (v.get('location', '--'), 'Location', False),
        (v.get('date', '--'), 'Date', False),
        (v.get('field_size', '--'), 'Field Size', True),
    ]
    # Add entry cost if available
    if v.get('entry_cost'):
        stats.append((v['entry_cost'], 'Entry Cost', True))
    else:
        stats.append(('--', 'Entry Cost', False))

    cards = '\n      '.join(
        f'''<div class="rl-stat-card">
          <div class="rl-stat-value{' rl-stat-countable' if countable else ''}">{esc(val)}</div>
          <div class="rl-stat-label">{esc(label)}</div>
        </div>'''
        for val, label, countable in stats
    )

    # Difficulty gauge — based on course profile (technicality + elevation + climate + adventure)
    hard_dims = ['technicality', 'elevation', 'climate', 'adventure']
    hard_score = sum(rd['explanations'].get(d, {}).get('score', 0) for d in hard_dims)
    hard_pct = int((hard_score / 20) * 100)
    if hard_pct >= 80:
        hard_label, hard_color = 'BRUTAL', COLORS['near_black']
    elif hard_pct >= 60:
        hard_label, hard_color = 'HARD', COLORS['primary_brown']
    elif hard_pct >= 40:
        hard_label, hard_color = 'MODERATE', COLORS['gold']
    else:
        hard_label, hard_color = 'ACCESSIBLE', COLORS['teal']

    # Calendar export — Google Calendar link + .ics download
    cal_html = ''
    date_specific = v.get('date_specific', '')
    cal_start, _cal_end = parse_event_dates(date_specific)

    if cal_start:
        iso_date = cal_start.replace('-', '')
        race_title = rd['name']
        location_str = v.get('location', '')
        from urllib.parse import quote
        gcal_url = (
            f"https://calendar.google.com/calendar/render?action=TEMPLATE"
            f"&text={quote(race_title)}"
            f"&dates={iso_date}/{iso_date}"
            f"&details={quote(f'Gravel race — {race_title}. More info at roadlabs.cc')}"
            f"&location={quote(location_str)}"
        )
        ics_data = (
            f"BEGIN:VCALENDAR\\nVERSION:2.0\\nPRODID:-//GravelGod//EN\\n"
            f"BEGIN:VEVENT\\n"
            f"DTSTART;VALUE=DATE:{iso_date}\\n"
            f"DTEND;VALUE=DATE:{iso_date}\\n"
            f"SUMMARY:{race_title}\\n"
            f"LOCATION:{location_str}\\n"
            f"DESCRIPTION:Gravel race. More info at roadlabs.cc\\n"
            f"END:VEVENT\\nEND:VCALENDAR"
        )
        cal_html = f'''<div class="rl-calendar-export">
        <a href="{esc(gcal_url)}" target="_blank" rel="noopener" class="rl-cal-btn rl-cal-btn--google">+ Google Calendar</a>
        <a href="#" class="rl-cal-btn rl-cal-btn--ics" onclick="var b=new Blob(['{ics_data}'.replace(/\\\\n/g,'\\n')],{{type:'text/calendar'}});var a=document.createElement('a');a.href=URL.createObjectURL(b);a.download='{esc(rd["slug"])}.ics';a.click();return false;">Download .ics</a>
      </div>'''

    gauge_html = f'''<div class="rl-difficulty-gauge">
        <div class="rl-difficulty-header">
          <span class="rl-difficulty-title">DIFFICULTY</span>
          <span class="rl-difficulty-label">{hard_label}</span>
        </div>
        <div class="rl-difficulty-track">
          <div class="rl-difficulty-fill" data-width="{hard_pct}" style="width:0%;background:{hard_color}"></div>
        </div>
        <div class="rl-difficulty-scale">
          <span>ACCESSIBLE</span><span>MODERATE</span><span>HARD</span><span>BRUTAL</span>
        </div>
      </div>'''

    nearby_html = _build_nearby_races(rd, race_index or [])

    return f'''<section id="course" class="rl-section rl-fade-section">
    <div class="rl-section-header">
      <span class="rl-section-kicker">[01]</span>
      <h2 class="rl-section-title">Course Overview</h2>
    </div>
    <div class="rl-section-body">
      {tagline_html}
      {map_html}
      <div class="rl-stat-grid">
      {cards}
      </div>
      {cal_html}
      {gauge_html}
      {nearby_html}
    </div>
  </section>'''


def build_history(rd: dict) -> str:
    """Build [02] Facts & History section."""
    h = rd['history']

    # Skip entirely if no meaningful content
    if not h.get('origin_story') and not h.get('notable_moments') and not h.get('reputation'):
        return ''

    body_parts = []

    # Origin story — suppress generic stub text (< 60 chars ending in "event." etc.)
    origin = h.get('origin_story', '').strip()
    is_stub_origin = len(origin) < 60 and origin.endswith(('event.', 'race.', 'community.'))
    if origin and not is_stub_origin:
        founded = f" Founded in {h['founded']}." if h.get('founded') else ''
        # Suppress generic "X organizers" founder text
        founder_text = h.get('founder', '')
        founder = f" By {founder_text}." if founder_text and founder_text != 'Unknown' and not founder_text.endswith('organizers') else ''
        body_parts.append(f'<div class="rl-prose"><p>{esc(origin)}{esc(founded)}{esc(founder)}</p></div>')

    # Reputation
    if h.get('reputation'):
        body_parts.append(f'<div class="rl-prose"><p><strong>Reputation:</strong> {esc(h["reputation"])}</p></div>')

    # Timeline
    moments = h.get('notable_moments', [])
    if moments:
        items = '\n        '.join(
            f'<div class="rl-timeline-item"><div class="rl-timeline-text">{esc(m)}</div></div>'
            for m in moments
        )
        body_parts.append(f'''<div class="rl-timeline">
        {items}
      </div>''')

    if not body_parts:
        return ''

    body = '\n      '.join(body_parts)

    return f'''<section id="history" class="rl-section rl-section--dark rl-fade-section">
    <div class="rl-section-header rl-section-header--teal">
      <span class="rl-section-kicker">[02]</span>
      <h2 class="rl-section-title">Facts &amp; History</h2>
    </div>
    <div class="rl-section-body">
      {body}
    </div>
  </section>'''


def _build_riders_report(groups: list[tuple[list[dict], str]]) -> str:
    """Build a single RIDERS REPORT callout box from one or more item groups.

    Each group is a (items, item_type) tuple:
      - item_type "named": items with name + description + optional mile_marker
      - item_type "text": items with text field

    Returns '' if all groups are empty. One badge per callout, regardless of
    how many item types are combined.
    """
    active = [(items, itype) for items, itype in groups if items]
    if not active:
        return ''

    parts = ['<div class="rl-riders-report">',
             '<div class="rl-riders-report-badge">RIDERS REPORT</div>']

    for items, item_type in active:
        for item in items:
            if item_type == "named":
                name = esc(item.get("name", ""))
                desc = esc(item.get("description", ""))
                mile = str(item.get("mile_marker", "")) if item.get("mile_marker") is not None else ""
                mile_html = f' <span class="rl-riders-report-mile">MI {esc(mile)}</span>' if mile else ''
                parts.append(
                    f'<div class="rl-riders-report-item">'
                    f'<div class="rl-riders-report-name">{name}{mile_html}</div>'
                    f'<div class="rl-riders-report-desc">{desc}</div>'
                    f'</div>'
                )
            else:
                text = esc(item.get("text", ""))
                parts.append(
                    f'<div class="rl-riders-report-item">'
                    f'<div class="rl-riders-report-desc">{text}</div>'
                    f'</div>'
                )

    parts.append('</div>')
    return '\n      '.join(parts)


def build_course_route(rd: dict) -> str:
    """Build [03] The Course section — suffering zones."""
    c = rd['course']
    zones = c.get('suffering_zones', [])

    if not zones and not c.get('character') and not c.get('signature_challenge'):
        return ''

    body_parts = []

    # Photo gallery (video stills) — top of Course section
    gallery = [p for p in rd.get('photos', [])
               if not p.get('primary') and not p.get('gif')][:4]
    if gallery:
        items = []
        for p in gallery:
            alt = esc(p.get('alt', rd['name']))
            credit = p.get('credit', '')
            credit_html = (
                f'<span class="rl-photo-credit">Photo: {esc(credit)}</span>'
                if credit else ''
            )
            items.append(
                f'<figure class="rl-photo-item">'
                f'<img src="{esc(p["url"])}" alt="{alt}" loading="lazy"'
                f' width="600" height="400">'
                f'{credit_html}'
                f'</figure>'
            )
        body_parts.append(
            f'<div class="rl-photo-grid">{"".join(items)}</div>'
        )

    if c.get('character'):
        body_parts.append(f'<div class="rl-prose"><p>{esc(c["character"])}</p></div>')

    if c.get('signature_challenge'):
        body_parts.append(f'<div class="rl-prose"><p><strong>Signature challenge:</strong> {esc(c["signature_challenge"])}</p></div>')

    # Surface breakdown bar chart
    surface = c.get('surface_breakdown', {})
    if surface:
        surface_colors = {
            'gravel': 'var(--rl-color-teal)',
            'pavement': 'var(--rl-color-gold)',
            'dirt': 'var(--rl-color-warm-brown)',
            'singletrack': 'var(--rl-color-primary-brown)',
            'doubletrack': 'var(--rl-color-secondary-brown)',
            'trail': 'var(--rl-color-secondary-brown)',
            'sand': 'var(--rl-color-tan)',
            'mud': 'var(--rl-color-dark-brown)',
        }
        bars_html = []
        for dist_label, surfaces in surface.items():
            segs = []
            for stype, pct in sorted(surfaces.items(), key=lambda x: -x[1]):
                color = surface_colors.get(stype, 'var(--rl-color-tan)')
                label_text = f'{esc(stype)} {pct}%' if pct >= 10 else ''
                segs.append(
                    f'<div class="rl-surface-seg" style="width:{pct}%;background:{color}" '
                    f'title="{esc(stype)} {pct}%">{label_text}</div>'
                )
            legend_items = [
                f'<span class="rl-surface-legend-item">'
                f'<span class="rl-surface-legend-dot" style="background:{surface_colors.get(s, "var(--rl-color-tan)")}">'
                f'</span>{esc(s)} {p}%</span>'
                for s, p in sorted(surfaces.items(), key=lambda x: -x[1])
            ]
            bars_html.append(f'''<div class="rl-surface-row">
              <div class="rl-surface-dist">{esc(dist_label)}</div>
              <div class="rl-surface-bar">{"".join(segs)}</div>
              <div class="rl-surface-legend">{"".join(legend_items)}</div>
            </div>''')
        body_parts.append(f'''<div class="rl-surface-breakdown">
          <div class="rl-surface-header">SURFACE COMPOSITION</div>
          {"".join(bars_html)}
        </div>''')

    if zones:
        zone_html = []
        for idx, z in enumerate(zones, 1):
            # Handle both dict format {mile, label, desc} and plain string format
            if isinstance(z, dict):
                mile = esc(z.get("mile", str(idx)))
                label = esc(z.get("label", z.get("named_section", "")))
                desc = esc(z.get("desc", ""))
            else:
                mile = str(idx)
                z_str = str(z)
                if ": " in z_str:
                    label, desc = z_str.split(": ", 1)
                    label = esc(label)
                    desc = esc(desc)
                else:
                    label = ""
                    desc = esc(z_str)
            zone_html.append(f'''<div class="rl-suffering-zone">
          <div class="rl-suffering-mile">
            <div class="rl-suffering-mile-num">{mile}</div>
            <div class="rl-suffering-mile-label">ZONE</div>
          </div>
          <div class="rl-suffering-content">
            <div class="rl-suffering-name">{label}</div>
            <div class="rl-suffering-desc">{desc}</div>
          </div>
        </div>''')
        body_parts.append('\n      '.join(zone_html))

    # Course preview GIF gallery (from YouTube screenshots)
    preview_gifs = [p for p in rd.get('photos', []) if p.get('gif')]
    if preview_gifs:
        gif_items = []
        for pg in preview_gifs:
            gif_credit = esc(pg.get('credit', ''))
            credit_html = (
                f'<span class="rl-photo-credit">{gif_credit}</span>'
                if gif_credit else ''
            )
            gif_items.append(
                f'<div class="rl-course-preview">'
                f'<img src="{esc(pg["url"])}" alt="{esc(pg.get("alt", "Course preview"))}"'
                f' loading="lazy" width="400" height="225" class="rl-preview-gif">'
                f'{credit_html}'
                f'</div>'
            )
        if len(gif_items) == 1:
            body_parts.append(gif_items[0])
        else:
            body_parts.append(
                f'<div class="rl-gif-gallery">{"".join(gif_items)}</div>'
            )

    # Riders Report: key challenges + terrain notes (single combined callout)
    intel = rd.get('rider_intel', {})
    course_report = _build_riders_report([
        (intel.get('key_challenges', []), "named"),
        (intel.get('terrain_notes', []), "text"),
    ])
    if course_report:
        body_parts.append(course_report)

    body = '\n      '.join(body_parts)

    return f'''<section id="route" class="rl-section rl-section--accent rl-fade-section">
    <div class="rl-section-header">
      <span class="rl-section-kicker">[03]</span>
      <h2 class="rl-section-title">The Course</h2>
    </div>
    <div class="rl-section-body">
      {body}
    </div>
  </section>'''


def _format_view_count(count: int) -> str:
    """Format a view count as a compact string (e.g., 68980 → '69K')."""
    if not count or count < 0:
        return ''
    if count >= 1_000_000:
        return f'{count / 1_000_000:.1f}M'.replace('.0M', 'M')
    if count >= 1_000:
        return f'{count / 1_000:.1f}K'.replace('.0K', 'K')
    return str(count)


def build_from_the_field(rd: dict) -> str:
    """Build [04] From the Field section — rider quotes + YouTube video embeds.

    Returns '' if no youtube_data exists, so unenriched pages render identically.
    Uses lite-youtube facade for zero performance cost until user clicks play.
    Embeds use youtube-nocookie.com for GDPR/privacy compliance.
    """
    videos = rd.get('youtube_videos', [])
    quotes = rd.get('youtube_quotes', [])

    if not videos and not quotes:
        return ''

    body_parts = []

    # Rider quotes — teal-bordered blockquotes
    if quotes:
        for q in quotes:
            source_channel = esc(q.get('source_channel', ''))
            view_count = _format_view_count(q.get('source_view_count', 0))
            attribution = source_channel
            if view_count:
                attribution += f' &middot; {esc(view_count)} views'
            body_parts.append(
                f'<blockquote class="rl-field-quote">'
                f'<p class="rl-field-quote-text">{esc(q.get("text", ""))}</p>'
                f'<cite class="rl-field-quote-cite">{attribution}</cite>'
                f'</blockquote>'
            )

    # Video embeds — lite-youtube facade (thumbnail + play, iframe on click)
    if videos:
        video_cards = []
        for v in sorted(videos, key=lambda x: x.get('display_order', 99)):
            vid = esc(v.get('video_id', ''))
            title = esc(v.get('title', ''))
            channel = esc(v.get('channel', ''))
            duration = esc(v.get('duration_string', ''))
            view_count = _format_view_count(v.get('view_count', 0))
            meta_parts = [channel]
            if view_count:
                meta_parts.append(f'{esc(view_count)} views')
            if duration:
                meta_parts.append(duration)
            meta_text = ' &middot; '.join(meta_parts)

            thumb_url = esc(v.get('thumbnail_url', ''))
            if thumb_url and 'maxresdefault' in thumb_url:
                thumb_w, thumb_h = 1280, 720
            else:
                thumb_url = f'https://i.ytimg.com/vi/{vid}/hqdefault.jpg'
                thumb_w, thumb_h = 480, 360

            video_cards.append(
                f'<div class="rl-field-video">'
                f'<div class="rl-lite-youtube" data-videoid="{vid}">'
                f'<img src="{thumb_url}" '
                f'alt="{title}" class="rl-lite-youtube-thumb" loading="lazy" width="{thumb_w}" height="{thumb_h}">'
                f'<button class="rl-lite-youtube-play" aria-label="Play {title}">'
                f'<svg viewBox="0 0 68 48" width="68" height="48"><path d="M66.52 7.74c-.78-2.93-2.49-5.41-5.42-6.19C55.79.13 34 0 34 0S12.21.13 6.9 1.55c-2.93.78-4.64 3.26-5.42 6.19C.06 13.05 0 24 0 24s.06 10.95 1.48 16.26c.78 2.93 2.49 5.41 5.42 6.19C12.21 47.87 34 48 34 48s21.79-.13 27.1-1.55c2.93-.78 4.64-3.26 5.42-6.19C67.94 34.95 68 24 68 24s-.06-10.95-1.48-16.26z" fill="#212121" fill-opacity=".8"/><path d="M45 24 27 14v20" fill="#fff"/></svg>'
                f'</button>'
                f'</div>'
                f'<div class="rl-field-video-meta">{meta_text}</div>'
                f'</div>'
            )
        body_parts.append(
            f'<div class="rl-field-video-grid">{"".join(video_cards)}</div>'
        )

    body = '\n      '.join(body_parts)

    return f'''<section id="from-the-field" class="rl-section rl-section--teal-accent rl-fade-section">
    <div class="rl-section-header rl-section-header--teal">
      <span class="rl-section-kicker">[04]</span>
      <h2 class="rl-section-title">From the Field</h2>
    </div>
    <div class="rl-section-body">
      {body}
    </div>
  </section>'''


def build_ratings(rd: dict) -> str:
    """Build [05] The Ratings section — merged course + editorial with accordions."""
    # Summary row
    summary = f'''<div class="rl-ratings-summary">
        <div class="rl-ratings-summary-card">
          <div class="rl-ratings-summary-score">{rd['course_profile']}<span class="rl-ratings-summary-max">/35</span></div>
          <div class="rl-ratings-summary-label">Course Profile</div>
        </div>
        <div class="rl-ratings-summary-card">
          <div class="rl-ratings-summary-score">{rd['opinion_total']}<span class="rl-ratings-summary-max">/35</span></div>
          <div class="rl-ratings-summary-label">Editorial</div>
        </div>
      </div>'''

    radar = build_radar_charts(rd['explanations'], rd['course_profile'], rd['opinion_total'])
    course_accordion = build_accordion_html(COURSE_DIMS, rd['explanations'], idx_offset=0)
    opinion_accordion = build_accordion_html(OPINION_DIMS, rd['explanations'], idx_offset=7)

    return f'''<section id="ratings" class="rl-section rl-section--teal-accent rl-fade-section">
    <div class="rl-section-header rl-section-header--dark">
      <span class="rl-section-kicker">[05]</span>
      <h2 class="rl-section-title">The Ratings</h2>
    </div>
    <div class="rl-section-body">
      {summary}
      {radar}
      <h3 class="rl-accordion-group-title">Course Profile</h3>
      {course_accordion}
      <h3 class="rl-accordion-group-title rl-mt-md">Editorial Assessment</h3>
      {opinion_accordion}
    </div>
  </section>'''


def build_verdict(rd: dict, race_index: list = None) -> str:
    """Build [05] Final Verdict section — Race This If / Skip This If."""
    bo = rd['biased_opinion']
    fv = rd['final_verdict']

    strengths = bo.get('strengths', [])
    weaknesses = bo.get('weaknesses', [])

    if not strengths and not weaknesses and not fv.get('should_you_race'):
        # Fallback: show summary if available
        if bo.get('summary'):
            return f'''<section id="verdict" class="rl-section rl-section--dark rl-fade-section">
    <div class="rl-section-header rl-section-header--gold">
      <span class="rl-section-kicker">[06]</span>
      <h2 class="rl-section-title">Final Verdict</h2>
    </div>
    <div class="rl-section-body">
      <div class="rl-prose"><p>{esc(bo["summary"])}</p></div>
    </div>
  </section>'''
        return ''

    # Build Race This If / Skip This If
    race_items = '\n          '.join(f'<li>{esc(s)}</li>' for s in strengths) if strengths else '<li>See the ratings above for details.</li>'
    skip_items = '\n          '.join(f'<li>{esc(w)}</li>' for w in weaknesses) if weaknesses else '<li>See the ratings above for details.</li>'

    verdict_grid = f'''<div class="rl-verdict-grid">
        <div class="rl-verdict-box rl-verdict-box--race">
          <div class="rl-verdict-box-title">Race This If</div>
          <ul class="rl-verdict-list">
          {race_items}
          </ul>
        </div>
        <div class="rl-verdict-box rl-verdict-box--skip">
          <div class="rl-verdict-box-title">Skip This If</div>
          <ul class="rl-verdict-list">
          {skip_items}
          </ul>
        </div>
      </div>'''

    bottom_line = ''
    bl_text = bo.get('bottom_line') or fv.get('should_you_race', '')
    if bl_text:
        bottom_line = f'''<div class="rl-verdict-bottom-line">
        <strong>Bottom Line:</strong> {esc(bl_text)}
      </div>'''

    # Alternatives with race links
    alt_html = ''
    if fv.get('alternatives'):
        linked = linkify_alternatives(fv['alternatives'], race_index or [])
        alt_html = f'''<div class="rl-prose rl-mt-md"><p><strong>Alternatives:</strong> {linked}</p></div>'''

    return f'''<section id="verdict" class="rl-section rl-section--dark rl-fade-section">
    <div class="rl-section-header rl-section-header--gold">
      <span class="rl-section-kicker">[06]</span>
      <h2 class="rl-section-title">Final Verdict</h2>
    </div>
    <div class="rl-section-body">
      {verdict_grid}
      {bottom_line}
      {alt_html}
    </div>
  </section>'''


def _build_inline_review_form(slug: str, name: str) -> str:
    """Build inline review form HTML — replaces Google Forms link."""
    years = "".join(f'<option value="{y}">{y}</option>' for y in range(int(CURRENT_YEAR), 2019, -1))
    return f'''<div class="rl-review-form-wrap" id="rl-review-form-wrap">
      <h3 class="rl-review-form-title">RATE {esc(name.upper())}</h3>
      <form class="rl-review-form" id="rl-review-form" autocomplete="off">
        <input type="hidden" name="race_slug" value="{esc(slug)}">
        <input type="hidden" name="race_name" value="{esc(name)}">
        <input type="hidden" name="website" value="">
        <div class="rl-review-stars-input" id="rl-review-stars-input">
          <label class="rl-review-field-label" id="rl-review-star-label">Overall Experience <span style="color:var(--rl-color-teal)">*</span></label>
          <div class="rl-review-star-row" role="radiogroup" aria-labelledby="rl-review-star-label">
            {"".join(f'<button type="button" class="rl-review-star-btn" data-star="{i}" role="radio" aria-checked="false" aria-label="{i} star{"s" if i>1 else ""}">&#9733;</button>' for i in range(1, 6))}
          </div>
          <input type="hidden" name="stars" id="rl-review-stars-val" value="">
        </div>
        <div class="rl-review-form-row">
          <div class="rl-review-field">
            <label for="rl-review-email">Email <span style="color:var(--rl-color-teal)">*</span></label>
            <input type="email" id="rl-review-email" name="email" required placeholder="you@example.com" class="rl-review-input">
          </div>
          <div class="rl-review-field">
            <label for="rl-review-year">Year Raced</label>
            <select id="rl-review-year" name="year_raced" class="rl-review-select">
              <option value="">Select</option>
              {years}
            </select>
          </div>
        </div>
        <div class="rl-review-form-row">
          <div class="rl-review-field">
            <label for="rl-review-again">Would you race again?</label>
            <select id="rl-review-again" name="would_race_again" class="rl-review-select">
              <option value="">Select</option>
              <option value="yes">Yes</option>
              <option value="no">No</option>
            </select>
          </div>
          <div class="rl-review-field">
            <label for="rl-review-finish">Finish Position</label>
            <select id="rl-review-finish" name="finish_position" class="rl-review-select">
              <option value="">Select</option>
              <option value="Top 10%">Top 10%</option>
              <option value="Top Quarter">Top Quarter</option>
              <option value="Mid-Pack">Mid-Pack</option>
              <option value="Back Half">Back Half</option>
              <option value="DNF">DNF</option>
            </select>
          </div>
        </div>
        <div class="rl-review-field rl-review-field--full">
          <label for="rl-review-best">Best thing about this race</label>
          <textarea id="rl-review-best" name="best" maxlength="500" rows="2" class="rl-review-textarea" placeholder="What made it great?"></textarea>
          <span class="rl-review-charcount" data-for="rl-review-best">0/500</span>
        </div>
        <div class="rl-review-field rl-review-field--full">
          <label for="rl-review-worst">Worst thing about this race</label>
          <textarea id="rl-review-worst" name="worst" maxlength="500" rows="2" class="rl-review-textarea" placeholder="What could improve?"></textarea>
          <span class="rl-review-charcount" data-for="rl-review-worst">0/500</span>
        </div>
        <button type="submit" class="rl-btn rl-btn--rate">SUBMIT REVIEW</button>
      </form>
      <div class="rl-review-success" id="rl-review-success" style="display:none">
        <div class="rl-review-success-icon">&#10003;</div>
        <p class="rl-review-success-text">Review submitted — thank you! It will appear after moderation.</p>
      </div>
    </div>'''


def build_racer_reviews(rd: dict) -> str:
    """Build Racer Reviews section — star summary, text reviews, inline form."""
    rr = rd.get('racer_rating', {})
    total_ratings = rr.get('total_ratings', 0)
    total_reviews = rr.get('total_reviews', 0)
    star_avg = rr.get('star_average')
    reviews = rr.get('reviews', [])
    name = rd['name']
    slug = rd['slug']

    review_form = _build_inline_review_form(slug, name)

    # No ratings at all — empty state
    if total_ratings == 0:
        return f'''<section class="rl-racer-reviews rl-fade-section">
    <div class="rl-racer-empty">
      <div class="rl-racer-empty-text">No racer ratings yet. Be the first to rate {esc(name)}.</div>
      {review_form}
    </div>
  </section>'''

    # Below threshold — pending state
    if total_ratings < RACER_RATING_THRESHOLD:
        needed = RACER_RATING_THRESHOLD - total_ratings
        return f'''<section class="rl-racer-reviews rl-fade-section">
    <div class="rl-racer-pending">
      <div class="rl-racer-pending-text">{total_ratings} rating{"s" if total_ratings != 1 else ""} so far &mdash; {needed} more needed to display the Racer Rating.</div>
      {review_form}
    </div>
  </section>'''

    # Full display — star summary + reviews
    parts = []

    # Star summary bar
    if star_avg is not None:
        full_stars = int(star_avg)
        half_star = (star_avg - full_stars) >= 0.5
        stars_html = '&#9733;' * full_stars
        if half_star:
            stars_html += '&#9733;'
            empty = 5 - full_stars - 1
        else:
            empty = 5 - full_stars
        stars_html += '&#9734;' * empty
        parts.append(f'''<div class="rl-racer-stars">
      <span class="rl-racer-stars-icons">{stars_html}</span>
      <span class="rl-racer-stars-avg">{star_avg:.1f} avg</span>
      <span class="rl-racer-stars-sep">&middot;</span>
      <span class="rl-racer-stars-count">{total_reviews} review{"s" if total_reviews != 1 else ""}</span>
    </div>''')

    # Text reviews (up to 5)
    for review in reviews[:5]:
        text = review.get('text', '')
        if not text:
            continue
        stars = review.get('stars')
        finish = review.get('finish_category', '')
        meta_parts = []
        if stars:
            meta_parts.append(f'{"&#9733;" * stars}')
        if finish:
            meta_parts.append(f'<span class="rl-review-finish">{esc(finish)}</span>')
        meta_html = f'<div class="rl-review-meta">{" ".join(meta_parts)}</div>' if meta_parts else ''
        parts.append(f'''<div class="rl-review-item">
      <div class="rl-review-text">{esc(text)}</div>
      {meta_html}
    </div>''')

    parts.append(review_form)

    inner = '\n    '.join(parts)
    return f'''<section class="rl-racer-reviews rl-fade-section">
    <div class="rl-section-header rl-section-header--teal">
      <span class="rl-section-kicker">RACER</span>
      <h2 class="rl-section-title">Racer Reviews</h2>
    </div>
    <div class="rl-section-body">
    {inner}
    </div>
  </section>'''


def build_training(rd: dict) -> str:
    """Build [06] Training section — two distinct paths, countdown, clear differentiation."""
    race_name = rd['name']

    # Race date countdown — parsed from date_specific
    countdown_html = ''
    date_specific = rd['vitals'].get('date_specific', '')
    cd_start, _cd_end = parse_event_dates(date_specific)
    if cd_start:
        # Reconstruct display date from ISO for no-JS/crawlers
        parts = cd_start.split('-')
        month_names = {v: k.capitalize() for k, v in MONTH_NUMBERS.items()}
        display_month = month_names.get(parts[1], parts[1])
        display_date = f"{display_month} {int(parts[2])}, {parts[0]}"
        countdown_html = f'<div class="rl-countdown" data-date="{cd_start}"><span class="rl-countdown-num" id="rl-days-left">{esc(display_date)}</span> {esc(race_name.upper())}</div>'

    # Riders Report: gear mentions before training plan CTA
    gear_html = _build_riders_report([
        (rd.get('rider_intel', {}).get('gear_mentions', []), "text"),
    ])

    return f'''<section id="training" class="rl-section rl-fade-section">
    <div class="rl-section-header">
      <span class="rl-section-kicker">[07]</span>
      <h2 class="rl-section-title">Training</h2>
    </div>
    <div class="rl-section-body">
      {countdown_html}
      {gear_html}
      <div class="rl-training-free">
        <a href="/race/{esc(rd['slug'])}/prep-kit/" class="rl-btn rl-btn--outline">GET FREE RACE PREP KIT</a>
        <p class="rl-training-free-desc">12-week timeline + race-day checklist + packing list. Free.</p>
      </div>
      <div class="rl-training-primary">
        <h3>Custom Training Plan</h3>
        <p class="rl-training-subtitle">Race-specific. Built for {esc(race_name)}. $15/week, capped at $249.</p>
        <ul class="rl-training-bullets">
          <li>Structured workouts pushed to your device</li>
          <li>30+ page custom training guide</li>
          <li>Heat &amp; altitude protocols</li>
          <li>Nutrition plan</li>
          <li>Strength training</li>
        </ul>
        <a href="{esc(TRAINING_PLANS_URL)}?race={esc(rd['slug'])}" class="rl-btn">BUILD MY PLAN &mdash; $15/WK</a>
      </div>
      <div class="rl-training-divider">
        <span class="rl-training-divider-line"></span>
        <span class="rl-training-divider-text">OR</span>
        <span class="rl-training-divider-line"></span>
      </div>
      <div class="rl-training-secondary">
        <div class="rl-training-secondary-text">
          <h4>1:1 Coaching</h4>
          <p class="rl-training-subtitle">A human in your corner. Adapts week to week.</p>
          <p>Your coach reviews every session, adjusts when life happens, and builds race-day strategy with you. Not a plan &mdash; a partnership.</p>
        </div>
        <a href="{esc(COACHING_URL)}" class="rl-btn">APPLY FOR 1:1 COACHING</a>
      </div>
    </div>
  </section>'''


# ── Workout showcase data for race-specific training section ──
# Each entry: viz structure, duration, descriptions for the flagship workout
# per archetype category. Viz format matches training-plans.html.
WORKOUT_SHOWCASE = {
    'Tired VO2max': {
        'duration': '2.5hr',
        'summary': 'VO2max intervals after 2 hours of endurance — power when it matters most.',
        'viz': [
            {"z":"z2","w":40,"h":48,"l":"Z2 Base 2hr"},
            {"z":"z5","w":12,"h":85,"l":"4m VO2"},
            {"z":"z1","w":8,"h":28,"l":"4m"},
            {"z":"z5","w":12,"h":88,"l":"4m VO2"},
            {"z":"z1","w":8,"h":28,"l":"4m"},
            {"z":"z2","w":10,"h":40,"l":"CD"},
        ],
        'structure': '2hr Zone 2 \u2192 2\u00d74min @ 110% FTP / 4min recovery \u2192 10min cool-down',
        'execution': 'Hold steady Zone 2 for 2 hours. Then hit VO2max intervals on tired legs. They will feel significantly harder than fresh \u2014 that\'s the point. This is what separates race-ready athletes from gym-fit athletes. Fight for form when fatigue hits.',
        'cadence': '85\u201390rpm during Z2 base | 95\u2013100rpm on VO2 efforts',
        'position': 'Hoods for Z2 base. Drops for VO2 intervals \u2014 aggressive, race position.',
        'rpe': 'Z2 base: 3\u20134 | VO2 intervals: 8\u20139',
        'power': 'Z2: 65\u201370% FTP | VO2: 110% FTP | Recovery: 55% FTP',
    },
    '5x3 VO2 Classic': {
        'duration': '1hr',
        'summary': 'The gold standard VO2max session \u2014 5 efforts at your aerobic ceiling.',
        'viz': [
            {"z":"z2","w":14,"h":45,"l":"WU 10m"},
            {"z":"z5","w":8,"h":85,"l":"3m"},{"z":"z1","w":6,"h":28,"l":"3m"},
            {"z":"z5","w":8,"h":87,"l":"3m"},{"z":"z1","w":6,"h":28,"l":"3m"},
            {"z":"z5","w":8,"h":89,"l":"3m"},{"z":"z1","w":6,"h":28,"l":"3m"},
            {"z":"z5","w":8,"h":91,"l":"3m"},{"z":"z1","w":6,"h":28,"l":"3m"},
            {"z":"z5","w":8,"h":93,"l":"3m"},
            {"z":"z2","w":8,"h":40,"l":"CD"},
        ],
        'structure': '10min warm-up \u2192 5\u00d73min @ 115% FTP / 3min recovery \u2192 5min cool-down',
        'execution': 'Build into each interval over the first 30 seconds. Hold steady \u2014 don\'t surge and fade. If you can\'t hold power on rep 5, the target was too high. These should be controlled suffering, not panicked sprinting.',
        'cadence': '95\u2013105rpm throughout intervals',
        'position': 'Seated in drops, elbows bent. Standing OK for final 30s of each rep.',
        'rpe': 'Reps 1\u20133: 8 | Reps 4\u20135: 9',
        'power': 'Intervals: 112\u2013118% FTP | Recovery: 50\u201355% FTP',
    },
    'HVLI Extended Z2': {
        'duration': '3hr',
        'summary': 'Pure endurance volume \u2014 the aerobic engine that fuels everything else.',
        'viz': [
            {"z":"z2","w":12,"h":46,"l":"WU 15m"},
            {"z":"z2","w":70,"h":52,"l":"Z2 Steady 2.5hr"},
            {"z":"z2","w":12,"h":42,"l":"CD 15m"},
        ],
        'structure': '15min progressive warm-up \u2192 2.5hr steady Zone 2 \u2192 15min cool-down',
        'execution': 'This is the foundation ride. Perfectly steady Zone 2 \u2014 no surges, no coasting, no excuses. Nasal breathing pace. This is where fat oxidation improves, mitochondrial density increases, and your body learns to go long. The most important ride of the week.',
        'cadence': '80\u201390rpm \u2014 find your sustainable rhythm and hold it',
        'position': 'Alternate every 30min: hoods \u2192 drops \u2192 tops. Build position endurance.',
        'rpe': '3\u20134 throughout \u2014 conversational pace, never labored',
        'power': '65\u201370% FTP steady \u2014 if heart rate drifts above Z2, reduce power',
    },
    'Breakaway Simulation': {
        'duration': '1.5hr',
        'summary': 'Attack, then hold \u2014 the tactical pattern that wins gravel races.',
        'viz': [
            {"z":"z2","w":12,"h":45,"l":"WU 15m"},
            {"z":"z5","w":10,"h":82,"l":"5m ATK"},
            {"z":"z4","w":18,"h":65,"l":"10m HOLD"},
            {"z":"z2","w":6,"h":35,"l":"5m"},
            {"z":"z5","w":10,"h":85,"l":"5m ATK"},
            {"z":"z4","w":18,"h":68,"l":"10m HOLD"},
            {"z":"z2","w":8,"h":40,"l":"CD"},
        ],
        'structure': '15min warm-up \u2192 2\u00d7(5min @ 110% FTP attack + 10min @ 88% FTP hold) / 5min recovery \u2192 cool-down',
        'execution': 'This is race tactics on the trainer. Attack hard for 5 minutes \u2014 simulate bridging a gap or cresting a climb. Then immediately settle to tempo and HOLD. The transition from attack to hold is where races are lost. Practice it.',
        'cadence': '95\u2013105rpm on attacks | 85\u201395rpm on holds',
        'position': 'Out of saddle for first 60s of attacks. Seated in drops for holds.',
        'rpe': 'Attacks: 8\u20139 | Holds: 6\u20137 | Recovery: 2\u20133',
        'power': 'Attacks: 108\u2013112% FTP | Holds: 86\u201390% FTP | Recovery: 50% FTP',
    },
    'Single Sustained Threshold': {
        'duration': '1.25hr',
        'summary': '2\u00d720min at threshold \u2014 the ultimate FTP builder.',
        'viz': [
            {"z":"z2","w":12,"h":45,"l":"WU 10m"},
            {"z":"z4","w":28,"h":72,"l":"20m FTP"},
            {"z":"z2","w":6,"h":38,"l":"5m"},
            {"z":"z4","w":28,"h":74,"l":"20m FTP"},
            {"z":"z2","w":10,"h":40,"l":"CD"},
        ],
        'structure': '10min warm-up \u2192 20min @ 95\u2013100% FTP \u2192 5min recovery \u2192 20min @ 95\u2013100% FTP \u2192 cool-down',
        'execution': 'Lock in your power. Don\'t start too hard \u2014 the first 5 minutes should feel almost easy. Build into it. At minute 15, you\'ll want to quit. That\'s where the adaptation happens. Breathing should be heavy but controlled.',
        'cadence': '85\u201395rpm seated \u2014 constant, metronomic',
        'position': 'Primary: seated on hoods. Switch to drops at minute 10 for aero practice.',
        'rpe': '7\u20138 throughout \u2014 sustainable suffering',
        'power': 'Intervals: 95\u2013100% FTP | Recovery: 55% FTP',
    },
    'G-Spot Standard': {
        'duration': '1.5hr',
        'summary': '2\u00d720min at 88\u201392% FTP \u2014 the workhorse of gravel training.',
        'viz': [
            {"z":"z2","w":12,"h":45,"l":"WU 10m"},
            {"z":"z3","w":6,"h":55,"l":"5m"},
            {"z":"z4","w":22,"h":68,"l":"20m G-Spot"},
            {"z":"z2","w":6,"h":38,"l":"5m"},
            {"z":"z4","w":22,"h":70,"l":"20m G-Spot"},
            {"z":"z3","w":6,"h":52,"l":"5m"},
            {"z":"z2","w":10,"h":40,"l":"CD"},
        ],
        'structure': '10min warm-up \u2192 5min tempo ramp \u2192 20min @ 88\u201392% FTP \u2192 5min recovery \u2192 20min @ 88\u201392% FTP \u2192 5min tempo \u2192 cool-down',
        'execution': 'The G-Spot is the sweet spot that actually works for gravel. Slightly below threshold \u2014 enough stimulus for FTP gains, low enough for recovery within 24 hours. This is your bread-and-butter session. Nail the power. Nail the position. Nail the cadence.',
        'cadence': '85\u201395rpm throughout \u2014 seated, smooth pedal stroke',
        'position': 'Hoods, seated. Practice race posture \u2014 relaxed shoulders, bent elbows.',
        'rpe': '6\u20137 \u2014 hard but repeatable. You could do a third set but shouldn\'t.',
        'power': 'G-Spot: 88\u201392% FTP | Tempo ramp: 76\u201385% FTP | Recovery: 55% FTP',
    },
    'Seated/Standing Climbs': {
        'duration': '1.25hr',
        'summary': 'Alternating seated and standing efforts \u2014 builds climbing versatility.',
        'viz': [
            {"z":"z2","w":12,"h":45,"l":"WU 10m"},
            {"z":"z4","w":10,"h":70,"l":"3m SEAT"},
            {"z":"z5","w":7,"h":80,"l":"2m STAND"},
            {"z":"z2","w":5,"h":35,"l":"5m"},
            {"z":"z4","w":10,"h":72,"l":"3m SEAT"},
            {"z":"z5","w":7,"h":82,"l":"2m STAND"},
            {"z":"z2","w":5,"h":35,"l":"5m"},
            {"z":"z4","w":10,"h":74,"l":"3m SEAT"},
            {"z":"z5","w":7,"h":84,"l":"2m STAND"},
            {"z":"z2","w":8,"h":40,"l":"CD"},
        ],
        'structure': '10min warm-up \u2192 3\u00d7(3min seated @ 95% FTP + 2min standing @ 105% FTP) / 5min recovery \u2192 cool-down',
        'execution': 'Alternate between seated grinding and standing power. The transition is key \u2014 shift up 1\u20132 gears when standing, maintain cadence. This builds the ability to change climbing style mid-effort, exactly what variable-grade gravel climbs demand.',
        'cadence': 'Seated: 70\u201380rpm (force) | Standing: 60\u201370rpm (torque)',
        'position': 'Seated: hands on hoods, core engaged | Standing: hands on hoods, bike rocking gently',
        'rpe': 'Seated: 7 | Standing: 8\u20139',
        'power': 'Seated: 93\u201397% FTP | Standing: 103\u2013107% FTP | Recovery: 55% FTP',
    },
    'Classic Over-Unders': {
        'duration': '1hr',
        'summary': 'Oscillating above and below threshold \u2014 trains lactate clearance under load.',
        'viz': [
            {"z":"z2","w":12,"h":45,"l":"WU 10m"},
            {"z":"z4","w":9,"h":64,"l":"3m UNDER"},
            {"z":"z5","w":4,"h":82,"l":"1m OVER"},
            {"z":"z4","w":9,"h":64,"l":"3m UNDER"},
            {"z":"z5","w":4,"h":84,"l":"1m OVER"},
            {"z":"z4","w":9,"h":64,"l":"3m UNDER"},
            {"z":"z5","w":4,"h":86,"l":"1m OVER"},
            {"z":"z2","w":6,"h":35,"l":"REST"},
            {"z":"z4","w":14,"h":66,"l":"SET 2"},
            {"z":"z2","w":6,"h":35,"l":"REST"},
            {"z":"z4","w":14,"h":68,"l":"SET 3"},
            {"z":"z2","w":8,"h":40,"l":"CD"},
        ],
        'structure': '10min warm-up \u2192 3 sets of (3min @ 90% + 1min @ 106% FTP)\u00d73 reps / 3min recovery between sets \u2192 cool-down',
        'execution': 'The "under" should feel controlled \u2014 right at threshold. The "over" is a punch above. Your body learns to clear lactate while still working. The transitions should be INSTANT \u2014 no ramping, no soft-pedaling. That\'s what a gravel surge feels like.',
        'cadence': '90rpm on unders | 95\u2013100rpm on overs',
        'position': 'Seated throughout. Hands on drops during overs.',
        'rpe': 'Unders: 7 | Overs: 8\u20139',
        'power': 'Unders: 88\u201392% FTP | Overs: 104\u2013108% FTP | Rest: 50% FTP',
    },
    'Surge and Settle': {
        'duration': '1hr',
        'summary': 'Explosive surges into tempo settling \u2014 the signature gravel-specific workout.',
        'viz': [
            {"z":"z2","w":14,"h":45,"l":"WU 15m"},
            {"z":"z6","w":4,"h":92,"l":"SURGE"},
            {"z":"z3","w":9,"h":58,"l":"SETTLE"},
            {"z":"z6","w":4,"h":94,"l":"SURGE"},
            {"z":"z3","w":9,"h":58,"l":"SETTLE"},
            {"z":"z6","w":4,"h":95,"l":"SURGE"},
            {"z":"z3","w":9,"h":58,"l":"SETTLE"},
            {"z":"z2","w":6,"h":35,"l":"5m"},
            {"z":"z6","w":3,"h":92,"l":"S"},
            {"z":"z3","w":7,"h":58,"l":"SET 2"},
            {"z":"z6","w":3,"h":94,"l":"S"},
            {"z":"z3","w":7,"h":58,"l":""},
            {"z":"z6","w":3,"h":95,"l":"S"},
            {"z":"z3","w":7,"h":58,"l":""},
            {"z":"z2","w":8,"h":40,"l":"CD"},
        ],
        'structure': '15min warm-up \u2192 2 sets of 3\u00d7(20sec surge @ 130% FTP + 90sec settle @ 85% FTP) / 5min between sets \u2192 cool-down',
        'execution': 'Out of the saddle for every surge \u2014 explosive, violent power. Then immediately drop to tempo and SETTLE. Smooth your breathing. Recover while still working. This is what gravel racing IS: attack the rock garden, settle on the straight, attack the climb, settle on the descent. Over and over.',
        'cadence': '100\u2013120rpm surge (explosive) | 85\u201390rpm settle (smooth)',
        'position': 'Standing for surges | Seated in drops for settle',
        'rpe': 'Surges: 9\u201310 | Settle: 5\u20136',
        'power': 'Surges: 125\u2013135% FTP | Settle: 83\u201387% FTP',
    },
    'Pre-Race Openers': {
        'duration': '45min',
        'summary': 'Race-eve activation \u2014 short, sharp efforts to prime the neuromuscular system.',
        'viz': [
            {"z":"z2","w":25,"h":46,"l":"WU 15m"},
            {"z":"z5","w":6,"h":80,"l":"30s"},
            {"z":"z2","w":10,"h":40,"l":"3m"},
            {"z":"z5","w":6,"h":85,"l":"30s"},
            {"z":"z2","w":10,"h":40,"l":"3m"},
            {"z":"z5","w":6,"h":88,"l":"30s"},
            {"z":"z2","w":25,"h":42,"l":"CD 10m"},
        ],
        'structure': '15min warm-up \u2192 3\u00d730sec @ 120% FTP / 3min easy \u2192 10min cool-down',
        'execution': 'Race is tomorrow. This isn\'t a workout \u2014 it\'s an activation. Three short openers to remind your legs what hard feels like. Don\'t go deep. Don\'t go long. Feel the snap. Spin easy. Go to bed.',
        'cadence': '100\u2013110rpm on openers | 85\u201390rpm easy spin',
        'position': 'Race position for openers. Comfortable for everything else.',
        'rpe': 'Openers: 7\u20138 | Easy: 2\u20133',
        'power': 'Openers: 115\u2013125% FTP | Easy: 55\u201365% FTP',
    },
    'Above CP Repeats': {
        'duration': '1hr',
        'summary': 'Sustained efforts above critical power \u2014 expands your high-end ceiling.',
        'viz': [
            {"z":"z2","w":14,"h":45,"l":"WU 10m"},
            {"z":"z5","w":10,"h":80,"l":"5m"},
            {"z":"z1","w":8,"h":28,"l":"5m"},
            {"z":"z5","w":10,"h":83,"l":"5m"},
            {"z":"z1","w":8,"h":28,"l":"5m"},
            {"z":"z5","w":10,"h":86,"l":"5m"},
            {"z":"z1","w":8,"h":28,"l":"5m"},
            {"z":"z5","w":10,"h":88,"l":"5m"},
            {"z":"z2","w":8,"h":40,"l":"CD"},
        ],
        'structure': '10min warm-up \u2192 4\u00d75min @ 106\u2013110% FTP / 5min recovery \u2192 cool-down',
        'execution': 'These are above your critical power but below VO2max \u2014 the no-man\'s-land where W\' depletion meets aerobic capacity. Hold each effort perfectly even. If you fade in the last minute, you started too hard.',
        'cadence': '90\u2013100rpm \u2014 high turnover reduces muscular fatigue',
        'position': 'Seated in drops. Aero position practice under load.',
        'rpe': '8 across all reps \u2014 consistent, not progressive',
        'power': 'Intervals: 106\u2013110% FTP | Recovery: 50\u201355% FTP',
    },
    '2min Killers': {
        'duration': '50min',
        'summary': 'Short, brutal anaerobic repeats \u2014 builds the punch for climbs and attacks.',
        'viz': [
            {"z":"z2","w":14,"h":45,"l":"WU 10m"},
            {"z":"z5","w":7,"h":88,"l":"2m"},{"z":"z1","w":7,"h":28,"l":"3m"},
            {"z":"z5","w":7,"h":90,"l":"2m"},{"z":"z1","w":7,"h":28,"l":"3m"},
            {"z":"z5","w":7,"h":92,"l":"2m"},{"z":"z1","w":7,"h":28,"l":"3m"},
            {"z":"z5","w":7,"h":94,"l":"2m"},{"z":"z1","w":7,"h":28,"l":"3m"},
            {"z":"z5","w":7,"h":95,"l":"2m"},
            {"z":"z2","w":8,"h":40,"l":"CD"},
        ],
        'structure': '10min warm-up \u2192 5\u00d72min @ 120\u2013130% FTP / 3min recovery \u2192 cool-down',
        'execution': 'Two minutes of controlled violence. Start strong, hold on. These are short enough to survive but long enough to demand anaerobic capacity. By rep 4, your legs will burn. Rep 5 is where champions are made.',
        'cadence': '95\u2013105rpm \u2014 spin the gear, don\'t mash it',
        'position': 'Seated for reps 1\u20133. Standing for the final 30s of reps 4\u20135 if needed.',
        'rpe': '9 \u2014 near-maximal for every rep',
        'power': 'Intervals: 120\u2013130% FTP | Recovery: 50% FTP',
    },
    'Attack Repeats': {
        'duration': '45min',
        'summary': 'Sprint attacks with short recovery \u2014 neuromuscular power for race moves.',
        'viz': [
            {"z":"z2","w":16,"h":45,"l":"WU 12m"},
            {"z":"z6","w":4,"h":95,"l":"15s"},{"z":"z1","w":8,"h":28,"l":"2m"},
            {"z":"z6","w":4,"h":95,"l":"15s"},{"z":"z1","w":8,"h":28,"l":"2m"},
            {"z":"z6","w":4,"h":95,"l":"15s"},{"z":"z1","w":8,"h":28,"l":"2m"},
            {"z":"z6","w":4,"h":95,"l":"15s"},{"z":"z1","w":8,"h":28,"l":"2m"},
            {"z":"z6","w":4,"h":95,"l":"15s"},{"z":"z1","w":8,"h":28,"l":"2m"},
            {"z":"z6","w":4,"h":95,"l":"15s"},
            {"z":"z2","w":10,"h":40,"l":"CD"},
        ],
        'structure': '12min warm-up \u2192 6\u00d715sec all-out sprint / 2min recovery \u2192 cool-down',
        'execution': 'Maximum intensity. Every sprint is an all-out race attack \u2014 imagine you\'re jumping away from a group on a gravel climb. Recruit every muscle fiber. Full commitment for 15 seconds, then completely recover. Quality over quantity.',
        'cadence': '120\u2013140rpm \u2014 pure leg speed and explosive power',
        'position': 'Standing, hands in drops, bike rocking side to side',
        'rpe': '10 \u2014 absolute maximum on every sprint',
        'power': 'Sprints: 150\u2013200%+ FTP | Recovery: 45\u201350% FTP',
    },
    'Norwegian 4x8 Classic': {
        'duration': '1.25hr',
        'summary': '4\u00d78min at threshold \u2014 the Norwegian method for sustained power.',
        'viz': [
            {"z":"z2","w":12,"h":45,"l":"WU 10m"},
            {"z":"z4","w":14,"h":72,"l":"8m"},
            {"z":"z2","w":5,"h":38,"l":"4m"},
            {"z":"z4","w":14,"h":74,"l":"8m"},
            {"z":"z2","w":5,"h":38,"l":"4m"},
            {"z":"z4","w":14,"h":76,"l":"8m"},
            {"z":"z2","w":5,"h":38,"l":"4m"},
            {"z":"z4","w":14,"h":78,"l":"8m"},
            {"z":"z2","w":10,"h":40,"l":"CD"},
        ],
        'structure': '10min warm-up \u2192 4\u00d78min @ 90\u201395% FTP / 4min recovery \u2192 cool-down',
        'execution': 'The Norwegian double-threshold method \u2014 longer intervals at a controlled intensity. The key is RESTRAINT. Don\'t push above target. These should feel hard but manageable until the final set. If you\'re dying on set 3, you went too hard on set 1.',
        'cadence': '85\u201395rpm throughout \u2014 steady, metronomic',
        'position': 'Seated on hoods. Switch to drops for the final 2 minutes of each interval.',
        'rpe': 'Sets 1\u20132: 7 | Sets 3\u20134: 8',
        'power': 'Intervals: 90\u201395% FTP | Recovery: 55\u201360% FTP',
    },
    'SFR Low Cadence': {
        'duration': '1hr',
        'summary': 'Low-cadence force work \u2014 builds muscular strength for climbing and headwinds.',
        'viz': [
            {"z":"z2","w":14,"h":45,"l":"WU 10m"},
            {"z":"z3","w":12,"h":60,"l":"8m 55rpm"},
            {"z":"z2","w":6,"h":38,"l":"4m"},
            {"z":"z3","w":12,"h":62,"l":"8m 55rpm"},
            {"z":"z2","w":6,"h":38,"l":"4m"},
            {"z":"z3","w":12,"h":64,"l":"8m 55rpm"},
            {"z":"z2","w":6,"h":38,"l":"4m"},
            {"z":"z3","w":12,"h":66,"l":"8m 55rpm"},
            {"z":"z2","w":8,"h":40,"l":"CD"},
        ],
        'structure': '10min warm-up \u2192 4\u00d78min @ 80\u201385% FTP at 50\u201360rpm / 4min recovery at 90rpm \u2192 cool-down',
        'execution': 'Big gear, low cadence, steady torque. This is strength work on the bike. Keep your upper body quiet \u2014 all force through the pedals. If your knees complain, reduce resistance. Recovery spins at normal cadence to flush the legs.',
        'cadence': 'Efforts: 50\u201360rpm (force) | Recovery: 90rpm (flush)',
        'position': 'Seated, hands on hoods. Core braced, no rocking.',
        'rpe': '6\u20137 \u2014 hard on muscles, moderate on heart',
        'power': 'Efforts: 80\u201385% FTP | Recovery: 55% FTP',
    },
    'High Cadence Drills': {
        'duration': '50min',
        'summary': 'Cadence pyramids and spin-ups \u2014 neuromuscular efficiency and pedal smoothness.',
        'viz': [
            {"z":"z2","w":16,"h":45,"l":"WU 10m"},
            {"z":"z2","w":10,"h":52,"l":"100rpm"},
            {"z":"z2","w":10,"h":56,"l":"110rpm"},
            {"z":"z2","w":10,"h":60,"l":"120rpm"},
            {"z":"z2","w":10,"h":56,"l":"110rpm"},
            {"z":"z2","w":10,"h":52,"l":"100rpm"},
            {"z":"z2","w":10,"h":46,"l":"90rpm"},
            {"z":"z2","w":10,"h":42,"l":"CD"},
        ],
        'structure': '10min warm-up \u2192 Cadence pyramid: 3min each at 100\u2192110\u2192120\u2192110\u2192100rpm \u2192 repeat \u2192 cool-down',
        'execution': 'Same power, increasing cadence. Your legs spin faster while your upper body stays perfectly still. No bouncing. No hip rocking. The moment you bounce, drop 5rpm and stabilize. This is skill work \u2014 it makes every other workout more efficient.',
        'cadence': 'Progressive: 100 \u2192 110 \u2192 120 \u2192 110 \u2192 100rpm',
        'position': 'Seated, light grip, relaxed shoulders. Upper body is a statue.',
        'rpe': '4\u20135 \u2014 moderate effort, high neuromuscular focus',
        'power': '65\u201375% FTP throughout \u2014 power stays constant, only cadence changes',
    },
    'Z2 + VO2 Combo': {
        'duration': '1.5hr',
        'summary': 'Long endurance ride bookended with VO2 efforts \u2014 endurance with a bite.',
        'viz': [
            {"z":"z2","w":12,"h":45,"l":"WU 10m"},
            {"z":"z5","w":6,"h":85,"l":"3m"},
            {"z":"z1","w":4,"h":28,"l":"3m"},
            {"z":"z5","w":6,"h":87,"l":"3m"},
            {"z":"z2","w":35,"h":50,"l":"Z2 Steady 50m"},
            {"z":"z5","w":6,"h":88,"l":"3m"},
            {"z":"z1","w":4,"h":28,"l":"3m"},
            {"z":"z5","w":6,"h":90,"l":"3m"},
            {"z":"z2","w":10,"h":40,"l":"CD"},
        ],
        'structure': '10min warm-up \u2192 2\u00d73min VO2 @ 115% FTP \u2192 50min Zone 2 \u2192 2\u00d73min VO2 \u2192 cool-down',
        'execution': 'VO2 bookends around a long Z2 block. The first set is fresh \u2014 lock in your power. The Z2 middle builds endurance. The second VO2 set on tired legs builds durability. A complete session in 90 minutes.',
        'cadence': 'VO2: 95\u2013100rpm | Z2: 85\u201390rpm',
        'position': 'Drops for VO2 intervals. Alternating hoods/drops for Z2.',
        'rpe': 'VO2: 8\u20139 | Z2: 3\u20134',
        'power': 'VO2: 112\u2013118% FTP | Z2: 65\u201370% FTP',
    },
    'Tempo Blocks': {
        'duration': '1.25hr',
        'summary': 'Extended tempo efforts \u2014 muscular endurance for sustained gravel power.',
        'viz': [
            {"z":"z2","w":12,"h":45,"l":"WU 10m"},
            {"z":"z3","w":28,"h":60,"l":"20m TEMPO"},
            {"z":"z2","w":6,"h":38,"l":"5m"},
            {"z":"z3","w":28,"h":62,"l":"20m TEMPO"},
            {"z":"z2","w":10,"h":40,"l":"CD"},
        ],
        'structure': '10min warm-up \u2192 2\u00d720min @ 76\u201385% FTP / 5min recovery \u2192 cool-down',
        'execution': 'Tempo is the engine behind long races. Harder than Z2, easier than threshold. You should be able to speak in short sentences but not hold a conversation. This power range is where you\'ll spend most of your race \u2014 make it feel like home.',
        'cadence': '85\u201395rpm \u2014 steady, comfortable',
        'position': 'Race position. Practice staying aero for the full 20 minutes.',
        'rpe': '5\u20136 \u2014 moderate, sustainable discomfort',
        'power': 'Tempo: 76\u201385% FTP | Recovery: 55% FTP',
    },
    'MAF Capped Ride': {
        'duration': '1.5hr',
        'summary': 'Heart rate capped endurance \u2014 pure aerobic development below LT1.',
        'viz': [
            {"z":"z2","w":12,"h":44,"l":"WU 10m"},
            {"z":"z2","w":72,"h":48,"l":"MAF Zone 1.5hr"},
            {"z":"z2","w":12,"h":42,"l":"CD"},
        ],
        'structure': '10min warm-up \u2192 1.5hr capped at MAF heart rate (180 \u2212 age) \u2192 cool-down',
        'execution': 'Ego-free riding. Set your heart rate cap and obey it. When hills push you above MAF, reduce power \u2014 even if it means crawling. Over weeks, your pace at the same heart rate will increase. That\'s aerobic development. That\'s what wins 100+ mile races.',
        'cadence': '80\u201390rpm \u2014 whatever keeps HR below cap',
        'position': 'Comfortable. This is about time and heart rate, not power.',
        'rpe': '2\u20134 \u2014 easy, sometimes frustratingly so',
        'power': 'Variable \u2014 whatever keeps HR below MAF cap (typically 55\u201370% FTP)',
    },
    'Easy Spin': {
        'duration': '30\u201345min',
        'summary': 'Active recovery \u2014 blood flow without training stress.',
        'viz': [
            {"z":"z1","w":15,"h":35,"l":"Easy 5m"},
            {"z":"z1","w":60,"h":38,"l":"Recovery Spin 25\u201335m"},
            {"z":"z1","w":15,"h":35,"l":"Easy 5m"},
        ],
        'structure': '5min easy spin \u2192 25\u201335min @ 50\u201355% FTP \u2192 5min easy spin',
        'execution': 'The easiest ride you can do. No ego. No Strava. No pushing. Light resistance, smooth pedaling. This ride exists to flush metabolic waste and promote recovery between hard sessions. If it felt hard, you did it wrong.',
        'cadence': '85\u201395rpm \u2014 light, smooth, effortless',
        'position': 'Upright, relaxed grip, zero tension in shoulders',
        'rpe': '1\u20132 \u2014 barely above sitting on the couch',
        'power': '50\u201355% FTP maximum \u2014 err on the side of too easy',
    },
    'Double Day Simulation': {
        'duration': '2hr (AM+PM)',
        'summary': 'Two sessions in one day \u2014 AM endurance, PM intensity. Trains the double-day fatigue of multi-day events.',
        'viz': [
            {"z":"z2","w":35,"h":48,"l":"AM: Z2 1hr"},
            {"z":"z1","w":6,"h":25,"l":"REST"},
            {"z":"z2","w":14,"h":46,"l":"PM WU"},
            {"z":"z4","w":12,"h":72,"l":"10m FTP"},
            {"z":"z2","w":5,"h":38,"l":"5m"},
            {"z":"z4","w":12,"h":74,"l":"10m FTP"},
            {"z":"z2","w":8,"h":40,"l":"CD"},
        ],
        'structure': 'AM: 1hr Zone 2 | PM: 10min warm-up \u2192 2\u00d710min @ 95% FTP / 5min recovery \u2192 cool-down',
        'execution': 'The AM ride loads fatigue. The PM session tests your ability to produce quality power on pre-stressed legs. This is what stage racing and back-to-back hard days feel like. Don\u2019t skip the AM ride \u2014 that\u2019s the whole point.',
        'cadence': 'AM: 85\u201390rpm easy | PM: 85\u201395rpm on intervals',
        'position': 'AM: comfortable, any position | PM: race position for intervals',
        'rpe': 'AM: 3\u20134 | PM intervals: 7\u20138',
        'power': 'AM: 65\u201370% FTP | PM intervals: 93\u201397% FTP | PM recovery: 55% FTP',
    },
    'Progressive Fatigue': {
        'duration': '2hr',
        'summary': 'Power targets INCREASE as duration goes on \u2014 reverse-pacing that builds race-finishing strength.',
        'viz': [
            {"z":"z2","w":14,"h":45,"l":"WU 15m"},
            {"z":"z2","w":18,"h":50,"l":"Z2 30m"},
            {"z":"z3","w":16,"h":58,"l":"TEMPO 20m"},
            {"z":"z4","w":14,"h":68,"l":"G-SPOT 15m"},
            {"z":"z4","w":12,"h":75,"l":"FTP 10m"},
            {"z":"z5","w":8,"h":85,"l":"VO2 5m"},
            {"z":"z2","w":8,"h":40,"l":"CD"},
        ],
        'structure': '15min warm-up \u2192 30min Z2 \u2192 20min Tempo \u2192 15min G-Spot \u2192 10min Threshold \u2192 5min VO2 \u2192 cool-down',
        'execution': 'Each block is harder than the last. By the time you hit threshold, you\u2019ve been riding for 80+ minutes. The final VO2 effort is the test \u2014 can you go HARD when everything says stop? This is how you win the last 20 miles of a gravel race.',
        'cadence': 'Z2: 85rpm | Tempo: 88rpm | G-Spot: 90rpm | Threshold: 92rpm | VO2: 95\u2013100rpm',
        'position': 'Progressive: hoods \u2192 drops as intensity rises',
        'rpe': 'Z2: 3 | Tempo: 5 | G-Spot: 6\u20137 | Threshold: 8 | VO2: 9',
        'power': 'Z2: 65\u201370% | Tempo: 78\u201385% | G-Spot: 88\u201392% | Threshold: 95\u2013100% | VO2: 110\u2013115% FTP',
    },
    'Descending VO2 Pyramid': {
        'duration': '55min',
        'summary': '5-4-3-2-1 minute intervals at ascending power \u2014 a VO2 pyramid that gets shorter and harder.',
        'viz': [
            {"z":"z2","w":14,"h":45,"l":"WU 10m"},
            {"z":"z5","w":12,"h":80,"l":"5m"},
            {"z":"z1","w":6,"h":28,"l":"4m"},
            {"z":"z5","w":10,"h":84,"l":"4m"},
            {"z":"z1","w":5,"h":28,"l":"3m"},
            {"z":"z5","w":8,"h":88,"l":"3m"},
            {"z":"z1","w":5,"h":28,"l":"2m"},
            {"z":"z5","w":6,"h":92,"l":"2m"},
            {"z":"z1","w":4,"h":28,"l":"1m"},
            {"z":"z6","w":4,"h":95,"l":"1m"},
            {"z":"z2","w":8,"h":40,"l":"CD"},
        ],
        'structure': '10min warm-up \u2192 5min @ 108% \u2192 4min @ 112% \u2192 3min @ 116% \u2192 2min @ 120% \u2192 1min @ 130% FTP (equal rest) \u2192 cool-down',
        'execution': 'Each interval gets shorter but HARDER. The 5-minute effort is controlled. The 1-minute finale is all-out. This pyramid teaches pacing discipline \u2014 start conservative, finish violent. Recovery between efforts equals the interval just completed.',
        'cadence': '95\u2013100rpm throughout | 105rpm+ on the 1-minute finale',
        'position': 'Seated for 5-4-3 min intervals. Standing option for 2-1 min intervals.',
        'rpe': '5min: 7\u20138 | 4min: 8 | 3min: 8\u20139 | 2min: 9 | 1min: 10',
        'power': '5min: 108% | 4min: 112% | 3min: 116% | 2min: 120% | 1min: 130% FTP',
    },
    'Norwegian 4x8': {
        'duration': '1.25hr',
        'summary': '4\u00d78min at VO2max intensity \u2014 the Norwegian method pushed to aerobic ceiling.',
        'viz': [
            {"z":"z2","w":12,"h":45,"l":"WU 10m"},
            {"z":"z5","w":14,"h":80,"l":"8m"},
            {"z":"z2","w":5,"h":38,"l":"4m"},
            {"z":"z5","w":14,"h":83,"l":"8m"},
            {"z":"z2","w":5,"h":38,"l":"4m"},
            {"z":"z5","w":14,"h":86,"l":"8m"},
            {"z":"z2","w":5,"h":38,"l":"4m"},
            {"z":"z5","w":14,"h":88,"l":"8m"},
            {"z":"z2","w":10,"h":40,"l":"CD"},
        ],
        'structure': '10min warm-up \u2192 4\u00d78min @ 106\u2013112% FTP / 4min recovery \u2192 cool-down',
        'execution': 'Longer VO2 intervals demand pacing. Don\u2019t start at 120% and crater at minute 4. Hold steady at your 8-minute maximum sustainable intensity. Breathing should be maximal but controlled. If you can\u2019t finish set 4, your target was too high.',
        'cadence': '95\u2013105rpm throughout intervals',
        'position': 'Seated in drops. Aero position for final 2 minutes of each set if possible.',
        'rpe': 'Sets 1\u20132: 8 | Sets 3\u20134: 9',
        'power': 'Intervals: 106\u2013112% FTP | Recovery: 55\u201360% FTP',
    },
    'Multi-Hour Z2': {
        'duration': '4hr',
        'summary': 'The long ride. 4 hours of pure Zone 2 \u2014 massive aerobic volume for ultra-distance preparation.',
        'viz': [
            {"z":"z2","w":8,"h":46,"l":"WU"},
            {"z":"z2","w":78,"h":52,"l":"Z2 Steady 3.5hr"},
            {"z":"z2","w":8,"h":42,"l":"CD"},
        ],
        'structure': '15min progressive warm-up \u2192 3.5hr steady Zone 2 \u2192 15min cool-down',
        'execution': 'This is the big one. Four hours in the saddle. Perfectly steady Z2 \u2014 no caf\u00e9 stops, no coasting downhill, no surges. Practice race-day nutrition (80g carbs/hr). Alternate positions every 30 minutes. This ride builds the aerobic capacity that makes everything else possible.',
        'cadence': '80\u201390rpm \u2014 find your rhythm and lock it in for 4 hours',
        'position': 'Rotate every 30min: hoods \u2192 drops \u2192 tops \u2192 aero. Build position endurance.',
        'rpe': '3\u20134 throughout \u2014 if it drifts above 5, reduce power immediately',
        'power': '65\u201370% FTP \u2014 if heart rate creeps up after hour 3, drop to 60\u201365%',
    },
    'Back-to-Back Long': {
        'duration': '2.5hr + 2hr',
        'summary': 'Saturday long ride, Sunday medium ride \u2014 back-to-back volume that mimics multi-day fatigue.',
        'viz': [
            {"z":"z2","w":40,"h":52,"l":"SAT: Z2 2.5hr"},
            {"z":"z1","w":6,"h":25,"l":"SLEEP"},
            {"z":"z2","w":35,"h":48,"l":"SUN: Z2 2hr"},
            {"z":"z2","w":8,"h":42,"l":"CD"},
        ],
        'structure': 'Saturday: 2.5hr Zone 2 | Sunday: 2hr Zone 2 with 3\u00d75min tempo inserts',
        'execution': 'Saturday loads the fatigue. Sunday tests your ability to ride steady on tired legs. The Sunday tempo inserts at minutes 45, 75, and 105 simulate the surges you\u2019ll face late in a race when your legs are already cooked. This is durability training.',
        'cadence': 'Saturday: 85\u201390rpm | Sunday: 85\u201390rpm, 90\u201395rpm on tempo inserts',
        'position': 'Both days: rotate positions. Sunday tempo inserts in drops.',
        'rpe': 'Saturday: 3\u20134 | Sunday Z2: 4\u20135 | Sunday tempo: 5\u20136',
        'power': 'Both: 65\u201370% FTP | Sunday tempo: 76\u201382% FTP',
    },
    'Variable Pace Chaos': {
        'duration': '1.25hr',
        'summary': 'Unpredictable power changes \u2014 no pattern, no rhythm, pure gravel race simulation.',
        'viz': [
            {"z":"z2","w":12,"h":45,"l":"WU 10m"},
            {"z":"z3","w":5,"h":55,"l":"2m"},
            {"z":"z5","w":3,"h":82,"l":"30s"},
            {"z":"z4","w":8,"h":68,"l":"3m"},
            {"z":"z2","w":5,"h":42,"l":"90s"},
            {"z":"z5","w":4,"h":85,"l":"1m"},
            {"z":"z3","w":6,"h":58,"l":"2m"},
            {"z":"z6","w":3,"h":92,"l":"20s"},
            {"z":"z4","w":7,"h":70,"l":"3m"},
            {"z":"z2","w":4,"h":42,"l":"1m"},
            {"z":"z5","w":4,"h":88,"l":"1m"},
            {"z":"z3","w":8,"h":55,"l":"3m"},
            {"z":"z4","w":6,"h":65,"l":"2m"},
            {"z":"z2","w":8,"h":40,"l":"CD"},
        ],
        'structure': '10min warm-up \u2192 20min chaos block: random 30sec\u20133min efforts @ 85\u2013130% FTP \u2192 5min recovery \u2192 repeat \u2192 cool-down',
        'execution': 'There is no pattern. That\u2019s the point. Power jumps randomly between zones \u2014 like a gravel race where terrain, wind, and competitors dictate your effort. Don\u2019t anticipate. React. Recover when you can. Suffer when you must. This workout teaches metabolic flexibility.',
        'cadence': 'Variable \u2014 match the effort. 80rpm on tempo, 100rpm on VO2, 120rpm on sprints.',
        'position': 'Change constantly. That\u2019s the chaos.',
        'rpe': 'Varies wildly: 4\u201310 within a single block',
        'power': 'Range: 85\u2013130% FTP | No two minutes at the same power',
    },
    'Sector Simulation': {
        'duration': '1.5hr',
        'summary': 'Timed race sectors with transitions \u2014 practice racing in segments, not just riding.',
        'viz': [
            {"z":"z2","w":12,"h":45,"l":"WU 10m"},
            {"z":"z4","w":14,"h":70,"l":"SECTOR 1 12m"},
            {"z":"z2","w":5,"h":38,"l":"TRANSIT"},
            {"z":"z5","w":8,"h":82,"l":"SECTOR 2 6m"},
            {"z":"z2","w":5,"h":38,"l":"TRANSIT"},
            {"z":"z4","w":14,"h":72,"l":"SECTOR 3 12m"},
            {"z":"z2","w":5,"h":38,"l":"TRANSIT"},
            {"z":"z5","w":8,"h":85,"l":"SECTOR 4 6m"},
            {"z":"z2","w":5,"h":38,"l":"TRANSIT"},
            {"z":"z4","w":10,"h":74,"l":"FINAL 8m"},
            {"z":"z2","w":8,"h":40,"l":"CD"},
        ],
        'structure': '10min warm-up \u2192 5 sectors (12-6-12-6-8min) at race pace / 4min transit between \u2192 cool-down',
        'execution': 'Each sector is a race within the race. Sector 1: settle into race pace. Sector 2: short, hard \u2014 a hill or technical section. Sector 3: sustained power. Sector 4: another hard punch. Final sector: everything you have left. The transits are active recovery \u2014 drink, eat, prepare for the next sector.',
        'cadence': 'Sectors: 88\u201395rpm | Transits: 80\u201385rpm (easy spin)',
        'position': 'Race position on sectors. Sit up and eat during transits.',
        'rpe': 'Long sectors: 7\u20138 | Short sectors: 8\u20139 | Transits: 3',
        'power': 'Long sectors: 90\u201395% FTP | Short sectors: 105\u2013110% FTP | Transits: 55% FTP',
    },
    'Threshold Ramps': {
        'duration': '1hr',
        'summary': 'Progressive threshold ramps \u2014 start below, finish above. Teaches threshold precision.',
        'viz': [
            {"z":"z2","w":12,"h":45,"l":"WU 10m"},
            {"z":"z3","w":6,"h":58,"l":"88%"},
            {"z":"z4","w":6,"h":65,"l":"92%"},
            {"z":"z4","w":6,"h":70,"l":"96%"},
            {"z":"z4","w":6,"h":75,"l":"100%"},
            {"z":"z2","w":6,"h":38,"l":"5m"},
            {"z":"z3","w":6,"h":58,"l":"88%"},
            {"z":"z4","w":6,"h":65,"l":"92%"},
            {"z":"z4","w":6,"h":70,"l":"96%"},
            {"z":"z4","w":6,"h":75,"l":"100%"},
            {"z":"z5","w":4,"h":82,"l":"104%"},
            {"z":"z2","w":8,"h":40,"l":"CD"},
        ],
        'structure': '10min warm-up \u2192 Ramp 1: 4\u00d74min @ 88\u2192100% FTP \u2192 5min rest \u2192 Ramp 2: 5\u00d74min @ 88\u2192104% \u2192 cool-down',
        'execution': 'Start easy, finish hard. The ramp teaches you where your threshold REALLY is \u2014 the point where controlled becomes desperate. The second ramp pushes one step further. If you survive the 104% block, your FTP might be higher than you think.',
        'cadence': '88\u201392rpm throughout \u2014 steady, no changes as power rises',
        'position': 'Seated on hoods. Switch to drops above 96%.',
        'rpe': '88%: 5\u20136 | 92%: 6\u20137 | 96%: 7\u20138 | 100%: 8 | 104%: 9',
        'power': 'Ramp: 88% \u2192 92% \u2192 96% \u2192 100% \u2192 104% FTP in 4min steps',
    },
    'Descending Threshold': {
        'duration': '1hr',
        'summary': '20-15-10-5 minute threshold blocks with descending duration \u2014 intensity through fatigue.',
        'viz': [
            {"z":"z2","w":10,"h":45,"l":"WU"},
            {"z":"z4","w":24,"h":72,"l":"20m FTP"},
            {"z":"z2","w":5,"h":38,"l":"5m"},
            {"z":"z4","w":18,"h":74,"l":"15m FTP"},
            {"z":"z2","w":5,"h":38,"l":"4m"},
            {"z":"z4","w":12,"h":76,"l":"10m FTP"},
            {"z":"z2","w":4,"h":38,"l":"3m"},
            {"z":"z4","w":8,"h":78,"l":"5m FTP"},
            {"z":"z2","w":8,"h":40,"l":"CD"},
        ],
        'structure': '10min warm-up \u2192 20min @ 95% \u2192 15min @ 97% \u2192 10min @ 100% \u2192 5min @ 103% FTP (decreasing rest) \u2192 cool-down',
        'execution': 'The intervals get shorter but harder. By the 5-minute block, you\u2019re above FTP on tired legs \u2014 this is the finish-line effort. The decreasing rest (5-4-3 min) compounds the fatigue. If you can hold the 5-minute block, you\u2019re race-ready.',
        'cadence': '88\u201395rpm throughout',
        'position': 'Seated. Drops for the final 10min and 5min blocks.',
        'rpe': '20min: 7 | 15min: 7\u20138 | 10min: 8 | 5min: 9',
        'power': '20min: 95% | 15min: 97% | 10min: 100% | 5min: 103% FTP',
    },
    'G-Spot Extended': {
        'duration': '1.75hr',
        'summary': '3\u00d715min at 88\u201392% FTP \u2014 extended G-Spot for deep muscular endurance.',
        'viz': [
            {"z":"z2","w":10,"h":45,"l":"WU 10m"},
            {"z":"z3","w":5,"h":55,"l":"5m"},
            {"z":"z4","w":18,"h":68,"l":"15m G-Spot"},
            {"z":"z2","w":5,"h":38,"l":"5m"},
            {"z":"z4","w":18,"h":70,"l":"15m G-Spot"},
            {"z":"z2","w":5,"h":38,"l":"5m"},
            {"z":"z4","w":18,"h":72,"l":"15m G-Spot"},
            {"z":"z3","w":5,"h":52,"l":"5m"},
            {"z":"z2","w":8,"h":40,"l":"CD"},
        ],
        'structure': '10min warm-up \u2192 5min tempo ramp \u2192 3\u00d715min @ 88\u201392% FTP / 5min recovery \u2192 5min tempo \u2192 cool-down',
        'execution': '45 total minutes in the G-Spot zone. This is the workhorse session for gravel racers who need to hold high power for hours. The third set is where the real adaptation happens \u2014 maintaining form and power when everything wants to quit.',
        'cadence': '85\u201395rpm throughout \u2014 no grinding, no spinning',
        'position': 'Race position. Practice staying in drops for the full 15 minutes.',
        'rpe': 'Set 1: 6 | Set 2: 7 | Set 3: 7\u20138',
        'power': 'G-Spot: 88\u201392% FTP | Tempo ramp: 76\u201385% | Recovery: 55% FTP',
    },
    'Criss-Cross': {
        'duration': '1.25hr',
        'summary': 'Alternating between G-Spot and tempo in 2-minute blocks \u2014 relentless oscillation.',
        'viz': [
            {"z":"z2","w":12,"h":45,"l":"WU 10m"},
            {"z":"z4","w":6,"h":68,"l":"2m G"},
            {"z":"z3","w":6,"h":55,"l":"2m T"},
            {"z":"z4","w":6,"h":70,"l":"2m G"},
            {"z":"z3","w":6,"h":55,"l":"2m T"},
            {"z":"z4","w":6,"h":72,"l":"2m G"},
            {"z":"z3","w":6,"h":55,"l":"2m T"},
            {"z":"z2","w":5,"h":38,"l":"5m"},
            {"z":"z4","w":6,"h":70,"l":"SET 2"},
            {"z":"z3","w":6,"h":55,"l":""},
            {"z":"z4","w":6,"h":72,"l":""},
            {"z":"z3","w":6,"h":55,"l":""},
            {"z":"z4","w":6,"h":74,"l":""},
            {"z":"z2","w":8,"h":40,"l":"CD"},
        ],
        'structure': '10min warm-up \u2192 2 sets of 6\u00d72min alternating G-Spot (90%)/Tempo (80%) / 5min recovery \u2192 cool-down',
        'execution': 'No rest. Just oscillation. 2 minutes hard, 2 minutes moderate, repeat. The tempo blocks aren\u2019t recovery \u2014 they\u2019re active maintenance. Your body never fully recovers, just like mid-race gravel where terrain constantly shifts the effort.',
        'cadence': 'G-Spot: 90rpm | Tempo: 85rpm \u2014 rhythm changes every 2 minutes',
        'position': 'G-Spot: drops | Tempo: hoods. Practice transitions.',
        'rpe': 'G-Spot: 6\u20137 | Tempo: 5\u20136 | The cumulative effect hits by set 2',
        'power': 'G-Spot: 88\u201392% FTP | Tempo: 78\u201382% FTP | Recovery: 55% FTP',
    },
    'Variable Grade Simulation': {
        'duration': '1.25hr',
        'summary': 'Simulated climb with grade changes every 2 minutes \u2014 builds pacing for real-world climbs.',
        'viz': [
            {"z":"z2","w":12,"h":45,"l":"WU 10m"},
            {"z":"z3","w":6,"h":58,"l":"4%"},
            {"z":"z4","w":5,"h":70,"l":"8%"},
            {"z":"z3","w":6,"h":55,"l":"3%"},
            {"z":"z4","w":6,"h":75,"l":"10%"},
            {"z":"z3","w":5,"h":52,"l":"2%"},
            {"z":"z5","w":4,"h":82,"l":"15%"},
            {"z":"z2","w":5,"h":38,"l":"5m"},
            {"z":"z3","w":6,"h":58,"l":"4%"},
            {"z":"z4","w":6,"h":72,"l":"8%"},
            {"z":"z5","w":5,"h":80,"l":"12%"},
            {"z":"z3","w":5,"h":55,"l":"3%"},
            {"z":"z4","w":6,"h":78,"l":"10%"},
            {"z":"z2","w":8,"h":40,"l":"CD"},
        ],
        'structure': '10min warm-up \u2192 2 sets of simulated variable-grade climb (2min blocks @ 75\u2013110% FTP matching grade) / 5min recovery \u2192 cool-down',
        'execution': 'Imagine a real climb with constantly changing gradient. Power adjusts every 2 minutes \u2014 from 4% grade (tempo) to 15% grade (above threshold). The key is smooth transitions: don\u2019t surge when grade increases, don\u2019t coast when it eases.',
        'cadence': 'Low grade: 85\u201390rpm | Mid grade: 75\u201385rpm | Steep: 60\u201370rpm',
        'position': 'Low grade: seated hoods | Steep: standing or low-cadence seated',
        'rpe': 'Flat: 5 | Moderate: 7 | Steep: 8\u20139',
        'power': 'Maps to gradient: 4%=78% | 8%=92% | 10%=98% | 12%=105% | 15%=110% FTP',
    },
    'Ladder Over-Unders': {
        'duration': '1.1hr',
        'summary': 'Over-unders with increasing over-duration \u2014 the ladder adds progressive stress.',
        'viz': [
            {"z":"z2","w":12,"h":45,"l":"WU 10m"},
            {"z":"z4","w":8,"h":64,"l":"3m U"},
            {"z":"z5","w":3,"h":82,"l":"30s O"},
            {"z":"z4","w":8,"h":64,"l":"3m U"},
            {"z":"z5","w":4,"h":84,"l":"45s O"},
            {"z":"z4","w":8,"h":64,"l":"3m U"},
            {"z":"z5","w":5,"h":86,"l":"60s O"},
            {"z":"z4","w":8,"h":64,"l":"3m U"},
            {"z":"z5","w":6,"h":88,"l":"75s O"},
            {"z":"z4","w":8,"h":64,"l":"3m U"},
            {"z":"z5","w":7,"h":90,"l":"90s O"},
            {"z":"z2","w":8,"h":40,"l":"CD"},
        ],
        'structure': '10min warm-up \u2192 5\u00d7(3min under @ 90% + ladder over @ 106%: 30s, 45s, 60s, 75s, 90s) \u2192 cool-down',
        'execution': 'Same under, increasing over. Each rung of the ladder demands more time above threshold. By the 90-second over, your lactate is screaming \u2014 and you\u2019re still clearing it at 90% FTP. This builds the lactate tolerance that wins races.',
        'cadence': 'Unders: 90rpm | Overs: 95\u2013100rpm',
        'position': 'Seated throughout. Hands on drops during overs.',
        'rpe': 'Unders: 7 | 30s over: 8 | 90s over: 9\u201310',
        'power': 'Unders: 88\u201392% FTP | Overs: 104\u2013108% FTP',
    },
    'Terrain Microbursts': {
        'duration': '50min',
        'summary': '15-second microbursts every 45 seconds \u2014 the relentless terrain-driven surges of gravel.',
        'viz': [
            {"z":"z2","w":16,"h":45,"l":"WU 10m"},
            {"z":"z6","w":3,"h":90,"l":"15s"},{"z":"z2","w":4,"h":42,"l":"45s"},
            {"z":"z6","w":3,"h":90,"l":"15s"},{"z":"z2","w":4,"h":42,"l":"45s"},
            {"z":"z6","w":3,"h":90,"l":"15s"},{"z":"z2","w":4,"h":42,"l":"45s"},
            {"z":"z6","w":3,"h":90,"l":"15s"},{"z":"z2","w":4,"h":42,"l":"45s"},
            {"z":"z6","w":3,"h":90,"l":"15s"},{"z":"z2","w":4,"h":42,"l":"45s"},
            {"z":"z6","w":3,"h":90,"l":"15s"},{"z":"z2","w":4,"h":42,"l":"45s"},
            {"z":"z6","w":3,"h":90,"l":"15s"},{"z":"z2","w":4,"h":42,"l":"45s"},
            {"z":"z6","w":3,"h":90,"l":"15s"},{"z":"z2","w":4,"h":42,"l":"45s"},
            {"z":"z2","w":10,"h":40,"l":"CD"},
        ],
        'structure': '10min warm-up \u2192 2 sets of 8\u00d7(15sec @ 150% FTP / 45sec @ 65% FTP) / 5min between sets \u2192 cool-down',
        'execution': 'Every 60 seconds, EXPLODE. 15 seconds of maximum power \u2014 like hitting a rock garden, a short kicker, or responding to an attack. Then recover just enough to do it again. And again. This is what technical gravel terrain actually feels like: relentless microbursts with incomplete recovery.',
        'cadence': 'Bursts: 100\u2013130rpm (explosive) | Recovery: 85\u201390rpm',
        'position': 'Standing for every burst. Seated for recovery.',
        'rpe': 'Bursts: 9\u201310 | Recovery: 3\u20134 | Cumulative: devastating',
        'power': 'Bursts: 140\u2013160% FTP | Recovery: 60\u201365% FTP',
    },
    'Terrain Simulation Z2': {
        'duration': '2hr',
        'summary': 'Zone 2 with rolling terrain simulation \u2014 undulating power that builds fat oxidation.',
        'viz': [
            {"z":"z2","w":10,"h":45,"l":"WU"},
            {"z":"z2","w":8,"h":55,"l":"RISE"},
            {"z":"z2","w":10,"h":45,"l":"FLAT"},
            {"z":"z2","w":8,"h":55,"l":"RISE"},
            {"z":"z2","w":10,"h":42,"l":"VALLEY"},
            {"z":"z2","w":8,"h":55,"l":"RISE"},
            {"z":"z2","w":10,"h":45,"l":"FLAT"},
            {"z":"z2","w":8,"h":55,"l":"RISE"},
            {"z":"z2","w":10,"h":42,"l":"VALLEY"},
            {"z":"z2","w":8,"h":55,"l":"RISE"},
            {"z":"z2","w":8,"h":42,"l":"CD"},
        ],
        'structure': '10min warm-up \u2192 1.75hr alternating 4min @ 72\u201378% FTP (rises) and 6min @ 62\u201368% FTP (valleys) \u2192 cool-down',
        'execution': 'Stay in Zone 2 the entire time, but undulate your power to simulate rolling terrain. The rises push the top of Z2; the valleys ease off. This builds terrain-responsive pacing without leaving the aerobic zone. Your body learns to modulate power without thinking.',
        'cadence': 'Rises: 80\u201385rpm | Valleys: 88\u201392rpm',
        'position': 'Alternate: hoods on rises, drops on flats. Build position endurance.',
        'rpe': '3\u20134 throughout \u2014 never hard, but never mindless',
        'power': 'Rises: 72\u201378% FTP | Valleys: 62\u201368% FTP | All within Zone 2',
    },
    'W-Prime Depletion': {
        'duration': '1hr',
        'summary': 'Repeated efforts that systematically drain your anaerobic battery \u2014 then test what\u2019s left.',
        'viz': [
            {"z":"z2","w":12,"h":45,"l":"WU 10m"},
            {"z":"z5","w":8,"h":82,"l":"3m"},
            {"z":"z1","w":5,"h":28,"l":"3m"},
            {"z":"z5","w":8,"h":84,"l":"3m"},
            {"z":"z1","w":5,"h":28,"l":"3m"},
            {"z":"z5","w":8,"h":86,"l":"3m"},
            {"z":"z1","w":5,"h":28,"l":"3m"},
            {"z":"z5","w":8,"h":88,"l":"3m"},
            {"z":"z1","w":5,"h":28,"l":"2m"},
            {"z":"z5","w":8,"h":90,"l":"3m ALL OUT"},
            {"z":"z2","w":8,"h":40,"l":"CD"},
        ],
        'structure': '10min warm-up \u2192 5\u00d73min @ 108\u2013115% FTP with DECREASING recovery (3-3-3-2-0min) \u2192 cool-down',
        'execution': 'Each effort chips away at your W\u2019 (anaerobic work capacity). Recovery gets shorter \u2014 by rep 5, there\u2019s no rest at all. The final effort with a depleted W\u2019 is the moment of truth. Can you still produce power when the tank is empty? That\u2019s what decides gravel races.',
        'cadence': '95\u2013100rpm throughout \u2014 spin, don\u2019t mash when depleted',
        'position': 'Seated for reps 1\u20133. Standing option for reps 4\u20135 when desperate.',
        'rpe': 'Rep 1: 7\u20138 | Rep 3: 8\u20139 | Rep 5: 10 (empty tank effort)',
        'power': 'Reps 1\u20134: 108\u2013112% FTP | Rep 5: all-out (target 115%+ FTP)',
    },
    '90sec Repeats': {
        'duration': '50min',
        'summary': '90-second anaerobic repeats \u2014 the sweet spot between sprint and sustained suffering.',
        'viz': [
            {"z":"z2","w":14,"h":45,"l":"WU 10m"},
            {"z":"z5","w":6,"h":88,"l":"90s"},{"z":"z1","w":6,"h":28,"l":"3m"},
            {"z":"z5","w":6,"h":90,"l":"90s"},{"z":"z1","w":6,"h":28,"l":"3m"},
            {"z":"z5","w":6,"h":92,"l":"90s"},{"z":"z1","w":6,"h":28,"l":"3m"},
            {"z":"z5","w":6,"h":93,"l":"90s"},{"z":"z1","w":6,"h":28,"l":"3m"},
            {"z":"z5","w":6,"h":95,"l":"90s"},{"z":"z1","w":6,"h":28,"l":"3m"},
            {"z":"z5","w":6,"h":95,"l":"90s"},
            {"z":"z2","w":8,"h":40,"l":"CD"},
        ],
        'structure': '10min warm-up \u2192 6\u00d790sec @ 120\u2013130% FTP / 3min recovery \u2192 cool-down',
        'execution': '90 seconds is long enough to hurt, short enough to survive. Pure anaerobic capacity work. Each rep should feel like a 2-minute climb where you\u2019re fighting to hold the wheel ahead of you. Hold form \u2014 when your upper body starts flailing, the power is going to the wrong places.',
        'cadence': '95\u2013105rpm \u2014 high cadence reduces muscular strain',
        'position': 'Seated for first 60s. Standing for final 30s if needed.',
        'rpe': '9 across all reps \u2014 consistently near-maximal',
        'power': 'Reps: 120\u2013130% FTP | Recovery: 50% FTP',
    },
    'Sprint Buildups': {
        'duration': '45min',
        'summary': 'Progressive sprint buildups \u2014 from moderate to maximum over 20 seconds.',
        'viz': [
            {"z":"z2","w":18,"h":45,"l":"WU 12m"},
            {"z":"z3","w":3,"h":55,"l":""},{"z":"z5","w":3,"h":78,"l":""},{"z":"z6","w":3,"h":95,"l":"MAX"},
            {"z":"z1","w":8,"h":28,"l":"3m"},
            {"z":"z3","w":3,"h":55,"l":""},{"z":"z5","w":3,"h":80,"l":""},{"z":"z6","w":3,"h":95,"l":"MAX"},
            {"z":"z1","w":8,"h":28,"l":"3m"},
            {"z":"z3","w":3,"h":55,"l":""},{"z":"z5","w":3,"h":82,"l":""},{"z":"z6","w":3,"h":95,"l":"MAX"},
            {"z":"z1","w":8,"h":28,"l":"3m"},
            {"z":"z3","w":3,"h":55,"l":""},{"z":"z5","w":3,"h":84,"l":""},{"z":"z6","w":3,"h":95,"l":"MAX"},
            {"z":"z2","w":12,"h":40,"l":"CD"},
        ],
        'structure': '12min warm-up \u2192 4\u00d720sec buildups (moderate \u2192 hard \u2192 all-out over 20sec) / 3min recovery \u2192 cool-down',
        'execution': 'Each buildup starts moderate and finishes at absolute maximum. Don\u2019t go all-out from the start \u2014 the buildup teaches neuromuscular recruitment patterns. By the final 5 seconds, you should be producing peak power. Full recovery between efforts \u2014 this is quality, not fatigue work.',
        'cadence': 'Start: 90rpm | Build to: 120\u2013140rpm by the end of each sprint',
        'position': 'Start seated, transition to standing as power builds. Full sprint position at peak.',
        'rpe': 'Start of each buildup: 5 | Peak: 10',
        'power': 'Build: 100% \u2192 150% \u2192 200%+ FTP over 20 seconds | Recovery: 45\u201350% FTP',
    },
    'Double Threshold': {
        'duration': '1.5hr',
        'summary': 'Two threshold sessions separated by Z2 \u2014 the Norwegian double-session in one ride.',
        'viz': [
            {"z":"z2","w":10,"h":45,"l":"WU"},
            {"z":"z4","w":14,"h":72,"l":"8m FTP"},
            {"z":"z2","w":4,"h":38,"l":"4m"},
            {"z":"z4","w":14,"h":74,"l":"8m FTP"},
            {"z":"z2","w":14,"h":48,"l":"Z2 20m"},
            {"z":"z4","w":14,"h":72,"l":"8m FTP"},
            {"z":"z2","w":4,"h":38,"l":"4m"},
            {"z":"z4","w":14,"h":76,"l":"8m FTP"},
            {"z":"z2","w":8,"h":40,"l":"CD"},
        ],
        'structure': '10min warm-up \u2192 2\u00d78min @ 92\u201395% FTP \u2192 20min Z2 \u2192 2\u00d78min @ 92\u201395% FTP \u2192 cool-down',
        'execution': 'The Z2 middle block is NOT recovery \u2014 it\u2019s an aerobic buffer that simulates the pattern of real racing. The second pair of threshold intervals on partially fatigued legs is where the magic happens. This builds lactate clearance capacity more effectively than a single continuous block.',
        'cadence': 'Threshold: 88\u201395rpm | Z2: 85\u201390rpm',
        'position': 'Threshold: drops, race position | Z2: hoods, relaxed',
        'rpe': 'First pair: 7\u20138 | Z2: 3\u20134 | Second pair: 8\u20139',
        'power': 'Threshold: 92\u201395% FTP | Z2 block: 65\u201370% FTP | Recovery: 55% FTP',
    },
    'Force Repeats': {
        'duration': '55min',
        'summary': 'Short, maximal-force efforts at very low cadence \u2014 pure neuromuscular strength.',
        'viz': [
            {"z":"z2","w":16,"h":45,"l":"WU 12m"},
            {"z":"z4","w":6,"h":65,"l":"2m 50rpm"},
            {"z":"z2","w":6,"h":40,"l":"3m 90rpm"},
            {"z":"z4","w":6,"h":68,"l":"2m 50rpm"},
            {"z":"z2","w":6,"h":40,"l":"3m 90rpm"},
            {"z":"z4","w":6,"h":70,"l":"2m 50rpm"},
            {"z":"z2","w":6,"h":40,"l":"3m 90rpm"},
            {"z":"z4","w":6,"h":72,"l":"2m 50rpm"},
            {"z":"z2","w":6,"h":40,"l":"3m 90rpm"},
            {"z":"z4","w":6,"h":74,"l":"2m 50rpm"},
            {"z":"z2","w":6,"h":40,"l":"3m 90rpm"},
            {"z":"z4","w":6,"h":76,"l":"2m 50rpm"},
            {"z":"z2","w":10,"h":40,"l":"CD"},
        ],
        'structure': '12min warm-up \u2192 6\u00d72min @ 85\u201395% FTP at 45\u201355rpm / 3min recovery at 90rpm \u2192 cool-down',
        'execution': 'Big gear. Low cadence. Maximum force per pedal stroke. This is strength training on the bike. Keep your core engaged and upper body still \u2014 all force through the pedals. If your knees protest, reduce the gear by one. Recovery spins at normal cadence flush the muscular fatigue.',
        'cadence': 'Efforts: 45\u201355rpm (force) | Recovery: 90rpm (flush)',
        'position': 'Seated, hands on hoods, core braced. No rocking, no pulling on bars.',
        'rpe': '7\u20138 \u2014 muscularly hard, cardiovascularly moderate',
        'power': 'Efforts: 85\u201395% FTP | Recovery: 55% FTP',
    },
    'Cadence Pyramids': {
        'duration': '50min',
        'summary': 'Full cadence pyramid from 70rpm to 130rpm and back \u2014 builds complete pedaling range.',
        'viz': [
            {"z":"z2","w":14,"h":45,"l":"WU 10m"},
            {"z":"z2","w":6,"h":42,"l":"70rpm"},
            {"z":"z2","w":6,"h":48,"l":"80rpm"},
            {"z":"z2","w":6,"h":52,"l":"90rpm"},
            {"z":"z2","w":6,"h":56,"l":"100rpm"},
            {"z":"z2","w":6,"h":60,"l":"110rpm"},
            {"z":"z2","w":6,"h":64,"l":"120rpm"},
            {"z":"z2","w":6,"h":68,"l":"130rpm"},
            {"z":"z2","w":6,"h":64,"l":"120rpm"},
            {"z":"z2","w":6,"h":60,"l":"110rpm"},
            {"z":"z2","w":6,"h":56,"l":"100rpm"},
            {"z":"z2","w":6,"h":52,"l":"90rpm"},
            {"z":"z2","w":6,"h":48,"l":"80rpm"},
            {"z":"z2","w":6,"h":42,"l":"70rpm"},
            {"z":"z2","w":8,"h":40,"l":"CD"},
        ],
        'structure': '10min warm-up \u2192 Pyramid: 2min each at 70\u219280\u219290\u2192100\u2192110\u2192120\u2192130\u2192120\u2192...\u219270rpm \u2192 cool-down',
        'execution': 'Same power throughout \u2014 only cadence changes. The low end (70rpm) is muscular strength. The high end (130rpm) is neuromuscular speed. The transition zones are where most people are inefficient. This pyramid fills those gaps.',
        'cadence': '70rpm \u2192 130rpm \u2192 70rpm in 10rpm steps, 2min each',
        'position': 'Seated throughout. Zero upper-body movement at all cadences.',
        'rpe': 'Low cadence: 5 (muscular) | Mid: 3 | High: 5 (coordination)',
        'power': '65\u201375% FTP constant \u2014 power does not change, only cadence',
    },
    'Endurance with Spikes': {
        'duration': '1.5hr',
        'summary': 'Long Z2 ride peppered with random high-intensity spikes \u2014 endurance meets unpredictability.',
        'viz': [
            {"z":"z2","w":12,"h":48,"l":"WU"},
            {"z":"z2","w":10,"h":50,"l":"Z2"},
            {"z":"z5","w":3,"h":85,"l":"30s"},
            {"z":"z2","w":12,"h":50,"l":"Z2"},
            {"z":"z6","w":2,"h":92,"l":"15s"},
            {"z":"z2","w":14,"h":50,"l":"Z2"},
            {"z":"z5","w":4,"h":82,"l":"1m"},
            {"z":"z2","w":10,"h":50,"l":"Z2"},
            {"z":"z6","w":2,"h":95,"l":"20s"},
            {"z":"z2","w":12,"h":50,"l":"Z2"},
            {"z":"z5","w":3,"h":85,"l":"30s"},
            {"z":"z2","w":8,"h":42,"l":"CD"},
        ],
        'structure': '10min warm-up \u2192 75min Zone 2 with 5\u20136 random spikes (15\u201360sec @ 120\u2013150% FTP) scattered throughout \u2192 cool-down',
        'execution': 'Mostly Zone 2, with occasional violence. The spikes simulate race moments \u2014 a sudden climb, an attack, a technical section that demands a burst. Return to Z2 immediately after each spike. The aerobic system learns to absorb these disruptions without derailing.',
        'cadence': 'Z2: 85\u201390rpm | Spikes: 100\u2013120rpm (explosive)',
        'position': 'Z2: comfortable, rotating | Spikes: race position, aggressive',
        'rpe': 'Z2: 3\u20134 | Spikes: 8\u201310 | Overall: mostly easy with moments of violence',
        'power': 'Z2: 65\u201370% FTP | Spikes: 120\u2013150% FTP',
    },
    'Extended Tempo': {
        'duration': '1.5hr',
        'summary': '45 minutes of continuous tempo \u2014 the longest sustained effort below threshold.',
        'viz': [
            {"z":"z2","w":12,"h":45,"l":"WU 10m"},
            {"z":"z3","w":5,"h":55,"l":"RAMP"},
            {"z":"z3","w":52,"h":62,"l":"TEMPO 45min"},
            {"z":"z3","w":5,"h":55,"l":"RAMP DOWN"},
            {"z":"z2","w":10,"h":40,"l":"CD"},
        ],
        'structure': '10min warm-up \u2192 5min ramp to tempo \u2192 45min @ 78\u201385% FTP \u2192 5min ramp down \u2192 cool-down',
        'execution': '45 unbroken minutes at tempo. No intervals, no recovery, no escape. This builds the muscular endurance for hours of sustained gravel racing. The first 15 minutes feel easy. Minutes 30\u201345 reveal your actual tempo fitness. Hold power. Hold position. Hold focus.',
        'cadence': '85\u201395rpm throughout \u2014 metronomic consistency',
        'position': 'Race position for the full 45 minutes. Practice aero comfort.',
        'rpe': 'Minutes 1\u201315: 5 | Minutes 15\u201330: 5\u20136 | Minutes 30\u201345: 6\u20137',
        'power': 'Tempo: 78\u201385% FTP | Ramps: 70\u201378% FTP',
    },
    'LT1 Assessment': {
        'duration': '1hr',
        'summary': 'Step test to find your LT1 \u2014 the aerobic threshold that defines your endurance ceiling.',
        'viz': [
            {"z":"z2","w":14,"h":45,"l":"WU 10m"},
            {"z":"z2","w":10,"h":48,"l":"STEP 1"},
            {"z":"z2","w":10,"h":52,"l":"STEP 2"},
            {"z":"z2","w":10,"h":56,"l":"STEP 3"},
            {"z":"z3","w":10,"h":60,"l":"STEP 4"},
            {"z":"z3","w":10,"h":64,"l":"STEP 5"},
            {"z":"z3","w":10,"h":68,"l":"STEP 6"},
            {"z":"z4","w":8,"h":72,"l":"STEP 7"},
            {"z":"z2","w":10,"h":40,"l":"CD"},
        ],
        'structure': '10min warm-up \u2192 7 steps of 5min each, starting at 55% FTP and increasing by 5% per step \u2192 cool-down',
        'execution': 'This is an assessment, not a workout. Increase power by 5% FTP every 5 minutes. At each step, note your heart rate and breathing. LT1 is where breathing first shifts from nasal to mouth, or where heart rate-to-power ratio breaks from linear. Once identified, LT1 becomes your endurance ceiling for all Z2 work.',
        'cadence': '90rpm throughout all steps \u2014 cadence must stay constant',
        'position': 'Seated, hoods. Don\u2019t change position between steps \u2014 it affects heart rate.',
        'rpe': 'Steps 1\u20133: 2\u20133 | Step 4\u20135: 4\u20135 | Step 6\u20137: 6\u20137',
        'power': 'Steps: 55% \u2192 60% \u2192 65% \u2192 70% \u2192 75% \u2192 80% \u2192 85% FTP',
    },
    'Active Recovery': {
        'duration': '30min',
        'summary': 'The gentlest ride possible \u2014 active recovery to flush fatigue between hard sessions.',
        'viz': [
            {"z":"z1","w":20,"h":32,"l":"Easy 5m"},
            {"z":"z1","w":55,"h":36,"l":"Recovery 20m"},
            {"z":"z1","w":20,"h":32,"l":"Easy 5m"},
        ],
        'structure': '5min easy spin \u2192 20min @ 45\u201350% FTP \u2192 5min easy spin',
        'execution': 'Easier than easy. If you\u2019re sweating, you\u2019re going too hard. This ride exists only to promote blood flow and recovery. Zero training stress. Zero Strava bragging. The discipline to ride this easy is harder than any interval session.',
        'cadence': '85\u201395rpm \u2014 light, smooth, no resistance',
        'position': 'Upright, relaxed. Hands on tops. Zero tension anywhere.',
        'rpe': '1 \u2014 easier than walking',
        'power': '45\u201350% FTP maximum \u2014 if in doubt, go easier',
    },
}

# ── Showcase eligibility rules ──
# Each workout can have constraints: min_dist, max_dist, min_climbing,
# _never_showcase (assessments/taper/recovery that don't demonstrate training).
# If ALL workouts in a category fail eligibility, the category is skipped.
SHOWCASE_ELIGIBILITY = {
    # Durability — 2hr base ride requires a race long enough to justify it
    'Tired VO2max':          {'min_dist': 60},
    'Double Day Simulation': {'min_dist': 200},   # ultra/multi-day only
    'Progressive Fatigue':   {},                   # universal

    # VO2max — irrelevant for ultra-bikepacking
    '5x3 VO2 Classic':        {'max_dist': 400},
    'Descending VO2 Pyramid': {'max_dist': 400},
    'Norwegian 4x8':          {'max_dist': 400},

    # HVLI_Extended — volume work needs distance to justify
    'HVLI Extended Z2':  {'min_dist': 80},
    'Multi-Hour Z2':     {'min_dist': 100},
    'Back-to-Back Long': {'min_dist': 120},

    # Race_Simulation — competitive race concepts, not ultra-endurance
    'Breakaway Simulation': {'max_dist': 300},
    'Variable Pace Chaos':  {'max_dist': 300},
    'Sector Simulation':    {'max_dist': 300},

    # Threshold — universal
    'Single Sustained Threshold': {},
    'Threshold Ramps':            {},
    'Descending Threshold':       {},

    # G_Spot — universal, extended version needs endurance
    'G-Spot Standard':  {},
    'G-Spot Extended':  {'min_dist': 60},
    'Criss-Cross':      {},

    # Climbing — only show if climbing demand warrants it
    'Seated/Standing Climbs':    {'min_climbing': 5},
    'Variable Grade Simulation': {'min_climbing': 5},

    # Over_Under — universal
    'Classic Over-Unders': {},
    'Ladder Over-Unders':  {},

    # Gravel_Specific — surging not relevant for ultra
    'Surge and Settle':    {'max_dist': 300},
    'Terrain Microbursts': {'max_dist': 300},

    # Endurance
    'Pre-Race Openers':    {'_never_showcase': True},   # taper, not training
    'Terrain Simulation Z2': {},                        # universal

    # Critical_Power — high-intensity, not for ultra
    'Above CP Repeats':  {'max_dist': 300},
    'W-Prime Depletion': {'max_dist': 300},

    # Anaerobic — short-race focused
    '2min Killers':  {'max_dist': 200},
    '90sec Repeats': {'max_dist': 200},

    # Sprint — competitive race context
    'Attack Repeats':  {'max_dist': 200},
    'Sprint Buildups': {'max_dist': 200},

    # Norwegian_Double — irrelevant for ultra
    'Norwegian 4x8 Classic': {'max_dist': 400},
    'Double Threshold':      {'max_dist': 400},

    # SFR/Force — universal (grinding is always relevant)
    'SFR Low Cadence': {},
    'Force Repeats':   {},

    # Cadence — universal
    'High Cadence Drills': {},
    'Cadence Pyramids':    {},

    # Blended
    'Z2 + VO2 Combo':      {'max_dist': 300},
    'Endurance with Spikes': {},

    # Tempo — universal
    'Tempo Blocks':    {},
    'Extended Tempo':  {'min_dist': 60},

    # Assessments — never showcase
    'MAF Capped Ride':  {'_never_showcase': True},
    'LT1 Assessment':   {'_never_showcase': True},

    # Recovery — never showcase
    'Easy Spin':        {'_never_showcase': True},
    'Active Recovery':  {'_never_showcase': True},
}


def _workout_eligible(name: str, distance_mi: float, demands: dict) -> bool:
    """Check if a workout passes eligibility for this race context."""
    rules = SHOWCASE_ELIGIBILITY.get(name, {})
    if rules.get('_never_showcase'):
        return False
    if 'min_dist' in rules and distance_mi < rules['min_dist']:
        return False
    if 'max_dist' in rules and distance_mi > rules['max_dist']:
        return False
    if 'min_climbing' in rules and demands.get('climbing', 0) < rules['min_climbing']:
        return False
    return True


def build_train_for_race(rd: dict) -> str:
    """Build [08] Train for This Race section with showcase workouts."""
    slug = rd['slug']
    race_name = rd['name']

    # Load race-pack preview JSON
    preview_path = Path(__file__).resolve().parent.parent / 'web' / 'race-packs' / f'{slug}.json'
    if not preview_path.exists():
        return ''

    try:
        with open(preview_path) as f:
            preview = json.load(f)
    except (json.JSONDecodeError, OSError):
        return ''

    demands = preview.get('demands', {})
    top_categories = preview.get('top_categories', [])
    race_overlay = preview.get('race_overlay', {})
    distance_mi = preview.get('distance_mi', 0)

    if not demands or not top_categories:
        return ''

    # Build demand bars (8 dimensions, each 0-10)
    dim_labels = {
        'durability': 'Durability',
        'climbing': 'Climbing',
        'vo2_power': 'VO2 Power',
        'threshold': 'Threshold',
        'technical': 'Technical',
        'heat_resilience': 'Heat',
        'altitude': 'Altitude',
        'race_specificity': 'Race Specificity',
    }
    demand_bars = []
    for dim_key in ['durability', 'climbing', 'vo2_power', 'threshold',
                     'technical', 'heat_resilience', 'altitude', 'race_specificity']:
        score = demands.get(dim_key, 0)
        label = dim_labels.get(dim_key, dim_key)
        pct = score * 10  # 0-10 -> 0-100%
        demand_bars.append(
            f'<div class="rl-pack-demand">'
            f'<span class="rl-pack-demand-label">{esc(label)}</span>'
            f'<div class="rl-pack-demand-track">'
            f'<div class="rl-pack-demand-fill" style="width:{pct}%"></div>'
            f'</div>'
            f'<span class="rl-pack-demand-score">{score}</span>'
            f'</div>'
        )
    demands_html = '\n      '.join(demand_bars)

    # Build 5 showcase workout cards — walk the full ranked list,
    # skip categories where no workout passes eligibility.
    workout_cards = []
    card_idx = 0
    for tc in top_categories:
        if card_idx >= 5:
            break
        cat_name = tc['category'].replace('_', ' ')
        workouts_list = tc.get('workouts', [])
        if not workouts_list:
            continue
        # Filter to workouts that exist in showcase AND pass eligibility
        eligible = [w for w in workouts_list
                    if w in WORKOUT_SHOWCASE
                    and _workout_eligible(w, distance_mi, demands)]
        if not eligible:
            continue  # skip this category entirely
        # Deterministic rotation among eligible workouts
        h = int(hashlib.md5(f"{slug}-{tc['category']}".encode()).hexdigest(), 16)
        workout_name = eligible[h % len(eligible)]
        showcase = WORKOUT_SHOWCASE.get(workout_name)
        if not showcase:
            continue
        i = card_idx
        card_idx += 1

        # Build viz HTML (static, no JS needed)
        viz_blocks = []
        for block in showcase['viz']:
            h_px = int(block['h'] * 0.95)
            z_cls = block['z']
            w_pct = block['w']
            lbl = esc(block.get('l', ''))
            viz_blocks.append(
                f'<div class="rl-pack-viz-block rl-pack-viz-{z_cls}" '
                f'style="flex-basis:{w_pct}%;height:{h_px}px;">'
                f'<span class="rl-pack-viz-label">{lbl}</span></div>'
            )
        viz_html = '\n            '.join(viz_blocks)

        # Build expanded detail HTML
        # Race overlay items (filter to non-empty)
        overlay_items = []
        if race_overlay.get('heat'):
            overlay_items.append(
                f'<div class="rl-pack-wo-overlay-item">'
                f'<span class="rl-pack-wo-overlay-tag">HEAT PREP</span> '
                f'{esc(race_overlay["heat"])}</div>')
        if race_overlay.get('nutrition'):
            overlay_items.append(
                f'<div class="rl-pack-wo-overlay-item">'
                f'<span class="rl-pack-wo-overlay-tag">NUTRITION</span> '
                f'{esc(race_overlay["nutrition"])}</div>')
        if race_overlay.get('altitude'):
            overlay_items.append(
                f'<div class="rl-pack-wo-overlay-item">'
                f'<span class="rl-pack-wo-overlay-tag">ALTITUDE</span> '
                f'{esc(race_overlay["altitude"])}</div>')
        if race_overlay.get('terrain'):
            overlay_items.append(
                f'<div class="rl-pack-wo-overlay-item">'
                f'<span class="rl-pack-wo-overlay-tag">TERRAIN</span> '
                f'{esc(race_overlay["terrain"])}</div>')
        overlay_html = '\n            '.join(overlay_items) if overlay_items else ''

        overlay_section = ''
        if overlay_html:
            overlay_section = (
                f'<div class="rl-pack-wo-overlay">'
                f'<div class="rl-pack-wo-overlay-title">RACE-SPECIFIC: {esc(race_name.upper())}</div>'
                f'{overlay_html}</div>'
            )

        context_text = tc.get('workout_context', '')
        context_line = (
            f'          <p class="rl-pack-workout-context">{esc(context_text)}</p>\n'
            if context_text else ''
        )

        card_html = (
            f'<div class="rl-pack-workout" data-workout-idx="{i}" data-workout-cat="{esc(tc["category"])}">\n'
            f'          <div class="rl-cfg-phase-badge" style="display:none;"></div>\n'
            f'          <div class="rl-pack-workout-header">\n'
            f'            <div class="rl-pack-workout-info">\n'
            f'              <span class="rl-pack-workout-cat">{esc(cat_name)}</span>\n'
            f'              <span class="rl-pack-workout-name">{esc(workout_name)}</span>\n'
            f'            </div>\n'
            f'            <div class="rl-pack-workout-meta">\n'
            f'              <span class="rl-pack-workout-dur">{esc(showcase["duration"])}</span>\n'
            f'              <span class="rl-pack-workout-expand">+</span>\n'
            f'            </div>\n'
            f'          </div>\n'
            f'          <p class="rl-pack-workout-summary">{esc(showcase["summary"])}</p>\n'
            f'{context_line}'
            f'          <div class="rl-cfg-level-note" style="display:none;"></div>\n'
            f'          <div class="rl-pack-workout-viz">\n'
            f'            {viz_html}\n'
            f'          </div>\n'
            f'          <div class="rl-pack-workout-detail" style="display:none;">\n'
            f'            <div class="rl-pack-wo-field">\n'
            f'              <span class="rl-pack-wo-label">STRUCTURE</span>\n'
            f'              <span class="rl-pack-wo-value">{esc(showcase["structure"])}</span>\n'
            f'            </div>\n'
            f'            <div class="rl-pack-wo-field">\n'
            f'              <span class="rl-pack-wo-label">EXECUTION</span>\n'
            f'              <span class="rl-pack-wo-value">{esc(showcase["execution"])}</span>\n'
            f'            </div>\n'
            f'            <div class="rl-pack-wo-field">\n'
            f'              <span class="rl-pack-wo-label">POWER</span>\n'
            f'              <span class="rl-pack-wo-value">{esc(showcase["power"])}</span>\n'
            f'            </div>\n'
            f'            <div class="rl-pack-wo-field">\n'
            f'              <span class="rl-pack-wo-label">CADENCE</span>\n'
            f'              <span class="rl-pack-wo-value">{esc(showcase["cadence"])}</span>\n'
            f'            </div>\n'
            f'            <div class="rl-pack-wo-field">\n'
            f'              <span class="rl-pack-wo-label">POSITION</span>\n'
            f'              <span class="rl-pack-wo-value">{esc(showcase["position"])}</span>\n'
            f'            </div>\n'
            f'            <div class="rl-pack-wo-field">\n'
            f'              <span class="rl-pack-wo-label">RPE</span>\n'
            f'              <span class="rl-pack-wo-value">{esc(showcase["rpe"])}</span>\n'
            f'            </div>\n'
            f'            {overlay_section}\n'
            f'          </div>\n'
            f'        </div>'
        )
        workout_cards.append(card_html)

    workouts_html = '\n      '.join(workout_cards)
    num_workouts = len(workout_cards)

    plan_url = f"{TRAINING_PLANS_URL}?race={esc(slug)}"

    # Embed race data for client-side configurator
    race_data_js = {
        'slug': slug,
        'race_name': race_name,
        'date_specific': rd['vitals'].get('date_specific', ''),
        'distance_mi': distance_mi,
    }
    race_data_json = _safe_json_for_script(race_data_js, ensure_ascii=False, separators=(',', ':'))

    # Workout toggle + panel — only render if we have workouts
    workouts_section = ''
    if num_workouts > 0:
        workouts_section = (
            f'<div class="rl-pack-workouts-toggle" id="rl-pack-workouts-toggle">\n'
            f'        <button type="button" class="rl-pack-toggle-btn" id="rl-pack-toggle-btn" '
            f'aria-expanded="false" aria-controls="rl-pack-workouts-panel">\n'
            f'          <span id="rl-pack-toggle-text">SEE {num_workouts} SAMPLE WORKOUTS</span>\n'
            f'          <span class="rl-pack-toggle-arrow" aria-hidden="true">&#9662;</span>\n'
            f'        </button>\n'
            f'      </div>\n'
            f'      <div class="rl-pack-workouts" id="rl-pack-workouts-panel" '
            f'style="display:none;" role="region" aria-label="Sample workouts">\n'
            f'        <h3 class="rl-pack-subtitle">{num_workouts} WORKOUTS BUILT FOR THIS RACE</h3>\n'
            f'        <p class="rl-pack-workouts-intro">Each workout below is selected from our '
            f'archetype library based on {esc(race_name)}&rsquo;s specific demands. '
            f'Click any workout to see the full execution protocol.</p>\n'
            f'        {workouts_html}\n'
            f'      </div>'
        )

    return f'''<section id="train-for-race" class="rl-section rl-fade-section">
    <div class="rl-section-header">
      <span class="rl-section-kicker">[08]</span>
      <h2 class="rl-section-title">Train for {esc(race_name)}</h2>
    </div>
    <div class="rl-section-body">
      <div class="rl-pack-demands">
        <h3 class="rl-pack-subtitle">RACE DEMAND PROFILE</h3>
        <div class="rl-pack-demands-inline">
          {demands_html}
        </div>
      </div>
      <div class="rl-cfg-bar">
        <h3 class="rl-cfg-title">PREVIEW YOUR TRAINING PLAN</h3>
        <div class="rl-cfg-inputs">
          <div class="rl-cfg-field">
            <label class="rl-cfg-label" for="rl-cfg-level">YOUR FITNESS</label>
            <select id="rl-cfg-level" class="rl-cfg-select">
              <option value="beginner">Beginner</option>
              <option value="intermediate" selected>Intermediate</option>
              <option value="advanced">Advanced</option>
              <option value="elite">Elite</option>
            </select>
          </div>
          <div class="rl-cfg-field">
            <label class="rl-cfg-label" for="rl-cfg-hours">HOURS/WEEK</label>
            <select id="rl-cfg-hours" class="rl-cfg-select">
              <option value="6-8">6&ndash;8 hrs</option>
              <option value="8-12" selected>8&ndash;12 hrs</option>
              <option value="12-16">12&ndash;16 hrs</option>
              <option value="16+">16+ hrs</option>
            </select>
          </div>
          <div class="rl-cfg-field">
            <label class="rl-cfg-label" for="rl-cfg-date">RACE DATE</label>
            <input type="date" id="rl-cfg-date" class="rl-cfg-input">
          </div>
        </div>
        <button type="button" id="rl-cfg-btn" class="rl-btn rl-cfg-preview-btn">PREVIEW MY PLAN</button>
      </div>
      <div id="rl-cfg-summary" class="rl-cfg-summary" style="display:none;" aria-live="polite" role="region" aria-label="Training plan preview">
        <div class="rl-cfg-summary-title" id="rl-cfg-summary-title"></div>
        <div class="rl-cfg-timeline" id="rl-cfg-timeline"></div>
        <div class="rl-cfg-timeline-bar" id="rl-cfg-timeline-bar"></div>
        <div class="rl-cfg-details" id="rl-cfg-details"></div>
      </div>
      <div class="rl-pack-cta" id="rl-pack-cta-default">
        <a href="{plan_url}" class="rl-btn" id="rl-pack-cta-link">BUILD MY PLAN &mdash; $15/WK</a>
        <p class="rl-pack-cta-detail">Race-specific. Built for {esc(race_name)}. $15/week, capped at $249.</p>
      </div>
      <div class="rl-pack-cta rl-cfg-cta" id="rl-cfg-cta" style="display:none;" aria-hidden="true">
        <a href="{plan_url}" class="rl-btn rl-cfg-cta-btn" id="rl-cfg-cta-link" tabindex="-1">BUILD MY PLAN</a>
        <p class="rl-pack-cta-detail" id="rl-cfg-cta-detail"></p>
      </div>
      {workouts_section}
    </div>
    <script>window.__GG_RACE_DATA__={race_data_json};</script>
  </section>'''


def build_logistics_section(rd: dict) -> str:
    """Build [09] Race Logistics section."""
    lg = rd['logistics']

    items_data = [
        ('Airport', lg.get('airport', '')),
        ('Lodging', lg.get('lodging_strategy', '')),
        ('Food', lg.get('food', '')),
        ('Packet Pickup', lg.get('packet_pickup', '')),
        ('Parking', lg.get('parking', '')),
    ]

    # Filter out empty items and placeholder text ("Check X website/calendars")
    items_data = [(label, val) for label, val in items_data
                  if val and not re.match(r'^Check\s', val, re.IGNORECASE)]

    if not items_data:
        return ''

    items = '\n      '.join(
        f'''<div class="rl-logistics-item">
          <div class="rl-logistics-item-label">{esc(label)}</div>
          <div class="rl-logistics-item-value">{esc(val)}</div>
        </div>'''
        for label, val in items_data
    )

    # Official site link
    official = lg.get('official_site', '')
    site_html = ''
    if official and official.startswith('http'):
        site_html = f'''<div class="rl-mt-md">
        <a href="{esc(official)}" class="rl-btn rl-btn--secondary" target="_blank" rel="noopener">OFFICIAL SITE</a>
      </div>'''

    # Riders Report: race day tips after logistics grid
    tips_html = _build_riders_report([
        (rd.get('rider_intel', {}).get('race_day_tips', []), "text"),
    ])

    return f'''<section id="logistics" class="rl-section rl-section--accent rl-fade-section">
    <div class="rl-section-header">
      <span class="rl-section-kicker">[09]</span>
      <h2 class="rl-section-title">Race Logistics</h2>
    </div>
    <div class="rl-section-body">
      <div class="rl-logistics-grid">
      {items}
      </div>
      {tips_html}
      {site_html}
    </div>
  </section>'''


def build_tire_picks(rd: dict) -> str:
    """Build compact tire recommendation section — top 3 picks + link to full guide."""
    tr = rd.get('tire_recommendations', {})
    primary = tr.get('primary', [])
    if not primary:
        return ''

    slug = rd['slug']
    width_mm = tr.get('recommended_width_mm')
    surface = tr.get('race_surface_profile', '')

    width_badge = ''
    if width_mm:
        width_badge = (
            f'<span class="rl-tire-badge">{esc(str(width_mm))}mm</span>'
        )
    surface_badge = ''
    if surface:
        surface_badge = (
            f'<span class="rl-tire-badge">{esc(surface.upper())}</span>'
        )

    picks_html = []
    for t in primary[:3]:
        rank = t.get('rank', '')
        name = t.get('name', '')
        w = t.get('recommended_width_mm', '')
        price = t.get('msrp_usd')
        crr = t.get('crr_watts')
        why = t.get('why', '')

        price_str = f'${price:.0f}' if price else ''
        crr_str = f'{crr:.0f}W' if crr else ''

        meta_parts = []
        if w:
            meta_parts.append(f'{w}mm')
        if price_str:
            meta_parts.append(price_str)
        if crr_str:
            meta_parts.append(crr_str)
        meta = ' · '.join(meta_parts)

        why_html = f'<div class="rl-tire-why">{esc(why)}</div>' if why else ''
        picks_html.append(
            f'<div class="rl-tire-pick">'
            f'<div class="rl-tire-rank">{esc(str(rank))}</div>'
            f'<div class="rl-tire-info">'
            f'<div class="rl-tire-name">{esc(name)}</div>'
            f'<div class="rl-tire-meta">{esc(meta)}</div>'
            f'{why_html}'
            f'</div>'
            f'</div>'
        )

    # Front/rear split callout
    split = tr.get('front_rear_split', {})
    split_html = ''
    if split.get('applicable') and split.get('front') and split.get('rear'):
        front = split['front']
        rear = split['rear']
        rationale = split.get('rationale', '')
        rationale_html = f'<span class="rl-tire-split-why">{esc(rationale)}</span>' if rationale else ''
        split_html = (
            f'<div class="rl-tire-split">'
            f'<span class="rl-tire-split-label">FRONT/REAR SPLIT</span> '
            f'<span class="rl-tire-split-combo">'
            f'{esc(front.get("name", ""))} {esc(str(front.get("width_mm", "")))}mm'
            f' / '
            f'{esc(rear.get("name", ""))} {esc(str(rear.get("width_mm", "")))}mm'
            f'</span>'
            f'{rationale_html}'
            f'</div>'
        )

    return f'''<section id="tires" class="rl-section rl-fade-section">
    <div class="rl-section-header">
      <span class="rl-section-kicker">[10]</span>
      <h2 class="rl-section-title">Tire Picks</h2>
    </div>
    <div class="rl-section-body">
      <div class="rl-tire-badges">{width_badge}{surface_badge}</div>
      <div class="rl-tire-list">
        {"".join(picks_html)}
      </div>
      {split_html}
      <div class="rl-mt-md">
        <a href="/race/{esc(slug)}/tires/" class="rl-btn rl-btn--outline">FULL TIRE GUIDE &amp; PRESSURE TABLE</a>
      </div>
    </div>
  </section>'''


def build_news_section(rd: dict) -> str:
    """Build Latest News section — fetches Google News RSS via rss2json.com at runtime.
    Only renders for T1/T2 races (T3/T4 rarely have news, wastes API calls).
    Starts hidden to prevent layout shift — JS reveals it if headlines load."""
    tier = rd.get('tier', 4)
    if tier > 2:
        return ''
    name = rd['name']
    search_query = name.replace(' ', '+')

    return f'''<div class="rl-news-ticker rl-fade-section" id="rl-news-ticker" role="region" aria-label="Latest news" data-query="{esc(search_query)}" style="display:none">
    <div class="rl-news-ticker-label" aria-hidden="true">LATEST NEWS</div>
    <div class="rl-news-ticker-track">
      <div class="rl-news-ticker-content" id="rl-news-feed" aria-live="polite" aria-atomic="true"></div>
    </div>
  </div>'''


def build_pullquote(rd: dict) -> str:
    """Build a pull-quote block from the biased opinion summary.
    Uses summary (not bottom_line) to avoid duplicating the verdict section."""
    bo = rd['biased_opinion']
    fv = rd['final_verdict']
    # Use summary first; only use bottom_line if summary is empty AND bottom_line
    # differs from what the verdict section will show
    text = bo.get('summary', '').strip()
    if not text:
        bl = bo.get('bottom_line', '').strip()
        should_race = fv.get('should_you_race', '').strip()
        # Only use bottom_line for pullquote if it won't be shown in verdict
        if bl and bl != should_race:
            text = bl
    if not text:
        return ''

    return f'''<div class="rl-pullquote rl-fade-section">
    <blockquote class="rl-pullquote-text">&ldquo;{esc(text)}&rdquo;</blockquote>
  </div>'''


def _build_race_name_map(race_index: list) -> dict:
    """Build name → slug mapping from the full race index for linkification."""
    name_map = {}
    for r in race_index:
        slug = r.get('slug', '')
        name = r.get('name', '')
        if name and slug:
            name_map[name] = slug
    return name_map


def linkify_alternatives(alt_text: str, race_index: list) -> str:
    """Parse race names from alternatives text and link to profile pages.
    Builds name→slug mapping from the full race index."""
    if not alt_text:
        return ''

    # Build mapping from index; include common aliases as fallback
    name_map = _build_race_name_map(race_index) if race_index else {}
    # Add well-known aliases that differ from display names
    aliases = {
        'Unbound': 'unbound-200',
        'Unbound Gravel': 'unbound-200',
        'BWR': 'bwr-california',
        'Belgian Waffle Ride': 'bwr-california',
        'Big Sugar': 'big-sugar',
        'Land Run': 'mid-south',
        'Leadville': 'leadville-trail-100-mtb',
    }
    for alias, slug in aliases.items():
        if alias not in name_map:
            name_map[alias] = slug

    result = esc(alt_text)
    # Sort by length descending to match longer names first
    for name, slug in sorted(name_map.items(), key=lambda x: len(x[0]), reverse=True):
        escaped_name = esc(name)
        if escaped_name in result:
            link = f'<a href="/race/{slug}/" class="rl-alt-link">{escaped_name}</a>'
            result = result.replace(escaped_name, link, 1)

    return result


def build_email_capture(rd: dict) -> str:
    """Build email capture section — prep kit CTA + Substack subscribe."""
    slug = esc(rd["slug"])
    name = esc(rd["name"])
    return f'''<div class="rl-email-capture rl-fade-section">
    <div class="rl-email-capture-inner">
      <div class="rl-email-capture-badge">FREE DOWNLOAD</div>
      <h3 class="rl-email-capture-title">GET THE {name.upper()} PREP KIT</h3>
      <p class="rl-email-capture-text">12-week training timeline, race-day checklists, packing list, and personalized fueling calculator — delivered instantly.</p>
      <form class="rl-email-capture-form" id="rl-email-capture-form" autocomplete="off">
        <input type="hidden" name="race_slug" value="{slug}">
        <input type="hidden" name="race_name" value="{name}">
        <input type="hidden" name="source" value="race_profile">
        <input type="hidden" name="website" value="">
        <div class="rl-email-capture-row">
          <input type="email" name="email" required placeholder="your@email.com" class="rl-email-capture-input" aria-label="Email address">
          <button type="submit" class="rl-email-capture-btn">GET PREP KIT</button>
        </div>
      </form>
      <div class="rl-email-capture-success" id="rl-email-capture-success" style="display:none">
        <p class="rl-email-capture-check">\u2713 Prep kit unlocked!</p>
        <a href="/race/{slug}/prep-kit/" class="rl-email-capture-link">Open Your {name} Prep Kit \u2192</a>
      </div>
      <p class="rl-email-capture-fine">No spam. Unsubscribe anytime.</p>
    </div>
  </div>'''


def build_visible_faq(rd: dict) -> str:
    """Build visible FAQ section for long-tail SEO. Uses same data as FAQ schema
    but renders as on-page content with H3 headings for search engines."""
    explanations = rd.get('explanations', {})
    name = rd['name']
    fv = rd['final_verdict']

    questions = []
    # Top FAQ dimensions
    for dim in FAQ_PRIORITY:
        if len(questions) >= 4:
            break
        entry = explanations.get(dim, {})
        expl = entry.get('explanation', '').strip()
        if not expl:
            continue
        q_template = FAQ_TEMPLATES.get(dim, f'What about {dim} at {{name}}?')
        questions.append((q_template.format(name=name), expl))

    # Verdict question
    should_race = fv.get('should_you_race', '').strip()
    if should_race:
        questions.append((f"Should I race {name}?", should_race))

    if not questions:
        return ''

    items = []
    for q, a in questions:
        items.append(f'''<div class="rl-faq-item">
        <div class="rl-faq-question" role="button" tabindex="0" aria-expanded="false">
          <h3>{esc(q)}</h3>
          <span class="rl-faq-toggle" aria-hidden="true">+</span>
        </div>
        <div class="rl-faq-answer"><p>{esc(a)}</p></div>
      </div>''')

    return f'''<section id="faq" class="rl-section rl-fade-section">
    <div class="rl-section-header">
      <span class="rl-section-kicker">[&mdash;]</span>
      <h2 class="rl-section-title">Frequently Asked Questions</h2>
    </div>
    <div class="rl-section-body">
      {''.join(items)}
    </div>
  </section>'''


def build_similar_races(rd: dict, race_index: list) -> str:
    """Build Similar Races section from the race index.
    Finds 4 races in same region or adjacent tier, excluding self."""
    if not race_index:
        return ''

    slug = rd['slug']
    tier = rd.get('tier', 4)
    score = rd.get('overall_score', 0)
    # Derive region from location
    location = rd['vitals'].get('location', '')

    # Find region by matching this slug in the index
    my_region = ''
    for r in race_index:
        if r.get('slug') == slug:
            my_region = r.get('region', '')
            break

    my_distance = rd['vitals'].get('distance_mi') or 0
    if isinstance(my_distance, str):
        try:
            my_distance = float(re.sub(r'[^\d.]', '', str(my_distance)))
        except (ValueError, TypeError):
            my_distance = 0

    candidates = []
    for r in race_index:
        if r.get('slug') == slug:
            continue
        r_region = r.get('region', '')
        r_tier = r.get('tier', 4)
        r_score = r.get('overall_score', 0)
        r_dist = r.get('distance_mi', 0) or 0
        # Score: same region = 10, same tier = 5, adjacent tier = 2, score + distance proximity
        relevance = 0
        if my_region and r_region == my_region:
            relevance += 10
        if r_tier == tier:
            relevance += 5
        elif abs(r_tier - tier) == 1:
            relevance += 2
        relevance += max(0, 10 - abs(r_score - score) / 5)
        # Distance similarity bonus (up to 5 points)
        if my_distance > 0 and r_dist > 0:
            dist_ratio = min(my_distance, r_dist) / max(my_distance, r_dist)
            relevance += dist_ratio * 5
        candidates.append((relevance, r))

    # Sort by relevance descending, take top 6
    candidates.sort(key=lambda x: x[0], reverse=True)
    top = [c[1] for c in candidates[:6]]

    if not top:
        return ''

    cards = []
    for r in top:
        tier_num = r.get('tier', 4)
        dist = r.get('distance_mi', '')
        dist_str = f" &middot; {dist} mi" if dist else ''
        cards.append(f'''<a href="/race/{esc(r['slug'])}/" class="rl-similar-card">
        <span class="rl-similar-tier">T{tier_num}</span>
        <span class="rl-similar-name">{esc(r['name'])}</span>
        <span class="rl-similar-meta">{esc(r.get('location', ''))}{dist_str} &middot; {r.get('overall_score', 0)}/100</span>
      </a>''')

    return f'''<section class="rl-section rl-fade-section">
    <div class="rl-section-header rl-section-header--dark">
      <span class="rl-section-kicker">[&mdash;]</span>
      <h2 class="rl-section-title">Similar Races</h2>
    </div>
    <div class="rl-section-body">
      <div class="rl-similar-grid">
        {''.join(cards)}
      </div>
    </div>
  </section>'''


def build_citations_section(rd: dict) -> str:
    """Build Sources & Citations section from race.citations data."""
    citations = rd.get('citations', [])
    if not citations:
        return ''

    # Group by category
    categories = {}
    for c in citations:
        cat = c.get('category', 'other')
        categories.setdefault(cat, []).append(c)

    # Category display order and labels
    cat_order = [
        ('official', 'Official'),
        ('route', 'Route Maps'),
        ('media', 'Media & Press'),
        ('community', 'Community'),
        ('video', 'Video'),
        ('registration', 'Registration'),
        ('social', 'Social'),
        ('tracking', 'Live Tracking'),
        ('reference', 'Reference'),
        ('activity', 'Activity'),
        ('other', 'Other Sources'),
    ]

    items = []
    for cat_key, cat_label in cat_order:
        if cat_key not in categories:
            continue
        for c in categories[cat_key]:
            url = c.get('url', '')
            label = c.get('label', 'Source')
            # Truncate long URLs for display
            display_url = url.replace('https://', '').replace('http://', '')
            if len(display_url) > 60:
                display_url = display_url[:57] + '...'
            items.append(
                f'<li class="rl-citation-item">'
                f'<span class="rl-citation-cat">{esc(cat_label)}</span> '
                f'<a href="{esc(url)}" target="_blank" rel="noopener noreferrer" '
                f'class="rl-citation-link">{esc(label)}</a>'
                f'<span class="rl-citation-url">{esc(display_url)}</span>'
                f'</li>'
            )

    if not items:
        return ''

    return f'''<section class="rl-section rl-fade-section" id="citations">
    <div class="rl-section-header rl-section-header--dark">
      <span class="rl-section-kicker">[11]</span>
      <h2 class="rl-section-title">Sources &amp; Citations</h2>
    </div>
    <div class="rl-section-body">
      <p class="rl-citations-intro">Research sources used to build this race profile. Always verify details with official race sources before making travel or registration decisions.</p>
      <ol class="rl-citations-list">
        {''.join(items)}
      </ol>
    </div>
  </section>'''


def build_breadcrumb_jsonld(rd: dict, race_index: list) -> dict:
    """Build BreadcrumbList JSON-LD schema."""
    return {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Home",
             "item": SITE_BASE_URL},
            {"@type": "ListItem", "position": 2, "name": "Gravel Races",
             "item": f"{SITE_BASE_URL}/gravel-races/"},
            {"@type": "ListItem", "position": 3, "name": rd['tier_label'],
             "item": f"{SITE_BASE_URL}/race/tier-{rd['tier']}/"},
            {"@type": "ListItem", "position": 4, "name": rd['name'],
             "item": f"{SITE_BASE_URL}/race/{rd['slug']}/"},
        ]
    }


def build_webpage_jsonld(rd: dict) -> dict:
    """Build WebPage JSON-LD with speakable targeting key content sections."""
    canonical_url = f"{SITE_BASE_URL}/race/{rd['slug']}/"
    return {
        "@context": "https://schema.org",
        "@type": "WebPage",
        "name": build_seo_title(rd),
        "url": canonical_url,
        "dateModified": rd.get('_file_mtime', date.today().isoformat()),
        "isPartOf": {
            "@type": "WebSite",
            "name": "Road Labs",
            "url": SITE_BASE_URL,
        },
        "speakable": {
            "@type": "SpeakableSpecification",
            "cssSelector": [
                ".rl-overview-tagline",
                ".rl-verdict-text",
                ".rl-faq-answer",
            ],
        },
    }


def _build_breadcrumb_series_segment(rd: dict) -> str:
    """Build the series breadcrumb segment if the race belongs to a series."""
    series = rd.get('series', {})
    if series.get('id') and series.get('name'):
        return (
            f'<a href="{SITE_BASE_URL}/race/series/{esc(series["id"])}/">'
            f'{esc(series["name"])} Series</a>\n'
            f'    <span class="rl-breadcrumb-sep">&rsaquo;</span>\n    '
        )
    # Fallback: tier link
    return (
        f'<a href="{SITE_BASE_URL}/race/tier-{rd["tier"]}/">{esc(rd["tier_label"])}</a>\n'
        f'    <span class="rl-breadcrumb-sep">&rsaquo;</span>\n    '
    )


def build_nav_header(rd: dict, race_index: list) -> str:
    """Build visible navigation header with breadcrumb trail."""
    return get_site_header_html(active="races") + f'''
  <div class="rl-breadcrumb">
    <a href="{SITE_BASE_URL}/">Home</a>
    <span class="rl-breadcrumb-sep">&rsaquo;</span>
    <a href="{SITE_BASE_URL}/gravel-races/">Gravel Races</a>
    <span class="rl-breadcrumb-sep">&rsaquo;</span>
    {_build_breadcrumb_series_segment(rd)}
    <span class="rl-breadcrumb-current">{esc(rd['name'])}</span>
  </div>'''


def build_footer(rd: dict = None) -> str:
    """Build page footer with last-updated line and shared mega-footer."""
    updated = ''
    if rd and rd.get('_file_mtime'):
        try:
            dt = datetime.strptime(rd['_file_mtime'], '%Y-%m-%d')
            updated = f'<p class="rl-footer-updated">Last updated {dt.strftime("%B %Y")}</p>'
        except ValueError:
            pass
    return updated + get_mega_footer_html()


# ── CSS ────────────────────────────────────────────────────────

def get_page_css() -> str:
    """Return the full page CSS with brand tokens, self-hosted fonts, and editorial typography."""
    tokens = get_tokens_css()
    fonts = get_font_face_css("/race/assets/fonts")
    return f'''<style>
{fonts}

{tokens}

/* Skip link */
.rl-skip-link {{ position: absolute; top: -100px; left: 16px; background: var(--rl-color-gold); color: var(--rl-color-dark-brown); padding: 8px 16px; font-family: var(--rl-font-data); font-size: 12px; font-weight: 700; text-decoration: none; z-index: 999; border: var(--rl-border-standard); }}
.rl-skip-link:focus {{ top: 8px; outline: 3px solid var(--rl-color-near-black); outline-offset: 2px; }}

/* Focus indicators */
.rl-neo-brutalist-page a:focus-visible, .rl-neo-brutalist-page button:focus-visible, .rl-neo-brutalist-page [role="button"]:focus-visible, .rl-neo-brutalist-page .rl-btn:focus-visible {{ outline: 3px solid var(--rl-color-gold); outline-offset: 2px; }}
.rl-neo-brutalist-page .rl-faq-question:focus-visible {{ outline: 3px solid var(--rl-color-gold); outline-offset: -3px; }}

/* Utility */
.rl-mt-md {{ margin-top: var(--rl-spacing-md); }}

/* Page wrapper */
.rl-neo-brutalist-page {{
  max-width: 960px;
  margin: 0 auto;
  padding: 0 20px;
  font-family: var(--rl-font-data);
  color: var(--rl-color-dark-brown);
  line-height: 1.6;
  background: var(--rl-color-warm-paper);
}}
.rl-neo-brutalist-page *, .rl-neo-brutalist-page *::before, .rl-neo-brutalist-page *::after {{
  border-radius: 0 !important;
  box-shadow: none !important;
  box-sizing: border-box;
}}

/* Hero — clean editorial masthead: name left, score right */
.rl-neo-brutalist-page .rl-hero {{ background: var(--rl-color-warm-paper); color: var(--rl-color-dark-brown); padding: 48px 32px; border-bottom: 2px solid var(--rl-color-gold); margin-bottom: 0; display: flex; align-items: flex-end; justify-content: space-between; gap: 32px; }}
.rl-neo-brutalist-page .rl-hero-content {{ flex: 1; min-width: 0; }}
.rl-neo-brutalist-page .rl-hero-tier {{ display: inline-block; font-family: var(--rl-font-data); font-size: var(--rl-font-size-2xs); font-weight: var(--rl-font-weight-bold); letter-spacing: var(--rl-letter-spacing-ultra-wide); text-transform: uppercase; color: var(--rl-color-secondary-brown); margin-bottom: var(--rl-spacing-sm); }}
.rl-neo-brutalist-page .rl-series-badge {{ display: inline-block; margin-left: 12px; color: var(--rl-color-teal); font-family: var(--rl-font-data); font-size: 9px; font-weight: var(--rl-font-weight-bold); letter-spacing: var(--rl-letter-spacing-wider); text-transform: uppercase; text-decoration: none; border-bottom: 1px solid var(--rl-color-teal); padding-bottom: 1px; }}
.rl-neo-brutalist-page .rl-series-badge:hover {{ color: var(--rl-color-dark-teal); }}
.rl-neo-brutalist-page .rl-hero h1 {{ font-family: var(--rl-font-editorial); font-size: 42px; font-weight: var(--rl-font-weight-bold); line-height: 1.05; letter-spacing: var(--rl-letter-spacing-tight); margin: 0; color: var(--rl-color-dark-brown); }}
.rl-neo-brutalist-page .rl-hero-vitals {{ font-family: var(--rl-font-data); font-size: 11px; color: var(--rl-color-secondary-brown); letter-spacing: 1px; text-transform: uppercase; margin-top: 14px; }}
.rl-neo-brutalist-page .rl-hero-score {{ text-align: center; flex-shrink: 0; }}
.rl-neo-brutalist-page .rl-hero-score-number {{ font-family: var(--rl-font-editorial); font-size: 72px; font-weight: var(--rl-font-weight-bold); line-height: 1; color: var(--rl-color-gold); }}
.rl-neo-brutalist-page .rl-hero-score-label {{ font-family: var(--rl-font-data); font-size: 10px; font-weight: var(--rl-font-weight-bold); letter-spacing: 3px; text-transform: uppercase; color: var(--rl-color-secondary-brown); margin-top: 4px; }}

/* TOC — light version */
.rl-neo-brutalist-page .rl-toc {{ background: var(--rl-color-warm-paper); padding: 16px 20px; border-bottom: 1px solid var(--rl-color-gold); display: flex; flex-wrap: wrap; gap: 8px 20px; margin-bottom: 32px; }}
.rl-neo-brutalist-page .rl-toc a {{ color: var(--rl-color-secondary-brown); text-decoration: none; font-family: var(--rl-font-data); font-size: 11px; font-weight: 700; letter-spacing: var(--rl-letter-spacing-wider); text-transform: uppercase; transition: color 0.2s; }}
.rl-neo-brutalist-page .rl-toc a:hover {{ color: var(--rl-color-gold); }}

/* Section common — Variant F: warm paper bg, gold hairlines */
.rl-neo-brutalist-page .rl-section {{ margin-bottom: 32px; border: 1px solid var(--rl-color-tan); background: var(--rl-color-warm-paper); }}
.rl-neo-brutalist-page .rl-section-header {{ background: var(--rl-color-warm-paper); color: var(--rl-color-dark-brown); padding: 14px 20px; display: flex; align-items: center; gap: 12px; border-bottom: 1px solid var(--rl-color-gold); }}
.rl-neo-brutalist-page .rl-section-kicker {{ font-family: var(--rl-font-data); font-size: var(--rl-font-size-2xs); font-weight: 700; letter-spacing: var(--rl-letter-spacing-ultra-wide); text-transform: uppercase; color: var(--rl-color-gold); white-space: nowrap; }}
.rl-neo-brutalist-page .rl-section-title {{ font-family: var(--rl-font-editorial); font-size: var(--rl-font-size-md); font-weight: var(--rl-font-weight-semibold); letter-spacing: var(--rl-letter-spacing-normal); color: var(--rl-color-dark-brown); margin: 0; }}
.rl-neo-brutalist-page .rl-section-body {{ padding: 24px 20px; }}

/* Section header variant: dark — now uses primary-brown text on warm paper */
.rl-neo-brutalist-page .rl-section-header--dark {{ background: var(--rl-color-warm-paper); }}
.rl-neo-brutalist-page .rl-section-header--dark .rl-section-kicker {{ color: var(--rl-color-gold); }}

/* Section variant: accent (subtle warm bg) */
.rl-neo-brutalist-page .rl-section--accent {{ background: var(--rl-color-warm-paper); }}

/* Section variant: dark — now warm-paper with brown text (no dark backgrounds) */
.rl-neo-brutalist-page .rl-section--dark {{ background: var(--rl-color-warm-paper); }}
.rl-neo-brutalist-page .rl-section--dark .rl-section-body {{ color: var(--rl-color-primary-brown); }}
.rl-neo-brutalist-page .rl-section--dark .rl-prose {{ color: var(--rl-color-primary-brown); }}
.rl-neo-brutalist-page .rl-section--dark .rl-prose p {{ color: var(--rl-color-primary-brown); }}
.rl-neo-brutalist-page .rl-section--dark .rl-prose strong {{ color: var(--rl-color-dark-brown); }}
.rl-neo-brutalist-page .rl-section--dark .rl-timeline {{ border-left-color: var(--rl-color-gold); }}
.rl-neo-brutalist-page .rl-section--dark .rl-timeline-text {{ color: var(--rl-color-primary-brown); }}
.rl-neo-brutalist-page .rl-section--dark .rl-verdict-grid {{ gap: 16px; }}
.rl-neo-brutalist-page .rl-section--dark .rl-verdict-box--race {{ background: var(--rl-color-warm-paper); border-color: var(--rl-color-tan); }}
.rl-neo-brutalist-page .rl-section--dark .rl-verdict-box--skip {{ background: var(--rl-color-warm-paper); border-color: var(--rl-color-tan); }}
.rl-neo-brutalist-page .rl-section--dark .rl-verdict-box-title {{ color: var(--rl-color-dark-brown); }}
.rl-neo-brutalist-page .rl-section--dark .rl-verdict-list li {{ color: var(--rl-color-primary-brown); }}
.rl-neo-brutalist-page .rl-section--dark .rl-verdict-bottom-line {{ background: var(--rl-color-warm-paper); border-color: var(--rl-color-gold); color: var(--rl-color-primary-brown); }}
.rl-neo-brutalist-page .rl-section--dark .rl-verdict-bottom-line strong {{ color: var(--rl-color-gold); }}

/* Section variant: teal accent (teal top border) */
.rl-neo-brutalist-page .rl-section--teal-accent {{ border-top: 2px solid var(--rl-color-teal); }}

/* Section header variant: teal — now warm-paper with teal text */
.rl-neo-brutalist-page .rl-section-header--teal {{ background: var(--rl-color-warm-paper); border-bottom-color: var(--rl-color-teal); }}
.rl-neo-brutalist-page .rl-section-header--teal .rl-section-title {{ color: var(--rl-color-teal); }}
.rl-neo-brutalist-page .rl-section-header--teal .rl-section-kicker {{ color: var(--rl-color-teal); opacity: 0.6; }}

/* Section header variant: gold — now warm-paper with gold text */
.rl-neo-brutalist-page .rl-section-header--gold {{ background: var(--rl-color-warm-paper); border-bottom-color: var(--rl-color-gold); }}
.rl-neo-brutalist-page .rl-section-header--gold .rl-section-title {{ color: var(--rl-color-gold); }}
.rl-neo-brutalist-page .rl-section-header--gold .rl-section-kicker {{ color: var(--rl-color-gold); opacity: 0.6; }}

/* Stat cards */
.rl-neo-brutalist-page .rl-stat-grid {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; }}
.rl-neo-brutalist-page .rl-stat-card {{ border: 1px solid var(--rl-color-tan); padding: var(--rl-spacing-md); text-align: center; background: var(--rl-color-warm-paper); transition: border-color var(--rl-transition-hover); }}
.rl-neo-brutalist-page .rl-stat-card:hover {{ border-color: var(--rl-color-gold); }}
.rl-neo-brutalist-page .rl-stat-value {{ font-family: var(--rl-font-editorial); font-size: var(--rl-font-size-xl); font-weight: var(--rl-font-weight-bold); color: var(--rl-color-dark-brown); line-height: var(--rl-line-height-tight); }}
.rl-neo-brutalist-page .rl-stat-label {{ font-family: var(--rl-font-data); font-size: var(--rl-font-size-2xs); font-weight: var(--rl-font-weight-bold); letter-spacing: var(--rl-letter-spacing-wider); text-transform: uppercase; color: var(--rl-color-gold); margin-top: var(--rl-spacing-2xs); }}

/* Calendar export */
.rl-neo-brutalist-page .rl-calendar-export {{ display: flex; gap: 8px; margin-top: 12px; flex-wrap: wrap; }}
.rl-neo-brutalist-page .rl-cal-btn {{ font-family: var(--rl-font-data); font-size: 11px; font-weight: 700; letter-spacing: var(--rl-letter-spacing-wider); text-transform: uppercase; padding: 6px 14px; border: 2px solid var(--rl-color-dark-brown); text-decoration: none; transition: background var(--rl-transition-hover), color var(--rl-transition-hover); cursor: pointer; }}
.rl-neo-brutalist-page .rl-cal-btn--google {{ background: var(--rl-color-warm-paper); color: var(--rl-color-dark-brown); }}
.rl-neo-brutalist-page .rl-cal-btn--google:hover {{ background: var(--rl-color-teal); color: var(--rl-color-white); }}
.rl-neo-brutalist-page .rl-cal-btn--ics {{ background: var(--rl-color-warm-paper); color: var(--rl-color-dark-brown); }}
.rl-neo-brutalist-page .rl-cal-btn--ics:hover {{ background: var(--rl-color-gold); color: var(--rl-color-dark-brown); }}

/* Difficulty gauge */
.rl-neo-brutalist-page .rl-difficulty-gauge {{ margin-top: 20px; border: var(--rl-border-standard); padding: 16px; background: var(--rl-color-warm-paper); }}
.rl-neo-brutalist-page .rl-difficulty-header {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; }}
.rl-neo-brutalist-page .rl-difficulty-title {{ font-family: var(--rl-font-data); font-size: var(--rl-font-size-2xs); font-weight: 700; letter-spacing: var(--rl-letter-spacing-wider); color: var(--rl-color-secondary-brown); }}
.rl-neo-brutalist-page .rl-difficulty-label {{ font-family: var(--rl-font-data); font-size: 12px; font-weight: 700; letter-spacing: var(--rl-letter-spacing-wider); color: var(--rl-color-dark-brown); }}
.rl-neo-brutalist-page .rl-difficulty-track {{ height: 12px; background: var(--rl-color-sand); border: 1px solid var(--rl-color-dark-brown); position: relative; overflow: hidden; }}
.rl-neo-brutalist-page .rl-difficulty-fill {{ height: 100%; transition: width 1.5s cubic-bezier(0.22,1,0.36,1); }}
.rl-neo-brutalist-page .rl-difficulty-scale {{ display: flex; justify-content: space-between; margin-top: 6px; font-family: var(--rl-font-data); font-size: 8px; font-weight: 700; letter-spacing: 1px; color: var(--rl-color-warm-brown); text-transform: uppercase; }}

/* Nearby races — in-content cross-links */
.rl-neo-brutalist-page .rl-nearby-races {{ margin-top: 16px; padding: 10px 16px; background: var(--rl-color-sand); border: 1px solid var(--rl-color-tan); font-family: var(--rl-font-data); font-size: 11px; }}
.rl-neo-brutalist-page .rl-nearby-label {{ font-weight: 700; letter-spacing: var(--rl-letter-spacing-wider); color: var(--rl-color-gold); }}
.rl-neo-brutalist-page .rl-nearby-races a {{ color: var(--rl-color-primary-brown); text-decoration: none; }}
.rl-neo-brutalist-page .rl-nearby-races a:hover {{ color: var(--rl-color-gold); text-decoration: underline; }}

/* Overview tagline — editorial lead */
.rl-neo-brutalist-page .rl-overview-tagline {{ font-family: var(--rl-font-editorial); font-size: var(--rl-font-size-md); font-style: italic; line-height: var(--rl-line-height-prose); color: var(--rl-color-primary-brown); margin: 0 0 20px 0; }}

/* Map embed */
.rl-neo-brutalist-page .rl-map-embed {{ border: var(--rl-border-subtle); margin-bottom: 16px; overflow: hidden; }}
.rl-neo-brutalist-page .rl-map-embed iframe {{ width: 100%; height: 500px; border: none; display: block; }}

/* Prose — editorial font */
.rl-neo-brutalist-page .rl-prose {{ font-family: var(--rl-font-editorial); font-size: var(--rl-font-size-base); line-height: var(--rl-line-height-prose); color: var(--rl-color-dark-brown); }}
.rl-neo-brutalist-page .rl-prose p {{ margin-bottom: 14px; }}
.rl-neo-brutalist-page .rl-prose p:last-child {{ margin-bottom: 0; }}

/* Timeline */
.rl-neo-brutalist-page .rl-timeline {{ border-left: var(--rl-border-standard); border-left-color: var(--rl-color-gold); margin: 16px 0 0 12px; padding-left: 20px; }}
.rl-neo-brutalist-page .rl-timeline-item {{ position: relative; margin-bottom: 16px; padding-bottom: 4px; opacity: 0; transform: translateY(10px); transition: opacity 0.4s, transform 0.4s; }}
.rl-neo-brutalist-page .rl-timeline-item.is-visible {{ opacity: 1; transform: translateY(0); }}
.rl-neo-brutalist-page .rl-timeline-item::before {{ content: ''; position: absolute; left: -27px; top: 6px; width: 10px; height: 10px; background: var(--rl-color-gold); border: 2px solid var(--rl-color-dark-brown); }}
.rl-neo-brutalist-page .rl-timeline-text {{ font-family: var(--rl-font-editorial); font-size: var(--rl-font-size-xs); color: var(--rl-color-dark-brown); line-height: 1.5; }}

/* Surface breakdown chart */
.rl-neo-brutalist-page .rl-surface-breakdown {{ border: var(--rl-border-standard); padding: var(--rl-spacing-md); background: var(--rl-color-warm-paper); margin-bottom: 20px; }}
.rl-neo-brutalist-page .rl-surface-header {{ font-family: var(--rl-font-data); font-size: 10px; font-weight: 700; letter-spacing: var(--rl-letter-spacing-wider); text-transform: uppercase; color: var(--rl-color-warm-brown); margin-bottom: 12px; }}
.rl-neo-brutalist-page .rl-surface-row {{ margin-bottom: 10px; }}
.rl-neo-brutalist-page .rl-surface-row:last-child {{ margin-bottom: 0; }}
.rl-neo-brutalist-page .rl-surface-dist {{ font-family: var(--rl-font-data); font-size: var(--rl-font-size-xs); font-weight: 700; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 4px; color: var(--rl-color-dark-brown); }}
.rl-neo-brutalist-page .rl-surface-bar {{ display: flex; height: 24px; border: 1px solid var(--rl-color-dark-brown); overflow: hidden; }}
.rl-neo-brutalist-page .rl-surface-seg {{ display: flex; align-items: center; justify-content: center; font-family: var(--rl-font-data); font-size: 9px; font-weight: 700; color: var(--rl-color-white); text-transform: uppercase; letter-spacing: 0.5px; white-space: nowrap; overflow: hidden; }}
.rl-neo-brutalist-page .rl-surface-legend {{ display: flex; flex-wrap: wrap; gap: 8px; margin-top: 4px; }}
.rl-neo-brutalist-page .rl-surface-legend-item {{ font-family: var(--rl-font-data); font-size: 10px; color: var(--rl-color-dark-brown); display: flex; align-items: center; gap: 4px; text-transform: capitalize; }}
.rl-neo-brutalist-page .rl-surface-legend-dot {{ width: 8px; height: 8px; border: 1px solid var(--rl-color-dark-brown); flex-shrink: 0; }}

/* Tire picks */
.rl-neo-brutalist-page .rl-tire-badges {{ display: flex; gap: 8px; margin-bottom: 16px; }}
.rl-neo-brutalist-page .rl-tire-badge {{ font-family: var(--rl-font-data); font-size: 10px; font-weight: 700; letter-spacing: var(--rl-letter-spacing-wider); text-transform: uppercase; color: var(--rl-color-teal); border: 2px solid var(--rl-color-teal); padding: 2px 10px; }}
.rl-neo-brutalist-page .rl-tire-list {{ display: flex; flex-direction: column; gap: 0; }}
.rl-neo-brutalist-page .rl-tire-pick {{ display: flex; gap: 12px; padding: 12px 0; border-bottom: 1px solid var(--rl-color-muted-tan); }}
.rl-neo-brutalist-page .rl-tire-pick:last-child {{ border-bottom: none; }}
.rl-neo-brutalist-page .rl-tire-rank {{ font-family: var(--rl-font-data); font-size: var(--rl-font-size-xl); font-weight: 700; color: var(--rl-color-gold); min-width: 28px; text-align: center; line-height: 1; padding-top: 2px; }}
.rl-neo-brutalist-page .rl-tire-info {{ flex: 1; }}
.rl-neo-brutalist-page .rl-tire-name {{ font-family: var(--rl-font-data); font-size: var(--rl-font-size-sm); font-weight: 700; text-transform: uppercase; letter-spacing: 1px; color: var(--rl-color-dark-brown); }}
.rl-neo-brutalist-page .rl-tire-meta {{ font-family: var(--rl-font-data); font-size: var(--rl-font-size-xs); color: var(--rl-color-secondary-brown); margin-top: 2px; }}
.rl-neo-brutalist-page .rl-tire-why {{ font-family: var(--rl-font-editorial); font-size: var(--rl-font-size-xs); color: var(--rl-color-primary-brown); margin-top: 4px; line-height: var(--rl-line-height-relaxed); }}
.rl-neo-brutalist-page .rl-tire-split {{ border: var(--rl-border-subtle); padding: 12px 16px; background: var(--rl-color-warm-paper); margin-top: 16px; }}
.rl-neo-brutalist-page .rl-tire-split-label {{ font-family: var(--rl-font-data); font-size: 10px; font-weight: 700; letter-spacing: var(--rl-letter-spacing-wider); text-transform: uppercase; color: var(--rl-color-teal); }}
.rl-neo-brutalist-page .rl-tire-split-combo {{ font-family: var(--rl-font-data); font-size: var(--rl-font-size-xs); color: var(--rl-color-dark-brown); font-weight: 700; }}
.rl-neo-brutalist-page .rl-tire-split-why {{ display: block; font-family: var(--rl-font-editorial); font-size: var(--rl-font-size-xs); color: var(--rl-color-secondary-brown); margin-top: 4px; line-height: var(--rl-line-height-relaxed); }}

/* Suffering zones */
.rl-neo-brutalist-page .rl-suffering-zone {{ border: var(--rl-border-subtle); margin-bottom: 12px; display: flex; background: var(--rl-color-warm-paper); opacity: 0; transform: translateX(-30px); transition: opacity 0.5s, transform 0.5s; }}
.rl-neo-brutalist-page .rl-suffering-zone.is-visible {{ opacity: 1; transform: translateX(0); }}
.rl-neo-brutalist-page .rl-suffering-mile {{ background: var(--rl-color-teal); color: var(--rl-color-white); min-width: 80px; display: flex; flex-direction: column; align-items: center; justify-content: center; padding: 12px; border-right: var(--rl-border-width-subtle) solid var(--rl-color-dark-brown); }}
.rl-neo-brutalist-page .rl-suffering-mile-num {{ font-family: var(--rl-font-data); font-size: var(--rl-font-size-xl); font-weight: 700; }}
.rl-neo-brutalist-page .rl-suffering-mile-label {{ font-family: var(--rl-font-data); font-size: 9px; letter-spacing: var(--rl-letter-spacing-wider); text-transform: uppercase; color: rgba(255,255,255,0.7); }}
.rl-neo-brutalist-page .rl-suffering-content {{ padding: 12px 16px; flex: 1; }}
.rl-neo-brutalist-page .rl-suffering-name {{ font-family: var(--rl-font-data); font-size: var(--rl-font-size-sm); font-weight: 700; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 4px; }}
.rl-neo-brutalist-page .rl-suffering-desc {{ font-family: var(--rl-font-editorial); font-size: 12px; color: var(--rl-color-secondary-brown); line-height: 1.5; }}

/* Course photos + preview GIF */
.rl-neo-brutalist-page .rl-photo-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 12px; margin-bottom: 24px; }}
.rl-neo-brutalist-page .rl-photo-item {{ margin: 0; border: 2px solid var(--rl-color-dark-brown); }}
.rl-neo-brutalist-page .rl-photo-item img {{ display: block; width: 100%; aspect-ratio: 3/2; object-fit: cover; }}
.rl-neo-brutalist-page .rl-photo-item .rl-photo-credit {{ display: block; font-family: var(--rl-font-data); font-size: 9px; letter-spacing: var(--rl-letter-spacing-wider); text-transform: uppercase; color: var(--rl-color-secondary-brown); padding: 4px 8px; background: var(--rl-color-warm-paper); }}
.rl-neo-brutalist-page .rl-gif-gallery {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 12px; margin: 24px 0; }}
.rl-neo-brutalist-page .rl-gif-gallery .rl-course-preview {{ margin: 0; }}
.rl-neo-brutalist-page .rl-course-preview {{ margin: 24px 0; border: 2px solid var(--rl-color-dark-brown); }}
.rl-neo-brutalist-page .rl-preview-gif {{ display: block; width: 100%; aspect-ratio: 16/9; object-fit: cover; }}
.rl-neo-brutalist-page .rl-course-preview .rl-photo-credit {{ display: block; font-family: var(--rl-font-data); font-size: 9px; letter-spacing: var(--rl-letter-spacing-wider); text-transform: uppercase; color: var(--rl-color-secondary-brown); padding: 4px 8px; background: var(--rl-color-warm-paper); }}

/* Accordion */
.rl-neo-brutalist-page .rl-accordion {{ border-top: var(--rl-border-standard); }}
.rl-neo-brutalist-page .rl-accordion-group-title {{ font-family: var(--rl-font-data); font-size: 12px; font-weight: 700; text-transform: uppercase; letter-spacing: var(--rl-letter-spacing-wider); color: var(--rl-color-secondary-brown); padding: var(--rl-spacing-md) 0 var(--rl-spacing-xs) 0; }}
.rl-neo-brutalist-page .rl-accordion-item {{ border-bottom: 2px solid var(--rl-color-dark-brown); }}
.rl-neo-brutalist-page .rl-accordion-trigger {{ display: flex; align-items: center; width: 100%; padding: 10px 0; cursor: pointer; background: none; border: none; font-family: var(--rl-font-data); font-size: 12px; text-align: left; gap: 8px; }}
.rl-neo-brutalist-page .rl-accordion-trigger:hover {{ background: var(--rl-color-warm-paper); }}
.rl-neo-brutalist-page .rl-accordion-label {{ font-family: var(--rl-font-data); width: 110px; min-width: 110px; font-weight: 700; text-transform: uppercase; letter-spacing: 1px; font-size: 11px; color: var(--rl-color-dark-brown); }}
.rl-neo-brutalist-page .rl-accordion-bar-track {{ flex: 1; height: 8px; background: var(--rl-color-sand); position: relative; border: 1px solid var(--rl-color-dark-brown); }}
.rl-neo-brutalist-page .rl-accordion-bar-fill {{ height: 100%; transition: width 0.3s; }}
.rl-neo-brutalist-page .rl-accordion-score {{ font-family: var(--rl-font-editorial); width: 40px; min-width: 40px; text-align: center; font-weight: var(--rl-font-weight-bold); font-size: var(--rl-font-size-sm); color: var(--rl-color-gold); }}
.rl-neo-brutalist-page .rl-accordion-arrow {{ width: 20px; min-width: 20px; text-align: center; font-size: var(--rl-font-size-2xs); color: var(--rl-color-warm-brown); transition: transform 0.2s; }}
.rl-neo-brutalist-page .rl-accordion-item.is-open .rl-accordion-arrow {{ transform: rotate(90deg); color: var(--rl-color-gold); }}
.rl-neo-brutalist-page .rl-accordion-panel {{ max-height: 0; overflow: hidden; transition: max-height 0.3s ease-out; }}
.rl-neo-brutalist-page .rl-accordion-item.is-open .rl-accordion-panel {{ max-height: 500px; }}
.rl-neo-brutalist-page .rl-accordion-content {{ font-family: var(--rl-font-editorial); padding: 0 0 14px 122px; font-size: var(--rl-font-size-sm); line-height: var(--rl-line-height-relaxed); color: var(--rl-color-primary-brown); }}

/* Radar charts */
.rl-neo-brutalist-page .rl-radar-pair {{ display: flex; gap: 16px; margin-bottom: 24px; }}
.rl-neo-brutalist-page .rl-radar-chart {{ flex: 1; border: var(--rl-border-subtle); background: var(--rl-color-warm-paper); padding: 12px 8px 12px; text-align: center; }}
.rl-neo-brutalist-page .rl-radar-svg {{ width: 100%; height: auto; display: block; margin: 0 auto; }}
.rl-neo-brutalist-page .rl-radar-label {{ font-family: var(--rl-font-data); font-size: var(--rl-font-size-2xs); font-weight: 700; text-transform: uppercase; letter-spacing: var(--rl-letter-spacing-wider); color: var(--rl-color-secondary-brown); margin-top: var(--rl-spacing-2xs); }}
.rl-neo-brutalist-page .rl-radar-chart.is-drawn .rl-radar-polygon {{ stroke-dashoffset: 0 !important; fill-opacity: 0.2; transition: stroke-dashoffset 1.2s ease-out, fill-opacity 0.8s ease-out 0.6s; }}
.rl-neo-brutalist-page .rl-radar-chart.is-drawn .rl-radar-dot {{ opacity: 1; transition: opacity 0.3s ease-out; }}
.rl-neo-brutalist-page .rl-radar-hit:hover ~ .rl-radar-ring {{ opacity: 0; }}
.rl-neo-brutalist-page .rl-radar-chart .rl-radar-ring {{ transition: opacity 0.2s; }}

/* Verdict box hover */
.rl-neo-brutalist-page .rl-verdict-box {{ transition: border-color var(--rl-transition-hover); }}
.rl-neo-brutalist-page .rl-verdict-box:hover {{ border-color: var(--rl-color-gold); }}

/* Accordion item hover highlight */
.rl-neo-brutalist-page .rl-accordion-item {{ transition: background 0.15s; }}
.rl-neo-brutalist-page .rl-accordion-item.is-highlighted {{ background: var(--rl-color-sand); }}

/* Ratings summary */
.rl-neo-brutalist-page .rl-ratings-summary {{ display: flex; gap: 16px; margin-bottom: 20px; }}
.rl-neo-brutalist-page .rl-ratings-summary-card {{ flex: 1; border: var(--rl-border-subtle); padding: 16px; text-align: center; background: var(--rl-color-warm-paper); }}
.rl-neo-brutalist-page .rl-ratings-summary-card:first-child {{ border-left: 4px solid var(--rl-color-gold); }}
.rl-neo-brutalist-page .rl-ratings-summary-card:last-child {{ border-left: 4px solid var(--rl-color-teal); }}
.rl-neo-brutalist-page .rl-ratings-summary-score {{ font-family: var(--rl-font-data); font-size: 32px; font-weight: 700; color: var(--rl-color-primary-brown); line-height: 1; }}
.rl-neo-brutalist-page .rl-ratings-summary-max {{ font-size: 14px; color: var(--rl-color-tier-3); }}
.rl-neo-brutalist-page .rl-ratings-summary-label {{ font-family: var(--rl-font-data); font-size: var(--rl-font-size-2xs); font-weight: 700; letter-spacing: var(--rl-letter-spacing-wider); text-transform: uppercase; color: var(--rl-color-secondary-brown); margin-top: var(--rl-spacing-2xs); }}

/* Verdict */
.rl-neo-brutalist-page .rl-verdict-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }}
.rl-neo-brutalist-page .rl-verdict-box {{ border: var(--rl-border-standard); padding: var(--rl-spacing-md); }}
.rl-neo-brutalist-page .rl-verdict-box-title {{ font-family: var(--rl-font-editorial); font-size: var(--rl-font-size-base); font-weight: var(--rl-font-weight-semibold); margin-bottom: var(--rl-spacing-sm); color: var(--rl-color-dark-brown); }}
.rl-neo-brutalist-page .rl-verdict-box--race {{ background: var(--rl-color-sand); border-left: 4px solid var(--rl-color-gold); }}
.rl-neo-brutalist-page .rl-verdict-box--race .rl-verdict-box-title {{ color: var(--rl-color-gold); }}
.rl-neo-brutalist-page .rl-verdict-box--skip {{ background: var(--rl-color-warm-paper); border-left: 4px solid var(--rl-color-warm-brown); }}
.rl-neo-brutalist-page .rl-verdict-list {{ list-style: none; padding: 0; }}
.rl-neo-brutalist-page .rl-verdict-list li {{ font-family: var(--rl-font-editorial); font-size: var(--rl-font-size-xs); line-height: var(--rl-line-height-relaxed); color: var(--rl-color-dark-brown); padding: 6px 0; padding-left: 24px; position: relative; }}
.rl-neo-brutalist-page .rl-verdict-list li::before {{ content: '\\2014'; position: absolute; left: 0; top: 6px; color: var(--rl-color-warm-brown); font-weight: var(--rl-font-weight-regular); }}
.rl-neo-brutalist-page .rl-verdict-box--race .rl-verdict-list li::before {{ color: var(--rl-color-gold); }}
.rl-neo-brutalist-page .rl-verdict-bottom-line {{ margin-top: var(--rl-spacing-md); padding: var(--rl-spacing-md); border: var(--rl-border-standard); border-top: var(--rl-border-double); background: var(--rl-color-warm-paper); font-family: var(--rl-font-editorial); font-size: var(--rl-font-size-xs); line-height: var(--rl-line-height-relaxed); color: var(--rl-color-dark-brown); }}
.rl-neo-brutalist-page .rl-verdict-bottom-line strong {{ color: var(--rl-color-gold); }}

/* Pull quote — Desert Editorial: centered, tan bg, double-rule, curly quotes */
.rl-neo-brutalist-page .rl-pullquote {{ margin: var(--rl-spacing-xl) 0; padding: var(--rl-spacing-2xl); background: var(--rl-color-tan); border-top: var(--rl-border-double); border-bottom: var(--rl-border-double); text-align: center; position: relative; }}
.rl-neo-brutalist-page .rl-pullquote-text {{ font-family: var(--rl-font-editorial); font-size: var(--rl-font-size-lg); font-weight: var(--rl-font-weight-regular); font-style: italic; line-height: var(--rl-line-height-relaxed); color: var(--rl-color-dark-brown); margin: 0 0 var(--rl-spacing-sm) 0; position: relative; }}
.rl-neo-brutalist-page .rl-pullquote-text::before {{ content: '\\201c'; font-family: var(--rl-font-editorial); font-size: var(--rl-font-size-4xl); font-style: normal; color: var(--rl-color-gold); position: absolute; top: -10px; left: -20px; line-height: 1; }}
.rl-neo-brutalist-page .rl-pullquote-text::after {{ content: '\\201d'; font-family: var(--rl-font-editorial); font-size: var(--rl-font-size-4xl); font-style: normal; color: var(--rl-color-gold); position: relative; top: 10px; margin-left: 4px; line-height: 1; }}
.rl-neo-brutalist-page .rl-pullquote-attr {{ font-family: var(--rl-font-data); font-size: 11px; color: var(--rl-color-secondary-brown); letter-spacing: var(--rl-letter-spacing-wide); text-transform: uppercase; font-style: normal; }}

/* Alternative links */
.rl-neo-brutalist-page .rl-alt-link {{ color: var(--rl-color-teal); text-decoration: underline; text-underline-offset: 2px; }}
.rl-neo-brutalist-page .rl-alt-link:hover {{ color: #14695F; }}

/* Buttons */
.rl-neo-brutalist-page .rl-btn {{ display: inline-block; padding: 10px 24px; font-family: var(--rl-font-data); font-size: var(--rl-font-size-xs); font-weight: 700; text-transform: uppercase; letter-spacing: var(--rl-letter-spacing-wider); text-decoration: none; cursor: pointer; border: var(--rl-border-standard); transition: background 0.15s, color 0.15s; }}
.rl-neo-brutalist-page .rl-btn--primary {{ background: var(--rl-color-gold); color: var(--rl-color-dark-brown); }}
.rl-neo-brutalist-page .rl-btn--primary:hover {{ background: var(--rl-color-light-gold); }}
.rl-neo-brutalist-page .rl-btn--secondary {{ background: var(--rl-color-teal); color: var(--rl-color-white); }}
.rl-neo-brutalist-page .rl-btn--secondary:hover {{ background: var(--rl-color-light-teal); }}

/* Training */
.rl-neo-brutalist-page .rl-training-primary {{ border: 1px solid var(--rl-color-tan); border-left: 4px solid var(--rl-color-gold); background: var(--rl-color-warm-paper); color: var(--rl-color-dark-brown); padding: 32px; margin-bottom: 16px; }}
.rl-neo-brutalist-page .rl-training-primary h3 {{ font-family: var(--rl-font-editorial); font-size: var(--rl-font-size-lg); font-weight: 700; text-transform: uppercase; letter-spacing: var(--rl-letter-spacing-wider); margin-bottom: 6px; color: var(--rl-color-dark-brown); }}
.rl-neo-brutalist-page .rl-training-primary .rl-training-subtitle {{ font-family: var(--rl-font-editorial); font-size: 12px; color: var(--rl-color-secondary-brown); margin-bottom: 20px; }}
.rl-neo-brutalist-page .rl-training-bullets {{ list-style: none; padding: 0; margin-bottom: 24px; }}
.rl-neo-brutalist-page .rl-training-bullets li {{ font-family: var(--rl-font-editorial); font-size: var(--rl-font-size-xs); line-height: var(--rl-line-height-relaxed); color: var(--rl-color-primary-brown); padding: 6px 0; padding-left: 20px; position: relative; }}
.rl-neo-brutalist-page .rl-training-bullets li::before {{ content: '\\2014'; position: absolute; left: 0; color: var(--rl-color-gold); }}
.rl-neo-brutalist-page .rl-training-primary .rl-btn {{ background: var(--rl-color-gold); color: var(--rl-color-dark-brown); border-color: var(--rl-color-gold); }}
.rl-neo-brutalist-page .rl-training-primary .rl-btn:hover {{ background: var(--rl-color-light-gold); }}
.rl-neo-brutalist-page .rl-training-divider {{ display: flex; align-items: center; gap: 16px; margin: 20px 0; }}
.rl-neo-brutalist-page .rl-training-divider-line {{ flex: 1; height: 1px; background: var(--rl-color-tan); }}
.rl-neo-brutalist-page .rl-training-divider-text {{ font-family: var(--rl-font-data); font-size: 11px; font-weight: 700; color: var(--rl-color-secondary-brown); letter-spacing: var(--rl-letter-spacing-ultra-wide); }}
.rl-neo-brutalist-page .rl-training-secondary {{ border: 1px solid var(--rl-color-tan); border-top: 2px solid var(--rl-color-gold); background: var(--rl-color-warm-paper); padding: 28px 32px; display: flex; align-items: center; justify-content: space-between; gap: 24px; }}
.rl-neo-brutalist-page .rl-training-secondary-text h4 {{ font-family: var(--rl-font-data); font-size: var(--rl-font-size-sm); font-weight: 700; text-transform: uppercase; letter-spacing: var(--rl-letter-spacing-wider); margin-bottom: 6px; color: var(--rl-color-dark-brown); }}
.rl-neo-brutalist-page .rl-training-secondary-text .rl-training-subtitle {{ font-family: var(--rl-font-editorial); font-size: 12px; color: var(--rl-color-secondary-brown); margin: 0 0 8px 0; }}
.rl-neo-brutalist-page .rl-training-secondary-text p {{ font-family: var(--rl-font-editorial); font-size: 12px; color: var(--rl-color-secondary-brown); line-height: 1.5; margin: 0; }}
.rl-neo-brutalist-page .rl-training-secondary .rl-btn {{ background: transparent; color: var(--rl-color-primary-brown); border-color: var(--rl-color-primary-brown); }}
.rl-neo-brutalist-page .rl-training-secondary .rl-btn:hover {{ background: var(--rl-color-primary-brown); color: var(--rl-color-warm-paper); }}

/* Free Prep Kit CTA */
.rl-neo-brutalist-page .rl-training-free {{ text-align: center; margin-bottom: 20px; padding: 20px; border: var(--rl-border-subtle); background: var(--rl-color-warm-paper); }}
.rl-neo-brutalist-page .rl-training-free-desc {{ font-family: var(--rl-font-editorial); font-size: 12px; color: var(--rl-color-secondary-brown); margin: 8px 0 0; }}
.rl-neo-brutalist-page .rl-btn--outline {{ background: transparent; color: var(--rl-color-teal); border-color: var(--rl-color-teal); }}
.rl-neo-brutalist-page .rl-btn--outline:hover {{ background: var(--rl-color-teal); color: var(--rl-color-white); }}

/* ── Train for This Race ── */
.rl-neo-brutalist-page .rl-pack-subtitle {{ font-family: var(--rl-font-data); font-size: var(--rl-font-size-2xs); font-weight: 700; letter-spacing: var(--rl-letter-spacing-ultra-wide); text-transform: uppercase; color: var(--rl-color-secondary-brown); margin-bottom: 12px; }}
.rl-neo-brutalist-page .rl-pack-demands {{ margin-bottom: 24px; }}
.rl-neo-brutalist-page .rl-pack-demands-inline {{ display: grid; grid-template-columns: 1fr 1fr; gap: 4px 24px; }}
.rl-neo-brutalist-page .rl-pack-demand {{ display: flex; align-items: center; gap: 6px; }}
.rl-neo-brutalist-page .rl-pack-demand-label {{ font-family: var(--rl-font-data); font-size: 10px; width: 90px; min-width: 90px; text-transform: uppercase; letter-spacing: var(--rl-letter-spacing-wider); color: var(--rl-color-primary-brown); }}
.rl-neo-brutalist-page .rl-pack-demand-track {{ flex: 1; height: 6px; background: var(--rl-color-tan); border: 1px solid var(--rl-color-tan); }}
.rl-neo-brutalist-page .rl-pack-demand-fill {{ height: 100%; background: var(--rl-color-teal); transition: width 0.6s ease-out; }}
.rl-neo-brutalist-page .rl-pack-demand-score {{ font-family: var(--rl-font-data); font-size: 10px; width: 16px; text-align: right; color: var(--rl-color-secondary-brown); }}
@media (max-width: 600px) {{ .rl-neo-brutalist-page .rl-pack-demands-inline {{ grid-template-columns: 1fr; }} }}
.rl-neo-brutalist-page .rl-pack-workouts-toggle {{ text-align: center; margin: 24px 0 8px; }}
.rl-neo-brutalist-page .rl-pack-toggle-btn {{ width: 100%; background: transparent; color: var(--rl-color-secondary-brown); border: 2px solid var(--rl-color-tan); border-radius: 0; font-family: var(--rl-font-data); font-size: 12px; font-weight: 700; text-transform: uppercase; letter-spacing: var(--rl-letter-spacing-wider); display: flex; align-items: center; justify-content: center; gap: 8px; padding: 12px 16px; cursor: pointer; transition: border-color 0.2s, color 0.2s; -webkit-appearance: none; appearance: none; }}
.rl-neo-brutalist-page .rl-pack-toggle-btn:hover {{ border-color: var(--rl-color-primary-brown); color: var(--rl-color-primary-brown); background: transparent; }}
.rl-neo-brutalist-page .rl-pack-toggle-btn:focus-visible {{ outline: 2px solid var(--rl-color-teal); outline-offset: 2px; }}
.rl-neo-brutalist-page .rl-pack-toggle-arrow {{ font-size: 10px; transition: transform 0.2s; }}
@media (prefers-reduced-motion: reduce) {{ .rl-neo-brutalist-page .rl-pack-toggle-arrow {{ transition: none; }} }}
.rl-neo-brutalist-page .rl-pack-toggle-btn[aria-expanded="true"] .rl-pack-toggle-arrow {{ transform: rotate(180deg); }}
.rl-neo-brutalist-page .rl-pack-workouts {{ margin-bottom: 16px; margin-top: 16px; }}
.rl-neo-brutalist-page .rl-pack-workouts-intro {{ font-family: var(--rl-font-editorial); font-size: var(--rl-font-size-sm); color: var(--rl-color-secondary-brown); line-height: 1.6; margin-bottom: 20px; }}
.rl-neo-brutalist-page .rl-pack-workout {{ border: 2px solid var(--rl-color-tan); margin-bottom: 12px; background: var(--rl-color-warm-paper); cursor: pointer; transition: border-color 0.2s; }}
.rl-neo-brutalist-page .rl-pack-workout:hover {{ border-color: var(--rl-color-primary-brown); }}
.rl-neo-brutalist-page .rl-pack-workout.active {{ border-color: var(--rl-color-teal); border-width: 2px; }}
.rl-neo-brutalist-page .rl-pack-workout-header {{ display: flex; justify-content: space-between; align-items: flex-start; padding: 16px 16px 0; }}
.rl-neo-brutalist-page .rl-pack-workout-info {{ display: flex; flex-direction: column; gap: 2px; }}
.rl-neo-brutalist-page .rl-pack-workout-cat {{ font-family: var(--rl-font-data); font-size: 10px; font-weight: 700; text-transform: uppercase; letter-spacing: var(--rl-letter-spacing-ultra-wide); color: var(--rl-color-teal); }}
.rl-neo-brutalist-page .rl-pack-workout-name {{ font-family: var(--rl-font-data); font-size: var(--rl-font-size-sm); font-weight: 700; text-transform: uppercase; letter-spacing: var(--rl-letter-spacing-wider); color: var(--rl-color-dark-brown); }}
.rl-neo-brutalist-page .rl-pack-workout-meta {{ display: flex; align-items: center; gap: 12px; }}
.rl-neo-brutalist-page .rl-pack-workout-dur {{ font-family: var(--rl-font-data); font-size: 11px; color: var(--rl-color-secondary-brown); text-transform: uppercase; }}
.rl-neo-brutalist-page .rl-pack-workout-expand {{ font-family: var(--rl-font-data); font-size: 18px; font-weight: 700; color: var(--rl-color-teal); line-height: 1; width: 24px; height: 24px; display: flex; align-items: center; justify-content: center; transition: transform 0.2s; }}
.rl-neo-brutalist-page .rl-pack-workout.active .rl-pack-workout-expand {{ transform: rotate(45deg); }}
.rl-neo-brutalist-page .rl-pack-workout-summary {{ font-family: var(--rl-font-editorial); font-size: 12px; color: var(--rl-color-secondary-brown); line-height: 1.5; padding: 4px 16px 12px; }}
.rl-neo-brutalist-page .rl-pack-workout-context {{ font-family: var(--rl-font-editorial); font-size: 12px; font-style: italic; color: var(--rl-color-teal); line-height: 1.5; padding: 0 16px 8px; border-left: 3px solid var(--rl-color-teal); margin: 0 16px 8px; }}
.rl-neo-brutalist-page .rl-pack-workout-viz {{ display: flex; align-items: flex-end; gap: 1px; padding: 0 16px 16px; min-height: 50px; }}
.rl-neo-brutalist-page .rl-pack-viz-block {{ display: flex; align-items: flex-end; justify-content: center; border: 1px solid var(--rl-color-tan); font-family: var(--rl-font-data); font-size: 9px; font-weight: 600; overflow: hidden; }}
.rl-neo-brutalist-page .rl-pack-viz-label {{ padding: 2px; text-align: center; word-break: break-all; }}
.rl-neo-brutalist-page .rl-pack-viz-z1 {{ background: color-mix(in srgb, var(--rl-color-near-black) 8%, var(--rl-color-white)); color: var(--rl-color-near-black); }}
.rl-neo-brutalist-page .rl-pack-viz-z2 {{ background: var(--rl-color-sand); border-color: var(--rl-color-primary-brown); color: var(--rl-color-near-black); }}
.rl-neo-brutalist-page .rl-pack-viz-z3 {{ background: var(--rl-color-tan); color: var(--rl-color-near-black); }}
.rl-neo-brutalist-page .rl-pack-viz-z4 {{ background: var(--rl-color-primary-brown); color: var(--rl-color-sand); }}
.rl-neo-brutalist-page .rl-pack-viz-z5 {{ background: var(--rl-color-near-black); color: var(--rl-color-sand); }}
.rl-neo-brutalist-page .rl-pack-viz-z6 {{ background: var(--rl-color-near-black); color: var(--rl-color-light-teal); }}
.rl-neo-brutalist-page .rl-pack-workout-detail {{ padding: 0 16px 16px; border-top: 1px solid var(--rl-color-tan); margin: 0 16px; }}
.rl-neo-brutalist-page .rl-pack-wo-field {{ display: flex; gap: 12px; padding: 10px 0; border-bottom: 1px solid color-mix(in srgb, var(--rl-color-tan) 50%, transparent); }}
.rl-neo-brutalist-page .rl-pack-wo-field:last-child {{ border-bottom: none; }}
.rl-neo-brutalist-page .rl-pack-wo-label {{ font-family: var(--rl-font-data); font-size: 10px; font-weight: 700; text-transform: uppercase; letter-spacing: var(--rl-letter-spacing-ultra-wide); color: var(--rl-color-primary-brown); min-width: 80px; padding-top: 2px; }}
.rl-neo-brutalist-page .rl-pack-wo-value {{ font-family: var(--rl-font-editorial); font-size: 13px; color: var(--rl-color-near-black); line-height: 1.55; }}
.rl-neo-brutalist-page .rl-pack-wo-overlay {{ margin-top: 16px; padding: 16px; border: 2px solid var(--rl-color-teal); background: color-mix(in srgb, var(--rl-color-teal) 5%, var(--rl-color-warm-paper)); }}
.rl-neo-brutalist-page .rl-pack-wo-overlay-title {{ font-family: var(--rl-font-data); font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: var(--rl-letter-spacing-ultra-wide); color: var(--rl-color-teal); margin-bottom: 12px; }}
.rl-neo-brutalist-page .rl-pack-wo-overlay-item {{ margin-bottom: 10px; font-family: var(--rl-font-editorial); font-size: 12px; color: var(--rl-color-near-black); line-height: 1.5; }}
.rl-neo-brutalist-page .rl-pack-wo-overlay-item:last-child {{ margin-bottom: 0; }}
.rl-neo-brutalist-page .rl-pack-wo-overlay-tag {{ font-family: var(--rl-font-data); font-size: 10px; font-weight: 700; text-transform: uppercase; letter-spacing: var(--rl-letter-spacing-wider); color: var(--rl-color-teal); margin-right: 8px; }}
.rl-neo-brutalist-page .rl-pack-cta {{ text-align: center; padding: 24px; border: 2px solid var(--rl-color-tan); border-top: 3px solid var(--rl-color-teal); background: var(--rl-color-warm-paper); }}
.rl-neo-brutalist-page .rl-pack-cta .rl-btn {{ background: var(--rl-color-teal); color: var(--rl-color-white); border-color: var(--rl-color-teal); }}
.rl-neo-brutalist-page .rl-pack-cta .rl-btn:hover {{ background: var(--rl-color-light-teal); }}
.rl-neo-brutalist-page .rl-pack-cta-detail {{ font-family: var(--rl-font-editorial); font-size: 12px; color: var(--rl-color-secondary-brown); margin-top: 8px; }}

/* ── Plan Preview Configurator ── */
.rl-neo-brutalist-page .rl-cfg-bar {{ background: var(--rl-color-warm-paper); border: 3px solid var(--rl-color-primary-brown); padding: 24px; margin-bottom: 32px; }}
.rl-neo-brutalist-page .rl-cfg-title {{ font-family: var(--rl-font-data); font-size: var(--rl-font-size-2xs); font-weight: 700; letter-spacing: var(--rl-letter-spacing-ultra-wide); text-transform: uppercase; color: var(--rl-color-primary-brown); margin-bottom: 16px; }}
.rl-neo-brutalist-page .rl-cfg-inputs {{ display: flex; gap: 16px; margin-bottom: 16px; flex-wrap: wrap; }}
.rl-neo-brutalist-page .rl-cfg-field {{ display: flex; flex-direction: column; gap: 4px; flex: 1; min-width: 140px; }}
.rl-neo-brutalist-page .rl-cfg-label {{ font-family: var(--rl-font-data); font-size: 10px; font-weight: 700; text-transform: uppercase; letter-spacing: var(--rl-letter-spacing-wider); color: var(--rl-color-secondary-brown); }}
.rl-neo-brutalist-page .rl-cfg-select, .rl-neo-brutalist-page .rl-cfg-input {{ font-family: var(--rl-font-data); font-size: 13px; border: 2px solid var(--rl-color-primary-brown); border-radius: 0; background: var(--rl-color-white); padding: 8px 12px; color: var(--rl-color-near-black); -webkit-appearance: none; appearance: none; }}
.rl-neo-brutalist-page .rl-cfg-select {{ background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 12 12'%3E%3Cpath d='M2 4l4 4 4-4' fill='none' stroke='%2359473c' stroke-width='2'/%3E%3C/svg%3E"); background-repeat: no-repeat; background-position: right 10px center; padding-right: 32px; }}
.rl-neo-brutalist-page .rl-cfg-preview-btn {{ width: 100%; background: var(--rl-color-primary-brown); color: var(--rl-color-warm-paper); border-color: var(--rl-color-primary-brown); font-size: 13px; letter-spacing: var(--rl-letter-spacing-wider); }}
.rl-neo-brutalist-page .rl-cfg-preview-btn:hover {{ background: var(--rl-color-near-black); border-color: var(--rl-color-near-black); }}
.rl-neo-brutalist-page .rl-cfg-summary {{ border: 3px solid var(--rl-color-teal); background: var(--rl-color-warm-paper); padding: 24px; margin-bottom: 32px; }}
.rl-neo-brutalist-page .rl-cfg-summary-title {{ font-family: var(--rl-font-data); font-size: var(--rl-font-size-base); font-weight: 700; text-transform: uppercase; letter-spacing: var(--rl-letter-spacing-wider); color: var(--rl-color-near-black); margin-bottom: 16px; }}
.rl-neo-brutalist-page .rl-cfg-timeline {{ display: flex; gap: 4px; align-items: center; font-family: var(--rl-font-data); font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: var(--rl-letter-spacing-wider); color: var(--rl-color-secondary-brown); margin-bottom: 8px; flex-wrap: wrap; }}
.rl-neo-brutalist-page .rl-cfg-timeline-sep {{ color: var(--rl-color-tan); }}
.rl-neo-brutalist-page .rl-cfg-timeline-bar {{ display: flex; height: 8px; margin-bottom: 16px; }}
.rl-neo-brutalist-page .rl-cfg-bar-base {{ background: var(--rl-color-primary-brown); }}
.rl-neo-brutalist-page .rl-cfg-bar-build {{ background: var(--rl-color-teal); }}
.rl-neo-brutalist-page .rl-cfg-bar-peak {{ background: var(--rl-color-gold); }}
.rl-neo-brutalist-page .rl-cfg-bar-taper {{ background: var(--rl-color-tan); }}
.rl-neo-brutalist-page .rl-cfg-details {{ font-family: var(--rl-font-data); font-size: 12px; color: var(--rl-color-secondary-brown); line-height: 1.8; }}
.rl-neo-brutalist-page .rl-cfg-phase-badge {{ font-family: var(--rl-font-data); font-size: 10px; font-weight: 700; text-transform: uppercase; letter-spacing: var(--rl-letter-spacing-wider); padding: 4px 12px 0; }}
.rl-neo-brutalist-page .rl-cfg-phase-base {{ color: var(--rl-color-primary-brown); }}
.rl-neo-brutalist-page .rl-cfg-phase-build {{ color: var(--rl-color-teal); }}
.rl-neo-brutalist-page .rl-cfg-phase-peak {{ color: var(--rl-color-gold); }}
.rl-neo-brutalist-page .rl-cfg-level-note {{ font-family: var(--rl-font-data); font-size: 0.85em; color: var(--rl-color-secondary-brown); padding: 0 16px 8px; line-height: 1.5; }}
.rl-neo-brutalist-page .rl-cfg-cta {{ border-color: var(--rl-color-teal); }}
.rl-neo-brutalist-page .rl-cfg-cta-btn {{ background: var(--rl-color-teal); color: var(--rl-color-white); border-color: var(--rl-color-teal); font-size: 14px; letter-spacing: var(--rl-letter-spacing-wider); }}
.rl-neo-brutalist-page .rl-cfg-cta-btn:hover {{ background: var(--rl-color-light-teal); }}

/* Logistics */
.rl-neo-brutalist-page .rl-logistics-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }}
.rl-neo-brutalist-page .rl-logistics-item {{ border: var(--rl-border-subtle); padding: 12px; background: var(--rl-color-warm-paper); }}
.rl-neo-brutalist-page .rl-logistics-item-label {{ font-family: var(--rl-font-data); font-size: var(--rl-font-size-2xs); font-weight: 700; letter-spacing: var(--rl-letter-spacing-wider); text-transform: uppercase; color: var(--rl-color-secondary-brown); margin-bottom: var(--rl-spacing-2xs); }}
.rl-neo-brutalist-page .rl-logistics-item-value {{ font-family: var(--rl-font-editorial); font-size: var(--rl-font-size-sm); color: var(--rl-color-dark-brown); line-height: 1.5; }}

/* Riders Report callout */
.rl-neo-brutalist-page .rl-riders-report {{ border-left: 3px solid var(--rl-color-teal); padding: var(--rl-spacing-md) var(--rl-spacing-lg); margin-top: var(--rl-spacing-lg); background: var(--rl-color-warm-paper); }}
.rl-neo-brutalist-page .rl-riders-report-badge {{ font-family: var(--rl-font-data); font-size: 10px; font-weight: 700; letter-spacing: var(--rl-letter-spacing-wider); text-transform: uppercase; color: var(--rl-color-teal); margin-bottom: var(--rl-spacing-sm); }}
.rl-neo-brutalist-page .rl-riders-report-item {{ margin-bottom: var(--rl-spacing-sm); }}
.rl-neo-brutalist-page .rl-riders-report-item:last-child {{ margin-bottom: 0; }}
.rl-neo-brutalist-page .rl-riders-report-name {{ font-family: var(--rl-font-data); font-size: var(--rl-font-size-xs); font-weight: 700; color: var(--rl-color-primary-brown); }}
.rl-neo-brutalist-page .rl-riders-report-mile {{ font-family: var(--rl-font-data); font-size: var(--rl-font-size-2xs); color: var(--rl-color-teal); margin-left: var(--rl-spacing-xs); }}
.rl-neo-brutalist-page .rl-riders-report-desc {{ font-family: var(--rl-font-editorial); font-size: var(--rl-font-size-sm); color: var(--rl-color-dark-brown); line-height: 1.5; margin-top: 2px; }}
@media (max-width: 600px) {{
  .rl-neo-brutalist-page .rl-riders-report {{ padding: var(--rl-spacing-sm) var(--rl-spacing-md); }}
}}

/* News ticker */
.rl-neo-brutalist-page .rl-news-ticker {{ background: var(--rl-color-sand); border: 1px solid var(--rl-color-tan); margin-bottom: 32px; display: flex; align-items: stretch; overflow: hidden; height: 48px; }}
.rl-neo-brutalist-page .rl-news-ticker-label {{ background: var(--rl-color-gold); color: var(--rl-color-warm-paper); font-family: var(--rl-font-data); font-size: var(--rl-font-size-2xs); font-weight: 700; letter-spacing: var(--rl-letter-spacing-wider); text-transform: uppercase; padding: 0 var(--rl-spacing-md); display: flex; align-items: center; white-space: nowrap; min-width: fit-content; border-right: 1px solid var(--rl-color-tan); }}
.rl-neo-brutalist-page .rl-news-ticker-track {{ flex: 1; overflow: hidden; position: relative; display: flex; align-items: center; }}
.rl-neo-brutalist-page .rl-news-ticker-content {{ display: flex; align-items: center; white-space: nowrap; animation: rl-ticker-scroll 80s linear infinite; padding-left: 100%; }}
.rl-neo-brutalist-page .rl-news-ticker-content:hover {{ animation-play-state: paused; }}
.rl-neo-brutalist-page .rl-news-ticker-item {{ display: inline-flex; align-items: center; gap: 6px; padding: 0 32px; }}
.rl-neo-brutalist-page .rl-news-ticker-item a {{ color: var(--rl-color-primary-brown); text-decoration: none; font-family: var(--rl-font-data); font-size: 12px; font-weight: 700; letter-spacing: 0.5px; }}
.rl-neo-brutalist-page .rl-news-ticker-item a:hover {{ color: var(--rl-color-teal); }}
.rl-neo-brutalist-page .rl-news-ticker-source {{ color: var(--rl-color-secondary-brown); font-size: var(--rl-font-size-2xs); font-weight: 400; }}
.rl-neo-brutalist-page .rl-news-ticker-sep {{ color: var(--rl-color-teal); font-size: 8px; margin: 0 8px; }}
.rl-neo-brutalist-page .rl-news-ticker-loading {{ color: var(--rl-color-secondary-brown); font-size: 11px; letter-spacing: 1px; padding-left: 16px; }}
.rl-neo-brutalist-page .rl-news-ticker-empty {{ color: var(--rl-color-secondary-brown); font-size: 11px; letter-spacing: 1px; padding-left: 16px; }}
@keyframes rl-ticker-scroll {{ 0% {{ transform: translateX(0); }} 100% {{ transform: translateX(-100%); }} }}

/* Sticky CTA */
.rl-sticky-cta {{ position: fixed; bottom: 0; left: 0; right: 0; z-index: 200; background: var(--rl-color-near-black); border-top: 3px solid var(--rl-color-teal); padding: 12px 24px; transform: translateY(100%); transition: transform 0.3s ease; }}
.rl-sticky-cta.is-visible {{ transform: translateY(0); }}
.rl-sticky-cta-inner {{ max-width: 960px; margin: 0 auto; display: flex; align-items: center; justify-content: space-between; gap: 16px; }}
.rl-sticky-cta-name {{ font-family: var(--rl-font-data); font-size: 13px; font-weight: 700; color: var(--rl-color-white); text-transform: uppercase; letter-spacing: 1px; }}
.rl-sticky-cta .rl-btn {{ font-family: var(--rl-font-data); background: var(--rl-color-teal); color: var(--rl-color-white); border: var(--rl-border-width-subtle) solid var(--rl-color-teal); padding: var(--rl-spacing-xs) 20px; font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: var(--rl-letter-spacing-wider); text-decoration: none; cursor: pointer; }}
.rl-sticky-cta .rl-btn:hover {{ background: #14695F; border-color: #14695F; }}
.rl-sticky-dismiss {{ background: none; border: none; color: var(--rl-color-white); font-size: 22px; cursor: pointer; opacity: 0.6; padding: 0 4px; line-height: 1; }}
.rl-sticky-dismiss:hover {{ opacity: 1; }}


/* Back to top */
.rl-back-to-top {{ position: fixed; bottom: 72px; right: 20px; z-index: 199; width: 40px; height: 40px; background: var(--rl-color-dark-brown); color: var(--rl-color-warm-paper); border: 2px solid var(--rl-color-warm-paper); font-size: 18px; cursor: pointer; opacity: 0; visibility: hidden; transition: opacity 0.2s, visibility 0.2s; display: flex; align-items: center; justify-content: center; }}
.rl-back-to-top.is-visible {{ opacity: 1; visibility: visible; }}
.rl-back-to-top:hover {{ background: var(--rl-color-warm-paper); color: var(--rl-color-dark-brown); }}

/* Scroll fade-in */
.rl-neo-brutalist-page .rl-fade-section {{ opacity: 0; transform: translateY(20px); transition: opacity 0.6s ease, transform 0.6s ease; }}
.rl-neo-brutalist-page .rl-fade-section.is-visible {{ opacity: 1; transform: translateY(0); }}

/* Email capture */
.rl-neo-brutalist-page .rl-email-capture {{ margin-bottom: var(--rl-spacing-xl); border: 1px solid var(--rl-color-tan); border-top: 2px solid var(--rl-color-teal); background: var(--rl-color-warm-paper); padding: 0; }}
.rl-neo-brutalist-page .rl-email-capture-inner {{ padding: var(--rl-spacing-lg) var(--rl-spacing-xl); text-align: center; }}
.rl-neo-brutalist-page .rl-email-capture-badge {{ display: inline-block; font-family: var(--rl-font-data); font-size: 10px; font-weight: 700; letter-spacing: 3px; text-transform: uppercase; background: var(--rl-color-teal); color: var(--rl-color-white); padding: 3px 10px; margin-bottom: var(--rl-spacing-xs); }}
.rl-neo-brutalist-page .rl-email-capture-title {{ font-family: var(--rl-font-data); font-size: var(--rl-font-size-sm); font-weight: 700; letter-spacing: var(--rl-letter-spacing-ultra-wide); color: var(--rl-color-dark-brown); margin: 0 0 var(--rl-spacing-2xs) 0; }}
.rl-neo-brutalist-page .rl-email-capture-text {{ font-family: var(--rl-font-editorial); font-size: 12px; color: var(--rl-color-secondary-brown); line-height: var(--rl-line-height-relaxed); margin: 0 0 var(--rl-spacing-md) 0; max-width: 500px; margin-left: auto; margin-right: auto; }}
.rl-neo-brutalist-page .rl-email-capture-row {{ display: flex; gap: 0; max-width: 420px; margin: 0 auto var(--rl-spacing-xs); }}
.rl-neo-brutalist-page .rl-email-capture-input {{ flex: 1; font-family: var(--rl-font-data); font-size: 13px; padding: 12px 14px; border: 2px solid var(--rl-color-tan); border-right: none; background: var(--rl-color-white); color: var(--rl-color-dark-brown); min-width: 0; }}
.rl-neo-brutalist-page .rl-email-capture-input:focus {{ outline: none; border-color: var(--rl-color-teal); }}
.rl-neo-brutalist-page .rl-email-capture-btn {{ font-family: var(--rl-font-data); font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: 2px; padding: 12px 18px; background: var(--rl-color-teal); color: var(--rl-color-white); border: 2px solid var(--rl-color-teal); cursor: pointer; white-space: nowrap; transition: background 0.2s; }}
.rl-neo-brutalist-page .rl-email-capture-btn:hover {{ background: var(--rl-color-light-teal); }}
.rl-neo-brutalist-page .rl-email-capture-fine {{ font-family: var(--rl-font-data); font-size: 10px; color: var(--rl-color-warm-brown); letter-spacing: 1px; margin: 0; }}
.rl-neo-brutalist-page .rl-email-capture-success {{ padding: var(--rl-spacing-sm) 0; }}
.rl-neo-brutalist-page .rl-email-capture-check {{ font-family: var(--rl-font-data); font-size: 14px; font-weight: 700; color: var(--rl-color-light-teal); margin: 0 0 var(--rl-spacing-xs); }}
.rl-neo-brutalist-page .rl-email-capture-link {{ display: inline-block; font-family: var(--rl-font-data); font-size: 13px; font-weight: 700; text-transform: uppercase; letter-spacing: 2px; color: var(--rl-color-white); background: var(--rl-color-teal); padding: 10px 20px; text-decoration: none; border: 2px solid var(--rl-color-teal); transition: background 0.2s; }}
.rl-neo-brutalist-page .rl-email-capture-link:hover {{ background: var(--rl-color-light-teal); }}

/* Countdown */
.rl-neo-brutalist-page .rl-countdown {{ border: 1px solid var(--rl-color-teal); background: var(--rl-color-warm-paper); color: var(--rl-color-dark-brown); padding: var(--rl-spacing-md); text-align: center; font-family: var(--rl-font-data); font-size: 12px; font-weight: 700; letter-spacing: var(--rl-letter-spacing-ultra-wide); margin-bottom: 20px; }}
.rl-neo-brutalist-page .rl-countdown-num {{ font-size: 32px; color: var(--rl-color-teal); display: block; line-height: 1.2; }}

/* FAQ accordion */
.rl-neo-brutalist-page .rl-faq-item {{ border-bottom: 1px solid var(--rl-color-sand); }}
.rl-neo-brutalist-page .rl-faq-item:last-child {{ border-bottom: none; }}
.rl-neo-brutalist-page .rl-faq-question {{ display: flex; align-items: center; justify-content: space-between; cursor: pointer; padding: 16px 0; gap: 12px; }}
.rl-neo-brutalist-page .rl-faq-question h3 {{ font-family: var(--rl-font-editorial); font-size: var(--rl-font-size-xs); font-weight: 700; color: var(--rl-color-dark-brown); margin: 0; text-transform: none; letter-spacing: 0; }}
.rl-neo-brutalist-page .rl-faq-toggle {{ font-size: 20px; font-weight: 700; color: var(--rl-color-primary-brown); transition: transform 0.3s; flex-shrink: 0; }}
.rl-neo-brutalist-page .rl-faq-item.open .rl-faq-toggle {{ transform: rotate(45deg); }}
.rl-neo-brutalist-page .rl-faq-answer {{ max-height: 0; overflow: hidden; transition: max-height 0.3s ease; }}
.rl-neo-brutalist-page .rl-faq-answer p {{ font-family: var(--rl-font-editorial); font-size: var(--rl-font-size-sm); color: var(--rl-color-secondary-brown); line-height: var(--rl-line-height-prose); margin: 0; }}
.rl-neo-brutalist-page .rl-faq-item.open .rl-faq-answer {{ max-height: 500px; padding-bottom: 16px; }}

/* Similar races */
.rl-neo-brutalist-page .rl-similar-grid {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; }}
.rl-neo-brutalist-page .rl-similar-card {{ display: block; border: var(--rl-border-subtle); padding: 16px; background: var(--rl-color-warm-paper); text-decoration: none; color: var(--rl-color-dark-brown); transition: border-color 0.15s, background 0.15s; }}
.rl-neo-brutalist-page .rl-similar-card:hover {{ border-color: var(--rl-color-gold); background: var(--rl-color-sand); }}
.rl-neo-brutalist-page .rl-similar-tier {{ font-family: var(--rl-font-data); display: inline-block; background: var(--rl-color-gold); color: var(--rl-color-dark-brown); padding: 2px 8px; font-size: 9px; font-weight: 700; letter-spacing: var(--rl-letter-spacing-wider); margin-bottom: 6px; }}
.rl-neo-brutalist-page .rl-similar-name {{ font-family: var(--rl-font-editorial); display: block; font-size: var(--rl-font-size-base); font-weight: var(--rl-font-weight-semibold); letter-spacing: 0; margin-bottom: 4px; }}
.rl-neo-brutalist-page .rl-similar-meta {{ display: block; font-size: var(--rl-font-size-2xs); color: var(--rl-color-secondary-brown); letter-spacing: 0.5px; }}

{get_site_header_css()}
.rl-breadcrumb {{ font-family: var(--rl-font-data); font-size: 11px; padding: 8px 24px; background: var(--rl-color-sand); }}
.rl-breadcrumb a {{ color: var(--rl-color-warm-brown); text-decoration: none; }}
.rl-breadcrumb a:hover {{ color: var(--rl-color-gold); }}
.rl-breadcrumb-sep {{ color: var(--rl-color-secondary-brown); margin: 0 4px; }}
.rl-breadcrumb-current {{ color: var(--rl-color-dark-brown); }}

/* Citations */
.rl-neo-brutalist-page .rl-citations-intro {{ font-size: var(--rl-font-size-xs); color: var(--rl-color-secondary-brown); margin-bottom: var(--rl-spacing-md); line-height: var(--rl-line-height-relaxed); }}
.rl-neo-brutalist-page .rl-citations-list {{ list-style: decimal; padding-left: 24px; margin: 0; }}
.rl-neo-brutalist-page .rl-citation-item {{ font-size: var(--rl-font-size-2xs); line-height: 1.8; border-bottom: 1px solid var(--rl-color-cream); padding: 4px 0; }}
.rl-neo-brutalist-page .rl-citation-item:last-child {{ border-bottom: none; }}
.rl-neo-brutalist-page .rl-citation-cat {{ display: inline-block; background: var(--rl-color-dark-brown); color: var(--rl-color-warm-paper); font-size: 9px; font-weight: 700; letter-spacing: var(--rl-letter-spacing-wider); text-transform: uppercase; padding: 1px 6px; margin-right: 6px; }}
.rl-neo-brutalist-page .rl-citation-link {{ color: var(--rl-color-dark-teal); text-decoration: none; font-weight: 600; }}
.rl-neo-brutalist-page .rl-citation-link:hover {{ color: var(--rl-color-teal); text-decoration: underline; }}
.rl-neo-brutalist-page .rl-citation-url {{ display: block; color: var(--rl-color-secondary-brown); font-size: 9px; word-break: break-all; }}

/* Footer — last-updated line (mega-footer CSS is appended separately) */
.rl-neo-brutalist-page .rl-footer-updated {{ color: var(--rl-color-secondary-brown); font-size: var(--rl-font-size-2xs); margin: var(--rl-spacing-xs) 0 0 0; letter-spacing: 1px; text-transform: uppercase; text-align: center; }}

/* Racer reviews section */
.rl-neo-brutalist-page .rl-racer-reviews {{ margin-bottom: 32px; border: var(--rl-border-standard); background: var(--rl-color-warm-paper); }}
.rl-neo-brutalist-page .rl-racer-stars {{ display: flex; align-items: center; gap: 8px; margin-bottom: var(--rl-spacing-md); font-family: var(--rl-font-data); font-size: var(--rl-font-size-sm); }}
.rl-neo-brutalist-page .rl-racer-stars-icons {{ color: var(--rl-color-gold); font-size: var(--rl-font-size-md); }}
.rl-neo-brutalist-page .rl-racer-stars-avg {{ font-weight: var(--rl-font-weight-bold); color: var(--rl-color-dark-brown); }}
.rl-neo-brutalist-page .rl-racer-stars-sep {{ color: var(--rl-color-warm-brown); }}
.rl-neo-brutalist-page .rl-racer-stars-count {{ color: var(--rl-color-secondary-brown); }}
.rl-neo-brutalist-page .rl-review-item {{ border-bottom: 1px solid var(--rl-color-sand); padding: var(--rl-spacing-sm) 0; }}
.rl-neo-brutalist-page .rl-review-item:last-of-type {{ border-bottom: none; }}
.rl-neo-brutalist-page .rl-review-text {{ font-family: var(--rl-font-editorial); font-size: var(--rl-font-size-sm); font-style: italic; line-height: var(--rl-line-height-relaxed); color: var(--rl-color-dark-brown); }}
.rl-neo-brutalist-page .rl-review-meta {{ font-family: var(--rl-font-data); font-size: var(--rl-font-size-2xs); color: var(--rl-color-gold); margin-top: 4px; }}
.rl-neo-brutalist-page .rl-review-finish {{ display: inline-block; background: var(--rl-color-sand); color: var(--rl-color-secondary-brown); padding: 1px 6px; font-size: 9px; font-weight: var(--rl-font-weight-bold); letter-spacing: var(--rl-letter-spacing-wider); text-transform: uppercase; margin-left: 8px; }}
.rl-neo-brutalist-page .rl-btn--rate {{ display: inline-block; margin-top: var(--rl-spacing-md); padding: 10px 24px; background: var(--rl-color-teal); color: var(--rl-color-white); font-family: var(--rl-font-data); font-size: var(--rl-font-size-xs); font-weight: var(--rl-font-weight-bold); text-transform: uppercase; letter-spacing: var(--rl-letter-spacing-wider); text-decoration: none; border: var(--rl-border-standard); cursor: pointer; }}
.rl-neo-brutalist-page .rl-btn--rate:hover {{ background: #14695F; }}
.rl-neo-brutalist-page .rl-racer-empty, .rl-neo-brutalist-page .rl-racer-pending {{ background: var(--rl-color-sand); padding: var(--rl-spacing-xl); text-align: center; }}
.rl-neo-brutalist-page .rl-racer-empty-text, .rl-neo-brutalist-page .rl-racer-pending-text {{ font-family: var(--rl-font-data); font-size: var(--rl-font-size-sm); color: var(--rl-color-secondary-brown); letter-spacing: var(--rl-letter-spacing-wider); text-transform: uppercase; margin-bottom: var(--rl-spacing-sm); }}

/* Inline review form */
.rl-neo-brutalist-page .rl-review-form-wrap {{ border-top: 2px solid var(--rl-color-tan); padding-top: var(--rl-spacing-lg); margin-top: var(--rl-spacing-lg); }}
.rl-neo-brutalist-page .rl-review-form-title {{ font-family: var(--rl-font-data); font-size: var(--rl-font-size-sm); font-weight: 700; text-transform: uppercase; letter-spacing: var(--rl-letter-spacing-ultra-wide); color: var(--rl-color-dark-brown); margin: 0 0 var(--rl-spacing-md); }}
.rl-neo-brutalist-page .rl-review-form-row {{ display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-bottom: 12px; }}
.rl-neo-brutalist-page .rl-review-field {{ display: flex; flex-direction: column; gap: 4px; }}
.rl-neo-brutalist-page .rl-review-field--full {{ grid-column: 1 / -1; margin-bottom: 12px; }}
.rl-neo-brutalist-page .rl-review-field label {{ font-family: var(--rl-font-data); font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: 1px; color: var(--rl-color-dark-brown); }}
.rl-neo-brutalist-page .rl-review-input, .rl-neo-brutalist-page .rl-review-select, .rl-neo-brutalist-page .rl-review-textarea {{ font-family: var(--rl-font-data); font-size: 13px; padding: 8px 10px; border: 2px solid var(--rl-color-tan); background: var(--rl-color-white); color: var(--rl-color-dark-brown); width: 100%; box-sizing: border-box; }}
.rl-neo-brutalist-page .rl-review-input:focus, .rl-neo-brutalist-page .rl-review-textarea:focus {{ outline: none; border-color: var(--rl-color-teal); }}
.rl-neo-brutalist-page .rl-review-textarea {{ resize: vertical; min-height: 48px; }}
.rl-neo-brutalist-page .rl-review-charcount {{ display: block; font-family: var(--rl-font-data); font-size: 10px; color: var(--rl-color-secondary-brown); text-align: right; margin-top: 2px; letter-spacing: 0.5px; }}
.rl-neo-brutalist-page .rl-review-star-row {{ display: flex; gap: 4px; margin-bottom: 12px; }}
.rl-neo-brutalist-page .rl-review-star-btn {{ background: none; border: none; font-size: 28px; color: var(--rl-color-tan); cursor: pointer; padding: 0 2px; transition: color 0.15s; }}
.rl-neo-brutalist-page .rl-review-star-btn:hover, .rl-neo-brutalist-page .rl-review-star-btn.is-active {{ color: var(--rl-color-gold); }}
.rl-neo-brutalist-page .rl-review-field-label {{ font-family: var(--rl-font-data); font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: 1px; color: var(--rl-color-dark-brown); margin-bottom: 4px; }}
.rl-neo-brutalist-page .rl-review-success {{ text-align: center; padding: var(--rl-spacing-lg); }}
.rl-neo-brutalist-page .rl-review-success-icon {{ font-size: 36px; color: var(--rl-color-teal); margin-bottom: var(--rl-spacing-xs); }}
.rl-neo-brutalist-page .rl-review-success-text {{ font-family: var(--rl-font-data); font-size: 13px; color: var(--rl-color-primary-brown); }}

/* From the Field — rider quotes + video embeds */
.rl-neo-brutalist-page .rl-field-quote {{ border-left: 3px solid var(--rl-color-teal); padding: 12px 16px; margin: 0 0 16px 0; background: var(--rl-color-sand); }}
.rl-neo-brutalist-page .rl-field-quote-text {{ font-family: var(--rl-font-editorial); font-size: var(--rl-font-size-base); font-style: italic; line-height: var(--rl-line-height-prose); color: var(--rl-color-primary-brown); margin: 0 0 6px 0; }}
.rl-neo-brutalist-page .rl-field-quote-cite {{ display: block; font-family: var(--rl-font-data); font-size: 11px; font-style: normal; font-weight: 700; letter-spacing: var(--rl-letter-spacing-wider); text-transform: uppercase; color: var(--rl-color-secondary-brown); }}
.rl-neo-brutalist-page .rl-field-video-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-top: 20px; }}
.rl-neo-brutalist-page .rl-field-video {{ border: 1px solid var(--rl-color-tan); background: var(--rl-color-warm-paper); }}
.rl-neo-brutalist-page .rl-lite-youtube {{ position: relative; cursor: pointer; overflow: hidden; aspect-ratio: 16/9; background: var(--rl-color-near-black); }}
.rl-neo-brutalist-page .rl-lite-youtube-thumb {{ width: 100%; height: 100%; object-fit: cover; display: block; }}
.rl-neo-brutalist-page .rl-lite-youtube-play {{ position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); background: none; border: none; cursor: pointer; padding: 0; opacity: 0.85; transition: opacity 0.2s; }}
.rl-neo-brutalist-page .rl-lite-youtube-play:hover {{ opacity: 1; }}
.rl-neo-brutalist-page .rl-lite-youtube iframe {{ position: absolute; top: 0; left: 0; width: 100%; height: 100%; border: none; }}
.rl-neo-brutalist-page .rl-field-video-meta {{ font-family: var(--rl-font-data); font-size: 11px; color: var(--rl-color-secondary-brown); padding: 8px 10px; letter-spacing: 0.5px; }}

/* Responsive — tablet */
@media (max-width: 1024px) {{
  .rl-neo-brutalist-page .rl-radar-pair {{ gap: 8px; }}
  .rl-neo-brutalist-page .rl-similar-grid {{ grid-template-columns: 1fr 1fr; }}  /* 2-col on tablet */
  .rl-neo-brutalist-page .rl-stat-grid {{ grid-template-columns: repeat(3, 1fr); gap: 10px; }}
  .rl-neo-brutalist-page .rl-news-ticker {{ display: none; }}
}}

/* Responsive — mobile */
@media (max-width: 768px) {{
  .rl-neo-brutalist-page .rl-hero {{ flex-direction: column; align-items: flex-start; padding: 32px 20px; gap: 20px; }}
  .rl-neo-brutalist-page .rl-hero h1 {{ font-size: 28px; }}
  .rl-neo-brutalist-page .rl-hero-score {{ display: flex; align-items: baseline; gap: 10px; }}
  .rl-neo-brutalist-page .rl-hero-score-number {{ font-size: 48px; }}
  .rl-neo-brutalist-page .rl-hero-score-label {{ margin-top: 0; }}
  .rl-neo-brutalist-page .rl-stat-grid {{ grid-template-columns: repeat(2, 1fr); }}
  .rl-neo-brutalist-page .rl-verdict-grid {{ grid-template-columns: 1fr; }}
  .rl-neo-brutalist-page .rl-logistics-grid {{ grid-template-columns: 1fr; }}
  .rl-neo-brutalist-page .rl-ratings-summary {{ flex-direction: column; }}
  .rl-neo-brutalist-page .rl-radar-pair {{ flex-direction: column; }}
  .rl-neo-brutalist-page .rl-accordion-label {{ width: 80px; min-width: 80px; font-size: 10px; }}
  .rl-neo-brutalist-page .rl-accordion-content {{ padding-left: 0; }}
  .rl-neo-brutalist-page .rl-training-secondary {{ flex-direction: column; text-align: center; }}
  .rl-neo-brutalist-page .rl-pack-demand-label {{ width: 80px; min-width: 80px; font-size: 10px; }}
  .rl-neo-brutalist-page .rl-pack-workout-header {{ flex-wrap: wrap; }}
  .rl-neo-brutalist-page .rl-pack-wo-field {{ flex-direction: column; gap: 4px; }}
  .rl-neo-brutalist-page .rl-pack-wo-label {{ min-width: unset; }}
  .rl-neo-brutalist-page .rl-pack-viz-label {{ font-size: 8px; }}
  .rl-neo-brutalist-page .rl-cfg-inputs {{ flex-direction: column; }}
  .rl-neo-brutalist-page .rl-cfg-bar {{ padding: 16px; }}
  .rl-neo-brutalist-page .rl-cfg-summary {{ padding: 16px; }}
  .rl-neo-brutalist-page .rl-cfg-timeline {{ font-size: 10px; }}
  .rl-sticky-cta-name {{ display: none; }}
  .rl-sticky-cta .rl-btn {{ width: 100%; text-align: center; }}
  .rl-neo-brutalist-page .rl-toc {{ flex-direction: column; gap: 6px; }}
  .rl-neo-brutalist-page .rl-map-embed iframe {{ height: 350px; }}
  .rl-neo-brutalist-page .rl-pullquote {{ padding: var(--rl-spacing-lg); }}
  .rl-neo-brutalist-page .rl-pullquote-text {{ font-size: var(--rl-font-size-base); }}
  .rl-neo-brutalist-page .rl-pullquote-text::before {{ position: static; display: block; margin-bottom: -10px; }}
  .rl-neo-brutalist-page .rl-pullquote-text::after {{ display: none; }}
  .rl-neo-brutalist-page .rl-news-ticker-label {{ font-size: 9px; padding: 0 10px; letter-spacing: 1px; }}
  .rl-neo-brutalist-page .rl-email-capture-row {{ flex-direction: column; gap: 8px; }}
  .rl-neo-brutalist-page .rl-email-capture-input {{ border-right: 2px solid var(--rl-color-tan); }}
  .rl-neo-brutalist-page .rl-similar-grid {{ grid-template-columns: 1fr; }}
  .rl-neo-brutalist-page .rl-field-video-grid {{ grid-template-columns: 1fr; }}
  .rl-neo-brutalist-page .rl-review-form-row {{ grid-template-columns: 1fr; }}
  .rl-neo-brutalist-page .rl-countdown-num {{ font-size: 24px; }}
}}

/* Responsive — small phones */
@media (max-width: 480px) {{
  .rl-neo-brutalist-page {{ padding: 0 12px; }}
  .rl-neo-brutalist-page .rl-hero {{ padding: var(--rl-spacing-xl) var(--rl-spacing-md); }}
  .rl-neo-brutalist-page .rl-hero h1 {{ font-size: var(--rl-font-size-xl); }}
  .rl-neo-brutalist-page .rl-hero-score-number {{ font-size: var(--rl-font-size-3xl); }}
  .rl-neo-brutalist-page .rl-stat-grid {{ grid-template-columns: 1fr; }}
  .rl-neo-brutalist-page .rl-section-header {{ flex-wrap: wrap; gap: 4px 12px; padding: 12px 16px; }}
  .rl-neo-brutalist-page .rl-section-kicker {{ white-space: normal; }}
  .rl-neo-brutalist-page .rl-section-body {{ padding: 16px 12px; }}
  .rl-neo-brutalist-page .rl-suffering-mile {{ min-width: 60px; padding: 8px; }}
  .rl-neo-brutalist-page .rl-suffering-mile-num {{ font-size: var(--rl-font-size-md); }}
  .rl-neo-brutalist-page .rl-suffering-content {{ padding: 8px 12px; }}
  .rl-neo-brutalist-page .rl-accordion-label {{ width: 65px; min-width: 65px; font-size: 9px; letter-spacing: 0.5px; }}
  .rl-neo-brutalist-page .rl-accordion-score {{ width: 32px; min-width: 32px; font-size: 12px; }}
  .rl-neo-brutalist-page .rl-breadcrumb {{ font-size: 10px; }}
  .rl-sticky-cta {{ padding: 10px 12px; }}
  .rl-back-to-top {{ bottom: 60px; right: 12px; width: 36px; height: 36px; }}
}}
''' + get_mega_footer_css() + '''
</style>'''


# ── Shared Assets ─────────────────────────────────────────────


def _extract_css_content() -> str:
    """Extract raw CSS from get_page_css() (strip <style> tags)."""
    raw = get_page_css()
    return raw.replace('<style>', '').replace('</style>', '').strip()


def _extract_js_content() -> str:
    """Extract raw JS from build_inline_js() (strip <script> tags)."""
    raw = build_inline_js()
    return raw.replace('<script>', '').replace('</script>', '').strip()


def write_shared_assets(output_dir: Path) -> dict:
    """Write shared CSS/JS to external files with content hash. Returns asset info."""
    assets_dir = output_dir / "assets"
    assets_dir.mkdir(parents=True, exist_ok=True)

    # Copy self-hosted font files (clean stale files first)
    fonts_dir = assets_dir / "fonts"
    fonts_dir.mkdir(parents=True, exist_ok=True)
    wanted = set(FONT_FILES)
    for old in fonts_dir.glob("*.woff2"):
        if old.name not in wanted:
            old.unlink()
    for font_file in FONT_FILES:
        src = BRAND_FONTS_DIR / font_file
        dst = fonts_dir / font_file
        if src.exists():
            shutil.copy2(src, dst)
        else:
            print(f"  WARNING: Font file not found: {src}")
    print(f"  Copied {len(FONT_FILES)} font files to {fonts_dir}/")

    css_content = _extract_css_content()
    js_content = _extract_js_content()

    css_hash = hashlib.md5(css_content.encode()).hexdigest()[:8]
    js_hash = hashlib.md5(js_content.encode()).hexdigest()[:8]

    css_file = f"rl-styles.{css_hash}.css"
    js_file = f"rl-scripts.{js_hash}.js"

    # Clean up stale hashed assets before writing new ones
    for old in assets_dir.glob("rl-styles.*.css"):
        if old.name != css_file:
            old.unlink()
    for old in assets_dir.glob("rl-scripts.*.js"):
        if old.name != js_file:
            old.unlink()

    (assets_dir / css_file).write_text(css_content, encoding='utf-8')
    (assets_dir / js_file).write_text(js_content, encoding='utf-8')

    print(f"  Wrote {assets_dir / css_file} ({len(css_content):,} bytes)")
    print(f"  Wrote {assets_dir / js_file} ({len(js_content):,} bytes)")

    return {
        "css_tag": f'<link rel="stylesheet" href="/race/assets/{css_file}">',
        "js_tag": f'<script src="/race/assets/{js_file}"></script>',
    }


# ── Page Assembly ──────────────────────────────────────────────

def generate_page(rd: dict, race_index: list = None, external_assets: dict = None) -> str:
    """Generate complete HTML page from normalized race data.

    If external_assets is provided, references external CSS/JS files instead of inlining.
    """
    race_index = race_index or []
    canonical_url = f"{SITE_BASE_URL}/race/{rd['slug']}/"

    # JSON-LD
    jsonld_parts = []
    sports_event = build_sports_event_jsonld(rd)
    if sports_event is not None:
        jsonld_parts.append(_safe_json_for_script(sports_event, ensure_ascii=False, separators=(',', ':')))
    faq = build_faq_jsonld(rd)
    if faq:
        jsonld_parts.append(_safe_json_for_script(faq, ensure_ascii=False, separators=(',', ':')))
    if race_index:
        breadcrumb = build_breadcrumb_jsonld(rd, race_index)
        jsonld_parts.append(_safe_json_for_script(breadcrumb, ensure_ascii=False, separators=(',', ':')))

    webpage = build_webpage_jsonld(rd)
    jsonld_parts.append(_safe_json_for_script(webpage, ensure_ascii=False, separators=(',', ':')))

    jsonld_html = '\n'.join(
        f'<script type="application/ld+json">{j}</script>'
        for j in jsonld_parts
    )

    # Build sections
    nav_header = build_nav_header(rd, race_index)
    hero = build_hero(rd)
    course_overview = build_course_overview(rd, race_index)
    history = build_history(rd)
    pullquote = build_pullquote(rd)
    course_route = build_course_route(rd)
    from_the_field = build_from_the_field(rd)
    ratings = build_ratings(rd)
    verdict = build_verdict(rd, race_index)
    racer_reviews = build_racer_reviews(rd)
    email_capture = build_email_capture(rd)
    visible_faq = build_visible_faq(rd)
    news = build_news_section(rd)
    training = build_training(rd)
    train_for_race = build_train_for_race(rd)
    logistics_sec = build_logistics_section(rd)
    tire_picks = build_tire_picks(rd)
    similar = build_similar_races(rd, race_index)
    citations_sec = build_citations_section(rd)
    footer = build_footer(rd)
    sticky_cta = build_sticky_cta(rd['name'], rd['slug'])

    # Dynamic TOC — only link to sections that have content
    active = {'course', 'ratings', 'training'}  # always present
    if history:
        active.add('history')
    if course_route:
        active.add('route')
    if from_the_field:
        active.add('from-the-field')
    if verdict:
        active.add('verdict')
    if logistics_sec:
        active.add('logistics')
    if tire_picks:
        active.add('tires')
    if train_for_race:
        active.add('train-for-race')
    if citations_sec:
        active.add('citations')
    toc = build_toc(active)

    # Use external assets if provided, otherwise inline
    if external_assets:
        # Inline @font-face so browser discovers fonts immediately and downloads
        # them in parallel with the external CSS (instead of sequentially).
        # External CSS stays render-blocking (prevents CLS from late style loads).
        fonts_inline = get_font_face_css("/race/assets/fonts")
        critical_css = f'<style>{fonts_inline}</style>'
        css = critical_css + '\n  ' + external_assets['css_tag']
        inline_js = external_assets['js_tag']
    else:
        css = get_page_css()
        inline_js = build_inline_js()

    # Section order
    content_sections = []
    for section in [course_overview, history, pullquote,
                    course_route, from_the_field, ratings, verdict,
                    racer_reviews, email_capture, news, training,
                    train_for_race,
                    logistics_sec, tire_picks, similar, visible_faq,
                    citations_sec]:
        if section:
            content_sections.append(section)

    content = '\n\n  '.join(content_sections)

    # SEO-optimized title and description
    seo_title = build_seo_title(rd)
    seo_description = build_seo_description(rd)

    # Open Graph meta tags
    og_image_url = f"{SITE_BASE_URL}/og/{rd['slug']}.jpg"
    og_tags = f'''<meta property="og:title" content="{esc(seo_title)}">
  <meta property="og:description" content="{esc(seo_description)}">
  <meta property="og:type" content="article">
  <meta property="og:url" content="{esc(canonical_url)}">
  <meta property="og:image" content="{esc(og_image_url)}">
  <meta property="og:image:width" content="1200">
  <meta property="og:image:height" content="630">
  <meta property="og:site_name" content="Road Labs">
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:title" content="{esc(seo_title)}">
  <meta name="twitter:description" content="{esc(seo_description)}">
  <meta name="twitter:image" content="{esc(og_image_url)}">'''

    preload = get_preload_hints()

    return f'''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{esc(seo_title)}</title>
  <meta name="description" content="{esc(seo_description)}">
  <meta name="robots" content="index, follow">
  <link rel="canonical" href="{esc(canonical_url)}">
  <link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'><rect width='32' height='32' fill='%233a2e25'/><text x='16' y='24' text-anchor='middle' font-family='serif' font-size='24' font-weight='700' fill='%239a7e0a'>G</text></svg>">
  <link rel="preconnect" href="https://www.googletagmanager.com" crossorigin>
  <link rel="dns-prefetch" href="https://ridewithgps.com">
  <link rel="dns-prefetch" href="https://api.rss2json.com">
  <link rel="dns-prefetch" href="https://i.ytimg.com">
  {preload}
  {og_tags}
  {jsonld_html}
  {css}
  {get_ga4_head_snippet()}
</head>
<body>

<a href="#course" class="rl-skip-link">Skip to content</a>
<div class="rl-neo-brutalist-page">
  {nav_header}

  {hero}

  {toc}

  {content}

  {footer}
</div>

{sticky_cta}
<button class="rl-back-to-top" id="rl-back-to-top" aria-label="Back to top">&uarr;</button>
{inline_js}

{get_consent_banner_html()}
</body>
</html>'''


# ── Data Loading ───────────────────────────────────────────────

def find_data_file(slug: str, data_dirs: list) -> Optional[Path]:
    """Find a race data file by slug, searching multiple directories."""
    for d in data_dirs:
        d = Path(d)
        # New format: {slug}.json
        candidate = d / f"{slug}.json"
        if candidate.exists():
            return candidate
        # Old format: {slug}-data.json
        candidate = d / f"{slug}-data.json"
        if candidate.exists():
            return candidate
    return None


def load_race_data(filepath: Path) -> dict:
    """Load and normalize race data from a JSON file."""
    with open(filepath, 'r', encoding='utf-8') as f:
        raw = json.load(f)
    rd = normalize_race_data(raw)
    # Store file mtime for accurate dateModified in JSON-LD
    rd['_file_mtime'] = datetime.fromtimestamp(filepath.stat().st_mtime).strftime('%Y-%m-%d')
    return rd


def main():
    parser = argparse.ArgumentParser(
        description="Generate neo-brutalist landing page HTML for gravel race profiles."
    )
    parser.add_argument('slug', nargs='?', help='Race slug (e.g., unbound-200)')
    parser.add_argument('--all', action='store_true', help='Generate pages for all races')
    parser.add_argument('--data-dir', help='Primary data directory (default: auto-detect)')
    parser.add_argument('--output-dir', default=None, help='Output directory (default: wordpress/output/)')
    args = parser.parse_args()

    if not args.slug and not args.all:
        parser.error("Provide a race slug or use --all")

    # Resolve data directories
    script_dir = Path(__file__).parent
    project_root = script_dir.parent

    data_dirs = []
    if args.data_dir:
        data_dirs.append(Path(args.data_dir))
    data_dirs.append(project_root / 'race-data')
    data_dirs.append(project_root / 'data')

    # Output directory
    if args.output_dir:
        output_dir = Path(args.output_dir)
    else:
        output_dir = script_dir / 'output'
    output_dir.mkdir(parents=True, exist_ok=True)

    # Load race index for internal linking + breadcrumbs
    index_path = project_root / 'web' / 'race-index.json'
    race_index = []
    if index_path.exists():
        with open(index_path, 'r', encoding='utf-8') as f:
            race_index = json.load(f)
        print(f"Loaded race index: {len(race_index)} races")

    if args.all:
        # Generate for all races in the primary data directory
        primary = None
        for d in data_dirs:
            d = Path(d)
            if d.exists() and list(d.glob('*.json')):
                primary = d
                break
        if not primary:
            print("ERROR: No data directory found with JSON files.", file=sys.stderr)
            sys.exit(1)

        files = sorted(primary.glob('*.json'))
        total = len(files)
        success = 0
        errors = []

        # Write shared CSS/JS assets
        assets = write_shared_assets(output_dir)

        for i, f in enumerate(files, 1):
            slug = f.stem.replace('-data', '')
            try:
                rd = load_race_data(f)
                page_html = generate_page(rd, race_index, external_assets=assets)
                out = output_dir / f"{slug}.html"
                out.write_text(page_html, encoding='utf-8')
                success += 1
                if i % 50 == 0 or i == total:
                    print(f"  [{i}/{total}] Generated {slug}.html")
            except Exception as e:
                errors.append((slug, str(e)))
                print(f"  ERROR: {slug}: {e}", file=sys.stderr)

        print(f"\nDone. {success}/{total} pages generated in {output_dir}/")
        if errors:
            print(f"\n{len(errors)} errors:")
            for slug, err in errors:
                print(f"  {slug}: {err}")
    else:
        # Single race
        filepath = find_data_file(args.slug, data_dirs)
        if not filepath:
            print(f"ERROR: No data file found for slug '{args.slug}'", file=sys.stderr)
            print(f"  Searched: {', '.join(str(d) for d in data_dirs)}", file=sys.stderr)
            sys.exit(1)

        assets = write_shared_assets(output_dir)
        rd = load_race_data(filepath)
        page_html = generate_page(rd, race_index, external_assets=assets)
        out = output_dir / f"{args.slug}.html"
        out.write_text(page_html, encoding='utf-8')
        print(f"Generated: {out}")
        print(f"  Race: {rd['name']}")
        print(f"  Tier: {rd['tier_label']} (Score: {rd['overall_score']})")
        print(f"  Sections: Course Overview, History, Course, Ratings, Verdict, FAQ, Training, Logistics, Similar Races")


if __name__ == '__main__':
    main()
