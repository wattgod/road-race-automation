"""Source and generated-artifact contracts for Granfondo Colombia 2026."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROFILE = ROOT / "race-data" / "granfondo-colombia.json"
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


def test_granfondo_colombia_is_the_active_medellin_successor() -> None:
    race = _race()

    assert race["slug"] == "granfondo-colombia"
    assert race["vitals"]["location"] == "Medellín, Antioquia, Colombia"
    assert race["vitals"]["date"] == "November 29, 2026"
    assert race["eligibility"]["status"] == "active"
    assert race["eligibility"]["verified"] == "2026-08-10"
    assert race["training_plan_clearance"]["status"] == "ready"
    assert "granfondo-bogota" in race["catalog_flags"]["status_note"]
    assert "gfny-colombia" in race["catalog_flags"]["status_note"]


def test_granfondo_colombia_preserves_the_official_route_discrepancy() -> None:
    race = _race()
    vitals = race["vitals"]
    route_text = " ".join(vitals["route_options"])

    assert vitals["distance_km"] == 138
    assert vitals["distance_mi"] == 85.7
    assert vitals["elevation_m"] == 2000
    assert vitals["elevation_ft"] == 6562
    assert "138 km" in route_text
    assert "120 km" in route_text
    assert "150 km" in route_text
    assert "rechecked before race week" in race["fondo_rating"]["scoring_notes"]


def test_granfondo_colombia_score_and_tier_follow_the_road_formula() -> None:
    rating = _race()["fondo_rating"]
    expected = round(
        (sum(rating[field] for field in SCORE_FIELDS) + rating["cultural_impact"])
        / 70
        * 100
    )

    assert expected == 60
    assert rating["overall_score"] == expected
    assert rating["tier"] == 2
    assert rating["tier_label"] == "TIER 2"


def test_granfondo_colombia_generated_pipeline_artifacts_are_current() -> None:
    readiness = json.loads((ROOT / "data" / "plan-readiness.json").read_text())
    sku_map = json.loads((ROOT / "data" / "tp-sku-map.json").read_text())
    race_pack = json.loads(
        (ROOT / "web" / "race-packs" / "granfondo-colombia.json").read_text()
    )
    index = json.loads((ROOT / "web" / "race-index.json").read_text())

    record = readiness["races"]["granfondo-colombia"]
    assert record["ready"] is True
    assert record["race_date"] == "2026-11-29"
    assert record["plan_clearance_status"] == "ready"
    assert sku_map["granfondo-colombia"] == "road-alpine-fondo"
    assert race_pack["demands"]["altitude"] == 8
    assert "8,300ft above sea level" in race_pack["race_overlay"]["altitude"]
    assert any(row["slug"] == "granfondo-colombia" for row in index)


def test_granfondo_colombia_uses_official_sources() -> None:
    urls = [citation["url"] for citation in _race()["citations"]]

    assert any("ucigranfondoworldseries.com" in url for url in urls)
    assert any("ucigranfondocolombia.com/recorridos" in url for url in urls)
    assert any("registroucigranfondocolombia" in url for url in urls)
