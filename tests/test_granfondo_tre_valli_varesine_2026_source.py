"""Current-source contracts for Granfondo Tre Valli Varesine 2026."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROFILE = ROOT / "race-data" / "granfondo-tre-valli-varesine.json"
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


def test_tre_valli_uses_the_october_4_2026_race() -> None:
    race = _race()
    vitals = race["vitals"]

    assert vitals["date"] == "Sunday, October 4, 2026"
    assert vitals["date_specific"] == "October 4, 2026 (Sunday)"
    assert vitals["distance_km"] == 126.0
    assert vitals["distance_mi"] == 78.3
    assert vitals["elevation_m"] == 1993
    assert "9:00-9:40am" in vitals["start_format"]
    assert "€60 online" in vitals["entry_fee"]
    assert "€80 on site" in vitals["entry_fee"]
    assert "Montegrino Valtravaglia by 12:00pm" in vitals["cutoff_time"]
    assert race["eligibility"]["verified"] == "2026-08-15"


def test_tre_valli_course_copy_matches_the_august_race_guide() -> None:
    text = json.dumps(_race(), ensure_ascii=False)

    for fact in (
        "km 37.2 (Cugliate Fabiasco)",
        "km 64.6 (Brezzo di Bedero)",
        "km 88.5 (Castello Cabiaglio)",
        "km 125.0 in Varese",
        "Alpe Tedesco",
        "Santuario della Madonna di Ardena",
        "Lake Maggiore",
        "riders passed by the end-of-race vehicle must follow normal road rules",
    ):
        assert fact in text

    assert "Limited to 2,000" not in text
    assert "Not specified in available sources" not in text
    assert "Road quality is excellent" not in text
    assert "Closed roads through" not in text


def test_tre_valli_records_both_2026_championship_roles() -> None:
    text = json.dumps(_race(), ensure_ascii=False)

    assert "2026 UEC Granfondo European Championships" in text
    assert "2027 UCI Gran Fondo World Championships" in text
    assert "first 25% of finishers in each UCI age category" in text


def test_tre_valli_rating_remains_rubric_consistent() -> None:
    rating = _race()["fondo_rating"]
    expected = round(
        (sum(rating[field] for field in SCORE_FIELDS) + rating["cultural_impact"])
        / 70
        * 100
    )

    assert rating["overall_score"] == expected == 74
    assert rating["tier"] == 2
    assert rating["tier_label"] == "TIER 2"


def test_tre_valli_cites_current_official_sources() -> None:
    urls = [citation["url"] for citation in _race()["citations"]]

    assert (
        "https://trevallivaresine.info/wp-content/uploads/2025/12/"
        "Regolamento_GF_2026_eng-1.pdf"
    ) in urls
    assert (
        "https://trevallivaresine.info/wp-content/uploads/2026/08/"
        "Raceguide_3_valli_2026-3.pdf"
    ) in urls
    assert (
        "https://trevallivaresine.info/en/races/"
        "gran-fondo-tre-valli-varesine-uci-world-series/registration/"
    ) in urls
    assert (
        "https://ucigranfondoworldseries.com/en/"
        "uec-granfondo-european-championships-awarded-to-varese-on-3-4-october/"
    ) in urls


def test_tre_valli_generated_index_is_current() -> None:
    index = json.loads((ROOT / "web" / "race-index.json").read_text())
    row = next(
        record
        for record in index
        if record["slug"] == "granfondo-tre-valli-varesine"
    )

    assert row["month"] == "October"
    assert row["distance_km"] == 126.0
    assert row["elevation_m"] == 1993
    assert row["overall_score"] == 74
    assert row["tier"] == 2
