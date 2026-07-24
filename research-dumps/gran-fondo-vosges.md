# Research Dump: Gran Fondo Vosges (UCI Granfondo, La Bresse-Hohneck)

Verified 2026-07-24 via codex gpt-5.6-sol foreground research + direct curl verification, as part of the Roadie Labs debt-sweep (batch 4).

## Quick Facts
- **Location**: La Bresse-Hohneck ski station, Vosges, France
- **2026 edition**: May 17, 2026 (completed) — 9th edition overall, 6th consecutive year as a UCI GFWS qualifier (since 2021).
- **Organizer**: Cycling Classics (cyclingclassics.fr)

## UCI Gran Fondo World Series status: CURRENT for 2026
Confirmed on the official UCI GFWS calendar. UCI's own event page explicitly calls it the series' longest race:

> "Starting from the La Bresse-Hohneck station, this **longest Granfondo in the UCI Gran Fondo World Series** takes you over a number of often short but steep climbs..." — curl-verified text from https://ucigranfondoworldseries.com/en/granfondo-vosges/

## Vitals: CORRECTED
The profile's vitals (174.9 km / 2,894 m) are stale. Curl-verified directly from the organizer's own current course page:

> "UCI GRANFONDO 17/05/2026 Start at 7.30am 177,5 kilometers 3087 meters of elevation gain 3 feed stations" — https://granfondovosges.com/en/uci-granfondo/ (curl-verified 200)

The UCI's own event page still shows the older, rounder figures (175 km / 2,894 m) — the organizer's page is more current/precise for the actual completed 2026 edition and is used as the authoritative figure.

Corrected: `distance_km` 174.9 → 177.5, `distance_mi` 108.7 → 110.3 (177.5 / 1.60934), `elevation_m` 2894 → 3087, `elevation_ft` 9495.0 → 10131.0 (3087 × 3.28084). Same correction applied to the matching `route_options[0]` (Granfondo) entry.

## Claim verification

| Claim | Verdict | Evidence |
|---|---|---|
| tagline: "Longest UCI Gran Fondo qualifier in the forested Vosges mountains" | **TRUE** | UCI's own event page uses the exact "longest Granfondo in the UCI Gran Fondo World Series" framing (quoted above). No fix needed. |
| final_verdict.one_liner: "T2: Premier UCI Gran Fondo qualifier..." | TRUE for the 2026 edition | UCI GFWS status and "longest" superlative both confirmed above. "Premier" is editorial framing, not a specific factual claim requiring a citation. |

## Fix applied
- `vitals.distance_km`: 174.9 → 177.5
- `vitals.distance_mi`: 108.7 → 110.3
- `vitals.elevation_m`: 2894 → 3087
- `vitals.elevation_ft`: 9495.0 → 10131.0
- `route_options[0]` (Granfondo) distance/elevation fields updated to match.
- Added citation for the organizer's UCI Granfondo course page (source of corrected vitals).

## Eligibility
- status: active
- verified: 2026-07-24
- source: https://granfondovosges.com/en/uci-granfondo/
- notes: "2026 (9th edition, 6th consecutive UCI GFWS year) completed May 17, 2026. No 2027 date published yet as of Jul 2026."

## Sol adversarial review pass (2026-07-24)
- **Applied**: `elevation_ft` arithmetic error — 3087m × 3.28084 = 10,127.95 ft, correctly rounds to 10,128 ft, not the 10,131 I originally wrote. Fixed in both `vitals.elevation_ft` and `route_options[0].elevation_ft`.
- **Applied**: `logistics.official_site` was empty; populated with the verified organizer course page URL.
- **Rejected**: sol flagged `history.founded: 2021` as contradicting `origin_story`'s "First edition ~2018." On inspection this is not a contradiction I introduced or verified either way — `founded` plausibly tracks "first year as a UCI qualifier" (2021, matching "6th consecutive year 2026" = 2021+5) while `origin_story` separately tracks the raw cyclosportif's first edition (~2018, matching "9th edition 2026" = 2026-8). This is pre-existing profile content, not part of my batch's flagged claims, and I have no independent verification of which interpretation (or whether either) is correct — left unchanged and flagging here for a future pass rather than guessing.

