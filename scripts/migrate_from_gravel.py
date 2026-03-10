#!/usr/bin/env python3
"""
Migrate road profiles from gravel-race-automation → road-race-automation schema.

Source: gravel-race-automation/race-data/*.json (discipline="road")
Target: road-race-automation/race-data/*.json (fondo_rating schema)

Usage:
    python3 scripts/migrate_from_gravel.py                    # dry-run (print summary)
    python3 scripts/migrate_from_gravel.py --write             # write migrated profiles
    python3 scripts/migrate_from_gravel.py --write --force     # overwrite existing profiles
    python3 scripts/migrate_from_gravel.py --slug gran-fondo-stelvio  # migrate single profile
"""

import argparse
import copy
import json
import math
import os
import re
import sys
from pathlib import Path

SOURCE_DIR = Path("/Users/mattirowe/Documents/GravelGod/gravel-race-automation/race-data")
TARGET_DIR = Path(__file__).resolve().parent.parent / "race-data"
CONFIG_DIR = Path(__file__).resolve().parent.parent / "config"

# Dimension mapping: source key → target key
DIMENSION_MAP = {
    "length": "distance",
    "elevation": "climbing",
    "technicality": "descent_technicality",
    "climate": "climate_risk",
    "race_quality": "organization",
    "experience": "scenic_experience",
    "community": "community_culture",
    # Unchanged dimensions (identity mapping)
    "altitude": "altitude",
    "logistics": "logistics",
    "prestige": "prestige",
    "field_depth": "field_depth",
    "value": "value",
    "expenses": "expenses",
}

# Source dimension to DROP (gravel-specific, no road equivalent)
DROPPED_DIMENSIONS = {"adventure"}

# Target dimension with no source equivalent (needs derivation)
NEW_DIMENSIONS = {"road_surface"}

# Discipline inference rules
HILLCLIMB_KEYWORDS = [
    "hillclimb", "hill climb", "hill-climb", "summit", "mount ",
    "mt ", "mt. ", "pikes peak", "washington", "ventoux",
]
MULTI_STAGE_KEYWORDS = ["haute route", "stage", "etape", "multi-day", "multi day"]
SPORTIVE_KEYWORDS = ["sportive", "l'eroica", "eroica", "retro", "vintage"]


def infer_discipline(race_data):
    """Infer road-race-automation discipline from source profile."""
    name = race_data.get("name", "").lower()
    slug = race_data.get("slug", "").lower()
    vitals = race_data.get("vitals", {})

    # Distance-based: very short = hillclimb
    distance_mi = _safe_float(vitals.get("distance_mi"))
    if distance_mi and distance_mi < 15:
        return "hillclimb"

    combined = f"{name} {slug}"

    for kw in HILLCLIMB_KEYWORDS:
        if kw in combined:
            return "hillclimb"

    for kw in MULTI_STAGE_KEYWORDS:
        if kw in combined:
            # Check if actually multi-stage (not just "L'Etape" single stage)
            if "haute route" in combined:
                return "multi_stage"
            duration = vitals.get("duration_days")
            if duration and _safe_float(duration) and _safe_float(duration) > 1:
                return "multi_stage"

    for kw in SPORTIVE_KEYWORDS:
        if kw in combined:
            return "sportive"

    # Check for century (100mi events)
    if distance_mi and 95 <= distance_mi <= 105:
        if "century" in combined:
            return "century"

    return "gran_fondo"


def derive_road_surface(race_data):
    """Derive road_surface score (1-5) from terrain data."""
    terrain = race_data.get("terrain", {})

    # Check surface_breakdown if available
    breakdown = terrain.get("surface_breakdown", {})
    if breakdown:
        gravel_pct = _safe_float(breakdown.get("gravel", 0)) or 0
        if gravel_pct == 0:
            return 1
        elif gravel_pct < 20:
            return 2
        elif gravel_pct < 50:
            return 3
        elif gravel_pct < 80:
            return 4
        else:
            return 5

    # Check terrain overview for surface clues
    overview = str(terrain.get("overview", "") or "").lower()
    surface = str(terrain.get("surface", "") or "").lower()
    combined = f"{overview} {surface}"

    if any(w in combined for w in ["cobble", "cobblestone", "strade bianche", "pavé"]):
        return 4
    if any(w in combined for w in ["rough", "deteriorat", "pothole", "broken"]):
        return 3
    if any(w in combined for w in ["mixed", "patch"]):
        return 2

    # Default: paved road events = smooth surface
    return 1


