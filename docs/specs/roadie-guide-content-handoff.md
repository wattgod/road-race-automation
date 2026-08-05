# Handoff — Write the Roadie Labs Training Guide (content)

**For:** Fable, in Cursor.
**Job:** expand `guide/road-guide-content.json` from a 9,385-char skeleton to a
real guide. **Writing only — do not build or deploy.**
**Companion spec:** `docs/specs/roadie-guide-handoff.md` covers the generator
port and deploy. Read this one first; you do not need the toolchain to write.
**Written:** 2026-08-05.

---

## 0. Everything, by absolute path

| What | Path |
|---|---|
| **The file you edit** | `/Users/mattirowe/Documents/GravelGod/road-race-automation/guide/road-guide-content.json` |
| This handoff | `…/road-race-automation/docs/specs/roadie-guide-content-handoff.md` |
| Build/port spec | `…/road-race-automation/docs/specs/roadie-guide-handoff.md` |
| **Exemplar to match** | `/Users/mattirowe/Documents/GravelGod/gravel-race-automation/guide/gravel-guide-content.json` |
| Block renderers (source of truth for what's legal) | `…/gravel-race-automation/wordpress/generate_guide.py` → `BLOCK_RENDERERS` |
| Road race profiles (for `race_reference`) | `…/road-race-automation/race-data/*.json` (397 files) |
| Road brand tokens | `…/road-race-automation/wordpress/brand_tokens.py` |
| Repo rules | `…/road-race-automation/CLAUDE.md` |
| Repo skills | `…/road-race-automation/.claude/skills/` — `brand-and-trust`, `schema-and-data`, `deploy-and-siteground` |

Open the gravel exemplar side by side. It is the single most useful reference
here — it shows depth, rhythm, and how blocks get used in anger.

---

## 1. Why this matters

Roadie Labs has **6 lifetime email leads, 0 opens, 0 clicks, 0 sales**.
Gravel has ~240 enrollments and 22–27% open rates off the same machinery. The
difference is not the emails — it is that road has no top-of-funnel. Its guide
404s at `roadielabs.com/guide/` and there is no exit-intent capture.

This guide is the biggest single lever on that number. It is also the surface
that, on the gravel side, produces the warmest replies in the whole funnel — a
rider finishes a chapter, gives an address, and gets a chapter-aware email.

---

## 2. What's there now

Eight chapters, correct schema, good bones, **far too thin**:

| # | id | title | gated | current |
|---|---|---|---|---|
| 1 | `what-is-road-racing` | What Is Road Racing? | no | ~1,335 ch |
| 2 | `choosing-your-race` | Choosing Your Race | no | ~1,120 ch |
| 3 | `building-the-engine` | Building the Engine | no | ~1,194 ch |
| 4 | `workout-execution` | Workout Execution | **yes** | ~1,233 ch |
| 5 | `fueling-for-the-distance` | Fueling for the Distance | **yes** | ~1,161 ch |
| 6 | `pack-skills-and-tactics` | Pack Skills & Race Tactics | **yes** | ~1,250 ch |
| 7 | `race-week` | Race Week | **yes** | ~1,009 ch |
| 8 | `after-the-finish` | After the Finish | **yes** | ~1,083 ch |

Each chapter is **one section, three `prose` blocks**. The prose that exists is
good and genuinely road — keep it, build around it:

> "A flat 100-mile fondo rewards sustained tempo and pack craft; a mountainous
> sportive with 10,000 ft of climbing rewards a high power-to-weight and the
> discipline to ride your own pace up the cols. Pick the demands first, then
> build toward them."

**Target:** gravel runs 144,916 chars total, ~18k per chapter, 6–12 sections
each. Aim for the same order of magnitude. Do not pad to hit a number — a tight
12k chapter beats a bloated 18k one.

---

## 3. Schema — exactly what's legal

```
{
  "title": "...", "subtitle": "...", "meta_description": "...",
  "personalization": { ... },      // MISSING in road — see §4
  "glossary": { "TERM": "definition", ... },   // MISSING in road — see §4
  "chapters": [ {
      "number": 1,
      "id": "what-is-road-racing",       // becomes /guide/{id}/ — DO NOT CHANGE
      "title": "...", "subtitle": "...",
      "gated": false,
      "cta_after": null,                  // or a CTA key
      "hero_image": "ch1-hero",
      "sections": [ { "id": "...", "title": "...", "blocks": [ ... ] } ]
  } ]
}
```

`section.title` is optional (gravel omits it in places). `section.id` must be
unique within the file.

### Block types

29 renderers exist. These 18 are proven in the gravel guide — **prefer these**:

`prose` (89 uses), `image` (30), `callout` (20), `personalized_content` (17),
`race_reference` (15), `timeline` (11), `data_table` (9), `race_callout` (9),
`tabs` (8), `accordion` (8), `knowledge_check` (8), `process_list` (7),
`hero_stat` (3), `calculator` (3), `scenario` (3), `flashcard` (2),
`decision_tree` (1), `zone_visualizer` (1).

Also available but unused in gravel: `black_box`, `commitment`,
`continue_gate`, `drill`, `labeled_graphic`, `process`, `quiz`,
`recovery_protocol`, `sensation_target`, `sorting_activity`, `video`.

**Do not invent a block type.** If it is not in `BLOCK_RENDERERS`, it renders as
nothing. Check the source before using anything outside the proven 18.

### Shapes, verbatim from the gravel guide

```jsonc
{"type": "prose", "content": "..."}                  // markdown inline supported

{"type": "callout", "style": "highlight", "content": "..."}

{"type": "hero_stat", "value": "8", "unit": "%",
 "context": "Of 328 rated races earn Tier 1 status. The bar is deliberately high."}

{"type": "data_table", "caption": "...",
 "headers": ["Component", "Minimum Viable", "Why", "Skip Until Later"],
 "rows": [["Frame", "...", "...", "..."]]}

{"type": "process_list", "items": [
 {"label": "Fitness", "detail": "...", "percentage": 70}]}

{"type": "timeline", "title": "The Adaptation Cycle",
 "steps": [{"label": "Stress", "content": "..."}]}

{"type": "accordion", "items": [{"title": "...", "content": "..."}]}

{"type": "knowledge_check", "question": "...",
 "options": [{"text": "...", "correct": false, "explanation": "..."}]}

{"type": "scenario", "prompt": "...", "options": [{"label": "...", "response": "..."}]}

{"type": "image", "asset_id": "ch1-rider-grid",
 "alt": "...", "caption": "..."}          // asset_id must exist — see §5

{"type": "race_reference", "slug": "mallorca-312", "context": "distance"}

{"type": "tabs", "tabs": [{"label": "...", "rider_type": "...", "title": "...", "content": "..."}]}

{"type": "personalized_content", "variants": {"<rider_id>": {"content": "..."}}}
```

---

## 4. Two things you must add that road does not have

### `personalization` — required before any `tabs` / `personalized_content`

Gravel's:

```json
{"rider_types": [
  {"id": "ayahuasca",  "label": "Ayahuasca",  "hours": "0-5 hrs/week",  "default_ftp": 150},
  {"id": "finisher",   "label": "Finisher",   "hours": "5-12 hrs/week", "default_ftp": 200},
  {"id": "competitor", "label": "Competitor", "hours": "12-18 hrs/week","default_ftp": 260},
  {"id": "podium",     "label": "Podium",     "hours": "18+ hrs/week",  "default_ftp": 320}],
 "storage_key": "gg_guide_rider_type"}
```

**"Ayahuasca" is a gravel-culture joke and does not transfer.** Road needs its
own archetypes in road terms — the axis riders actually sort themselves by is
usually *fondo finisher → group-ride sharp end → licensed racer*, and
power-to-weight matters more than raw FTP on climbing courses. Propose the set
to Matti before writing 17 personalised variants against it. Use
`storage_key: "rl_guide_rider_type"` (road prefix, not `gg_`).

### `glossary` — flat `{"TERM": "definition"}`, 15 entries in gravel

Gravel's are power/training terms (FTP, CTL, ATL, TSB, TSS…) — most transfer
directly. Add road-specific ones: echelon, cat/category, sportive vs fondo vs
gran fondo, neutral start, feed zone, broom wagon, UCI gran fondo qualifier,
autobus. Drop anything gravel-only.

---

## 5. Hard constraints

- **Never invent a fact, number, race, or citation.** This is the whole brand
  position — Roadie Labs is an honest critic. See the repo's `brand-and-trust`
  skill before writing any trust-bearing claim.
- **`race_reference.slug` must exist** in `race-data/`. 397 road profiles are
  available. Verified high-scoring slugs you can safely cite:
  `maratona-dles-dolomites` (90), `letape-du-tour` (90), `haute-route-alps`
  (87), `cheaha-challenge-gran-fondo` (87), `tour-of-flanders-sportive` (86),
  `mallorca-312` (86), `la-marmotte` (86), `quebrantahuesos` (84), `le-loop`
  (84), `paris-brest-paris` (83). Anything else, check the file exists first.
- **`image.asset_id` must have a real asset.** Do not reference images that do
  not exist — they render as a hole. If in doubt, write without images and flag
  where one would earn its place.
- **This is road, not gravel.** Tire pressure, washboard, tire clearance, mud,
  "gravel" — all out. In: power-to-weight, cols, echelons, pack craft, wheel
  position, sportive/fondo/gran fondo distinctions, feed zones, group dynamics,
  descending in a bunch, cat racing where relevant.
- **Don't copy gravel prose and swap nouns.** The *structure* transfers, the
  *content* does not. A reader who rides both will notice instantly, and that
  is the exact credibility the brand trades on.
- **Voice:** dry-direct coaching prose, personality through professionalism.
  This is a product surface, not a Substack essay — no hot-take register, no
  gonzo. Treat the reader as an adult. Load the `voice` skill; the third
  register ("Product Surfaces") is the one you want.
- **Banned:** fabricated anything, fake scarcity, countdown timers, hype
  adjectives, identity-transformation promises, defensive copy ("no sponsors"),
  "as promised" sequence meta, P.S. teasers.
- **Matti reads every word before publish.** Do not treat any of this as
  shippable on your own signature.

---

## 6. Chapter briefs

Keep every existing prose block. Build outward from it.

1. **What Is Road Racing?** — the landscape: sportive vs gran fondo vs
   crit vs road race vs randonnée. What each actually demands. Who the guide is
   for. The honest version of "can I finish this." Good place for `hero_stat`
   and a `data_table` of event types.
2. **Choosing Your Race** — matching event demands to your engine and calendar.
   Runway (14–18 weeks from a real base for a first century/fondo). One A-event,
   B-events as hard training days. Climbing honesty and weight-adjusted
   threshold. `race_reference` blocks earn their place here.
3. **Building the Engine** — aerobic base, threshold, the role of volume,
   why power-to-weight dominates on climbing courses. `timeline` for the
   adaptation cycle; `personalized_content` by rider archetype.
4. **Workout Execution** *(gated)* — translating a prescription into a ride.
   Pacing intervals, what to do when you're short on sleep or time,
   adjusting mid-session. `scenario` and `knowledge_check` fit naturally.
5. **Fueling for the Distance** *(gated)* — carbs/hour, drinking, the
   difference between a 4-hour fondo and a 7-hour mountain day, feed-zone
   practicalities, GI training. `calculator` if the numbers warrant it.
6. **Pack Skills & Race Tactics** *(gated)* — the chapter with no gravel
   equivalent and the strongest reason a road guide has to exist. Wheel
   position, echelons in crosswind, cornering in a bunch, when to move up,
   descending safely in a group, energy cost of bad positioning.
7. **Race Week** *(gated)* — taper, travel, equipment check, sleep, the day
   before, morning routine. `process_list` / `accordion` suit checklists.
8. **After the Finish** *(gated)* — recovery, what to learn from the data,
   deciding the next objective, off-season.

---

## 7. Before you hand back

```bash
cd /Users/mattirowe/Documents/GravelGod/road-race-automation

# 1. valid JSON + a structural sanity pass
python3 - <<'PY'
import json, pathlib
d = json.load(open('guide/road-guide-content.json'))
ids = [c['id'] for c in d['chapters']]
assert len(ids) == len(set(ids)) == 8, ids
tot = 0
for c in d['chapters']:
    n = len(json.dumps(c))
    tot += n
    secs = len(c.get('sections', []))
    blocks = sum(len(s.get('blocks', [])) for s in c.get('sections', []))
    print(f"ch{c['number']} {c['id']:28} {n:>7,} chars  {secs} sections  {blocks} blocks")
print(f"TOTAL {tot:,} chars   (gravel: 144,916)")
PY

# 2. every race_reference slug resolves
python3 - <<'PY'
import json, pathlib, re
src = pathlib.Path('guide/road-guide-content.json').read_text()
slugs = set(re.findall(r'"slug":\s*"([a-z0-9-]+)"', src))
missing = [s for s in slugs if not pathlib.Path(f'race-data/{s}.json').exists()]
print("race_reference slugs:", len(slugs), "| MISSING:", missing or "none")
PY

# 3. no gravel vocabulary leaked in — REVIEW the hits, don't auto-strip them
grep -oiE "gravel|washboard|tire pressure|tire clearance" guide/road-guide-content.json | sort | uniq -c
```

On the current file that last check returns exactly one hit, and it is **correct
and should stay** — ch1 uses gravel as a deliberate contrast:

> "What makes the road different from gravel or the trail is the pack. Drafting
> is the whole game — sit in the right wheel and you save 25-30% of your energy."

That is the good use. The bad use is gravel *mechanics* smuggled in as road
advice. Read every hit; don't let a grep delete a working sentence.

Then: **do not commit to `main`.** Branch (`content/roadie-guide-expansion`),
open a PR, and let Matti read it. If you touched anything outside the content
file, run `python3 -m pytest tests/ -q` and get an adversarial review:

```bash
codex exec -m gpt-5.6-sol -s read-only -C . < brief.md > review.md
```

---

## 8. Open decision Matti still owns

Chapters 4–8 are marked `gated: true`. At current depth that puts **three
paragraphs behind an email wall** — the exact broken-promise pattern that
triggered this whole audit (a lead replied "however no guide attached?" to a
gravel email, and unwinding that found the quiz dead, five capture forms
reporting false success, and an HTML-injection hole in the email templates).

If you expand chapters 4–8 to real depth, gating is honest and the flags stay.
If the expansion stops short, flip them to `false` and ship the guide free —
better a strong free asset than a wall around a stub. **Flag which one you did
in the PR description.** Do not leave it ambiguous.
