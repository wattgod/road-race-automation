"""Source-contract tests for the 2027 L'Ardéchoise plan target."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROFILE = ROOT / "race-data" / "lardechoise.json"
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


def test_lardechoise_targets_the_current_named_route() -> None:
    race = _race()
    vitals = race["vitals"]

    assert vitals["date"] == "June 12, 2027"
    assert vitals["date_specific"] == "2027: June 12"
    assert vitals["distance_km"] == 221
    assert vitals["distance_mi"] == 137.3
    assert vitals["elevation_m"] == 4415
    assert vitals["elevation_ft"] == 14485
    assert race["climb_profile"]["total_climbs"] == 10
    assert "Col de la Barricaude" in race["climb_profile"]["key_climbs"]


def test_lardechoise_score_and_tier_follow_the_road_formula() -> None:
    rating = _race()["fondo_rating"]
    expected = round(
        (sum(rating[field] for field in SCORE_FIELDS) + rating["cultural_impact"])
        / 70
        * 100
    )

    assert expected == 81
    assert rating["overall_score"] == expected
    assert rating["tier"] == 1
    assert rating["tier_label"] == "TIER 1"


def test_lardechoise_2027_date_is_explicitly_derived() -> None:
    race = _race()
    review = race["source_review"]

    assert race["eligibility"]["verified"] == "2026-08-10"
    assert review["reviewed_at"] == "2026-08-10"
    assert review["race_date"] == {
        "status": "derived_from_official_event_window_and_weekday",
        "value": "2027-06-12",
        "basis": review["race_date"]["basis"],
    }
    assert "June 8-12" in review["race_date"]["basis"]
    assert "Saturday June 12" in review["race_date"]["basis"]


def test_lardechoise_keeps_unpublished_2027_details_guarded() -> None:
    race = _race()
    vitals = race["vitals"]
    pending = race["source_review"]["facts_scope"]["pending"]

    assert "final 2027 route" in vitals["route_options"][-1].lower()
    assert "pending" in vitals["start_format"].lower()
    assert "not yet published" in vitals["registration"].lower()
    assert "pending" in vitals["feed_zones"].lower()
    assert "pending" in vitals["cutoff_time"].lower()
    assert len(pending) == 5


def test_lardechoise_removes_stale_flagship_claims() -> None:
    source = PROFILE.read_text(encoding="utf-8")

    for stale_claim in ("276.8", "5,370", "16 cols", "2027 dates not yet announced"):
        assert stale_claim not in source
