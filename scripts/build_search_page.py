#!/usr/bin/env python3
"""Wrap the embeddable race-search fragment in a complete HTML document.

web/road-labs-search.html is a headless fragment (built for a WordPress
shortcode that no longer exists — the live site is static). Served bare it has
no <head>: no title, no meta description, no canonical, no GA4, and no site
header/footer. This script produces the two full pages the static site serves:

  wordpress/output/road-races/index.html   canonical self (/road-races/ is canonical)
  wordpress/output/search/index.html       canonical -> /road-races/ (duplicate URL)

Deploy both to the matching public_html dirs. /search/ keeps hosting the
shared assets (race-index.json, road-labs-search.js, rl-search.css).

Usage:
    python3 scripts/build_search_page.py
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "wordpress"))

from brand_tokens import get_ga4_head_snippet  # noqa: E402
from shared_footer import get_mega_footer_css, get_mega_footer_html  # noqa: E402
from shared_header import get_site_header_css, get_site_header_html  # noqa: E402

SITE_BASE_URL = "https://roadielabs.com"
CANONICAL = f"{SITE_BASE_URL}/road-races/"

TITLE = "Road Race Search — 427 Rated Races | Roadie Labs"
META_DESCRIPTION = (
    "Search 427 road races — gran fondos, sportives, hillclimbs — each scored "
    "on 14 base dimensions plus cultural impact. Filter by distance, climbing, region, month, and tier."
)


def build_page(fragment: str) -> str:
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{TITLE}</title>
<meta name="description" content="{META_DESCRIPTION}">
<link rel="canonical" href="{CANONICAL}">
{get_ga4_head_snippet()}
<style>
{get_site_header_css()}
{get_mega_footer_css()}
</style>
</head>
<body>
{get_site_header_html(active="races")}
{fragment}
{get_mega_footer_html()}
</body>
</html>
"""


def main() -> int:
    fragment = (PROJECT_ROOT / "web" / "road-labs-search.html").read_text(encoding="utf-8")
    page = build_page(fragment)
    for out_dir in ("road-races", "search"):
        target = PROJECT_ROOT / "wordpress" / "output" / out_dir
        target.mkdir(parents=True, exist_ok=True)
        (target / "index.html").write_text(page, encoding="utf-8")
        print(f"Generated {target / 'index.html'} ({len(page):,} bytes)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
