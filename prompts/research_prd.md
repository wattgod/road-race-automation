# PRD: Research Road Cycling Events

## Objective
Research road cycling events from the seed list and produce scored JSON profiles.

## Input
- Seed event list: `config/seed_events.json`
- Scoring rubric: `config/dimensions.json`
- Schema: `config/schema.json`
- Calibration anchors: `race-data/maratona-dles-dolomites.json` (T1), `race-data/gfny-nyc.json` (T2)

## Completion Criteria
For each event in `config/seed_events.json` that does NOT already have a profile in `race-data/`:

- [ ] Research dump exists at `research-dumps/{slug}.md` (1-3 pages of raw notes, quotes, URLs)
- [ ] Scored JSON profile exists at `race-data/{slug}.json` matching `config/schema.json`
- [ ] All 14 scoring dimensions have integer scores (1-5)
- [ ] Every score has a citation in the `citations` array
- [ ] `vitals` section is complete (distance_km, distance_mi, elevation_m, elevation_ft, location, date)
- [ ] `climb_profile` section exists for any event with climbing score >= 3
- [ ] `final_verdict.one_liner` is filled
- [ ] `fondo_rating.discipline` is set to the correct discipline tag
- [ ] Profile passes `python3 scripts/validate_profile.py race-data/{slug}.json`

## Process Per Event

### Step 1: Research
Use web search to find:
- Official race website (distance, elevation, registration, date, field size)
- Route details (climbs, surface, key features)
- Community opinions (Reddit, cycling forums, race reports)
- YouTube recaps (if available)
- Historical data (founding year, notable moments)
- Logistics (airport, lodging, transport)

Save raw research to `research-dumps/{slug}.md`.

### Step 2: Score
Using the rubric in `config/dimensions.json`, score all 14 dimensions. For each score, note the citation that supports it. Use the calibration anchor events to calibrate:
- Maratona dles Dolomites = T1 reference (95 overall, climbing=5, scenic=5)
- GFNY NYC = T2 reference (~65 overall, logistics=1, prestige=3)

### Step 3: Build Profile
Create `race-data/{slug}.json` matching the schema. Required sections:
- `race.name`, `race.slug`, `race.tagline`
- `race.vitals` (all distance/elevation in BOTH km/m and mi/ft)
- `race.fondo_rating` (all 14 dimensions + overall_score + tier + discipline)
- `race.climb_profile` (if climbing >= 3)
- `race.course_description` (character, signature challenge)
- `race.logistics` (airport, lodging, official site)
- `race.history` (founded, origin story if available)
- `race.final_verdict` (one_liner, should_you_race)
- `race.citations` (at least 3 per event)

### Step 4: Validate
Run `python3 scripts/recalculate_tiers.py --dry-run` to verify the score/tier math is correct.

## Quality Gates
- No fabricated claims (every factual statement must have a citation)
- Scores must be calibrated against anchor events
- Distance/elevation must be verified against official source
- Tier distribution should trend toward: ~8% T1, ~20% T2, ~35% T3, ~37% T4

## Events Per Loop
Process 2-3 events per Ralph loop iteration. Progress is in files, not context.