def _safe_float(val):
    """Safely parse a numeric value."""
    if val is None:
        return None
    if isinstance(val, (int, float)):
        return float(val)
    if isinstance(val, str):
        cleaned = re.sub(r"[^\d.\-]", "", val.split()[0] if val.strip() else "")
        try:
            return float(cleaned)
        except (ValueError, IndexError):
            return None
    return None


def _safe_int(val):
    """Safely parse an integer score value."""
    f = _safe_float(val)
    if f is None:
        return None
    return max(1, min(5, round(f)))


def _km_from_mi(mi):
    """Convert miles to km."""
    f = _safe_float(mi)
    return round(f * 1.60934, 1) if f else None


def _m_from_ft(ft):
    """Convert feet to meters."""
    f = _safe_float(ft)
    return round(f * 0.3048) if f else None


def _extract_country(location):
    """Try to extract country from location string."""
    if not location:
        return None
    parts = [p.strip() for p in location.split(",")]
    if len(parts) >= 2:
        last = parts[-1]
        # Common US state abbreviations
        if re.match(r"^[A-Z]{2}$", last) or last in ("USA", "US"):
            return "USA"
        return last
    return None


def _extract_location_badge(location, country=None):
    """Create short location badge from full location."""
    if not location:
        return None
    parts = [p.strip() for p in location.split(",")]
    if len(parts) >= 3:
        return f"{parts[0]}, {parts[-1]}"
    if len(parts) == 2:
        return location
    return location[:50] if len(location) > 50 else location


def _extract_year(text):
    """Extract founding year from text."""
    if not text:
        return None
    match = re.search(r"(?:founded|started|inaugural|first|established|since)\s+(?:in\s+)?(\d{4})", text.lower())
    if match:
        year = int(match.group(1))
        if 1800 <= year <= 2026:
            return year
    # Try standalone 4-digit year in history context
    match = re.search(r"\b(19\d{2}|20[0-2]\d)\b", text)
    if match:
        return int(match.group(1))
    return None


def _restructure_suffering_zones(zones):
    """Convert suffering_zones from [{label, description}] to [string]."""
    if not zones:
        return []
    if isinstance(zones, list):
        result = []
        for z in zones:
            if isinstance(z, str):
                result.append(z)
            elif isinstance(z, dict):
                label = z.get("label", "")
                desc = z.get("description", "")
                if label and desc:
                    result.append(f"{label}: {desc}")
                elif desc:
                    result.append(desc)
                elif label:
                    result.append(label)
        return [s for s in result if s.strip()]
    return []


def _categorize_citation(url, title=""):
    """Categorize a citation URL."""
    url_lower = (url or "").lower()
    title_lower = (title or "").lower()

    if any(d in url_lower for d in [".gov", "wikipedia.org", "strava.com/segments"]):
        return "reference"
    if any(d in url_lower for d in ["youtube.com", "vimeo.com"]):
        return "media"
    if any(w in title_lower for w in ["official", "registration", "entry"]):
        return "official"
    if any(w in url_lower for w in ["blog", "review", "article", "magazine", "rouleur", "cyclingtips", "velonews"]):
        return "editorial"
    if any(w in url_lower for w in ["ridewithgps", "strava", "climbfinder", "pjamm"]):
        return "data"
    # If URL matches race's own domain, likely official
    return "reference"


def calculate_score(dimensions, cultural_impact=0):
    """Calculate overall_score using the standard formula."""
    # Sum of 14 base dimensions + cultural_impact bonus, / 70 * 100
    base_sum = sum(dimensions.values())
    total = base_sum + (cultural_impact or 0)
    return round((total / 70) * 100)


