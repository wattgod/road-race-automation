"""Regression tests for country-aware and distance-variant-aware fuzzy
duplicate detection (issue #11 work order 1)."""

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
    distance_km: float | None = None,
) -> None:
    vitals = {"country": country, "location": location}
    if distance_km is not None:
        vitals["distance_km"] = distance_km
    profile = {
        "race": {
            "name": name,
            "slug": slug,
            "vitals": vitals,
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


# ── Distance-variant suppression (issue #11 WO1, 2026-09-04) ─────────────────
# Same-series entries at different distances are not duplicates. The rule is
# general (variant tokens / distance delta), never a per-slug allowlist, and
# must NOT swallow the real duplicate gran-fondo-medellin / granfondo-colombia
# (same UCI event, 120 km vs 138 km — only ~13% apart).

def test_utrecht_ultra_vs_xl_is_suppressed(tmp_path, monkeypatch):
    """The pair that fired every night for 26 days: real profiles' name +
    distance shape (1000 km vs 1600 km, 'XL' suffix, same country)."""
    _write_profile(tmp_path, "utrecht-ultra", "Utrecht Ultra",
                   country="Netherlands", location="Utrecht, Netherlands",
                   distance_km=1000.0)
    _write_profile(tmp_path, "utrecht-ultra-xl", "Utrecht Ultra XL",
                   country="Netherlands", location="Utrecht, Netherlands",
                   distance_km=1600.0)
    monkeypatch.setattr(immune_check, "RACE_DATA_DIR", tmp_path)

    assert immune_check.check_fuzzy_duplicates() == []


def test_gran_fondo_medellin_vs_granfondo_colombia_still_flags(tmp_path, monkeypatch):
    """Real duplicate: same UCI event under two slugs. Names differ by more
    than a variant token ('UCI', 'Fondo' vs 'Granfondo') and the distances are
    only ~13% apart, so neither suppression rule may fire."""
    _write_profile(tmp_path, "gran-fondo-medellin", "UCI Gran Fondo Colombia",
                   country="Colombia", location="Medellín, Antioquia, Colombia",
                   distance_km=120.0)
    _write_profile(tmp_path, "granfondo-colombia", "Granfondo Colombia",
                   country="Colombia", location="Medellín, Antioquia, Colombia",
                   distance_km=138)
    monkeypatch.setattr(immune_check, "RACE_DATA_DIR", tmp_path)

    findings = immune_check.check_fuzzy_duplicates()

    assert len(findings) == 1
    assert findings[0].code == "duplicate-race"
    assert "gran-fondo-medellin" in findings[0].detail
    assert "granfondo-colombia" in findings[0].detail


def test_variant_token_alone_suppresses_without_distances(tmp_path, monkeypatch):
    """Token rule is independent of the distance rule: no distance_km on
    either side, names differ only by a known variant token."""
    _write_profile(tmp_path, "alpine-fondo", "Alpine Fondo",
                   country="Italy", location="Italy")
    _write_profile(tmp_path, "alpine-fondo-half", "Alpine Fondo Half",
                   country="Italy", location="Italy")
    monkeypatch.setattr(immune_check, "RACE_DATA_DIR", tmp_path)

    assert immune_check.check_fuzzy_duplicates() == []


def test_distance_delta_alone_suppresses_without_variant_token(tmp_path, monkeypatch):
    """Distance rule is independent of the token rule: names differ by a
    non-variant word, but the courses are 50% apart."""
    _write_profile(tmp_path, "coastal-classic", "Coastal Classic Ride",
                   country="Australia", location="Australia", distance_km=100)
    _write_profile(tmp_path, "coastal-classic-tour", "Coastal Classic Tour",
                   country="Australia", location="Australia", distance_km=200)
    monkeypatch.setattr(immune_check, "RACE_DATA_DIR", tmp_path)

    assert immune_check.check_fuzzy_duplicates() == []


@pytest.mark.parametrize(
    ("name_a", "name_b", "km_a", "km_b", "expected"),
    [
        # token rule
        ("Utrecht Ultra", "Utrecht Ultra XL", None, None, True),
        ("Medio Fondo Dolomiti", "Gran Fondo Dolomiti", None, None, True),
        ("Sea to Sky 100", "Sea to Sky 200", None, None, True),
        ("Dirty Reiver 130km", "Dirty Reiver 200km", None, None, True),
        ("Pyrenees Sportive Short", "Pyrenees Sportive Long", None, None, True),
        # a bare year is not a distance numeral
        ("Gran Fondo Roma 2026", "Gran Fondo Roma 2027", None, None, False),
        # identical names never suppress on tokens alone
        ("Mt. Washington Hillclimb", "Mt. Washington Hillclimb", None, None, False),
        # distance rule: threshold is >25% of the longer course
        ("UCI Gran Fondo Colombia", "Granfondo Colombia", 120.0, 138.0, False),
        ("Utrecht Ultra", "Utrecht Ultra XL", 1000.0, 1600.0, True),
        ("Race A", "Race B", 100.0, 125.0, False),   # exactly 20% — not a variant
        ("Race A", "Race B", 100.0, 134.0, True),    # ~25.4% — variant
        # unknown / zero distance on either side disables the distance rule
        ("Race A", "Race B", None, 200.0, False),
        ("Race A", "Race B", 0, 200.0, False),
    ],
)
def test_is_distance_variant_rule(name_a, name_b, km_a, km_b, expected):
    assert immune_check.is_distance_variant(name_a, name_b, km_a, km_b) is expected


def test_profile_retired_via_duplicate_of_flag_stops_flagging(tmp_path, monkeypatch):
    """catalog_flags.duplicate_of is the repo's soft-retire path (generator
    refuses to regen, index skips). Once a duplicate is resolved that way the
    detector must stop firing on the pair."""
    _write_profile(tmp_path, "gran-fondo-medellin", "UCI Gran Fondo Colombia",
                   country="Colombia", location="Medellín, Antioquia, Colombia",
                   distance_km=120.0)
    _write_profile(tmp_path, "granfondo-colombia", "Granfondo Colombia",
                   country="Colombia", location="Medellín, Antioquia, Colombia",
                   distance_km=138)
    retired = tmp_path / "gran-fondo-medellin.json"
    data = json.loads(retired.read_text(encoding="utf-8"))
    data["race"]["catalog_flags"] = {"duplicate_of": "granfondo-colombia"}
    retired.write_text(json.dumps(data), encoding="utf-8")
    monkeypatch.setattr(immune_check, "RACE_DATA_DIR", tmp_path)

    assert immune_check.check_fuzzy_duplicates() == []
