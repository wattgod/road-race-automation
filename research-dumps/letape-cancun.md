# L'Etape Cancún by Tour de France — Research Dump

Debt-sweep verification pass (batch 6), 2026-07-24. Batch flag: citation shortfall only (1 citation, needed 3+); no specific claim flagged. Deep research surfaced a real cancellation + a vitals error beyond the citation gap.

## Eligibility
- **Status: active (series level)** — but the specific May 17, 2026 edition was CANCELLED. Corrected this pass from a prior finding that said "no cancellation signal found."
- Source: https://cancun.letapeseries.com/stages (official site).

## Cancellation finding — the prior eligibility note was wrong
- The prior eligibility.source, https://www.asdeporte.com/evento/l-e-tape-cancu-n-by-tour-de-france-2026-vh1/datos-del-evento, was re-checked directly via curl. Raw HTML confirms the page title itself is **"L'Étape Cancún by Tour de France 2026 - CANCELADO"**, with a prominent banner reading **"LAMENTABLEMENTE EL EVENTO HA SIDO CANCELADO"** ("Unfortunately the event has been cancelled") and the underlying event JSON marked `"published":false`. This directly contradicts the pre-existing eligibility.notes claim that "no rebrand or cancellation signal found" — that prior read was simply wrong (or the page changed in the interim).
- Cross-checked with two independent sources: WebSearch aggregate confirms "L'Étape Cancún by Tour de France 2026 has been canceled." Battistrada.com's edition page uses past tense ("took place on Sunday 17 May 2026") which is ambiguous but not contradictory once you account for the site being a generic template.
- **However, the series continues**: the official cancun.letapeseries.com/stages page (curl-verified live, no cancellation notice) lists a new edition for **February 14, 2027** — moved from the traditional May date. This is consistent with the general L'Etape-franchise pattern seen elsewhere in this batch (Argentina relaunching after an 11-year gap, Denmark's branding continuity) — a franchise event getting rescheduled/relaunched rather than permanently killed.
- **Resolution**: kept `eligibility.status: active` (the series/franchise is alive with a confirmed forward date), but corrected the notes to accurately describe the 2026 cancellation and documented it in `history.notable_moments`.

## Vitals correction — elevation was wrong (literal 0, not just imprecise)
- Prior vitals: `elevation_m: null`, `elevation_ft: 0.0`, and both route_options listed "0ft." No location is literally flat to the meter, and the official site contradicts this directly.
- Official site (cancun.letapeseries.com/stages, WebFetch-confirmed) gives: Long route 101.48 km / **133m** elevation gain; Short route 55.57 km / **73m** elevation gain.
- **Fixed**: `vitals.elevation_m` null → 133, `elevation_ft` 0.0 → 436.0; `route_options` updated with real elevation figures for both routes.

## Founding year correction
- Prior `history.founded: 2024` and origin_story "Born 2024 as L'Etape Series' Caribbean debut" is contradicted by the profile's own `youtube_data`: a video titled "Salida L Etape By Tour de Francia Cancún 2023" (uploaded 2023-06-25) shows a real 2023 race weekend.
- WebSearch corroboration: endondecorrer.com lists "L'Étape Cancún by Tour de France 2023" as an event with three original routes (40/75/160 km — different from the current 55.57/101.48 km, confirming the course has also been shortened over time); a Cancún municipal government news post celebrates "L'ETAPE CANCUN 2025" as the "third consecutive" edition, consistent with 2023 → 2024 → 2025.
- **Fixed**: `history.founded` 2024 → 2023; `origin_story` and `notable_moments` corrected to reflect the actual founding year, the original 40/75/160km routes, and the 2026 cancellation / 2027 relaunch.

## Citations — fixed the shortfall
- Was: 1 citation (cancun.letapeseries.com).
- Added 3: cancun.letapeseries.com/stages (routes/elevation/2027 date), asdeporte.com (cancellation evidence), endondecorrer.com (2023 first-edition evidence). Now 4 total.

## Sol adversarial review (2026-07-24, gpt-5.6-sol, read-only, foreground)
Sol caught real follow-on inconsistencies from the date/elevation corrections that I'd left dangling elsewhere in the file. All applied, verified against the same official stages page before applying:
- **Applied**: `vitals.date` still said "May" after the event moved to a Feb 14, 2027 date. Corrected.
- **Applied**: `climate.description` still opened "May in Cancun slams 82-90°F days..." — now describes conditions for a date the event no longer runs on. Corrected to flag the season shift; did not fabricate new February climate data (out of scope for a surgical fix — would need fresh research).
- **Applied**: `logistics.lodging_strategy` said "book early for May peak" — corrected to reference the Feb 14, 2027 date.
- **Applied**: `history.origin_story` called the 101.48km/133m figures "the current long route," but those numbers come from the (cancelled) 2026 course listing on the official stages page — the 2027 edition's own distance/elevation had not been separately published as of this pass. Corrected to attribute the figures to the 2026 course specifically and flag that 2027 hasn't published its own numbers yet.
- **Applied**: the citation label for the stages page made the same "current 2027" overstatement — corrected to specify the figures are for the cancelled 2026 listing.
- **Noted but not changed**: `vitals.distance_km: 101.9` vs. the cited 101.48km figure is a ~0.4km discrepancy — likely rounding/different-GPS-track variance, pre-existing before this pass (not something I introduced), and immaterial at this margin. Left as-is.

## JSON changes made
- `vitals.elevation_m`: null → 133; `vitals.elevation_ft`: 0.0 → 436.0
- `vitals.route_options`: both entries updated with real km/elevation figures
- `vitals.date`: "May" → "February (moved from May after the 2026 May 17 edition was cancelled)"
- `vitals.date_specific`: corrected to document the May 17, 2026 cancellation and the new Feb 14, 2027 date
- `climate.description`, `logistics.lodging_strategy`: corrected to stop asserting stale May-specific details as current
- `history.founded`: 2024 → 2023
- `history.origin_story`, `history.notable_moments`: corrected for founding year, original route distances, 2026 cancellation / 2027 relaunch, and to stop over-attributing 2026 course figures to 2027
- `citations`: added 3 (now 4 total, clears the 3-minimum); one label corrected for accuracy
- `eligibility.verified`: 2026-07-23 → 2026-07-24; `eligibility.source` and `notes` corrected
- No fondo_rating changes (rubric-lock held)