def calculate_tier(score, prestige=None, prestige_override=None):
    """Calculate tier with prestige overrides."""
    # Base tier from score
    if score >= 80:
        tier = 1
    elif score >= 60:
        tier = 2
    elif score >= 45:
        tier = 3
    else:
        tier = 4

    # Prestige overrides
    if prestige == 5:
        if score >= 75:
            tier = 1
        else:
            tier = min(tier, 2)  # cap at T2
    elif prestige == 4:
        tier = max(1, tier - 1)  # promote 1 tier
        if prestige != 5:
            tier = max(tier, 2)  # never into T1 via p4

    return tier


def migrate_profile(source_data):
    """Transform a gravel-race-automation road profile to road-race-automation schema."""
    src = source_data.get("race", source_data)
    vitals = src.get("vitals", {})
    ggr = src.get("gravel_god_rating", {})
    climate_src = src.get("climate", {})
    terrain_src = src.get("terrain", {})
    logistics_src = src.get("logistics", {})
    history_src = src.get("history", {})
    course_src = src.get("course_description", {})
    citations_src = src.get("citations", [])
    biased_src = src.get("biased_opinion", {})
    biased_ratings = src.get("biased_opinion_ratings", {})
    final_src = src.get("final_verdict", {})
    youtube_src = src.get("youtube_data", {})
    guide_vars = src.get("guide_variables", {})

    # === VITALS ===
    distance_mi = _safe_float(vitals.get("distance_mi"))
    distance_km = _safe_float(vitals.get("distance_km")) or _km_from_mi(distance_mi)
    elevation_ft = _safe_float(vitals.get("elevation_ft"))
    elevation_m = _safe_float(vitals.get("elevation_m")) or _m_from_ft(elevation_ft)
    location = vitals.get("location", "")
    country = vitals.get("country") or _extract_country(location)
    location_badge = vitals.get("location_badge") or _extract_location_badge(location, country)

    target_vitals = {
        "distance_km": distance_km,
        "distance_mi": distance_mi,
        "elevation_m": elevation_m,
        "elevation_ft": elevation_ft,
        "location": location,
        "location_badge": location_badge,
        "country": country,
        "date": vitals.get("date", ""),
        "date_specific": vitals.get("date_specific", ""),
        "field_size": vitals.get("field_size") or guide_vars.get("field_size"),
        "start_format": vitals.get("start_format"),  # null if unknown
        "registration": vitals.get("registration") or vitals.get("registration_url"),
        "entry_fee": vitals.get("entry_fee") or vitals.get("registration_cost"),
        "feed_zones": vitals.get("aid_stations") or vitals.get("feed_zones"),
        "cutoff_time": vitals.get("cutoff_time") or vitals.get("time_limit"),
        "lat": _safe_float(vitals.get("lat")),
        "lng": _safe_float(vitals.get("lng")),
        "route_options": _build_route_options(vitals, guide_vars),
    }

    # === CLIMATE ===
    target_climate = {
        "primary": climate_src.get("primary") or _infer_climate_primary(climate_src),
        "description": (
            climate_src.get("description")
            or climate_src.get("overview")
            or climate_src.get("summary")
            or ""
        ),
        "challenges": _build_climate_challenges(climate_src),
    }

    # === TERRAIN ===
    target_terrain = {
        "primary": terrain_src.get("primary") or _infer_terrain_primary(terrain_src),
        "surface": _build_surface_description(terrain_src),
        "technical_rating": _safe_int(terrain_src.get("technical_rating")) or derive_road_surface(src),
        "features": _build_terrain_features(terrain_src, course_src),
    }

    # === FONDO RATING (dimensions) ===
    base_dimensions = {}
    for src_key, tgt_key in DIMENSION_MAP.items():
        val = _safe_int(ggr.get(src_key))
        if val is not None:
            base_dimensions[tgt_key] = val

    # Add road_surface (new dimension)
    base_dimensions["road_surface"] = derive_road_surface(src)

    # cultural_impact (bonus, not in base 14)
    cultural_impact = _safe_int(ggr.get("cultural_impact")) or 0

    # Recalculate score with new dimensions
    overall_score = calculate_score(base_dimensions, cultural_impact)
    prestige_val = base_dimensions.get("prestige")
    tier = calculate_tier(overall_score, prestige_val)
    discipline = infer_discipline(src)

    target_fondo_rating = {
        **base_dimensions,
        "cultural_impact": cultural_impact,
        "overall_score": overall_score,
        "tier": tier,
        "tier_label": f"TIER {tier}",
        "discipline": discipline,
        "prestige_override": ggr.get("prestige_override"),
        "scoring_notes": f"Migrated from gravel-race-automation. Original score: {ggr.get('overall_score')}. "
                         f"adventure dimension dropped, road_surface added. "
                         f"Score recalculated: {overall_score}.",
    }

    # === CLIMB PROFILE (empty placeholder — needs enrichment) ===
    target_climb_profile = {
        "total_climbs": None,
        "hc_climbs": None,
        "cat_1_climbs": None,
        "cat_2_climbs": None,
        "cat_3_climbs": None,
        "key_climbs": [],
        "profile_type": None,
        "king_of_mountain": None,
        "_needs_enrichment": True,
    }

    # === COURSE DESCRIPTION ===
    suffering_zones = (
        _restructure_suffering_zones(course_src.get("suffering_zones"))
        or _restructure_suffering_zones(src.get("suffering_zones"))
    )
    target_course = {
        "character": course_src.get("character", ""),
        "signature_challenge": course_src.get("signature_challenge", ""),
        "suffering_zones": suffering_zones,
    }

    # === LOGISTICS ===
    target_logistics = {
        "airport": _format_airports(logistics_src),
        "lodging_strategy": (
            logistics_src.get("accommodation")
            or logistics_src.get("lodging_strategy")
            or logistics_src.get("lodging")
            or ""
        ),
        "transport": logistics_src.get("transport") or logistics_src.get("overview") or "",
        "food": logistics_src.get("food") or "",
        "official_site": (
            logistics_src.get("official_site")
            or logistics_src.get("website")
            or vitals.get("website")
            or ""
        ),
    }

    # === HISTORY ===
    history_overview = history_src.get("overview") or history_src.get("origin_story") or ""
    target_history = {
        "founded": (
            history_src.get("founded")
            or _safe_int(vitals.get("founded_year") or vitals.get("year_founded") or vitals.get("founded"))
            or _extract_year(history_overview)
        ),
        "origin_story": history_overview,
        "notable_moments": history_src.get("notable_moments", []),
        "reputation": history_src.get("reputation", ""),
    }

    # === BIASED OPINION ===
    target_biased = {
        "verdict": biased_src.get("verdict", ""),
        "summary": biased_src.get("summary") or biased_src.get("overview") or "",
        "strengths": biased_src.get("strengths", []),
        "weaknesses": biased_src.get("weaknesses", []),
        "bottom_line": biased_src.get("bottom_line", ""),
    }

    # === FINAL VERDICT ===
    target_verdict = {
        "score": f"{overall_score}/100",
        "one_liner": (
            final_src.get("one_liner")
            or src.get("tagline", "")
        ),
        "should_you_race": final_src.get("full_verdict") or final_src.get("should_you_race") or "",
        "alternatives": final_src.get("alternatives", ""),
    }

    # === CITATIONS ===
    target_citations = []
    if isinstance(citations_src, list):
        for c in citations_src:
            if isinstance(c, dict):
                url = c.get("url", "")
                title = c.get("title") or c.get("label") or ""
                target_citations.append({
                    "url": url,
                    "category": c.get("category") or _categorize_citation(url, title),
                    "label": title,
                })

    # === ASSEMBLE ===
    target = {
        "race": {
            "name": src.get("name", ""),
            "slug": src.get("slug", ""),
            "display_name": src.get("display_name") or src.get("name", ""),
            "tagline": src.get("tagline", ""),
            "vitals": target_vitals,
            "climate": target_climate,
            "terrain": target_terrain,
            "fondo_rating": target_fondo_rating,
            "climb_profile": target_climb_profile,
            "course_description": target_course,
            "logistics": target_logistics,
            "history": target_history,
            "biased_opinion": target_biased,
            "final_verdict": target_verdict,
            "citations": target_citations,
        }
    }

    # Preserve youtube_data if present
    if youtube_src:
        target["race"]["youtube_data"] = youtube_src

    return target


