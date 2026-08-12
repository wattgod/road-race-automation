import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_epic_gran_canaria_is_cleared_for_a_two_day_plan_ladder():
    race = json.loads(
        (ROOT / "race-data/epic-gran-canaria.json").read_text(encoding="utf-8")
    )["race"]
    clearance = race["training_plan_clearance"]

    assert race["fondo_rating"]["overall_score"] == 67
    assert race["fondo_rating"]["tier"] == 2
    assert clearance["status"] == "ready"
    assert clearance["race_date"] == "2027-02-13"
    assert clearance["event_end_date"] == "2027-02-14"
    assert clearance["ladder"] == "FULL-7"
    assert clearance["variation"] == "Alpine-Fondo"
    assert "planning-demand references only" in clearance["guard"]
    assert "Final 2027" in clearance["guard"]


def test_epic_gran_canaria_preserves_source_uncertainty():
    serialized = (ROOT / "race-data/epic-gran-canaria.json").read_text(encoding="utf-8")

    assert '"elevation_m": null' in serialized
    assert '"elevation_ft": null' in serialized
    assert "2026 stage details" not in json.loads(serialized)["race"][
        "training_plan_clearance"
    ].get("blockers", [])
