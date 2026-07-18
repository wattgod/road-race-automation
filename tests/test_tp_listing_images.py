"""Acceptance tests for Roadie Labs TP listing and OG image generators."""

import json
from pathlib import Path

from scripts import generate_og_images as og
from scripts import generate_tp_listing_images as tp


REPO_ROOT = Path(__file__).resolve().parent.parent
CONFIG_DIMS = json.loads(
    (REPO_ROOT / "config" / "dimensions.json").read_text()
)["dimensions"]
GRAVEL_ONLY_DIMS = {
    "length",
    "technicality",
    "elevation",
    "climate",
    "adventure",
    "race_quality",
    "experience",
    "community",
}
ROAD_RENAMED_DIMS = {
    "distance",
    "descent_technicality",
    "climbing",
    "climate_risk",
    "road_surface",
    "organization",
    "scenic_experience",
    "community_culture",
}


def _rated_race(score=3):
    rating = {dimension["key"]: score for dimension in CONFIG_DIMS}
    rating.update({"overall_score": 60, "tier": 2})
    return {
        "slug": "roadie-test-race",
        "display_name": "Roadie Test Race",
        "vitals": {
            "location": "Boulder, Colorado",
            "distance_mi": 100,
            "date_specific": "2026: July 19",
        },
        "fondo_rating": rating,
    }


def test_dimensions_config_produces_fourteen_dims_split_seven_and_seven():
    loaded = tp.load_dimensions_config()

    assert len(loaded) == 14
    assert len(tp.COURSE_DIMS) == 7
    assert len(tp.OPINION_DIMS) == 7
    assert set(tp.COURSE_DIMS).isdisjoint(tp.OPINION_DIMS)
    assert tp.ALL_DIMS == [dimension["key"] for dimension in CONFIG_DIMS]
    assert tp.DIM_LABELS == {
        dimension["key"]: dimension["label"] for dimension in CONFIG_DIMS
    }


def test_all_fourteen_nonzero_dimensions_render_in_both_radars():
    image, alt = tp.build_header_image(_rated_race(score=3))

    assert image.mode == "RGB"
    assert image.width == tp.HEADER_W
    assert "Course 21/35" in alt
    assert "Editorial 21/35" in alt


def test_no_gravel_dimension_names_survive_in_tp_generator():
    configured = set(tp.COURSE_DIMS + tp.OPINION_DIMS)

    assert configured.isdisjoint(GRAVEL_ONLY_DIMS)
    assert ROAD_RENAMED_DIMS <= configured


def test_normal_render_palette_never_uses_oxblood():
    oxblood = (139, 26, 26)
    happy_path_colors = {
        tp.PAPER,
        tp.DARK_BROWN,
        tp.ACCENT,
        tp.ACCENT_DEEP,
        tp.RADAR_COURSE,
        tp.RADAR_EDITORIAL,
        tp.SAND,
    }

    assert oxblood not in happy_path_colors
    assert tp.PAPER == (245, 245, 240)
    assert tp.DARK_BROWN == (26, 26, 26)
    assert tp.RADAR_COURSE == (74, 74, 74)


def test_mental_program_tile_is_not_in_standard_tiles():
    assert len(tp.STANDARD_TILES) == 5
    assert all(icon_key != "mental" for icon_key, _ in tp.STANDARD_TILES)
    assert "mental" not in tp.ICON_DRAWERS


def test_og_dimensions_match_config_and_exclude_gravel_names():
    expected = [dimension["key"] for dimension in CONFIG_DIMS]

    assert og.ALL_DIMS == expected
    assert len(og.ALL_DIMS) == 14
    assert set(og.ALL_DIMS).isdisjoint(GRAVEL_ONLY_DIMS)
    assert ROAD_RENAMED_DIMS <= set(og.ALL_DIMS)


def test_tier_label_fallback_and_pending_domain_use_roadie_brand():
    race = _rated_race()
    assert tp._tier_label(race) == "TIER 2"

    pending = {
        "slug": "pending-road-race",
        "display_name": "Pending Road Race",
        "vitals": {},
    }
    _, alt = tp.build_header_image(pending)
    assert alt == "Pending Road Race — not yet rated by roadielabs.com."


def test_five_standard_tiles_still_form_a_complete_grid():
    image, alt = tp.build_includes_image(
        _rated_race(),
        plan_class="finisher",
        plan={"tier": "Finisher"},
        altitude_flag=False,
    )

    expected_rows = 3
    expected_height = (
        tp.TILE_MARGIN * 2
        + 70
        + expected_rows * tp.TILE_H
        + (expected_rows - 1) * tp.TILE_GAP
    )
    assert image.size == (tp.INCLUDES_W, expected_height)
    assert alt == ""
