# Roadie Labs — LLM Handoff (as of 2026-07-01)

You are picking up work on **Roadie Labs** (roadielabs.com), the road-cycling
sibling of Gravel God Cycling. This doc is everything you need to continue. Read
it fully before touching anything. Also read `CLAUDE.md` (repo rules) and, in the
user's auto-memory, `roadie-labs-duplication.md` (running log) and
`cross-brand-lessons.md` (infra pitfalls that apply here).

---

## 1. Mission & ecosystem

Rated race databases (gravel/road/ski) earn trust as honest race critics →
convert to a plan/course/coaching ladder → ultimately delivered on Endure Labs
(replacing TrainingPeaks). Roadie Labs is the **second vertical**, duplicating
Gravel God's tracking/business/pipeline and adapting content to road cycling.
Canonical plan: `gravel-god-cycling/NORTHSTAR.md`.

**Repos (all under `/Users/mattirowe/Documents/GravelGod/`):**
- `road-race-automation/` — THIS repo. 427 road race profiles, generators, static site. GitHub `wattgod/road-race-automation`.
- `gravel-race-automation/` — Gravel God (WordPress). Source of most patterns; the shared Cloudflare workers live here.
- `athlete-custom-training-plan-pipeline/` — shared Flask webhook (Railway) + Stripe + the plan-generation pipeline. Serves BOTH brands.
- `road-labs-brand/` — road design tokens (`tokens.css`, `--rl-*`).

**Brand facts:** GA4 = `G-WQ7W8XN11N` (property `540984732`). CSS prefix `--rl-`.
Monochrome palette (newsprint/charcoal; `#1a1a1a`, `#f5f5f0`, error `#8b1a1a`).
Rating key is `race.fondo_rating` (NOT `gravel_god_rating`). 14 scored dimensions
+ `cultural_impact` bonus = "15 criteria". Tiers T1≥80/T2≥60/T3≥45/T4<45, labels
**Elite / Contender / Rising / Local** (canonical, in `brand_tokens.TIER_NAMES`).

---

## 2. ⚠️ DEPLOY REALITY (read this or you WILL break things)

**roadielabs.com is a STATIC HTML site on SiteGround. It is NOT WordPress.**
There is no `wp-content/`. `scripts/push_wordpress.py` is WordPress-oriented and
several of its functions target dead paths — trust it only where verified below.

- **SSH/SCP:** host `giow1060.siteground.us`, user `u3586-cbpfw5houmt3`, port
  `18765`, key `~/.ssh/roadlabs_key`. Doc root
  `/home/customer/www/roadielabs.com/public_html/`.
- **Deploy = direct SCP** to the matching dir. Examples that WORK:
  - Race pages (bulk): `python3 scripts/push_wordpress.py --sync-pages --pages-dir <dir-of-{slug}.html>` → tar+ssh to `/race/<slug>/index.html`. **Generate race pages to a DEDICATED dir** (`generate_neo_brutalist.py --all --output-dir /tmp/x`), because `--sync-pages` globs `*.html` and would otherwise sweep up homepage.html etc.
  - Single pages: `scp -i ~/.ssh/roadlabs_key -P 18765 <file> u3586-...@giow1060.siteground.us:<docroot>/<path>/index.html`
- **URL → server path map** (verified):
  - `/` → `public_html/index.html` (**stale-prone**: the homepage pipeline writes `/homepage/`, but `/` serves root `index.html`. Deploy homepage to BOTH.)
  - `/road-races/` → `public_html/road-races/index.html` — the canonical race browser (the site links here everywhere). Content = `web/road-labs-search.html`.
  - `/search/` → `public_html/search/index.html` — a SECOND copy of the search page + where its **assets** live (`/search/race-index.json`, `/search/road-labs-search.js`, `/search/rl-search.css`). Both `/road-races/` and `/search/` currently serve the search page (minor duplicate-content; dedup is an open item).
  - `/race/<slug>/` → race pages. `/race/methodology/` → methodology page.
  - `/assets/rl-styles.<hash>.css` + `/assets/rl-scripts.<hash>.js` → shared page CSS/JS (content-hashed). `/ab/experiments.json` + `/ab/rl-ab-tests.<hash>.js` → A/B engine.
  - `/questionnaire/` → training-plan questionnaire (`index.html` + `training-plans-form.js`).
- **`/assets/` gotcha:** it was MISSING entirely until this session (every page's 89KB external stylesheet 404'd site-wide; pages ran on ~5.7KB inline critical CSS). When you regenerate pages, the asset hash may change — if so, SCP the new `wordpress/output/assets/rl-*.{css,js}` to `/assets/` or pages break. Current hashes: CSS `5f337585`, JS `7354be26`.
- **CACHE:** SiteGround dynamic cache serves stale pages. `wp sg purge` does NOT
  work (no WordPress) — `purge_cache()` now detects this and prints the manual
  step. **After any deploy, the USER must flush via Site Tools → Speed → Caching
  → Dynamic Cache → Flush.** You cannot flush from CLI. Verify new content with a
  `?cb=<random>` query param (bypasses the cache).
