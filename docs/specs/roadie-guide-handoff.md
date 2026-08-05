# Handoff — Build the Roadie Labs Training Guide

**Status:** not started. Content skeleton exists, generator does not.
**Owner:** Fable session (this is a multi-hour build, not a config change).
**Written:** 2026-08-05, from the funnel audit that followed the "no guide
attached?" lead reply.

---

## 1. Why this is the highest-leverage item on Roadie Labs

Roadie Labs has **six lifetime email leads. Zero opens. Zero clicks. Zero
sales.** Measured from production via `railway run --service athlete-profiles
python3 scripts/sequence_report.py` in the gravel repo:

| Brand | Enrollments | Sends | Opens | Clicks | Buys |
|---|---|---|---|---|---|
| Gravel God | ~240 | 836 | 197 (22–27%) | 19 | 1 |
| **Roadie Labs** | **6** | 8 | **0** | **0** | **0** |
| XC Ski Labs | 2 | 4 | 0 | 0 | 0 |

This is not a conversion problem. Roadie copied the *back half* of the gravel
strategy — 6 of 7 sequence triggers, 12 live emails — and only **half the
capture layer**: 6 of 12 sources. The two highest-volume gravel surfaces are
missing entirely:

- **`roadielabs.com/guide/` → 404.** Content written, never built. This is the
  single biggest gap and is what this handoff covers.
- **exit-intent capture: 9 files in gravel, 0 in road.**

On the gravel side the guide is a real funnel: the end-of-chapter gate posts
`source: training_guide` with `guide_chapter`, which enrolls into `welcome_v1`
and renders a chapter-specific opener. That path currently produces nothing for
road because there is no guide.

---

## 2. What already exists

### Content: `road-race-automation/guide/road-guide-content.json`

Eight chapters, correct schema, free/gated split already marked:

| # | id | title | gated |
|---|---|---|---|
| 1 | `what-is-road-racing` | What Is Road Racing? | no |
| 2 | `choosing-your-race` | Choosing Your Race | no |
| 3 | `building-the-engine` | Building the Engine | no |
| 4 | `workout-execution` | Workout Execution | **yes** |
| 5 | `fueling-for-the-distance` | Fueling for the Distance | **yes** |
| 6 | `pack-skills-and-tactics` | Pack Skills & Race Tactics | **yes** |
| 7 | `race-week` | Race Week | **yes** |
| 8 | `after-the-finish` | After the Finish | **yes** |

**The writing is good and genuinely road-specific** — not recycled gravel:

> "A flat 100-mile fondo rewards sustained tempo and pack craft; a mountainous
> sportive with 10,000 ft of climbing rewards a high power-to-weight and the
> discipline to ride your own pace up the cols. Pick the demands first, then
> build toward them."

**But it is a skeleton.** Three `prose` blocks per chapter, one section each:

| | Gravel | Road |
|---|---|---|
| total | 144,916 chars | **9,385** |
| sections per chapter | 6–12 | **1** |
| per chapter | ~18,000 chars | **~1,200** |

Chapter schema (per chapter): `number`, `id`, `title`, `subtitle`, `gated`,
`cta_after`, `hero_image`, `sections[]`. Each section: `id`, `title`,
`blocks[]`. Each block currently `{"type": "prose", "content": "..."}`.
Gravel uses many more block types — see `BLOCK_RENDERERS` in
`gravel-race-automation/wordpress/generate_guide.py`.

### Infrastructure already in the road repo
`brand_tokens.py`, `cookie_consent.py`, `shared_header.py`, `shared_footer.py`,
`generate_neo_brutalist.py` — all present and road-branded.

### Missing from the road repo — the whole guide toolchain

| module | lines | needed for |
|---|---|---|
| `generate_guide_cluster.py` | 1,627 | pillar + chapter pages, gate, chapter nav |
| `generate_guide.py` | 3,418 | block renderers, guide CSS/JS, CTAs, rider selector |
| `guide_infographics.py` | 2,689 | infographic block types — **only if content uses them** |
| `guide_plates.py` | 160 | chapter hero plates (`hero_image` is already set) |
| `guide_configs.py` | 204 | `GuideConfig` / `GateFormConfig` / `CtaSetConfig` |

