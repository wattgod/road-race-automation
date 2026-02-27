"""Tests for the scoring system (recalculate_tiers.py)."""

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from recalculate_tiers import (
    calculate_tier,
    apply_prestige_override,
    recalculate_score,
    recalculate_race,
    SCORE_FIELDS,
    T1_THRESHOLD,
    T2_THRESHOLD,
    T3_THRESHOLD,
    P5_T1_FLOOR,
)


class TestCalculateTier:
    def test_t1_at_threshold(self):
        assert calculate_tier(80) == 1

    def test_t1_above(self):
        assert calculate_tier(95) == 1

    def test_t2_at_threshold(self):
        assert calculate_tier(60) == 2

    def test_t2_mid(self):
        assert calculate_tier(70) == 2

    def test_t3_at_threshold(self):
        assert calculate_tier(45) == 3

    def test_t4_below(self):
        assert calculate_tier(44) == 4

    def test_t4_zero(self):
        assert calculate_tier(0) == 4

    def test_t1_100(self):
        assert calculate_tier(100) == 1


class TestPrestigeOverride:
    def test_p5_high_score_promotes_to_t1(self):
        tier, reason = apply_prestige_override(2, 5, 80)
        assert tier == 1
        assert "Tier 1" in reason

    def test_p5_at_floor_promotes(self):
        tier, reason = apply_prestige_override(3, 5, 75)
        assert tier == 1

    def test_p5_below_floor_caps_at_t2(self):
        tier, reason = apply_prestige_override(3, 5, 70)
        assert tier == 2
        assert "Tier 2" in reason

    def test_p5_below_floor_already_t2(self):
        tier, reason = apply_prestige_override(2, 5, 70)
        assert tier == 2
        assert reason is None  # No change needed

    def test_p4_promotes_one_tier(self):
        tier, reason = apply_prestige_override(3, 4, 50)
        assert tier == 2
        assert "Prestige 4" in reason

    def test_p4_wont_promote_into_t1(self):
        tier, reason = apply_prestige_override(2, 4, 70)
        assert tier == 2  # Stays T2, not promoted to T1

    def test_p3_no_effect(self):
        tier, reason = apply_prestige_override(3, 3, 50)
        assert tier == 3
        assert reason is None

    def test_p0_no_effect(self):
        tier, reason = apply_prestige_override(4, 0, 30)
        assert tier == 4

    def test_p5_t4_below_floor(self):
        tier, reason = apply_prestige_override(4, 5, 60)
        assert tier == 2  # p5 caps at T2


class TestRecalculateScore:
    def test_all_fives(self):
        rating = {f: 5 for f in SCORE_FIELDS}
        assert recalculate_score(rating) == 100

    def test_all_ones(self):
        rating = {f: 1 for f in SCORE_FIELDS}
        assert recalculate_score(rating) == 20

    def test_all_threes(self):
        rating = {f: 3 for f in SCORE_FIELDS}
        assert recalculate_score(rating) == 60

    def test_with_cultural_impact(self):
        rating = {f: 3 for f in SCORE_FIELDS}
        rating["cultural_impact"] = 5
        score = recalculate_score(rating)
        assert score > 60  # CI should boost it

    def test_missing_field_treated_as_zero(self):
        rating = {f: 3 for f in SCORE_FIELDS[:-1]}  # Missing last dim
        score = recalculate_score(rating)
        assert score < 60  # Missing dim = 0

    def test_14_dimensions(self):
        """Verify we're scoring on exactly 14 dimensions."""
        assert len(SCORE_FIELDS) == 14


class TestRecalculateRace:
    def _make_profile(self, scores: dict, slug="test-race"):
        """Build a minimal valid profile dict."""
        rating = {f: scores.get(f, 3) for f in SCORE_FIELDS}
        rating.update({k: v for k, v in scores.items() if k not in SCORE_FIELDS})
        return {
            "race": {
                "name": "Test Race",
                "slug": slug,
                "fondo_rating": rating,
            }
        }

    def test_tier_assigned(self):
        data = self._make_profile({f: 5 for f in SCORE_FIELDS})
        change = recalculate_race(data, "test-race")
        assert change["new_tier"] == 1
        assert data["race"]["fondo_rating"]["tier"] == 1
        assert data["race"]["fondo_rating"]["tier_label"] == "TIER 1"

    def test_t4_race(self):
        data = self._make_profile({f: 1 for f in SCORE_FIELDS})
        change = recalculate_race(data, "test-race")
        assert change["new_tier"] == 4

    def test_discipline_preserved(self):
        data = self._make_profile({f: 3 for f in SCORE_FIELDS})
        data["race"]["fondo_rating"]["discipline"] = "hillclimb"
        change = recalculate_race(data, "test-race")
        assert change["discipline"] == "hillclimb"

    def test_discipline_defaults_to_gran_fondo(self):
        data = self._make_profile({f: 3 for f in SCORE_FIELDS})
        change = recalculate_race(data, "test-race")
        assert change["discipline"] == "gran_fondo"


class TestConfig:
    """Verify config/dimensions.json is well-formed."""

    def test_config_loads(self):
        config_path = Path(__file__).parent.parent / "config" / "dimensions.json"
        config = json.loads(config_path.read_text())
        assert "dimensions" in config
        assert len(config["dimensions"]) == 14

    def test_all_dimensions_have_rubrics(self):
        config_path = Path(__file__).parent.parent / "config" / "dimensions.json"
        config = json.loads(config_path.read_text())
        for dim in config["dimensions"]:
            assert "key" in dim, f"Missing key in dimension: {dim}"
            assert "rubric" in dim, f"Missing rubric for {dim['key']}"
            rubric = dim["rubric"]
            for level in ("1", "2", "3", "4", "5"):
                assert level in rubric, f"Missing level {level} in rubric for {dim['key']}"

    def test_tier_thresholds_ordered(self):
        config_path = Path(__file__).parent.parent / "config" / "dimensions.json"
        config = json.loads(config_path.read_text())
        thresholds = config["tier_thresholds"]
        assert thresholds["T1"] > thresholds["T2"] > thresholds["T3"] > thresholds["T4"]

    def test_disciplines_non_empty(self):
        config_path = Path(__file__).parent.parent / "config" / "dimensions.json"
        config = json.loads(config_path.read_text())
        assert len(config["disciplines"]) >= 3

    def test_prestige_5_events_listed(self):
        config_path = Path(__file__).parent.parent / "config" / "dimensions.json"
        config = json.loads(config_path.read_text())
        assert len(config["prestige_5_events"]) >= 5
