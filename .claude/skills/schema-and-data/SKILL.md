---
name: schema-and-data
description: Load when adding/editing race profiles, scraping, or regenerating pages in road-race-automation (Roadie Labs).
---

# Schema and Data — Roadie Labs (road-race-automation)

For the `fondo_rating` vs `gravel_god_rating` key rule and the "Key Differences
from Gravel God" list, read `CLAUDE.md` in this repo first — not repeated here.

## 1. Data flow

`race-data/*.json` (427 profiles, source of truth) → `scripts/generate_index.py`
builds `web/race-index.json` (427 entries, flat list) → `wordpress/generate_neo_brutalist.py`
renders per-race HTML → deployed by direct SCP. **This is a static HTML site on
SiteGround, not WordPress** — `push_wordpress.py`'s WP-specific sync paths are
wrong for road; see `docs/whoops-audit-jul2026.md` for deploy gotchas.

Verified counts (recounted from `race-data/`, Jul 2026): 427 profiles,
discipline split `gran_fondo` 395, `sportive` 17, `hillclimb` 11, `multi_stage` 3,
`century` 1 — older counts in memory files are stale, recount if it matters.

```bash
python3 scripts/recalculate_tiers.py --dry-run   # then without --dry-run
python3 scripts/generate_index.py                # rebuilds web/race-index.json
python3 scripts/validate_profile.py --all         # schema check, see §4
python3 wordpress/generate_neo_brutalist.py       # race page HTML
```
Editing a `generate_*.py` file does not update output — rerun it (CLAUDE.md
rule #5). Same for `generate_index.py`: race-data edits are invisible to the
site until both the index and the page generator rerun.

## 2. The duplication war story

Roadie Labs was forked from Gravel God in "Sprint 41" (`scripts/migrate_from_gravel.py`
did the `gravel_god_rating` → `fondo_rating` key rename). The fork carried over
more than the schema: GA4 tracking sent to the gravel property, hardcoded gravel
race links in the search page, gravel dimension keys baked into the page generator
(8 of 14 radar dimensions rendered zero on every live race page until caught), and
gravel prose fragments left in race copy. A multi-week P0/P1/P2 remediation, not
a one-off bug.

**Standing rule**: never copy Gravel God copy, structure, or business config
verbatim into a road surface. Road has its own vocabulary — fondos, grand fondos,
sportives, hillclimbs, multi-stage — and its own dimension names (`distance`/
`climbing`/`road_surface`, not `length`/`elevation`/`adventure`). Porting a
generator from the gravel repo means re-deriving every gravel-specific key,
label, and example race for road, not pasting it in.

## 3. Scrapling stack

The Scrapling stack lives **in this repo**, not gravel-race-automation:
- `scripts/scrape_utils.py` — tiered fetcher (`Fetcher` fast HTTP → `StealthyFetcher`
  Cloudflare-bypass browser), 7-day HTML cache, Cloudflare-challenge detection
- `scripts/scrape_official_sites.py` — CLI, requires `scrapling[fetchers]` and
  `ANTHROPIC_API_KEY` (unless `--no-claude`)
- `scripts/fact_check_profiles.py` — compares scraped facts against profile JSON
- `scripts/batch_date_search.py --use-scraper` — checks `data/scrape-extracts/`
  cache first, falls back to direct scrape of `official_site`

Cautions: `data/scrape-cache/` is gitignored and verified empty on this
checkout — don't assume a warm cache exists (7-day TTL, SHA-256 URL keys).
`fetch_url(strategy="auto")` tries fast HTTP first and only escalates to
`StealthyFetcher` (10-60s) if blocked — don't default to `"stealth"` for a batch,
it's an order of magnitude slower. Do not run these against live official race
sites for a handover check — real third-party sites, real `ANTHROPIC_API_KEY` spend.

## 4. Profile schema traps (verified: `race-data/alpe-dhuzes.json` + full-corpus scan)

- `climb_profile._needs_enrichment: true` is the default, not the exception —
  **417 of 427 profiles** (97.7%) are placeholders: `total_climbs`/`hc_climbs`/
  `cat_1_climbs`/etc. all `null`, `key_climbs: []`. Guard for `None`, don't
  assume a migrated profile has real climb data.
- `vitals.start_format` is `null` on **417 of 427** — same story, guard it.
- `vitals.route_options` (array) exists as a key on every profile but is empty
  `[]` on 231 of 427 — don't assume a non-empty array.
- `logistics.transport` can be an empty string (live example: `alpe-dhuzes.json`)
  rather than absent — `if not val` is correct, `"transport" in race` is not
  (CLAUDE.md rule #1 on `is None` checks applies to empty strings too).
- `scripts/validate_profile.py --all` currently reports **216 pre-existing
  errors across 427 profiles** (run Jul 2026), almost all "Only 0 citations
  (minimum 3)". Known standing debt — don't treat a nonzero exit as your fault
  on an unrelated diff, but do fix any *new* error on a profile you touched.
- `climbing >= 3` requires a `climb_profile` key to exist (validator enforces
  this) — existing doesn't mean populated, see above.
- Validator-required top-level keys: `name`, `slug`, `vitals`, `fondo_rating`,
  `final_verdict`, `citations`. `history`/`biased_opinion` appear on real
  profiles but aren't schema-enforced — don't assume every profile has them.

## 5. Cross-repo trust rule: never fabricate or vertical-swap social proof

roadielabs.com shipped fabricated testimonials **twice**, same root cause both
times: reusing Gravel God athlete quotes without checking what they said.
Commit `9aa8de5` (Jun 10) found the Sprint 41 fork had swapped road race names
into real Gravel God testimonials — 3 on `/products/training-plans/` and all 50
on `/about/`, same person/quote, different race, live on a site whose pitch is
being an honest critic. Commit `47a4d0a` (Jul 2) found homepage testimonials
re-fabricated the same way and purged them again. The fix both times: restore
the real original quote with its real race labeled inline, add a provenance
line explaining these are Gravel God results on the same coaching engine, and
leave the section empty rather than fabricated until real road quotes exist.
Treat a fabricated or vertical-swapped quote as security-bug severity. Real
sourced quotes or nothing.

## When NOT to use this

- Brand tokens, CSS, or fonts (`--rl-` palette, Unbounded/Sometype Mono/Source
  Serif 4) — that's `road-labs-brand` and `wordpress/brand_tokens.py`.
- Deploy mechanics (SCP paths, cache flush, SSL) — see `docs/whoops-audit-jul2026.md`.
- Scoring dimension *definitions* or tier math — read `config/dimensions.json`
  and the Scoring System section of `CLAUDE.md` directly.
- Pure content/copywriting passes on existing, already-real prose.
