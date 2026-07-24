# Research Dump: TotalEnergies Gran Fondo Alberto Contador

Verified 2026-07-24 via codex gpt-5.6-sol foreground research + direct curl verification, as part of the Roadie Labs debt-sweep (batch 4).

## Quick Facts
- **Location**: Oliva, Valencia, Spain
- **2026 edition**: September 19, 2026 (XV edition), confirmed active.
- Official rules page (curl-verified 200): https://granfondoalbertocontador.com/rules/
- UCI competition record: https://www.uci.org/competition-details/2026/CPT/79242

## UCI Gran Fondo World Series status: NOT a GFWS qualifier — FALSE claim found and corrected
This event is **absent from the official UCI Gran Fondo World Series calendar**. Its UCI competition record classifies it as **CPTR — "Cycling For All" — Road**, a general UCI-sanctioned amateur road category, not the Gran Fondo World Series (which uses the UGF classification, see e.g. Loutraki/Villars/Vosges/Belgium in this same batch).

Curl-verified: fetching https://www.uci.org/competition-details/2026/CPT/79242 and grepping the raw HTML returns "CPTR" and "Cycling for All" / "Cycling For All" text, and does **not** return any "World Series" match.

- UCI GFWS calendar (no Contador/Oliva reference): https://ucigranfondoworldseries.com/en/calendar/
- UCI competition record (CPTR classification, curl-verified): https://www.uci.org/competition-details/2026/CPT/79242

This directly contradicts several claims already present in the profile that assert or imply UCI Gran Fondo World Series qualifier status:
- `final_verdict.should_you_race`: "Yes if a UCI qualifier with timed climbing sections suits your competitive instincts." (flagged claim, batch 4)
- `biased_opinion.strengths[1]`: "UCI Gran Fondo World Series qualifier with timed climbing sections for competitive riders"
- `biased_opinion.summary`: "It is a UCI-sanctioned qualifier with real competitive structure..."
- `history.notable_moments`: "UCI Gran Fondo World Series qualifier — age-group finishers qualify for UCI World Championships"

All four describe the same underlying fabrication (GFWS qualifier / Worlds qualification pathway) and were corrected together, since they're one factual error appearing in multiple places, not four separate claims. The event remains a genuine UCI-sanctioned competition (Cycling For All / CPTR) — that fact is preserved, just without the false GFWS/Worlds-qualification framing.

## Vitals: CORRECTED
The profile's route description (146.4 km / 91 mi Gran Fondo + 111 km / 69 mi Medio Fondo) is stale. The official 2026 rules page states:

> "...will consist of a single 138,43km route and will finish in the same place as the start..." — https://granfondoalbertocontador.com/rules/ (curl-verified 200)

