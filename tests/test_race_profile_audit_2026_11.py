"""Guards for the Nov 2026 race-profile audit (wattgod/gravel-race-automation#547).

- gran-fondo-coimbra merged into granfondo-leiria (UCI moved and renamed it).
- gfny-philippines and granfondo-alpe-adria retired (no current edition).
- the-majestics and nordsjorittet retired to Gravel God (gravel, not road).
- douro-gran-fondo stays the Love Tiles Douro Granfondo in Peso da Régua.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]

REDIRECTS = {
    "gran-fondo-coimbra": (
        "/race/granfondo-leiria/",
        "/race/granfondo-leiria/$1",
        "/race/granfondo-leiria.md",
    ),
    "gfny-philippines": (
        "/road-races/?region=Asia",
        "/road-races/?region=Asia",
        "/road-races/?region=Asia",
    ),
    "granfondo-alpe-adria": (
        "/road-races/?region=Western+Europe",
        "/road-races/?region=Western+Europe",
        "/road-races/?region=Western+Europe",
    ),
    "the-majestics": (
        "https://gravelgodcycling.com/race/the-majestics-gravel/",
        "https://gravelgodcycling.com/race/the-majestics-gravel/",
        "https://gravelgodcycling.com/race/the-majestics-gravel.md",
    ),
    "nordsjorittet": (
        "https://gravelgodcycling.com/race/nordsjorittet/",
        "https://gravelgodcycling.com/race/nordsjorittet/",
        "https://gravelgodcycling.com/race/nordsjorittet.md",
    ),
}


def _json(rel: str):
    return json.loads((ROOT / rel).read_text(encoding="utf-8"))


def _push_redirect_block() -> str:
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "push_wordpress", ROOT / "scripts" / "push_wordpress.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.REDIRECT_BLOCK


@pytest.mark.parametrize("slug", sorted(REDIRECTS))
def test_retired_slug_is_gone_from_the_catalog(slug: str) -> None:
    readiness = _json("data/plan-readiness.json")
    sku_map = _json("data/tp-sku-map.json")
    race_dates = _json("web/race-dates.json")
    index = _json("web/race-index.json")
    sitemap = (ROOT / "web" / "sitemap.xml").read_text(encoding="utf-8")

    assert not (ROOT / "race-data" / f"{slug}.json").exists()
    assert not (ROOT / "web" / "race-packs" / f"{slug}.json").exists()
    assert slug not in readiness["races"]
    assert slug not in readiness["ranked_queue"]
    assert slug not in readiness["pilot_candidates"]
    assert slug not in sku_map
    assert slug not in race_dates
    assert all(row["slug"] != slug for row in index)
    assert f"roadielabs.com/race/{slug}/<" not in sitemap


@pytest.mark.parametrize("slug", sorted(REDIRECTS))
def test_retired_slug_301s_in_both_redirect_sources(slug: str) -> None:
    bare, sub, md = REDIRECTS[slug]
    expected = (
        f"RewriteRule ^race/{slug}/?$ {bare} [R=301,L]",
        f"RewriteRule ^race/{slug}/(.*)$ {sub} [R=301,L]",
        f"RewriteRule ^race/{slug}\\.md$ {md} [R=301,L]",
    )
    deployed = (ROOT / "web" / "htaccess-root").read_text(encoding="utf-8")
    block = _push_redirect_block()
    for rule in expected:
        assert rule in deployed, rule
        assert rule in block, rule
    # Rules must sit before the 404 handler / inside the managed block.
    assert deployed.index(expected[0]) < deployed.index("ErrorDocument 404")


def test_leiria_carries_the_coimbra_lineage_and_2027_date() -> None:
    race = _json("race-data/granfondo-leiria.json")["race"]
    vitals = race["vitals"]
    organizer = "https://cabreirasolutions.com/evento/granfondo-leiria-region/"
    cited = {c["url"] for c in race["citations"]}

    assert vitals["date"] == "2027: February 27-28"
    assert vitals["date_specific"] == "2027: February 27-28"
    assert _json("web/race-dates.json")["granfondo-leiria"] == "2027-02-27"
    assert race["eligibility"]["status"] == "active"
    assert race["eligibility"]["source"] == organizer
    assert race["logistics"]["official_site"] == organizer
    assert race["history"]["founded"] == 2021
    assert organizer in cited
    assert (
        "https://ucigranfondoworldseries.com/en/"
        "granfondo-coimbra-region-a-very-successful-newcomer-in-the-series/"
    ) in cited
    assert (
        "https://ucigranfondoworldseries.com/en/"
        "portuguese-uci-gran-fondo-world-series-event-moves-to-leiria-region/"
    ) in cited

    rendered = json.dumps(
        {k: race[k] for k in ("vitals", "final_verdict", "biased_opinion",
                              "course_description", "logistics", "climate")},
        ensure_ascii=False,
    )
    for stale in ("Spring TBD", "unconfirmed for 2027", "gran-fondo-coimbra.json",
                  "No confirmed 2027 date"):
        assert stale not in rendered, stale


def test_douro_is_the_love_tiles_granfondo_in_peso_da_regua() -> None:
    race = _json("race-data/douro-gran-fondo.json")["race"]
    vitals = race["vitals"]

    assert race["name"] == "Love Tiles Douro Granfondo"
    assert vitals["location"].startswith("Peso da Régua")
    assert vitals["date_specific"].startswith("2026: April 26")
    assert "Porto" not in json.dumps(race, ensure_ascii=False)
    assert any(
        c["url"] == "https://bikeservice.pt/event/douro-granfondo/regulamento-douro-granfondo/"
        for c in race["citations"]
    )
