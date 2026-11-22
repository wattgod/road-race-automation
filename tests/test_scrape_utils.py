"""Tests for scrape_utils.py — cache, Cloudflare detection, site loading, extraction."""

import json
import time
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from scrape_utils import (
    _cache_key,
    get_cached,
    set_cached,
    is_cloudflare_blocked,
    load_official_sites,
    _truncate_html,
    _build_extraction_prompt,
    load_extract,
    save_extract,
    CACHE_TTL_SECONDS,
    MAX_HTML_FOR_CLAUDE,
    CLOUDFLARE_MARKERS,
    SCRAPE_CACHE_DIR,
    SCRAPE_EXTRACTS_DIR,
    RACE_DATA_DIR,
)


# ---------------------------------------------------------------------------
# Cache key determinism
# ---------------------------------------------------------------------------

class TestCacheKey:
    def test_deterministic(self):
        """Same URL always produces same cache key."""
        url = "https://unboundgravel.com"
        assert _cache_key(url) == _cache_key(url)

    def test_different_urls_differ(self):
        """Different URLs produce different keys."""
        assert _cache_key("https://a.com") != _cache_key("https://b.com")

    def test_length(self):
        """Cache key is 16 hex chars."""
        key = _cache_key("https://example.com")
        assert len(key) == 16
        assert all(c in "0123456789abcdef" for c in key)

    def test_special_chars(self):
        """URLs with special chars produce valid keys."""
        key = _cache_key("https://example.com/path?q=hello world&x=1#frag")
        assert len(key) == 16
        assert all(c in "0123456789abcdef" for c in key)

    def test_unicode_url(self):
        """Unicode in URL doesn't crash."""
        key = _cache_key("https://example.com/räce/über")
        assert len(key) == 16


# ---------------------------------------------------------------------------
# Cache round-trip
# ---------------------------------------------------------------------------

class TestCacheRoundTrip:
    def test_set_and_get(self, tmp_path, monkeypatch):
        """Cached data can be retrieved."""
        monkeypatch.setattr("scrape_utils.SCRAPE_CACHE_DIR", tmp_path)
        url = "https://unboundgravel.com"
        set_cached(url, "<html>hello</html>", 200, "fetcher")
        result = get_cached(url)
        assert result is not None
        assert result["html"] == "<html>hello</html>"
        assert result["status"] == 200
        assert result["fetcher"] == "fetcher"
        assert result["url"] == url

    def test_miss_returns_none(self, tmp_path, monkeypatch):
        """Non-cached URL returns None."""
        monkeypatch.setattr("scrape_utils.SCRAPE_CACHE_DIR", tmp_path)
        assert get_cached("https://nonexistent.example.com") is None

    def test_expired_returns_none(self, tmp_path, monkeypatch):
        """Expired cache entry returns None."""
        monkeypatch.setattr("scrape_utils.SCRAPE_CACHE_DIR", tmp_path)
        url = "https://expired.example.com"
        set_cached(url, "<html>old</html>", 200, "fetcher")
        # Backdate the timestamp
        path = tmp_path / f"{_cache_key(url)}.json"
        data = json.loads(path.read_text())
        data["timestamp"] = time.time() - CACHE_TTL_SECONDS - 1
        path.write_text(json.dumps(data))
        assert get_cached(url) is None

    def test_fresh_cache_within_ttl(self, tmp_path, monkeypatch):
        """Cache entry just within TTL is returned."""
        monkeypatch.setattr("scrape_utils.SCRAPE_CACHE_DIR", tmp_path)
        url = "https://fresh.example.com"
        set_cached(url, "<html>fresh</html>", 200, "fetcher")
        # Backdate but still within TTL
        path = tmp_path / f"{_cache_key(url)}.json"
        data = json.loads(path.read_text())
        data["timestamp"] = time.time() - CACHE_TTL_SECONDS + 60
        path.write_text(json.dumps(data))
        result = get_cached(url)
        assert result is not None
        assert result["html"] == "<html>fresh</html>"

    def test_corrupt_cache_returns_none(self, tmp_path, monkeypatch):
        """Corrupt JSON in cache returns None."""
        monkeypatch.setattr("scrape_utils.SCRAPE_CACHE_DIR", tmp_path)
        url = "https://corrupt.example.com"
        path = tmp_path / f"{_cache_key(url)}.json"
        path.write_text("NOT VALID JSON {{{")
        assert get_cached(url) is None

    def test_null_html_cached(self, tmp_path, monkeypatch):
        """None html value round-trips correctly (failed fetch)."""
        monkeypatch.setattr("scrape_utils.SCRAPE_CACHE_DIR", tmp_path)
        url = "https://failed.example.com"
        set_cached(url, None, 403, "http_403")
        result = get_cached(url)
        assert result is not None
        assert result["html"] is None
        assert result["status"] == 403

    def test_creates_directory(self, tmp_path, monkeypatch):
        """set_cached creates cache directory if missing."""
        cache_dir = tmp_path / "deep" / "nested" / "cache"
        monkeypatch.setattr("scrape_utils.SCRAPE_CACHE_DIR", cache_dir)
        set_cached("https://example.com", "<html/>", 200, "fetcher")
        assert cache_dir.exists()


