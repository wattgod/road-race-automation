# Cheaha Challenge Gran Fondo — Research Dump

Debt-sweep verification pass, 2026-07-24. All URLs curl-verified live (HTTP 200) on 2026-07-24 unless noted.

## Eligibility
- **Status: active.** Jacksonville, Alabama. 2026 edition scheduled May 16-17.
- Source: https://www.cheahachallenge.com/ (curl-verified live).

## UCI affiliation claim — CONFIRMED TRUE
- Flagged claim: final_verdict.should_you_race, "if you're vert-hungry with UCI qualifier ambitions..."
- Direct verification #1: the official Cheaha Challenge site (cheahachallenge.com, curl-verified live) states the fondo runs "Saturday May 16, 2026 to Sunday May 17, 2026" and lists race categories including "ULTRA, UCI Qualifier - Please Select Age Group," "100 Mile Challenge - Non UCI," and other distances — confirming at least one official category is a literal UCI qualifier, alongside explicitly non-UCI categories at other distances.
- Direct verification #2: a dedicated official page, https://www.cheahachallenge.com/Race/CheahaChallengeGranFondo/Page/ucigfws (curl-verified live, page title "Cheaha Challenge Gran Fondo: UCI Gran Fondo World Series Qualifying Info"), spells out the UCI GFWS qualifying rules — added as a citation this pass.
- Direct verification #3: the UCI GFWS calendar itself (https://ucigranfondoworldseries.com/en/calendar/, curl-verified live) lists "Cheaha Challenge Granfondo," Jacksonville, Alabama, dated "Saturday 16 May 2026 - 17 May 2026" — matches vitals.date_specific exactly.
- Conclusion: claim is TRUE. should_you_race's general reference to "UCI qualifier ambitions" does not claim every distance/category is UCI-qualifying (it isn't — the 126-mile Ultra and several shorter distances are explicitly non-UCI per the official category list), so no correction needed; the claim as written is accurate at the event level.

## Citations (existing, spot-checked live 2026-07-24)
- https://ucigranfondoworldseries.com/en/cheaha-challenge-granfondo/ — 200
- https://www.cheahachallenge.com — 200
- https://northsouth.live/event/cheaha-challenge-gran-fondo — 200
- https://www.cheahachallenge.com/Race/CheahaChallengeGranFondo/Page/ucigfws — 200 (new, added this pass)

## Sol adversarial review
GPT-5.6-sol (read-only, foreground) reviewed this race. Verdict: CONFIRM, with a precision note that the 126-mile "Ultra" itself is not the UCI-qualifying category (the separate 100-mile age-group category is) — this is consistent with the official site's own category list and does not require a text correction since should_you_race speaks to the event overall, not the Ultra distance specifically.

## JSON changes made
- `eligibility.verified`: 2026-07-20 → 2026-07-24
- `eligibility.notes`: added (was previously absent), documents the UCI qualifier verification
- Added one citation (official UCI GFWS qualifying-info page)
- No claim text changes (flagged claim verified TRUE)
- No fondo_rating changes
