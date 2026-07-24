# Adelaide Epic Ride — Research Dump

Debt-sweep verification pass, 2026-07-24. All URLs curl-verified on 2026-07-24 unless noted.

## Eligibility
- **Status: active.** NX Sports-owned participation ride in South Australia, an associated event of the Santos Tour Down Under. No 2027 date posted yet as of this pass.
- Source: https://adelaideepic.org/ (curl-verified live, HTTP 200, page title "Home - Adelaide Epic Ride").

## UCI WorldTour route claim — CONFIRMED TRUE
- Flagged claims: tagline "...same roads as the UCI WorldTour pros... The community ride of Australia's biggest professional cycling race"; terrain.features "Rides the exact same route as the UCI WorldTour Men's Stage 3 on the same day"; final_verdict.one_liner "136 km on a UCI WorldTour stage route..."
- Direct verification #1: adelaideepic.org (curl-verified live) contains the text "You'll ride through the Santos Tour Down Under Ziptrak Men's Stage 3 finish line on Old Princes Highway in Nairne and will be in place to witness many more incredible finishes and stories throughout the day," and separately references Chandlers Hill as a notable climb on the route — matches vitals.location and terrain.features.
- Direct verification #2: the Tour Down Under's UCI WorldTour status is independently confirmed via https://en.wikipedia.org/wiki/Tour_Down_Under (curl-verified live, "...World Tour and UCI Women's WorldTour...") and — per sol's review — https://www.uci.org/competition-details/2026/ROA/76890 (curl-verified live, HTTP 200), the primary UCI regulatory source, added as a citation this pass.
- Conclusion: claim is substantively TRUE — the ride does follow the same course as an actual UCI WorldTour stage, run the same day. No text correction needed.

## Citation link rot (not corrected this pass — informational only)
- Two pre-existing citations are now dead: https://tourdownunder.com.au/ride/adelaide-epic-ride (404) and https://tourdownunder.com.au/products/events/2026/adelaide-epic-ride (404). Not swapped — 5 of the profile's 7 citations remain live, above the 3-citation gate floor, and the brief scopes citation edits to the <3 case. Flagging for a future cleanup pass.
- https://glamadelaide.com.au/thousands-of-riders-prepare-for-bupa-challenge-tour returned 403 under one User-Agent string and 200 under another — likely basic bot-blocking, not a dead link; treated as live.
- Added citation: https://www.uci.org/competition-details/2026/ROA/76890 (UCI's own competition-details page for the 2026 Tour Down Under) — strengthens the flagged UCI WorldTour claim with the primary regulatory source rather than relying on Wikipedia alone.

## Citations spot-checked live 2026-07-24
- https://adelaideepic.org/ — 200
- https://en.wikipedia.org/wiki/Tour_Down_Under — 200
- https://bicyclingaustralia.com.au/news/mass-participation-ride-returns-to-tdu/ — 200
- https://www.sportspro.com/news/bupa_renews_tour_down_under_cycling_sponsorship/ — 200
- https://www.uci.org/competition-details/2026/ROA/76890 — 200 (new)

## Sol adversarial review
GPT-5.6-sol (read-only, foreground) reviewed this race. Verdict: CONFIRM. Sol recommended citing uci.org directly rather than relying solely on Wikipedia for WorldTour status — applied (added as citation).

## JSON changes made
- `eligibility.verified`: 2026-07-22 → 2026-07-24
- `eligibility.notes`: appended UCI WorldTour reconfirmation + dead-link flag
- Added one citation (uci.org competition-details page)
- No claim text changes (all flagged claims verified TRUE)
- No fondo_rating changes
