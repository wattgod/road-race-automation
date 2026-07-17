# Roadie Labs Race Pages — Canonical Spine v2

**Decision date:** 2026-07-17  
**Status:** Implemented and catalog-audited on `race-page-canonical-rollout`; staged, not deployed  
**Owner approval:** Matti approved the shared structure and Roadie-specific brand adaptation

This is the durable source of truth for Roadie Labs race-page structure. Roadie Labs
shares Gravel God’s approved information architecture, not its visual identity or
data vocabulary.

## Decision rationale

The Gravel God funnel evidence established the structural problem: the rating earns
attention and trust, while an offer buried near the end of a long reference page is
rarely seen. The approved cross-brand rule therefore reuses the page architecture,
while Roadie Labs keeps its own rating schema, tokens, typography, assets, copy nouns,
URLs, analytics property, and static-site deployment process.

This is intentional structural parity, not a Gravel reskin.

## Final owner-approved contract

Top-level order:

1. Hero, including the concise race verdict already carried by the hero data.
2. Interactive two-radar Ratings component.
3. Custom Plan offer.
4. Coaching footnote.
5. Full Breakdown navigation.
6. Original collapsible Deep Dive.

The top custom-plan CTA is exactly:

- `START MY CUSTOM PLAN →`
- `$15 / WEEK`

The coaching footnote is exactly:

- `Really want to see what you can do?`
- `Hire a coach. You’ll never become what you could be alone. (And no, AI isn’t a person.)`
- `GET ME IN YOUR CORNER →`

The Deep Dive retains its original accordion/mobile behavior and useful road-specific
intelligence:

- Course Overview
- Facts & History
- The Course
- From the Field
- Racer Reviews
- Training
- Train for This Race
- Race Logistics
- Tire Picks
- Latest Coverage when data permits
- Similar Races
- FAQ
- Sources
- Race-demand profile
- Training considerations and rider intelligence
- Expandable sample workouts

## Explicit removals

Do not reintroduce any of the following without a new owner decision:

- A standalone Final Verdict section.
- A transition strip between the rating and offer.
- `BUILT FOR THIS` framing.
- Race-date repetition inside the custom-plan offer.
- “Less than one gel per ride.”
- “What the plan has to solve.”
- Sticky training-plan CTAs.
- Plan ladders on race pages.
- Plan configurators or preview controls inside Deep Dive.
- Plan/coaching sales copy or purchase links inside Deep Dive.
- Duplicated plan/coaching pitches.

The purpose is to keep one calm commercial decision above the reference layer and
prevent the Deep Dive from repeatedly introducing buying friction.

## Roadie Labs invariants

- Rating key: `fondo_rating`, never `gravel_god_rating`.
- Classes and tokens: `rl-*` and `--rl-*`, never Gravel God `gg-*`/`--gg-*`.
- Palette and typography: Roadie Labs Newsprint/Charcoal system.
- Canonical domain: `https://roadielabs.com/race/<slug>/`.
- GA4 property: `G-WQ7W8XN11N`.
- Page marker: `data-page-format="spine-v2-approved"`.
- Exactly one approved plan CTA and one approved coaching CTA appear above Deep Dive.
- `#ratings` precedes the offer; the offer precedes coaching; coaching precedes
  `#breakdown`; breakdown precedes `#deep-dive`.
- `#training` and `#train-for-race` live inside Deep Dive.
- Deep Dive contains no questionnaire, coaching, plan-guide, configurator, preview,
  or sticky-CTA commerce.
- No duplicate IDs, hardcoded colors, fabricated race content, or data-derived
  `innerHTML`.
- Roadie Labs remains a static SiteGround site; WordPress deployment assumptions are
  invalid here.

## Implementation record

Generator:

- `wordpress/generate_neo_brutalist.py`

Key Roadie Labs commits:

- `162c1b7` — adopt approved Roadie Labs spine
- `0f58d3e` — add repeatable catalog audit

Catalog result:

- 427 race profiles
- 427/427 pages generated
- 427/427 pages have race-demand packs
- 427/427 passed `scripts/audit_spine_v2_catalog.py`
- Focused generator suite: 165 passed, 1 skipped
- Python 3.11 compilation passed
- Rendered QA passed at desktop and 390px mobile with no horizontal overflow
- Deep Dive keyboard/accordion behavior was exercised successfully

Staged output:

- `wordpress/output-spine-v2-stage/`

## Regenerate and verify

```bash
python3 wordpress/generate_neo_brutalist.py --all \
  --output-dir wordpress/output-spine-v2-stage
python3 -m pytest tests/test_neo_brutalist.py -q
uv run --python 3.11 --no-project python -m py_compile \
  wordpress/generate_neo_brutalist.py
python3 scripts/audit_spine_v2_catalog.py
```

## Deploy gate

The staged catalog is not permission to publish. Do not push `main`, SCP pages, or
change SiteGround state without Matti’s separate deploy approval. For an approved
deploy, generate into a dedicated directory, deploy all content-hashed assets required
by the generated pages, sync the 427 page files, verify server-side, and have Matti
flush SiteGround Dynamic Cache. Follow
`.claude/skills/deploy-and-siteground/SKILL.md` exactly.
