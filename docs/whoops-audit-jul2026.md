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
3. **No automated link-checker** — tonight's dead links sat there since
   April. Cheap fix: a weekly GitHub Action that crawls the live homepage +
   3 sample pages, extracts internal hrefs, fails on non-200s.
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
