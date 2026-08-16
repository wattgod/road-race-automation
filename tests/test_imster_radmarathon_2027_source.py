"""Regression coverage for the newly cataloged Imster Radmarathon 2027 race."""

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
PROFILE = ROOT / "race-data" / "imster-radmarathon.json"


def _race() -> dict:
    return json.loads(PROFILE.read_text())["race"]


def test_imster_uses_current_official_2027_route_a() -> None:
    race = _race()
    vitals = race["vitals"]

    assert vitals["date"] == "May 23, 2027"
    assert vitals["date_specific"] == "May 23, 2027 (Sunday, 07:00 start)"
    assert vitals["distance_km"] == 110.0
    assert vitals["elevation_m"] == 2300
    assert "Haimingerberg/Sattele" in vitals["feed_zones"]
    assert "Jerzens 14:30" in vitals["cutoff_time"]


def test_imster_profile_preserves_open_road_and_timing_facts() -> None:
    race = _race()
    record = (ROOT / "research-dumps" / "imster-radmarathon.md").read_text()

    assert "open to normal traffic" in race["terrain"]["surface"]
    assert race["fondo_rating"]["organization"] == 2
    assert "transponder system" in record
    assert "roads are **not closed**" in record
    assert "1,000 vertical metres in 10 kilometres" in record


def test_imster_rating_is_mathematically_consistent() -> None:
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

    assert rating["overall_score"] == expected == 59
    assert rating["tier"] == 3
    assert rating["tier_label"] == "TIER 3"


def test_imster_is_cleared_from_first_party_evidence() -> None:
    race = _race()
    review = race["source_review"]
    clearance = race["training_plan_clearance"]
    eligibility = race["eligibility"]

    assert review["race_date"] == "2027-05-23"
    assert review["plan_status"] == "CLEARED FOR FULL-7 ROADIE LABS PLAN BUILD"
    assert clearance["status"] == "ready"
    assert clearance["race_date"] == "2027-05-23"
    assert clearance["ladder"] == "FULL-7"
    assert clearance["variation"] == "Alpine-Fondo"
    assert clearance["blockers"] == []
    assert eligibility["status"] == "active"
    assert eligibility["verified"] == "2026-08-15"
    assert "CLEARED FOR PLAN BUILD" in eligibility["notes"]


def test_imster_citations_are_first_party() -> None:
    citations = _race()["citations"]

    assert len(citations) >= 7
    assert all(citation["category"] == "official" for citation in citations)
    assert all(
        citation["url"].startswith(
            ("https://www.imster-radmarathon.at/", "https://www.radsportevents.com/", "https://www.imst.at/")
        )
        for citation in citations
    )


def test_imster_generated_pipeline_artifacts_are_current() -> None:
    readiness = json.loads((ROOT / "data" / "plan-readiness.json").read_text())
    sku_map = json.loads((ROOT / "data" / "tp-sku-map.json").read_text())
    race_pack = json.loads(
        (ROOT / "web" / "race-packs" / "imster-radmarathon.json").read_text()
    )
    race_dates = json.loads((ROOT / "web" / "race-dates.json").read_text())
    index = json.loads((ROOT / "web" / "race-index.json").read_text())

    record = readiness["races"]["imster-radmarathon"]
    assert record["ready"] is True
    assert record["race_date"] == "2027-05-23"
    assert record["plan_clearance_status"] == "ready"
    assert sku_map["imster-radmarathon"] == "road-allrounder"
    assert race_pack["distance_mi"] == 68.4
    assert race_pack["demands"]["climbing"] == 6
    assert race_pack["demands"]["heat_resilience"] == 0
    assert "heat" not in race_pack["race_overlay"]
    assert "weather" in race_pack["race_overlay"]
    assert "adaptable layers" in race_pack["race_overlay"]["weather"]
    assert "wet-road braking" in race_pack["race_overlay"]["weather"]
    assert race_dates["imster-radmarathon"] == "2027-05-23"
    assert any(
        row["slug"] == "imster-radmarathon"
        and row["overall_score"] == 59
        and row["location"] == "Imst, Tyrol, Austria"
        for row in index
    )