# ---------------------------------------------------------------------------
# Cloudflare detection
# ---------------------------------------------------------------------------

class TestCloudflareDetection:
    def test_detects_challenge_page(self):
        """Detects 'Just a moment' Cloudflare challenge."""
        html = """<!DOCTYPE html><html><head><title>Just a moment...</title>
        </head><body>Enable JavaScript and cookies to continue</body></html>"""
        assert is_cloudflare_blocked(html) is True

    def test_detects_cf_browser_verification(self):
        """Detects cf-browser-verification marker."""
        html = '<div id="cf-browser-verification">Verifying...</div>'
        assert is_cloudflare_blocked(html) is True

    def test_detects_cf_chl_opt(self):
        """Detects _cf_chl_opt script variable."""
        html = '<script>window._cf_chl_opt = {cType: "managed"};</script>'
        assert is_cloudflare_blocked(html) is True

    def test_normal_page_not_blocked(self):
        """Normal HTML is not flagged as Cloudflare blocked."""
        html = """<!DOCTYPE html><html><head><title>Unbound Gravel</title>
        </head><body><h1>Welcome to Unbound</h1><p>Register now!</p></body></html>"""
        assert is_cloudflare_blocked(html) is False

    def test_none_input(self):
        """None html returns False (not blocked)."""
        assert is_cloudflare_blocked(None) is False

    def test_empty_string(self):
        """Empty string returns False."""
        assert is_cloudflare_blocked("") is False

    def test_marker_deep_in_page_ignored(self):
        """Cloudflare markers past first 5000 chars are ignored (normal content)."""
        html = "x" * 5001 + "Just a moment"
        assert is_cloudflare_blocked(html) is False


# ---------------------------------------------------------------------------
# load_official_sites
# ---------------------------------------------------------------------------

class TestLoadOfficialSites:
    def test_loads_from_real_data(self):
        """Loads at least some races from actual race-data/."""
        sites = load_official_sites()
        assert len(sites) > 200  # we know ~289 have URLs

    def test_known_race_present(self):
        """A known T1 race is in the results."""
        sites = load_official_sites(slug_filter="gfny-lourdes-tourmalet")
        assert "gfny-lourdes-tourmalet" in sites
        assert "gfny.com" in sites["gfny-lourdes-tourmalet"]["url"]
        assert sites["gfny-lourdes-tourmalet"]["tier"] == 1

    def test_tier_filter(self):
        """Tier filter narrows results."""
        all_sites = load_official_sites()
        t1_only = load_official_sites(tier_filters={1})
        assert len(t1_only) < len(all_sites)
        for info in t1_only.values():
            assert info["tier"] == 1

    def test_slug_filter(self):
        """Slug filter returns at most one result."""
        sites = load_official_sites(slug_filter="unbound-200")
        assert len(sites) <= 1

    def test_structure(self):
        """Each entry has required keys."""
        sites = load_official_sites(slug_filter="unbound-200")
        if "unbound-200" in sites:
            info = sites["unbound-200"]
            assert "url" in info
            assert "name" in info
            assert "tier" in info
            assert "date_specific" in info

    def test_no_non_http_urls(self):
        """All returned URLs start with http."""
        sites = load_official_sites()
        for slug, info in sites.items():
            assert info["url"].startswith("http"), f"{slug} has non-HTTP URL: {info['url']}"


# ---------------------------------------------------------------------------
# HTML truncation
# ---------------------------------------------------------------------------

