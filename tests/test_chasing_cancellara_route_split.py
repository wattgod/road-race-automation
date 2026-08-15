"""Official-source and commerce-gate contract for Chasing Cancellara routes."""

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
    "chasing-cancellara-granfondo-vaduz": {
        "name": "Chasing Cancellara Granfondo Vaduz",
        "distance_km": 98,
        "elevation_m": 1290,
        "score": 53,
        "tier": 3,
        "variation": "Climbing",
        "official_page": "https://www.chasingcancellara.com/granfondo-vaduz",
    },
    "chasing-cancellara-zurich-andermatt": {
        "name": "Chasing Cancellara Zürich to Andermatt",
        "distance_km": 203.5,
        "elevation_m": 4335,
        "score": 74,
        "tier": 2,
        "variation": "Climbing",
        "official_page": "https://www.chasingcancellara.com/zurich-andermatt",
    },
    "chasing-cancellara-bern-zermatt": {
        "name": "Chasing Cancellara Bern to Zermatt",
        "distance_km": 274,
        "elevation_m": None,
        "score": 73,
        "tier": 2,
        "variation": "Ultra",
        "official_page": "https://www.chasingcancellara.com/bern-zermatt",
    },
}


def _raw(slug: str) -> dict:
    return json.loads(
        (ROOT / "race-data" / f"{slug}.json").read_text(encoding="utf-8")
    )


def test_generic_series_profile_is_replaced_by_three_exact_routes() -> None:
    assert not (ROOT / "race-data" / "chasing-cancellara.json").exists()
    assert not (ROOT / "web" / "race-packs" / "chasing-cancellara.json").exists()

    for slug, expected in RACES.items():
        race = _raw(slug)["race"]
        rating = race["fondo_rating"]

        assert race["name"] == expected["name"]
        assert race["vitals"]["distance_km"] == expected["distance_km"]
        assert race["vitals"]["elevation_m"] == expected["elevation_m"]
        assert race["logistics"]["official_site"] == expected["official_page"]
        assert rating["overall_score"] == expected["score"]
        assert rating["tier"] == expected["tier"]
        assert round(
            (sum(rating[key] for key in DIMENSIONS) + rating["cultural_impact"])
            / 70
            * 100
        ) == expected["score"]
        assert rating["discipline"] == "gran_fondo"


def test_routes_are_source_blocked_until_a_next_edition_is_announced() -> None:
    for slug, expected in RACES.items():
        race = _raw(slug)["race"]
        clearance = race["training_plan_clearance"]

        assert race["eligibility"]["status"] == "active"
        assert race["eligibility"]["verified"] == "2026-08-15"
        assert race["vitals"]["course_status"] == "source_blocked"
        assert race["source_review"]["race_date"] is None
        assert clearance["status"] == "source_blocked"
        assert clearance["race_date"] is None
        assert clearance["ladder"] == "FULL-7"
        assert clearance["variation"] == expected["variation"]
        assert "No organizer-confirmed next-edition" in clearance["blockers"][0]


def test_bern_zermatt_does_not_invent_an_elevation_total() -> None:
    source = (
        ROOT / "race-data" / "chasing-cancellara-bern-zermatt.json"
    ).read_text(encoding="utf-8")
    race = json.loads(source)["race"]

    assert race["vitals"]["elevation_m"] is None
    assert race["vitals"]["elevation_ft"] is None
    assert race["climb_profile"]["total_climbs"] is None
    assert "5,500" not in source
    assert "18,045" not in source


def test_source_blocked_guides_train_without_selling_a_race_plan(tmp_path) -> None:
    index = json.loads((ROOT / "web" / "race-index.json").read_text(encoding="utf-8"))

    for slug in RACES:
        html = generate_page(normalize_race_data(_raw(slug)), index)
        page = tmp_path / f"{slug}.html"
        page.write_text(html, encoding="utf-8")

        assert 'id="train-for-race"' in html
        assert "PLAN DETAILS PENDING" in html
        assert "The race guide remains available" in html
        assert "START MY CUSTOM PLAN" not in html
        assert 'data-cta="approved_custom_plan"' not in html
        assert 'data-cta="prep_strip_build"' not in html
        assert f"training-plans/?race={slug}" not in html
        assert '"@type":"SportsEvent"' not in html
        assert "data-race-date=" not in html
        assert audit_page(page) == []


def test_catalog_artifacts_replace_the_generic_series_identity() -> None:
    index = json.loads((ROOT / "web" / "race-index.json").read_text(encoding="utf-8"))
    readiness = json.loads((ROOT / "data" / "plan-readiness.json").read_text())
    race_dates = json.loads((ROOT / "web" / "race-dates.json").read_text())
    sku_map = json.loads((ROOT / "data" / "tp-sku-map.json").read_text())
    rows = {row["slug"]: row for row in index}

    assert "chasing-cancellara" not in rows
    assert "chasing-cancellara" not in readiness["races"]
    assert "chasing-cancellara" not in race_dates
    assert "chasing-cancellara" not in sku_map

    for slug, expected in RACES.items():
        assert rows[slug]["name"] == expected["name"]
        assert rows[slug]["overall_score"] == expected["score"]
        assert (ROOT / "web" / "race-packs" / f"{slug}.json").is_file()
        assert slug not in race_dates
        assert slug in sku_map
        record = readiness["races"][slug]
        assert record["ready"] is False
        assert record["race_date"] is None
        assert record["plan_clearance_status"] == "source_blocked"


def test_generic_urls_redirect_to_the_flagship_route() -> None:
    redirects = (ROOT / "web" / "htaccess-root").read_text(encoding="utf-8")
    deploy_source = (ROOT / "scripts" / "push_wordpress.py").read_text(
        encoding="utf-8"
    )

    exact_rule = (
        "RewriteRule ^race/chasing-cancellara/?$ "
        "/race/chasing-cancellara-bern-zermatt/ [R=301,L]"
    )
    subpath_rule = (
        "RewriteRule ^race/chasing-cancellara/(.*)$ "
        "/race/chasing-cancellara-bern-zermatt/$1 [R=301,L]"
    )

    assert exact_rule in redirects
    assert subpath_rule in redirects
    assert exact_rule in deploy_source
    assert subpath_rule in deploy_source
