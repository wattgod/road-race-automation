# ROADIE LABS — COACHING PHILOSOPHY & TRAINING SYSTEM (v1 DRAFT)

**Status: v1, drafted 2026-07-19 by Fable for Matti's edit — this is the reference document
for how Roadie Labs training plans are built, what they share with Gravel God, what is
genuinely road-specific today, and what is on the differentiation roadmap. It is written to
be HONEST: nothing here claims road-specific science we have not built. Matti's voice pass
pending; treat the philosophy sections as his to rewrite.**

---

## 1. The one-paragraph philosophy

Roadie Labs coaches the same way Gravel God does, because physiology doesn't care what
surface you ride on: measure the athlete first (the Testing Week), pick ONE methodology and
commit to it, protect the easy days so the hard days count, build durability before
sharpness, and arrive at race week rested instead of impressive-in-training. What changes
for road is the *demand profile*: road racing is decided by sustained climbs, repeated
surges, pack dynamics, and pacing discipline at higher average speeds — so road plans bias
the intensity library toward steady-state and progressive threshold work over gravel's
torque/technicality work, and the supporting material (skills, equipment, race-week
logistics) speaks road.

## 2. The shared engine (identical to Gravel God — by design, stated plainly)

- **Testing Week opens every plan**: 7-day self-assessment protocol; every later zone
  prescription derives from numbers the athlete produced, not a calculator's guess.
- **One methodology per plan, chosen by the engine from the athlete/variation profile**:
  Polarized · Time-Crunched (sweet-spot-leaning) · G-Spot · Traditional Pyramidal. The
  selector scores realistic weekly hours, limiter, and runway; the plan then COMMITS — no
  methodology soup.
- **Mesocycle arc**: base → build → peak → taper (build_peak_taper progression), weekly
  structure anchored on 2 key cardio days + long ride + 2 strength days + endurance filler,
  scaled by tier hours (Finisher 7-11 · Compete 9-13 · Masters 7-11 recovery-first ·
  Time-Crunched 4-6 · Save My Race 5-9).
- **Durability library** (shared 525-workout pool), strength program with video
  walkthroughs, compliance gating, race-week taper logic, and the same honest-coaching
  register in every workout description.
- **Masters tier**: same recovery-first structuring as gravel (harder sessions spaced,
  recovery protected) — the road Masters plans inherit that engineering unchanged.

## 3. What is road-specific TODAY (the honest list)

1. **Intensity selection overlay** — road slots pull from a road alternatives pool where
   gravel pulls torque/technicality work:
   | Phase/slot | Gravel gets | Road gets |
   |---|---|---|
   | Base, 2nd intensity | SFR / low-cadence torque | **Tempo** |
   | Build, 1st intensity | Microbursts | **Threshold Progressive** |
   | Build, 3rd intensity | Mixed Climbing | **Blended VO2max + G-Spot** |
   | Race prep | (course-specific) | **G-Spot** (slot currently inert — known bug, see §6) |
   These selections are protected from methodology overwrite (fixed + tested 2026-07-18).
2. **Four road plan variations**, mapped from each race's fondo profile:
   **Alpine-Fondo** (sustained-climbing bias) · **Rolling-Fast** (punchy/surge bias) ·
   **Distance** (long-steady bias) · **All-Rounder** (balanced). All 427 rated road races
   are pre-mapped to a variation.
3. **Road guide content**: Road Skills chapter (pacelines, cornering at speed, descending
   in groups, feed-zone craft), road equipment checklist, road tire/rim pressure guidance
   (manufacturer limits, lower-of-tire-and-rim wins — never invented PSI), women's-specific
   and masters sections in road register.
4. **Brand register**: Newsprint/Charcoal monochrome, Source Serif 4 + Sometype Mono,
   racing-culture-literate honest-critic editorial voice (see §7). Support:
   support@roadielabs.com.
5. **No mental-program tile**: Gravel Grit is gravel-branded; the road equivalent is
   deliberately unnamed until a name earns its place (Matti G4 ruling, 2026-07-18). Road
   plans ship without a mental-curriculum tile rather than with a forced one.

## 4. What is deliberately NOT claimed

- No separate road workout library exists. We do not claim "road-specific intervals
  engineered from road racing science" — the library is shared, the *selection* is
  road-biased. Copy must never overclaim this (same honesty rule as the gravel
  methodology-blindness ruling).
- No crit/sprint-finish variation yet (see roadmap).
- Periodization philosophy is not road-differentiated: same methodology engine, same arc.
  What differs is which workouts fill the slots and what the athlete reads around them.

## 5. The plan-content stack (what a buyer actually receives)

Per plan: Testing Week + full workout calendar (structured, device-exportable) + strength
with videos + heat-training protocols where the race's climate demands them + weekly Monday
coach notes (the week's WHY — see §6 status) + Day-1 guide note linking the hosted Roadie
Labs training guide + day-after-race closeout note (survey/review + next-step) + the
TP listing description in the v3.2 format (verdict line → course paragraph → who-it's-for),
Roadie brand tokens throughout.

## 6. Known gaps & open work (kept honest, dated 2026-07-19)

- **Weekly Monday notes: NOT YET ON ROAD MASTERS** (gravel masters carry 14-16 per plan;
  road masters carry zero). The gravel notes are authored content, not engine output —
  road needs its own pass (port + de-gravel + Roadie register + Matti gate). Blocking
  pilot publish.
- **Day-1 guide note + closeout survey/coupon note**: added per-plan at customization
  (pilot customization phase); closeout note is also the owned-audience capture since TP
  hides buyer emails.
- **race_prep G-Spot slot inert** (`workout_selection.yaml` default None) — separate bug.
- **Race-day weekday note mismatch** (both catalogs): notes can state a weekday that
  disagrees with placement — pre-existing engine bug, ticketed.
- **No Roadie Labs logo mark exists** — listing headers use a neutral placeholder.
- **Latin-ext glyphs** (Taupō-class) render as missing-glyph boxes in baked images until a
  font-fallback chain is built.

## 7. Voice (working definition — Matti to ratify)

The Roadie Labs editorial voice is the same honest critic wearing road-racing literacy:
precise, history-aware, allergic to hype. Verdicts name what a race IS ("The Original",
"A domestique's home roads", "The monument you can ride") — never inflated, never
try-hard. The offer register stays quiet and specific (Built-For rules). Where Gravel God
speaks in mud, suffering and self-sufficiency, Roadie Labs speaks in pace, position,
tactics, and the long history of the sport.

## 8. Differentiation roadmap (G2-B track, unscheduled)

1. Name + build the road mental curriculum (Gravel Grit's counterpart).
2. Crit-punchy / sprint-finish variation axis (from current-plan-system-map).
3. Road-native workout modules where the science earns them (pack-surge simulation,
   lead-out work, hillclimb pacing blocks) — added to the LIBRARY as road-tagged entries,
   not copy-renames.
4. Discipline-differentiated periodization only if/when we can defend it honestly.

## 9. Cross-references

- Engine: `athlete-custom-training-plan-pipeline` (archetype registry, workout_selection.yaml
  disciplines.road, workout_selector._DISCIPLINE_INTENSITY, training_guide_builder road path).
- Catalog machine: `gravel-god-training-plans` (specs/road-tp-catalog/SPEC.md, tp_catalog_config
  ROAD, road who-for lines, ROAD_SOL_QC_SPEC).
- Brand: `road-labs-brand` (tokens, fonts). Guides: wattgod/roadie-labs-guides (Pages).
- Rated race database: this repo, 427 profiles, fondo_rating 14-dimension model.
