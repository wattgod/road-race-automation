"""Road race-pack previews must stay road-specific."""

import json
import sys
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from generate_race_pack_previews import (  # noqa: E402
    calculate_category_scores,
    generate_preview,
    generate_race_overlay,
    generate_ultra_nutrition,
    generate_workout_context,
    get_top_categories,
    repair_safety_overlays,
    repair_ultra_nutrition_overlays,
)


def test_technical_road_demands_never_emit_gravel_category():
    demands = {
        "technical": 10,
        "race_specificity": 10,
    }

    scores = calculate_category_scores(demands)
    categories = [row["category"] for row in get_top_categories(demands)]

    assert "Road_Specific" in scores
    assert "Road_Specific" in categories
    assert "Gravel_Specific" not in scores
    assert "Gravel_Specific" not in categories


def test_generated_road_preview_uses_road_specific_context():
    preview = generate_preview({
        "race": {
            "name": "Example Road Race",
            "slug": "example-road-race",
            "vitals": {
                "distance_mi": 100,
                "elevation_ft": 5000,
                "date": "2027: May 1",
            },
            "terrain": {
                "primary": "technical rolling roads",
                "technical_rating": 5,
                "features": ["tight corners", "short climbs"],
            },
            "fondo_rating": {
                "distance": 4,
                "climbing": 4,
                "descent_technicality": 5,
                "climate_risk": 3,
                "organization": 4,
                "scenic_experience": 4,
                "community_culture": 4,
                "altitude": 2,
                "logistics": 3,
                "prestige": 4,
                "field_depth": 4,
                "value": 3,
                "expenses": 3,
                "road_surface": 4,
                "cultural_impact": 3,
                "overall_score": 70,
                "tier": 2,
            },
            "climate": {"challenges": []},
        }
    })

    road_category = next(
        row for row in preview["top_categories"]
        if row["category"] == "Road_Specific"
    )

    assert "out of corners" in road_category["workout_context"]
    assert "rough stuff" not in road_category["workout_context"]
    assert "Gravel_Specific" not in str(preview)


def test_high_altitude_overlay_avoids_unverified_medical_prescriptions():
    race = {
        "display_name": "Taiwan KOM Challenge",
        "vitals": {"distance_mi": 65.2, "elevation_ft": 11155},
        "terrain": {"primary": "paved mountain road"},
        "climate": {
            "challenges": ["High altitude changes pacing and recovery demands"],
        },
    }

    overlay = generate_race_overlay(race, {"altitude": 10, "technical": 2})

    assert "5\u201315%" not in overlay["altitude"]
    assert "fluid loss" not in overlay["altitude"]
    assert "Increase iron" not in overlay["altitude"]
    assert "clinician-guided" in overlay["altitude"]


def test_high_climb_context_does_not_invent_repeated_climbs_or_walking():
    race = {
        "display_name": "Taiwan KOM Challenge",
        "vitals": {"distance_mi": 65.2, "elevation_ft": 11155},
        "terrain": {"primary": "paved mountain road"},
    }

    vo2 = generate_workout_context(race, {}, "VO2max")
    threshold = generate_workout_context(race, {}, "TT_Threshold")

    assert "fifth climb" not in vo2
    assert "repeated surges" not in vo2
    assert "walk" not in threshold
    assert "sustained" in threshold.lower()


def test_ultra_nutrition_avoids_fixed_total_burn_and_short_event_target():
    race = {
        "display_name": "Example Multi-Day Ultra",
        "vitals": {"distance_mi": 994.2, "elevation_ft": 45932},
        "terrain": {"primary": "mixed lowland and mountain roads"},
    }

    nutrition = generate_race_overlay(race, {})["nutrition"]

    assert "8,000" not in nutrition
    assert "12,000" not in nutrition
    assert "80\u2013100g" not in nutrition
    assert "resupply plan" in nutrition
    assert "sleep strategy" in nutrition
    assert "fixed total-calorie estimate" in nutrition


def test_long_one_day_nutrition_does_not_claim_multi_day_or_sleep_strategy():
    nutrition = generate_ultra_nutrition(160)

    assert "multi-day" not in nutrition
    assert "sleep strategy" not in nutrition
    assert "expected duration" in nutrition
    assert "confirmed feed or commercial resupply options" in nutrition


def test_repair_ultra_nutrition_overlays_updates_only_stale_long_pack(tmp_path):
    stale = {
        "distance_mi": 160,
        "race_overlay": {
            "nutrition": (
                "Ultra-distance fueling for 160 miles: 80\u2013100g carbs/hour "
                "from mile 1 \u2014 160 miles burns 8,000\u201312,000+ calories."
            )
        },
        "generated_at": "2026-08-05",
    }
    current = {
        "distance_mi": 100,
        "race_overlay": {"nutrition": "Existing century guidance."},
        "generated_at": "2026-08-05",
    }
    stale_path = tmp_path / "stale.json"
    current_path = tmp_path / "current.json"
    stale_path.write_text(json.dumps(stale))
    current_path.write_text(json.dumps(current))

    repaired = repair_ultra_nutrition_overlays(str(tmp_path))

    assert repaired == 1
    assert "expected duration" in json.loads(stale_path.read_text())["race_overlay"]["nutrition"]
    assert json.loads(current_path.read_text()) == current


