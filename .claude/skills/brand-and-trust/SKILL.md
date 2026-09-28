---
name: brand-and-trust
description: Load when touching Roadie Labs visual styling, copy, or any trust-bearing claim (scores, testimonials, "honest" framing).
---

# Brand and Trust — Roadie Labs

Ecosystem context and the anti-shill principle live in `gravel-god-cycling/NORTHSTAR.md`
(canonical) — this repo's `CLAUDE.md` has a pointer. Read that before large or
ambiguous brand/trust work. This skill covers what's specific to Roadie Labs.

## 1. Token chain — and where it breaks

Source of truth is the sibling repo `../road-labs-brand/`:
- `road-labs-brand/tokens/tokens.json` — edit here
- `road-labs-brand/tokens/tokens.css` — generated, run `python3 tokens/generate_css.py` after editing json
- Never hand-edit `tokens.css` or hardcode hex in that repo.

**This repo does not consume that chain programmatically.** `wordpress/brand_tokens.py`
defines `BRAND_DIR = .../road-labs-brand` but only uses it to locate font files
(`BRAND_FONTS_DIR`). The `:root` CSS block from `get_tokens_css()` and the
`COLORS` dict used for SVG attrs are hand-typed hex literals that happen to
currently match `tokens.json`. Edit `tokens.json` + regenerate `tokens.css`
and `brand_tokens.py` will NOT pick up the change — silent drift, no
automated guard. If you change a color, edit both and diff by hand. Same
drift-risk class as the Gravel God repo's `brand_tokens.py` copy — CLAUDE.md
rule #10 ("never hardcode hex in generators") protects *generators* from
hardcoding; it does not protect `brand_tokens.py` itself from drifting off
`road-labs-brand`.

Generators must pull colors from `brand_tokens.py` (`COLORS` dict or the CSS
custom properties, `--rl-*`) — never inline a new hex value in a generator.

## 2. Palette identity — Newsprint / Charcoal, not Gravel God desert

Roadie Labs is monochrome, not the Gravel God warm brown/tan/gold palette.
CSS prefix is `--rl-*`, never `--gg-*`. Verified current values (`tokens.css`
/ `brand_tokens.py`, matching):
- Rich black `#1a1a1a` (text, borders, primary, T1 tier)
- Charcoal `#333333` (accent/CTA — token name is `signal-red` but the actual
  color is charcoal, not red; don't trust token names over values)
- Medium gray `#555555`, muted gray `#777777` (T3 tier), light gray `#999999`
  / `#b8b8b0`
- Warm silver `#d0d0c8` (borders/dividers), newsprint `#f5f5f0` (background,
  not sterile white), white `#ffffff`
- Error/oxblood `#8b1a1a` — the only non-monochrome color in the system
- Tiers: T1 `#1a1a1a`, T2 `#4a4a4a`, T3 `#777777`, T4 `#aaaaaa`

Fonts: Source Serif 4 (editorial) + Sometype Mono (data). `road-labs-brand/CLAUDE.md`
still lists Unbounded as a display font, but this repo's `CLAUDE.md` and
`brand_tokens.py` note Unbounded was removed Jul 2026 (never deployed, every
page 404'd its preload) — don't reintroduce without updating both sides.
Neo-brutalist rules: no border-radius, no box-shadow, 2-3px solid borders
(4px double on structural breaks), hover transitions limited to
border-color/background-color/color at 300ms.

When porting a generator or component from `gravel-race-automation`, the
Gravel God `--gg-*` palette (warm brown/tan/gold) must not leak through —
swap to `--rl-*` tokens and check for hardcoded `--gg-` or gravel hex values
left over from the port.

## 3. Trust rules

**Testimonials: consented and sourced, or none.** No testimonial, athlete name,
rating, customer count or scarcity line renders unless it traces to a real
person, a source, and written approval of the exact text. Empty beats fake.

Correction of the record (2026-09-28). This skill used to say the 50 quotes
on `/about/` and the 3 on `/training-plans/` were "real Gravel God athlete
quotes" and that labelling them "Gravel God athletes — same coach, same plan
engine, different surface" was the acceptable cross-vertical pattern. That
was wrong. Gravel God's quotes were placeholder text written by Claude
sessions in February 2026, not real people. The Sprint 41 fork copied 53 of
them here (Mar 2026, `7db7daa`), and the June "integrity fix" (`9aa8de5`)
relabelled them as real originals instead of removing them. A separate set of
invented homepage quotes was emptied Jul 2 2026 (`47a4d0a`). All of it came
down 2026-09-28 (Receipts spec, phase 0 takedown), along with the unverified
"100+ athletes coached / 1,000+ plans sold" counts and the `coaching_scarcity`
A/B experiment ("Limited spots.", "20 athletes/month.", "Opens quarterly.").

Current state: no testimonials anywhere on roadielabs.com. There is no
acceptable "borrowed" pattern. Roadie does not show Gravel God quotes. When
real proof exists it follows the Receipts spec (wattgod/gravel-race-automation
`docs/specs/receipts-social-proof-2026.md`): a coach identity block, the TP
ratings line, and a link to Gravel God's /athletes/ page only for athletes
who consented to the roadie channel. `tests/test_no_unsourced_proof.py`
enforces this on rendered pages. `wordpress/generate_homepage.py`'s
`TESTIMONIALS` list stays empty (owner ruling 2026-07-18: no homepage
testimonials). The same rule holds for future verticals (ski).

**Never defensive messaging.** Matt's standing rule: phrases like "no
sponsors," "no affiliates," "no pulled punches," "no algorithms, no pay-to-play"
answer a question nobody was asking and plant doubt that wasn't there. This
repo shipped that exact mistake and reverted it (commit `c57731a`, Jul 1 2026):
the homepage/methodology hero dropped that copy for positive framing ("scored
by human editors who ride them"). Do not reintroduce defensive copy on hero
sections, CTAs, taglines, or any marketing-facing text.

**Sanctioned exception (2026-07-18).** Corner-frame coaching copy naming what
coaching isn't (AI, dashboard, spreadsheet-coach) is allowed ONLY on
`/coaching/`, never elsewhere. Precedent: the `/coaching/` hero sub-line "Not
an AI, not a dashboard, not a coach who reads you like a spreadsheet"
(`wordpress/generate_coaching.py`, `build_hero()`), owner-approved 2026-07-18
as aspirational "corner" framing (what you're getting), not a defensive
rebuttal to an objection nobody raised. Same frame already ships on race pages
("A human in your corner. Adapts week to week." —
`generate_neo_brutalist.py:2681`).

**Honest-critic scores are the product.** Roadie Labs' `fondo_rating` (14
dimensions + `cultural_impact` bonus / 70 denominator, see this repo's
`CLAUDE.md`) is the same anti-shill mechanic as Gravel God — harsh T4s on
famous races are what make the ratings credible, per
`gravel-god-cycling/NORTHSTAR.md` ("The anti-shill operating principle").
Never soften a score or inflate a tier for commercial reasons. Every claim
backing a score needs a citation — run `scripts/audit_fabricated_claims.py`
after any batch of profile edits; it flags high-confidence claims
(championship/official/state/national/world) not backed by a research dump.

## When NOT to use this

Skip this skill for pure data/schema work (race JSON fields, scoring math,
`config/dimensions.json`) that touches no rendered copy, CSS, or trust claim —
use the repo's `CLAUDE.md` scoring/critical-rules sections instead. Skip it
for infra/deploy work (SSH, SiteGround, sitemap generation) with no visual or
copy change.
