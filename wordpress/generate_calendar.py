#!/usr/bin/env python3
"""
Generate the season race calendar pages for SEO.

Creates /race/calendar/{year}/index.html for every season from
FIRST_CALENDAR_YEAR to the rider-facing season (season.season_year()).

A year's page lists only races whose profile has a published date in that
year (vitals.date_specific, read with parse_event_dates — the date the string
leads with). Races without one are not listed for that year: no date is
copied from another edition, shifted forward or estimated (RL-14).

Features:
  - Month-by-month sections with race cards and the edition date
  - Filter by tier and region (JavaScript client-side)
  - Monthly race count summary
  - JSON-LD BreadcrumbList
  - Newsletter sign-up (Roadie's own list, RL-16)

Usage:
    python wordpress/generate_calendar.py
"""

import argparse
import html as html_mod
import json
import sys
from collections import defaultdict
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from brand_tokens import COLORS, get_font_face_css, get_ga4_head_snippet, get_tokens_css, SITE_BASE_URL
from newsletter_signup import NEWSLETTER_TEXT, NEWSLETTER_TITLE, newsletter_css, newsletter_form_html
from shared_header import get_site_header_css, get_site_header_html
from cookie_consent import get_consent_banner_html

from generate_neo_brutalist import parse_event_dates  # noqa: E402
from season import season_year  # noqa: E402

PROJECT_ROOT = Path(__file__).resolve().parent.parent
RACE_DATA_DIR = PROJECT_ROOT / "race-data"
SEASON_YEAR = season_year()  # rider-facing season; rolls over in September
# First season with a calendar page (/race/calendar/2026/ is indexed).
FIRST_CALENDAR_YEAR = 2026

from brand_tokens import TIER_NAMES  # noqa: E402  (one mapping, see brand_tokens)
TIER_COLORS = {
    1: COLORS["primary_brown"],
    2: COLORS["secondary_blue"],
    3: COLORS["steel"],
    4: COLORS["tier_4"],
}

MONTHS = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
]

REGIONS = ["West", "Midwest", "South", "Northeast", "Europe", "North America", "Oceania", "Africa", "Asia", "South America"]


def esc(text) -> str:
    return html_mod.escape(str(text)) if text else ""


def load_edition_dates(race_data_dir: Path = RACE_DATA_DIR) -> dict:
    """slug -> (start ISO, end ISO) for every profile with a parseable date.

    Profiles whose date_specific has no concrete leading date (TBD, status
    notes, cancelled) are absent from the result.
    """
    dates = {}
    for f in sorted(Path(race_data_dir).glob("*.json")):
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        race = data.get("race", data)
        start, end = parse_event_dates((race.get("vitals") or {}).get("date_specific") or "")
        if start:
            dates[race.get("slug") or f.stem] = (start, end or start)
    return dates


def races_for_year(index: list, edition_dates: dict, year: int) -> list:
    """Index entries whose published edition starts in ``year``, with its date."""
    races = []
    for entry in index:
        dates = edition_dates.get(entry.get("slug"))
        if not dates or not dates[0].startswith(f"{year}-"):
            continue
        race = dict(entry)
        race["start_date"], race["end_date"] = dates
        races.append(race)
    return races


def _date_label(start_iso: str, end_iso: str) -> str:
    """"Jun 27", "Jun 27–29" or "Jun 26 – Jul 18" from ISO dates."""
    start = date.fromisoformat(start_iso)
    end = date.fromisoformat(end_iso or start_iso)
    label = f"{MONTHS[start.month - 1][:3]} {start.day}"
    if end == start:
        return label
    if end.month == start.month:
        return f"{label}–{end.day}"
    return f"{label} – {MONTHS[end.month - 1][:3]} {end.day}"


