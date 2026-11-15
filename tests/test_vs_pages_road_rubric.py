"""RL-05: vs pages must score races on the road rubric, never zero-fill."""

import json
import re
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "wordpress"))

import generate_vs_pages as vs  # noqa: E402

CONFIG = json.loads((REPO_ROOT / "config" / "dimensions.json").read_text())["dimensions"]
COURSE = [(d["key"], d["label"]) for d in CONFIG if d["category"] == "course"]
EDITORIAL = [(d["key"], d["label"]) for d in CONFIG if d["category"] == "editorial"]
GRAVEL_KEYS = {"length", "technicality", "elevation", "climate", "adventure",
               "race_quality", "experience", "community"}


def _race(slug, base, overall, **overrides):
    scores = {key: base for key, _ in COURSE + EDITORIAL}
    scores.update(overrides)
    return {"slug": slug, "name": slug.replace("-", " ").title(), "tier": 1,
            "overall_score": overall, "scores": scores, "location": "Somewhere",
            "month": "July", "tagline": "A road race.", "distance_mi": 100,
            "elevation_ft": 10000}


def _index_pairs():
    index = json.loads((REPO_ROOT / "web" / "race-index.json").read_text())
    race_map = {r["slug"]: r for r in index}
    return [(race_map[a], race_map[b]) for a, b in vs.select_pairs(index)[:25]]


def test_axes_come_from_road_rubric_config():
    assert vs.COURSE_DIMS == COURSE
    assert vs.EDITORIAL_DIMS == EDITORIAL
    assert not GRAVEL_KEYS & {k for k, _ in vs.ALL_DIMS}


def test_every_rubric_dimension_has_choose_if_copy():
    assert set(vs.CHOOSE_IF) == {k for k, _ in COURSE + EDITORIAL}


def test_radar_axes_and_scores_use_config_labels():
    a = _race("race-a", 3, 70, climbing=5)
    b = _race("race-b", 2, 60)
    svg = vs.build_radar_svg(a, b)
    labels = re.findall(r'dominant-baseline="middle">([^<]+)</text>', svg)
    assert labels == [vs.esc(label) for _, label in COURSE]
    assert "Climbing 5/5" in svg and "Climbing 2/5" in svg


def test_generated_pages_never_show_zero_scores():
    pairs = _index_pairs()
    assert pairs, "expected vs pairs from web/race-index.json"
    for race_a, race_b in pairs:
        html = vs.build_vs_page(race_a, race_b, {}, {})
        assert ":0 /" not in html, f"{race_a['slug']} vs {race_b['slug']} has a zero axis"
        assert " 0/5" not in html
        for gravel_label in ("LEN:", "TECH:", "ELEV:", "ADV:"):
            assert gravel_label not in html
        for key, _ in COURSE + EDITORIAL:
            assert f'data-dim="{key}"' in html


def test_verdict_uses_road_dimensions():
    a = _race("race-a", 3, 80, descent_technicality=5, expenses=5)
    b = _race("race-b", 3, 70, value=5)
    verdict = vs.build_verdict(a, b, {}, {})
    assert vs.CHOOSE_IF["descent_technicality"] in verdict
    assert vs.CHOOSE_IF["expenses"].replace("'", "&#x27;") in verdict
    assert vs.CHOOSE_IF["value"] in verdict


def test_race_missing_a_dimension_is_refused():
    a = _race("race-a", 3, 70)
    b = _race("race-b", 3, 70)
    del b["scores"]["road_surface"]
    with pytest.raises(vs.MissingScoreError, match="race-b.*road_surface"):
        vs.build_vs_page(a, b, {}, {})


@pytest.mark.parametrize("bad", [None, "", "n/a", 0, 6])
def test_unusable_score_is_refused_not_zeroed(bad):
    a = _race("race-a", 3, 70, climbing=bad)
    with pytest.raises(vs.MissingScoreError):
        vs.race_scores(a)


def test_string_scores_are_normalised():
    a = _race("race-a", "3.0", 70, climbing="4")
    scores = vs.race_scores(a)
    assert scores["climbing"] == 4 and scores["distance"] == 3


def test_missing_overall_score_is_refused():
    a = _race("race-a", 3, None)
    b = _race("race-b", 3, 70)
    with pytest.raises(vs.MissingScoreError, match="overall_score"):
        vs.build_vs_page(a, b, {}, {})
