# Istria Granfondo — Research Dump

Debt-sweep verification pass (batch 6), 2026-07-24. All URLs curl/WebFetch-verified live unless noted.

## Eligibility
- **Status: active.** Umag, Croatia. 2026 edition (12th) ran Saturday, April 11, 2026.
- Source: https://www.istria-bike.com/en/events/istria-granfondo (official organizer site, curl-verified 200).

## UCI affiliation claims — CONFIRMED TRUE
Flagged claims: tagline ("UCI qualifier..."), biased_opinion.verdict ("Scenic UCI stunner"), final_verdict.one_liner ("UCI-approved...").

- Confirmed via two independent sources: official site (istria-bike.com) states "officially recognized by the Union Cycliste Internationale (UCI) since 2023"; granfondoguide.com independently corroborates "In 2023, the Istria Gran Fondo became an officially recognized event under the leadership of the UCI-World Cycling Organization."
- Confirmed current/active: the 2026 edition (April 11, 2026) is explicitly described as a qualifier feeding into the UCI Gran Fondo World Series Championship, Aug 26-30, 2026, in Niseko, Japan (WebSearch corroborated by granfondoguide.com race-results dashboard).
- No correction needed — claims are true and current.

## Vitals correction — distance was stale
- **Fixed**: `vitals.distance_km` 112.0 → 105.0, `distance_mi` 69.6 → 65.2. `route_options` Granfondo/Mediofondo entries updated to 105km/80km with a note on year-to-year variance.
- Evidence: the current 2026 official event page (istria-bike.com, curl 200) states plainly: "Istria Gran Fondo: 105 km long route" and "Istria Medio Fondo: 80 km long route" for the April 11, 2026 edition.
- Course distance clearly varies by year — this is not a one-time data error but a genuinely shifting course length across editions: istra.hr's 2024 race recap cites a 112 km Granfondo / 87 km Mediofondo (the numbers our profile had, apparently carried over from a prior-year pass); granfondoguide.com's own listing (a different, seemingly stale page) cites 94/119 km; the current 2026 official site is unambiguous at 105/80 km and is treated as authoritative for the "active" 2026 edition.
- **Elevation NOT changed**: 1,745m could not be independently reconfirmed for the shorter 105km 2026 course (no source found gives a 2026-specific elevation figure). Left as-is, flagged as unverified for the current course length in eligibility.notes.
- Field size ("Up to 700 riders from 15 countries") also not independently reconfirmed for 2026 (istra.hr's 2024 recap cites "over 1,000 riders from 33 countries" — different year, not touched, no strong current-year figure found).

## Citations (existing 3, spot-checked live 2026-07-24)
- https://coloursofistria.com/en/events/istria-granfondo — 200
- https://www.granfondoguide.com/Contents/IndexFull/7145/register-now-for-the-international-uci-istria-gran-fondo — reachable via search, content corroborates UCI status
- https://www.istra.hr/en/destinations/umag/events/26640 — 200, corroborates current 105km distance

Citation count already meets the 3-minimum; no additions made.

## Sol adversarial review (2026-07-24, gpt-5.6-sol, read-only, foreground)
Sol caught two real issues, both applied:
- **Applied**: `tagline` still said "112km" after the vitals distance fix to 105km — a direct internal contradiction. Fixed to "105km."
- **Applied**: `route_options[0]` combined the corrected 2026 distance (105km) with the old, unverified 1745m/5725ft elevation figure as if both were confirmed together for the current course. Reworded to explicitly flag the elevation as not independently reconfirmed for the shorter distance.
No findings rejected.

## JSON changes made
- `vitals.distance_km`: 112.0 → 105.0
- `vitals.distance_mi`: 69.6 → 65.2
- `vitals.route_options`: Granfondo/Mediofondo entries updated to 105km/80km with year-variance note
- `eligibility.verified`: 2026-07-22 → 2026-07-24
- `eligibility.notes`: added, documenting UCI confirmation + distance correction + elevation caveat
- No fondo_rating changes (rubric-lock held)
