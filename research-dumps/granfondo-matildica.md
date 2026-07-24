# Research Dump: Granfondo Matildica

Verified 2026-07-24 via live web search (codex/gpt-5.6-sol) + direct curl verification of every URL below.

## Quick Facts
- Location: Reggio Emilia, Emilia-Romagna, Italy.
- Date: September 13, 2026.
- Course: Gran Fondo 153 km / 2,150 m gain; Medio Fondo 126 km / 1,450 m gain (organizer's current 2026 figures — match the existing JSON vitals exactly). Note: some body text on the UCI GFWS event page retains older 130/156 km figures from prior editions — the organizer's site and header figures are the authoritative current values, which is what's already in race-data/granfondo-matildica.json.
- Founded 1973 (53rd edition ran 2025).

## UCI Gran Fondo World Series Status — VERIFIED TRUE (the UCI-affiliation portion specifically)
The UCI-affiliation clauses in the tagline ("...UCI Gran Fondo World Series qualifier through the Emilia-Romagna Apennines"), one_liner ("Essential UCI qualifier for road enthusiasts"), and should_you_race ("offering legitimate UCI World Series qualification split smartly by age") are confirmed accurate — this is specifically a UCI Gran Fondo World Series qualifier, not merely a generic UCI-sanctioned event. Note this verifies the UCI-affiliation clauses only, not every other claim in those same sentences (e.g. "Italy's oldest gran fondo" — see caveat below, which was correctly scoped out of this batch's fix).

- Live UCI Gran Fondo World Series event page for the 2026 edition: https://ucigranfondoworldseries.com/en/gran-fondo-matildica-2026/ (HTTP 200 via curl --resolve)
- A UCI GFWS calendar-update article confirms Matildica returns to the World Series on September 13, 2026 as "the first qualifier for the 2027 UCI Gran Fondo World Championships." https://ucigranfondoworldseries.com/en/calendar-update-two-date-changes-and-one-new-event-added-to-the-2026-uci-gran-fondo-world-series/ (HTTP 200)
- Independently corroborated by Battistrada's 2026 course listing. https://battistrada.com/en/cycling-calendar/edition/granfondo-matildica-2026/51676/ (HTTP 200)
- Pre-existing race-data citation (ucigranfondoworldseries.com/en/gran-fondo-mathildica-2025/) already confirmed the 2025 edition was also a World Series stop; this dump adds 2026 confirmation.

## "Italy's Oldest Gran Fondo" Claim — NOT in this batch's flagged scope, noted for completeness
The founding year (1973) is confirmed by the organizer's own site and by BICITV's history coverage. However, sources support "one of Italy's/the world's oldest gran fondos" more directly than the stronger, singular claim "Italy's oldest." This specific claim was NOT flagged by the audit for this batch (only the UCI-affiliation claims were flagged) — per the debt-sweep brief's surgical-fix rule, no text change was made to the "Italy's oldest gran fondo" tagline language. Flagging here for a future editorial pass if the age-claim gets audited separately.

## Eligibility
- Status: active. Matches existing eligibility block (verified 2026-07-20, source granfondomatildica.it). Reconfirmed live via the UCI GFWS 2026 event page.

## Citations (curl-verified 2026-07-24)
1. Official 2026 race site — https://www.granfondomatildica.it/it/ (HTTP 200, pre-existing citation, re-verified)
2. UCI Gran Fondo World Series 2026 event page — https://ucigranfondoworldseries.com/en/gran-fondo-matildica-2026/ (HTTP 200)
3. UCI GFWS calendar-update article confirming 2027-qualifier status — https://ucigranfondoworldseries.com/en/calendar-update-two-date-changes-and-one-new-event-added-to-the-2026-uci-gran-fondo-world-series/ (HTTP 200)
4. Battistrada — independent 2026 course listing — https://battistrada.com/en/cycling-calendar/edition/granfondo-matildica-2026/51676/ (HTTP 200)
5. BICITV — history/presentation report — https://www.bicitv.it/2024/06/21/presentazione-granfondo-matildica-merida/ (HTTP 200)

Note on sandbox DNS: `ucigranfondoworldseries.com` fails to resolve via this environment's default resolver but resolves via `dig`. All ucigranfondoworldseries.com URLs above were confirmed HTTP 200 using `curl --resolve host:443:<resolved-ip>`.
