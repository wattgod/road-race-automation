"""Rendered-copy guardrails for Roadie Labs trust language."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
WORDPRESS_DIR = PROJECT_ROOT / "wordpress"
if str(WORDPRESS_DIR) not in sys.path:
    sys.path.insert(0, str(WORDPRESS_DIR))

import generate_about  # noqa: E402
import generate_homepage  # noqa: E402
import generate_methodology  # noqa: E402


BANNED_PATTERNS = [
    r"honestly rated",
    r"honest review",
    r"unbiased",
    r"no sponsors",
    r"zero sponsors",
    r"pay-to-play",
]


def _assert_restrained(name: str, html: str) -> None:
    lowered = html.lower()
    for pattern in BANNED_PATTERNS:
        assert not re.search(pattern, lowered), f"{name} contains banned copy: {pattern}"


def test_generated_homepage_about_methodology_avoid_defensive_trust_copy(monkeypatch):
    monkeypatch.setattr(generate_homepage, "fetch_substack_posts", lambda: [])
    race_index = json.loads((PROJECT_ROOT / "web" / "race-index.json").read_text())

    pages = {
        "homepage": generate_homepage.generate_homepage(
            race_index,
            race_data_dir=PROJECT_ROOT / "race-data",
            guide_path=PROJECT_ROOT / "guide" / "road-guide-content.json",
        ),
        "about": generate_about.generate_about_page(),
        "methodology": generate_methodology.generate_methodology_page(),
    }

    for name, html in pages.items():
        _assert_restrained(name, html)
