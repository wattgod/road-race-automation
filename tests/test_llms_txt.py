"""Regression tests for web/llms.txt content (audit 2026-11-14)."""

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

import generate_llms_txt as g  # noqa: E402


def _index():
    return json.loads((PROJECT_ROOT / "web" / "race-index.json").read_text())


def test_contact_is_matti_address_not_matt():
    text = g.generate_llms_txt(_index())
    assert "Email: gravelgodcoaching@gmail.com" in text
    assert "matt@" not in text.lower()


def test_markdown_example_is_a_real_roadie_race():
    index = _index()
    assert g.EXAMPLE_SLUG in {r["slug"] for r in index}
    assert (PROJECT_ROOT / "race-data" / f"{g.EXAMPLE_SLUG}.json").exists()
    text = g.generate_llms_txt(index)
    assert f"/race/{g.EXAMPLE_SLUG}.md" in text
    assert "unbound" not in text.lower()


def test_example_omitted_when_slug_not_in_index():
    text = g.generate_llms_txt([{"slug": "some-other-race", "tier": 2}])
    assert "e.g." not in text


def test_counts_are_pluralised():
    text = g.generate_llms_txt([{"slug": "a", "tier": 4}])
    assert "1 races" not in text
    assert "1 entries" not in text
    assert "1 race rated" in text
    assert "**Tier 4 (Local)**: 1 race " in text
    full = g.generate_llms_full_txt([{"slug": "a", "tier": 4}], PROJECT_ROOT / "race-data")
    assert "1 races" not in full and "1 road cycling events" not in full
