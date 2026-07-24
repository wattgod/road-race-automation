# Research Dump: GFNY Florida Hardee (re-slugged from gfny-florida-sebring)

Researched: 2026-07-24. All URLs curl-verified 200 on this date unless noted.

## CORRECTION (2026-07-24, post sol adversarial review)

The first draft of this dump/profile asserted "largely the same roads"/"roads barely
changed" between Sebring and Hardee. That overstated the evidence. GFNY's own
announcement page (gfny.com/gfny-usa-announces-new-host-location-for-gfny-florida-2026/,
curl-verified 200) contains BOTH of the following, verbatim:

> "GFNY USA introduces a brand-new course that showcases the rural beauty and open roads
> of central Florida. The redesigned route will offer riders a fast and competitive
> racing experience."

> "Hardee County has been an outstanding partner since 2021, when we shifted the course
> west of Sebring. In fact, the majority of the racecourse has taken place in Hardee
> County in recent years, making it the natural first choice for this transition."

These are both GFNY's own words on the same page — one promotional ("brand-new"/
"redesigned"), one explanatory (geographic continuity since 2021). The profile now
quotes both rather than resolving them into a single "same roads" claim. The
franchise-continuation call (re-slug, not defunct) remains correct at the ORGANIZER/
FRANCHISE level; the specific 2026 Hardee routing should be treated as unrun/unproven
until the race actually happens.

## Re-slug decision: RENAMED/RELOCATED — same continuing franchise, not defunct

GFNY's own official announcement confirms this is the 7th edition of the same GFNY
Florida franchise under a new host-location name, not a new/distinct event:

> "the majority of the racecourse has taken place in Hardee County in recent years"
> — GFNY President Lidia Fluhme, on why Hardee replaces Sebring as host for 2026.

Source: https://www.endurancesportswire.com/gfny-usa-announces-new-host-location-for-gfny-florida-2026/ (curl 200),
https://gfny.com/gfny-usa-announces-new-host-location-for-gfny-florida-2026/ (curl 200).

This is NOT thin evidence: it is GFNY's own first-party statement (their race-finder/
official site, florida.gfny.com, already carries the "GFNY Florida Hardee" branding),
with a real, sourced course for the new venue (below). Per the task's re-slug threshold,
this warrants renaming `gfny-florida-sebring` -> `gfny-florida-hardee`, not leaving the
profile marked "defunct." A prior editorial pass (commit 11b2e96, "Editorial wave 9,"
2026-07-24) set `eligibility.status = "defunct"` and flagged the re-slug-vs-defunct call
for a human — this research resolves that flag in favor of re-slug, based on GFNY's own
explicit "continuation" language, which was not cited in that prior pass (no research
dump existed for either slug before this one).

## Core facts (verified)

- **Current official name**: GFNY Florida Hardee.
  Source: https://florida.gfny.com/ (curl 200, page title "Home - GFNY Florida Hardee").
- **Date**: October 25, 2026. 7th edition of the GFNY Florida franchise (6 editions ran
  at Sebring, 2020-2025).
  Source: gfny.com/gfny-announces-seven-2026-usa-races-on-the-road-to-nyc/ (curl 200).
- **Venue**: Hardee County Agri Civic Center, Wauchula, FL (Hardee County seat; start/finish
  "just outside the entrance to the property" per the official site).
  Source: https://florida.gfny.com/ (curl 200); venue address cross-checked against
  Hardee County's own listing (515/507 Civic Center Dr, Wauchula, FL 33873 — the county's
  own extension-office address, same complex) via public county-government sources.
- **Reason for move**: GFNY's own stated reason is "evolving course challenges" plus the
  fact that the majority of recent Sebring-era racecourse mileage was already routed
  through Hardee County since 2021 — a geographic correction, per GFNY's own framing,
  not a rebrand-to-avoid-a-failing-event narrative.
  Source: endurancesportswire.com (above, curl 200).

## Course — CORRECTED for the new Hardee venue (previous profile's vitals describe the retired Sebring course and are no longer current)

- **Long/Competitive course**: 135.7 km / 244 m gain (≈ 84.3 mi / 800 ft).
  Source: https://gfny.com/gfny-announces-seven-2026-usa-races-on-the-road-to-nyc/ (curl 200,
  direct quote: "a fast 135.7 km course with 244 meters of climbing").
  Cross-confirmed (84 mi / 800 ft) by endurancesportswire.com (curl 200).
- **Medium/Recreational course**: 45 mi / 400 ft (≈ 72.4 km / 122 m).
  Source: endurancesportswire.com (above, curl 200).
- **Format**: standard GFNY two-tier structure — long course is "A COMPETITION" with
  category rankings, Overall and Podium awards; medium course is explicitly "NOT A
  COMPETITION," riders get a start-to-finish time but results are listed alphabetically,
  not ranked.
  Source: https://florida.gfny.com/ (curl 200, direct site language).
- **Terrain**: fast, flat, rural Central Florida roads — farmland, open roads, "designed
  for high-speed racing and consistent conditions."
  Source: gfny.com/gfny-announces-seven-2026-usa-races-on-the-road-to-nyc/ (curl 200).

Note: `https://florida.gfny.com/gfny-florida-sebring-course-guide/` (curl 200) is still
live but describes the RETIRED Sebring course (89.5 mi/144 km, 715 ft/218 m, 2nd edition,
YMCA start) — this is historical, not the current Hardee course. Do not use its numbers
for the current profile; kept only as a historical citation for what the Sebring editions
were.

## Registration

- https://florida.gfny.com/register/ (curl 200) — active registration page for the
  October 25, 2026 edition.

## Prior Sebring-era history (retained as historical context, not current vitals)

- 6 editions ran at Sebring, October 2020 - October 26, 2025 (final Sebring edition).
  Source: https://gfny.com/flynn-and-pallone-win-6th-gfny-florida-sebring/ (curl 200).
- Founded 2020 (inaugural GFNY Florida edition, at Sebring). The franchise founding year
  is unchanged by the venue rename — this is edition 7 of the same continuing race, not
  a new race starting a fresh count.

## Old slug for redirect

Old slug: `gfny-florida-sebring`. This profile was re-slugged to `gfny-florida-hardee`
on 2026-07-24. The parent repo should add a redirect from the old slug to the new one
on next deploy.

## URLs curl-verified 2026-07-24 (all HTTP 200)

- https://gfny.com/gfny-usa-announces-new-host-location-for-gfny-florida-2026/
- https://www.endurancesportswire.com/gfny-usa-announces-new-host-location-for-gfny-florida-2026/
- https://gfny.com/gfny-announces-seven-2026-usa-races-on-the-road-to-nyc/
- https://florida.gfny.com/
- https://florida.gfny.com/register/
- https://florida.gfny.com/gfny-florida-sebring-course-guide/ (historical Sebring data only)
- https://gfny.com/flynn-and-pallone-win-6th-gfny-florida-sebring/ (historical Sebring data only)
