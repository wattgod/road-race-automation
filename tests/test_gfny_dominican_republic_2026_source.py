"""Current-source contracts for GFNY Dominican Republic 2026."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROFILE = ROOT / "race-data" / "gfny-dominican-republic.json"
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


def test_gfny_dominican_republic_uses_current_2026_course() -> None:
    race = _race()
    vitals = race["vitals"]

    assert vitals["date_specific"] == "2026: September 13 (Sunday)"
    assert vitals["distance_km"] == 144.6
    assert vitals["distance_mi"] == 89.9
    assert vitals["elevation_m"] == 647
    assert vitals["elevation_ft"] == 2123
    assert vitals["location"] == "Punta Cana, Dominican Republic"
    assert "Caribbean Lake Park" in vitals["start_format"]
    assert "Long: 144.6 km" in vitals["route_options"][0]
    assert "Medium: 95.9 km" in vitals["route_options"][1]
    assert race["eligibility"]["verified"] == "2026-08-15"


def test_gfny_dominican_republic_preserves_operational_limits() -> None:
    race = _race()
    vitals = race["vitals"]
    text = json.dumps(race, ensure_ascii=False)

    assert "corrals close at 6:15am" in vitals["start_format"]
    assert "starts at 6:30am" in vitals["start_format"]
    assert "$185 standard entry" in vitals["entry_fee"]
    assert "$18.50 service fee" in vitals["entry_fee"]
    assert "No rider cutoff is published" in vitals["cutoff_time"]
    assert "estimate is not a stated cutoff" in vitals["cutoff_time"]
    assert "cannot race without their packet" in vitals["registration"]
    assert "GFNY jersey is mandatory" in vitals["registration"]
    assert "conflict" in race["eligibility"]["notes"]
    assert "Blue Mall" not in text
    assert "67km" not in text
    assert "149.7km" not in text
    assert "93.8km" not in text


def test_gfny_dominican_republic_regrade_follows_the_rubric() -> None:
    rating = _race()["fondo_rating"]
    expected = round(
        (sum(rating[field] for field in SCORE_FIELDS) + rating["cultural_impact"])
        / 70
        * 100
    )

    assert rating["distance"] == 3
    assert rating["climbing"] == 2
    assert rating["logistics"] == 1
    assert rating["organization"] == 2
    assert rating["road_surface"] == 2
    assert rating["overall_score"] == expected == 51
    assert rating["tier"] == 3
    assert rating["tier_label"] == "TIER 3"


def test_gfny_dominican_republic_cites_current_official_sources() -> None:
    urls = [citation["url"] for citation in _race()["citations"]]

    assert "https://gfny.com/gfny-relaunches-gfny-punta-cana-for-2026-season/" in urls
    assert "https://puntacana.gfny.com/course/?lang=en" in urls
    assert "https://puntacana.gfny.com/schedule-of-events/?lang=en" in urls
    assert "https://puntacana.gfny.com/rules/?lang=en" in urls
    assert any("gfny.cc/next/iframe?id=369" in url for url in urls)
    assert "https://puntacana.gfny.com/getting-here/?lang=en" in urls


def test_gfny_dominican_republic_generated_artifacts_are_current() -> None:
    readiness = json.loads((ROOT / "data" / "plan-readiness.json").read_text())
    sku_map = json.loads((ROOT / "data" / "tp-sku-map.json").read_text())
    race_pack = json.loads(
        (ROOT / "web" / "race-packs" / "gfny-dominican-republic.json").read_text()
    )
    index = json.loads((ROOT / "web" / "race-index.json").read_text())
    row = next(record for record in index if record["slug"] == "gfny-dominican-republic")

    ready = readiness["races"]["gfny-dominican-republic"]
    assert ready["ready"] is True
    assert ready["race_date"] == "2026-09-13"
    assert ready["score"] == 51
    assert ready["tier"] == 3
    assert sku_map["gfny-dominican-republic"] == "road-allrounder"

    pack_text = json.dumps(race_pack, ensure_ascii=False)
    assert race_pack["distance_mi"] == 89.9
    assert "before September" in pack_text
    assert "before March" not in pack_text
    assert "62 miles" not in pack_text
    assert "3,500ft" not in pack_text

    assert row["month"] == "September"
    assert row["distance_km"] == 144.6
    assert row["elevation_m"] == 647
    assert row["overall_score"] == 51
    assert row["tier"] == 3
