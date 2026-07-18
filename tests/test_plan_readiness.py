"""
Tests for qc/plan_readiness.py.

Fixture-based unit tests exercise each individual check in isolation. One
integration test runs the real generator against the live race-data/ corpus
and asserts the output is well-formed.
"""

import json
import sys
from datetime import date
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "qc"))

import plan_readiness  # noqa: E402

TODAY = date(2026, 7, 17)


def _base_race(**overrides):
    """A minimal race dict that passes every check by default."""
    race = {
        "name": "Fixture Fondo",
        "slug": "fixture-fondo",
        "display_name": "Fixture Fondo",
        "tagline": "A fixture race",
        "vitals": {
            "distance_km": 120,
            "distance_mi": 74.6,
            "location": "Fixtureville",
            "date": "2027: July",
            "date_specific": "2027: July 15",
        },
        "climate": {},
        "terrain": {},
        "fondo_rating": {
            "distance": 3,
            "climbing": 2,
            "descent_technicality": 2,
            "road_surface": 2,
            "climate_risk": 2,
            "altitude": 1,
            "logistics": 3,
            "prestige": 4,
            "organization": 4,
            "scenic_experience": 4,
            "community_culture": 3,
            "field_depth": 3,
            "value": 3,
            "expenses": 3,
            "cultural_impact": 2,
            "overall_score": 59,  # (39 dim sum + 2 cultural_impact) / 70 * 100, rounded
            "tier": 1,
            "tier_label": "TIER 1",
            "discipline": "gran_fondo",
            "prestige_override": None,
        },
        "climb_profile": {"needs_enrichment": False},
        "course_description": {
            "character": "Rolling countryside with a long false-flat finish.",
        },
        "logistics": {},
        "history": {},
        "biased_opinion": {
            "verdict": "Solid",
            "summary": "A genuinely fun day out with good organization.",
            "strengths": ["Well marked", "Good food stops"],
            "weaknesses": ["Pricey"],
        },
        "final_verdict": {"one_liner": "Worth doing once."},
        "citations": [
            {"url": "https://example.com/a", "category": "official", "label": "Official"},
            {"url": "https://example.com/b", "category": "press", "label": "Press"},
            {"url": "https://example.com/c", "category": "forum", "label": "Forum"},
        ],
        "eligibility": {
            "status": "active",
            "verified": "2026-07-17",
            "source": "https://example.com/official",
        },
    }
    for key, value in overrides.items():
        if value is None:
            race.pop(key, None)
        else:
            race[key] = value
    return race


def _write_fixture(tmp_path: Path, slug: str, race: dict) -> Path:
    path = tmp_path / f"{slug}.json"
    race = dict(race)
    race["slug"] = slug
    path.write_text(json.dumps({"race": race}, indent=2))
    return path


