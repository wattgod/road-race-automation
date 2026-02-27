#!/usr/bin/env python3
"""
Generate web/race-index.json from race-data/*.json profiles.

Creates a compact searchable index with one entry per event.
"""

import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
RACE_DATA = PROJECT_ROOT / "race-data"
OUTPUT = PROJECT_ROOT / "web" / "race-index.json"
CONFIG = PROJECT_ROOT / "config" / "dimensions.json"

_config = json.loads(CONFIG.read_text())
SCORE_FIELDS = [d["key"] for d in _config["dimensions"]]
RATING_KEY = "fondo_rating"


def _region_from_country(country: str) -> str:
    """Map country to region for filtering."""
    regions = {
        "Western Europe": ["France", "Germany", "Netherlands", "Belgium", "Luxembourg", "Austria", "Switzerland"],
        "Southern Europe": ["Italy", "Spain", "Portugal", "Greece", "Croatia", "Slovenia"],
        "Northern Europe": ["Sweden", "Norway", "Denmark", "Finland", "Iceland", "Estonia", "Latvia", "Lithuania"],
        "UK & Ireland": ["UK", "England", "Scotland", "Wales", "Ireland", "Northern Ireland"],
        "Eastern Europe": ["Poland", "Czech Republic", "Hungary", "Romania", "Bulgaria"],
        "North America": ["USA", "Canada", "Mexico"],
        "South America": ["Brazil", "Argentina", "Chile", "Colombia"],
        "Oceania": ["Australia", "New Zealand"],
        "Africa": ["South Africa", "Kenya", "Morocco", "Ethiopia"],
        "Asia": ["Japan", "China", "Taiwan", "South Korea", "India"],
    }
    for region, countries in regions.items():
        if country in countries:
            return region
    # Check multi-country events
    if "/" in country:
        parts = [c.strip() for c in country.split("/")]
        for p in parts:
            r = _region_from_country(p)
            if r != "Other":
                return r
    return "Other"


def build_index_entry(data: dict) -> dict:
    """Build a compact index entry from a full profile."""
    race = data.get("race", {})
    vitals = race.get("vitals", {})
    rating = race.get(RATING_KEY, {})
    verdict = race.get("final_verdict", {})

    country = vitals.get("country", "")
    location = vitals.get("location", "")

    # Extract month from date string
    month = ""
    date_str = vitals.get("date", "")
    for m in ["January", "February", "March", "April", "May", "June",
              "July", "August", "September", "October", "November", "December"]:
        if m.lower() in date_str.lower():
            month = m
            break

    scores = {f: rating.get(f, 0) for f in SCORE_FIELDS}
    scores["cultural_impact"] = rating.get("cultural_impact", 0)

    return {
        "name": race.get("name", ""),
        "slug": race.get("slug", ""),
        "location": location,
        "country": country,
        "region": _region_from_country(country),
        "month": month,
        "distance_km": vitals.get("distance_km", 0),
        "distance_mi": vitals.get("distance_mi", 0),
        "elevation_m": vitals.get("elevation_m", 0),
        "elevation_ft": vitals.get("elevation_ft", 0),
        "tier": rating.get("tier", 4),
        "overall_score": rating.get("overall_score", 0),
        "scores": scores,
        "tagline": race.get("tagline", verdict.get("one_liner", "")),
        "has_profile": True,
        "profile_url": f"/race/{race.get('slug', '')}/",
        "discipline": rating.get("discipline", "gran_fondo"),
        "lat": vitals.get("lat"),
        "lng": vitals.get("lng"),
        "route_options": vitals.get("route_options", []),
    }


def main():
    profiles = sorted(RACE_DATA.glob("*.json"))
    print(f"Building index from {len(profiles)} profiles...")

    entries = []
    for path in profiles:
        try:
            data = json.loads(path.read_text())
            entry = build_index_entry(data)
            entries.append(entry)
        except (json.JSONDecodeError, KeyError) as e:
            print(f"  SKIP {path.name}: {e}")

    # Sort by tier (asc) then overall_score (desc)
    entries.sort(key=lambda e: (e["tier"], -e["overall_score"]))

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(entries, indent=2, ensure_ascii=False) + "\n")
    print(f"Wrote {len(entries)} entries to {OUTPUT}")

    # Tier distribution
    tier_dist = {1: 0, 2: 0, 3: 0, 4: 0}
    for e in entries:
        tier_dist[e["tier"]] += 1
    print(f"Tier distribution: T1={tier_dist[1]}, T2={tier_dist[2]}, T3={tier_dist[3]}, T4={tier_dist[4]}")


if __name__ == "__main__":
    main()
