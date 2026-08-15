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
    assert race["eligibility"]["verified"] == "2026-08-14"
    assert race["eligibility"]["source"] == "https://my.raceresult.com/395104/"


def test_krk_remains_course_blocked_without_projecting_2026_facts():
    race = _race()
    notes = race["eligibility"]["notes"]
    clearance = race["training_plan_clearance"]

    assert "source-blocked" in notes
    assert "edition-specific 2027 course" in notes
    assert "until" in notes
    assert clearance["status"] == "source_blocked"
    assert clearance["race_date"] == "2027-04-24"
    assert clearance["ladder"] == "FULL-7"
    assert clearance["blockers"]
    assert "Do not project the 2026" in clearance["guard"]
    assert race["course_description"]["character"].startswith(
        "Latest official route reference (2026; not yet confirmed for 2027)"
    )
    assert "wait for the 2027 course" in race["final_verdict"]["should_you_race"]


def test_krk_cites_the_organizer_embedded_event():
    race = _race()
    urls = {citation["url"] for citation in race["citations"]}

    assert "https://krkgranfondo.com/index.php/en/register/" in urls
    assert "https://my.raceresult.com/395104/" in urls
