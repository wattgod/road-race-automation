# ROADIE LABS — COACHING PHILOSOPHY & TRAINING SYSTEM (v2)

**Status: v2, 2026-07-18. Rewritten after the adversarial audit
(`docs/ROADIE_PHILOSOPHY_CRITIQUE.md`, sol + Fable, 15 findings) and after the
fixes that audit forced were SHIPPED: road-specific variation emphasis in the
master engine, a genuinely differentiating road overlay in the custom pipeline,
honest Testing Week wording, and corrected Compete hours. Every implementation
claim below is written against the shipped artifact it describes and names which
engine it belongs to. Matti's voice pass pending on the philosophy prose; the
technical sections are auditable as written.**

---

## 1. The thesis

**In gravel you choose your power; on the road, the race chooses it.**

A gravel racer mostly rides alone against the course: power is a pacing decision,
and the decisive variables are durability, fueling, and technical execution. A
road racer rides inside a peloton that sets the price of admission: the decisive
moments are repeated supra-threshold surges — attacks, gaps out of corners,
cresting climbs, closing splits — taken with incomplete recovery, at times the
athlete does not pick. Draft changes everything: road racing is stochastic
(coast, then violence) where gravel is steady-state (your watts, all day).

So the shared aerobic engine is trained the same way — physiology doesn't care
what surface you ride on — but road plans bias selection toward surge
repeatability, sustained climbing threshold, and race-shaped simulation, and the
supporting material (skills, tactics, equipment) speaks road.

## 2. The one-paragraph philosophy

Roadie Labs coaches the way Gravel God does at the foundation: open every plan by
measuring the athlete (the Testing Week), apply one named methodology per plan
rather than methodology soup, protect the easy days so the hard days count, build
durability before sharpness, and arrive at race week rested instead of
impressive-in-training. What changes for road is the demand model in §1: the
same workout library is *selected differently* — each of the four road
variations pulls its key sessions and long rides from pools weighted for that
variation's decisive demand — and the guide, tactics, and race-week material are
road-native.

## 3. Architecture — which engine does what (read this before citing anything)

Two engines produce Roadie Labs plans. Claims about one are not claims about the
other.

| | **Master-plan engine** | **Custom athlete pipeline** |
|---|---|---|
| Repo | `gravel-god-training-plans` | `athlete-custom-training-plan-pipeline` |
| Produces | The 40 road master plans (and their per-race clones) sold on TrainingPeaks | One-off custom plans from a real athlete's questionnaire |
| Road mechanism | `ROAD_VARIATION_EMPHASIS` in `engine/workout_generator.py` — for `event_type == "road"` it **replaces** the gravel demand-emphasis table with road-specific category weights per variation | `disciplines.road` overlay in `athletes/config/workout_selection.yaml` + `_DISCIPLINE_INTENSITY` protection in `workout_selector.py` |
| Methodology | Pinned per tier via `methodology_override` in the road base intakes (see §6) | Scored from the athlete's questionnaire by `select_methodology.py` |
| Guides | `engine/guide_generator.py` (hosted at wattgod.github.io/roadie-labs-guides) | `training_guide_builder.py` (fuller road-skills treatment) |

Workout library: one shared library of ~524 structured `.zwo` workouts across
ten categories (Endurance, Tempo, Threshold, VO2max, Anaerobic Capacity,
Explosive Power, Torque, Durability, Race Simulation, Recovery). There is no
separate road workout library and we do not claim one — road differentiation is
**selection**, not new files. The custom pipeline additionally draws on its
archetype system (100 archetypes × durations).

## 4. Demand model and supported scope

Road is not one physiology. Roadie Labs currently models and supports:

- **Gran fondo / sportive / century completion and competitive fondo riding** —
  the core product. Pacing discipline, drafting economy, climbing execution,
  fueling under speed.
- **Hillclimb** — via the Alpine-Fondo variation (sustained threshold + torque).
- **Amateur multi-stage events** — via the Distance variation's durability bias
  plus stage-race logistics in the guide.

Explicitly **not yet supported** as dedicated plan types: criteriums, time
trials, and sprint-finish preparation. The library contains the raw material
(TT Send, Kolie Moore TTE, sprint mechanics work), but no coherent progression
is shipped for those formats, so we don't sell one. When we do, it will be a new
variation axis, not a copy-rename.

## 5. What is road-specific TODAY (post-fix, both engines)

### 5.1 Master engine: road variation emphasis (shipped 2026-07-18)

`ROAD_VARIATION_EMPHASIS` replaces — does not append to — the gravel-authored
emphasis table for road plans. Per variation, key-cardio and long-ride slots are
weighted toward:

