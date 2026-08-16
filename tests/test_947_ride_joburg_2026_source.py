"""Current-source contracts for 947 Ride Joburg 2026."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROFILE = ROOT / "race-data" / "947-ride-joburg.json"
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


def test_joburg_uses_current_2026_identity_and_route() -> None:
    race = _race()
    vitals = race["vitals"]

    assert race["name"] == "947 Ride Joburg"
    assert race["slug"] == "947-ride-joburg"
    assert vitals["date"] == "November 22, 2026"
    assert vitals["date_specific"].startswith("Sunday, November 22, 2026")
    assert vitals["distance_km"] == 97.0
    assert vitals["distance_mi"] == 60.3
    assert vitals["elevation_m"] == 1398.0
    assert vitals["elevation_ft"] == 4587.0
    assert vitals["route_options"] == ["97km Road Race"]
    assert "29th edition" in vitals["date_specific"]
    assert "first time" in vitals["date_specific"]
    assert "Kyalami" in vitals["date_specific"]
    assert race["eligibility"]["verified"] == "2026-08-15"
    assert race["eligibility"]["source"].endswith("/road.html")


def test_joburg_preserves_current_operational_limits_and_conflicts() -> None:
    race = _race()
    vitals = race["vitals"]
    text = json.dumps(race, ensure_ascii=False)

    assert "not published a 2026 field cap" in vitals["field_size"]
    assert "Seeded start groups" in vitals["start_format"]
    assert "October 8, 2026" in vitals["start_format"]
    assert "R810" in vitals["entry_fee"]
    assert "October 4" in vitals["registration"]
    assert "October 21" in vitals["registration"]
    assert "November 1, 2026" in vitals["registration"]
    for distance in ("9.25", "19", "30.2", "40", "59", "68", "76", "84.5"):
        assert distance in vitals["feed_zones"]
    assert "Six hours after the last start group" in vitals["cutoff_time"]
    assert "1,398m" in race["course_description"]["character"]
    assert "1,304" in race["course_description"]["character"]
    assert "mislabeled" in race["course_description"]["character"]
    assert "toughest climbing now comes early" in race["course_description"]["signature_challenge"]
    assert "R735" not in text
    assert "Entries close early September" not in text
    assert "fully closed roads" not in text.lower()


def test_joburg_regrade_follows_the_rubric() -> None:
    rating = _race()["fondo_rating"]
    expected = round(
        (sum(rating[field] for field in SCORE_FIELDS) + rating["cultural_impact"])
        / 70
        * 100
    )

    assert rating["distance"] == 2
    assert rating["climbing"] == 2
    assert rating["descent_technicality"] == 1
    assert rating["road_surface"] == 2
    assert rating["organization"] == 4
    assert rating["logistics"] == 2
    assert rating["field_depth"] == 4
    assert rating["value"] == 3
    assert rating["cultural_impact"] == 4
    assert rating["overall_score"] == expected == 64
    assert rating["tier"] == 2
    assert rating["tier_label"] == "TIER 2"


def test_joburg_cites_current_official_sources() -> None:
    urls = [citation["url"] for citation in _race()["citations"]]

    assert "https://ridejoburg.co.za/road.html" in urls
    assert "https://ridejoburg.co.za/rules.html" in urls
    assert "https://ridejoburg.co.za/blog.html?p=kyalami-2026" in urls
    assert "https://ridejoburg.co.za/documents/Ride_Joburg_Route_26.pdf" in urls


def test_joburg_generated_artifacts_are_current() -> None:
    readiness = json.loads((ROOT / "data" / "plan-readiness.json").read_text())
    sku_map = json.loads((ROOT / "data" / "tp-sku-map.json").read_text())
    race_pack = json.loads(
        (ROOT / "web" / "race-packs" / "947-ride-joburg.json").read_text()
    )
    index = json.loads((ROOT / "web" / "race-index.json").read_text())
    row = next(record for record in index if record["slug"] == "947-ride-joburg")

    ready = readiness["races"]["947-ride-joburg"]
    assert ready["ready"] is True
    assert ready["race_date"] == "2026-11-22"
    assert ready["score"] == 64
    assert ready["tier"] == 2
    assert sku_map["947-ride-joburg"] == "road-allrounder"

    pack_text = json.dumps(race_pack, ensure_ascii=False)
    assert race_pack["race_name"] == "947 Ride Joburg"
    assert race_pack["distance_mi"] == 60.3
    assert "4,587" in pack_text
    assert "R735" not in pack_text

    assert row["name"] == "947 Ride Joburg"
    assert row["month"] == "November"
    assert row["distance_km"] == 97.0
    assert row["distance_mi"] == 60.3
    assert row["elevation_m"] == 1398.0
    assert row["overall_score"] == 64
    assert row["tier"] == 2
