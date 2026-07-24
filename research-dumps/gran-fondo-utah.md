# Research Dump: Gran Fondo Utah

Verified 2026-07-24 via codex gpt-5.6-sol foreground research + direct curl verification, as part of the Roadie Labs debt-sweep (batch 4).

## Quick Facts
- **Location**: Payson Memorial Park, Payson, UT, USA
- **2026 edition**: June 13, 2026, completed — 2nd Annual Gran Fondo Utah.
- **Series**: Gran Fondo National Series (GFNS) — NOT UCI. Never appeared on the UCI Gran Fondo World Series calendar (curl-verified: `ucigranfondoworldseries.com/en/calendar/` page source contains no Utah/Payson reference).

## Vitals: CORRECTED
The profile's Gran Route vitals were wrong. Curl-verified directly from two independent official/quasi-official sources:

1. GFNS official event page (curl-verified 200): "Gran Route, 93 miles Medio Route 63 miles Piccolo Route, 35 miles" — https://www.granfondonationalseries.com/gran-fondo-utah
2. Payson City government event page (curl-verified 200): "Gran Route - 93 Miles 6800 FT Elevation Medio Route - 62 Miles 2000 FT Elevation Piccolo Route - 35 Miles 1000 FT Elevation" — https://www.paysonutah.gov/385/Gran-Fondo-Utah

Both sources independently confirm **93 miles / 6,800 ft** for the Gran Route, not the profile's 100 miles / 9,000 ft (2,743 m).

Corrected: `distance_mi` 100.0 → 93.0, `distance_km` 160.9 → 149.7 (93 × 1.60934), `elevation_ft` 9000.0 → 6800.0, `elevation_m` 2743 → 2073 (6800 × 0.3048).

## Claim verification

| Claim | Verdict | Evidence |
|---|---|---|
| tagline: "Nebo Loop in Utah's Gran Fondo National Series" | TRUE | Official page names Nebo Loop as the Gran-course centerpiece and confirms GFNS membership. |
| final_verdict.one_liner: "National Series prestige" | TRUE (GFNS membership fact; "prestige" is editorial) | Official GFNS 2026 calendar lists Utah. |
| history.origin_story: "inaugural event...to expand in Rockies; 2026 is 2nd annual" | TRUE | Official 2026 page calls it "2nd Annual"; GFNS 2025 results/calendar list the inaugural 2025 edition. |

## Fix applied
- `vitals.distance_mi`: 100.0 → 93.0
- `vitals.distance_km`: 160.9 → 149.7
- `vitals.elevation_ft`: 9000.0 → 6800.0
- `vitals.elevation_m`: 2743 → 2073
- Added citation for the Payson City official event page (source of the corrected vitals).

## Eligibility
- status: active
- verified: 2026-07-24
- source: https://www.granfondonationalseries.com/gran-fondo-utah
- notes: "2026 (2nd Annual) edition completed June 13, 2026. granfondoguide.com lists a tentative, explicitly 'Unconfirmed' June 12, 2027 date; GFNS has not yet published an official 2027 confirmation."
