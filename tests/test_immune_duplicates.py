"""Regression tests for country-aware fuzzy duplicate detection."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

import immune_check


def _write_profile(
    directory: Path,
    slug: str,
    name: str,
    *,
    country: str | None,
    location: str,
) -> None:
    profile = {
        "race": {
            "name": name,
            "slug": slug,
            "vitals": {"country": country, "location": location},
            "citations": [],
        }
    }
    (directory / f"{slug}.json").write_text(json.dumps(profile), encoding="utf-8")


@pytest.mark.parametrize(
    ("slug_a", "name_a", "country_a", "slug_b", "name_b", "country_b"),
    [
        (
            "letape-brazil",
            "L'Etape Brasil by Tour de France",
            "Brazil",
            "letape-dubai",
            "L'Etape Dubai by Tour de France",
            "UAE",
        ),
        (
            "letape-poland",
            "L'Etape Poland by Tour de France",
            "Poland",
            "letape-thailand",
            "L'Etape Thailand by Tour de France",
            "Thailand",
        ),
        (
            "letape-slovakia",
            "L'Etape Slovakia by Tour de France",
            "Slovakia",
            "letape-slovenia",
            "L'Étape Slovenia by Tour de France",
            "Slovenia",
        ),
        (
            "letape-taiwan",
            "L'Etape Taiwan by Tour de France",
            "Taiwan",
            "letape-thailand",
            "L'Etape Thailand by Tour de France",
            "Thailand",
        ),
    ],
)
def test_distinct_letape_countries_do_not_flag(
    tmp_path,
    monkeypatch,
    slug_a,
    name_a,
    country_a,
    slug_b,
    name_b,
    country_b,
):
    _write_profile(tmp_path, slug_a, name_a, country=country_a, location=country_a)
    _write_profile(tmp_path, slug_b, name_b, country=country_b, location=country_b)
    monkeypatch.setattr(immune_check, "RACE_DATA_DIR", tmp_path)

    assert immune_check.check_fuzzy_duplicates() == []


@pytest.mark.parametrize(
    ("slug_a", "name_a", "slug_b", "name_b", "country"),
    [
        (
            "dreilaendergiro",
            "Dreiländergiro",
            "dreilander-giro",
            "Dreilander Giro",
            "Austria",
        ),
        (
            "mount-washington-hillclimb",
            "Mt. Washington Auto Road Bicycle Hillclimb",
            "mt-washington-hillclimb",
            "Mt. Washington Auto Road Bicycle Hillclimb",
            "United States",
        ),
    ],
)
def test_same_country_genuine_duplicates_still_flag(
    tmp_path,
    monkeypatch,
    slug_a,
    name_a,
    slug_b,
    name_b,
    country,
):
    _write_profile(tmp_path, slug_a, name_a, country=country, location=country)
    _write_profile(tmp_path, slug_b, name_b, country=country, location=country)
    monkeypatch.setattr(immune_check, "RACE_DATA_DIR", tmp_path)

    findings = immune_check.check_fuzzy_duplicates()

    assert len(findings) == 1
    assert findings[0].code == "duplicate-race"
    assert slug_a in findings[0].detail
    assert slug_b in findings[0].detail
