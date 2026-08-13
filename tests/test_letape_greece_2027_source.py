"""Source and generated-artifact contracts for L'Étape Greece 2027."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROFILE = ROOT / "race-data" / "letape-greece.json"


def _race() -> dict:
    return json.loads(PROFILE.read_text(encoding="utf-8"))["race"]


def test_letape_greece_is_cleared_for_a_sunday_full_ladder() -> None:
    race = _race()
    vitals = race["vitals"]
    clearance = race["training_plan_clearance"]

    assert vitals["date"] == "April 4, 2027"
    assert vitals["distance_km"] == 140
    assert vitals["elevation_m"] == 1700
    assert vitals["cutoff_time"].startswith("7 hours for The Race")
    assert clearance["status"] == "ready"
    assert clearance["race_date"] == "2027-04-04"
    assert clearance["ladder"] == "FULL-7"
    assert clearance["variation"] == "Allrounder"
    assert clearance["blockers"] == []


def test_letape_greece_cites_current_official_sources() -> None:
    race = _race()
    urls = {citation["url"] for citation in race["citations"]}

    assert "https://greece.letapeseries.com/stages" in urls
    assert "https://greece.letapeseries.com/route/48" in urls
    assert "https://greece.letapeseries.com/rules" in urls
    assert "https://greece.letapeseries.com/registration" in urls
    assert race["eligibility"]["verified"] == "2026-08-13"


def test_letape_greece_generated_pipeline_artifacts_are_current() -> None:
    readiness = json.loads((ROOT / "data" / "plan-readiness.json").read_text())
    sku_map = json.loads((ROOT / "data" / "tp-sku-map.json").read_text())
    race_pack = json.loads(
        (ROOT / "web" / "race-packs" / "letape-greece.json").read_text()
    )
    race_dates = json.loads((ROOT / "web" / "race-dates.json").read_text())
    index = json.loads((ROOT / "web" / "race-index.json").read_text())

    record = readiness["races"]["letape-greece"]
    assert record["ready"] is True
    assert record["race_date"] == "2027-04-04"
    assert record["plan_clearance_status"] == "ready"
    assert sku_map["letape-greece"] == "road-allrounder"
    assert race_pack["distance_mi"] == 87
    assert race_pack["demands"]["threshold"] == 8
    assert race_dates["letape-greece"] == "2027-04-04"
    assert any(
        row["slug"] == "letape-greece"
        and row["location"] == "Sparta, Laconia, Peloponnese, Greece"
        for row in index
    )
