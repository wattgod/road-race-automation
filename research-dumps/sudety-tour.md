# Sudety Tour — Research Dump

Debt-sweep verification pass, 2026-07-24. URLs curl/WebFetch-verified live unless noted.

## Eligibility
- **Status: active.** Confirmed by both official site (sudetytour.cz, HTTP 200) and independent 2026 race coverage.
- The 13th edition of Dekom System Sudety Tour ran May 9-10, 2026 in Broumov, Czechia — its UCI Gran Fondo World Series debut, and Czechia's first-ever UCI Gran Fondo World Series stop. Source: https://granfondodailynews.com/2026/05/11/uci-gran-fondo-world-series-sudety-tour-delivers-drama-on-czech-polish-border/ (WebFetch-confirmed, contains full race report with results).
- Format confirmed: Saturday 10.6 km uphill time trial in Radków, Poland; Sunday 85 km mediofondo and 147 km granfondo. Top 25% qualified for the 2026 UCI Gran Fondo World Championships (Niseko, Japan).
- Winners (gran fondo, 147 km): Jan Miazga (men, 03:44:14, photo finish over teammate Artur Sowiński), Adéla Koclířová (women, 04:09:18).
- Note: the race report cites 147 km for the gran fondo vs. the profile's vitals.distance_km 149.7 — a minor, non-material discrepancy (could reflect a different measured/GPS distance vs. official course distance); not corrected, as it is not one of the flagged claims and doesn't rise to "wrong vitals" by any meaningful margin.
- Existing eligibility block (verified 2026-07-22, source sudetytour.cz/en/) is consistent with this and correctly reflects 2027 dates (May 8-9) for the next edition. No change needed.

## UCI affiliation claim — CONFIRMED TRUE
- Flagged claim: `final_verdict.should_you_race` — "...the event's 2023 revival and 2026 UCI integration mean limited hist[orical data]..."
- Verification: WebSearch (GranFondoGuide, granfondodailynews.com) and the official site independently confirm: Sudety Tour originally ran 2004-2013, was revived in 2023 as "Dekom System Sudety Tour," and 2026 was confirmed as its first year in the UCI Gran Fondo World Series ("Sudety Tour will mark the first-ever UCI Gran Fondo in Czechia").
- Conclusion: claim is accurate as written. No correction needed.

## Citations (existing, spot-checked)
- https://ucigranfondoworldseries.com/en/sudety-tour/ — could not curl-verify directly (sandbox DNS/TLS to this host times out even with --resolve 8.8.8.8; consistent with the known landmine for this domain), but independently corroborated via WebSearch snippet showing the live UCI GFWS listing title "Sudety Tour - UCI Gran Fondo World Series."
- https://www.sudetytour.cz — HTTP 200, curl-verified.
- https://sudetytour.cz/en/ — HTTP 200, curl-verified.
- https://www.uci.org/competition-details/2026/CPT/78723 — curl timed out from this sandbox (exit 28); not independently re-verified this pass, but was already present/verified in a prior wave (existing citation, left as-is).
- 4 citations total — meets the >=3 minimum. No additions made.

## Sol adversarial review
Not run as a separate pass for this race individually — batch-level sol review below covers all 8 races (see tour-of-georgia-gran-fondo dump for the consolidated summary, or the executor's final report).

## JSON changes made
- None. Flagged claim verified TRUE, citations already >=3, eligibility block already correct and current.
