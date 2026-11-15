"""/road-races/ title and description count the races in the index (issue #166).

The title said "427 Rated Races" while web/race-index.json held 421.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from build_search_page import build_page, race_count  # noqa: E402

FRAGMENT = (ROOT / "web" / "road-labs-search.html").read_text(encoding="utf-8")


def test_count_matches_the_committed_index():
    index = json.loads((ROOT / "web" / "race-index.json").read_text(encoding="utf-8"))
    assert race_count() == len(index)


def test_page_states_the_index_count(tmp_path):
    index = tmp_path / "race-index.json"
    index.write_text(json.dumps([{"slug": f"r{i}"} for i in range(7)]), encoding="utf-8")
    html = build_page(FRAGMENT, race_count(index))
    assert "<title>Road Race Search — 7 Rated Races | Roadie Labs</title>" in html
    assert 'content="Search 7 road races' in html


def test_empty_index_refuses(tmp_path):
    index = tmp_path / "race-index.json"
    index.write_text("[]", encoding="utf-8")
    with pytest.raises(ValueError):
        race_count(index)


def test_no_hardcoded_count_in_source():
    src = (ROOT / "scripts" / "build_search_page.py").read_text(encoding="utf-8")
    assert not re.search(r"\b\d{3} (Rated Races|road races)", src)