def _build_route_options(vitals, guide_vars):
    """Build route_options array from various source fields."""
    opts = vitals.get("route_options") or vitals.get("distance_options") or vitals.get("distances")
    if opts:
        if isinstance(opts, list):
            return opts
        if isinstance(opts, str):
            return [opts]
    gv = guide_vars.get("distance_options")
    if gv:
        return [gv] if isinstance(gv, str) else gv
    return []


def _infer_climate_primary(climate):
    """Infer a one-line climate category from source data."""
    overview = (climate.get("overview", "") or "").lower()
    temp = _safe_float(climate.get("average_temp_f"))

    if any(w in overview for w in ["alpine", "mountain"]):
        return "Alpine mountain"
    if any(w in overview for w in ["tropical", "humid", "monsoon"]):
        return "Tropical"
    if any(w in overview for w in ["desert", "arid"]):
        return "Arid desert"
    if any(w in overview for w in ["mediterran"]):
        return "Mediterranean"
    if temp and temp > 85:
        return "Hot"
    if temp and temp < 40:
        return "Cold"
    return "Temperate"


def _build_climate_challenges(climate):
    """Build challenges array from source climate data."""
    challenges = climate.get("challenges", [])
    if isinstance(challenges, list) and challenges:
        return challenges

    result = []
    precip = climate.get("precipitation_chance", "")
    if precip:
        result.append(f"Precipitation: {precip}")

    overview = climate.get("overview", "")
    if overview and not result:
        # Try to extract challenge-like sentences
        for sentence in re.split(r"[.;]", overview):
            s = sentence.strip()
            if s and any(w in s.lower() for w in ["risk", "wind", "rain", "heat", "cold", "storm", "snow", "fog"]):
                result.append(s)

    return result


