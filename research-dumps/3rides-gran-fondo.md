# 3RIDES Gran Fondo Südliche Weinstrasse — Research Dump

Debt-sweep verification pass, 2026-07-24. All URLs curl-verified live (HTTP 200) on 2026-07-24 unless noted.

## Eligibility
- **Status: active.** 2026 event held as the 100 km UCI 3RIDES Gran Fondo Südliche Weinstrasse, based at the Porte des Vins Allemands (German Wine Gate), Schweigen-Rechtenbach, Rhineland-Palatinate, Germany, crossing briefly into France. Relocated from the former Aachen venue.
- Source: https://weinstrasse.3rides.de/en/3rides-gran-fondo-suedliche-weinstrasse-podlaski-and-jehle-triumph/ (2026 race report, curl-verified 200) — confirms the 2026 Schweigen-Rechtenbach edition ran and names winners Podlaski and Jehle.
- 2025 Aachen edition was cancelled at the start due to severe weather — a one-off cancellation, not evidence of a defunct event.
- No 2027 date posted yet as of this pass.

## UCI affiliation claim — CONFIRMED TRUE
- Flagged claims: tagline "UCI Gran Fondo qualifier through German vineyards and into France"; final_verdict.one_liner "Technically demanding UCI road qualifier in scenic Pfalz wine lands."
- Direct verification: https://ucigranfondoworldseries.com/fr/3rides-gran-fondo/ — curl-verified live (HTTP 200), page `<title>` reads "3RIDES Gran Fondo - UCI Gran Fondo World Series", `dateModified` in page JSON-LD is 2026-04-24 (i.e., updated after the 2026 event ran), confirming the event is a live, current UCI Gran Fondo World Series calendar stop, not a stale listing.
- Alternate UCI GFWS URL also checked live: https://ucigranfondoworldseries.com/en/3rides/ (HTTP 200).
- The full UCI GFWS calendar page (https://ucigranfondoworldseries.com/en/calendar/, curl-verified live) independently lists "3RIDES Gran Fondo" under country GER, city Schweigen-Rechtenbach, dated Saturday 25 Apr 2026 — consistent with vitals.date_specific ("2026: April 25").
- Conclusion: no correction needed. Claim is accurate and current.

## Vitals cross-check
- distance_km 100.0 / elevation_m 600.0 / date "2026: April 25" — consistent with official race report and UCI GFWS calendar entry. No changes made.

## Citations (existing, all curl-verified live 2026-07-24)
- https://3rides.de/en/ — 200
- https://ucigranfondoworldseries.com/fr/3rides-gran-fondo/ — 200
- https://weinstrasse.3rides.de/en/3rides-gran-fondo-suedliche-weinstrasse-podlaski-and-jehle-triumph/ — 200

## Sol adversarial review
GPT-5.6-sol (read-only, foreground) reviewed this race alongside the rest of the batch. Verdict: CONFIRM, no correction. Sol independently found the same UCI GFWS page and confirmed Schweigen-Rechtenbach/25 April 2026/qualifier status.

## JSON changes made
- `eligibility.verified`: 2026-07-22 → 2026-07-24
- `eligibility.notes`: appended UCI reconfirmation detail
- No claim text changes (all flagged claims verified TRUE)
- No fondo_rating changes
