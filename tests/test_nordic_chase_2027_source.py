"""Official-source and commerce-gate contract for Nordic Chase road races."""

from __future__ import annotations

import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "wordpress"))
sys.path.insert(0, str(ROOT / "scripts"))

from audit_spine_v2_catalog import audit_page
from generate_neo_brutalist import generate_page, normalize_race_data


DIMENSIONS = (
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
RACES = {
    "nordic-chase-berlin-copenhagen-road": {
        "name": "Nordic Chase Berlin to Copenhagen Road",
        "location": "Berlin, Germany to Copenhagen, Denmark",
        "distance_km": 710,
        "elevation_m": 2670,
        "window": "2027 event window: June 5-10",
        "score": 54,
        "tier": 3,
        "official_page": "https://nordicchase.com/ber-cph-road",
    },
    "nordic-chase-copenhagen-oslo-road": {
        "name": "Nordic Chase Copenhagen to Oslo Road",
        "location": "Copenhagen, Denmark to Oslo, Norway",
        "distance_km": 726,
        "elevation_m": 5200,
        "window": "2027 event window: June 18-24",
        "score": 60,
        "tier": 2,
        "official_page": "https://nordicchase.com/cph-osl-road",
    },
}


def _raw(slug: str) -> dict:
    return json.loads(
        (ROOT / "race-data" / f"{slug}.json").read_text(encoding="utf-8")
    )


def test_nordic_chase_road_routes_are_distinct_and_honestly_graded() -> None:
    for slug, expected in RACES.items():
        race = _raw(slug)["race"]
        vitals = race["vitals"]
        rating = race["fondo_rating"]

        assert race["name"] == expected["name"]
        assert vitals["location"] == expected["location"]
        assert vitals["distance_km"] == expected["distance_km"]
        assert vitals["elevation_m"] == expected["elevation_m"]
        assert vitals["date_specific"].startswith("TBD —")
        assert expected["window"] in vitals["date_specific"]
        assert race["logistics"]["official_site"] == expected["official_page"]
        assert rating["overall_score"] == expected["score"]
        assert rating["tier"] == expected["tier"]
        assert round(
            (sum(rating[key] for key in DIMENSIONS) + rating["cultural_impact"])
            / 70
            * 100
        ) == expected["score"]
        assert rating["discipline"] == "gran_fondo"
        assert "road-ultra category" in race["catalog_flags"]["status_note"]


def test_nordic_chase_road_plans_remain_source_blocked() -> None:
    for slug in RACES:
        race = _raw(slug)["race"]
        clearance = race["training_plan_clearance"]

        assert race["eligibility"]["status"] == "active"
        assert race["eligibility"]["verified"] == "2026-08-15"
        assert race["vitals"]["course_status"] == "source_blocked"
        assert race["source_review"]["race_date"] is None
        assert clearance["status"] == "source_blocked"
        assert clearance["race_date"] is None
        assert clearance["ladder"] == "FULL-7"
        assert clearance["variation"] == "Distance"
        assert "exact grand-depart date" in clearance["blockers"][0]
        assert "Do not project the completed 2026" in clearance["guard"]


def test_source_blocked_road_guides_do_not_sell_a_race_specific_plan() -> None:
    index = json.loads((ROOT / "web" / "race-index.json").read_text(encoding="utf-8"))

    for slug in RACES:
        rd = normalize_race_data(_raw(slug))
        html = generate_page(rd, index)

        assert "PLAN DETAILS PENDING" in html
        assert "The race guide remains available" in html
        assert "START MY CUSTOM PLAN" not in html
        assert 'data-cta="approved_custom_plan"' not in html
        assert 'data-cta="prep_strip_build"' not in html
        assert f"training-plans/?race={slug}" not in html
        assert '"@type":"SportsEvent"' not in html
        assert "data-race-date=" not in html


def test_source_blocked_guides_pass_the_commerce_aware_spine_audit(tmp_path) -> None:
    index = json.loads((ROOT / "web" / "race-index.json").read_text(encoding="utf-8"))

    for slug in RACES:
        page = tmp_path / f"{slug}.html"
        page.write_text(
            generate_page(normalize_race_data(_raw(slug)), index),
            encoding="utf-8",
        )
        assert audit_page(page) == []


def test_generated_catalog_artifacts_include_guides_but_no_false_dates() -> None:
    index = json.loads((ROOT / "web" / "race-index.json").read_text(encoding="utf-8"))
    dates = json.loads((ROOT / "web" / "race-dates.json").read_text(encoding="utf-8"))
    readiness = json.loads((ROOT / "data" / "plan-readiness.json").read_text())
    rows = {row["slug"]: row for row in index if row["slug"] in RACES}

    assert set(rows) == set(RACES)
    for slug, expected in RACES.items():
        assert rows[slug]["name"] == expected["name"]
        assert rows[slug]["overall_score"] == expected["score"]
        assert slug not in dates
        record = readiness["races"][slug]
        assert record["ready"] is False
        assert record["race_date"] is None
        assert record["plan_clearance_status"] == "source_blocked"
