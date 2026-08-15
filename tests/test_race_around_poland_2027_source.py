"""Official-source contract for Race Around Poland 2027."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROFILE = ROOT / "race-data" / "race-around-poland.json"


def race() -> dict:
    return json.loads(PROFILE.read_text(encoding="utf-8"))["race"]


def test_rap_has_the_organizer_confirmed_2027_dates_and_full_route_demand() -> None:
    profile = race()
    vitals = profile["vitals"]

    assert vitals["date_specific"] == "2027: June 26-July 8"
    assert "July 8, 2027" in vitals["date"]
    assert vitals["distance_km"] == 3600.0
    assert vitals["elevation_m"] == 33100
    assert "12 days" in vitals["cutoff_time"]
    assert vitals["route_options"][0].startswith("2027 RAP (full)")
    assert vitals["location"] == "Warsaw, Poland"


def test_rap_is_cleared_with_a_final_gpx_guard() -> None:
    profile = race()
    review = profile["source_review"]
    clearance = profile["training_plan_clearance"]

    assert review["race_date"] == "2027-06-26"
    assert review["reviewed_at"] == "2026-08-14"
    assert "CLEARED FOR FULL-7" in review["plan_status"]
    assert clearance["status"] == "ready"
    assert clearance["race_date"] == "2027-06-26"
    assert clearance["ladder"] == "FULL-7"
    assert clearance["variation"] == "Distance"
    assert clearance["blockers"] == []
    assert "start-day GPX override" in clearance["guard"]
    assert "CLEARED FOR PLAN BUILD" in profile["eligibility"]["notes"]


def test_rap_cites_the_first_party_2027_rulebook() -> None:
    citations = {citation["url"] for citation in race()["citations"]}

    assert "https://racearoundpoland.pl/" in citations
    assert "https://racearoundpoland.pl/route" in citations
    assert (
        "https://racearoundpoland.pl/files/2026-08/"
        "regulamin-eng-rap-2027.pdf"
    ) in citations


def test_rap_rating_is_consistent_and_does_not_claim_high_altitude() -> None:
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

    assert rating["overall_score"] == expected == 63
    assert rating["tier"] == 2
    assert rating["altitude"] == 1


def test_rap_generated_pipeline_artifacts_are_current() -> None:
    readiness = json.loads((ROOT / "data" / "plan-readiness.json").read_text())
    sku_map = json.loads((ROOT / "data" / "tp-sku-map.json").read_text())
    race_pack = json.loads(
        (ROOT / "web" / "race-packs" / "race-around-poland.json").read_text()
    )
    race_dates = json.loads((ROOT / "web" / "race-dates.json").read_text())
    index = json.loads((ROOT / "web" / "race-index.json").read_text())

    record = readiness["races"]["race-around-poland"]
    assert record["ready"] is True
    assert record["race_date"] == "2027-06-26"
    assert record["plan_clearance_status"] == "ready"
    assert sku_map["race-around-poland"] == "road-distance"
    assert race_pack["distance_mi"] == 2237.0
    assert race_pack["demands"]["durability"] == 10
    assert "altitude" not in race_pack["race_overlay"]
    assert "multi-day 2237-mile race" in race_pack["race_overlay"]["nutrition"]
    assert "8,000" not in race_pack["race_overlay"]["nutrition"]
    assert race_dates["race-around-poland"] == "2027-06-26"
    assert any(
        row["slug"] == "race-around-poland"
        and row["overall_score"] == 63
        for row in index
    )