def test_long_gran_fondo_copy_avoids_false_depletion_and_stale_month():
    race = {
        "display_name": "Example Alpine Gran Fondo",
        "vitals": {
            "distance_mi": 87.07,
            "elevation_ft": 9255,
            "date": "May",
        },
        "terrain": {
            "primary": (
                "Maritime Alps roads with three major climbs and a summit gravel sector"
            )
        },
    }

    durability = generate_workout_context(race, {}, "Durability")
    simulation = generate_workout_context(race, {}, "Race_Simulation")
    road = generate_workout_context(race, {}, "Road_Specific")
    nutrition = generate_race_overlay(race, {})["nutrition"]

    assert "glycogen is gone" not in durability
    assert "final third" in durability
    assert "before race day" in simulation
    assert "before May" not in simulation
    assert "Road-specific control matters" in road
    assert "and a rewards" not in road
    assert "roads with three major climbs rewards" not in road
    assert "Bonking" not in nutrition
    assert "60\u201380g" not in nutrition
    assert "feed-zone locations" in nutrition


def test_preview_overlays_avoid_fixed_heat_resupply_and_tire_claims():
    race = {
        "display_name": "Example Hot Technical Race",
        "vitals": {"distance_mi": 65, "elevation_ft": 3000, "date": "July"},
        "terrain": {
            "primary": "technical paved roads",
            "surface": "tight corners and variable pavement",
        },
        "climate": {"description": "hot and humid", "challenges": ["heat"]},
    }

    overlay = generate_race_overlay(
        race,
        {"heat_resilience": 9, "technical": 9, "altitude": 0},
    )

    assert "Pre-load sodium" not in overlay["heat"]
    assert "500\u2013750ml/hr" not in overlay["heat"]
    assert "fixed fluid or sodium prescription" in overlay["heat"]
    assert "confirmed resupply points" not in overlay["nutrition"]
    assert "confirm the organizer\u2019s current resupply locations" in overlay["nutrition"]
    assert "5 PSI" not in overlay["terrain"]
    assert "15+ minutes" not in overlay["terrain"]


def test_repair_safety_overlays_updates_only_known_stale_claims(tmp_path):
    output_dir = tmp_path / "packs"
    race_dir = tmp_path / "races"
    output_dir.mkdir()
    race_dir.mkdir()
    stale = {
        "slug": "example-hot-race",
        "demands": {"heat_resilience": 9, "technical": 9, "altitude": 0},
        "race_overlay": {
            "heat": "Pre-load sodium 48 hours out. Target 500–750ml/hr.",
            "nutrition": "Carry enough between confirmed resupply points.",
            "terrain": "5 PSI wrong costs you 15+ minutes.",
        },
        "generated_at": "2026-08-05",
    }
    current = {
        "slug": "current-race",
        "race_overlay": {"nutrition": "Current safe guidance."},
        "generated_at": "2026-08-05",
    }
    (output_dir / "example-hot-race.json").write_text(json.dumps(stale))
    (output_dir / "current-race.json").write_text(json.dumps(current))
    (race_dir / "example-hot-race.json").write_text(json.dumps({
        "race": {
            "display_name": "Example Hot Race",
            "vitals": {"distance_mi": 65, "elevation_ft": 3000, "date": "July"},
            "terrain": {
                "primary": "technical paved roads",
                "surface": "tight corners and variable pavement",
            },
            "climate": {"description": "hot and humid", "challenges": ["heat"]},
        }
    }))

    repaired = repair_safety_overlays(str(output_dir), str(race_dir))
    updated = json.loads((output_dir / "example-hot-race.json").read_text())

    assert repaired == 1
    assert "Pre-load sodium" not in updated["race_overlay"]["heat"]
    assert "confirmed resupply points" not in updated["race_overlay"]["nutrition"]
    assert "5 PSI" not in updated["race_overlay"]["terrain"]
    assert json.loads((output_dir / "current-race.json").read_text()) == current


def test_repair_safety_overlays_repairs_orphaned_alias_pack(tmp_path):
    output_dir = tmp_path / "packs"
    race_dir = tmp_path / "races"
    output_dir.mkdir()
    race_dir.mkdir()
    alias = {
        "slug": "old-alias",
        "race_name": "Old Alias Race",
        "distance_mi": 70,
        "demands": {"heat_resilience": 6, "technical": 8},
        "race_overlay": {
            "heat": "Increase sodium intake 48 hours before race day.",
            "terrain": "5 PSI wrong costs you 15+ minutes.",
        },
    }
    (output_dir / "old-alias.json").write_text(json.dumps(alias))

    assert repair_safety_overlays(str(output_dir), str(race_dir)) == 1
    repaired = json.loads((output_dir / "old-alias.json").read_text())
    assert "Increase sodium intake" not in repaired["race_overlay"]["heat"]
    assert "5 PSI" not in repaired["race_overlay"]["terrain"]