- **HTTP from an agent sandbox may be blocked:** after many curls the SiteGround
  WAF rate-limited the agent IP (all `https://roadielabs.com/*` returned `000`).
  This is NOT a site outage. **Verify deploys SERVER-SIDE over SSH** (grep the
  deployed file) — that's definitive. `?cb=` HTTP checks are a bonus when reachable.

---

## 3. Backend / charging pipeline (shared, both brands)

- **Webhook:** `athlete-custom-training-plan-pipeline-production.up.railway.app`
  (Railway, auto-deploys on push to `main` of the pipeline repo).
- **Flow:** race page CTA "BUILD MY PLAN — $15/WK" → `/questionnaire/?race=<slug>`
  → form POSTs to `/api/create-checkout` → returns a Stripe `checkout_url` →
  redirect → payment → Stripe webhook → `run_pipeline()` builds the plan.
- **Brand routing:** the webhook derives brand from the `Origin` header
  (`roadielabs.com` → `roadielabs`). No brand field needed in the payload. The
  `brand→discipline` fix (pipeline commit `20fc0ab`, LIVE on Railway) makes road
  orders build ROAD plans (previously an unknown race name → gravel plan).
- **Verified working** this session via `scripts/checkout_monitor.py --brand road`
  (mints a real, never-charged Stripe session). Health monitor runs daily via
  `.github/workflows/checkout-monitor.yml`.
- **Lead capture:** race/prep-kit/quiz email forms POST to the shared Cloudflare
  worker `fueling-lead-intake.gravelgodcoaching.workers.dev` (in the GRAVEL repo,
  now brand-aware — road payloads send `brand:'roadielabs'`). Activates on the
  next road page regen+deploy.

---

## 4. What shipped this session (all committed; road `main` @ `c57731a`)

Ordered roughly by impact. Every commit staged ONLY explicitly-listed files.

**Data-integrity / money (P0):**
- GA4 split-brain: `rl-ga4.php` was sending road traffic to the GRAVEL GA4 property → fixed to `G-WQ7W8XN11N`.
- `brand→discipline`: road orders were building gravel plans → fixed (pipeline `20fc0ab`, live on Railway).
- Demand analyzer read dead gravel keys → all road races collapsed toward one TP SKU. Fixed to `fondo_rating` keys; regenerated 427 race-packs + SKU map (alpine-fondo 67→176).

**Race pages (the big one):** `generate_neo_brutalist.py` keyed its whole rating
pipeline (radar chart, accordion, score sums, difficulty gauge, FAQ) off GRAVEL
dimension keys → **8 of 14 rating dimensions rendered score 0 on every one of the
427 race pages** (the core rating viz was mostly zeros site-wide). Remapped
`COURSE_DIMS/OPINION_DIMS/DIM_LABELS/RADAR_LABELS/hard_dims/FAQ_*` to road
`fondo_rating` keys. **Full 427-page regen + deploy done** — pages now have real
radar scores, 6-item nav, working JS.

**Search page:** was fully broken since April (WordPress asset paths 404'd on the
static site; brand CSS never ported). Ported `web/rl-search.css` (monochrome),
fixed paths to `/search/`, deployed. Then made `/road-races/` the canonical URL
resolve.

**Site-wide CSS:** `/assets/` was never deployed → 89KB stylesheet 404'd
everywhere. Deployed it.

**Copy / brand hygiene:** removed "No sponsors/affiliates/pay-to-play" defensive
hero copy (homepage + methodology + A/B control); TIER_NAMES gravel leftovers
("The Icons/Grassroots") → Elite/Contender/Rising/Local; methodology page cited
FOUR 404 gravel races as tier examples → real road races; methodology dimensions
table now data-driven from `config/dimensions.json`; anti-slop
(world-class/iconic/bucket-list) removed; llms.txt fixed (removed dead
`/race-index.json` + nonexistent `/api/v1/docs`, 14→15 criteria); removed broken
"Featured in" logos from homepage.

**Infra / tracking parity ported to road:** A/B engine (`rl-ab-tests.js`,
`ab_experiments.py`, `experiments.json`, brand_tokens bootstrap; deployed to
`/ab/`), `funnel_report.py`, `indexing_audit.py`, `checkout_monitor.py` +
workflow, blog generators GA4, Courses nav item (+ `/courses/` landing page
deployed).

**CI:** Regression Tests had been red on every push (pre-existing) — fixed two
"passes-local/fails-CI" bugs: a test read an uncommitted generated file (now
reads generator source); `node -e` blew ARG_MAX in CI (now runs from a temp
file). **CI is green.**

---

## 5. Open items (prioritized)

**P1**
1. **Cache flush pending** — several deploys (homepage no-sponsors, methodology,
   `/road-races/`, questionnaire JS, `/ab/`, all 427 race pages) went out; the
   user must flush SiteGround dynamic cache for default visitors to see them.
