"""Current-source contracts for L'Étape Hermosillo 2026."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROFILE = ROOT / "race-data" / "letape-hermosillo.json"
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


def test_hermosillo_preserves_verified_identity_and_route() -> None:
    race = _race()
    vitals = race["vitals"]

    assert race["slug"] == "letape-hermosillo"
    assert vitals["date"] == "October 18, 2026"
    assert vitals["distance_km"] == 120
    assert vitals["distance_mi"] == 74.6
    assert vitals["elevation_m"] is None
    assert vitals["elevation_ft"] is None
    assert vitals["route_options"] == ["Long: 120 km", "Short: 60 km"]
    assert "Parque Madero" in vitals["start_format"]
    assert "Bahía de Kino" in vitals["start_format"]


def test_hermosillo_discloses_current_official_conflicts() -> None:
    race = _race()
    vitals = race["vitals"]
    text = json.dumps(race, ensure_ascii=False)

    assert "León, Guanajuato" in vitals["start_format"]
    assert "registration Open" in vitals["registration"]
    assert "generic L'Étape Draft template" in vitals["registration"]
    assert "Hermosillo-specific entry" in vitals["registration"]
    assert "León host line conflicts" in race["source_review"]["facts_scope"]
    assert "León, Guanajuato" in race["course_description"]["character"]
    assert "generic L'Étape Draft template" in race["course_description"]["character"]
    for unknown in (
        "Exact gain",
        "route file",
        "start time",
        "cutoff",
        "aid plan",
        "price",
        "equipment rules",
        "transport",
    ):
        assert unknown in race["source_review"]["facts_scope"]
    assert "170-kilometer Alpine profile" in text


def test_hermosillo_preview_does_not_invent_resupply() -> None:
    preview_path = ROOT / "web" / "race-packs" / "letape-hermosillo.json"
    preview = json.loads(preview_path.read_text(encoding="utf-8"))
    nutrition = preview["race_overlay"]["nutrition"]

    assert "confirmed resupply points" not in nutrition
    assert "has not published a reliable resupply plan" in nutrition


def test_hermosillo_grade_follows_the_rubric() -> None:
    rating = _race()["fondo_rating"]
    expected = round(
        (sum(rating[field] for field in SCORE_FIELDS) + rating["cultural_impact"])
        / 70
        * 100
    )

    assert rating["overall_score"] == expected == 56
    assert rating["tier"] == 3
    assert rating["tier_label"] == "TIER 3"
    assert _race()["training_plan_clearance"]["ladder"] == "SHORT-3"
    assert _race()["training_plan_clearance"]["variation"] == "All-Rounder"


def test_hermosillo_cites_current_primary_sources() -> None:
    urls = [citation["url"] for citation in _race()["citations"]]

    assert "https://www.letapeseries.com/the-series-en" in urls
    assert "https://hermosillo.letapeseries.com/" in urls
    assert any("serial-letape-mexico-2026" in url for url in urls)
    assert any("hermosillo.gob.mx" in url for url in urls)
