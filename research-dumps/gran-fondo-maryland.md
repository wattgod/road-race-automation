# Research Dump: Gran Fondo Maryland

Verified 2026-07-24 via codex gpt-5.6-sol foreground research + direct curl verification, as part of the Roadie Labs debt-sweep (batch 4).

## Quick Facts
- **Location**: Frederick, Maryland, USA
- **2026 edition**: September 20, 2026 — confirmed active on the official site.
- **Vitals**: 87 mi / 140 km, 8,500 ft / 2,591 m — matches the profile, no change needed.
- **Series**: Gran Fondo National Series (GFNS) — NOT a UCI event. Hosts the USA Cycling Gran Fondo National Championship.
- Official site (curl-verified 200): https://www.granfondonationalseries.com/gran-fondo-maryland

## Founding year: CORRECTED 2014 → 2012
The profile's `history.founded: 2014` and origin_story "Born in 2014" are **FALSE**. Curl-verified directly from the GFNS official blog:

> "Gran Fondo Maryland, first held in 2012, was the founding event of the Gran Fondo National Series and the original Gran Fondo National Championship location. I'm proud to bring the Championship back to its place of inception." — Reuben Kline, Gran Fondo National Series Founder and Director

Source (curl-verified 200, text extracted and quoted above): https://www.granfondonationalseries.com/blog/2022/9/14/gran-fondo-maryland-announced-as-usa-cycling-gran-fondo-national-championship-for-2023

This same page states the GFNS "has been organizing the Gran Fondo National Championship since 2012," directly tying to the 2012 founding of the Maryland race — it was the founding event of the whole series, not merely "part of" a series that predates it.

## Claim verification

| Claim | Verdict | Evidence |
|---|---|---|
| history.origin_story: "Born in 2014 as part of the National Series quest..." | **FALSE** — should be 2012, and it was the *founding* event of GFNS, not a later addition | GFNS blog quote above |
| "part of the Gran Fondo National Series" | TRUE | Confirmed the founding/anchor event of GFNS; still the series' final stop in 2026. |
| 2026 edition, September 20 | TRUE | Official 2026 event page. |

## Fix applied
- `history.founded`: 2014 → 2012
- `history.origin_story`: rewritten to correct the year and reflect that Maryland was the *founding* event of the Gran Fondo National Series (not merely "part of" a pre-existing series), matching surrounding voice/register.
- Added citation for the GFNS founding-year blog post.

## Eligibility
- status: active
- verified: 2026-07-24
- source: https://www.granfondonationalseries.com/gran-fondo-maryland
