"""Official-source contract for DGI Hærvejsløbet 2027."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROFILE = ROOT / "race-data" / "letape-denmark.json"


def race() -> dict:
    return json.loads(PROFILE.read_text(encoding="utf-8"))["race"]


def test_haervejsloebet_has_the_organizer_confirmed_2027_date() -> None:
    profile = race()
    vitals = profile["vitals"]

    assert "2027: June 26" in vitals["date_specific"]
    assert vitals["distance_km"] == 300.0
    assert vitals["distance_mi"] == 186.4
    assert vitals["elevation_m"] == 2500
    assert vitals["route_options"][0].startswith("300 km road")
    assert "seven feed depots" in vitals["feed_zones"]


def test_haervejsloebet_is_blocked_on_2027_competition_and_course_facts() -> None:
    profile = race()
    review = profile["source_review"]
    clearance = profile["training_plan_clearance"]

    assert review["reviewed_at"] == "2026-08-14"
    assert review["race_date"] == "2027-06-26"
    assert "SOURCE BLOCKED" in review["plan_status"]
    assert clearance["status"] == "source_blocked"
    assert clearance["race_date"] == "2027-06-26"
    assert clearance["ladder"] == "FULL-7"
    assert clearance["variation"] == "Distance"
    assert len(clearance["blockers"]) == 1
    assert "timed competition format" in clearance["blockers"][0]
    assert "Do not project the 2026" in clearance["guard"]
    assert "source-blocked" in profile["eligibility"]["notes"]


def test_haervejsloebet_cites_first_party_date_and_route_sources() -> None:
    citations = {citation["url"] for citation in race()["citations"]}

    assert "https://sites.dgi.dk/haervejsloebet" in citations
    assert "https://denmark.letapeseries.com/stages" in citations
    assert "https://denmark.letapeseries.com/participant-information" in citations


def test_haervejsloebet_generated_pipeline_artifacts_are_current() -> None:
    readiness = json.loads((ROOT / "data" / "plan-readiness.json").read_text())
    sku_map = json.loads((ROOT / "data" / "tp-sku-map.json").read_text())
    race_pack = json.loads(
        (ROOT / "web" / "race-packs" / "letape-denmark.json").read_text()
    )
    race_dates = json.loads((ROOT / "web" / "race-dates.json").read_text())

    record = readiness["races"]["letape-denmark"]
    assert record["ready"] is False
    assert record["race_date"] == "2027-06-26"
    assert record["plan_clearance_status"] == "source_blocked"
    assert "timed competition format" in record["blockers"][0]
    assert sku_map["letape-denmark"] == "road-distance"
    assert race_pack["distance_mi"] == 186.4
    assert race_dates["letape-denmark"] == "2027-06-26"
