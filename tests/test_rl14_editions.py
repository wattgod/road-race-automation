"""RL-14: titles name the coming season; calendars list only dated editions."""

import json
import sys
from datetime import date
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "wordpress"))

import generate_calendar as cal  # noqa: E402
import generate_homepage as hp  # noqa: E402
import generate_power_rankings as pr  # noqa: E402
from season import season_year  # noqa: E402


# ── season_year ──────────────────────────────────────────────

class TestSeasonYear:
    def test_rolls_over_in_september(self):
        assert season_year(date(2026, 8, 31)) == 2026
        assert season_year(date(2026, 9, 1)) == 2027

    def test_build_date_of_this_ticket(self):
        assert season_year(date(2026, 11, 15)) == 2027

    def test_january_is_same_year(self):
        assert season_year(date(2027, 1, 2)) == 2027


# ── Titles ───────────────────────────────────────────────────

INDEX = [{
    "name": "Alpha Fondo", "slug": "alpha-fondo", "location": "Somewhere",
    "country": "Italy", "region": "Southern Europe", "month": "June",
    "tier": 1, "overall_score": 85, "distance_mi": 100, "elevation_ft": 9000,
    "scores": {}, "tagline": "x", "has_profile": True,
}, {
    "name": "Beta Sportive", "slug": "beta-sportive", "location": "Elsewhere",
    "country": "France", "region": "Western Europe", "month": "July",
    "tier": 2, "overall_score": 70, "distance_mi": 80, "elevation_ft": 5000,
    "scores": {}, "tagline": "y", "has_profile": True,
}, {
    "name": "Gamma Hillclimb", "slug": "gamma-hillclimb", "location": "Hill",
    "country": "Spain", "region": "Southern Europe", "month": "May",
    "tier": 3, "overall_score": 55, "distance_mi": 20, "elevation_ft": 4000,
    "scores": {}, "tagline": "z", "has_profile": True,
}]


class TestTitles:
    def test_homepage_says_coming_season(self, monkeypatch):
        monkeypatch.setattr(hp, "SEASON_YEAR", 2027)
        hero = hp.build_hero({"race_count": 421, "t1_count": 10, "t2_count": 50,
                              "dimensions": 14, "countries": 40, "regions": 8})
        assert "Races Scored for 2027" in hero
        assert "THE 2027 RACE DATABASE" in hero
        assert "for 2026" not in hero

    def test_homepage_module_uses_season_year(self):
        assert hp.SEASON_YEAR == season_year()

    def test_power_rankings_use_season_year(self, monkeypatch):
        monkeypatch.setattr(pr, "SEASON_YEAR", 2027)
        html = pr.build_power_rankings_page(INDEX)
        assert "Road Race Power Rankings 2027" in html
        assert "/race/power-rankings-2027/" in html
        assert "/race/calendar/2027/" in html
        assert "2026" not in html.split("<title>")[1].split("</title>")[0]


# ── Calendar ─────────────────────────────────────────────────

def _write_profiles(tmp_path, dates):
    for slug, ds in dates.items():
        (tmp_path / f"{slug}.json").write_text(json.dumps(
            {"race": {"slug": slug, "vitals": {"date_specific": ds}}}), encoding="utf-8")
    return tmp_path


class TestCalendar:
    def test_only_races_with_that_years_date_are_listed(self, tmp_path):
        data_dir = _write_profiles(tmp_path, {
            "alpha-fondo": "2027: June 27 (38th edition; 37th ran June 28, 2026)",
            "beta-sportive": "2026: July 5 (completed). 2027 date not yet announced.",
            "gamma-hillclimb": "TBD — 2027 event window: May",
        })
        dates = cal.load_edition_dates(data_dir)
        assert dates == {"alpha-fondo": ("2027-06-27", "2027-06-27"),
                         "beta-sportive": ("2026-07-05", "2026-07-05")}
        races_2027 = cal.races_for_year(INDEX, dates, 2027)
        assert [r["slug"] for r in races_2027] == ["alpha-fondo"]
        races_2026 = cal.races_for_year(INDEX, dates, 2026)
        assert [r["slug"] for r in races_2026] == ["beta-sportive"]

    def test_past_edition_not_shifted_into_next_season(self, tmp_path):
        data_dir = _write_profiles(tmp_path, {
            "beta-sportive": "2026: June 13 (completed). 2027 date not yet published.",
        })
        dates = cal.load_edition_dates(data_dir)
        assert cal.races_for_year(INDEX, dates, 2027) == []

    def test_page_shows_real_dates_and_counts(self, monkeypatch):
        monkeypatch.setattr(cal, "SEASON_YEAR", 2027)
        races = cal.races_for_year(INDEX, {
            "alpha-fondo": ("2027-06-26", "2027-07-18"),
            "beta-sportive": ("2027-06-12", "2027-06-12"),
        }, 2027)
        html = cal.build_calendar_page(races, 2027)
        assert "<title>Road Race Calendar 2027 — 2 Events | Roadie Labs</title>" in html
        assert 'href="https://roadielabs.com/race/calendar/2027/"' in html
        assert "2 rated events with a published 2027 date" in html
        assert '<time datetime="2027-06-12">Jun 12</time>' in html
        assert '<time datetime="2027-06-26">Jun 26 – Jul 18</time>' in html
        assert "Gamma Hillclimb" not in html
        assert "Date TBD" not in html
        # Both races sit in June, by date
        june = html.split('id="month-june"')[1].split("</section>")[0]
        assert june.index("Beta Sportive") < june.index("Alpha Fondo")
        assert '<a href="/race/calendar/2026/">2026 calendar</a>' in html

    def test_empty_season_page_builds_without_dates(self):
        html = cal.build_calendar_page([], 2027)
        assert "0 rated events with a published 2027 date" in html
        assert 'class="rl-cal-card"' not in html

    def test_main_writes_every_season_from_real_data(self, tmp_path, monkeypatch):
        monkeypatch.setattr(cal, "SEASON_YEAR", 2027)
        monkeypatch.setattr(sys, "argv", ["generate_calendar.py", "--output-dir", str(tmp_path)])
        cal.main()
        for year in (2026, 2027):
            html = (tmp_path / "calendar" / str(year) / "index.html").read_text()
            assert f"{year} Road Race Calendar" in html
        # Every card on the 2027 page carries a 2027 date from its profile
        html_2027 = (tmp_path / "calendar" / "2027" / "index.html").read_text()
        import re
        stamps = re.findall(r'<time datetime="(\d{4})-', html_2027)
        assert stamps and set(stamps) == {"2027"}


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
