#!/usr/bin/env python3
"""Regenerate the Static Race Directory block in web/road-labs-search.html.

The search page is JS-driven (renders cards from race-index.json client-side),
but it also ships a crawlable, no-JS "Race Directory" — a tier-grouped list of
every race with a deep link to its review. That block was copied wholesale from
the gravel search page, so it listed 327 GRAVEL races (and gravel tier names
like "The Icons") on the road domain: customer-facing wrong links + an SEO
liability. This generator rebuilds it from web/race-index.json so it always
mirrors the live road catalog.

The block is rewritten in place between the HTML markers:
    <!-- Static Race Directory ... -->  ...  <!-- End Race Directory -->

Usage: python3 scripts/generate_race_directory.py [--check]
  --check  Exit 1 if the file would change (CI guard), don't write.
"""

import argparse
import html
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
INDEX_PATH = ROOT / "web" / "race-index.json"
SEARCH_PATH = ROOT / "web" / "road-labs-search.html"

# Customer-facing tier labels — must match wordpress/generate_homepage.py.
TIER_LABELS = {1: "Elite", 2: "Contender", 3: "Rising", 4: "Local"}

START_RE = re.compile(
    r"  <!-- Static Race Directory[^\n]*-->\n.*?  <!-- End Race Directory -->",
    re.DOTALL,
)


def _load_races():
    data = json.loads(INDEX_PATH.read_text())
    return data if isinstance(data, list) else data.get("races", [])


def _tier_of(race):
    return race.get("tier") or (race.get("fondo_rating") or {}).get("tier")


def build_directory_html(races) -> str:
    by_tier = {1: [], 2: [], 3: [], 4: []}
    for r in races:
        t = _tier_of(r)
        if t in by_tier:
            by_tier[t].append(r)

    lines = [
        "  <!-- Static Race Directory — crawlable by search engines, independent of JS -->",
        '  <div class="rl-race-directory">',
        '    <h2 class="rl-directory-heading">Race Directory</h2>',
        '    <p class="rl-directory-desc">Browse all road races rated by Roadie Labs. '
        "Click any race for the full review with course maps, ratings, and logistics.</p>",
    ]

    for tier in (1, 2, 3, 4):
        group = by_tier[tier]
        if not group:
            continue
        # Highest score first, then alphabetical for stable diffs.
        group.sort(key=lambda r: (-(r.get("overall_score") or 0), r.get("name", "")))
        label = TIER_LABELS[tier]
        lines.append('    <div class="rl-directory-tier">')
        lines.append(
            f'      <h3 class="rl-directory-tier-heading tier-{tier}">'
            f"Tier {tier} — {label} ({len(group)})</h3>"
        )
        lines.append('      <div class="rl-directory-links">')
        for r in group:
            slug = html.escape(r.get("slug", ""), quote=True)
            name = html.escape(r.get("name", r.get("slug", "")))
            lines.append(
                f'        <a href="/race/{slug}/" class="rl-directory-link">{name}</a>'
            )
        lines.append("      </div>")
        lines.append("    </div>")

    lines.append("  </div>")
    lines.append("  <!-- End Race Directory -->")
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="Exit 1 if file would change")
    args = ap.parse_args()

    races = _load_races()
    block = build_directory_html(races)
    original = SEARCH_PATH.read_text()

    if not START_RE.search(original):
        print("ERROR: directory markers not found in", SEARCH_PATH, file=sys.stderr)
        return 2

    updated = START_RE.sub(lambda _m: block, original, count=1)

    if args.check:
        if updated != original:
            print("Race directory is STALE — run generate_race_directory.py")
            return 1
        print("Race directory up to date.")
        return 0

    if updated == original:
        print("Race directory already current (no change).")
        return 0

    SEARCH_PATH.write_text(updated)
    n = sum(1 for r in races if _tier_of(r) in (1, 2, 3, 4))
    print(f"Rebuilt race directory: {n} races → {SEARCH_PATH}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
