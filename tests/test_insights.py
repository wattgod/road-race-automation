"""Tests for the dynamic Roadie Labs insights generator."""
from __future__ import annotations

import json
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path

import pytest

WORDPRESS_DIR = Path(__file__).parent.parent / "wordpress"
PROJECT_ROOT = WORDPRESS_DIR.parent
sys.path.insert(0, str(WORDPRESS_DIR))

from generate_insights import (  # noqa: E402
    CRITERIA_PHRASE,
    MONTHS,
    compute_stats,
    enrich_races,
    generate_insights_page,
    load_race_index,
    normalise_country,
)


@pytest.fixture(scope="module")
def races():
    return enrich_races(load_race_index())


@pytest.fixture(scope="module")
def stats(races):
    return compute_stats(races)


@pytest.fixture(scope="module")
def insights_html():
    return generate_insights_page()


def test_page_generates(insights_html):
    assert "<!DOCTYPE html>" in insights_html
    for section in ("tier-breakdown", "geography", "calendar-crunch", "entry-cost", "overachievers"):
        assert f'id="{section}"' in insights_html


def test_stats_recompute_from_index_and_profiles(races, stats):
    raw = json.loads((PROJECT_ROOT / "web" / "race-index.json").read_text(encoding="utf-8"))
    assert stats["total_races"] == len(raw)
    assert stats["tier_counts"] == {
        tier: sum(int(r.get("tier", 0)) == tier for r in raw)
        for tier in range(1, 5)
    }
    expected_countries = Counter(normalise_country(r["country_name"]) for r in races if r.get("country_name"))
    assert stats["country_counts"] == expected_countries
    expected_months = Counter(r.get("month") for r in raw if r.get("month") in MONTHS)
    assert stats["month_counts"] == {month: expected_months[month] for month in MONTHS}
    assert stats["entry_fee_count"] == sum(bool(r.get("entry_fee")) for r in races)


def test_page_uses_current_recomputed_counts(insights_html, stats):
    assert f'>{stats["total_races"]}</strong><span>races rated</span>' in insights_html
    assert f'{stats["entry_fee_count"]} of {stats["total_races"]} profiles' in insights_html
    for tier, count in stats["tier_counts"].items():
        assert f'>Tier {tier}</span>' in insights_html
        assert f'>{count}</span>' in insights_html


def test_no_hardcoded_catalog_count_in_generator():
    source = (WORDPRESS_DIR / "generate_insights.py").read_text(encoding="utf-8")
    current_count = len(load_race_index())
    assert str(current_count) not in source
    assert "total_races" in source


def test_ga4_and_seo_are_present(insights_html):
    assert "G-WQ7W8XN11N" in insights_html
    assert "googletagmanager.com" in insights_html
    assert 'rel="canonical" href="https://roadielabs.com/insights/"' in insights_html
    assert 'application/ld+json' in insights_html
    assert 'content="index, follow"' in insights_html


def test_criteria_phrase_matches_methodology(insights_html):
    methodology = (WORDPRESS_DIR / "generate_methodology.py").read_text(encoding="utf-8").lower()
    assert CRITERIA_PHRASE in methodology
    assert CRITERIA_PHRASE in insights_html.lower()
    assert "denominator remains 70" in insights_html


def test_no_emojis_or_non_road_branding(insights_html):
    emoji = re.compile("[\\U0001F300-\\U0001FAFF\\U00002700-\\U000027BF]")
    assert not emoji.search(insights_html)
    assert "Gravel God" not in insights_html
    assert "--gg-" not in insights_html


def test_insights_css_has_no_raw_hex():
    source = (WORDPRESS_DIR / "generate_insights.py").read_text(encoding="utf-8")
    css = re.search(r"def build_insights_css\(\).*?return '''(.*?)'''", source, re.S).group(1)
    assert not re.findall(r"#[0-9a-fA-F]{3,8}\\b", css)


def test_entry_cost_correlation_is_withheld_without_normalised_currency(insights_html, stats):
    assert stats["entry_fee_coverage"] >= 0.60
    assert stats["normalised_price_count"] == 0
    assert "price-versus-score correlation" in insights_html


def test_cli_writes_insights_page(tmp_path):
    result = subprocess.run(
        [sys.executable, str(WORDPRESS_DIR / "generate_insights.py"), "--output-dir", str(tmp_path)],
        cwd=PROJECT_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    output = tmp_path / "insights.html"
    assert output.exists()
    assert "Generated" in result.stdout


def test_deploy_flag_and_fail_on_partial_are_wired():
    deploy = (PROJECT_ROOT / "scripts" / "push_wordpress.py").read_text(encoding="utf-8")
    assert '"--sync-insights"' in deploy
    assert 'f"{REMOTE_BASE}/insights"' in deploy
    assert "Insights deploy incomplete" in deploy
