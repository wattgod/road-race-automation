# AGENTS.md — entry point for any coding agent

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