| Variation | `demand_emphasis` | Key-cardio bias | Long-ride bias |
|---|---|---|---|
| **Rolling-Fast** | `punchy` | Anaerobic Capacity 0.7, VO2max 0.5, Explosive Power 0.5, Race Sim 0.4 | Race Sim 0.5 |
| **Alpine-Fondo** | `climber` | Threshold 0.7, Torque 0.5, Durability 0.3 | Durability 0.6, Race Sim 0.2 |
| **Distance** | `ultra` | Tempo 0.5, Threshold 0.3, Durability 0.3 | Durability 0.9, Endurance 0.4 |
| **All-Rounder** | `all_rounder` | Race Sim 0.4, Threshold 0.3, Explosive Power 0.2, Torque 0.15 | Race Sim 0.3 |

In the shipped masters this is visible as, e.g., Rolling-Fast plans carrying
Microbursts / Above-CP repeats / Criss-Cross where the gravel equivalent carries
torque work. The 40 masters on TrainingPeaks were regenerated with this table
and verified workout-for-workout on 2026-07-18.

### 5.2 Custom pipeline: the road overlay (rebuilt 2026-07-18)

Post-audit state of `disciplines.road` (the audit found three of four original
rows inert or duplicate — those are gone):

- Base, 2nd intensity: pool widened with **Tempo with Sprints** and **Cadence
  Work** — surge exposure and leg speed inside base, not plain Tempo.
- Build, 3rd intensity: **Microbursts** added (stochastic supra-threshold work);
  the duplicate entries the audit flagged were removed.
- Race prep, 3rd intensity: slot **activated** with a road default of **Race
  Simulation** (it was previously unreachable — `default: null` killed it before
  the overlay applied).
- These road selections are protected from methodology overwrite via
  `_DISCIPLINE_INTENSITY` (regression-tested:
  `TestRoadSelectionSurvivesMethodology`).

Honest mechanics note: overlay entries are **rotating alternatives added to a
pool**, not hard replacements. The bias is real and tested, but an athlete will
still see shared-library staples; that is by design.

### 5.3 Variation assignment for the 427 race SKUs

Every rated road race maps to one variation via a **first-match threshold
cascade** (`scripts/assign_tp_skus.py`): durability ≥ 7 → Distance; else
altitude or climbing ≥ 7 → Alpine-Fondo; else VO2max demand ≥ 7 → Rolling-Fast;
else All-Rounder. Current counts: Alpine-Fondo 176, All-Rounder 153, Distance
73, Rolling-Fast 25. This is a deliberate priority rule, not a multidimensional
nearest-neighbor — a long alpine event classifies Distance first, on the theory
that duration is the demand that DNFs riders. Disclosed here so nobody mistakes
it for something fancier.

### 5.4 Road-native supporting material

- Road guide content: pack riding, descending in groups, road equipment, road
  tire/rim pressure guidance (manufacturer limits, lower-of-tire-and-rim wins —
  never invented PSI). The custom-pipeline guide carries the fuller treatment
  (pacelines, crosswinds, feed-zone craft); the master-engine guide is leaner —
  see §9.
- Brand register: Newsprint/Charcoal monochrome, Source Serif 4 + Sometype
  Mono, honest-critic editorial voice (§10). Support: support@roadielabs.com
  (live, delivery-verified).
- No mental-program tile: Gravel Grit is gravel-branded; road ships without a
  forced counterpart until a name earns its place (Matti G4 ruling).

## 6. Methodology: what actually decides it

The master engine's selector supports twelve methodologies, but **every road
master pins its methodology via `methodology_override` by product tier**:

| Tier | Methodology | Why |
|---|---|---|
| Finisher, Compete, Masters, Save My Race | **Polarized** | The tier's hours support real polarization; predictable product |
| Time-Crunched | **G-Spot** (sweet-spot-leaning) | 5-7 hours can't afford a large easy base; density wins |

So: the road *masters* are methodologically pinned by tier, not scored per
athlete. The *custom pipeline* genuinely scores its four methodologies
(Polarized · Time-Crunched · G-Spot · Traditional Pyramidal) from the athlete's
hours, history, stress, schedule, and goals — and the chosen methodology applies
a named bias within the shared phase structure (base → build → peak → taper),
it does not swap in a wholly different periodization model. We say "applies one
named methodology bias," not "commits to a bespoke periodization," because
that's what the code does.

## 7. The Testing Week — what it does and does not do

Every plan opens with the 7-day self-assessment protocol (RPE-anchored: FTP
estimate, 5-minute, sprint, fade, decoupling, strength screen).

**What it does:** gives the athlete real numbers to set zones — the guide walks
them through updating FTP in TrainingPeaks so every subsequent structured
workout scales from a measured value, and calibrates execution feel for the
plan's RPE language.

