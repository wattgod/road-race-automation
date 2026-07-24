# Superior Morgul Road Race — Research Dump

Debt-sweep verification pass, 2026-07-24. URLs curl/WebFetch-verified live unless noted.

## Eligibility
- **Status: active.** Existing eligibility block (verified 2026-07-23, source superiorcolorado.gov 2026 event listing) confirmed current — 2026 edition runs May 17, 2026 as part of the Superville Stage Race, organized by Without Limits Productions. No change needed.

## Flagged claim — "state championship" — CORRECTED (was FALSE)
- Flagged text: `final_verdict.should_you_race` — "...well-organized circuit race on closed roads with state championship stakes." Also present, unflagged but same underlying claim: `biased_opinion.strengths` — "Colorado State Road Race Championships designation."
- Verification: fetched the Colorado Bicycle Racing Association (CBRA) official 2026 road race calendar directly (https://www.coloradobicycleracing.org/road, HTTP 200, curl-verified). The calendar explicitly labels only three 2026 CBRA state championship events, each tagged in-page:
  - **Road State Championship** = Boulder Roubaix Road Race, 04/26/2026 (a different event).
  - **TT State Championship** = Superior Time-Trial, 05/16/2026 — part of the same Superville Stage Race weekend as the Morgul Road Race, but a separate discipline/event.
  - **Criterium State Championship** = Gold Rush Omnium — Longmont, 08/23/2026.
  - The Morgul Road Race itself, 05/17/2026, carries **no** championship tag on the official calendar.
- Cross-checked against the organizer's own site (withoutlimits.co/morgul-bismark-cycling-race, WebFetch): no mention of state championship status for the road race.
- Conclusion: the claim that the Morgul Road Race carries "state championship stakes" or a "Colorado State Road Race Championships designation" is **false** as currently constituted. The Colorado state championship attached to this event weekend is the Time Trial (held the day before), not the road race itself.
- **Fix applied**: corrected both the strengths bullet and the should_you_race line in `race-data/superior-morgul-road-race.json` to accurately attribute the state championship to the Superville weekend's TT component rather than the Morgul Road Race, preserving the surrounding voice/register. No other text touched.

## Citations (existing, spot-checked)
- https://www.withoutlimits.co/morgul-bismark-cycling-race — HTTP 200, WebFetch-confirmed live, matches 2026 date and course details.
- https://www.coloradobicycleracing.org/road — HTTP 200, curl-verified (new source used for this pass's verification; not added to citations array since 9 citations already exceed the minimum, but documented here for the record).
- 9 citations total in the existing array — well above the >=3 minimum. No additions made.

## Rubric-lock note
- No fondo_rating dimensions touched. `prestige: 4` with `tier_override_reason: "historic US road race with strong regional prestige"` is about the Coors Classic/Red Zinger/LeMond/Hinault historical lineage, not the (now-corrected) championship claim — no scoring mismatch, no scoring_notes flag needed.

## JSON changes made
- `biased_opinion.strengths[3]`: "Colorado State Road Race Championships designation" → "Anchors the Superville Stage Race weekend — the Colorado TT State Championship runs the day before, though the road race itself carries no championship title"
- `final_verdict.should_you_race`: removed the false "state championship stakes" framing for the road race itself; replaced with an accurate description (TT State Championship runs the day before, as part of the same Superville weekend, not this race). Wording tightened in a self-review pass to match the terse, declarative register used elsewhere in this profile and in GOLD exemplars (flandrien-ride.json, gfny-grand-ballon.json) — first draft was accurate but overhedged ("does carry... which... as part of...").

## Adversarial review note
- The codex `gpt-5.6-sol` review pass for this batch hit the known models_cache crash/endless-retry mode (repeated `failed to renew cache TTL: missing field supports_reasoning_summaries` errors, no verdict produced after several minutes of churn). Per the debt-sweep brief's documented landmine guidance, the run was killed and the adversarial check was performed directly by the executor: re-verified the CBRA calendar finding against the primary source, and self-critiqued the initial JSON edit for voice — found it overhedged relative to GOLD register and tightened it (see JSON changes above). No other issues found.
