# CLAUDE.md — Road Labs: Scored Road Cycling Event Database

## Project Overview
Road Labs is a scored event database for road cycling (gran fondos, sportives, centuries, hillclimbs, multi-stage amateur races). Migrated from the Gravel God system in Sprint 41. Clinical, technical, data-driven brand identity.

- **Brand**: Road Labs
- **Domain**: roadlabs.cc (not yet live)
- **CSS variable prefix**: `--rl-` (not `--gg-`)
- **Palette**: Navy / steel blue / signal red on cool white. Neo-brutalist rules: no border-radius, no box-shadow, solid borders.
- **Fonts**: Unbounded (display), Sometype Mono (data), Source Serif 4 (editorial)
- **Brand tokens**: `wordpress/brand_tokens.py` reads from `road-labs-brand` repo

## Architecture
```
road-race-automation/
├── race-data/           ← 427 event JSON profiles (source of truth)
├── research-dumps/      ← Raw research per event
├── scripts/             ← Generators, validators, scoring, batch tools
├── wordpress/           ← HTML generators, brand tokens, mu-plugins
├── web/                 ← Client-side output (race-index.json, search UI, robots.txt)
├── data/                ← Stripe products, indexes
├── config/              ← dimensions.json, schema.json, seed_events.json
├── tests/               ← pytest suite
├── docs/                ← Scoring system docs, deploy runbook
├── prompts/             ← Claude prompt templates for research/scoring
├── seo/                 ← SEO tooling
├── workers/             ← Cloudflare Workers (review-intake, training-plan-intake)
└── reports/             ← Generated reports
```

## Scoring System
- **14 dimensions** (1-5 scale each): distance, climbing, descent_technicality, road_surface, climate_risk, altitude, logistics, prestige, organization, scenic_experience, community_culture, field_depth, value, expenses
- **Bonus**: cultural_impact (0-5, additive — not included in denominator)
- **Formula**: `overall_score = round((sum_of_14 + cultural_impact) / 70 * 100)`
- **Tiers**: T1 (>=80), T2 (>=60), T3 (>=45), T4 (<45)
- **Prestige override**: p5 + score>=75 → T1, p5 + score<75 → T2 cap, p4 = 1-tier promotion (not into T1)
- **Config source of truth**: `config/dimensions.json`

### Rating Key
```python
# CORRECT — Road Labs uses fondo_rating
d['race']['fondo_rating']

# WRONG — this is the Gravel God key, do NOT use
d['race']['gravel_god_rating']
```

### Disciplines
`gran_fondo`, `sportive`, `century`, `multi_stage`, `hillclimb`

### Key Differences from Gravel God
1. Rating key is `fondo_rating`, NOT `gravel_god_rating`
2. Dimension names differ: `distance` (not `length`), `climbing` (not `elevation`), `road_surface` (new), `adventure` (dropped)
3. Dual units: `distance_km` + `distance_mi`, `elevation_m` + `elevation_ft`
4. New `climb_profile` section with per-climb gradient data (many profiles have `_needs_enrichment: true` placeholder)
5. `route_options` array for events with short/medium/long courses

## Critical Rules
1. **`_safe(0)` must check `is None`** — Python falsiness. `not 0` is True. Check `val is None or val == ""`, not `not val`.
2. **Never use innerHTML with data-derived values** — XSS. Use textContent/createElement.
3. **`json.dumps` inside `<script>` = injection** — `</script>` in data breaks HTML. Use `_safe_json_for_script()`.
4. **Deep copy cached data** — `copy.deepcopy()` on any data returned to callers.
5. **Regenerate output after editing generators** — `generate_*.py` edits don't auto-update output files.
6. **Config is source of truth** — scoring dimensions live in `config/dimensions.json`, never hardcoded.
7. **Scores come from `_parse_score()`** — `int("3.5")` crashes. Always normalize.
8. **Every score needs a citation** — no fabricated claims. Run `scripts/audit_fabricated_claims.py` after batches.
9. **SVG attrs can't resolve `var()`/`color-mix()`** — use CSS classes or the `COLORS` dict from `brand_tokens.py`.
10. **Brand tokens source of truth**: `wordpress/brand_tokens.py`. Never hardcode hex values in generators.
11. **`backdrop-filter` needs `@supports` fallback + `prefers-reduced-motion`** — Firefox/Linux lacks support.

## Running Tests
```bash
python3 -m pytest tests/ -v
```

## Common Commands
```bash
# Recalculate all tiers (dry-run first)
python3 scripts/recalculate_tiers.py --dry-run
python3 scripts/recalculate_tiers.py

# Generate search index
python3 scripts/generate_index.py

# Validate profiles
python3 scripts/validate_profile.py
python3 scripts/audit_fabricated_claims.py

# Preflight quality check
python3 scripts/preflight_quality.py

# Validate citations
python3 scripts/validate_citations.py

# Generate sitemap
python3 scripts/generate_sitemap.py

# Generate race pages
python3 wordpress/generate_neo_brutalist.py

# Generate homepage
python3 wordpress/generate_homepage.py
```

## Key Scripts
| Script | Purpose |
|--------|---------|
| `scripts/recalculate_tiers.py` | Recompute overall_score and tier for all profiles |
| `scripts/generate_index.py` | Build `web/race-index.json` from race-data/ |
| `scripts/validate_profile.py` | Schema validation for race JSON profiles |
| `scripts/audit_fabricated_claims.py` | Check for unsourced claims in profiles |
| `scripts/fact_check_profiles.py` | Cross-reference profile data against sources |
| `scripts/migrate_from_gravel.py` | Sprint 41 migration tool (gravel_god_rating → fondo_rating) |
| `scripts/race_demand_analyzer.py` | Compute demand vectors for training integration |
| `scripts/youtube_enrich.py` | YouTube video enrichment for race profiles |
| `scripts/youtube_extract_intel.py` | Extract rider intel from video transcripts |
| `scripts/preflight.py` | Full pre-deploy checklist runner |
| `wordpress/brand_tokens.py` | CSS custom properties, colors, font-face declarations |
| `wordpress/generate_neo_brutalist.py` | Race page HTML generator |

## Enrichment State
- Many migrated profiles have `climb_profile._needs_enrichment: true` — these are placeholders awaiting gradient data
- YouTube enrichment and rider intel from gravel-race-automation may need re-validation for road context
