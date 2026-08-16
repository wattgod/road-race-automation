"""Current-source contracts for CRC 506 Gran Fondo Costa Rica 2026."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROFILE = ROOT / "race-data" / "crc-506-gran-fondo-costa-rica.json"
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


def test_crc_506_uses_the_rescheduled_2026_race() -> None:
    race = _race()
    vitals = race["vitals"]

    assert vitals["date"] == "Sunday, September 13, 2026"
    assert vitals["date_specific"].startswith("September 13, 2026 (Sunday")
    assert vitals["distance_km"] == 141.4
    assert vitals["distance_mi"] == 87.6
    assert vitals["elevation_m"] == 841
    assert vitals["route_options"][1]["distance_km"] == 69.8
    assert vitals["route_options"][1]["distance_mi"] == 43.4
    assert "6:00am" in vitals["start_format"]
    assert "km 72" in vitals["cutoff_time"]
    assert "9:30am" in vitals["cutoff_time"]
    assert race["eligibility"]["verified"] == "2026-08-15"


def test_crc_506_course_copy_matches_the_technical_guide() -> None:
    race = _race()
    text = json.dumps(race, ensure_ascii=False)

    assert "4.6 km controlled rollout" in text
    assert "km 24.4, 53.3, 72, 88, and 117.3" in text
    assert "69.8 km Medio Fondo" in text
    assert "paved road event" in text
    assert "72.9km" not in text
    assert "Limited 1000 spots" not in text
    assert "87.6-mile gravel event" not in text


def test_crc_506_rating_remains_rubric_consistent() -> None:
    rating = _race()["fondo_rating"]
    expected = round(
        (sum(rating[field] for field in SCORE_FIELDS) + rating["cultural_impact"])
        / 70
        * 100
    )

    assert rating["overall_score"] == expected == 66
    assert rating["tier"] == 2
    assert rating["tier_label"] == "TIER 2"


def test_crc_506_cites_current_official_sources() -> None:
    urls = [citation["url"] for citation in _race()["citations"]]

    assert "https://2026.ucigranfondocostarica.com/" in urls
    assert (
        "https://ucigranfondocostarica.com/wp-content/uploads/2026/04/"
        "CRC-506-GRAN-FONDO-DE-COSTA-RICA-2026-GT180326-eng-v01.pdf"
    ) in urls
    assert "https://ucigranfondoworldseries.com/en/crc506-gran-fondo-of-costa-rica/" in urls


def test_crc_506_generated_index_is_current() -> None:
    index = json.loads((ROOT / "web" / "race-index.json").read_text())
    row = next(record for record in index if record["slug"] == "crc-506-gran-fondo-costa-rica")

    assert row["distance_km"] == 141.4
    assert row["elevation_m"] == 841
    assert row["overall_score"] == 66
    assert row["tier"] == 2