class TestTruncateHtml:
    def test_short_html_unchanged(self):
        """HTML under limit is returned as-is."""
        html = "<html><body>Hello</body></html>"
        assert _truncate_html(html) == html

    def test_long_html_truncated(self):
        """HTML over limit is truncated to MAX_HTML_FOR_CLAUDE chars."""
        html = "x" * (MAX_HTML_FOR_CLAUDE + 5000)
        result = _truncate_html(html)
        assert len(result) <= MAX_HTML_FOR_CLAUDE

    def test_extracts_main_tag(self):
        """Prefers <main> content when available."""
        main_content = "<p>" + "real content " * 100 + "</p>"
        html = "<html><head><style>" + "x" * 200000 + "</style></head>"
        html += f"<main>{main_content}</main></html>"
        result = _truncate_html(html)
        assert "real content" in result

    def test_strips_script_tags(self):
        """Strips <script> tags from truncated output."""
        html = "<script>var x = 1;</script>" * 1000 + "<p>content</p>" + "x" * MAX_HTML_FOR_CLAUDE
        result = _truncate_html(html)
        assert "var x = 1" not in result


# ---------------------------------------------------------------------------
# Extraction prompt
# ---------------------------------------------------------------------------

class TestBuildExtractionPrompt:
    def test_includes_race_name(self):
        """Prompt includes the race name."""
        prompt = _build_extraction_prompt("<html>test</html>", "Unbound 200", {})
        assert "Unbound 200" in prompt

    def test_includes_html(self):
        """Prompt includes the HTML content."""
        prompt = _build_extraction_prompt("<html><h1>Race Page</h1></html>", "Test Race", {})
        assert "Race Page" in prompt

    def test_includes_existing_data(self):
        """Prompt includes existing profile data for comparison."""
        existing = {"distance_mi": 200, "elevation_ft": 11000}
        prompt = _build_extraction_prompt("<html>test</html>", "Test Race", existing)
        assert "200" in prompt
        assert "11000" in prompt

    def test_requests_json_output(self):
        """Prompt asks for JSON output."""
        prompt = _build_extraction_prompt("<html>test</html>", "Test Race", {})
        assert "JSON" in prompt
        assert "next_edition_date" in prompt
        assert "distance_mi" in prompt


# ---------------------------------------------------------------------------
# Extract save/load
# ---------------------------------------------------------------------------

class TestExtractSaveLoad:
    def test_round_trip(self, tmp_path, monkeypatch):
        """Extract data round-trips through save/load."""
        monkeypatch.setattr("scrape_utils.SCRAPE_EXTRACTS_DIR", tmp_path)
        data = {"date_2026": "2026-06-06", "distance_mi": 200}
        save_extract("unbound-200", data)
        loaded = load_extract("unbound-200")
        assert loaded == data

    def test_load_missing_returns_none(self, tmp_path, monkeypatch):
        """Loading non-existent extract returns None."""
        monkeypatch.setattr("scrape_utils.SCRAPE_EXTRACTS_DIR", tmp_path)
        assert load_extract("nonexistent-race") is None

    def test_creates_directory(self, tmp_path, monkeypatch):
        """save_extract creates directory if missing."""
        extract_dir = tmp_path / "deep" / "extracts"
        monkeypatch.setattr("scrape_utils.SCRAPE_EXTRACTS_DIR", extract_dir)
        save_extract("test", {"x": 1})
        assert extract_dir.exists()


# ---------------------------------------------------------------------------
# Date staleness follows today's date
# ---------------------------------------------------------------------------

from datetime import date as _date

from scrape_utils import edition_date, extract_date, is_stale_date


class TestEditionDate:
    def test_profile_format(self):
        assert edition_date("2027: March 7") == (2027, 3, 7)

    def test_iso(self):
        assert edition_date("2026-06-06") == (2026, 6, 6)

    def test_range_uses_first_day(self):
        assert edition_date("2026: June 26-27 (Saturday)") == (2026, 6, 26)

    def test_no_year(self):
        assert edition_date("Last Sunday in May") == (None, 5, None)

    def test_year_after_the_date(self):
        assert edition_date("November 21, 2026") == (2026, 11, 21)

    def test_empty(self):
        assert edition_date(None) == (None, None, None)