2. **Full site-wide nav propagation:** the 6-item "Courses" nav is live on
   homepage, methodology, courses, and the freshly-regenerated race pages, but
   OTHER page types (about, coaching, calendar, tier hubs, vs pages, state hubs,
   prep kits, quiz) still show the OLD 5-item nav until regenerated + redeployed.
   Not broken (the `/courses/` + `/road-races/` targets exist), just inconsistent.
3. **Activate lead-capture brand tags + A/B on non-homepage pages:** these
   activate as each page type is regenerated with the current generators.

**P2**
4. **`/search/` vs `/road-races/` duplicate content** — both serve the search
   page. Pick one canonical; add a redirect or `<link rel=canonical>` for the
   other. Sitemap + nav use `/road-races/`, so make that canonical.
5. **`/` vs `/homepage/` path disconnect** — `/` serves root `index.html` but the
   pipeline writes `/homepage/`. Currently deploying to both. Decide one.
6. **JSON-LD logo + `web/feed/races.xml`** point at `/wp-content/` paths that
   don't exist (no logo asset hosted). Needs a real logo file at e.g. `/assets/`.
7. **Blog** not live (no content); blog generators fixed preventively.
8. **`web/race-index.json`** has an uncommitted 1-line data edit (a race's
   `cultural_impact` 3→2) sitting in the working tree — unrelated to the above;
   leave it or confirm with the user before committing.

---

## 6. Pitfalls / lessons (don't relearn these the hard way)

- **Generator uses gravel keys, data uses road keys.** The recurring root cause.
  When something renders blank/0/wrong on road, check whether the generator
  hardcodes gravel dimension names (`length/technicality/elevation/climate/
  adventure/race_quality/experience/community`) vs road `fondo_rating`
  (`distance/climbing/descent_technicality/climate_risk/road_surface/organization/
  scenic_experience/community_culture`). `config/dimensions.json` is the source of
  truth — prefer data-driven over hardcoded.
- **No auto-fire GA events** (cross-brand lesson #12). A coaching carousel fired
  GA on a 6s timer → 17,873 junk events on gravel; the road copy had the same bug
  (fixed). Grep new generators for `setInterval`/`setTimeout` near `gtag`.
- **Test the FULL flow, not the API** (lesson #10). Checkout can look "Online"
  while Stripe rejects every session. `checkout_monitor.py` does a real synthetic
  purchase.
- **Never guess CSS token names / hex** — read `road-labs-brand/tokens/tokens.css`
  or `wordpress/brand_tokens.py`. Static pages resolve tokens to hex at gen time;
  a runtime `var(--rl-*)` only works if a `:root` block is on the page (that's why
  `rl-search.css` carries its own inlined tokens).
- **Stage only your files.** Multiple things sit uncommitted in the working tree
  across sessions; `git add -A` would sweep up unrelated/incomplete work.
- **Owner rules:** NO "no sponsors/affiliates" defensive copy; NO fabricated
  claims/testimonials; do it right the first time (self-critique before "done").

---

## 7. First things to do when you pick up

1. `cd road-race-automation && git pull && python3 -m pytest tests/ -q` (expect
   ~1414 passed, ~86 skipped). Confirm CI green on `main`.
2. Ask the user to flush the SiteGround cache, then eyeball live: `/` (no
   featured-in, no "no sponsors"), `/road-races/` (200, styled), a race page
   `/race/letape-du-tour/` (radar fully populated, Courses nav), `/questionnaire/`.
3. If continuing the nav rollout: regenerate each remaining page type and deploy
   (watch the `/assets/` hash — redeploy assets if it changed).
4. Keep `roadie-labs-duplication.md` (user memory) updated as you go.

---

## 8. Key commands

```bash
# tests
python3 -m pytest tests/ -q

# regenerate
python3 wordpress/generate_neo_brutalist.py --all --output-dir /tmp/race_full   # 427 race pages
python3 wordpress/generate_homepage.py            # → wordpress/output/homepage.html
python3 wordpress/generate_methodology.py         # → wordpress/output/methodology.html
python3 wordpress/ab_experiments.py               # → web/ab/experiments.json
python3 scripts/generate_race_directory.py        # rebuild search-page directory from race-index.json

# deploy (static; SCP or the verified --sync-pages path)
python3 scripts/push_wordpress.py --sync-pages --pages-dir /tmp/race_full
scp -i ~/.ssh/roadlabs_key -P 18765 <file> u3586-cbpfw5houmt3@giow1060.siteground.us:/home/customer/www/roadielabs.com/public_html/<path>

# verify (server-side is definitive; HTTP may be WAF-blocked from a sandbox)
ssh -i ~/.ssh/roadlabs_key -p 18765 u3586-cbpfw5houmt3@giow1060.siteground.us "grep -c '<thing>' <docroot>/<path>"
curl -s -L "https://roadielabs.com/<path>/?cb=$RANDOM"   # ?cb= bypasses cache

# pipeline health
python3 scripts/checkout_monitor.py --brand road         # mints a real never-charged Stripe session
```
