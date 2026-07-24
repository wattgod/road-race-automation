# Research Dump: Gent-Wevelgem Cyclo (Cyclo In Flanders Fields – Wevelgem)

## Eligibility
- **Status: active.** 2026 edition held Saturday, March 28, 2026 (rebranded "Cyclo In Flanders Fields – Wevelgem"), matching the pro race's new "In Flanders Fields – From Middelkerke to Wevelgem" branding.
- Source: https://inflandersfieldscyclo.be/en/ (official 2026 event site — confirms date, distances, pricing).

## Flagged claims: [UCI affiliation] final_verdict.one_liner + should_you_race — "a historically rich mirror of a UCI WorldTour classic" / "ensures you're riding current UCI WorldTour terrain"
**TRUE — leave text as-is.** Verified:
- The professional Gent-Wevelgem race (now "In Flanders Fields – From Middelkerke to Wevelgem") was the **12th round of the 2026 UCI WorldTour**, run March 29, 2026, 240.8km, won by Jasper Philipsen, with all 18 UCI WorldTeams plus 7 UCI ProTeams starting. Source: Wikipedia 2026 Gent–Wevelgem race report (cross-checked against UCI's own competition page https://www.uci.org/competition-details/2026/ROA/76909, both live).
- The amateur cyclo is held the day before (Saturday) and shares the "In Flanders Fields" branding and finish town (Wevelgem) with the Sunday pro race, and its longer routes explicitly market shared terrain: the official 2026 cyclo site advertises "ride just like the pros across the world-famous **Plugstreets**" and cobbles crossing into France on the 225km route — both pro-race signature features.
- **Nuance for the record:** the official cyclo site does not publish a literal route-file comparison confirming 100% course overlap with the Sunday pro race (the pro race starts on the coast at Middelkerke; the cyclo starts/finishes in Wevelgem). The claim "riding current UCI WorldTour terrain" is defensible as shared signature sectors (Plugstreets, Kemmelberg-area climbs, Franco-Belgian cobbles), not a literal identical parcours. This is consistent with how every other "ride the pro course" cyclosportive markets itself (e.g., Étape du Tour) and does not rise to a fabrication — no correction needed.

## Vitals correction (found during verification, not part of original flag set)
- **File's primary vitals were stale/broken and did not match any current official distance:**
  - `distance_km: 65.0` / `distance_mi: 40.4` — no such distance exists in the current lineup. 2026 official distances (https://inflandersfieldscyclo.be/en/) are **70 / 95 / 125 / 150 / 225 km**, with elevation gain +340m / +600m / +900m / +1,100m / +1,100m respectively.
  - `elevation_m: 2901350.0` — a clear data-entry/concatenation error (2.9 million meters of climbing is impossible); paired `elevation_ft: 951.0` (≈290m) also didn't match any real distance's gain.
- The profile's course_description (Kemmelberg twice, Plugstreets, Franco-Flemish hills, French-border cobbles) describes the longest/flagship route. **CORRECTED vitals to the 225km route: distance_km 225.0 / distance_mi 139.8, elevation_m 1,100 / elevation_ft 3,609.** Added `route_options` listing all 5 official 2026 distances + elevation.
- Entry fee: file's `should_you_race` text claimed "estimated €47–60 entry" — current official 2026 pricing (VAT-inclusive) is **€25 (70km) to €45 (225km)** tiered by distance, plus a €5 refundable ID-tag deposit. **CORRECTED the entry-fee figure in should_you_race text**; left the "5,000 participants (40% international)" estimate untouched — no source found to confirm or deny it, flagging as unverified rather than fabricated.

## Citations
- Existing 7 citations (official site, Wikipedia, Etixx, cyclinginflanders.cc, cyclingstage.com, sportivebreaks.com, UCI competition page) spot-checked, all live and relevant to the claims above — no additions required (already above the 3-citation floor).

## Sources used this pass
- https://inflandersfieldscyclo.be/en/ (official 2026 cyclo site — distances, elevation, pricing, date)
- https://www.uci.org/competition-details/2026/ROA/76909 (UCI competition record for pro race)
- https://en.wikipedia.org/wiki/2026_Gent%E2%80%93Wevelgem (2026 pro race report, UCI WorldTour round confirmation)
