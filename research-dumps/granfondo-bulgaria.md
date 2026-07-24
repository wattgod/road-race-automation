# Research Dump: Granfondo Bulgaria

Verified 2026-07-24 via live web search (codex/gpt-5.6-sol) + direct curl verification of every URL below.

## Quick Facts
- Location: Velingrad, Bulgaria (Rhodope Mountains). Lat/lng ~42.017, 23.917.
- Date: June 21, 2026 (completed as of this verification — race has run).
- Course (organizer's live route page, granfondobulgaria.com/en/race/, fetched 2026-07-24): Granfondo 140 km displayed / precise embedded GPX data shows 140.4 km, **1,961 m elevation gain**, 1,337 m max altitude. Mediofondo 70 km displayed / 69.7 km precise, **663 m elevation gain**.
- Course (UCI GFWS event page, rounded/older): Granfondo 140 km / 1,905 m; Mediofondo 70 km / 620 m.
- **CORRECTION APPLIED (2026-07-24)**: The organizer's own live page is the more authoritative and more current source (it's the race's own GPX/course data, not a third-party summary). The prior JSON vitals (elevation_m 1905/Granfondo, 620/Mediofondo) undercounted by a material amount (56 m / 3% on the Granfondo, 43 m / 7% on the Mediofondo) — this is a genuine source discrepancy, not rounding noise. Corrected race-data/granfondo-bulgaria.json: `vitals.elevation_m` 1905→1961, `vitals.elevation_ft` 6250.0→6433.7, `route_options[0].elevation_m` 1905→1961 (ft 6250→6434), `route_options[1].elevation_m` 620→663 (ft 2034→2175). Also updated the matching "1905m" figure in `biased_opinion.summary` to "1961m" for internal consistency. `distance_km` (140.0) was left unchanged — the 0.4 km organizer/UCI difference is immaterial and both round to the same displayed "140 km."
- Field: qualification split "Men under 60, Women under 50" (Granfondo) vs "Men over 60, Women over 50" (Mediofondo) — matches existing route_options in the JSON.

## UCI Gran Fondo World Series Status — VERIFIED TRUE
The tagline/one_liner claim "First-ever UCI Gran Fondo qualifier in Bulgaria's stunning Rhodope Mountains" is confirmed accurate by the UCI's own event page.

- The UCI Gran Fondo World Series event page for Velingrad states the race is happening "for the first time as part of the UCI Gran Fondo World Series" and separately describes it as the "first ever UCI Granfondo in the country" (Bulgaria).
- Direct quote pulled via curl from https://ucigranfondoworldseries.com/en/velingrad/ (verified 200, live page, 2026-07-24):
  > "...first time as part of the UCI Gran Fondo World Series and takes place in the Rhodope..."
  > "...first ever UCI Granfondo in the country. COURSE Granfondo Bulgaria is a challenging r..."
- A post-race UCI results report (also live, 200) confirms the June 21, 2026 edition actually ran: "Borislav Hadzhistoyanov and Bel Levene conquer tough Rhodope Mountains at Granfondo Bulgaria."

This is a genuine, currently-active UCI Gran Fondo World Series qualifying event — not a fabricated or stale claim.

## Eligibility
- Status: active. Confirmed edition ran 2026-06-21 with a UCI post-race report. No cancellation/discontinuation signal found. Matches existing eligibility block in race-data/granfondo-bulgaria.json (verified 2026-07-23, same UCI source URL).

## Citations (curl-verified 2026-07-24, all HTTP 200)
1. Official race page — https://granfondobulgaria.com/en/race/
2. UCI Gran Fondo World Series event page — https://ucigranfondoworldseries.com/en/velingrad/
3. UCI Gran Fondo World Series post-race report — https://ucigranfondoworldseries.com/en/borislav-hadzhistoyanov-and-bel-levene-conquer-tough-rhodope-mountains-at-granfondo-bulgaria/
4. Independent timing/results platform (TrackSport) — https://tracksport.live/en/r/gran-fondo

Note: ucigranfondoworldseries.com does not resolve via this sandbox's default DNS (curl reports "Could not resolve host"); it resolves fine via `dig` (34.128.161.244) and `curl --resolve`. All ucigranfondoworldseries.com URLs above were confirmed HTTP 200 using `curl --resolve host:443:34.128.161.244`. This is a sandbox networking quirk, not a dead-domain signal.
