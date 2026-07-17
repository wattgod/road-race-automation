#!/usr/bin/env python3
"""Audit every staged Roadie Labs race page against the approved spine."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_OUTPUT = PROJECT_ROOT / "wordpress" / "output-spine-v2-stage"
EXPECTED_FORMAT = 'data-page-format="spine-v2-approved"'
GA_ID = "G-WQ7W8XN11N"


def audit_page(path: Path) -> list[str]:
    html = path.read_text(encoding="utf-8")
    issues: list[str] = []
    try:
        deep_start = html.index('id="deep-dive"')
        deep_end = html.index('<footer class="rl-mega-footer">', deep_start)
    except ValueError:
        return ["missing Deep Dive boundary"]

    top = html[:deep_start]
    deep = html[deep_start:deep_end]
    ordered = [
        'id="ratings"',
        'data-measure-section="custom-plan"',
        'data-measure-section="coaching"',
        'id="breakdown"',
        'id="deep-dive"',
        'id="course"',
        'id="training"',
        'id="train-for-race"',
    ]
    missing = [marker for marker in ordered if marker not in html]
    if missing:
        issues.append(f"missing required markers: {', '.join(missing)}")
    elif [html.index(marker) for marker in ordered] != sorted(
        html.index(marker) for marker in ordered
    ):
        issues.append("approved sections are out of order")

    if html.count(EXPECTED_FORMAT) != 1:
        issues.append("missing or duplicated approved page-format marker")
    if top.count("START MY CUSTOM PLAN &rarr;") != 1:
        issues.append("custom-plan CTA must appear exactly once above Deep Dive")
    if top.count("GET ME IN YOUR CORNER &rarr;") != 1:
        issues.append("coaching CTA must appear exactly once above Deep Dive")
    if 'id="verdict"' in html:
        issues.append("standalone verdict is present")

    forbidden = [
        "BUILD MY PLAN",
        "PREVIEW MY PLAN",
        "rl-cfg-bar",
        "rl-pack-cta",
        "/training-plan/",
        "/coaching/",
        "rl-sticky-cta",
        "questionnaire",
    ]
    deep_lower = deep.lower()
    leaked = [marker for marker in forbidden if marker.lower() in deep_lower]
    if leaked:
        issues.append(f"commerce leaked into Deep Dive: {', '.join(leaked)}")

    if "https://roadielabs.com/race/" not in html:
        issues.append("Roadie Labs canonical URL is missing")
    if GA_ID not in html:
        issues.append("Roadie Labs GA4 property is missing")
    if 'class="gg-' in html or "--gg-" in html:
        issues.append("Gravel God brand token/class leaked into Roadie Labs")

    ids = re.findall(r'\bid="([^"]+)"', html)
    duplicates = sorted({value for value in ids if ids.count(value) > 1})
    if duplicates:
        issues.append(f"duplicate IDs: {', '.join(duplicates)}")
    return issues


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    pages = sorted(args.output_dir.glob("*.html"))
    expected = len(list((PROJECT_ROOT / "race-data").glob("*.json")))
    failures = [(page.name, audit_page(page)) for page in pages]
    failures = [(name, issues) for name, issues in failures if issues]

    if len(pages) != expected:
        print(f"FAIL: found {len(pages)} staged pages; expected {expected}")
        return 1
    if failures:
        for name, issues in failures:
            for issue in issues:
                print(f"FAIL: {name}: {issue}")
        print(f"FAIL: {len(failures)}/{len(pages)} pages violated the approved spine")
        return 1
    print(f"PASS: {len(pages)} Roadie Labs pages match the approved spine")
    return 0


if __name__ == "__main__":
    sys.exit(main())
