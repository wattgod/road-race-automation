"""Guard the crawlable Race Directory in web/road-labs-search.html.

It once shipped 327 GRAVEL race links (copied from the gravel search page) on
the road domain. These tests ensure every directory link is a real road race
and that the block stays in sync with the generator.
"""

import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SEARCH_PATH = ROOT / "web" / "road-labs-search.html"
INDEX_PATH = ROOT / "web" / "race-index.json"
GEN = ROOT / "scripts" / "generate_race_directory.py"

LINK_RE = re.compile(r'/race/([a-z0-9-]+)/" class="rl-directory-link"')


def _road_slugs():
    data = json.loads(INDEX_PATH.read_text())
    races = data if isinstance(data, list) else data.get("races", [])
    return {r.get("slug") for r in races}


def _directory_slugs():
    return LINK_RE.findall(SEARCH_PATH.read_text())


def test_every_directory_link_is_a_real_road_race():
    road = _road_slugs()
    bad = [s for s in _directory_slugs() if s not in road]
    assert not bad, f"Directory links not in road race-index: {bad[:10]}"


def test_directory_covers_every_race():
    assert set(_directory_slugs()) == _road_slugs()


def test_no_gravel_series_block():
    # The gravel page had a "/race/series/..." block (Grinduro, Grasshopper).
    assert "/race/series/" not in SEARCH_PATH.read_text()


def test_no_gravel_tier_names():
    html = SEARCH_PATH.read_text()
    for gravel_label in ("The Icons", "Grassroots", "Tier 2 — Elite"):
        assert gravel_label not in html, f"Stale gravel tier label: {gravel_label}"


def test_generator_is_idempotent():
    # --check exits 1 if the committed file would change.
    result = subprocess.run(
        [sys.executable, str(GEN), "--check"], capture_output=True, text=True
    )
    assert result.returncode == 0, f"Directory is stale: {result.stdout}{result.stderr}"