**What it does not do:** the plan is generated in one pass before the athlete
ever rides. No engine ingests the test battery and regenerates later weeks.
Adaptation to test results is the athlete's manual FTP update (which rescales
workout targets) plus their own execution calibration — not an automated
feedback loop. Copy anywhere that implies otherwise is wrong and gets fixed
(this was audit finding 6; wording was corrected across engine and guides
2026-07-18).

## 8. Tier matrix (road, as shipped)

Hours below are the base-intake inputs the masters are actually generated from
(`base_intakes/*_road_*.json`) — not marketing ranges.

| Tier | Intake hours | Methodology | Durations | Design center |
|---|---|---|---|---|
| Finisher | 10-12 | Polarized | 8 / 12 / 16wk | Complete strong; durability first |
| Compete | 12-15 | Polarized | 12 / 16wk | Result-oriented; highest load |
| Masters | 10-12 | Polarized, recovery-first spacing | 12 / 16wk | Same engineering as gravel Masters: hard days spaced, recovery protected |
| Time-Crunched | 5-7 | G-Spot | 8 / 12wk | Density over volume |
| Save My Race | 8-10 | Polarized | 6wk | Triage: sharpen what exists |

Weekly skeleton across tiers: 2 key cardio days + long ride + 2 strength days +
endurance filler, scaled by tier hours. (Compete previously carried a "15+"
intake against a 9-13 advertised range — audit finding 7; the intake is now
12-15 and the regenerated masters reflect it.)

## 9. Known gaps & open work (dated 2026-07-18 — kept honest)

- **Heat training is not climate-gated** (either engine): heat cues fire by plan
  week regardless of the race's climate. A cold-race athlete currently reads
  heat-acclimation advice. Fix is queued (Matti: "2 next") — heat work has real
  recovery and adherence costs and should be gated by race climate data, which
  the race databases already hold.
- **Weekly Monday coach notes: not yet on road masters** (gravel masters carry
  14-16 authored notes each; road carry zero). Authored content, not engine
  output. Blocks pilot publish.
- **Pack skills are guide prose, not a trained progression.** The calendar does
  not yet schedule group-ride substitutions or corner-acceleration/feeding
  practice as week-attached notes. On the roadmap (calendarize road
  specificity).
- **Tactical registers not yet split by event format**: current guide tactics
  are fondo-completion tactics ("let the group go, ride your power") — correct
  for the core product, wrong for a competitive mass-start split. Guide
  branching by format is roadmap work; until then the guides serve the
  fondo/sportive scope of §4.
- **Master-engine guides are leaner than custom-pipeline guides** (no
  women's/masters/altitude sections in the master path today). Claims about
  guide content must name the output path.
- **race-day weekday note mismatch** (both catalogs) — pre-existing engine bug,
  ticketed.
- **No Roadie Labs logo mark**; Latin-ext glyphs (Taupō-class) missing from
  baked-image fonts.

## 10. Voice

The Roadie Labs editorial voice is the same honest critic wearing road-racing
literacy: precise, history-aware, allergic to hype. Verdicts name what a race IS
("The Original", "The monument you can ride") — never inflated, never try-hard.
The offer register stays quiet and specific (Built-For rules). Where Gravel God
speaks in mud, suffering, and self-sufficiency, Roadie Labs speaks in pace,
position, tactics, and the long history of the sport.

## 11. Differentiation roadmap

1. Calendarize road specificity: variation/phase-aware week notes (group-ride
   substitution, corner accelerations, feeding under load, crosswind craft).
2. Split guide tactics by event format (fondo / competitive road race / solo-TT
   / hillclimb registers).
3. Climate-gated heat protocol (queued next).
4. Crit / TT / sprint-finish variations — only when a real progression exists.
5. Name + build the road mental curriculum (Gravel Grit's counterpart).
6. Road-native workout modules where the science earns them (pack-surge
   simulation, lead-out work) — added to the library as road-tagged entries,
   not copy-renames.

## 12. Cross-references

- Engines: `gravel-god-training-plans` (`engine/workout_generator.py`
  ROAD_VARIATION_EMPHASIS, `engine/methodology_selector.py`) and
  `athlete-custom-training-plan-pipeline` (`workout_selection.yaml`
  disciplines.road, `workout_selector.py` _DISCIPLINE_INTENSITY,
  `training_guide_builder.py` road path).
- Audit this document answers to: `docs/ROADIE_PHILOSOPHY_CRITIQUE.md`.
- Catalog machine: `gravel-god-training-plans` (specs/road-tp-catalog/SPEC.md,
  tools/tp_catalog_config.py ROAD, qc/ROAD_SOL_QC_SPEC.md).
- Brand: `road-labs-brand`. Guides: wattgod/roadie-labs-guides (Pages).
- Rated race database: this repo — 427 profiles, fondo_rating 14-dimension
  model, `scripts/assign_tp_skus.py` variation cascade.
