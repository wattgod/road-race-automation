# Research Dump: Granfondo Novi Sad

Verified 2026-07-24 via live web search (codex/gpt-5.6-sol) + direct curl verification of every URL below.

## Quick Facts
- Location: Novi Sad, Serbia, through Fruška Gora National Park.
- Date: June 7, 2026 (third edition, completed as of this verification).
- Course: organizer-published figures are 100 km / 1,500 m gain (Granfondo) and 77 km / 1,200 m gain (Mediofondo) — these match the existing JSON vitals exactly.
- Data conflict noted for the record: the UCI event page lists 110 km/1,900 m and 70 km/1,300 m, while the race organizer, the City of Novi Sad, and Battistrada all give 100 km/1,500 m and 77 km/1,200 m. **Confirmed the conflict runs deeper than just the event page**: the UCI's own 2026 post-race results report also uses 110 km ("In the 110 km granfondo, Russia's Aidar Zakarin proved the strongest rider of the day..." — direct quote pulled via curl, 2026-07-24) — so the UCI side of the discrepancy is consistent across both its event page and its results reporting, not a one-off typo. The organizer figures (already in the JSON, 100 km/1,500 m) remain the values used, matching the organizer's own site, the City of Novi Sad's municipal report, and Battistrada's independent listing (3-of-4 sources vs. UCI's 2-of-2 pages) — no JSON change made, but flagging that this is a real, persistent two-source-family conflict, not a single stale page.

## UCI Gran Fondo World Series Status — VERIFIED TRUE
The tagline and one_liner ("UCI Gran Fondo World Series through Fruška Gora National Park") are confirmed accurate.

- Live UCI Gran Fondo World Series event page for Novi Sad: https://ucigranfondoworldseries.com/en/novisad/ (HTTP 200 via curl --resolve). Page text confirms "World Series" and "2024" (the race's first year in the Series) appear repeatedly, consistent with the race having joined the World Series in 2024 and running its third edition in 2026.
- A same-day UCI GFWS results report confirms the 2026 third edition actually ran: "Zakarin and Simenc Take Victories at Gran Fondo Novi Sad." https://ucigranfondoworldseries.com/en/zakarin-and-simenc-take-victories-at-gran-fondo-novi-sad/ (HTTP 200)
- Independently corroborated by Battistrada's 2026 listing (https://battistrada.com/en/cycling-calendar/edition/uci-granfondo-novi-sad-2026/51591/, HTTP 200) and the City of Novi Sad's own event-day report, which frames it as the "3rd international cycling race Gran Fondo Novi Sad" opened by the mayor (https://novisad.rs/lat/gradonacelnik-micin-otvorio-3-medunarodnu-biciklisticku-trku-gran-fondo-novi-sad, HTTP 200).

## Eligibility
- Status: active. Matches existing eligibility block (verified 2026-07-20, source granfondons.com/race/). Reconfirmed live via the UCI GFWS event page and the third-edition results report.

## Citations (curl-verified 2026-07-24)
1. Official race/course page — https://granfondons.com/race/ (HTTP 200, pre-existing citation, re-verified)
2. UCI Gran Fondo World Series event page — https://ucigranfondoworldseries.com/en/novisad/ (HTTP 200)
3. UCI GFWS 2026 results report — https://ucigranfondoworldseries.com/en/zakarin-and-simenc-take-victories-at-gran-fondo-novi-sad/ (HTTP 200)
4. Battistrada — independent 2026 listing — https://battistrada.com/en/cycling-calendar/edition/uci-granfondo-novi-sad-2026/51591/ (HTTP 200)
5. City of Novi Sad — event-day municipal report — https://novisad.rs/lat/gradonacelnik-micin-otvorio-3-medunarodnu-biciklisticku-trku-gran-fondo-novi-sad (HTTP 200)

Note on sandbox DNS: `ucigranfondoworldseries.com` fails to resolve via this environment's default resolver but resolves via `dig`. All ucigranfondoworldseries.com URLs above were confirmed HTTP 200 using `curl --resolve host:443:<resolved-ip>`.
