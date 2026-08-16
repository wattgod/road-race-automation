"""Current-source contracts for Amy's Gran Fondo 2026."""

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROFILE = ROOT / "race-data" / "amys-gran-fondo.json"
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


def test_amys_uses_the_current_2026_age_category_race() -> None:
    race = _race()
    vitals = race["vitals"]

    assert vitals["date_specific"] == "September 13, 2026 (Sunday)"
    assert vitals["distance_km"] == 122.0
    assert vitals["elevation_m"] == 1865
    assert "Age-category gun starts" in vitals["start_format"]
    assert "Four organizer-supported aid stations" in vitals["feed_zones"]
    assert "18 km/h" in vitals["cutoff_time"]
    assert race["eligibility"]["verified"] == "2026-08-15"


def test_amys_is_a_closed_road_uci_qualifier_not_a_charity_ride_only() -> None:
    race = _race()
    profile_text = " ".join(
        (
            race["tagline"],
            race["terrain"]["surface"],
            race["biased_opinion"]["summary"],
            race["biased_opinion"]["bottom_line"],
        )
    )

    assert "fully closed" in profile_text.lower()
    assert "UCI" in profile_text
    assert "top-25%" in profile_text
    assert "Not a race" not in json.dumps(race, ensure_ascii=False)
    assert "Aireys Inlet Finish" not in json.dumps(race, ensure_ascii=False)


def test_amys_rating_follows_the_repository_rubric() -> None:
    rating = _race()["fondo_rating"]
    expected = round(
        (sum(rating[field] for field in SCORE_FIELDS) + rating["cultural_impact"])
        / 70
        * 100
    )

    assert rating["distance"] == 3
    assert rating["climbing"] == 3
    assert rating["organization"] == 4
    assert rating["field_depth"] == 4
    assert rating["overall_score"] == expected == 63
    assert rating["tier"] == 2
    assert rating["tier_label"] == "TIER 2"


def test_amys_cites_the_current_organizer_page_and_embedded_route() -> None:
    urls = [citation["url"] for citation in _race()["citations"]]

    assert "https://www.amysgranfondo.org.au/amys-gran-fondo-ag/" in urls
    assert "https://ridewithgps.com/routes/43710392" in urls
    assert "https://www.amysgranfondo.org.au/faq/" in urls


def test_amys_generated_index_is_current() -> None:
    index = json.loads((ROOT / "web" / "race-index.json").read_text())
    row = next(record for record in index if record["slug"] == "amys-gran-fondo")

    assert row["distance_km"] == 122.0
    assert row["elevation_m"] == 1865
    assert row["overall_score"] == 63
    assert row["tier"] == 2
