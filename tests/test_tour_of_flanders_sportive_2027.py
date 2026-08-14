"""Official-source contract for the 2027 We Ride Flanders edition."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROFILE = ROOT / "race-data" / "tour-of-flanders-sportive.json"


def race() -> dict:
    return json.loads(PROFILE.read_text(encoding="utf-8"))["race"]


def test_flanders_has_the_organizer_confirmed_2027_date() -> None:
    profile = race()
    assert profile["vitals"]["date_specific"] == (
        "2027: April 3 (Saturday, organizer-confirmed)"
    )
    assert profile["source_review"]["race_date"] == "2027-04-03"
    assert profile["source_review"]["reviewed_at"] == "2026-08-14"
    assert "CLEARED FOR FULL-7" in profile["source_review"]["plan_status"]


def test_current_course_framework_uses_the_live_organizer_figures() -> None:
    profile = race()
    assert profile["vitals"]["distance_km"] == 247.0
    assert profile["vitals"]["distance_mi"] == 153.5
    assert profile["vitals"]["elevation_m"] == 2100
    assert profile["vitals"]["elevation_ft"] == 6890.0
    assert [247, 163, 133, 79] == [
        int(option.split()[3 if option.startswith("Current") else 0])
        for option in profile["vitals"]["route_options"]
    ]


def test_final_2027_route_and_operations_are_not_claimed_as_published() -> None:
    profile = race()
    notes = profile["eligibility"]["notes"]
    scope = profile["source_review"]["facts_scope"]
    assert "final 2027 GPX" in notes
    assert "must override" in notes
    assert "Final 2027 GPX" in scope
    assert profile["vitals"]["entry_fee"] == "Not yet published for 2027"


def test_first_party_date_and_course_pages_are_cited() -> None:
    citations = {citation["url"] for citation in race()["citations"]}
    assert "https://werideflanders.com/en/practical-info/" in citations
    assert "https://werideflanders.com/en/course/" in citations
