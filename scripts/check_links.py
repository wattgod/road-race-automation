#!/usr/bin/env python3
"""Live-site link checker — catches dead internal links before visitors do.

Born from the Jul 2026 whoops audit: five dead URLs sat in the global
nav/footer of every page for ~3 months because nothing was checking.

Crawls a small seed set of live pages, extracts same-site links + assets,
and verifies each resolves (200, or a redirect landing on 200). Exits 1
with a report if anything is dead — wired to a weekly GitHub Action.

Deliberately polite to the SiteGround WAF: capped URL count, small delay,
identifiable User-Agent, GET (some servers 405 on HEAD).

Usage:
    python3 scripts/check_links.py [--max-urls 200] [--delay 0.3]
"""

import argparse
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from html.parser import HTMLParser

SITE = "https://roadielabs.com"

# Pages whose outbound links get collected (keep small; nav+footer are on
# every page, so a few page types cover the shared chrome + section links).
SEED_PATHS = [
    "/",
    "/road-races/",
    "/race/methodology/",
    "/race/letape-du-tour/",            # race page (nav, prep strip, CTAs)
    "/race/letape-du-tour/training-plan/",
    "/race/letape-du-tour/prep-kit/",
    "/race/tier-1/",
    "/race/calendar/2026/",
    "/courses/",
    "/coaching/",
    "/about/",
    "/questionnaire/",
]

# Checked for existence but not crawled.
EXTRA_URLS = [
    f"{SITE}/sitemap.xml",
    f"{SITE}/robots.txt",
    f"{SITE}/race-dates.json",
    f"{SITE}/llms.txt",
    f"{SITE}/feed/races.xml",
    f"{SITE}/assets/road-labs-logo.png",
]

UA = "RoadieLabs-LinkCheck/1.0 (+https://roadielabs.com; weekly self-audit)"

# SiteGround's bot protection answers with HTTP 202 + an `sg-captcha` header
# instead of the page (seen 2026-07-22: 18 false "dead" findings, all 202).
# A 202 is never a real response from this static site, so exactly 202 is
# treated as a challenge (a real 404/500 stays dead even if it carries the
# header): back off, retry, and report still-challenged URLs separately
# rather than as dead links. Retries draw from a scan-wide sleep budget so a
# long WAF window can't blow the caller's timeout (immune_check allows 900s
# for the whole subprocess) — once the budget is spent, challenged URLs are
# recorded immediately without retrying.
CHALLENGE_BACKOFF = (20, 45)   # seconds to wait before each retry
CHALLENGE_RETRY_BUDGET = 180   # total seconds of backoff sleep per scan

_challenge_budget = CHALLENGE_RETRY_BUDGET


class LinkExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.urls: set[str] = set()

    def handle_starttag(self, tag, attrs):
        attr = dict(attrs)
        for key in ("href", "src"):
            val = attr.get(key)
            if not val or val.startswith(("#", "mailto:", "tel:", "data:", "javascript:")):
                continue
            url = urllib.parse.urljoin(SITE + "/", val)
            parsed = urllib.parse.urlparse(url)
            if parsed.netloc == urllib.parse.urlparse(SITE).netloc:
                # normalize: strip fragment + query
                self.urls.add(f"{parsed.scheme}://{parsed.netloc}{parsed.path}")


def fetch_once(url: str, timeout: int = 15) -> tuple[int, str, bool]:
    """GET a URL following redirects; return (final_status, body, challenged)."""
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = resp.read(400_000).decode("utf-8", "replace") \
                if "text/html" in resp.headers.get("Content-Type", "") else ""
            return resp.status, body, resp.status == 202
    except urllib.error.HTTPError as e:
        return e.code, "", e.code == 202
    except Exception:
        return 0, "", False


def fetch(url: str, timeout: int = 15) -> tuple[int, str, bool]:
    """fetch_once, retrying with backoff (budget-capped) while the WAF challenges us."""
    global _challenge_budget
    status, body, challenged = fetch_once(url, timeout)
    for pause in CHALLENGE_BACKOFF:
        if not challenged:
            break
        if _challenge_budget < pause:
            print(f"  WAF challenge on {url} — retry budget spent, recording as challenged")
            break
        _challenge_budget -= pause
        print(f"  WAF challenge on {url} — retrying in {pause}s")
        time.sleep(pause)
        status, body, challenged = fetch_once(url, timeout)
    return status, body, challenged


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--max-urls", type=int, default=200)
    parser.add_argument("--delay", type=float, default=0.3)
    args = parser.parse_args()

    to_check: set[str] = set(EXTRA_URLS)
    seed_failures = []
    challenged_urls = []

    for path in SEED_PATHS:
        url = SITE + path
        status, body, challenged = fetch(url)
        if challenged:
            challenged_urls.append((status, url))
            continue
        if status != 200:
            seed_failures.append((status, url))
            continue
        ex = LinkExtractor()
        ex.feed(body)
        to_check |= ex.urls
        time.sleep(args.delay)

    checked = dict.fromkeys(SEED_PATHS)  # seeds already verified
    urls = sorted(u for u in to_check
                  if urllib.parse.urlparse(u).path not in checked)
    if len(urls) > args.max_urls:
        print(f"NOTE: capping at {args.max_urls} of {len(urls)} discovered URLs "
              f"(raise --max-urls to cover all)")
        urls = urls[:args.max_urls]

    dead = list(seed_failures)
    for url in urls:
        status, _, challenged = fetch(url)
        if challenged:
            challenged_urls.append((status, url))
        elif status != 200:
            dead.append((status, url))
        time.sleep(args.delay)

    n_challenged_seeds = sum(1 for _, u in challenged_urls
                             if urllib.parse.urlparse(u).path in checked)
    print(f"Checked {len(SEED_PATHS) - n_challenged_seeds} of {len(SEED_PATHS)} seed pages "
          f"+ {len(urls)} discovered URLs"
          + (f" ({n_challenged_seeds} seed pages challenged — their outbound links "
             f"NOT crawled this run)" if n_challenged_seeds else ""))
    # Print challenged BEFORE dead: immune_check parses everything after the
    # "DEAD LINKS" header as dead links.
    if challenged_urls:
        rows = sorted(set(challenged_urls), key=lambda d: d[1])
        print(f"\nWAF-CHALLENGED ({len(rows)}): still behind SiteGround's "
              f"bot challenge after retries — scan inconclusive, NOT dead links")
        for status, url in rows:
            print(f"  {status or 'ERR':>4}  {url}")
    if dead:
        rows = sorted(set(dead), key=lambda d: d[1])
        print(f"\nDEAD LINKS ({len(rows)}):")
        for status, url in rows:
            print(f"  {status or 'ERR':>4}  {url}")
        return 1
    if challenged_urls:
        # Exit 2, not 0: an inconclusive scan must not read as a green one in
        # the weekly workflow. immune_check treats rc 2 + WAF block as YELLOW.
        print("No dead links found, but the scan is INCONCLUSIVE (WAF challenges).")
        return 2
    print("All links alive.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
