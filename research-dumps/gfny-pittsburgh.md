# Research Dump: GFNY Pittsburgh-Monroeville

## Eligibility
- **Status: active.** Inaugural edition held Sunday, September 21, 2025, at CCAC Boyce Campus, Monroeville, PA. 2026 edition confirmed for September 20, 2026 (per file's existing eligibility note, independently corroborated this pass).
- Source: https://pgh.gfny.com/ (official site, current) — matches file; note field already documents a prior adversarial correction distinguishing pgh.gfny.com (Pittsburgh) from pennsylvania.gfny.com (a separate GFNY York, PA event) — re-verified, still accurate.

## Flagged claim: [size claim] history.origin_story — "bringing the world's largest cycling marathon brand to Western Pennsylvania"
**TRUE — leave text as-is.** GFNY's own official "About" page states directly: "GFNY is the world's largest endurance sports marathon" and describes itself as "the largest cycling marathon series" with 30+ events across 15+ countries on four continents (https://gfny.com/about/). This is GFNY's own self-description, consistently used across its press materials — not a fabricated superlative. The claim in the file describes the *brand's* global scale, not a claim that the Pittsburgh race itself is large (Pittsburgh's own field is small — "hundreds of riders" per file, which is accurate and not contradicted).

## Vitals correction (found during verification, not part of the original flag)
- **File's long-course distance/elevation are pre-race marketing figures, superseded by the actual course as raced.**
  - Pre-event announcement (gfny.com/new-us-race-michelob-ultra-gfny-pittsburgh-monroeville-on-september-21-2025/): "The competitive long distance is 70 miles long with 7756 ft of climbing" — this matches the current file (`distance_mi: 70.0`, `elevation_ft: 7756.0`).
  - **Post-event report** (gfny.com/dominating-solo-wins-at-michelob-ultra-gfny-pittsburgh-monroeville/, published after the Sept 21, 2025 race): "The long course of **79.9 miles with 8,701 feet of climbing** made it the toughest GFNY race in the United States."
  - Per the site's established precedent for actual-vs-advertised course data (see flandrien-ride.json, gfny-grand-ballon.json), the post-event figure is authoritative. **CORRECTED vitals to distance_mi 79.9 / distance_km 128.6, elevation_ft 8,701 / elevation_m 2,652.** Updated the matching `route_options` long-course entry to match.

## Citations added (curl-verified 200)
- https://gfny.com/dominating-solo-wins-at-michelob-ultra-gfny-pittsburgh-monroeville/ — source for the corrected post-event distance/elevation figures.

## Notes
- Existing 4 citations (gfny.com announcement, endurancesportswire.com, gfny.com inaugural preview, pgh.gfny.com) re-verified live; the "note" field content re-verified accurate (Pittsburgh vs. York, PA URL confusion correctly resolved).
