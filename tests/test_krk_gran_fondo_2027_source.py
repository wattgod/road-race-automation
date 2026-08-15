import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
PROFILE = ROOT / "race-data" / "krk-gran-fondo.json"


def _race() -> dict:
    return json.loads(PROFILE.read_text(encoding="utf-8"))["race"]


def test_krk_uses_the_organizer_linked_2027_date():
    race = _race()

    assert race["vitals"]["date"] == "2027: April 24 (Saturday)"
    assert race["vitals"]["date_specific"] == "2027: April 24 (Saturday)"
    assert race["eligibility"]["verified"] == "2026-08-15"
    assert race["eligibility"]["source"] == "https://my.raceresult.com/395104/"


def test_krk_is_ready_with_2026_climbing_facts_guarded():
    race = _race()
    notes = race["eligibility"]["notes"]
    clearance = race["training_plan_clearance"]

    assert "edition-specific 82km route" in notes
    assert "only as conservative demand context" in notes
    assert clearance["status"] == "ready"
    assert clearance["race_date"] == "2027-04-24"
    assert clearance["ladder"] == "FULL-7"
    assert clearance["variation"] == "All-Rounder"
    assert clearance["blockers"] == []
    assert "demand context, not confirmed 2027 race facts" in clearance["guard"]
    assert race["course_description"]["character"].startswith(
        "The organizer-linked 2027 registration and timing page confirms an 82km"
    )
    assert "1,320m total and four categorized climbs are the latest 2026 reference" in (
        race["final_verdict"]["should_you_race"]
    )


def test_krk_cites_the_organizer_embedded_event():
    race = _race()
    urls = {citation["url"] for citation in race["citations"]}

    assert "https://krkgranfondo.com/index.php/en/register/" in urls
    assert "https://my.raceresult.com/395104/" in urls
    assert "https://protime.si/dogodek/4-krk-granfondo-croatia-2027/" in urls


def test_krk_source_review_records_the_build_contract():
    race = _race()
    review = race["source_review"]

    assert review["reviewed_at"] == "2026-08-15"
    assert review["race_date"] == "2027-04-24"
    assert review["plan_status"] == "CLEARED FOR FULL-7 ROADIE LABS PLAN BUILD"
    assert "82km route" in review["facts_scope"]
    assert "2026 elevation and climb profile" in review["guard"]
