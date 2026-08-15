"""Official-source contract for Iron Horse Bicycle Classic 2027."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROFILE = ROOT / "race-data" / "iron-horse-bicycle-classic.json"


def race() -> dict:
    return json.loads(PROFILE.read_text(encoding="utf-8"))["race"]


def test_iron_horse_uses_the_saturday_memorial_weekend_date() -> None:
    profile = race()
    review = profile["source_review"]
    clearance = profile["training_plan_clearance"]

    assert profile["vitals"]["date_specific"] == "2027: May 29"
    assert review["race_date"] == "2027-05-29"
    assert "annual rule" in review["guard"]
    assert clearance["status"] == "ready"
    assert clearance["race_date"] == "2027-05-29"
    assert clearance["ladder"] == "FULL-7"
    assert clearance["variation"] == "Alpine-Fondo"
    assert clearance["blockers"] == []


def test_iron_horse_keeps_the_competitive_road_race_identity_exact() -> None:
    profile = race()
    vitals = profile["vitals"]
    climbs = profile["climb_profile"]

    assert vitals["distance_mi"] == 47.0
    assert vitals["distance_km"] == 75.6
    assert vitals["elevation_ft"] == 5700.0
    assert "47 miles point to point" in vitals["route_options"][0]
    assert "50-mile noncompetitive" in vitals["route_options"][1]
    assert climbs["total_climbs"] == 2
    assert any("Coal Bank" in climb for climb in climbs["key_climbs"])
    assert any("Molas" in climb for climb in climbs["key_climbs"])


def test_iron_horse_grade_remains_mathematically_consistent() -> None:
    rating = race()["fondo_rating"]
    dimensions = [
        "distance",
        "climbing",
        "descent_technicality",
        "climate_risk",
        "organization",
        "scenic_experience",
        "community_culture",
        "altitude",
        "logistics",
        "prestige",
        "field_depth",
        "value",
        "expenses",
        "road_surface",
    ]
    expected = round(
        (sum(rating[key] for key in dimensions) + rating["cultural_impact"])
        / 70
        * 100
    )

    assert rating["overall_score"] == expected == 74
    assert rating["tier"] == 2


def test_iron_horse_first_party_sources_and_guard_are_recorded() -> None:
    profile = race()
    citations = {citation["url"] for citation in profile["citations"]}
    research = (ROOT / "research-dumps/iron-horse-bicycle-classic.md").read_text(
        encoding="utf-8"
    )

    assert "https://www.ironhorsebicycleclassic.com" in citations
    assert (
        "https://www.ironhorsebicycleclassic.com/index.php?nav=coke"
        in citations
    )
    assert "annual-rule derivation" in research
    assert "final 2027 schedule" in research


def test_iron_horse_generated_pipeline_artifacts_are_current() -> None:
    readiness = json.loads((ROOT / "data/plan-readiness.json").read_text())
    sku_map = json.loads((ROOT / "data/tp-sku-map.json").read_text())
    race_pack = json.loads(
        (ROOT / "web/race-packs/iron-horse-bicycle-classic.json").read_text()
    )
    race_dates = json.loads((ROOT / "web/race-dates.json").read_text())
    index = json.loads((ROOT / "web/race-index.json").read_text())

    record = readiness["races"]["iron-horse-bicycle-classic"]
    assert record["ready"] is True
    assert record["race_date"] == "2027-05-29"
    assert record["plan_clearance_status"] == "ready"
    assert sku_map["iron-horse-bicycle-classic"] == "road-alpine-fondo"
    assert race_pack["distance_mi"] == 47.0
    assert race_dates["iron-horse-bicycle-classic"] == "2027-05-29"
    assert any(
        row["slug"] == "iron-horse-bicycle-classic"
        and row["overall_score"] == 74
        for row in index
    )