No "Medio" or "Medio Fondo" reference appears anywhere on the current rules page or home page — the event has moved to a single 138.43 km route for 2026, dropping the separate Medio Fondo distance. Elevation gain (2,538 m) could not be independently confirmed or refuted from the official site (route/altimetry data is embedded in an inaccessible graphic, consistent with codex's finding) — left unchanged, flagged as unverified for 2026.

Corrected: `vitals.distance_km` 146.4 → 138.43, `vitals.distance_mi` 91.0 → 86.0 (138.43 / 1.60934). `route_options` simplified to reflect the single 138.43 km route for 2026, with a note that the historical Gran/Medio split is no longer current.

## Claim verification

| Claim | Verdict | Evidence |
|---|---|---|
| final_verdict.should_you_race: "Yes if a UCI qualifier with timed climbing sections suits your competitive instincts" | **FALSE** | Not a GFWS qualifier — CPTR classification (see above). Corrected to describe it as UCI-sanctioned Cycling For All, not a World Series qualifier. |

## Fix applied
- `vitals.distance_km`: 146.4 → 138.43
- `vitals.distance_mi`: 91.0 → 86.0
- `vitals.route_options`: simplified to the single 2026 138.43 km route (Medio Fondo removed, noted as historical)
- `final_verdict.should_you_race`: corrected "UCI qualifier" framing to accurate "UCI-sanctioned Cycling For All event, not a UCI Gran Fondo World Series qualifier"
- `biased_opinion.strengths[1]`: corrected same false framing
- `biased_opinion.summary`: "UCI-sanctioned qualifier" → "UCI-sanctioned event" (removed the false "qualifier"/Worlds-pathway implication)
- `history.notable_moments`: corrected the false GFWS/Worlds-qualification bullet
- Added citation for the official 2026 rules page (source of the vitals + UCI classification correction)
- `fondo_rating.scoring_notes`: flagged that `prestige: 4` may be overstated now that GFWS-qualifier status is confirmed false — NOT reassigned, per rubric-lock, flagging for a scoring-review pass.

## Eligibility
- status: active
- verified: 2026-07-24
- source: https://granfondoalbertocontador.com/rules/
- notes: "2026 (XV edition) confirmed for September 19, single 138.43km route (Medio Fondo dropped vs prior years). UCI competition record classifies this as CPTR 'Cycling For All' — Road, NOT a UCI Gran Fondo World Series qualifier; prior profile text implying GFWS/Worlds-qualification status was corrected 2026-07-24."

## Sol adversarial review pass (2026-07-24)
Sol caught real internal contradictions I'd left after the initial fix — the distance/route correction wasn't propagated everywhere it needed to be. Applied:
- `tagline` and `final_verdict.one_liner` still said "146 km" — updated to 138 km.
- `vitals.cutoff_time` still said "Participants may switch from Gran Fondo to Medio Fondo mid-route" — removed, since 2026 has no Medio Fondo.
- `terrain.features` (Fageca/Muro de Tollos entry) still framed the interior loop as "(Gran Fondo only)" distinguishing it from a Medio Fondo — reworded to past-tense framing, single 2026 route.
- `course_description.signature_challenge` computed "remaining 116 km" from the old 146km distance — corrected to ~108 km (138.43 − 30).
- `history.origin_story`: "reaching UCI Gran Fondo World Series status" — corrected to "grown into a UCI-sanctioned competition (Cycling For All Road category)," consistent with the CPTR finding.
- `history.notable_moments`: my inserted CPTR-classification bullet sat right after a pre-existing, unverified 2023 bullet claiming "UCI Gran Fondo World Series calendar" for that year, creating a direct-looking contradiction. Rescoped my bullet to "2026: UCI competition record classifies..." so it makes a dated, current claim rather than an implied blanket-historical one. The 2023 bullet itself was left untouched — I have no independent verification either way for that specific year, and it's outside what I researched (only 2026 UCI classification was checked).
- `route_options`: reworded the elevation caveat so it doesn't assert "unconfirmed" as a new unverified claim — now states the carried-over 2,538m figure hasn't been independently reconfirmed against the shorter 2026 course, without claiming to know it's wrong.

**Rejected**:
- Sol argued the `fondo_rating.scoring_notes` flag ("prestige=4 may be overstated... flagging for a scoring-review pass") should be reverted because it "invites a forbidden future score change." This is incorrect — the debt-sweep brief explicitly instructs: "RUBRIC-LOCK: never edit numeric fondo_rating dimensions... Mismatch → flag in scoring_notes." That's exactly what was done (no numeric value touched). Kept as-is, per the brief's own documented process (see also the flandrien-ride.json precedent for this pattern).
- Sol argued "timed climbing sections" (in `strengths` and `should_you_race`) should be removed as unsubstantiated for 2026. This phrase was pre-existing in the original profile (not introduced by my edit — I only replaced the "UCI qualifier" portion of those sentences) and is corroborated by other pre-existing, unedited content in the same profile (`terrain.features` calls Coll de Rates "the signature timed climb"; `course_description.signature_challenge` describes "a timed section"). It wasn't part of my batch's flagged claims, I have no evidence refuting it, and per the brief I should not rewrite course_description/terrain wholesale. Left unchanged.
