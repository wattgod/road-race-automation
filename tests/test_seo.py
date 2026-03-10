"""SEO regression tests.

Covers:
- Homepage title/meta length bounds, year freshness, count stability
- Sitemap ↔ race-index parity (every race in index must have a sitemap URL)
- Sitemap integrity (no duplicates, valid format, accurate URL counts)
- State hub page overlap detection (no content cannibalization)
- State hub discipline-aware titles (Italy shouldn't say "Gravel" when 86% road)
- State hub meta description length bounds
- Deploy script count accuracy
- Criteria count consistency
"""

import json
import re
import sys
from collections import Counter
from pathlib import Path

import pytest

# Ensure wordpress/ is importable
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "wordpress"))

PROJECT_ROOT = Path(__file__).resolve().parent.parent


# ── Fixtures ──────────────────────────────────────────────────


@pytest.fixture(scope="module")
def race_index():
    index_path = PROJECT_ROOT / "web" / "race-index.json"
    if not index_path.exists():
        pytest.skip("race-index.json not found")
    with open(index_path) as f:
        return json.load(f)


@pytest.fixture(scope="module")
def sitemap_text():
    sitemap_path = PROJECT_ROOT / "web" / "sitemap.xml"
    if not sitemap_path.exists():
        pytest.skip("sitemap.xml not found")
    return sitemap_path.read_text()


@pytest.fixture(scope="module")
def homepage_html():
    hp_path = PROJECT_ROOT / "wordpress" / "output" / "homepage.html"
    if not hp_path.exists():
        pytest.skip("homepage.html not found — run generate_homepage.py first")
    return hp_path.read_text()


@pytest.fixture(scope="module")
def state_hub_pages():
    """Return dict of slug → HTML content for all state hub pages."""
    output_dir = PROJECT_ROOT / "wordpress" / "output"
    pages = {}
    for d in output_dir.iterdir():
        if d.is_dir() and d.name.startswith("best-gravel-races-"):
            index = d / "index.html"
            if index.exists():
                pages[d.name] = index.read_text()
    if not pages:
        pytest.skip("No state hub pages found")
    return pages


# ── Homepage SEO ──────────────────────────────────────────────


class TestHomepageSEO:
    def test_title_length_within_google_limit(self, homepage_html):
        """Title tag should be <= 60 chars to avoid truncation in SERPs."""
        match = re.search(r"<title>([^<]+)</title>", homepage_html)
        assert match, "Homepage must have a <title> tag"
        title = match.group(1).replace("&amp;", "&")
        assert len(title) <= 60, (
            f"Title '{title}' is {len(title)} chars — Google truncates at ~60"
        )

    def test_title_contains_year(self, homepage_html):
        """Title must contain current year for freshness signal."""
        from datetime import date
        year = str(date.today().year)
        match = re.search(r"<title>([^<]+)</title>", homepage_html)
        assert year in match.group(1), (
            f"Title must contain {year} for freshness signal"
        )

    def test_title_count_is_stable(self, homepage_html):
        """Title must use rounded count (e.g., '750+') not exact (e.g., '757')."""
        match = re.search(r"<title>([^<]+)</title>", homepage_html)
        title = match.group(1)
        # Should contain a round number followed by "+"
        count_match = re.search(r"(\d+)\+?\s", title)
        assert count_match, "Title should contain a race count"
        count = int(count_match.group(1))
        assert count % 50 == 0, (
            f"Title count {count} is not rounded to nearest 50 — "
            f"exact counts cause title churn when races are added"
        )

    def test_meta_description_length(self, homepage_html):
        """Meta description must be 50-160 chars."""
        match = re.search(
            r'<meta\s+name="description"\s+content="([^"]+)"', homepage_html
        )
        assert match, "Homepage must have a meta description"
        desc = match.group(1).replace("&amp;", "&").replace("&#x27;", "'")
        assert 50 <= len(desc) <= 160, (
            f"Meta description is {len(desc)} chars (must be 50-160): '{desc}'"
        )

    def test_og_title_matches_page_title(self, homepage_html):
        """OG title must match page title for consistent SERP signals."""
        title_match = re.search(r"<title>([^<]+)</title>", homepage_html)
        og_match = re.search(
            r'<meta\s+property="og:title"\s+content="([^"]+)"', homepage_html
        )
        assert title_match and og_match, "Must have both title and og:title"
        assert title_match.group(1) == og_match.group(1), (
            f"Title and OG title mismatch: '{title_match.group(1)}' vs '{og_match.group(1)}'"
        )

    def test_schema_criteria_count_matches(self, homepage_html):
        """Schema.org description must say '15 criteria' (matches actual count)."""
        # Check all schema blocks
        schema_blocks = re.findall(
            r'<script type="application/ld\+json">([^<]+)</script>', homepage_html
        )
        for block in schema_blocks:
            if "criteria" in block:
                assert "15 criteria" in block, (
                    f"Schema says wrong criteria count: {block[:200]}"
                )


# ── Sitemap Integrity ─────────────────────────────────────────


