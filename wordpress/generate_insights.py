#!/usr/bin/env python3
"""Generate Roadie Labs' dynamic ``/insights/`` editorial page.

Every reported count is computed from ``web/race-index.json`` at generation
time.  Profile files supply the entry-fee coverage check; the index remains
the canonical source for the published score, tier, country, and month.
"""
from __future__ import annotations

import argparse
import datetime
import html
import json
import re
from collections import Counter
from pathlib import Path
from statistics import mean

from brand_tokens import get_ab_head_snippet, get_ga4_head_snippet, get_preload_hints
from cookie_consent import get_consent_banner_html
from generate_neo_brutalist import (
    SITE_BASE_URL,
    _safe_json_for_script,
    build_inline_js,
    get_page_css,
    write_shared_assets,
)
from shared_footer import get_mega_footer_html
from shared_header import get_site_header_html, get_site_header_js

OUTPUT_DIR = Path(__file__).parent / "output"
PROJECT_ROOT = Path(__file__).resolve().parent.parent
RACE_INDEX = PROJECT_ROOT / "web" / "race-index.json"
RACE_DATA_DIR = PROJECT_ROOT / "race-data"

MONTHS = (
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
)
CRITERIA_PHRASE = "14 base dimensions plus a cultural impact bonus"
PRICE_COVERAGE_MINIMUM = 0.60
US_STATE_COUNTRIES = {
    "Alabama", "Alaska", "Arizona", "Arkansas", "California", "Colorado",
    "Connecticut", "Delaware", "Florida", "Georgia", "Hawaii", "Idaho",
    "Illinois", "Indiana", "Iowa", "Kansas", "Kentucky", "Louisiana",
    "Maine", "Maryland", "Massachusetts", "Michigan", "Minnesota",
    "Mississippi", "Missouri", "Montana", "Nebraska", "Nevada", "New Hampshire",
    "New Jersey", "New Mexico", "New York", "North Carolina", "North Dakota",
    "Ohio", "Oklahoma", "Oregon", "Pennsylvania", "Rhode Island", "South Carolina",
    "South Dakota", "Tennessee", "Texas", "Utah", "Vermont", "Virginia",
    "Washington", "West Virginia", "Wisconsin", "Wyoming",
}
COUNTRY_ALIASES = {
    "USA": "United States", "US": "United States", "England": "United Kingdom",
    "Scotland": "United Kingdom", "Wales": "United Kingdom", "UK": "United Kingdom",
    "Czech Republic": "Czechia", "UAE": "United Arab Emirates",
    "Fukushima Prefecture": "Japan", "Scottish Highlands": "United Kingdom",
    "Northern Portugal": "Portugal",
}
# Profile country fields are editorial input, not an ISO column. This set keeps
# prose accidentally captured during migration (for example, a zip code or a
# route note) out of the country chart while retaining countries in the catalog.
KNOWN_COUNTRIES = frozenset({
    "Argentina", "Australia", "Austria", "Belgium", "Brazil", "Bulgaria", "Canada",
    "Chile", "China", "Colombia", "Costa Rica", "Croatia", "Cuba", "Cyprus", "Czechia",
    "Denmark", "Dominican Republic", "Ecuador", "Estonia", "Finland", "France", "Germany",
    "Greece", "Guadeloupe", "Hungary", "India", "Indonesia", "Ireland", "Israel", "Italy",
    "Japan", "Jordan", "Kazakhstan", "Luxembourg", "Malaysia", "Mexico", "Morocco",
    "Netherlands", "New Zealand", "Norway", "Oman", "Panama", "Peru", "Philippines", "Poland",
    "Portugal", "Puerto Rico", "Romania", "Serbia", "Singapore", "Slovakia", "Slovenia",
    "South Africa", "South Korea", "Spain", "Sweden", "Switzerland", "Taiwan", "Thailand",
    "The Bahamas", "Turkey", "United Arab Emirates", "United Kingdom", "United States", "Uruguay",
    "Venezuela", "Vietnam",
})


def esc(value: object) -> str:
    return html.escape(str(value)) if value is not None else ""