class TestIsStaleDate:
    TODAY = _date(2026, 11, 22)

    def test_past_edition_this_year_is_stale(self):
        assert is_stale_date("2026: June 21", self.TODAY)

    def test_upcoming_edition_this_year_is_fresh(self):
        assert not is_stale_date("2026: December 6", self.TODAY)

    def test_today_is_fresh(self):
        assert not is_stale_date("2026: November 22", self.TODAY)

    def test_next_year_is_fresh(self):
        assert not is_stale_date("2027: March 7", self.TODAY)

    def test_earlier_year_is_stale(self):
        assert is_stale_date("2025: July 10", self.TODAY)

    def test_no_year_is_stale(self):
        assert is_stale_date("TBD", self.TODAY)
        assert is_stale_date("", self.TODAY)

    def test_year_without_month_waits_for_year_end(self):
        assert not is_stale_date("2026: date to be announced", self.TODAY)
        assert is_stale_date("2026: date to be announced", _date(2027, 1, 1))

    def test_month_without_day_is_stale_after_the_month(self):
        assert not is_stale_date("2026: November", self.TODAY)
        assert is_stale_date("2026: October", self.TODAY)


class TestExtractDate:
    def test_prefers_next_edition_date(self):
        assert extract_date({"next_edition_date": "2027-06-27", "date_2026": "2026-06-27"}) == "2027-06-27"

    def test_reads_older_extracts(self):
        assert extract_date({"date_2026": "2026-06-27"}) == "2026-06-27"

    def test_empty(self):
        assert extract_date(None) is None and extract_date({}) is None


class TestPromptDates:
    def test_prompt_states_today_and_has_no_fixed_year_field(self):
        prompt = _build_extraction_prompt("<html>test</html>", "Test Race", {}, today=_date(2027, 2, 1))
        assert "Today is 2027-02-01." in prompt
        assert "date_2026" not in prompt
        assert "event_status" in prompt


from scrape_utils import date_is_on_page, extract_race_facts_via_claude


class TestDateIsOnPage:
    def test_numeric_day_first(self):
        assert date_is_on_page("<span>27/06/2027</span>", "2027-06-27")

    def test_numeric_month_first(self):
        assert date_is_on_page("SATURDAY 05/16/2026", "2026-05-16")

    def test_iso(self):
        assert date_is_on_page("starts 2027-03-07", "2027-03-07")

    def test_month_name_then_day(self):
        assert date_is_on_page("Dartmoor Classic on June 20, 2027. Choose", "2027-06-20")

    def test_first_day_of_a_range(self):
        assert date_is_on_page("<h2>Departure on June 5 and 6, 2027</h2>", "2027-06-05")

    def test_second_day_of_a_range(self):
        assert date_is_on_page("<h2>Departure on June 5 and 6, 2027</h2>", "2027-06-06")

    def test_day_then_month_other_language(self):
        assert date_is_on_page("Domenica 16 maggio 2027", "2027-05-16")
        assert date_is_on_page("le 27 juin 2027", "2027-06-27")

    def test_projected_date_is_rejected(self):
        """The page shows 2026's date and mentions 2027 elsewhere; 2027-05-15 is invented."""
        page = 'SATURDAY 05/16/2026 <a href="/percorsi2027.aspx">Routes 2027</a>'
        assert not date_is_on_page(page, "2027-05-15")
        assert date_is_on_page(page, "2026-05-16")

    def test_right_day_wrong_year_is_rejected(self):
        assert not date_is_on_page("June 20, 2026", "2027-06-20")

    def test_day_must_be_whole_number(self):
        assert not date_is_on_page("June 20, 2027", "2027-06-02")

    def test_year_must_belong_to_the_date(self):
        page = "Race day was 7 March 2026. See you in 2027!"
        assert not date_is_on_page(page, "2027-03-07")
        assert date_is_on_page(page, "2026-03-07")

    def test_impossible_date_is_rejected_not_raised(self):
        assert not date_is_on_page("13/13/2027", "2027-13-01")
        assert not date_is_on_page("31 February 2027", "2027-02-31")

    def test_bad_input(self):
        assert not date_is_on_page("June 20, 2027", "June 20")
        assert not date_is_on_page("", "2027-06-20")
        assert not date_is_on_page("June 20, 2027", None)


