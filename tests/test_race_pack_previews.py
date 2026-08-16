"""Road race-pack previews must stay road-specific."""

import sys
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from generate_race_pack_previews import (  # noqa: E402
    calculate_category_scores,
    generate_preview,
    generate_race_overlay,
    generate_workout_context,
    get_top_categories,
)


def test_every_race_profile_has_a_training_preview():
    root = Path(__file__).resolve().parent.parent
    profiles = {path.stem for path in (root / "race-data").glob("*.json")}
    previews = {path.stem for path in (root / "web" / "race-packs").glob("*.json")}

    assert profiles <= previews


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


def test_altitude_overlay_never_treats_total_climbing_as_finish_altitude():
    race = {
        "display_name": "UCI Granfondo Colombia",
        "vitals": {"distance_mi": 85.7, "elevation_ft": 6562},
        "terrain": {"primary": "mountain road"},
        "climb_profile": {
            "key_climbs": [{"summit_altitude_m": 2525}],
        },
        "climate": {
            "challenges": ["Racing for an extended period near or above 2,000 m"],
        },
    }

    overlay = generate_race_overlay(race, {"altitude": 8, "technical": 4})

    assert "8,300ft above sea level" in overlay["altitude"]
    assert "6,562ft of climbing" not in overlay["altitude"]
    assert "finishes high" not in overlay["altitude"]


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


def test_high_technical_overlay_stays_road_specific_and_avoids_fake_time_claims():
    race = {
        "display_name": "Sierra Nevada Límite Gran Fondo",
        "vitals": {"distance_mi": 73.9, "elevation_ft": 10826.8},
        "terrain": {"primary": "paved mountain roads"},
    }

    overlay = generate_race_overlay(race, {"altitude": 2, "technical": 8})

    assert "similar paved roads" in overlay["terrain"]
    assert "braking points" in overlay["terrain"]
    assert "unstable surfaces" not in overlay["terrain"]
    assert "5 PSI" not in overlay["terrain"]
    assert "15+ minutes" not in overlay["terrain"]


def test_multi_day_ultra_overlay_does_not_invent_a_single_calorie_total():
    race = {
        "display_name": "Race Around Poland",
        "vitals": {"distance_mi": 2237, "elevation_ft": 108596},
        "terrain": {"primary": "paved roads"},
    }

    overlay = generate_race_overlay(race, {"altitude": 2, "technical": 4})
    nutrition = overlay["nutrition"]

    assert "multi-day 2237-mile race" in nutrition
    assert "substantial meals at planned stops" in nutrition
    assert "category rules allow" in nutrition
    assert "8,000–12,000" not in nutrition
    assert "you cannot replace them all" not in nutrition


def test_climate_risk_without_heat_evidence_emits_weather_preparation():
    race = {
        "display_name": "Wet Alpine Fondo",
        "vitals": {
            "distance_mi": 68.4,
            "date": "May 23, 2027",
            "location": "Imst, Tyrol, Austria",
        },
        "climate": {
            "primary": "Changeable late-spring Alpine weather",
            "description": "Cool starts, rain, and fast temperature changes are possible.",
            "challenges": ["Rain and reduced grip", "Wind exposure"],
        },
    }

    race["fondo_rating"] = {"climate_risk": 4}
    overlay = generate_race_overlay(
        race, {"heat_resilience": 0, "altitude": 2, "technical": 2}
    )

    assert "heat" not in overlay
    assert "weather" in overlay
    assert "adaptable layers" in overlay["weather"]
    assert "wet-road braking" in overlay["weather"]
    assert "crosswinds" in overlay["weather"]


def test_explicit_hot_climate_keeps_heat_preparation():
    race = {
        "display_name": "Hot Summer Fondo",
        "vitals": {
            "distance_mi": 100,
            "date": "July 11, 2027",
            "location": "Tucson, Arizona",
        },
        "climate": {
            "primary": "Hot desert summer",
            "description": "High heat and sun exposure shape the race.",
            "challenges": ["Extreme heat", "Direct sun exposure"],
        },
    }

    overlay = generate_race_overlay(
        race, {"heat_resilience": 8, "altitude": 0, "technical": 2}
    )

    assert "heat" in overlay
    assert "heat acclimatization" in overlay["heat"]
    assert "weather" not in overlay


def test_nutrition_overlay_does_not_invent_confirmed_resupply_points():
    race = {
        "display_name": "Unpublished Aid Fondo",
        "vitals": {
            "distance_mi": 74.6,
            "feed_zones": "Not yet published",
        },
        "terrain": {"primary": "paved roads"},
    }

    overlay = generate_race_overlay(
        race, {"heat_resilience": 2, "altitude": 0, "technical": 2}
    )

    assert "confirmed resupply points" not in overlay["nutrition"]
    assert "has not published a reliable resupply plan" in overlay["nutrition"]


def test_nutrition_overlay_uses_confirmed_resupply_plan_when_present():
    race = {
        "display_name": "Supported Fondo",
        "vitals": {
            "distance_mi": 74.6,
            "feed_zones": "Three aid stations at kilometers 35, 70, and 100",
        },
        "terrain": {"primary": "paved roads"},
    }

    overlay = generate_race_overlay(
        race, {"heat_resilience": 2, "altitude": 0, "technical": 2}
    )

    assert "current resupply plan" in overlay["nutrition"]
    assert "has not published" not in overlay["nutrition"]
