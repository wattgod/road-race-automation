# Whoops Audit — visitor failure modes (Jul 2026)

Systematic pass over "what can go wrong for a live visitor," both brands.
FIXED items shipped in road commit 47a4d0a (full site regen + redeploy).
Gravel was spot-checked and is largely clean (WordPress + SG defaults).

## Fixed this audit (road)

| # | Failure mode | What a visitor experienced | Fix |
|---|---|---|---|
| 1 | **SSL expiry** | Site hard-down for everyone (cert expired Jul 1) | Plain Let's Encrypt (auto-renews; wildcard can NEVER auto-renew with NS on Cloudflare — cross-brand lesson) |
| 2 | **No HTTPS enforcement** | `http://` visitors stayed on insecure http; www served duplicate site | `.htaccess` (repo: `web/htaccess-root`): single 301 to `https://roadielabs.com/...` |
| 3 | **Unbranded 404 dead-end** | SiteGround's "we searched the space" page, no nav, no recovery | Branded `web/404.html` + ErrorDocument (links: database, calendar, methodology) |
| 4 | **Dead links in global nav+footer, every page** | 5 URLs 404/403'd sitewide: `/guide/`, `/articles/`, `/consulting/`, `/insights/`, `/fueling-methodology/` | Removed from header/footer; PRODUCTS dropdown now Plans+Courses; ARTICLES → live Substack |
| 5 | **Homepage advertised nonexistent content** | "Road Racing Guide" section (8 chapter links → 404) + "Latest Takes" (10 gravel article slugs → 404) | Sections gated off (builders return "" while empty); restore when pages ship |
| 6 | **Fabricated testimonials on homepage** | Invented athlete quotes w/ names+results (same violation as gravel's purged 53) | TESTIMONIALS emptied; populate only with real permissioned quotes |
| 7 | **Newsletter links → placeholder host** | `https://TODO_ROADLABS_NEWSLETTER` in 6 generators — footer SUBSCRIBE + nav ARTICLES went nowhere | Now `gravelgodcycling.substack.com` (swap when a road Substack exists) |
| 8 | **Search page invisible/naked** (earlier tonight) | `/road-races/` had no title/meta/canonical/GA4/nav | `scripts/build_search_page.py` full-page shell |
| 9 | **Race-page ratings showed zeros** (earlier tonight) | 8/14 radar dims = 0 on all 427 pages | Gravel→road key remap in `generate_neo_brutalist.py` |

## Round 2 — found by the new link checker (fixed same night)

| # | Failure mode | Fix |
|---|---|---|
| 10 | Unbounded font preloaded + @font-face'd on every page but never deployed anywhere (removed from the brand long ago) — 404 per page-load | Removed from road `brand_tokens.py`; full regen (new CSS hash `14abcaa1`) |
| 11 | `/questionnaire/` + `/products/training-plans/` were stale pre-fix pages still carrying all 5 dead nav links + unhashed AB script | Questionnaire regenerated; `/products/training-plans/` → 301 to canonical `/training-plans/` (.htaccess) |
| 12 | `/about/matti-avatar.png` referenced but never deployed | Deployed from gravel repo assets |
| 13 | **GRAVEL: A/B engine dead** — pages reference `gg-ab-tests.e0982843.js`, server had only the older `515fb8b0` hash. Experiments silently not running | Deployed current engine + experiments.json to gravel `/ab/` |

Gravel findings still open (Monday cron will keep them loud): `/course/`
404 (courses linked but never deployed — known launch blocker), `/feed/`
403 (dir link without index), `/methodology/` 404 (wrong path linked
somewhere; gravel's lives elsewhere).

## Known-and-accepted (documented, not bugs)

- **Email capture is fire-and-forget**: forms show success without checking
  `response.ok`. Deliberate for lead capture (failures shouldn't scare the
  visitor); the worker + Mission Control logs are the failure channel.
- **Mobile nav has no hamburger**: nav wraps + centers via CSS, dropdowns
  hidden on mobile. Functional; top-level links all reachable.
- **Quiz page is chromeless**: funnel page by design (gravel same).
- **Unused CSS rules** for gated sections remain in homepage styles —
  harmless; markup is what's gated.

## Still open (ranked)

1. **SiteGround dynamic cache staleness after deploys** — cache-flush is
   manual (Site Tools) and every deploy needs one; default visitors get
   stale pages until then. *Tonight's deploys are cached-stale right now.*
   Mitigation candidates: shorter TTL, or SG API flush if a token exists.
2. **`coach@roadielabs.com` FormSubmit inbox unverified** — the race-review
   form may silently drop submissions (P2 memory item). Verify the inbox
   or repoint the form at the shared worker.
3. ~~No automated link-checker~~ **BUILT**: `scripts/check_links.py` +
   `.github/workflows/link-check.yml` in BOTH repos (Mondays 12:00 UTC,
   `workflow_dispatch` for on-demand). Red run = visitor-clickable 404.
   Note: it fetches through the SiteGround cache — after a deploy+flush
   cycle, re-run manually for a clean read.
4. **`/products/training-plans/` vs `/training-plans/`** — both exist and
   serve content; pick a canonical (nav uses `/products/...`, emails use
   `/training-plans/`). Both 200 so not visitor-facing; SEO tidiness.
5. **Gravel deep audit** — gravel got redirect/404 spot-checks only
   (clean); a full dead-link crawl like tonight's hasn't run there.

## Recurring root causes (for CLAUDE.md-level awareness)

1. **Aspirational URLs**: generators link pages that were planned but never
   built (/guide/, /articles/, /insights/). Rule: a link ships only when
   its target is deployed — the new footer/header tests enforce the known
   set (`test_no_dead_link_targets`).
2. **Gravel copy-paste debt**: every audit finds more gravel leftovers
   (dimension keys, article slugs, tier names, guide chapters). When
   something is blank/0/404 on road, check for a gravel-shaped assumption.
3. **Placeholders that escape**: `TODO_ROADLABS_NEWSLETTER` shipped to prod
   for months. Grep for `TODO_` in generator output during preflight.
