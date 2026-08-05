"""Road race-pack previews must stay road-specific."""

import sys
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from generate_race_pack_previews import (  # noqa: E402
    calculate_category_scores,
    generate_preview,
    get_top_categories,
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
