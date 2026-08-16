"""Current-source contracts for Granfondo Matildica 2026."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROFILE = ROOT / "race-data" / "granfondo-matildica.json"
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


def test_matildica_uses_the_54th_edition_2026_race() -> None:
    race = _race()
    vitals = race["vitals"]

    assert vitals["date"] == "Sunday, September 13, 2026"
    assert vitals["date_specific"] == "September 13, 2026 (Sunday)"
    assert vitals["distance_km"] == 153.0
    assert vitals["distance_mi"] == 95.1
    assert vitals["elevation_m"] == 2150
    assert vitals["route_options"][1]["distance_km"] == 126
    assert vitals["route_options"][1]["elevation_m"] == 1450
    assert "7:30am" in vitals["start_format"]
    assert "6 hours 30 minutes" in vitals["cutoff_time"]
    assert race["eligibility"]["verified"] == "2026-08-15"


def test_matildica_course_copy_matches_current_organizer_pages() -> None:
    text = json.dumps(_race(), ensure_ascii=False)

    for sector in (
        "Vetto climb from km 45 to 47",
        "Gottano climb from km 52 to 56",
        "Ramiseto climb from km 61 to 64",
        "Maillo climb from km 95 to 99",
        "Stella climb from km 110 to 114",
    ):
        assert sector in text
    assert "first qualifier for the 2027 world championships" in text
    assert "€60 online" in text
    assert "€55 until August 29, 2025" not in text
    assert "Italy's oldest gran fondo" not in text
    assert "4km climb @5.5%" not in text
    assert "11km climb @3.5%" not in text


def test_matildica_rating_remains_rubric_consistent() -> None:
    rating = _race()["fondo_rating"]
    expected = round(
        (sum(rating[field] for field in SCORE_FIELDS) + rating["cultural_impact"])
        / 70
        * 100
    )

    assert rating["overall_score"] == expected == 74
    assert rating["tier"] == 2
    assert rating["tier_label"] == "TIER 2"


def test_matildica_cites_current_official_sources() -> None:
    urls = [citation["url"] for citation in _race()["citations"]]

    assert (
        "https://www.granfondomatildica.it/doc/2026/"
        "Regolamento-GF-2026-aggiornato.pdf"
    ) in urls
    assert "https://www.granfondomatildica.it/it/granfondo/" in urls
    assert "https://www.granfondomatildica.it/it/salite/" in urls
    assert "https://ucigranfondoworldseries.com/en/gran-fondo-matildica-2026/" in urls


def test_matildica_generated_index_is_current() -> None:
    index = json.loads((ROOT / "web" / "race-index.json").read_text())
    row = next(record for record in index if record["slug"] == "granfondo-matildica")

    assert row["distance_km"] == 153.0
    assert row["elevation_m"] == 2150
    assert row["overall_score"] == 74
    assert row["tier"] == 2
