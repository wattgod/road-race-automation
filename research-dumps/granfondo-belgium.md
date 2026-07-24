# Research Dump: Granfondo Belgium (UCI Gran Fondo Belgium, Lacs de l'Eau d'Heure)

Verified 2026-07-24 via codex gpt-5.6-sol foreground research + direct curl verification, as part of the Roadie Labs debt-sweep (batch 4).

## Quick Facts
- **Location**: Les Lacs de l'Eau d'Heure, Froidchapelle, Hainaut, Belgium
- **2026 edition**: moved from April 19 to March 29, 2026, with a redesigned car-free course — matches what the profile's own `eligibility.notes` already correctly documented.
- **Vitals**: 138 km / 2,100 m confirmed directly from the official race page — curl-verified text: "RACE DISTANCE : 138KM - 2100M D+" (https://www.granfondobelgium.com/en/epreuves). Profile's 137.9 km / 2,100 m is effectively identical (rounding); no fix needed.

## UCI Gran Fondo World Series status: CURRENT for 2026
Confirmed via the UCI's own calendar-change announcement:

> "Granfondo Belgium moves to 29 March with a new course layout... Riders will begin with a 33 km start loop... followed by three or four local laps of 22 km..." — curl-verified text from https://ucigranfondoworldseries.com/en/calendar-update-two-date-changes-and-one-new-event-added-to-the-2026-uci-gran-fondo-world-series/

- UCI GFWS calendar: https://ucigranfondoworldseries.com/en/calendar/
- UCI calendar-update announcement (curl-verified, quoted above): https://ucigranfondoworldseries.com/en/calendar-update-two-date-changes-and-one-new-event-added-to-the-2026-uci-gran-fondo-world-series/
- Official race page (curl-verified, vitals quoted above): https://www.granfondobelgium.com/en/epreuves

## Claim verification

| Claim | Verdict | Evidence |
|---|---|---|
| tagline: "car-free UCI qualifier that bites back" | TRUE | Official page confirms 100% closed-to-traffic course; UCI GFWS status confirmed current. |
| biased_opinion.verdict: "Revamped UCI sleeper hit" | TRUE (factual "revamped UCI" component; "sleeper hit" is editorial opinion) | UCI's own calendar-update announcement confirms the course redesign. |
| final_verdict.should_you_race: "Yes if chasing UCI worlds quals with Ardennes appeal..." | TRUE as evergreen recommendation copy | The March 29, 2026 edition has already run (today is 2026-07-24) and no 2027 date is confirmed yet, but this text is generic forward-looking advice (no specific date claimed) rather than a false current-availability claim — left unchanged. The `eligibility.notes` field (already on file, unchanged) carries the specific "no 2027 date published yet" caveat for anyone checking dates. |

## Fix applied
No prose changes — all flagged claims verified TRUE, and the profile's existing `eligibility` block already correctly documented the March 29 date move and the "no 2027 date" caveat. Added a citation for the UCI calendar-update announcement to strengthen the evidence base for the qualifier-status and course-redesign claims.

## Eligibility
(unchanged from what was already on file, verified date refreshed)
- status: active
- verified: 2026-07-24
- source: https://www.granfondobelgium.com/en
- notes: unchanged — "Sport & Tourism Promotion's UCI Gran Fondo World Series event at Lacs de l'Eau d'Heure. 2026 event was moved from April 19 to March 29 with a redesigned course; official 2026 results posted. No 2027 date published yet as of Jul 2026."