def _infer_terrain_primary(terrain):
    """Infer terrain primary type from overview."""
    overview = (terrain.get("overview", "") or "").lower()
    if any(w in overview for w in ["mountain", "alpine"]):
        return "Mountain passes"
    if any(w in overview for w in ["rolling", "undulating"]):
        return "Rolling hills"
    if any(w in overview for w in ["flat", "pancake"]):
        return "Flat"
    if any(w in overview for w in ["coastal"]):
        return "Coastal roads"
    if any(w in overview for w in ["urban", "city"]):
        return "Urban"
    return "Mixed terrain"


def _build_surface_description(terrain):
    """Build surface description from terrain data."""
    surface = terrain.get("surface", "")
    if surface:
        return surface

    breakdown = terrain.get("surface_breakdown", {})
    if breakdown:
        paved = _safe_float(breakdown.get("paved", 0)) or 0
        gravel = _safe_float(breakdown.get("gravel", 0)) or 0
        if paved >= 100:
            return "Fully paved"
        if gravel > 0:
            return f"{int(paved)}% paved, {int(gravel)}% gravel/unpaved"

    overview = terrain.get("overview", "")
    if overview:
        return overview

    return "Paved roads"


def _build_terrain_features(terrain, course):
    """Build features list from terrain and course data."""
    features = terrain.get("features", [])
    if isinstance(features, list) and features:
        return features

    result = []
    overview = terrain.get("overview", "")
    if overview:
        for sentence in re.split(r"[.;]", overview):
            s = sentence.strip()
            if s and len(s) > 10:
                result.append(s)

    return result[:5]  # cap at 5


def _format_airports(logistics):
    """Format airports into a single string."""
    airports = logistics.get("airports", [])
    if isinstance(airports, list) and airports:
        parts = []
        for a in airports:
            if isinstance(a, str):
                parts.append(a)
            elif isinstance(a, dict):
                code = a.get("code", "")
                name = a.get("name", "")
                dist = a.get("distance_km") or a.get("distance_miles")
                drive = a.get("drive_time_hours")
                label = f"{code} ({name})" if code and name else code or name
                if dist:
                    label += f", {dist}km" if a.get("distance_km") else f", {dist}mi"
                if drive:
                    label += f", {drive}hr drive"
                parts.append(label)
        return "; ".join(parts)
    airport = logistics.get("airport", "")
    if airport:
        return airport
    return ""