**~7,900 lines.** This is why it is a Fable job and not a config line.

---

## 3. Decisions already made by Matti (2026-08-05)

1. **Port into the road repo.** Not a `ROAD_GUIDE` config in the gravel repo.
   Road owns its own generators — that is how every other road generator works
   (`generate_quiz.py`, `generate_prep_kit.py`, `generate_neo_brutalist.py`).
2. **Content depth is the open question this handoff exists to resolve** — see
   §4. Do not gate three paragraphs behind an email wall.

---

## 4. The content decision — read this before writing code

Shipping the guide as-is means **five chapters of three paragraphs each behind
an email gate**. That is precisely the broken-promise pattern that started this
whole audit: a lead gives an address expecting substance and gets a stub. Do
not do that.

Two viable shapes. **Recommendation: A**, then B as a follow-up.

**A. Ship free and ungated now, deepen later.**
Build all 8 chapters as free, indexable pages with a soft end-of-chapter email
capture (no wall). Roadie gets a real top-of-funnel SEO/AEO asset immediately
and promises nothing it cannot deliver. Flip 4–8 to gated once they have
gravel-comparable substance. Requires setting `gated: false` across the
content and configuring the gate as a capture rather than a wall.

**B. Expand the content first, then ship with the gate.**
Draft chapters 1–8 to roughly gravel depth (~18k chars, 6–12 sections each) in
the Roadie voice. That is the bulk of the work and **Matti reads every word
before publish** — see `feedback_fork_governance` and
`feedback_droll_provocative_titles` in agent memory. Do not publish road
editorial copy without his explicit yes.

Whichever is chosen, the road guide must stay road: power-to-weight, cols,
pack craft, echelons, fondo/sportive/crit distinctions, group dynamics, and
road-specific fuelling. The gravel guide's *structure* transfers cleanly; its
*content* does not. Terrain, tire pressure and washboard have no place here.

---

## 5. Build steps

1. **Port the five modules** into `road-race-automation/wordpress/`. Rewrite
   imports to the road repo's `brand_tokens` / `shared_header` /
   `shared_footer` / `cookie_consent` / `generate_neo_brutalist`. Expect the
   brand constants (`SITE_BASE_URL`, `SUBSTACK_URL`, `COACHING_URL`,
   `TRAINING_PLANS_URL`) to differ — take them from the road versions.
2. **Trim what the content does not use.** Road content is prose-only today.
   `guide_infographics.py` (2,689 lines) is dead weight unless the expanded
   content adds infographic blocks — decide before copying it wholesale.
3. **Add a `ROAD_GUIDE` GuideConfig** in the road `guide_configs.py`:
   `content_path=guide/road-guide-content.json`, `url_base="/guide/"`,
   `local_storage_key_prefix="rl_guide"`, `guide_label="Training Guide"`.
   Point `gate_form` at the shared worker
   (`https://fueling-lead-intake.gravelgodcoaching.workers.dev`) with
   `worker_source_value="training_guide"` and **`brand: 'roadielabs'` in the
   payload** — without that the lead enrols in gravel sequences.
4. **Use the worker-first gate mode**, not the grandfathered FormSubmit path.
   `GateEndpointMode.WORKER_FIRST` already awaits the POST and reports failure
   — that behaviour was fixed in gravel PR #61 and must not be re-introduced
   in its fire-and-forget form.