class TestUnverifiedDateIsParked:
    def test_invented_date_is_removed_from_the_extract(self):
        from unittest.mock import patch
        with patch("youtube_enrich.call_api", return_value='{"next_edition_date": "2027-05-15"}'):
            facts = extract_race_facts_via_claude("SATURDAY 05/16/2026", "Bra Bra")
        assert facts["next_edition_date"] is None
        assert facts["unverified_date"] == "2027-05-15"

    def test_date_on_page_is_kept(self):
        from unittest.mock import patch
        with patch("youtube_enrich.call_api", return_value='{"next_edition_date": "2027-06-20"}'):
            facts = extract_race_facts_via_claude("Classic on June 20, 2027", "Dartmoor")
        assert facts["next_edition_date"] == "2027-06-20"
        assert "unverified_date" not in facts


from scrape_utils import weekly_batch


class TestWeeklyBatch:
    ITEMS = [f"race-{i}" for i in range(10)]

    def test_every_item_is_reached_within_a_cycle(self):
        from datetime import timedelta
        seen = set()
        for week in range(4):
            batch = weekly_batch(self.ITEMS, 3, _date(2026, 11, 22) + timedelta(weeks=week))
            assert len(batch) == 3
            seen.update(batch)
        assert seen == set(self.ITEMS)

    def test_limit_covering_everything(self):
        assert weekly_batch(self.ITEMS, 60) == self.ITEMS
        assert weekly_batch(self.ITEMS, 0) == []
        assert weekly_batch([], 5) == []


DATE_ON_PAGE_CASES = [
    ("<span>27/06/2027</span>", "2027-06-27", True),
    ("SATURDAY 05/16/2026", "2026-05-16", True),
    ("starts 2027-03-07", "2027-03-07", True),
    ("Dartmoor Classic on June 20, 2027. Choose", "2027-06-20", True),
    ("<h2>Departure on June 5 and 6, 2027</h2>", "2027-06-05", True),
    ("<h2>Departure on June 5 and 6, 2027</h2>", "2027-06-06", True),
    ("Domenica 16 maggio 2027", "2027-05-16", True),
    ("le 27 juin 2027", "2027-06-27", True),
    ("den 7. März 2027", "2027-03-07", True),
    ("2027: March 7", "2027-03-07", True),
    ("5–6 June 2027", "2027-06-05", True),
    ("5–6 June 2027", "2027-06-06", True),
    ("July 30 - August 1, 2027", "2027-07-30", True),
    ("July 30 - August 1, 2027", "2027-08-01", True),
    ("30 July - 1 August 2027", "2027-07-30", True),
    ("30 July - 1 August 2027", "2027-08-01", True),
    ("<h2>June&nbsp;20, 2027</h2>", "2027-06-20", True),
    ("June&#160;20, 2027", "2027-06-20", True),
    ("Sunday, March 7, 2027", "2027-03-07", True),
    ("June 20th, 2027", "2027-06-20", True),
    ("Sept. 19, 2027", "2027-09-19", True),
    ("06/06/2027", "2027-06-06", True),
    ("<b>07.03.2027</b>", "2027-03-07", True),
    ("07.03.2027", "2027-07-03", False),
    ("05/06/2027 Saturday 5 June 2027", "2027-06-05", True),
    ("Race day was 7 March 2026. See you in 2027!", "2026-03-07", True),
    # A projected date: the page shows last year's date and mentions next year elsewhere.
    ('SATURDAY 05/16/2026 <a href="/percorsi2027.aspx">Routes 2027</a>', "2027-05-15", False),
    ("June 20, 2026", "2027-06-20", False),
    ("June 20, 2027", "2027-06-02", False),
    ("Race day was 7 March 2026. See you in 2027!", "2027-03-07", False),
    # A full stop ends the date; the year belongs to the next sentence.
    ("Race day: June 20. 2027 registration opens soon.", "2027-06-20", False),
    # Day and month could be swapped, so the number proves neither reading.
    ("05/06/2027", "2027-05-06", False),
    ("05/06/2027", "2027-06-05", False),
    ("13/13/2027", "2027-13-01", False),
    ("31 February 2027", "2027-02-31", False),
    ("June 20, 2027", "June 20", False),
    ("", "2027-06-20", False),
    ("May 2027 edition: 16 riders", "2027-05-16", False),
]


@pytest.mark.parametrize("page, claimed, expected", DATE_ON_PAGE_CASES)
def test_date_is_on_page_cases(page, claimed, expected):
    assert date_is_on_page(page, claimed) is expected