def load_race_index() -> list[dict]:
    """Load the published race index, failing clearly if it is missing."""
    if not RACE_INDEX.exists():
        raise RuntimeError("race-index.json is required; run python3 scripts/generate_index.py first")
    data = json.loads(RACE_INDEX.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise RuntimeError("race-index.json must contain a list of races")
    return data


def load_profile(slug: str) -> dict:
    """Load a profile's race object, returning an empty object when unavailable."""
    path = RACE_DATA_DIR / f"{slug}.json"
    if not path.exists():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload.get("race", {})


def normalise_country(country: object, location: object = None) -> str | None:
    """Resolve known aliases and obvious state-as-country migration artifacts."""
    for source in (country, location):
        if not isinstance(source, str) or not source.strip():
            continue
        cleaned = source.strip()
        if cleaned in US_STATE_COUNTRIES:
            return "United States"
        if cleaned in COUNTRY_ALIASES:
            return COUNTRY_ALIASES[cleaned]
        if cleaned in KNOWN_COUNTRIES:
            return cleaned
        # Recover a country from a location note such as "France (Mont Ventoux
        # summit finish)". Longest first avoids United States/US overlap.
        for marker, canonical in sorted(
            {**{name: name for name in KNOWN_COUNTRIES}, **COUNTRY_ALIASES}.items(),
            key=lambda item: len(item[0]), reverse=True,
        ):
            if re.search(rf"(?<![A-Za-z]){re.escape(marker)}(?![A-Za-z])", cleaned, re.IGNORECASE):
                return canonical
        if any(re.search(rf"(?<![A-Za-z]){re.escape(state)}(?![A-Za-z])", cleaned) for state in US_STATE_COUNTRIES):
            return "United States"
    return None


def enrich_races(index: list[dict]) -> list[dict]:
    """Attach only profile facts needed for the fee-data quality check."""
    races = []
    for item in index:
        race = dict(item)
        profile = load_profile(str(race.get("slug", "")))
        vitals = profile.get("vitals", {}) if isinstance(profile, dict) else {}
        race["entry_fee"] = vitals.get("entry_fee")
        race["country_name"] = normalise_country(
            vitals.get("country") or race.get("country"), race.get("location")
        )
        races.append(race)
    return races


def _bar_rows(items: list[tuple[str, int]], maximum: int, kind: str, *, suffix: str = "") -> str:
    return "\n".join(
        f'''<div class="rl-ins-row">
  <span class="rl-ins-row-label">{esc(label)}</span>
  <div class="rl-ins-bar-track"><span class="rl-ins-bar rl-ins-bar--{esc(kind)}" style="width:{count / maximum * 100:.2f}%"></span></div>
  <span class="rl-ins-row-value">{count}{suffix}</span>
</div>'''
        for label, count in items
    )


def compute_stats(races: list[dict]) -> dict:
    """Return all page facts from the current index/profile corpus."""
    total = len(races)
    tiers = Counter(int(r["tier"]) for r in races if str(r.get("tier", "")).isdigit())
    countries = Counter(r["country_name"] for r in races if r.get("country_name"))
    months = Counter(r["month"] for r in races if r.get("month") in MONTHS)
    entry_fee_count = sum(bool(r.get("entry_fee")) for r in races)
    score_values = [float(r["overall_score"]) for r in races if isinstance(r.get("overall_score"), (int, float))]
    prestige_values = [
        r for r in races
        if isinstance(r.get("overall_score"), (int, float))
        and isinstance((r.get("scores") or {}).get("prestige"), (int, float))
    ]
    overachiever_pool = sorted(
        (r for r in prestige_values if r["overall_score"] >= 60 and r["scores"]["prestige"] <= 3),
        key=lambda r: (-r["overall_score"], r["scores"]["prestige"], r.get("name", "")),
    )
    overachievers = overachiever_pool[:8]
    top_country, top_country_count = countries.most_common(1)[0] if countries else ("Unspecified", 0)
    peak_month, peak_count = max(months.items(), key=lambda item: item[1]) if months else ("Unspecified", 0)
    month_items = [(month, months[month]) for month in MONTHS]
    country_items = countries.most_common(10)
    return {
        "total_races": total,
        "tier_counts": {tier: tiers[tier] for tier in range(1, 5)},
        "country_counts": countries,
        "country_items": country_items,
        "country_count": len(countries),
        "top_country": top_country,
        "top_country_count": top_country_count,
        "international_count": total - countries.get("United States", 0),
        "month_counts": {month: months[month] for month in MONTHS},
        "month_items": month_items,
        "dated_count": sum(months.values()),
        "peak_month": peak_month,
        "peak_count": peak_count,
        "entry_fee_count": entry_fee_count,
        "entry_fee_coverage": entry_fee_count / total if total else 0,
        # Profiles store free-text, multi-currency fees. There is deliberately
        # no invented FX conversion or pseudo-precise price/score correlation.
        "normalised_price_count": 0,
        "score_average": mean(score_values) if score_values else 0,
        "overachievers": overachievers,
        "overachiever_total": len(overachiever_pool),
    }


def build_nav() -> str:
    return get_site_header_html() + f'''<div class="rl-ins-breadcrumb">
  <a href="{SITE_BASE_URL}/">Home</a><span aria-hidden="true">&rsaquo;</span><span>Insights</span>
</div>'''


def build_hero(stats: dict) -> str:
    return f'''<section class="rl-ins-hero" id="hero">
  <p class="rl-ins-kicker">ROADIE LABS / FIELD NOTES</p>
  <h1>The State of Road Racing</h1>
  <p class="rl-ins-dek">{stats["total_races"]} races. {CRITERIA_PHRASE.capitalize()}. The catalogue, with its hands in its pockets.</p>
  <div class="rl-ins-metrics">
    <div><strong>{stats["total_races"]}</strong><span>races rated</span></div>
    <div><strong>{stats["country_count"]}</strong><span>countries represented</span></div>
    <div><strong>{stats["dated_count"]}</strong><span>calendar months dated</span></div>
    <div><strong>{stats["score_average"]:.0f}</strong><span>mean score / 100</span></div>
  </div>
</section>'''


def build_tier_section(stats: dict) -> str:
    counts = stats["tier_counts"]
    maximum = max(counts.values()) or 1
    rows = _bar_rows([(f"Tier {tier}", counts[tier]) for tier in range(1, 5)], maximum, "tier")
    return f'''<section class="rl-ins-section" id="tier-breakdown">
  <p class="rl-ins-section-number">01 / DISTRIBUTION</p>
  <h2>The score has a shape.</h2>
  <p>Tier 1 contains {counts[1]} of {stats["total_races"]} races. Tier 2 holds {counts[2]}; the middle of the catalogue is doing most of the work. The rating is not a popularity contest with better typography.</p>
  <div class="rl-ins-chart" role="img" aria-label="Road race counts by tier">{rows}</div>
</section>'''


def build_geography_section(stats: dict) -> str:
    items = stats["country_items"]
    maximum = max((count for _, count in items), default=1)
    rows = _bar_rows(items, maximum, "country")
    unknown = stats["total_races"] - sum(stats["country_counts"].values())
    unknown_note = f" {unknown} profiles do not yet resolve to a country." if unknown else ""
    return f'''<section class="rl-ins-section rl-ins-section--alt" id="geography">
  <p class="rl-ins-section-number">02 / GEOGRAPHY</p>
  <h2>Road racing is not a state map.</h2>
  <p>{stats["international_count"]} of {stats["total_races"]} catalogued races sit outside the United States. {esc(stats["top_country"])} leads with {stats["top_country_count"]}, but the useful unit here is the country, not the state. The chart lists the ten deepest country files.{unknown_note}</p>
  <div class="rl-ins-chart" role="img" aria-label="Top countries by number of rated road races">{rows}</div>
</section>'''


def build_calendar_section(stats: dict) -> str:
    maximum = max(stats["month_counts"].values()) or 1
    cols = "\n".join(
        f'''<div class="rl-ins-month">
  <span class="rl-ins-month-count">{count}</span>
  <span class="rl-ins-month-bar" style="height:{count / maximum * 100:.2f}%"></span>
  <span class="rl-ins-month-label">{month[:3]}</span>
</div>'''
        for month, count in stats["month_items"]
    )
    undated = stats["total_races"] - stats["dated_count"]
    return f'''<section class="rl-ins-section" id="calendar-crunch">
  <p class="rl-ins-section-number">03 / CALENDAR</p>
  <h2>The calendar has a bottleneck.</h2>
  <p>{esc(stats["peak_month"])} carries {stats["peak_count"]} races, the highest monthly total in the index. That makes planning less about finding an event and more about declining several at once. {undated} profiles have not resolved to a calendar month, so they are kept out of the chart rather than assigned a season by vibes.</p>
  <div class="rl-ins-month-chart" role="img" aria-label="Rated road races by calendar month">{cols}</div>
</section>'''


def build_price_section(stats: dict) -> str:
    present = stats["entry_fee_count"]
    missing = stats["total_races"] - present
    maximum = max(present, missing, 1)
    rows = _bar_rows([("Entry fee recorded", present), ("No entry fee recorded", missing)], maximum, "price")
    coverage = stats["entry_fee_coverage"] * 100
    if stats["normalised_price_count"] / stats["total_races"] >= PRICE_COVERAGE_MINIMUM:
        # Reserved for a future schema field such as entry_fee_usd. Keeping the
        # branch makes the eligibility rule explicit without fabricating FX data.
        narrative = "A normalized entry-cost analysis is available."
    else:
        narrative = "The source records free-text fees in several currencies and no normalized currency field. A price-versus-score correlation would be numerically tidy and substantively wrong, so it is not published."
    return f'''<section class="rl-ins-section rl-ins-section--alt" id="entry-cost">
  <p class="rl-ins-section-number">04 / ENTRY COST</p>
  <h2>The price comparison is not ready.</h2>
  <p>An entry fee appears in {present} of {stats["total_races"]} profiles ({coverage:.1f}%). {narrative}</p>
  <div class="rl-ins-chart" role="img" aria-label="Road race entry-fee data coverage">{rows}</div>
</section>'''


def build_overachiever_section(stats: dict) -> str:
    races = stats["overachievers"]
    rows = "\n".join(
        f'''<li class="rl-ins-overachiever">
  <a href="{SITE_BASE_URL}/race/{esc(r.get("slug", ""))}/">{esc(r.get("name", ""))}</a>
  <span>score {r["overall_score"]} / prestige {r["scores"]["prestige"]}</span>
</li>'''
        for r in races
    ) or '<li class="rl-ins-overachiever">No current profiles meet the threshold.</li>'
    return f'''<section class="rl-ins-section" id="overachievers">
  <p class="rl-ins-section-number">05 / OUTLIERS</p>
  <h2>Punching above their weight.</h2>
  <p>{stats["overachiever_total"]} races score at least 60 overall while carrying a prestige score of 3 or lower. The eight highest-scoring are below. That is not a claim that they are undiscovered; it is a reminder that a famous name is only one line in the rubric.</p>
  <ol class="rl-ins-overachievers">{rows}</ol>
</section>'''


def build_closing(stats: dict) -> str:
    return f'''<section class="rl-ins-closing" id="method">
  <p class="rl-ins-kicker">THE METHOD</p>
  <h2>Useful data begins with a rubric.</h2>
  <p>Every number on this page is regenerated from the current Roadie Labs race index and profiles. Scores use {CRITERIA_PHRASE}; the cultural impact bonus is additive while the denominator remains 70.</p>
  <a href="{SITE_BASE_URL}/race/methodology/">READ THE METHODOLOGY &rarr;</a>
</section>'''


def build_insights_css() -> str:
    """Page CSS. Colors are exclusively Roadie Labs custom properties."""
    return '''<style>
.rl-ins-breadcrumb,.rl-ins-hero,.rl-ins-section,.rl-ins-closing{max-width:960px;margin:0 auto;padding-left:var(--rl-spacing-xl);padding-right:var(--rl-spacing-xl)}
.rl-ins-breadcrumb{padding-top:var(--rl-spacing-md);padding-bottom:var(--rl-spacing-md);font-family:var(--rl-font-data);font-size:var(--rl-font-size-2xs);letter-spacing:var(--rl-letter-spacing-wide);color:var(--rl-color-secondary-blue)}
.rl-ins-breadcrumb a{color:inherit}.rl-ins-breadcrumb span{margin-left:var(--rl-spacing-xs)}
.rl-ins-hero{padding-top:var(--rl-spacing-3xl);padding-bottom:var(--rl-spacing-3xl);border-bottom:var(--rl-border-double)}
.rl-ins-kicker,.rl-ins-section-number{font-family:var(--rl-font-data);font-size:var(--rl-font-size-2xs);font-weight:var(--rl-font-weight-bold);letter-spacing:var(--rl-letter-spacing-ultra-wide);color:var(--rl-color-secondary-blue);margin:0 0 var(--rl-spacing-sm)}
.rl-ins-hero h1,.rl-ins-section h2,.rl-ins-closing h2{font-family:var(--rl-font-editorial);font-weight:var(--rl-font-weight-semibold);line-height:var(--rl-line-height-tight);color:var(--rl-color-dark-navy);margin:0}
.rl-ins-hero h1{font-size:clamp(42px,7vw,var(--rl-font-size-5xl));max-width:15ch}.rl-ins-dek,.rl-ins-section>p:not(.rl-ins-section-number),.rl-ins-closing p{font-family:var(--rl-font-editorial);font-size:var(--rl-font-size-md);line-height:var(--rl-line-height-prose);max-width:64ch;color:var(--rl-color-signal-red)}
.rl-ins-metrics{display:grid;grid-template-columns:repeat(4,1fr);border-top:var(--rl-border-subtle);border-bottom:var(--rl-border-subtle);margin-top:var(--rl-spacing-2xl)}
.rl-ins-metrics div{padding:var(--rl-spacing-md);border-right:1px solid var(--rl-color-silver)}.rl-ins-metrics div:last-child{border:0}.rl-ins-metrics strong,.rl-ins-metrics span{display:block}.rl-ins-metrics strong{font-family:var(--rl-font-editorial);font-size:var(--rl-font-size-2xl);line-height:1;color:var(--rl-color-dark-navy)}.rl-ins-metrics span{margin-top:var(--rl-spacing-xs);font-family:var(--rl-font-data);font-size:var(--rl-font-size-2xs);letter-spacing:var(--rl-letter-spacing-wide);text-transform:uppercase;color:var(--rl-color-secondary-blue)}
.rl-ins-section{padding-top:var(--rl-spacing-3xl);padding-bottom:var(--rl-spacing-3xl);border-bottom:var(--rl-border-subtle)}.rl-ins-section--alt{max-width:none;background:var(--rl-color-silver);padding-left:max(var(--rl-spacing-xl),calc((100% - 960px)/2 + var(--rl-spacing-xl)));padding-right:max(var(--rl-spacing-xl),calc((100% - 960px)/2 + var(--rl-spacing-xl)))}
.rl-ins-section h2,.rl-ins-closing h2{font-size:var(--rl-font-size-3xl)}.rl-ins-chart{margin-top:var(--rl-spacing-xl);border-top:var(--rl-border-subtle)}.rl-ins-row{display:grid;grid-template-columns:minmax(130px,1.2fr) minmax(80px,4fr) 48px;gap:var(--rl-spacing-sm);align-items:center;padding:var(--rl-spacing-sm) 0;border-bottom:1px solid var(--rl-color-light-steel)}.rl-ins-row-label,.rl-ins-row-value{font-family:var(--rl-font-data);font-size:var(--rl-font-size-xs);color:var(--rl-color-dark-navy)}.rl-ins-row-value{text-align:right}.rl-ins-bar-track{height:14px;background:var(--rl-color-cool-white);border:1px solid var(--rl-color-dark-navy)}.rl-ins-bar{display:block;height:100%;background:var(--rl-color-dark-navy)}.rl-ins-bar--country{background:var(--rl-color-signal-red)}.rl-ins-bar--price{background:var(--rl-color-secondary-blue)}
.rl-ins-month-chart{height:260px;display:grid;grid-template-columns:repeat(12,1fr);gap:var(--rl-spacing-xs);align-items:end;border-bottom:var(--rl-border-subtle);padding-top:var(--rl-spacing-xl)}.rl-ins-month{height:100%;display:grid;grid-template-rows:auto 1fr auto;gap:var(--rl-spacing-xs);text-align:center}.rl-ins-month-count,.rl-ins-month-label{font-family:var(--rl-font-data);font-size:var(--rl-font-size-2xs);color:var(--rl-color-secondary-blue)}.rl-ins-month-bar{align-self:end;display:block;min-height:2px;background:var(--rl-color-dark-navy);border:1px solid var(--rl-color-dark-navy)}
.rl-ins-overachievers{list-style:none;margin:var(--rl-spacing-xl) 0 0;padding:0;border-top:var(--rl-border-subtle)}.rl-ins-overachiever{display:flex;justify-content:space-between;gap:var(--rl-spacing-md);padding:var(--rl-spacing-md) 0;border-bottom:1px solid var(--rl-color-light-steel);font-family:var(--rl-font-data);font-size:var(--rl-font-size-xs)}.rl-ins-overachiever a{color:var(--rl-color-dark-navy);font-weight:var(--rl-font-weight-bold)}.rl-ins-overachiever span{color:var(--rl-color-secondary-blue);white-space:nowrap}
.rl-ins-closing{padding-top:var(--rl-spacing-3xl);padding-bottom:var(--rl-spacing-3xl)}.rl-ins-closing a{display:inline-block;margin-top:var(--rl-spacing-md);padding:var(--rl-spacing-sm) var(--rl-spacing-md);border:var(--rl-border-subtle);font-family:var(--rl-font-data);font-size:var(--rl-font-size-xs);font-weight:var(--rl-font-weight-bold);letter-spacing:var(--rl-letter-spacing-wide);text-decoration:none;color:var(--rl-color-dark-navy)}
@media (max-width:600px){.rl-ins-breadcrumb,.rl-ins-hero,.rl-ins-section,.rl-ins-closing{padding-left:var(--rl-spacing-md);padding-right:var(--rl-spacing-md)}.rl-ins-section--alt{padding-left:var(--rl-spacing-md);padding-right:var(--rl-spacing-md)}.rl-ins-metrics{grid-template-columns:repeat(2,1fr)}.rl-ins-metrics div:nth-child(2){border-right:0}.rl-ins-metrics div:nth-child(-n+2){border-bottom:1px solid var(--rl-color-silver)}.rl-ins-section h2,.rl-ins-closing h2{font-size:var(--rl-font-size-2xl)}.rl-ins-row{grid-template-columns:100px minmax(60px,1fr) 38px}.rl-ins-row-label,.rl-ins-row-value,.rl-ins-overachiever{font-size:var(--rl-font-size-2xs)}.rl-ins-overachiever{align-items:flex-start;flex-direction:column;gap:var(--rl-spacing-xs)}.rl-ins-month-chart{height:210px;gap:4px}}
</style>'''


def build_jsonld(stats: dict) -> str:
    payload = {
        "@context": "https://schema.org",
        "@type": "Article",
        "headline": f"The State of Road Racing: {stats['total_races']} Races Analyzed",
        "description": f"Dynamic Roadie Labs analysis of {stats['total_races']} rated road races across {stats['country_count']} countries.",
        "author": {"@type": "Organization", "name": "Roadie Labs", "url": SITE_BASE_URL},
        "publisher": {"@type": "Organization", "name": "Roadie Labs", "url": SITE_BASE_URL},
        "datePublished": datetime.date.today().isoformat(),
        "dateModified": datetime.date.today().isoformat(),
        "url": f"{SITE_BASE_URL}/insights/",
    }
    return f'<script type="application/ld+json">{_safe_json_for_script(payload, separators=(",", ":"))}</script>'


def generate_insights_page(external_assets: dict | None = None) -> str:
    races = enrich_races(load_race_index())
    stats = compute_stats(races)
    canonical_url = f"{SITE_BASE_URL}/insights/"
    page_css = external_assets["css_tag"] if external_assets else get_page_css()
    inline_js = external_assets["js_tag"] if external_assets else build_inline_js()
    meta_desc = f"Dynamic Roadie Labs analysis of {stats['total_races']} rated road races across {stats['country_count']} countries: tiers, geography, calendar, and the races outriding their prestige."
    sections = "\n".join((
        build_hero(stats), build_tier_section(stats), build_geography_section(stats),
        build_calendar_section(stats), build_price_section(stats), build_overachiever_section(stats), build_closing(stats),
    ))
    return f'''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>The State of Road Racing: {stats['total_races']} Races Analyzed | Roadie Labs</title>
  <meta name="description" content="{esc(meta_desc)}">
  <meta name="robots" content="index, follow">
  <link rel="canonical" href="{canonical_url}">
  <link rel="preconnect" href="https://www.googletagmanager.com" crossorigin>
  {get_preload_hints()}
  <meta property="og:title" content="The State of Road Racing | Roadie Labs">
  <meta property="og:description" content="{esc(meta_desc)}">
  <meta property="og:type" content="article">
  <meta property="og:url" content="{canonical_url}">
  <meta property="og:site_name" content="Roadie Labs">
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:title" content="The State of Road Racing | Roadie Labs">
  <meta name="twitter:description" content="{esc(meta_desc)}">
  {build_jsonld(stats)}
  {page_css}
  {build_insights_css()}
  {get_ga4_head_snippet()}
  {get_ab_head_snippet()}
</head>
<body>
<a href="#hero" class="rl-skip-link">Skip to content</a>
<div class="rl-neo-brutalist-page">
  {build_nav()}
  {sections}
  {get_mega_footer_html()}
</div>
{inline_js}
<script>{get_site_header_js()}</script>
{get_consent_banner_html()}
</body>
</html>'''


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate the Roadie Labs insights page")
    parser.add_argument("--output-dir", default=str(OUTPUT_DIR), help="Output directory")
    args = parser.parse_args()
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    assets = write_shared_assets(output_dir)
    output_file = output_dir / "insights.html"
    output_file.write_text(generate_insights_page(external_assets=assets), encoding="utf-8")
    print(f"Generated {output_file} ({output_file.stat().st_size:,} bytes)")


if __name__ == "__main__":
    main()
