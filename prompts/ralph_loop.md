# Ralph Loop Configuration

## What This Does
This is an autonomous research loop. Each iteration, the agent:
1. Reads `config/seed_events.json` for the event list
2. Checks which events already have profiles in `race-data/`
3. Picks the next 2-3 unresearched events
4. Researches each one (web search, official sites, YouTube)
5. Scores each on 14 dimensions using `config/dimensions.json` rubric
6. Writes JSON profiles to `race-data/{slug}.json`
7. Writes research dumps to `research-dumps/{slug}.md`
8. Runs `python3 scripts/recalculate_tiers.py --dry-run` to verify
9. Commits progress to git

## How to Run

### With ralph-starter
```bash
cd /Users/mattirowe/Documents/GravelGod/road-race-automation
npx ralph-starter run --file prompts/research_prd.md --loops 20
```

### With Claude Code ralph plugin
```bash
cd /Users/mattirowe/Documents/GravelGod/road-race-automation
# Use /ralph command in Claude Code pointing to research_prd.md
```

### Manual overnight script
```bash
cd /Users/mattirowe/Documents/GravelGod/road-race-automation
# Run N iterations, each processes 2-3 events
for i in $(seq 1 20); do
  echo "=== Ralph loop iteration $i ==="
  claude --print "Read prompts/research_prd.md. Check which events in config/seed_events.json don't have profiles yet. Research and score the next 2-3 events. Write profiles to race-data/ and research dumps to research-dumps/. Run recalculate_tiers.py --dry-run to verify. Commit your work." \
    --allowedTools "Read,Write,Edit,Glob,Grep,Bash,WebSearch,WebFetch" \
    2>&1 | tee -a reports/ralph_log_$(date +%Y%m%d).txt
  echo "=== Iteration $i complete ==="
done
```

## Progress Tracking
Progress lives in files, not context. Each new agent instance can see:
- Which profiles exist in `race-data/` (already done)
- Which events are in `config/seed_events.json` (todo list)
- The delta = what to work on next

## Quality Checks Between Loops
After every 10 events, manually run:
```bash
python3 scripts/recalculate_tiers.py --dry-run   # Verify tier distribution
python3 scripts/validate_profiles.py              # Check schema compliance
ls race-data/ | wc -l                             # Count profiles created
```

## Expected Output
- 20 loops × 2-3 events/loop = 40-60 scored profiles overnight
- Each profile: ~5-15KB JSON
- Each research dump: ~2-5KB markdown
- Total API cost: ~$10-15 (Claude API for research + web search)

## Calibration Anchors
The agent uses these completed profiles as scoring references:
- **T1 anchor**: `race-data/maratona-dles-dolomites.json` (score ~95)
- **T2 anchor**: `race-data/gfny-nyc.json` (score ~65)
Research these two FIRST (manually or in loop 1) before batch scoring others.
