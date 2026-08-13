"""Regression coverage for the verified Sierra Nevada Límite 2027 source."""

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent


def _race() -> dict:
    return json.loads(
        (ROOT / "race-data" / "sierra-nevada-limite.json").read_text()
    )["race"]


def test_sierra_nevada_limite_uses_confirmed_2027_vitals() -> None:
    race = _race()
    vitals = race["vitals"]

    assert vitals["date"] == "2027: May 15"
    assert vitals["date_specific"] == "2027: May 15 (Saturday, 08:00 start)"
    assert vitals["distance_km"] == 119.0
    assert vitals["elevation_m"] == 3300
    assert vitals["entry_fee"].startswith("EUR55 Gran Fondo")
    assert "sierra-nevada-limite-2027" in vitals["registration"]


def test_sierra_nevada_limite_score_matches_roadie_rubric() -> None:
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

    assert rating["distance"] == 2
    assert rating["climbing"] == 4
    assert rating["altitude"] == 4
    assert rating["overall_score"] == expected == 64
    assert rating["tier"] == 2


def test_sierra_nevada_limite_is_cleared_without_claiming_bad_route_data() -> None:
    race = _race()
    eligibility = race["eligibility"]
    source_record = (
        ROOT / "research-dumps" / "sierra-nevada-limite.md"
    ).read_text()

    assert eligibility["status"] == "active"
    assert eligibility["verified"] == "2026-08-13"
    assert "CLEARED FOR PLAN BUILD" in eligibility["notes"]
    assert "unrelated HUEX route" in eligibility["notes"]
    assert "beyond the stated 119km finish" in source_record
    assert "It is not usable for" in source_record
    assert "Sierra Nevada route reconstruction" in source_record


def test_sierra_nevada_limite_race_pack_is_current_and_road_specific() -> None:
    preview = json.loads(
        (ROOT / "web" / "race-packs" / "sierra-nevada-limite.json").read_text()
    )
    text = json.dumps(preview, ensure_ascii=False)

    assert preview["demands"]["climbing"] == 8
    assert preview["demands"]["altitude"] == 8
    assert "similar paved roads" in preview["race_overlay"]["terrain"]
    assert "10,890ft" not in text
    assert "above 8,000ft" not in text
    assert "unstable surfaces" not in text
    assert "5 PSI" not in text