class TestSitemapIntegrity:
    def test_every_race_in_sitemap(self, race_index, sitemap_text):
        """Every race in race-index.json must have a URL in the sitemap."""
        missing = []
        for race in race_index:
            slug = race.get("slug", "")
            expected_url = f"/race/{slug}/"
            if expected_url not in sitemap_text:
                missing.append(slug)
        assert not missing, (
            f"{len(missing)} races missing from sitemap (first 10): "
            f"{missing[:10]}"
        )

    def test_no_duplicate_page_urls(self, sitemap_text):
        """No duplicate <url><loc> entries in the sitemap."""
        urls = re.findall(r"<loc>(https://[^<]+)</loc>", sitemap_text)
        # Filter to only page URLs (exclude image:loc which are nested)
        page_urls = [u for u in urls if "/race/" in u or u.endswith(".com/")]
        dupes = [u for u, c in Counter(page_urls).items() if c > 1]
        assert not dupes, (
            f"{len(dupes)} duplicate URLs in sitemap: {dupes[:5]}"
        )

    def test_sitemap_url_count_matches_xml(self, sitemap_text):
        """URL count from <url> elements must match expected."""
        url_count = len(re.findall(r"<url>", sitemap_text))
        loc_count = sitemap_text.count("<loc>")
        # <url> count should be <= <loc> count (images add extra <loc>)
        assert url_count <= loc_count, (
            "Counting <url> should give fewer or equal results than <loc>"
        )
        assert url_count > 0, "Sitemap has no URLs"

    def test_state_hub_urls_in_sitemap(self, sitemap_text, state_hub_pages):
        """Every generated state hub page must be in the sitemap."""
        missing = []
        for slug in state_hub_pages:
            expected = f"/race/{slug}/"
            if expected not in sitemap_text:
                missing.append(slug)
        assert not missing, (
            f"{len(missing)} state hub pages missing from sitemap: {missing}"
        )


# ── State Hub Pages ───────────────────────────────────────────


class TestStateHubOverlap:
    """Detect content cannibalization from overlapping region pages."""

    KNOWN_SUBREGIONS = {
        # sub-region → parent that should absorb it
        "england": "uk",
        "scotland": "uk",
        "wales": "uk",
        "northern-ireland": "uk",
        "british-columbia": "canada",
        "ontario": "canada",
        "quebec": "canada",
        "alberta": "canada",
        "south-australia": "australia",
        "victoria": "australia",
        "new-south-wales": "australia",
        "queensland": "australia",
    }

    def test_no_subregion_pages_exist(self, state_hub_pages):
        """Sub-region pages must be merged into parent (e.g., no England page when UK exists)."""
        violations = []
        for slug in state_hub_pages:
            region = slug.replace("best-gravel-races-", "")
            if region in self.KNOWN_SUBREGIONS:
                parent = self.KNOWN_SUBREGIONS[region]
                parent_slug = f"best-gravel-races-{parent}"
                if parent_slug in state_hub_pages:
                    violations.append(
                        f"'{region}' should be merged into '{parent}'"
                    )
        assert not violations, (
            f"Content cannibalization: {violations}"
        )


class TestStateHubTitles:
    """Verify state hub pages have discipline-aware, SEO-compliant titles."""

    def test_title_length_within_limit(self, state_hub_pages):
        """All state hub page titles must be <= 60 chars."""
        violations = []
        for slug, html in state_hub_pages.items():
            match = re.search(r"<title>([^<]+)</title>", html)
            if match:
                title = match.group(1).replace("&amp;", "&")
                if len(title) > 60:
                    violations.append(f"{slug}: '{title}' ({len(title)} chars)")
        assert not violations, (
            f"{len(violations)} titles exceed 60 chars: {violations[:5]}"
        )

    def test_title_contains_year(self, state_hub_pages):
        """All state hub titles must contain current year."""
        from datetime import date
        year = str(date.today().year)
        missing = []
        for slug, html in state_hub_pages.items():
            match = re.search(r"<title>([^<]+)</title>", html)
            if match and year not in match.group(1):
                missing.append(slug)
        assert not missing, (
            f"{len(missing)} state hub titles missing year: {missing[:5]}"
        )

    def test_discipline_aware_titles(self, state_hub_pages, race_index):
        """Pages for road-dominant regions must NOT say 'Gravel Races'."""
        from generate_state_hubs import group_races_by_state, _discipline_label
        grouped = group_races_by_state(race_index)

        violations = []
        for state, races in grouped.items():
            disc_label = _discipline_label(races)
            from generate_state_hubs import _slugify
            slug = f"best-gravel-races-{_slugify(state)}"
            if slug not in state_hub_pages:
                continue
            html = state_hub_pages[slug]
            match = re.search(r"<title>([^<]+)</title>", html)
            if not match:
                continue
            title = match.group(1).replace("&amp;", "&")
            if disc_label != "Gravel" and "Best Gravel Races" in title:
                violations.append(
                    f"{slug}: title says 'Gravel Races' but discipline is '{disc_label}'"
                )
        assert not violations, (
            f"Discipline-title mismatch: {violations}"
        )

    def test_meta_description_length(self, state_hub_pages):
        """All state hub meta descriptions must be 50-160 chars."""
        violations = []
        for slug, html in state_hub_pages.items():
            match = re.search(
                r'<meta\s+name="description"\s+content="([^"]+)"', html
            )
            if match:
                desc = match.group(1).replace("&amp;", "&")
                if len(desc) < 50 or len(desc) > 160:
                    violations.append(f"{slug}: {len(desc)} chars")
        assert not violations, (
            f"{len(violations)} meta descriptions out of range (50-160): "
            f"{violations[:5]}"
        )

    def test_h1_matches_title_discipline(self, state_hub_pages):
        """H1 must use the same discipline label as the title."""
        violations = []
        for slug, html in state_hub_pages.items():
            title_match = re.search(r"<title>Best (\w[\w &]*) Races", html)
            h1_match = re.search(r"<h1>Best (\w[\w &]*) Races", html)
            if title_match and h1_match:
                title_disc = title_match.group(1)
                h1_disc = h1_match.group(1)
                if title_disc != h1_disc:
                    violations.append(
                        f"{slug}: title='{title_disc}' h1='{h1_disc}'"
                    )
        assert not violations, (
            f"Title/H1 discipline mismatch: {violations}"
        )


