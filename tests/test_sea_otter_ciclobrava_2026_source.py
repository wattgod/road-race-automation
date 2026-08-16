"""Current-source contracts for La Ciclobrava by Lapierre 2026."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROFILE = ROOT / "race-data" / "sea-otter-ciclobrava.json"
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


def test_ciclobrava_uses_current_2026_identity_and_long_route() -> None:
    race = _race()
    vitals = race["vitals"]

    assert race["name"] == "La Ciclobrava by Lapierre"
    assert race["display_name"] == "La Ciclobrava by Lapierre"
    assert vitals["date_specific"] == "2026: September 20"
    assert vitals["distance_km"] == 150.0
    assert vitals["distance_mi"] == 93.2
    assert vitals["elevation_m"] == 1756
    assert vitals["elevation_ft"] == 5761.0
    assert "150 km / 93.2 mi" in vitals["route_options"][0]
    assert "1,756 m / 5,761 ft" in vitals["route_options"][0]
    assert "Sant Grau d'Ardenya" in vitals["route_options"][0]
    assert "Romanyà" in vitals["route_options"][0]
    assert "La Ganga" in vitals["route_options"][0]
    assert "Montjuïc" in vitals["route_options"][0]
    assert race["eligibility"]["verified"] == "2026-08-15"
    assert "legacy sea-otter-ciclobrava slug" in race["eligibility"]["notes"]


def test_ciclobrava_preserves_current_operational_limits_and_conflicts() -> None:
    race = _race()
    vitals = race["vitals"]
    text = json.dumps(race, ensure_ascii=False)

    assert "1,800 participants" in vitals["field_size"]
    assert "150 km at 8:00am" in vitals["start_format"]
    assert "100 km at 8:10am" in vitals["start_format"]
    assert "70 km at 8:20am" in vitals["start_format"]
    assert "roads remain open to traffic" in vitals["start_format"]
    assert "€53 through August 17, 2026" in vitals["entry_fee"]
    assert "€60" in vitals["entry_fee"]
    assert "€10" in vitals["entry_fee"]
    assert "km 49 Mirador Punta de Vallpresona" in vitals["feed_zones"]
    assert "km 74 Romanyà" in vitals["feed_zones"]
    assert "11:45 PM" in vitals["cutoff_time"]
    assert "apparent AM/PM error" in vitals["cutoff_time"]
    assert "2:00pm at km 137 Campdorà" in vitals["cutoff_time"]
    assert "2:30pm" in vitals["cutoff_time"]
    assert "The route page's introductory paragraph still says 2,000 m" in text
    assert "70 km route has 800 m or 1,000 m" in text
    assert "Flexible for non-competitive format" not in text
    assert "weather perfection" not in text.lower()
    assert "140km Costa Brava bliss" not in text


def test_ciclobrava_regrade_follows_the_rubric() -> None:
    rating = _race()["fondo_rating"]
    expected = round(
        (sum(rating[field] for field in SCORE_FIELDS) + rating["cultural_impact"])
        / 70
        * 100
    )

    assert rating["distance"] == 4
    assert rating["climbing"] == 3
    assert rating["descent_technicality"] == 3
    assert rating["road_surface"] == 2
    assert rating["organization"] == 3
    assert rating["logistics"] == 3
    assert rating["field_depth"] == 3
    assert rating["value"] == 4
    assert rating["cultural_impact"] == 2
    assert rating["overall_score"] == expected == 63
    assert rating["tier"] == 2
    assert rating["tier_label"] == "TIER 2"


def test_ciclobrava_cites_current_official_sources() -> None:
    urls = [citation["url"] for citation in _race()["citations"]]

    assert "https://www.laciclobrava.com/en/" in urls
    assert "https://www.laciclobrava.com/en/routes/" in urls
    assert any("wikiloc/embedv2.do?id=231791544" in url for url in urls)
    assert "https://www.laciclobrava.com/en/schedule/" in urls
    assert "https://www.laciclobrava.com/en/regulation/" in urls
    assert any("girona-is-getting-ready" in url for url in urls)
    assert "https://www.seaottereurope.com/sports-event-schedule/" in urls
    assert "https://www.seaottereurope.com/general-festival-program/" in urls
    assert "https://www.seaottereurope.com/how-to-get-there-and-park/" in urls
    assert "https://www.seaottereurope.com/accommodation/" in urls


def test_ciclobrava_generated_artifacts_are_current() -> None:
    readiness = json.loads((ROOT / "data" / "plan-readiness.json").read_text())
    sku_map = json.loads((ROOT / "data" / "tp-sku-map.json").read_text())
    race_pack = json.loads(
        (ROOT / "web" / "race-packs" / "sea-otter-ciclobrava.json").read_text()
    )
    index = json.loads((ROOT / "web" / "race-index.json").read_text())
    row = next(record for record in index if record["slug"] == "sea-otter-ciclobrava")

    ready = readiness["races"]["sea-otter-ciclobrava"]
    assert ready["ready"] is True
    assert ready["race_date"] == "2026-09-20"
    assert ready["score"] == 63
    assert ready["tier"] == 2
    assert sku_map["sea-otter-ciclobrava"] == "road-alpine-fondo"

    pack_text = json.dumps(race_pack, ensure_ascii=False)
    assert race_pack["race_name"] == "La Ciclobrava by Lapierre"
    assert race_pack["distance_mi"] == 93.2
    assert "5,761" in pack_text
    assert "6,562" not in pack_text
    assert "140km" not in pack_text

    assert row["name"] == "La Ciclobrava by Lapierre"
    assert row["month"] == "September"
    assert row["distance_km"] == 150.0
    assert row["elevation_m"] == 1756
    assert row["overall_score"] == 63
    assert row["tier"] == 2
