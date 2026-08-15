import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "wordpress"))

import generate_neo_brutalist as generator


def test_configure_plans_db_resolves_path_and_invalidates_cache(tmp_path, monkeypatch):
    source = tmp_path / "plans.json"
    source.write_text('{"plans": []}\n', encoding="utf-8")
    monkeypatch.setattr(generator, "_PLANS_BY_SLUG_CACHE", {"stale": []})

    generator.configure_plans_db(source)

    assert generator.PLANS_DB_PATH == source.resolve()
    assert generator._PLANS_BY_SLUG_CACHE is None


def test_boone_and_panama_publish_the_complete_full_7_ladders():
    links = json.loads(
        (Path(__file__).resolve().parent.parent / "data" / "tp-race-plan-links.json")
        .read_text(encoding="utf-8")
    )

    assert [plan["planId"] for plan in links["boone-gran-fondo"]] == [
        669603, 669604, 669605, 669606, 669607, 669608, 669609
    ]
    assert [plan["planId"] for plan in links["gran-fondo-panama"]] == [
        669610, 669611, 669612, 669613, 669614, 669616, 669618
    ]
    assert all(plan["url"].endswith(f"tp-{plan['planId']}/p") for slug in (
        "boone-gran-fondo", "gran-fondo-panama"
    ) for plan in links[slug])


def test_millars_publishes_the_complete_full_7_ladder():
    links = json.loads(
        (Path(__file__).resolve().parent.parent / "data" / "tp-race-plan-links.json")
        .read_text(encoding="utf-8")
    )

    millars = links["the-millars-gran-fondo"]
    assert [plan["planId"] for plan in millars] == [
        669673,
        669674,
        669675,
        669676,
        669677,
        669678,
        669679,
    ]
    assert [plan["price"] for plan in millars] == [99, 79, 99, 79, 99, 99, 69]
    assert all(plan["url"].endswith(f"tp-{plan['planId']}/p") for plan in millars)


def test_race_around_poland_publishes_the_complete_full_7_ladder():
    links = json.loads(
        (Path(__file__).resolve().parent.parent / "data" / "tp-race-plan-links.json")
        .read_text(encoding="utf-8")
    )

    plans = links["race-around-poland"]
    assert [plan["planId"] for plan in plans] == [
        669693,
        669694,
        669695,
        669696,
        669697,
        669698,
        669699,
    ]
    assert [plan["price"] for plan in plans] == [99, 79, 99, 79, 99, 99, 69]
    assert all(plan["url"].endswith(f"tp-{plan['planId']}/p") for plan in plans)