# ── Deploy Script ─────────────────────────────────────────────


class TestDeployScript:
    def test_sitemap_count_uses_url_not_loc(self):
        """push_wordpress.py must count <url> elements, not <loc> (which includes images)."""
        push_script = PROJECT_ROOT / "scripts" / "push_wordpress.py"
        if not push_script.exists():
            pytest.skip("push_wordpress.py not found")
        content = push_script.read_text()
        # Must NOT count '<loc>' for URL count
        assert "count('<loc>')" not in content, (
            "push_wordpress.py counts '<loc>' which inflates URL count "
            "by including image sitemap entries"
        )

    def test_no_hardcoded_race_counts(self):
        """push_wordpress.py must not have hardcoded race/URL counts."""
        push_script = PROJECT_ROOT / "scripts" / "push_wordpress.py"
        if not push_script.exists():
            pytest.skip("push_wordpress.py not found")
        content = push_script.read_text()
        # Check for common hardcoded counts
        for count in ["328", "686", "707", "724", "742"]:
            # Allow in comments but not in print statements
            lines_with_count = [
                line.strip() for line in content.split("\n")
                if count in line and "print" in line and not line.strip().startswith("#")
            ]
            assert not lines_with_count, (
                f"Hardcoded count '{count}' found in print statement: "
                f"{lines_with_count[0]}"
            )


# ── Criteria Consistency ──────────────────────────────────────


class TestCriteriaConsistency:
    def test_all_races_have_at_least_14_criteria(self, race_index):
        """Every race must have at least 14 score criteria.

        Note: 'cultural_impact' (15th criterion) was added later and is
        missing from ~308 races. The scoring formula uses denominator 70
        (= 14 × 5) so both 14 and 15 criteria work correctly.
        """
        under_14 = [
            (r.get("slug"), len(r.get("scores", {})))
            for r in race_index
            if len(r.get("scores", {})) < 14
        ]
        assert not under_14, (
            f"{len(under_14)} races have fewer than 14 criteria: {under_14[:5]}"
        )

    def test_criteria_max_is_15(self, race_index):
        """No race should have more than 15 score criteria."""
        over_15 = [
            (r.get("slug"), len(r.get("scores", {})))
            for r in race_index
            if len(r.get("scores", {})) > 15
        ]
        assert not over_15, (
            f"{len(over_15)} races have more than 15 criteria: {over_15[:5]}"
        )

    def test_homepage_meta_says_15(self, homepage_html):
        """Homepage meta description must reference 15 criteria."""
        match = re.search(
            r'<meta\s+name="description"\s+content="([^"]+)"', homepage_html
        )
        assert match, "Homepage must have meta description"
        assert "15 criteria" in match.group(1), (
            f"Meta description says wrong criteria count: {match.group(1)}"
        )


# ── Region Merge Map ──────────────────────────────────────────


class TestRegionMergeMap:
    def test_merge_map_covers_all_subregions(self, race_index):
        """Any sub-region that appears in race data must be in REGION_MERGES
        if its parent also appears as a separate region."""
        from generate_state_hubs import REGION_MERGES, STATE_ABBR
        from collections import defaultdict

        # Group raw regions
        raw_regions = defaultdict(int)
        for r in race_index:
            loc = r.get("location", "")
            parts = [p.strip() for p in loc.split(",")]
            if len(parts) >= 2:
                state = parts[-1]
                if state in STATE_ABBR:
                    state = STATE_ABBR[state]
                raw_regions[state] += 1

        # Check for UK sub-regions not in merge map
        uk_subs = {"England", "Scotland", "Wales", "Northern Ireland"}
        for sub in uk_subs:
            if sub in raw_regions and sub not in REGION_MERGES:
                pytest.fail(
                    f"'{sub}' appears in race data ({raw_regions[sub]} races) "
                    f"but is not in REGION_MERGES — will create separate page"
                )