def main():
    parser = argparse.ArgumentParser(description="Migrate road profiles from gravel-race-automation")
    parser.add_argument("--write", action="store_true", help="Write migrated profiles to disk")
    parser.add_argument("--force", action="store_true", help="Overwrite existing profiles")
    parser.add_argument("--slug", help="Migrate a single profile by slug")
    parser.add_argument("--validate", action="store_true", help="Validate migrated profiles against config/dimensions.json")
    args = parser.parse_args()

    if not SOURCE_DIR.exists():
        print(f"ERROR: Source directory not found: {SOURCE_DIR}")
        sys.exit(1)

    # Load config dimensions for validation
    dims_config = None
    dims_path = CONFIG_DIR / "dimensions.json"
    if dims_path.exists():
        with open(dims_path) as f:
            dims_config = json.load(f)

    # Find road profiles in source
    source_profiles = []
    for fname in sorted(os.listdir(SOURCE_DIR)):
        if not fname.endswith(".json"):
            continue
        with open(SOURCE_DIR / fname) as f:
            data = json.load(f)
        race = data.get("race", data)
        ggr = race.get("gravel_god_rating", {})
        disc = ggr.get("discipline", "") or race.get("vitals", {}).get("discipline", "")
        if disc == "road":
            source_profiles.append((fname, data))

    print(f"Found {len(source_profiles)} road profiles in source")

    # Check existing profiles in target
    existing = set(f for f in os.listdir(TARGET_DIR) if f.endswith(".json"))
    print(f"Existing profiles in target: {len(existing)}")

    # Filter
    if args.slug:
        source_profiles = [(f, d) for f, d in source_profiles if f == f"{args.slug}.json"]
        if not source_profiles:
            print(f"ERROR: Profile not found: {args.slug}")
            sys.exit(1)

    # Migrate
    migrated = 0
    skipped = 0
    errors = []
    tier_counts = {1: 0, 2: 0, 3: 0, 4: 0}
    discipline_counts = {}
    score_changes = []

    for fname, data in source_profiles:
        if fname in existing and not args.force:
            skipped += 1
            continue

        try:
            target = migrate_profile(data)
            race = target["race"]
            fondo = race["fondo_rating"]

            tier_counts[fondo["tier"]] = tier_counts.get(fondo["tier"], 0) + 1
            disc = fondo["discipline"]
            discipline_counts[disc] = discipline_counts.get(disc, 0) + 1

            # Track score changes
            orig_score = data.get("race", data).get("gravel_god_rating", {}).get("overall_score")
            new_score = fondo["overall_score"]
            if orig_score and new_score != orig_score:
                score_changes.append((fname, orig_score, new_score))

            if args.write:
                out_path = TARGET_DIR / fname
                with open(out_path, "w") as f:
                    json.dump(target, f, indent=2, ensure_ascii=False)
                    f.write("\n")

            migrated += 1

        except Exception as e:
            errors.append((fname, str(e)))

    # Summary
    print(f"\n{'='*60}")
    print(f"Migration {'COMPLETE' if args.write else 'DRY RUN'}")
    print(f"{'='*60}")
    print(f"Migrated: {migrated}")
    print(f"Skipped (already exist): {skipped}")
    print(f"Errors: {len(errors)}")
    print()

    print("Tier distribution:")
    for t in [1, 2, 3, 4]:
        print(f"  T{t}: {tier_counts.get(t, 0)}")
    print()

    print("Discipline distribution:")
    for d, c in sorted(discipline_counts.items(), key=lambda x: -x[1]):
        print(f"  {d}: {c}")
    print()

    if score_changes:
        print(f"Score changes (top 10 biggest shifts):")
        score_changes.sort(key=lambda x: abs(x[2] - x[1]), reverse=True)
        for fname, orig, new in score_changes[:10]:
            delta = new - orig
            print(f"  {fname}: {orig} → {new} ({'+' if delta > 0 else ''}{delta})")
        if len(score_changes) > 10:
            print(f"  ... and {len(score_changes) - 10} more")
    print()

    if errors:
        print("ERRORS:")
        for fname, err in errors:
            print(f"  {fname}: {err}")
    print()

    if not args.write:
        print("This was a dry run. Use --write to write migrated profiles.")


if __name__ == "__main__":
    main()
