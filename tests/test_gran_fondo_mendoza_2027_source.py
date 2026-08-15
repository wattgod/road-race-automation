"""Official-source contract for Gran Fondo Mendoza 2027."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROFILE = ROOT / "race-data" / "gran-fondo-mendoza.json"


def race() -> dict:
    return json.loads(PROFILE.read_text(encoding="utf-8"))["race"]


def test_mendoza_has_the_organizer_confirmed_2027_date_and_routes() -> None:
    profile = race()
    vitals = profile["vitals"]

    assert vitals["date"] == "March 14, 2027"
    assert vitals["date_specific"] == "2027: March 14"
    assert vitals["distance_km"] == 109.6
    assert vitals["distance_mi"] == 68.1
    assert vitals["elevation_m"] == 1185
    assert vitals["elevation_ft"] == 3888
    assert "109.6 km / 1,185 m" in vitals["route_options"][0]
    assert "41.7 km / 401 m" in vitals["route_options"][1]
    assert "07:15" in vitals["start_format"]


def test_mendoza_is_cleared_with_a_final_rider_communications_guard() -> None:
    profile = race()
    review = profile["source_review"]
    clearance = profile["training_plan_clearance"]

    assert review["race_date"] == "2027-03-14"
    assert review["reviewed_at"] == "2026-08-14"
    assert review["plan_status"] == "CLEARED FOR FULL-7"
    assert clearance["status"] == "ready"
    assert clearance["race_date"] == "2027-03-14"
    assert clearance["ladder"] == "FULL-7"
    assert clearance["variation"] == "All-Rounder"
    assert clearance["blockers"] == []
    assert "final organizer route" in clearance["guard"]
    assert "CLEARED FOR PLAN BUILD" in profile["eligibility"]["notes"]


def test_mendoza_cites_first_party_2027_rules_and_route_files() -> None:
    citations = {citation["url"] for citation in race()["citations"]}

    assert "https://granfondomendoza.com.ar/" in citations
    assert "https://granfondomendoza.com.ar/inscripcion/" in citations
    assert (
        "https://granfondomendoza.com.ar/wp-content/uploads/2026/05/"
        "REGLAMENTO-GFM-2027-2.pdf"
    ) in citations
    assert "https://ridewithgps.com/routes/53154155" in citations
    assert "https://ridewithgps.com/routes/53154091" in citations


def test_mendoza_rating_is_mathematically_consistent() -> None:
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

    assert rating["overall_score"] == expected == 50
    assert rating["tier"] == 3


def test_mendoza_generated_pipeline_artifacts_are_current() -> None:
    readiness = json.loads((ROOT / "data" / "plan-readiness.json").read_text())
    sku_map = json.loads((ROOT / "data" / "tp-sku-map.json").read_text())
    race_pack = json.loads(
        (ROOT / "web" / "race-packs" / "gran-fondo-mendoza.json").read_text()
    )
    race_dates = json.loads((ROOT / "web" / "race-dates.json").read_text())
    index = json.loads((ROOT / "web" / "race-index.json").read_text())

    record = readiness["races"]["gran-fondo-mendoza"]
    assert record["ready"] is True
    assert record["race_date"] == "2027-03-14"
    assert record["plan_clearance_status"] == "ready"
    assert sku_map["gran-fondo-mendoza"] == "road-allrounder"
    assert race_pack["distance_mi"] == 68.1
    assert race_pack["demands"]["climbing"] < 7
    assert race_dates["gran-fondo-mendoza"] == "2027-03-14"
    assert any(
        row["slug"] == "gran-fondo-mendoza" and row["overall_score"] == 50
        for row in index
    )
