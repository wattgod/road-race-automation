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

**Testimonials — real or none, provenance-labeled if cross-vertical.** The
Sprint 41 fork swapped road race names into real Gravel God quotes, producing
53 fabricated testimonials live on roadielabs.com (fixed by restoring the
real originals with a provenance line, commit history June 2026). A second,
separate violation was caught and fixed Jul 2 2026 (`47a4d0a`, "whoops audit"):
invented athlete names and results with no real basis. Current verified state:
`wordpress/generate_about.py` (`_testimonial_data()`, reused by
`generate_coaching.py`) carries 50 real Gravel God athlete quotes labeled
"Gravel God athletes — same coach, same plan engine, different surface" —
this is the only acceptable pattern for cross-vertical social proof.
`wordpress/generate_homepage.py`'s `TESTIMONIALS` list is intentionally empty
with a comment explaining why — Roadie Labs has no road coaching results yet,
and `build_testimonials()` hides the section while empty. Do not fill it with
invented names. This is the precedent for future verticals (ski): never
name-swap testimonials.

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
`generate_neo_brutalist.py:2681`) and in the owner's canonical corner copy
(gravel race-page coaching footnote: "And no, AI isn't a person.").

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
