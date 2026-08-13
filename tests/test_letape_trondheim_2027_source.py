"""Regression coverage for the newly cataloged L'Étape Trondheim 2027 race."""

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
PROFILE = ROOT / "race-data" / "letape-trondheim.json"


def _race() -> dict:
    return json.loads(PROFILE.read_text())["race"]


def test_trondheim_uses_current_official_2027_long_course() -> None:
    race = _race()
    vitals = race["vitals"]

    assert vitals["date"] == "June 12, 2027"
    assert vitals["date_specific"] == "June 12, 2027 (Saturday, 11:00 start)"
    assert vitals["distance_km"] == 128.0
    assert vitals["elevation_m"] == 1570
    assert "NOK 1,290" in vitals["entry_fee"]
    assert "three on-course" in vitals["feed_zones"].lower()


def test_trondheim_has_three_verified_categorized_climbs() -> None:
    profile = _race()["climb_profile"]

    assert profile["total_climbs"] == 3
    assert profile["cat_3_climbs"] == 1
    assert any("Grøset" in climb and "7.1%" in climb for climb in profile["key_climbs"])
    assert any("Venn" in climb and "7%" in climb for climb in profile["key_climbs"])
    assert any("Ståggån" in climb and "5%" in climb for climb in profile["key_climbs"])


def test_trondheim_rating_is_mathematically_consistent() -> None:
    rating = _race()["fondo_rating"]
    score_keys = [
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
        (sum(rating[key] for key in score_keys) + rating["cultural_impact"])
        / 70
        * 100
    )

    assert rating["overall_score"] == expected == 60
    assert rating["tier"] == 2


def test_trondheim_is_cleared_from_first_party_evidence() -> None:
    race = _race()
    review = race["source_review"]
    clearance = race["training_plan_clearance"]
    eligibility = race["eligibility"]
    record = (ROOT / "research-dumps" / "letape-trondheim.md").read_text()

    assert review["race_date"] == "2027-06-12"
    assert review["plan_status"] == "CLEARED FOR FULL-7 ROADIE LABS PLAN BUILD"
    assert clearance["status"] == "ready"
    assert clearance["race_date"] == "2027-06-12"
    assert clearance["ladder"] == "FULL-7"
    assert clearance["variation"] == "All-Rounder"
    assert clearance["blockers"] == []
    assert eligibility["status"] == "active"
    assert eligibility["verified"] == "2026-08-13"
    assert "CLEARED FOR PLAN BUILD" in eligibility["notes"]
    assert "No 2027 cutoff" in record
    assert "No 2027 field size" in record


def test_trondheim_citations_are_first_party() -> None:
    citations = _race()["citations"]

    assert len(citations) >= 8
    assert all(citation["category"] == "official" for citation in citations)
    assert all(
        citation["url"].startswith("https://trondheim.letapeseries.com/")
        for citation in citations
    )


def test_trondheim_generated_pipeline_artifacts_are_current() -> None:
    readiness = json.loads((ROOT / "data" / "plan-readiness.json").read_text())
    sku_map = json.loads((ROOT / "data" / "tp-sku-map.json").read_text())
    race_pack = json.loads(
        (ROOT / "web" / "race-packs" / "letape-trondheim.json").read_text()
    )
    race_dates = json.loads((ROOT / "web" / "race-dates.json").read_text())
    index = json.loads((ROOT / "web" / "race-index.json").read_text())

    record = readiness["races"]["letape-trondheim"]
    assert record["ready"] is True
    assert record["race_date"] == "2027-06-12"
    assert record["plan_clearance_status"] == "ready"
    assert sku_map["letape-trondheim"] == "road-allrounder"
    assert race_pack["distance_mi"] == 79.5
    assert race_pack["demands"]["threshold"] == 7
    assert "three short categorized" not in json.dumps(race_pack)
    assert race_dates["letape-trondheim"] == "2027-06-12"
    assert any(
        row["slug"] == "letape-trondheim"
        and row["location"] == "Trondheim, Trøndelag, Norway"
        for row in index
    )
