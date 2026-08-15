"""Official-source contract for The Millars Gran Fondo 2027."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROFILE = ROOT / "race-data" / "the-millars-gran-fondo.json"


def race() -> dict:
    return json.loads(PROFILE.read_text(encoding="utf-8"))["race"]


def test_millars_has_the_organizer_confirmed_2027_date_and_course() -> None:
    profile = race()
    vitals = profile["vitals"]

    assert vitals["date_specific"] == "March 14, 2027"
    assert vitals["distance_km"] == 156.6
    assert vitals["distance_mi"] == 97.3
    assert vitals["elevation_m"] == 2211
    assert vitals["elevation_ft"] == 7254.0
    assert "Provisional 2027" in vitals["route_options"][0]


def test_millars_is_cleared_with_a_provisional_course_guard() -> None:
    profile = race()
    review = profile["source_review"]
    clearance = profile["training_plan_clearance"]

    assert review["race_date"] == "2027-03-14"
    assert review["reviewed_at"] == "2026-08-14"
    assert "CLEARED FOR FULL-7" in review["plan_status"]
    assert clearance["status"] == "ready"
    assert clearance["race_date"] == "2027-03-14"
    assert clearance["ladder"] == "FULL-7"
    assert clearance["variation"] == "Alpine-Fondo"
    assert clearance["blockers"] == []
    assert "override" in clearance["guard"]
    assert "CLEARED FOR PLAN BUILD" in profile["eligibility"]["notes"]


def test_millars_cites_the_first_party_2027_sources() -> None:
    citations = {citation["url"] for citation in race()["citations"]}

    assert "https://www.millarsgranfondo.com/en/registration/" in citations
    assert "https://www.millarsgranfondo.com/en/race/course/" in citations


def test_millars_rating_remains_mathematically_consistent() -> None:
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

    assert rating["overall_score"] == expected == 73
    assert rating["tier"] == 2


def test_millars_generated_pipeline_artifacts_are_current() -> None:
    readiness = json.loads((ROOT / "data" / "plan-readiness.json").read_text())
    sku_map = json.loads((ROOT / "data" / "tp-sku-map.json").read_text())
    race_pack = json.loads(
        (ROOT / "web" / "race-packs" / "the-millars-gran-fondo.json").read_text()
    )
    race_dates = json.loads((ROOT / "web" / "race-dates.json").read_text())
    index = json.loads((ROOT / "web" / "race-index.json").read_text())

    record = readiness["races"]["the-millars-gran-fondo"]
    assert record["ready"] is True
    assert record["race_date"] == "2027-03-14"
    assert record["plan_clearance_status"] == "ready"
    assert sku_map["the-millars-gran-fondo"] == "road-alpine-fondo"
    assert race_pack["distance_mi"] == 97.3
    assert race_pack["demands"]["climbing"] == 7
    assert race_pack["demands"]["heat_resilience"] == 0
    assert "heat" not in race_pack["race_overlay"]
    assert "altitude" not in race_pack["race_overlay"]
    assert race_dates["the-millars-gran-fondo"] == "2027-03-14"
    assert any(
        row["slug"] == "the-millars-gran-fondo"
        and row["overall_score"] == 73
        for row in index
    )
