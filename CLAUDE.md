# CLAUDE.md — Road Race / Gran Fondo Event Database

## Project Overview
Scored event database for road cycling events (gran fondos, sportives, centuries, hillclimbs, multi-stage amateur races). Modeled on the Gravel God system.

## Architecture
```
road-race-automation/
├── race-data/           ← Event JSON profiles (source of truth)
├── research-dumps/      ← Raw research per event
├── scripts/             ← Generators, validators, scoring, batch tools
├── wordpress/           ← HTML generators, mu-plugins (future)
├── web/                 ← Client-side output (index, search, sitemap)
├── data/                ← stripe-products.json, indexes
├── config/              ← dimensions.json, schema.json (scoring system definition)
├── tests/               ← pytest suite
├── docs/                ← Scoring system docs, deploy runbook
└── prompts/             ← Claude prompt templates for research/scoring
```

## Scoring System
- **14 dimensions** (1-5 scale each): distance, climbing, descent_technicality, road_surface, climate_risk, altitude, logistics, prestige, organization, scenic_experience, community_culture, field_depth, value, expenses
- **Bonus**: cultural_impact (0-5, additive)
- **Formula**: `overall_score = round((sum_of_14 + cultural_impact) / 70 * 100)`
- **Tiers**: T1 (>=80), T2 (>=60), T3 (>=45), T4 (<45)
- **Prestige override**: p5 + score>=75 → T1, p5 + score<75 → T2 cap, p4 = 1-tier promotion (not into T1)
- **Rating key**: `race.fondo_rating` (NOT `gravel_god_rating`)
- **Disciplines**: gran_fondo, sportive, century, multi_stage, hillclimb
- **Config source of truth**: `config/dimensions.json`

## Key Differences from Gravel God
1. Rating key is `fondo_rating`, not `gravel_god_rating`
2. Dual units: `distance_km` + `distance_mi`, `elevation_m` + `elevation_ft`
3. New `climb_profile` section with per-climb gradient data
4. `route_options` array for events with short/medium/long courses
5. Different dimension names: descent_technicality, road_surface, scenic_experience, community_culture

## Critical Rules
1. **`_safe(0)` must check `is None`** — Python falsiness. `not 0` is True. Check `val is None`, not `not val`.
2. **Never use innerHTML with data** — XSS. Use textContent/createElement.
3. **`json.dumps` inside `<script>` = injection** — `</script>` in data breaks HTML. Use `_safe_json_for_script()`.
4. **Deep copy cached data** — `copy.deepcopy()` on any data returned to callers.
5. **Regenerate output after editing generators** — `generate_*.py` edits don't auto-update files.
6. **Config is source of truth** — scoring dimensions are in `config/dimensions.json`, not hardcoded.
7. **Scores come from `_parse_score()`** — `int("3.5")` crashes. Always normalize.
8. **Every score needs a citation** — no fabricated claims. Run `audit_fabricated_claims.py` after batches.

## Running Tests
```bash
python3 -m pytest tests/ -v
```

## Scoring an Event
```bash
# Recalculate all tiers
python3 scripts/recalculate_tiers.py --dry-run
python3 scripts/recalculate_tiers.py

# Generate index
python3 scripts/generate_index.py
```
