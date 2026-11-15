"""Regression tests for the deploy-owned sitemap index."""

import sys
from pathlib import Path
from xml.etree import ElementTree


SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from generate_sitemap import generate_sitemap  # noqa: E402
from push_wordpress import build_sitemap_index  # noqa: E402


def _locations(xml: str) -> list[str]:
    root = ElementTree.fromstring(xml)
    return [node.text for node in root.iter() if node.tag.endswith("loc")]


def test_sitemap_index_contains_only_the_required_race_sitemap() -> None:
    assert _locations(build_sitemap_index("2026-08-28", False)) == [
        "https://roadielabs.com/race-sitemap.xml",
    ]


def test_sitemap_index_adds_blog_only_when_it_was_uploaded() -> None:
    assert _locations(build_sitemap_index("2026-08-28", True)) == [
        "https://roadielabs.com/race-sitemap.xml",
        "https://roadielabs.com/blog-sitemap.xml",
    ]


def test_sitemap_index_never_advertises_phantom_plugin_sitemaps() -> None:
    xml = build_sitemap_index("2026-08-28", True)
    assert "post-sitemap.xml" not in xml
    assert "page-sitemap.xml" not in xml
    assert "category-sitemap.xml" not in xml


def test_generated_sitemap_uses_only_the_canonical_methodology_url(tmp_path: Path) -> None:
    output = tmp_path / "web" / "sitemap.xml"
    generate_sitemap([], output)
    locations = _locations(output.read_text(encoding="utf-8"))
    assert "https://roadielabs.com/race/methodology/" in locations
    assert "https://roadielabs.com/methodology/" not in locations


def test_generated_sitemap_lists_public_site_pages(tmp_path: Path) -> None:
    output = tmp_path / "web" / "sitemap.xml"
    generate_sitemap([], output)
    locations = _locations(output.read_text(encoding="utf-8"))
    for path in ("/coaching/", "/consulting/", "/about/", "/privacy/", "/terms/",
                 "/race/tier-1/", "/race/tier-4/"):
        assert f"https://roadielabs.com{path}" in locations


def test_prep_kits_listed_only_for_generated_kits_of_indexed_races(tmp_path: Path) -> None:
    kits = tmp_path / "wordpress" / "output" / "prep-kit"
    kits.mkdir(parents=True)
    for name in ("index", "alpha", "orphan"):
        (kits / f"{name}.html").write_text("<html></html>", encoding="utf-8")
    output = tmp_path / "web" / "sitemap.xml"
    generate_sitemap([{"slug": "alpha", "tier": 2}, {"slug": "beta", "tier": 2}], output)
    locations = _locations(output.read_text(encoding="utf-8"))
    assert "https://roadielabs.com/race/alpha/prep-kit/" in locations
    assert "https://roadielabs.com/race/beta/prep-kit/" not in locations
    assert "https://roadielabs.com/race/orphan/prep-kit/" not in locations
    assert "https://roadielabs.com/race/index/prep-kit/" not in locations
