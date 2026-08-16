"""Current-source contracts for Mount Baker Hill Climb 2026."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROFILE = ROOT / "race-data" / "mount-baker-hill-climb.json"
SCORE_FIELDS = (
    "distance",
    "climbing",
    "descent_technicality",
    "road_surface",
    "climate_risk",
    "altitude",
    "logistics",
    "prestige",
    "organization",
    "scenic_experience",
    "community_culture",
    "field_depth",
    "value",
    "expenses",
)


def _race() -> dict:
    return json.loads(PROFILE.read_text(encoding="utf-8"))["race"]


def test_mount_baker_uses_current_2026_race_facts() -> None:
    race = _race()
    vitals = race["vitals"]

    assert vitals["date_specific"] == "2026: September 13"
    assert vitals["distance_mi"] == 22.0
    assert vitals["distance_km"] == 35.4
    assert vitals["elevation_ft"] == 4462.0
    assert "Snowater Road" in vitals["start_format"]
    assert "Social 7:00am" in vitals["start_format"]
    assert "Recreational 8:00am" in vitals["start_format"]
    assert "Competitive 8:30am" in vitals["start_format"]
    assert "capped at 450" in vitals["field_size"]
    assert "sold out with a waitlist open" in vitals["field_size"]
    assert race["tagline"].startswith("A timed 22-mile, 4,462-foot ascent")
    assert race["eligibility"]["verified"] == "2026-08-15"


def test_mount_baker_preserves_pricing_and_transport_distinctions() -> None:
    race = _race()
    vitals = race["vitals"]
    logistics = race["logistics"]

    assert "$90 individual / $120 tandem" in vitals["entry_fee"]
    assert "$80 / $100 early pricing" in vitals["entry_fee"]
    assert "does not publish a rider cutoff" in vitals["cutoff_time"]
    assert "reopens to traffic at 12:00pm" in vitals["cutoff_time"]
    assert "Artist Point at 10:30am" in vitals["cutoff_time"]
    assert "Heather Meadows Cafe at 12:30pm" in vitals["cutoff_time"]
    assert "strongly encourages carpooling" in logistics["airport"]
    assert "20 first-come seats" in logistics["transport"]
    assert "$5 NW Forest Pass" in logistics["transport"]
    assert "Cell service is limited" in logistics["transport"]

    text = json.dumps(race, ensure_ascii=False)
    assert "Carpool mandatory" not in text
    assert "No strict cutoff" not in text
    assert "custom medals/jersey" not in text


def test_mount_baker_climb_and_pack_do_not_confuse_gain_with_altitude() -> None:
    race = _race()
    climb = race["climb_profile"]
    race_pack = json.loads(
        (ROOT / "web" / "race-packs" / "mount-baker-hill-climb.json").read_text()
    )
    pack_text = json.dumps(race_pack, ensure_ascii=False)

    assert climb["total_climbs"] == 1
    assert climb["_needs_enrichment"] is False
    assert climb["key_climbs"][0]["summit_altitude_m"] == 1567
    assert "approximately 5,100ft above sea level" in pack_text
    assert "above 8,000ft" not in pack_text
    assert "heat exposure sessions" not in pack_text


def test_mount_baker_rating_remains_rubric_consistent() -> None:
    rating = _race()["fondo_rating"]
    expected = round(
        (sum(rating[field] for field in SCORE_FIELDS) + rating["cultural_impact"])
        / 70
        * 100
    )

    assert rating["overall_score"] == expected == 83
    assert rating["tier"] == 1
    assert rating["tier_label"] == "TIER 1"


def test_mount_baker_cites_current_official_sources() -> None:
    urls = [citation["url"] for citation in _race()["citations"]]

    assert "https://bakerhillclimb.com/" in urls or "https://bakerhillclimb.com" in urls
    assert "https://bakerhillclimb.com/about/" in urls
    assert "https://bakerhillclimb.com/race-information/" in urls
    assert "https://bakerhillclimb.com/race-day-information/" in urls
    assert "https://bakerhillclimb.com/prizes-winners/" in urls


def test_mount_baker_generated_index_is_current() -> None:
    index = json.loads((ROOT / "web" / "race-index.json").read_text())
    row = next(record for record in index if record["slug"] == "mount-baker-hill-climb")

    assert row["month"] == "September"
    assert row["distance_km"] == 35.4
    assert row["elevation_m"] == 1360
    assert row["overall_score"] == 83
    assert row["tier"] == 1
