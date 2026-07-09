---
name: deploy-and-siteground
description: Load before deploying roadielabs.com or touching any SiteGround/WordPress-shaped op in this repo — the site is static HTML, not WordPress, and the deploy script's naming lies about that.
---

Read this repo's `CLAUDE.md` first (architecture, scoring, brand tokens). This
skill covers only the deploy/hosting layer, which `CLAUDE.md` doesn't detail.

## The one fact that changes everything

`roadielabs.com` is a **static HTML site** on SiteGround — no WordPress, no
`wp-content/`. The deploy script is still named `scripts/push_wordpress.py`
(reused/adapted from the gravel repo), and its own `purge_cache()` docstring
says so explicitly: `wp sg purge` fails with "No WordPress installation
found" here, and the function detects that and prints a manual-flush
instruction instead of treating it as an error.

**Trap already in the script**: several `--sync-*` flags (`--sync-consent`,
`--sync-ga4`, `--sync-header`, `--sync-noindex`, `--sync-meta-descriptions`,
`--sync-ab`'s mu-plugin leg) upload PHP from `wordpress/mu-plugins/` to
`{REMOTE_BASE}/wp-content/mu-plugins/` — a path that does not exist on the
live server. They're dead weight inherited from the WordPress flow; don't
reach for them here. GA4/consent/CTA tracking are instead baked into the
static HTML at generation time — `GA_MEASUREMENT_ID = "G-WQ7W8XN11N"` lives
in `wordpress/brand_tokens.py` and is inlined as `gtag(...)` by
`wordpress/generate_neo_brutalist.py` and friends. If analytics look broken,
check the generator/token, not a mu-plugin sync.

## Actual deploy path

1. Regenerate the affected pages (`python3 wordpress/generate_neo_brutalist.py`
   for race pages, or the matching `generate_*.py` — see `CLAUDE.md` "Common
   Commands").
2. Push with `scripts/push_wordpress.py`, using flags that hit real static
   paths:
   - `--sync-pages --pages-dir <dir>` — tar+ssh's `{slug}.html` into
     `{slug}/index.html` under `{REMOTE_BASE}/race/`, plus prebuilt
     subdirectories (vs pages, state hubs, calendar) and shared `assets/`.
     Sets `chmod 755` on `/race/` for Apache/Googlebot.
   - Single-purpose flags SCP a page's own `index.html` + assets straight
     into its `public_html/<dir>/` — e.g. `sync_questionnaire()` writes into
     `/questionnaire/` with no `wp-content` dependency at all.
   - `--purge-cache` — best-effort `wp sg purge` over SSH; on this host it
     always no-ops with the "static site" message above. That message is
     expected, not a failure.
3. Credentials live in `.env` (gitignored): `SSH_HOST`, `SSH_USER`,
   `SSH_PORT` (18765), `REMOTE_BASE` (`/home/customer/www/roadielabs.com/public_html`),
   key at `~/.ssh/roadlabs_key`. The script blocklists `[;\s|&\`$]` in
   host/user before shelling out — don't bypass that.

**Vs. gravel-race-automation**: gravel deploys to real WordPress, so its
cache purge and mu-plugin syncs actually land. This repo shares the script's
shape but only a subset of flags do anything real — check a flag's remote
target is a static path before trusting it.

## Cache staleness after every deploy

SiteGround's NGINX/dynamic cache has no CLI flush for a static site. After
any HTML-changing deploy, default visitors see the old page until the TTL
expires or someone flushes manually: **Site Tools → Speed → Caching →
Dynamic Cache → Flush**. Verify a deploy with `?cb=...` before concluding a
fix didn't work — it may just be cached.

## War story: the SSL outage

The cert expired **Jul 1 2026 18:55 UTC** and took the whole site down for
all HTTPS visitors for an extended stretch — nothing in this repo could have
prevented or fixed it. Renewal is a **manual SiteGround Site Tools action**
(Security → SSL Manager); there is no script for it. **When roadielabs.com is
unreachable, check certificate validity first** (`openssl s_client -connect
roadielabs.com:443`, or the browser padlock) before assuming a code or
deploy problem. Noted root cause: a wildcard cert with nameservers on
Cloudflare can never auto-renew, so the site moved to a plain Let's Encrypt
cert to self-renew. [UNVERIFIED — session memory, Jul 2026: whether that
root cause was independently confirmed vs. a working theory.] A cache flush
from before the outage doesn't cover deploys made after the fix — flush
again post-renewal.

## The Jul 1 "fix all" sprint and generator drift

The Jul 1 2026 night sprint (commits `ceaa974`..`8f10bb2`, on `origin/main`)
shipped sitemap cleanup, tier hubs, vs-pages, a real `/search/` page shell,
and a **1,051-page regen+redeploy** (about, coaching, legal, quiz, calendar,
state hubs, vs pages, prep-kits, training-plans) — because those pages had
drifted behind fixes already made to the shared generators. The same window's
`e4d09cc` found `generate_neo_brutalist.py` still keyed its rating pipeline
off **gravel** dimension names instead of road's `fondo_rating` keys — 8 of
14 radar dimensions rendered zero on every one of 427 race pages until fixed.

**Lesson, not just history**: a fix to shared generator logic does not
retroactively apply to already-deployed static output. After any
shared-generator change, regenerate and redeploy every page type it touches
— check `docs/whoops-audit-jul2026.md`'s "recurring root causes" (aspirational
URLs, gravel copy-paste debt, escaped placeholders) before assuming a page
is current just because its generator was fixed.

## SiteGround/WordPress traps worth carrying over

- **Speed Optimizer strips raw `<script>` tags** injected by PHP — if this
  site ever runs real WP mu-plugins, use `wp_enqueue_script()`, not
  `echo '<script>'`.
- **`wp-login.php` may be hidden** on WordPress siblings — use Site Tools'
  "Log in to Admin Panel" button instead of guessing the URL.
- **Flush all three cache layers**, not just one — NGINX Direct Delivery,
  Dynamic Cache, Memcached are separate Site Tools toggles; OPcache can also
  hold stale PHP ~60s independently.
- **Auto-advance carousels must never fire GA events** — a timer-driven
  event drowned real signal on the gravel site (17,873 junk events from 9
  users); recheck after any carousel change here.

## When NOT to use this

Skip for race-data content edits, scoring/dimension changes, or local-only
generator/test work where nothing gets pushed to roadielabs.com. Also skip
for gravel-race-automation deploys — that site is real WordPress with its
own deploy conventions.
