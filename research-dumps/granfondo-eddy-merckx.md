# Research Dump: Granfondo Eddy Merckx

Verified 2026-07-24 via live web search (codex/gpt-5.6-sol) + direct curl verification of every URL below.

## Quick Facts
- Race status: DEFUNCT. Last located edition: June 22, 2014, Andenne, Wallonia, Belgium.
- 2014 qualifying course: 152 km (the profile's current 162.5 km/2,644 m figures describe a later/different route configuration than the last verified 2014 edition — see Data Caveat below).
- Organizing body: Golazo (Belgium's major sports-event company).
- Series: UCI World Cycling Tour (UWCT) — the pre-2019 name for what is now the UCI Gran Fondo World Series.

## UCI / World Championship Qualifying Claim — VERIFIED TRUE (historically)
The profile's `final_verdict.should_you_race` states: "Yes if UCI age-group competition and World Championship qualifying matter to your ambitions."

This is accurate for the era in which the race operated:
- Golazo's surviving event page (https://www.golazo.com/event/gran-fondo-eddy-merckx-2/, HTTP 200) documents the Gran Fondo Eddy Merckx as an Andenne-based Golazo event.
- A 2014 UCI World Cycling Tour timing/results PDF is explicitly titled "UCI World Cycling Tour – Gran Fondo Eddy Merckx," dated June 22, 2014, and contains age-category breakdowns with "Q" (qualification) markers. https://crdev.blob.core.windows.net/files/10634.pdf (HTTP 200)
- A contemporaneous cycling-media article on the 2014 UCI World Cycling Tour series confirms the format: the top 25% of finishers in each age/gender category qualified for the UCI Amateur Road World Championships. https://pedalmag.com/uci-announces-2014-world-cycling-tour-amateur-road-world-championships-qualifier-series/ (HTTP 200, requires a full browser-style User-Agent — returns 406 to a bare curl UA, confirmed 200 with a standard browser UA)
- A Spanish-language masters-cycling community post from May 2014 corroborates the qualification mechanism for the UCI Masters World Championship pathway. https://masters.abloque.com/2014/05/20/como-participar-en-el-campeonato-del-mundo-master-uci-2014/ (HTTP 200)

**Important nuance**: "World Championship qualifying" in this historical context means the UCI's *amateur/age-group* World Championships (UWCT era) or Gran Fondo World Championships pathway — not the elite/professional UCI Road World Championships. This is the same shorthand used consistently across every other UCI-affiliated race in this corpus (Matildica, Novi Sad, Tre Valli Varesine, Pomerode all use "World Championship qualifying" to mean the same age-group UCI Gran Fondo Worlds pathway).

**CORRECTION APPLIED (2026-07-24)**: While the underlying UCI-qualifying fact was true historically, the flagged sentence lived in `final_verdict.should_you_race`, phrased in present tense as "Yes if UCI age-group competition and World Championship qualifying matter to your ambitions" — implying a reader could still enter this race and obtain that qualifying today. The race is defunct (no edition since 2014). This is the exact "stale claim, race no longer on the calendar" pattern the debt-sweep brief calls out for in-place correction. It's also inconsistent with this corpus's established house convention for defunct races: a full-corpus scan of every profile with `eligibility.status: "defunct"` shows the dominant pattern is `should_you_race` opening with "No —" and redirecting to a current alternative (examples: axel-merckx-gran-fondo.json, belgrade-gran-fondo.json, cappadocia-gran-fondo.json, tour-of-cambridgeshire.json, uci-gran-fondo-ireland.json — dozens of others). Rewrote `final_verdict.should_you_race` in race-data/granfondo-eddy-merckx.json to open "No —", state the race hasn't run since June 22, 2014, describe what it offered in past tense (UCI World Cycling Tour qualifier, 18 Ardennes climbs, UCI age-group/World Championship qualifying), and redirect readers to the current UCI Gran Fondo World Series calendar — matching the house convention and the surrounding register (short, direct, no editorializing beyond what the corpus already does for defunct races). `biased_opinion` and `course_description` were NOT touched, per the debt-sweep brief's explicit prohibition on wholesale prose rewrites — only the one flagged, stale field was corrected. Note: `granfondo-campagnolo-roma.json` (also defunct, same batch) has the identical present-tense "Yes if" pattern in its own `should_you_race`, but that specific text was not flagged by the audit for this batch (its only flagged claim was the unrelated Campagnolo-company-history sentence in `history.origin_story`), so it was left untouched — flagging here for a future pass.

## Data Caveat (flag only, not corrected — outside this batch's flagged-claim scope)
The current JSON vitals (162.5 km, 2,644 m, "Third or fourth Sunday of June annually," Triple Mur de Monty signature climb) describe a route configuration not confirmed in the 2014 UCI PDF (which lists 152 km). It's plausible the course grew/changed across editions between the 2012 Blegny-based edition and the final 2014 Andenne edition, but no single-source confirmation of the 162.5 km/2,644 m figures was found in this research pass. This is a pre-existing vitals-precision question on a defunct race, not one of the batch's flagged UCI-affiliation claims — flagging for a future pass rather than correcting now, since eligibility.status is already correctly set to "defunct" and the race is not being marketed as currently running.

## Eligibility
- Status: defunct. Matches existing eligibility block in race-data/granfondo-eddy-merckx.json (verified 2026-07-22, source golazo.com). No later edition found after June 2014 in this research pass — consistent with the existing eligibility note.

## Citations (curl-verified 2026-07-24)
1. Golazo official event page — https://www.golazo.com/event/gran-fondo-eddy-merckx-2/ (HTTP 200)
2. UCI World Cycling Tour 2014 timing/results PDF — https://crdev.blob.core.windows.net/files/10634.pdf (HTTP 200)
3. Pedal Magazine — UCI announces 2014 World Cycling Tour amateur road World Championships qualifier series — https://pedalmag.com/uci-announces-2014-world-cycling-tour-amateur-road-world-championships-qualifier-series/ (HTTP 200 with browser UA)
4. Masters cycling community — UCI 2014 Masters World Championship qualification explainer — https://masters.abloque.com/2014/05/20/como-participar-en-el-campeonato-del-mundo-master-uci-2014/ (HTTP 200)

Note: existing JSON citations already include 10 entries (well above the 3-minimum gate); this dump adds the specific UCI-qualification evidence that was previously missing, it does not replace the existing citations array.