class TestIndividualChecks:
    def test_fully_ready_profile(self, tmp_path):
        path = _write_fixture(tmp_path, "ready-race", _base_race())
        record = plan_readiness.score_race(path, TODAY)
        assert record["checks"] == {
            "validator_clean": True,
            "editorial": True,
            "course_character": True,
            "future_date": True,
            "active_registerable": True,
        }
        assert record["ready"] is True
        assert record["blockers"] == []
        assert record["runway_weeks"] is not None and record["runway_weeks"] >= 0
        assert record["race_date"] == "2027-07-15"
        assert record["tier"] == 1
        assert record["score"] == 59
        assert record["eligibility_status"] == "active"

    def test_missing_editorial(self, tmp_path):
        race = _base_race(biased_opinion={"verdict": "Solid", "strengths": [], "weaknesses": []})
        path = _write_fixture(tmp_path, "no-editorial", race)
        record = plan_readiness.score_race(path, TODAY)
        assert record["checks"]["editorial"] is False
        assert record["ready"] is False
        assert any("editorial" in b for b in record["blockers"])

    def test_missing_course_character(self, tmp_path):
        race = _base_race(course_description={"character": ""})
        path = _write_fixture(tmp_path, "no-course-character", race)
        record = plan_readiness.score_race(path, TODAY)
        assert record["checks"]["course_character"] is False
        assert record["ready"] is False
        assert any("course_character" in b for b in record["blockers"])

    def test_validator_error_blocks_ready(self, tmp_path):
        race = _base_race()
        race["vitals"] = dict(race["vitals"])
        race["vitals"].pop("location")
        path = _write_fixture(tmp_path, "validator-error", race)
        record = plan_readiness.score_race(path, TODAY)
        assert record["checks"]["validator_clean"] is False
        assert record["ready"] is False
        assert any(b.startswith("validator: 1 error") for b in record["blockers"])

    def test_past_date_has_no_runway(self, tmp_path):
        race = _base_race()
        race["vitals"] = dict(race["vitals"])
        race["vitals"]["date_specific"] = "2020: May 3"
        path = _write_fixture(tmp_path, "past-date", race)
        record = plan_readiness.score_race(path, TODAY)
        assert record["checks"]["future_date"] is False
        assert record["runway_weeks"] is None
        assert record["ready"] is False
        assert "no parsed future date" in record["blockers"]

    def test_missing_eligibility_defaults_unknown(self, tmp_path):
        race = _base_race(eligibility=None)
        path = _write_fixture(tmp_path, "no-eligibility", race)
        record = plan_readiness.score_race(path, TODAY)
        assert record["eligibility_status"] == "unknown"
        assert record["checks"]["active_registerable"] is False
        assert record["ready"] is False
        assert "eligibility unverified (unknown)" in record["blockers"]

    def test_defunct_eligibility_blocks_ready(self, tmp_path):
        race = _base_race(
            eligibility={"status": "defunct", "verified": "2026-07-17", "source": "https://example.com"}
        )
        path = _write_fixture(tmp_path, "defunct-race", race)
        record = plan_readiness.score_race(path, TODAY)
        assert record["eligibility_status"] == "defunct"
        assert record["checks"]["active_registerable"] is False
        assert record["ready"] is False
        assert "eligibility: defunct" in record["blockers"]

    def test_cancelled_eligibility_blocks_ready(self, tmp_path):
        race = _base_race(
            eligibility={"status": "cancelled", "verified": "2026-07-17", "source": "https://example.com"}
        )
        path = _write_fixture(tmp_path, "cancelled-race", race)
        record = plan_readiness.score_race(path, TODAY)
        assert record["eligibility_status"] == "cancelled"
        assert record["checks"]["active_registerable"] is False
        assert "eligibility: cancelled" in record["blockers"]

    def test_active_without_provenance_blocks_ready(self, tmp_path):
        """status=active alone is not enough — verified/source must both be present.
        Regression test for a bug an adversarial review caught: {"status": "active"}
        with no citation used to pass active_registerable."""
        race = _base_race(eligibility={"status": "active"})
        path = _write_fixture(tmp_path, "active-no-provenance", race)
        record = plan_readiness.score_race(path, TODAY)
        assert record["eligibility_status"] == "active"
        assert record["checks"]["active_registerable"] is False
        assert record["ready"] is False
        assert any("missing verified/source provenance" in b for b in record["blockers"])

    def test_active_with_only_verified_no_source_blocks_ready(self, tmp_path):
        race = _base_race(eligibility={"status": "active", "verified": "2026-07-17"})
        path = _write_fixture(tmp_path, "active-no-source", race)
        record = plan_readiness.score_race(path, TODAY)
        assert record["checks"]["active_registerable"] is False

    def test_race_today_counts_as_future(self, tmp_path):
        """race_date == today is treated as future/runway=0 by design (not a bug —
        a race happening today still has a plan-readiness runway of 0 weeks)."""
        race = _base_race()
        race["vitals"] = dict(race["vitals"])
        race["vitals"]["date_specific"] = "2026: July 17"  # == TODAY
        path = _write_fixture(tmp_path, "race-today", race)
        record = plan_readiness.score_race(path, TODAY)
        assert record["checks"]["future_date"] is True
        assert record["runway_weeks"] == 0

    def test_runway_exactly_eight_weeks_is_pilot_eligible(self, tmp_path):
        race = _base_race()
        race["vitals"] = dict(race["vitals"])
        race["vitals"]["date_specific"] = "2026: September 11"  # exactly 8wk from Jul 17 2026
        path = _write_fixture(tmp_path, "exactly-8wk", race)
        record = plan_readiness.score_race(path, TODAY)
        assert record["runway_weeks"] == 8

    def test_malformed_eligibility_not_a_dict(self, tmp_path):
        race = _base_race()
        race["eligibility"] = "active"  # malformed: string instead of dict
        path = _write_fixture(tmp_path, "malformed-eligibility", race)
        record = plan_readiness.score_race(path, TODAY)
        assert record["eligibility_status"] == "unknown"
        assert record["checks"]["active_registerable"] is False


