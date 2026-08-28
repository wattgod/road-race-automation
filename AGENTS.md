# AGENTS.md — entry point for any coding agent

## AI writing as Matti

Before drafting, rewriting, or approving copy presented as Matti Rowe or one of
his brands, read `docs/AI_WRITING_POLICY.md`. Its source-retrieval,
provenance, privacy, and anti-slop requirements are binding.

## Baseline editorial and citation rules

These rules apply to every agent and every public-facing race, rating, article,
email, and product surface:

- Write the finished judgment, never the research process. Do not say a source's
  "assessment rings true," "according to our research," "sources say," or name
  the person/site that supplied an ordinary fact unless the attribution itself
  materially matters.
- Do not use the brand as a synthetic narrator (for example, "Roadie Labs
  scores..."). State the judgment directly in the brand's established voice.
- Lead every Course and Editorial/Experience rating with one sharp, standalone
  verdict sentence before discussing individual criteria.
- Put a numbered inline marker such as `[3]` on every factual or quoted claim.
  Every marker must resolve to that page's numbered source list; preserve stable
  source order, never invent a source number, and never use attribution prose as
  a substitute for the marker.
- Preserve a real person's exact words inside quotation marks and cite the quote.
  Clean up only the surrounding prose; do not flatten actual human language into
  house style.
- Cut AI filler: importance puffery, vague scene-setting, fake quotations,
  repetitive conclusions, canned transitions, generic superlatives, and words
  such as "delve," "testament," or "game-changing" when a concrete statement
  will do.
- Citation correctness and voice quality are separate gates. A sourced sentence
  can still be bad copy, and clean copy can still be unsupported. Verify both.

Binding instructions live in `CLAUDE.md` — read it first; it is written for
all agents, not just Claude. Roadie Labs uses `fondo_rating`, never
`gravel_god_rating` — the single most common cross-repo mistake.

## Handover skills

Distilled operating knowledge — incidents, settled decisions, playbooks not
derivable from the code. Read the one matching your task before starting.

| Before you… | Read |
|---|---|
| Deploy to roadielabs.com / touch SiteGround or WordPress | `.claude/skills/deploy-and-siteground/SKILL.md` |
| Add/edit race profiles, scrape, regenerate pages | `.claude/skills/schema-and-data/SKILL.md` |
| Touch visual styling, copy, or trust-bearing claims | `.claude/skills/brand-and-trust/SKILL.md` |

## Non-negotiables (full text in CLAUDE.md)

- `fondo_rating` is the rating key. `gravel_god_rating` is the wrong repo.
- Roadie Labs is Newsprint/Charcoal, not the Gravel God desert palette.
- Never fabricate testimonials, quotes, or review counts. Ever.
- If the site is unreachable, check the SSL cert before touching code.
