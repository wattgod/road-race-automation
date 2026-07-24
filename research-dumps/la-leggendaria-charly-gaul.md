# La Leggendaria Charly Gaul — Research Dump

Debt-sweep verification pass (batch 6), 2026-07-24.

## Eligibility
- **Status: defunct** (already correctly set from a prior pass; this pass confirmed and extended the finding).
- Source: https://www.quicicloturismo.it/2022/02/17/leggendaria-charly-gaul-game-over-e-fine-della-storia-non-siamo-piu-in-linea-con-le-dinamiche-degli-eventi-ciclistici/ (organizer's Feb 2022 announcement, "game over").
- Corroborating source (new this pass): https://granfondodailynews.com/2022/02/17/a-legend-calls-it-quits-uci-leggenaria-charly-gaul-gran-fondo-cancelled-for-good/ — independent English-language confirmation with additional detail.

## Key finding: last actual edition was 2019, not later — and a fabricated "2025: 20th edition" line was caught and removed
- WebFetch of granfondodailynews.com confirms: "the last actual edition of La Leggendaria Charly Gaul was held in 2019 (the article states the event 'saw the cancellation of the last two editions' as of Feb 2022, meaning 2020 and 2021 were pandemic cancellations)."
- The pre-existing profile's `history.notable_moments` contained the line **"2025: 20th edition continues the tradition — approximately 40 Luxembourg riders travel annually with ACC Contern"** — this is directly contradicted by the already-established "defunct" eligibility status and by the confirmed 2019 last-edition finding. No source found supports a 2025 edition; this reads as a fabrication. **Removed and replaced** with accurate 2019/2020-21/2022 entries.

## UCI affiliation claims — TRUE HISTORICALLY, but present-tense framing was misleading for a defunct race
Flagged claims: tagline ("...UCI Gran Fondo World Series qualifier since 2012"), final_verdict.one_liner, final_verdict.should_you_race ("Ride this if you want a UCI Gran Fondo World Series qualifier...").

- The underlying facts are true: the event was a genuine UCI Gran Fondo World Series qualifier from 2012 to its final 2019 edition, and it hosted the UCI Gran Fondo World Championships in 2013.
- **Nuance caught this pass**: the profile's origin_story and notable_moments also claimed the event "hosted the UCI Gran Fondo World Championships in ... 2022" — technically the roads were used, but per granfondodailynews.com, Trento's Sept 2022 hosting of the UCI Worlds was **organized separately by the Trento/Monte Bondone/Valle dei Laghi Tourism Board**, explicitly **not** by La Leggendaria Charly Gaul (which had already folded that February). Direct quote from the organizing committee via granfondodailynews: "Trento still plans to host the 2022 UCI Gran Fondo World Championships on the La Leggendaria Charly Gaul gran fondo course...but the event will now be organised by the Trento, Monte Bondone and Valle dei Laghi Tourism Board rather than La Leggendaria Charly Gaul." Conflating the two implied the granfondo itself continued into 2022, which is false.
- **Corrected** (present-tense → historically-bounded, eddy-merckx precedent):
  - `tagline`: "...UCI Gran Fondo World Series qualifier since 2012" → "...A UCI Gran Fondo World Series qualifier from 2012 until its final edition in 2019."
  - `final_verdict.one_liner`: added "...while it ran through 2019" to stop it reading as a current claim.
  - `final_verdict.should_you_race`: fully rewritten to an explicit "No — this race hasn't run since 2019..." framing (matches the precedent set for granfondo-eddy-merckx in flight 1 of this debt sweep), redirecting readers to the current UCI GFWS calendar rather than implying they can register for this event.
  - `history.origin_story` (final sentence) and `history.notable_moments`: rewritten to correctly separate "final granfondo edition: 2019" from "Trento separately hosted UCI Worlds in Sept 2022 under different management."
  - `history.reputation`: tense corrected to past ("was established," "was known for").
- **Not touched** (per brief, biased_opinion/course_description keep existing voice): `biased_opinion.*` fields still read in present tense throughout (e.g., "2,000-5,000 riders retrace his path") — flagging this for a human call if a fuller past-tense pass is ever wanted, but out of this pass's surgical scope.

## Citations
- Added: https://granfondodailynews.com/2022/02/17/a-legend-calls-it-quits-uci-leggenaria-charly-gaul-gran-fondo-cancelled-for-good/ (8th citation; already had 7, well above the 3-minimum).

## Sol adversarial review (2026-07-24, gpt-5.6-sol, read-only, foreground)
The "2025 fabrication" catch and the 2022-Worlds nuance were both found independently during direct WebFetch research, before the sol pass ran. Sol caught a real follow-on issue I'd missed: leaving `biased_opinion` and `vitals.registration` untouched (per the brief's "don't rewrite wholesale" instruction) meant they still directly repeated the exact false claim I'd already corrected in `history` — not just stale present tense, an active internal contradiction. Applied:
- `vitals.registration`: was giving live sign-up instructions for a race that hasn't run since 2019 ("Online via endu.net. UCI Gran Fondo World Series qualifier..."). Corrected to lead with "Discontinued — no longer accepting registrations," historical detail follows.
- `biased_opinion.summary`: "the field reflects this — La Leggendaria hosted the actual UCI Worlds in 2013 and 2022" repeated the exact 2013/2022 conflation already disproven in `history` (2022 Worlds were organized separately by the Trento tourism board after the granfondo had folded). Corrected to attribute only 2013 to the granfondo itself and cross-reference the history section for the 2022 distinction.
- `final_verdict` was already rewritten in the initial pass; `biased_opinion.bottom_line` still said "If you are targeting UCI World Championship qualification in Italy, this is your event" as a live recommendation. Corrected to past-tense framing redirecting to the current UCI GFWS calendar, consistent with the eddy-merckx precedent already applied to should_you_race.
No findings rejected. `biased_opinion.summary`'s scenic narrative ("Seventy years later, 2,000-5,000 riders retrace his path...") was left untouched — sol didn't flag it and it's arguably voice/scene-setting rather than a factual currency claim, consistent with the brief's "don't rewrite wholesale" instruction.

## JSON changes made
- `tagline`, `final_verdict.one_liner`, `final_verdict.should_you_race`: corrected to historically-bounded framing (see above)
- `history.origin_story`: final sentence corrected to accurately separate the 2019 final edition from the separately-organized 2022 UCI Worlds
- `history.notable_moments`: removed fabricated "2025: 20th edition" bullet, added accurate 2019/2020-21/2022 bullets
- `history.reputation`: tense corrected to past
- `eligibility.verified`: 2026-07-22 → 2026-07-24; `eligibility.notes` expanded with the 2019-last-edition and 2022-Worlds-separate-organizer findings
- `citations`: added granfondodailynews.com source
- No fondo_rating changes (rubric-lock held); `biased_opinion`/`course_description` left untouched per brief