5. **Deploy.** Load the repo's `deploy-and-siteground` skill first — it is
   short and it will save you an hour. The essentials:
   - **roadielabs.com is a static HTML site, not WordPress.** The deploy
     script is still called `scripts/push_wordpress.py` (inherited from the
     gravel repo) and its name lies. Any `--sync-*` flag that targets
     `wp-content/mu-plugins/` is dead weight here — that path does not exist
     on the server. Use flags whose remote target is a real static path.
   - GA4 is **baked into the HTML at generation time** (`GA_MEASUREMENT_ID`
     in `wordpress/brand_tokens.py`). If analytics look wrong, check the
     generator and the token, not a plugin sync.
   - `--purge-cache` always no-ops here ("No WordPress installation found").
     That message is expected, not a failure. The real flush is manual:
     **Site Tools → Speed → Caching → Dynamic Cache → Flush.**
   - Credentials are in the gitignored `.env`; key at `~/.ssh/roadlabs_key`,
     port 18765, `REMOTE_BASE=/home/customer/www/roadielabs.com/public_html`.
   - Confirm with a cache-buster before believing a result:
     `curl -s -o /dev/null -w "%{http_code}" "https://roadielabs.com/guide/?cb=1"`
     — 200 for the pillar and all eight chapters.
6. **Verify the lead actually lands.** Submit a real capture and confirm an
   enrollment row appears with `brand=roadielabs` and the right
   `guide_chapter`, and that `road_welcome_v1` — not `welcome_v1` — fires.

---

## 6. Landmines

- **`welcome_value.html` vs `road_welcome_value.html`.** The gravel guide
  branch email was reworded from "grabbing" to "reading" and given a chapter
  link (`wb_guide_url`). The road template says "reading" already but has **no
  `wb_guide_url`** — `GRAVEL_GUIDE_CHAPTER_SLUGS` in
  `gravel-race-automation/mission_control/routers/webhooks.py` is gravel-only
  by design. Add a road chapter map there when the road guide ships, or the
  road welcome email will ask about a chapter and link nowhere.
- **The unlock is honour-system.** `?unlocked=1` plus a one-click "I already
  subscribed" bypass. Do not treat the gate as an authorisation boundary.
- **The gravel pillar ships a stale JS bundle** without the `?unlocked=1`
  handler. Do not copy that pattern; make sure the road pillar and chapters
  both carry the current cluster JS.
- **Copy specs must not diverge from templates** —
  `.claude/skills/email-sequences/SKILL.md` ship rule. If you touch email copy,
  update `docs/specs/friend-register-copy-road.md` in the same change.
- **"as promised" is a banned phrase** in sequence copy (same SKILL.md).
- **A generator fix does not retroactively fix deployed pages.** This repo has
  been bitten hard: `generate_neo_brutalist.py` once keyed its rating pipeline
  off gravel dimension names instead of road's `fondo_rating` keys, and 8 of 14
  radar dimensions rendered zero on all 427 race pages until someone
  regenerated and redeployed. After any shared-generator change, regenerate and
  redeploy every page type it touches. See `docs/whoops-audit-jul2026.md`.
- **If roadielabs.com is unreachable, check the TLS certificate first.** It
  expired 2026-07-01 and took the site down for every HTTPS visitor; renewal is
  a manual Site Tools action with no script. Do not debug code for an outage
  that is a cert.
- **Never fire GA events on auto-advance carousels or timers.** A timer-driven
  event once produced 17,873 junk events from 9 users on the gravel site.
- **Adversarial review is mandatory** before dispatch or risky commits:
  `codex exec -m gpt-5.6-sol -s read-only -C <repo> < brief.md > review.md`.
  It caught four rounds of real defects in the gravel work this handoff came
  from, including two race-data "fixes" that were factually backwards. Verify
  its findings against live sources before acting — it overstates too.

---

## 7. Definition of done

- [ ] `roadielabs.com/guide/` returns 200; all 8 chapter URLs return 200
- [ ] Pages carry road brand tokens, GA4 snippet, consent banner, `@font-face`
- [ ] Capture posts `brand: 'roadielabs'` and enrolls in `road_welcome_v1`
- [ ] Gate awaits the POST and shows a retry on failure — never a false success
- [ ] Content decision from §4 executed; nothing thin sits behind a wall
- [ ] Matti has read any new editorial copy before publish
- [ ] Road test suite green (`python3 -m pytest tests/ -q`)
- [ ] sol review returns GO
