# Research Dump: GFNY Uppsala

Research pass: 2026-07-24, codex gpt-5.6-sol, real web search.

## Status: DEFUNCT/INACTIVE
- Absent from GFNY's current worldwide calendar and cycling Race Finder (which assigns Aug 23, 2026 to GFNY Orcieres, not Uppsala). `uppsala.gfny.com` still resolves but content is stale (references 2024 finisher medals, 2025 NYC championship); registration page has no ticket/date/form. Results index shows only 2023 and 2024.
- Source: https://uppsala.gfny.com/results/?lang=en (curl-verified 200), https://gfny.com/race-finder/?fwp_race_finder_event_type=cycling (curl-verified 200), https://uppsala.gfny.com/register/?lang=en

## Most recent confirmed edition: August 24, 2024 (2nd edition, GFNY European Championship)
- Long course: 133.5km / 494m climbing (GFNY post-race report; course page rounds to 134km/495m). Medium course: 79km.
- Surface: mixed, NOT fully paved — long course has 6 gravel sectors totaling 38km (~28% of route); medium has 3 gravel sectors totaling 19km (~24%). Hard-packed, ridden on road or gravel bikes.
- Route: start/finish at Ulva Kvarn, rolling Uppsala countryside — lakes, forests, nature preserves, villages, farms. No named/significant climbs; flat-to-gently-rolling, wind as the main difficulty.
- Format: one corralled start (licensed/qualified riders first, then age-group, then medium); chip-timed; long course ranked/competitive with age-group awards, medium timed but non-competitive. Riders must obey normal traffic law unless police direct otherwise (not fully closed roads).
- 2024 cutoff: 09:00 start, course closed 15:30 = 6.5 hours (historically correct for the 2024 edition specifically, not evidence of an active 2026 edition).
- Field size: not defensibly verifiable from public sources — left null rather than invented.
- Source: https://gfny.com/gfny-double-race-weekend-results/, https://uppsala.gfny.com/course/?lang=en, https://uppsala.gfny.com/rules/?lang=en, https://uppsala.gfny.com/wp-content/uploads/sites/68/2024/08/GFNY-Uppsala-Race-Guide-2024.pdf

## History
- Originally announced for July 2022 with a very different proposed course (168km/1,862m from the city ice rink) — that plan was never raced as such.
- First actual edition: August 27, 2023 (~144km, described with unpaved roads).
- 2024 was GFNY's own stated 2nd edition — confirms only 2 actual editions (2023, 2024).
- Source: https://gfny.com/gfny-expands-to-scandinavia-with-gfny-sweden-uppsala/, https://uppsala.gfny.com/the-2023-gfny-uppsala-jersey/, https://gfny.com/gfny-double-race-weekend-results/

## Format verdict (historical)
When active, GFNY Uppsala was a genuine mass-participation, chip-timed GFNY gran fondo with real gravel sectors (common to several GFNY European chapters) — not an MTB race, ultra, travel product, or virtual challenge. `discipline='gran_fondo'` retained (consistent with birkebeinerrittet-road.json precedent of keeping discipline for a mixed-surface event); `terrain.surface` corrected to reflect the real ~24-28% gravel content instead of "Paved roads". Defunct/inactive determination follows the birkebeinerrittet-road.json precedent.
