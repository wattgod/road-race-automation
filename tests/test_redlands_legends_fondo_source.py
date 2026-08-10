"""Source-contract tests for the Redlands Legends' Fondo catalog target."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROFILE = ROOT / "race-data" / "redlands-bicycle-classic.json"


def _race() -> dict:
    return json.loads(PROFILE.read_text(encoding="utf-8"))["race"]


def test_redlands_target_is_the_legends_fondo() -> None:
    race = _race()

    assert race["display_name"] == "Redlands Bicycle Classic — Legends' Fondo"
    assert race["eligibility"]["status"] == "active"
    assert "not a race" in race["eligibility"]["notes"]
    assert "separate events" in race["final_verdict"]["should_you_race"]
    assert race["training_plan_clearance"]["status"] == "excluded"


def test_redlands_uses_current_2026_fondo_route_facts() -> None:
    vitals = _race()["vitals"]

    assert vitals["date"] == "April 11, 2026 (latest confirmed Legends' Fondo)"
    assert vitals["distance_mi"] == 67.5
    assert vitals["distance_km"] == 108.6
    assert vitals["elevation_ft"] == 5778.0
    assert vitals["elevation_m"] == 1761
    assert vitals["route_options"] == [
        "Gran Route: 67.5 miles / 5,778 ft — organizer-linked 2026 route",
        "Medio Route: 52.1 miles — organizer-linked 2026 route",
        "Percosa Route: 40.4 miles — organizer-linked 2026 route",
        "Taste of Redlands Route: 15 miles — organizer-linked 2026 route",
    ]


def test_redlands_does_not_promote_the_pro_window_to_a_fondo_date() -> None:
    review = _race()["source_review"]

    assert review["reviewed_at"] == "2026-08-10"
    assert review["race_date"]["status"] == "pending_official_fondo_announcement"
    assert review["race_date"]["value"] is None
    assert "professional riders" in review["race_date"]["basis"]


def test_redlands_cites_the_organizer_nonrace_statement() -> None:
    citations = _race()["citations"]

    assert any(
        "not a race" in citation["label"].lower()
        and citation["url"].startswith("https://redlandsclassic.com/")
        for citation in citations
    )
