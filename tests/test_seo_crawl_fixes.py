"""Regression tests for the 2026-10-31 crawl/SEO audit of roadielabs.com."""

import json
import os
import subprocess
import sys
from pathlib import Path
from xml.etree import ElementTree

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "wordpress"))
sys.path.insert(0, str(ROOT / "scripts"))

from generate_sitemap import generate_sitemap  # noqa: E402
from push_wordpress import sitemap_missing_race_pages  # noqa: E402
from generate_vs_pages import select_pairs  # noqa: E402
from generate_neo_brutalist import (  # noqa: E402
    build_explore_links,
    build_seo_description,
    load_race_data,
)
from generate_training_plan_pages import plan_page_excluded  # noqa: E402
import generate_tier_hubs  # noqa: E402

RACE_INDEX = json.loads((ROOT / "web" / "race-index.json").read_text(encoding="utf-8"))


def _locs(path: Path) -> set:
    tree = ElementTree.parse(path)
    return {n.text for n in tree.iter() if n.tag.endswith("}loc")}


def _fake_root(tmp_path: Path) -> Path:
    root = tmp_path / "proj"
    out = root / "wordpress" / "output"
    (out / "a-race-vs-b-race").mkdir(parents=True)
    (out / "a-race-vs-b-race" / "index.html").write_text("x")
    (out / "best-road-races-utopia").mkdir()
    (out / "best-road-races-utopia" / "index.html").write_text("x")
    (out / "training-plan").mkdir()
    (out / "training-plan" / "a-race.html").write_text("x")
    (out / "training-plan" / "flagged-race.html").write_text("x")
    (root / "guide").mkdir()
    (root / "guide" / "road-guide-content.json").write_text(
        json.dumps({"chapters": [{"id": "chapter-one"}]}))
    return root


def test_sitemap_reads_pages_from_project_root_not_output_dir(tmp_path):
    root = _fake_root(tmp_path)
    out = tmp_path / "elsewhere" / "deep" / "sitemap.xml"
    generate_sitemap([{"slug": "a-race", "tier": 2}], out, project_root=root)
    locs = _locs(out)
    base = "https://roadielabs.com"
    assert f"{base}/race/a-race/" in locs
    assert f"{base}/race/a-race-vs-b-race/" in locs
    assert f"{base}/race/best-road-races-utopia/" in locs
    assert f"{base}/race/a-race/training-plan/" in locs
    assert f"{base}/race/a-race/prep-kit/" in locs
    assert f"{base}/guide/chapter-one/" in locs
    for path in ("/about/", "/coaching/", "/consulting/", "/season-plan/", "/guide/"):
        assert f"{base}{path}" in locs
    # A plan page whose race has no race page stays out.
    assert f"{base}/race/flagged-race/training-plan/" not in locs


def test_committed_sitemap_lists_every_race_page():
    xml = (ROOT / "web" / "sitemap.xml").read_text(encoding="utf-8")
    assert sitemap_missing_race_pages(xml, RACE_INDEX) == []


def test_sitemap_gate_catches_a_sitemap_without_race_pages():
    xml = ("<urlset><url><loc>https://roadielabs.com/race/a-race/training-plan/</loc>"
           "</url></urlset>")
    assert sitemap_missing_race_pages(xml, [{"slug": "a-race"}]) == ["a-race"]


def test_deploy_content_ships_the_sitemap():
    src = (ROOT / "scripts" / "push_wordpress.py").read_text(encoding="utf-8")
    block = src[src.index("if args.deploy_content:"):src.index("if args.deploy_all:")]
    assert "args.sync_sitemap = True" in block


def test_vs_pair_selection_is_the_same_in_every_process():
    # select_pairs builds a set; string hashing differs per process, so
    # without a full tie-break the 150-pair cap picked different pages on
    # each run. Two hash seeds must give the same list.
    code = ("import json,sys; sys.path.insert(0, 'wordpress'); "
            "from generate_vs_pages import select_pairs; "
            "print(json.dumps(select_pairs(json.load(open('web/race-index.json')))))")
    runs = [
        subprocess.run([sys.executable, "-c", code], cwd=ROOT, capture_output=True,
                       text=True, check=True, env={**os.environ, "PYTHONHASHSEED": seed}).stdout
        for seed in ("1", "2")
    ]
    assert runs[0] == runs[1]
    assert json.loads(runs[0]) == [list(p) for p in select_pairs(RACE_INDEX)]


def test_race_page_links_state_hub_and_vs_pages_but_not_plan_page():
    hit = None
    for r in RACE_INDEX:
        html = build_explore_links({"slug": r["slug"], "name": r["name"]}, RACE_INDEX)
        if "best-road-races-" in html and "-vs-" in html:
            hit = html
            break
    assert hit, "expected at least one race with a hub and a vs page"
    assert "/training-plan/" not in hit


def test_missing_elevation_never_renders_none():
    rd = load_race_data(ROOT / "race-data" / "ocbc-cycle-singapore.json")
    assert rd["vitals"]["elevation"] != "None"


def test_description_without_tagline_names_the_race():
    rd = {"slug": "x", "name": "Test Fondo", "tagline": "", "overall_score": 64,
          "tier": 2, "vitals": {"location": "--"}}
    assert build_seo_description(rd).startswith("Test Fondo race review.")


def test_tier_hub_titles_use_live_counts():
    tier1 = [r for r in RACE_INDEX if r.get("tier") == 1]
    html = generate_tier_hubs.build_hub_page(1, tier1, RACE_INDEX)
    assert f"<title>The {len(tier1)} Best Road Races" in html
    assert "{count}" not in html
    assert "&amp;mdash;" not in html


def test_plan_pages_skip_races_whose_plan_commerce_is_off():
    assert plan_page_excluded({"catalog_flags": {"discipline_mismatch": "mtb"}})
    assert plan_page_excluded({"eligibility": {"status": "defunct"}})
    assert plan_page_excluded({"training_plan_clearance": {"status": "source_blocked"}})
    assert not plan_page_excluded({"catalog_flags": {"status_note": "x", "ruled": "y"}})
