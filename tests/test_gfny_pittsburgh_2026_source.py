"""Current-source contracts for GFNY Pittsburgh 2026."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROFILE = ROOT / "race-data" / "gfny-pittsburgh.json"
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


def test_gfny_pittsburgh_uses_current_2026_linked_route() -> None:
    race = _race()
    vitals = race["vitals"]

    assert vitals["date_specific"] == "2026: September 20"
    assert vitals["distance_km"] == 120.4
    assert vitals["distance_mi"] == 74.8
    assert vitals["elevation_m"] == 2507
    assert vitals["elevation_ft"] == 8226
    assert vitals["location"] == "Monroeville, Pennsylvania, USA"
    assert "CCAC Boyce Campus" in vitals["start_format"]
    assert "120.39 km / 74.8 miles" in vitals["route_options"][0]
    assert "2,507 m / 8,226 feet" in vitals["route_options"][0]
    assert "71.56 km / 44.5 miles" in vitals["route_options"][1]
    assert "1,523 m / 4,995 feet" in vitals["route_options"][1]
    assert race["eligibility"]["verified"] == "2026-08-15"


def test_gfny_pittsburgh_preserves_current_operational_limits() -> None:
    race = _race()
    vitals = race["vitals"]
    text = json.dumps(race, ensure_ascii=False)

    assert "7:30am" in vitals["start_format"]
    assert "corrals close at 7:15am" in vitals["start_format"]
    assert "11:10am cutoff" in vitals["cutoff_time"]
    assert "2:00pm" in vitals["cutoff_time"]
    assert "$199 standard plus $16.92 fee" in vitals["entry_fee"]
    assert "limited Sunday-morning spots" in race["logistics"]["transport"]
    assert "normal traffic rules" in race["eligibility"]["notes"] or (
        "traffic controls" in race["terrain"]["surface"]
    )
    assert "Old Leechburg Road" in text
    assert "second pass through the 29-mile climbing loop" in text
    assert "79.9-mile route features" not in text
    assert "10 signature climbs" not in text
    assert "Final entry fees not disclosed" not in text
    assert "full police escort" not in text


def test_gfny_pittsburgh_regrade_follows_the_rubric() -> None:
    rating = _race()["fondo_rating"]
    expected = round(
        (sum(rating[field] for field in SCORE_FIELDS) + rating["cultural_impact"])
        / 70
        * 100
    )

    assert rating["distance"] == 3
    assert rating["climbing"] == 4
    assert rating["descent_technicality"] == 3
    assert rating["road_surface"] == 2
    assert rating["organization"] == 2
    assert rating["logistics"] == 2
    assert rating["cultural_impact"] == 0
    assert rating["overall_score"] == expected == 51
    assert rating["tier"] == 3
    assert rating["tier_label"] == "TIER 3"


def test_gfny_pittsburgh_cites_current_official_sources() -> None:
    urls = [citation["url"] for citation in _race()["citations"]]

    assert "https://pgh.gfny.com/course/" in urls
    assert "https://ridewithgps.com/routes/48724947" in urls
    assert "https://ridewithgps.com/routes/48590191" in urls
    assert "https://pgh.gfny.com/schedule-of-events/" in urls
    assert "https://pgh.gfny.com/rules/" in urls
    assert any("gfny.cc/next/iframe?id=371" in url for url in urls)
    assert "https://pgh.gfny.com/hotels/" in urls
    assert "https://pgh.gfny.com/getting-here/" in urls


def test_gfny_pittsburgh_generated_artifacts_are_current() -> None:
    readiness = json.loads((ROOT / "data" / "plan-readiness.json").read_text())
    sku_map = json.loads((ROOT / "data" / "tp-sku-map.json").read_text())
    race_pack = json.loads(
        (ROOT / "web" / "race-packs" / "gfny-pittsburgh.json").read_text()
    )
    index = json.loads((ROOT / "web" / "race-index.json").read_text())
    row = next(record for record in index if record["slug"] == "gfny-pittsburgh")

    ready = readiness["races"]["gfny-pittsburgh"]
    assert ready["ready"] is True
    assert ready["race_date"] == "2026-09-20"
    assert ready["score"] == 51
    assert ready["tier"] == 3
    assert sku_map["gfny-pittsburgh"] == "road-alpine-fondo"

    pack_text = json.dumps(race_pack, ensure_ascii=False)
    assert race_pack["distance_mi"] == 74.8
    assert "8,226" in pack_text
    assert "8,701" not in pack_text
    assert "79.9" not in pack_text

    assert row["month"] == "September"
    assert row["distance_km"] == 120.4
    assert row["elevation_m"] == 2507
    assert row["overall_score"] == 51
    assert row["tier"] == 3
