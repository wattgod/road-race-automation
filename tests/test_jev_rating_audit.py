from types import SimpleNamespace

from scripts import jev_rating_audit


def test_road_has_no_invented_rubric_and_checks_deterministic_mismatch():
    assert jev_rating_audit.parse_rubric() == {}
    profile = {
        "race": {
            "fondo_rating": {"distance": 2},
            "biased_opinion_ratings": {"distance": {"score": 3, "explanation": "Long."}},
        }
    }
    row = jev_rating_audit.audit_profile("synthetic", profile)[0]
    assert row["explanation_mismatch"] is True
    assert row["jev_level"] is None
    assert row["response_available"] is False


def test_unavailable_report_has_no_jev_flags(monkeypatch):
    monkeypatch.setattr(jev_rating_audit, "RACE_DATA", jev_rating_audit.ROOT / "missing")
    report = jev_rating_audit.run(SimpleNamespace(slug=None, tier=None, limit=None, all=False))
    assert report["model"] is None
    assert report["jev_available"] is False
    assert report["summary"]["high"] == 0
