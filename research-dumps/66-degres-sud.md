# 66 Degrés Sud — Research Dump

Debt-sweep verification pass, 2026-07-24. All URLs curl-verified live (HTTP 200) on 2026-07-24 unless noted.

## Eligibility
- **Status: active.** Canet-en-Roussillon, France. 6th edition ("La Cyclo Edition #6").
- Source: https://ucigranfondoworldseries.com/fr/66-degres-sud-2/ (curl-verified live, page title "66 Degrés Sud - UCI Gran Fondo World Series").

## Vitals correction — date_specific was WRONG, now fixed
- Pre-existing eligibility.notes (from a prior wave) already flagged: "2026 cyclo runs Apr 25 (6th ed.), not Apr 18 as our date field says" — this pass confirmed and resolved it.
- **Independent confirmation #1**: UCI GFWS calendar (https://ucigranfondoworldseries.com/en/calendar/, curl-verified live) lists "66 Degrés Sud" under country FRA, city Canet-en-Roussillon, with event-date text "Thursday 23 Apr 2026 - 25 Apr 2026."
- **Independent confirmation #2**: official site https://66-degres-sud.fr/accueil/ (curl-verified live) contains the text "La cyclo Edition #6 - Du 23 au 25 Avril 2026 au départ de Canet en Roussillon !" ("6th edition — 23 to 25 April 2026, starting from Canet-en-Roussillon"). A second banner on the same page shows a slightly looser "Rendez-vous du 23 au 26 Avril 2026" (23-26), likely referring to the full multi-day festival window including setup/departure days; the more specific "La cyclo Edition #6" banner (23-25) matches the UCI calendar exactly and is treated as authoritative for the race dates.
- **Fixed**: `vitals.date_specific` changed from "2026: April 18" to "2026: April 23-25 (La Cyclo, 6th edition; road races Saturday April 25)". Thursday 23 Apr appears to be the separate time trial (per pre-existing `logistics.transport` field: "time trial on Thursday"); the Gran Fondo road race itself runs Saturday 25 Apr, consistent with the pre-existing eligibility note and francecourses.fr.
- Sol's review flagged the same correction independently and additionally suggested clarifying that Thursday was the TT and Saturday the road race — incorporated into the corrected date_specific and eligibility.notes.

## UCI affiliation claim — CONFIRMED TRUE
- Flagged claims: tagline "A UCI Gran Fondo World Series event through the Pyrenees-Orientales wine country and mountain terrain"; final_verdict.one_liner; final_verdict.should_you_race ("The event's UCI World Series sanctioning...").
- Confirmed live and current via the UCI GFWS calendar entry above (Canet-en-Roussillon, Apr 23-25 2026) and the dedicated UCI GFWS event page (ucigranfondoworldseries.com/fr/66-degres-sud-2/, page title confirms "UCI Gran Fondo World Series"). No correction needed.

## Citations (existing, spot-checked live 2026-07-24)
- https://ucigranfondoworldseries.com/fr/66-degres-sud-2/ — 200
- https://66-degres-sud.fr — 200
- https://66-degres-sud.fr/accueil/ — 200 (source for date correction)
- https://www.finishers.com/course/66-sud-la-cyclo — 200
- https://followmysport.com/courses/66-degres-sud/ — 429 (rate-limited, not dead — retried live in browser)
- https://fr.milesrepublic.com/event/66-degres-sud-la-cyclo-12529 — 200

## Sol adversarial review
GPT-5.6-sol (read-only, foreground) reviewed this race alongside the rest of the batch. Verdict: CORRECT — matched my independent finding exactly (date_specific wrong, should be Apr 23-25; UCI claim otherwise true). Applied.

## JSON changes made
- `vitals.date_specific`: "2026: April 18" → "2026: April 23-25 (La Cyclo, 6th edition; road races Saturday April 25)"
- `eligibility.verified`: 2026-07-23 → 2026-07-24
- `eligibility.source`: francecourses.fr → ucigranfondoworldseries.com/fr/66-degres-sud-2/ (stronger primary source for the correction)
- `eligibility.notes`: rewritten to document the correction and its evidence
- No fondo_rating changes
