"""Athlete-facing pages never position Roadie Labs against AI.

Matti (2026-11-14): "we never position ourselves against AI, never say we
don't use it, we just don't bring it up." Generated pages must not carry a
standalone "AI" or a "not an AI" / "teach an algorithm" / "software flags"
contrast. The privacy policy is exempt: its processor list ("AI service
providers") is a legal disclosure, not positioning.
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

ROOT = Path(__file__).resolve().parent.parent
WORDPRESS = ROOT / "wordpress"
sys.path.insert(0, str(WORDPRESS))

STANDALONE_AI = re.compile(r"\bAI\b")
CONTRASTS = [
    re.compile(r"\bnot an? (AI|algorithm|bot|robot|software|app)\b", re.I),
    re.compile(r"\bAI isn", re.I),
    re.compile(r"\b(teach|teaches|than|unlike|instead of) (an? |the )?(algorithm|AI|software|robot|bot)s?\b", re.I),
    re.compile(r"\bsoftware flags\b", re.I),
]
# Code, not copy: executable scripts and CSS. JSON-LD stays in (search
# engines show it), so only non-ld+json <script> blocks are dropped.
_CODE = re.compile(
    r"<script(?![^>]*application/ld\+json)[^>]*>.*?</script>|<style[^>]*>.*?</style>",
    re.S | re.I)


def _copy(html: str) -> str:
    return _CODE.sub(" ", html)


def _violations(html: str) -> list[str]:
    text = _copy(html)
    hits = [m.group(0) for m in STANDALONE_AI.finditer(text)]
    for pat in CONTRASTS:
        hits += [m.group(0) for m in pat.finditer(text)]
    return hits


def _race_pages():
    from generate_neo_brutalist import generate_page, normalize_race_data
    index = json.loads((ROOT / "web" / "race-index.json").read_text(encoding="utf-8"))
    pages = {}
    for slug in ("paris-brest-paris", "letape-du-tour"):
        path = ROOT / "race-data" / f"{slug}.json"
        if path.exists():
            data = json.loads(path.read_text(encoding="utf-8"))
            pages[f"race:{slug}"] = generate_page(normalize_race_data(data), index)
    assert pages, "no race pages generated"
    return pages


def _pages() -> dict[str, str]:
    from generate_about import generate_about_page
    from generate_coaching import generate_coaching_page
    from generate_coaching_apply import generate_apply_page
    from generate_consulting import generate_consulting_page
    from generate_courses_page import generate_courses_page
    from generate_homepage import generate_homepage, load_race_index
    from generate_methodology import generate_methodology_page
    from generate_success_pages import PAGES, generate_success_page
    from generate_training_plans import generate_training_page

    pages = {
        "about": generate_about_page(),
        "coaching": generate_coaching_page(),
        "coaching-apply": generate_apply_page(),
        "consulting": generate_consulting_page(),
        "courses": generate_courses_page(),
        "methodology": generate_methodology_page(),
        "training-plans": generate_training_page(),
    }
    with patch("generate_homepage.fetch_substack_posts", return_value=[]):
        pages["homepage"] = generate_homepage(load_race_index())
    for key in PAGES:
        pages[f"success:{key}"] = generate_success_page(key)
    pages.update(_race_pages())
    return pages


@pytest.fixture(scope="module")
def pages():
    return _pages()


@pytest.fixture(scope="module")
def legal_pages(tmp_path_factory):
    out = tmp_path_factory.mktemp("legal")
    subprocess.run([sys.executable, str(WORDPRESS / "generate_legal_pages.py"),
                    "--output-dir", str(out)],
                   check=True, capture_output=True, text=True, cwd=ROOT, timeout=120)
    return {p.stem: p.read_text(encoding="utf-8") for p in out.glob("*.html")}


@pytest.fixture(scope="module")
def tier_hubs(tmp_path_factory):
    out = tmp_path_factory.mktemp("hubs")
    subprocess.run([sys.executable, str(WORDPRESS / "generate_tier_hubs.py"),
                    "--output-dir", str(out)],
                   check=True, capture_output=True, text=True, cwd=ROOT, timeout=120)
    return {p.parent.name: p.read_text(encoding="utf-8") for p in out.glob("*/index.html")}


def test_detector_catches_the_retired_lines():
    for line in (
        "Not an AI, not a dashboard, not a coach who reads you like a spreadsheet.",
        "Hire a coach. (And no, AI isn&rsquo;t a person.)",
        "Software flags a number. I notice the interval you bailed on.",
        "not after three missed targets teach an algorithm what a person would see",
    ):
        assert _violations(f"<p>{line}</p>"), line
    assert not _violations("<p>I read every file.</p><script>var AI=1;</script>")


def test_generated_pages_never_position_against_ai(pages):
    bad = {name: hits for name, html in pages.items() if (hits := _violations(html))}
    assert not bad, bad


def test_legal_pages_except_privacy(legal_pages):
    assert "privacy" in legal_pages
    bad = {name: hits for name, html in legal_pages.items()
           if name != "privacy" and (hits := _violations(html))}
    assert not bad, bad


def test_privacy_processor_disclosure_is_kept(legal_pages):
    # Legal statement, deliberately exempt and unchanged.
    assert "AI service providers" in legal_pages["privacy"]


def test_tier_hubs(tier_hubs):
    assert len(tier_hubs) == 4
    bad = {name: hits for name, html in tier_hubs.items() if (hits := _violations(html))}
    assert not bad, bad
