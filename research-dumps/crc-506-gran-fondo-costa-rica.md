# CRC 506 Gran Fondo Costa Rica — Research Dump

Debt-sweep verification pass, 2026-07-24. All URLs curl-verified on 2026-07-24 unless noted.

## Eligibility
- **Status: active** (rescheduled, not cancelled). Jacó, Garabito, Puntarenas Province, Costa Rica.
- Original June 7, 2026 date was postponed due to high thunderstorm risk; organizer rescheduled to September 13, 2026 and reopened registration.
- Source (this pass): https://www.miprensacr.com/crc-506-gran-fondo-costa-rica-se-realizara-el-13-de-septiembre-y-reabre-sus-inscripciones/ (curl-verified live, HTTP 200).
- The official site https://ucigranfondocostarica.com/ currently returns **HTTP 500 (database connection error)** as of 2026-07-24 — could not use as a live primary source this pass; relying on miprensacr.com plus the UCI GFWS calendar instead.

## UCI affiliation claim — CONFIRMED TRUE
- Flagged claims: tagline "Costa Rica's UCI Gran Fondo qualifier on the stunning Pacific coast"; final_verdict.one_liner "Strong regional UCI event with international appeal and qualification prestige."
- Direct verification: the UCI Gran Fondo World Series calendar (https://ucigranfondoworldseries.com/en/calendar/, curl-verified live) lists "CRC 506 Gran Fondo of Costa Rica," city Jaco, with event-date status showing **"Postponed"** — this is a rescheduled/postponed listing, not a removed/cancelled one. Combined with the organizer's own reschedule announcement (miprensacr.com, live), this confirms the event remains an active UCI GFWS calendar entry that simply hasn't had its calendar date field updated to reflect the September 13 reschedule.
- Additional corroborating source found by sol's review: https://semanariouniversidad.com/deportes/alerta-meteorologica-lleva-a-reprogramacion-de-gran-fondo-crc-506-en-septiembre/ (curl-verified live, title confirms "Alerta meteorológica lleva a reprogramación de Gran Fondo CRC 506 en septiembre") — independently confirms the storm-driven reschedule to September. Added as a citation this pass.
- Sol also proposed a dedicated 2026 official subdomain, https://2026.ucigranfondocostarica.com/ — **this does NOT resolve** (DNS failure, curl error 6 "Could not resolve host"). This specific sol finding is **rejected** — no such live subdomain exists as of 2026-07-24.
- Conclusion: claim is TRUE. Same treatment pattern as Cyprus Gran Fondo in this batch (postponed-on-calendar but organizer-confirmed rescheduled, not cancelled). No text correction needed.

## Citations (existing + added, spot-checked 2026-07-24)
- https://ucigranfondocostarica.com/ — HTTP 500 (currently down; not usable this pass, left as a historical citation)
- https://ucigranfondoworldseries.com/ — 200
- https://www.miprensacr.com/crc-506-gran-fondo-costa-rica-se-realizara-el-13-de-septiembre-y-reabre-sus-inscripciones/ — 200
- https://semanariouniversidad.com/deportes/alerta-meteorologica-lleva-a-reprogramacion-de-gran-fondo-crc-506-en-septiembre/ — 200 (new, added this pass)

## Sol adversarial review
GPT-5.6-sol (read-only, foreground) reviewed this race. Verdict: CONFIRM on Sept 13/qualification status, citing a semanariouniversidad.com article and claiming a live "2026.ucigranfondocostarica.com" official subdomain. The semanariouniversidad citation was verified and added; the subdomain claim was checked directly and REJECTED — it does not resolve (DNS failure).

## JSON changes made
- `eligibility.verified`: 2026-07-22 → 2026-07-24
- `eligibility.source`: ucigranfondocostarica.com (currently down) → miprensacr.com (live, curl-verified)
- `eligibility.notes`: appended the 500-error finding and TRUE-claim reconfirmation
- Added one citation (semanariouniversidad.com)
- No claim text changes (flagged claims verified TRUE)
- No fondo_rating changes