class TestBuildAggregate:
    def test_ranked_queue_orders_by_runway_times_rating(self, tmp_path):
        high = _base_race()
        high["vitals"] = dict(high["vitals"])
        high["vitals"]["date_specific"] = "2027: December 1"  # long runway
        high["fondo_rating"] = dict(high["fondo_rating"])
        high["fondo_rating"]["overall_score"] = 90

        low = _base_race()
        low["vitals"] = dict(low["vitals"])
        low["vitals"]["date_specific"] = "2026: August 1"  # short runway (~2wk from Jul 17 2026)
        low["fondo_rating"] = dict(low["fondo_rating"])
        low["fondo_rating"]["overall_score"] = 60

        _write_fixture(tmp_path, "high-priority", high)
        _write_fixture(tmp_path, "low-priority", low)

        payload = plan_readiness.build(tmp_path, today=TODAY)
        assert payload["ranked_queue"].index("high-priority") < payload["ranked_queue"].index("low-priority")

    def test_pilot_candidates_filter(self, tmp_path):
        # Tier 1, ready, runway >= 8wk -> included
        good = _base_race()
        good["vitals"] = dict(good["vitals"])
        good["vitals"]["date_specific"] = "2027: December 1"
        _write_fixture(tmp_path, "pilot-good", good)

        # Tier 3, otherwise ready -> excluded (tier)
        tier3 = _base_race()
        tier3["vitals"] = dict(tier3["vitals"])
        tier3["vitals"]["date_specific"] = "2027: December 1"
        tier3["fondo_rating"] = dict(tier3["fondo_rating"])
        tier3["fondo_rating"]["tier"] = 3
        _write_fixture(tmp_path, "pilot-tier3", tier3)

        # Tier 1, ready, runway < 8wk -> excluded (runway)
        short_runway = _base_race()
        short_runway["vitals"] = dict(short_runway["vitals"])
        short_runway["vitals"]["date_specific"] = "2026: July 25"  # ~1wk out
        _write_fixture(tmp_path, "pilot-short-runway", short_runway)

        # Tier 1, runway ok, but eligibility unverified -> excluded (not ready)
        not_ready = _base_race(eligibility=None)
        not_ready["vitals"] = dict(not_ready["vitals"])
        not_ready["vitals"]["date_specific"] = "2027: December 1"
        _write_fixture(tmp_path, "pilot-not-ready", not_ready)

        payload = plan_readiness.build(tmp_path, today=TODAY)
        assert "pilot-good" in payload["pilot_candidates"]
        assert "pilot-tier3" not in payload["pilot_candidates"]
        assert "pilot-short-runway" not in payload["pilot_candidates"]
        assert "pilot-not-ready" not in payload["pilot_candidates"]

    def test_summary_counts(self, tmp_path):
        _write_fixture(tmp_path, "one", _base_race())
        race2 = _base_race(biased_opinion={"verdict": "x", "strengths": [], "weaknesses": []})
        _write_fixture(tmp_path, "two", race2)
        payload = plan_readiness.build(tmp_path, today=TODAY)
        assert payload["summary"]["total"] == 2
        assert payload["summary"]["content_present"] == 1
        assert payload["summary"]["ready"] == 1


class TestDeterminism:
    def test_build_is_deterministic(self, tmp_path):
        _write_fixture(tmp_path, "a", _base_race())
        _write_fixture(tmp_path, "b", _base_race())
        p1 = plan_readiness.build(tmp_path, today=TODAY)
        p2 = plan_readiness.build(tmp_path, today=TODAY)
        p1.pop("generated_at")
        p2.pop("generated_at")
        assert p1 == p2


class TestIntegration:
    def test_real_corpus_well_formed(self):
        payload = plan_readiness.build()
        assert payload["summary"]["total"] == 427
        real_slugs = {p.stem for p in (PROJECT_ROOT / "race-data").glob("*.json")}
        assert set(payload["races"].keys()) == real_slugs
        for slug in payload["ranked_queue"]:
            assert slug in payload["races"]
        for slug in payload["pilot_candidates"]:
            assert payload["races"][slug]["ready"] is True
            assert payload["races"][slug]["tier"] in (1, 2)
            assert (payload["races"][slug]["runway_weeks"] or 0) >= plan_readiness.PILOT_MIN_RUNWAY_WEEKS
