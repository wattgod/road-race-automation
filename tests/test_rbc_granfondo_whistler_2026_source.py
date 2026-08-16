"""Current-source contracts for RBC GranFondo Whistler 2026."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROFILE = ROOT / "race-data" / "rbc-granfondo-whistler.json"
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


def test_whistler_uses_current_2026_gran_fondo_facts() -> None:
    race = _race()
    vitals = race["vitals"]

    assert vitals["date"] == "Saturday, September 12, 2026"
    assert vitals["date_specific"] == "September 12, 2026 (Saturday)"
    assert vitals["distance_km"] == 122
    assert vitals["distance_mi"] == 76
    assert vitals["elevation_m"] == 2300
    assert vitals["elevation_ft"] == 7500
    assert "6:20am" in vitals["start_format"]
    assert "4 supported rest stops" in vitals["feed_zones"]
    assert "CA$499" in vitals["entry_fee"]
    assert race["eligibility"]["verified"] == "2026-08-15"


def test_whistler_records_current_2026_route_options() -> None:
    text = json.dumps(_race(), ensure_ascii=False)

    for fact in (
        "Forte: 146km / 2,712m",
        "limited to 600 riders",
        "Gran Fondo: 122km / 2,300m",
        "Medio: 55km / 835m",
        "Mt. Callaghan",
    ):
        assert fact in text

    for stale_fact in (
        "Forte: 152km",
        "3,100m",
        "limited to 550 riders",
        "Cypress Bowl Road",
        "CAD $280-330",
    ):
        assert stale_fact not in text


def test_whistler_preserves_cutoff_source_conflict_without_guessing() -> None:
    cutoff = _race()["vitals"]["cutoff_time"]

    assert "Alice Lake at 72.5km" in cutoff
    assert "prints the Alice Lake time as 11:50pm" in cutoff
    assert "Salt Shed at 88km by 12:45pm" in cutoff
    assert "Brandywine at 105km by 2:15pm" in cutoff
    assert "finish closes at 4:00pm" in cutoff
    assert "September 7 rider guide" in cutoff


def test_whistler_rating_remains_rubric_consistent() -> None:
    rating = _race()["fondo_rating"]
    expected = round(
        (sum(rating[field] for field in SCORE_FIELDS) + rating["cultural_impact"])
        / 70
        * 100
    )

    assert rating["overall_score"] == expected == 61
    assert rating["tier"] == 2
    assert rating["tier_label"] == "TIER 2"


def test_whistler_cites_current_official_sources() -> None:
    urls = [citation["url"] for citation in _race()["citations"]]

    assert "https://www.rbcgranfondo.com/event/whistler" in urls
    assert (
        "https://www.rbcgranfondo.com/event-resources/whistler/distances" in urls
    )
    assert (
        "https://www.rbcgranfondo.com/event-resources/whistler/rules-guidelines"
        in urls
    )
    assert "https://www.rbcgranfondo.com/event-resources/whistler/agenda" in urls
    assert (
        "https://raceroster.com/events/2026/109976/"
        "rbc-granfondo-whistler-2026"
    ) in urls


def test_whistler_generated_index_is_current() -> None:
    index = json.loads((ROOT / "web" / "race-index.json").read_text())
    row = next(record for record in index if record["slug"] == "rbc-granfondo-whistler")

    assert row["month"] == "September"
    assert row["distance_km"] == 122
    assert row["elevation_m"] == 2300
    assert row["overall_score"] == 61
    assert row["tier"] == 2


def test_whistler_retired_alias_cannot_create_a_second_fleet() -> None:
    index = json.loads((ROOT / "web" / "race-index.json").read_text())
    sku_map = json.loads((ROOT / "data" / "tp-sku-map.json").read_text())

    assert sum(row["slug"] == "rbc-granfondo-whistler" for row in index) == 1
    assert all(row["slug"] != "whistler-granfondo" for row in index)
    assert "whistler-granfondo" not in sku_map
    assert not (ROOT / "race-data" / "whistler-granfondo.json").exists()
    assert not (ROOT / "web" / "race-packs" / "whistler-granfondo.json").exists()