def build_calendar_page(races: list, year: int = None) -> str:
    """Generate one season's calendar page from races dated in that season."""
    year = SEASON_YEAR if year is None else year
    # Group by the month of the published edition date
    by_month = defaultdict(list)
    for r in races:
        by_month[MONTHS[int(r["start_date"][5:7]) - 1]].append(r)

    # Sort each month's races by date, then score
    for month in by_month:
        by_month[month].sort(key=lambda x: (x["start_date"], -x.get("overall_score", 0)))

    # Extract unique regions for filter
    regions = sorted(set(r.get("region", "") for r in races if r.get("region")))

    # Month summary bar
    summary_items = []
    for m in MONTHS:
        count = len(by_month.get(m, []))
        summary_items.append(f'<a href="#month-{m.lower()}" class="rl-cal-summary-item">'
                             f'<span class="rl-cal-summary-month">{m[:3]}</span>'
                             f'<span class="rl-cal-summary-count">{count}</span></a>')
    summary_bar = "\n    ".join(summary_items)

    # Month sections
    month_sections = []
    for m in MONTHS:
        month_races = by_month.get(m, [])
        if not month_races:
            month_sections.append(
                f'<section id="month-{m.lower()}" class="rl-cal-month" data-month="{m}">'
                f'<h2>{m} <span class="rl-cal-month-count">0 races</span></h2>'
                f'<p class="rl-cal-empty">No rated races with a published {m} {year} date.</p></section>'
            )
            continue

        cards = []
        for r in month_races:
            score = r.get("overall_score", 0)
            tier = r.get("tier", 3)
            tier_color = TIER_COLORS.get(tier, COLORS["steel"])
            region = r.get("region", "")

            stat_parts = []
            dist = r.get("distance_mi")
            elev = r.get("elevation_ft")
            if dist:
                stat_parts.append(f"{dist} mi")
            if elev:
                try:
                    stat_parts.append(f"{int(elev):,} ft")
                except (ValueError, TypeError):
                    pass
            stats = " · ".join(stat_parts)

            cards.append(
                f'<a href="/race/{esc(r["slug"])}/" class="rl-cal-card" '
                f'data-tier="{tier}" data-region="{esc(region)}">'
                f'<div class="rl-cal-card-score" style="color:{tier_color}">{score}</div>'
                f'<div class="rl-cal-card-body">'
                f'<div class="rl-cal-card-tier" style="border-color:{tier_color}">T{tier}</div>'
                f'<div class="rl-cal-card-name">{esc(r["name"])}</div>'
                f'<div class="rl-cal-card-date">'
                f'<time datetime="{esc(r["start_date"])}">{esc(_date_label(r["start_date"], r["end_date"]))}</time></div>'
                f'<div class="rl-cal-card-location">{esc(r.get("location",""))}</div>'
                f'<div class="rl-cal-card-stats">{esc(stats)}</div>'
                f'</div></a>'
            )

        cards_html = "\n      ".join(cards)
        month_sections.append(
            f'<section id="month-{m.lower()}" class="rl-cal-month" data-month="{m}">'
            f'<h2>{m} <span class="rl-cal-month-count">{len(month_races)} '
            f'{"race" if len(month_races) == 1 else "races"}</span></h2>'
            f'<div class="rl-cal-grid">{cards_html}</div></section>'
        )

    months_html = "\n\n  ".join(month_sections)

    # Other seasons' calendars
    other_years = " &middot; ".join(
        f'<a href="/race/calendar/{y}/">{y} calendar</a>'
        for y in range(FIRST_CALENDAR_YEAR, SEASON_YEAR + 1) if y != year
    )
    undated_note = (
        f'<p class="rl-cal-note">Races without a published {year} date '
        f'aren&rsquo;t listed. <a href="/road-races/">Search every rated race</a>'
        + (f' &middot; {other_years}' if other_years else '') + '.</p>'
    )

    canonical = f"{SITE_BASE_URL}/race/calendar/{year}/"
    count_label = f"{len(races)} {'Event' if len(races) == 1 else 'Events'}"
    title = f"Road Race Calendar {year} — {count_label} | Roadie Labs"
    description = (
        f"{year} road race calendar: {len(races)} rated events with a published "
        f"{year} date. Filter by tier and region."
    )

    font_face = get_font_face_css()
    tokens = get_tokens_css()

    # Tier filter buttons
    tier_buttons = '<button class="rl-cal-filter-btn active" data-tier="all">All</button>'
    for t in [1, 2, 3, 4]:
        count = sum(1 for r in races if r.get("tier") == t)
        tier_buttons += f'<button class="rl-cal-filter-btn" data-tier="{t}">T{t} ({count})</button>'

    # Region filter
    region_options = '<option value="all">All Regions</option>'
    for reg in regions:
        count = sum(1 for r in races if r.get("region") == reg)
        region_options += f'<option value="{esc(reg)}">{esc(reg)} ({count})</option>'

    breadcrumb_jsonld = json.dumps({
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Home", "item": f"{SITE_BASE_URL}/"},
            {"@type": "ListItem", "position": 2, "name": "Road Races", "item": f"{SITE_BASE_URL}/road-races/"},
            {"@type": "ListItem", "position": 3, "name": f"Calendar {year}", "item": canonical},
        ],
    }, ensure_ascii=False, indent=2)

    return f'''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{esc(title)}</title>
  <meta name="description" content="{esc(description)}">
  <meta name="robots" content="index, follow">
  <link rel="canonical" href="{esc(canonical)}">
  <link rel="icon" href="/favicon.ico" sizes="32x32">
  <link rel="icon" type="image/svg+xml" href="/race/assets/rl-icon.svg?v=siped-1">
  <link rel="icon" type="image/png" sizes="32x32" href="/favicon-32x32.png">
  <link rel="apple-touch-icon" href="/apple-touch-icon.png">
  <meta property="og:title" content="{esc(title)}">
  <meta property="og:description" content="{esc(description)}">
  <meta property="og:type" content="website">
  <meta property="og:url" content="{esc(canonical)}">
  <script type="application/ld+json">
  {breadcrumb_jsonld}
  </script>
  <style>
{font_face}
{tokens}

body {{ margin: 0; background: var(--rl-color-cool-white); }}
*, *::before, *::after {{ border-radius: 0 !important; box-shadow: none !important; }}

.rl-cal-page {{
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 24px;
  font-family: var(--rl-font-data);
  color: var(--rl-color-dark-navy);
}}

{get_site_header_css()}
{newsletter_css()}

.rl-cal-breadcrumb {{ font-size: 11px; color: var(--rl-color-secondary-blue); padding: 12px 0; letter-spacing: 0.5px; }}
.rl-cal-breadcrumb a {{ color: var(--rl-color-secondary-blue); text-decoration: none; }}

.rl-cal-hero {{
  background: var(--rl-color-dark-navy);
  color: var(--rl-color-cool-white);
  padding: 48px 32px;
  margin: 0 -24px;
  text-align: center;
}}
.rl-cal-hero h1 {{ font-family: var(--rl-font-editorial); font-size: 36px; font-weight: 700; margin: 0 0 8px; }}
.rl-cal-hero-sub {{ font-size: 13px; color: var(--rl-color-silver); letter-spacing: 1px; }}

/* Summary bar */
.rl-cal-summary {{
  display: flex;
  border-bottom: 2px solid var(--rl-color-dark-navy);
  overflow-x: auto;
}}
.rl-cal-summary-item {{
  flex: 1;
  text-align: center;
  padding: 10px 4px;
  text-decoration: none;
  color: var(--rl-color-dark-navy);
  border-right: 1px solid var(--rl-color-silver);
  min-width: 50px;
}}
.rl-cal-summary-item:last-child {{ border-right: none; }}
.rl-cal-summary-item:hover {{ background: var(--rl-color-silver); }}
.rl-cal-summary-month {{ display: block; font-size: 10px; font-weight: 700; letter-spacing: 1px; text-transform: uppercase; }}
.rl-cal-summary-count {{ display: block; font-family: var(--rl-font-editorial); font-size: 20px; font-weight: 700; margin-top: 2px; }}

/* Filters */
.rl-cal-filters {{
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px 0;
  border-bottom: 2px solid var(--rl-color-silver);
  flex-wrap: wrap;
}}
.rl-cal-filter-label {{ font-size: 10px; font-weight: 700; letter-spacing: 2px; text-transform: uppercase; color: var(--rl-color-secondary-blue); }}
.rl-cal-filter-btn {{
  padding: 4px 10px;
  font-size: 11px;
  font-weight: 700;
  border: 2px solid var(--rl-color-dark-navy);
  background: transparent;
  color: var(--rl-color-dark-navy);
  cursor: pointer;
  font-family: var(--rl-font-data);
}}
.rl-cal-filter-btn.active {{ background: var(--rl-color-dark-navy); color: var(--rl-color-cool-white); }}
.rl-cal-filter-btn:hover:not(.active) {{ background: var(--rl-color-silver); }}
.rl-cal-filter-select {{
  padding: 4px 8px;
  font-size: 11px;
  border: 2px solid var(--rl-color-dark-navy);
  background: transparent;
  font-family: var(--rl-font-data);
  color: var(--rl-color-dark-navy);
}}

/* Month sections */
.rl-cal-month {{ margin: 32px 0; }}
.rl-cal-month h2 {{
  font-family: var(--rl-font-editorial);
  font-size: 24px;
  font-weight: 700;
  margin: 0 0 16px;
  padding-bottom: 8px;
  border-bottom: 2px solid var(--rl-color-dark-navy);
}}
.rl-cal-month-count {{ font-size: 13px; color: var(--rl-color-secondary-blue); font-weight: 400; }}
.rl-cal-empty {{ font-size: 13px; color: var(--rl-color-secondary-blue); font-style: italic; }}

/* Cards */
.rl-cal-grid {{ display: flex; flex-direction: column; gap: 0; }}
.rl-cal-card {{
  display: flex;
  align-items: stretch;
  border-bottom: 1px solid var(--rl-color-silver);
  text-decoration: none;
  color: inherit;
  transition: background 0.15s;
  padding: 0;
}}
.rl-cal-card:hover {{ background: var(--rl-color-silver); }}
.rl-cal-card-score {{
  display: flex;
  align-items: center;
  justify-content: center;
  min-width: 48px;
  font-family: var(--rl-font-editorial);
  font-size: 18px;
  font-weight: 700;
  padding: 8px;
}}
.rl-cal-card-body {{ flex: 1; padding: 8px 12px; }}
.rl-cal-card-tier {{
  display: inline-block;
  font-size: 9px;
  font-weight: 700;
  letter-spacing: 1px;
  padding: 0 4px;
  border: 1px solid;
  margin-right: 6px;
}}
.rl-cal-card-name {{ font-family: var(--rl-font-editorial); font-size: 14px; font-weight: 700; display: inline; }}
.rl-cal-card-date {{ font-size: 11px; font-weight: 700; letter-spacing: 0.5px; margin-top: 2px; }}
.rl-cal-note {{ font-size: 13px; color: var(--rl-color-secondary-blue); margin: 16px 0; }}
.rl-cal-note a {{ color: inherit; }}
.rl-cal-card-location {{ font-size: 10px; color: var(--rl-color-secondary-blue); text-transform: uppercase; letter-spacing: 0.5px; margin-top: 2px; }}
.rl-cal-card-stats {{ font-size: 10px; color: var(--rl-color-secondary-blue); }}
.rl-cal-card[data-hidden="true"] {{ display: none; }}

/* CTA */
.rl-cal-cta {{
  background: var(--rl-color-dark-navy);
  color: var(--rl-color-cool-white);
  padding: 32px;
  margin: 32px -24px;
  text-align: center;
}}
.rl-cal-cta h2 {{ font-family: var(--rl-font-editorial); font-size: 22px; color: var(--rl-color-cool-white); margin: 0 0 12px; border: none; }}
.rl-cal-cta > p {{ font-size: 14px; line-height: 1.6; margin: 0 0 16px; }}

.rl-cal-footer {{
  padding: 24px 0;
  margin-top: 32px;
  border-top: 4px double var(--rl-color-dark-navy);
  text-align: center;
  font-size: 11px;
  color: var(--rl-color-secondary-blue);
  letter-spacing: 1px;
  text-transform: uppercase;
}}
.rl-cal-footer a {{ color: var(--rl-color-secondary-blue); text-decoration: none; }}

@media (max-width: 768px) {{
  .rl-cal-hero {{ padding: 32px 20px; }}
  .rl-cal-hero h1 {{ font-size: 28px; }}
}}
@media (max-width: 480px) {{
  .rl-cal-page {{ padding: 0 12px; }}
  .rl-cal-hero {{ padding: 24px 12px; margin: 0 -12px; }}
  .rl-cal-hero h1 {{ font-size: 22px; }}
  .rl-cal-cta {{ margin: 32px -12px; padding: 24px 16px; }}
}}
  </style>
  {get_ga4_head_snippet()}
</head>
<body>

<div class="rl-cal-page">

  {get_site_header_html(active="races")}

  <div class="rl-cal-breadcrumb">
    <a href="/">Home</a> &rsaquo; <a href="/road-races/">Road Races</a> &rsaquo; Calendar {year}
  </div>

  <section class="rl-cal-hero">
    <h1>{year} Road Race Calendar</h1>
    <div class="rl-cal-hero-sub">{len(races)} rated {"event" if len(races) == 1 else "events"} with a published {year} date</div>
  </section>

  <div class="rl-cal-summary">
    {summary_bar}
  </div>

  <div class="rl-cal-filters">
    <span class="rl-cal-filter-label">Tier:</span>
    {tier_buttons}
    <span class="rl-cal-filter-label" style="margin-left:12px">Region:</span>
    <select class="rl-cal-filter-select" id="rl-cal-region-filter">
      {region_options}
    </select>
  </div>

  {undated_note}

  {months_html}

  <section class="rl-cal-cta">
    <h2>{esc(NEWSLETTER_TITLE)}</h2>
    <p>{esc(NEWSLETTER_TEXT)}</p>
    {newsletter_form_html("calendar", dark=True)}
  </section>

  <footer class="rl-cal-footer">
    <a href="/">Roadie Labs</a> &middot; {len(races)} races &middot;
    <a href="/road-races/">Search All</a> &middot;
    <a href="/race/methodology/">Methodology</a>
  </footer>

</div>

<script>
(function() {{
  var tierBtns = document.querySelectorAll('.rl-cal-filter-btn');
  var regionSel = document.getElementById('rl-cal-region-filter');
  var cards = document.querySelectorAll('.rl-cal-card');
  var activeTier = 'all';
  var activeRegion = 'all';

  function applyFilters() {{
    cards.forEach(function(card) {{
      var tierMatch = activeTier === 'all' || card.getAttribute('data-tier') === activeTier;
      var regionMatch = activeRegion === 'all' || card.getAttribute('data-region') === activeRegion;
      card.setAttribute('data-hidden', !(tierMatch && regionMatch));
    }});
    // Update month counts
    document.querySelectorAll('.rl-cal-month').forEach(function(section) {{
      var visible = section.querySelectorAll('.rl-cal-card:not([data-hidden="true"])').length;
      var countEl = section.querySelector('.rl-cal-month-count');
      if (countEl) countEl.textContent = visible + (visible === 1 ? ' race' : ' races');
    }});
  }}

  tierBtns.forEach(function(btn) {{
    btn.addEventListener('click', function() {{
      tierBtns.forEach(function(b) {{ b.classList.remove('active'); }});
      btn.classList.add('active');
      activeTier = btn.getAttribute('data-tier');
      applyFilters();
    }});
  }});

  if (regionSel) {{
    regionSel.addEventListener('change', function() {{
      activeRegion = regionSel.value;
      applyFilters();
    }});
  }}
}})();
</script>

{get_consent_banner_html()}
</body>
</html>'''


def main():
    parser = argparse.ArgumentParser(description="Generate season race calendar pages")
    parser.add_argument("--output-dir", default=None)
    args = parser.parse_args()

    output_dir = Path(args.output_dir) if args.output_dir else PROJECT_ROOT / "wordpress" / "output"

    index_path = PROJECT_ROOT / "web" / "race-index.json"
    if not index_path.exists():
        print("ERROR: web/race-index.json not found.", file=sys.stderr)
        sys.exit(1)

    with open(index_path, "r", encoding="utf-8") as f:
        all_races = json.load(f)
    print(f"Loaded {len(all_races)} races")
    edition_dates = load_edition_dates()

    for year in range(FIRST_CALENDAR_YEAR, SEASON_YEAR + 1):
        races = races_for_year(all_races, edition_dates, year)
        page_dir = output_dir / "calendar" / str(year)
        page_dir.mkdir(parents=True, exist_ok=True)
        (page_dir / "index.html").write_text(build_calendar_page(races, year), encoding="utf-8")
        print(f"Generated calendar/{year}/index.html "
              f"({len(races)} of {len(all_races)} races have a published {year} date)")


if __name__ == "__main__":
    main()
