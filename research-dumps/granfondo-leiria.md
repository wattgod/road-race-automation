# Research Dump: Granfondo Leiria Region – Sicó Lands

Compiled 2026-07-24, editorial wave 5 (gpt-5.6-sol web search, foreground).

## Quick Facts
- Status: 2026 debut edition CANCELLED/POSTPONED to spring 2027 (no confirmed 2027 date yet).
- This is the UCI Gran Fondo World Series' new name/host-region for the event previously run as Granfondo Coimbra Region (2021-2025) — same organizer, Cabreira Solutions.
- No edition of "Granfondo Leiria Region" has ever actually been held.
- Planned (cancelled) 2026 course: Granfondo 146 km / 1,478 m; Mediofondo 93 km / 1,000 m; Time trial 20.5 km / 98 m (flat), at Praia do Pedrógão.
- Planned original 2026 date: March 28-29, 2026, Pombal.

## UCI Affiliation — verified
Genuine UCI Gran Fondo World Series round (successor to the Coimbra round), not marketing-only branding.

Sources:
- UCI Leiria event page (course/format for the planned 2026 debut): https://ucigranfondoworldseries.com/en/granfondo-leiria-region/ (curl-verified 200, 2026-07-24)
- UCI — official relocation announcement, Jan 15 2026: https://ucigranfondoworldseries.com/en/portuguese-uci-gran-fondo-world-series-event-moves-to-leiria-region/ (curl-verified 200, 2026-07-24)
- UCI — official cancellation notice, Feb 20 2026, cites Storm Kristin damage: https://ucigranfondoworldseries.com/en/uci-granfondo-leiria-sica-lands-cancelled-due-to-exceptional-circumstances/ (curl-verified 200, 2026-07-24)
- Cabreira Solutions (organizer) live page, "Evento Adiado para 2027": https://cabreirasolutions.com/evento/granfondo-leiria-region/ (curl-verified 200, 2026-07-24)
- Gran Fondo Guide cancellation coverage, Feb 22 2026: https://www.granfondoguide.com/Contents/IndexFull/9025/2026-uci-granfondo-leiria-region-cancelled-after-storm-kristin-wreaks-havoc-in-portugal
- Jornal de Leiria local coverage, March 11 2026: https://www.jornaldeleiria.pt/noticia/ciclismo-granfondo-de-leiria-adiado-para-2027

## Cancellation ground truth
The UCI's Feb 20, 2026 cancellation notice states the event would not take place in 2026 and would be postponed to spring 2027 because Storm Kristin left widespread regional disruption — power/housing damage, closed hospitality businesses. Corroborated independently by the organizer's own live page and by two Portuguese press outlets. Current next-edition date: spring 2027, exact date TBD. A third-party (Gran Fondo Guide) listing shows March 27-28, 2027 but is explicitly labeled "Unconfirmed" with stale distance data (148/108km) — not to be trusted as official.

## One event or two? (relative to gran-fondo-coimbra.json)
One underlying event lineage and organizer (Cabreira Solutions), relocated to a new host territory/identity/course — not two coexisting races. UCI's own page calls Leiria "the new name for the successful Granfondo Coimbra Region." Treat gran-fondo-coimbra.json as the discontinued predecessor and this profile as the (as-yet-unrun) successor.

## Data-quality corrections applied to race-data/granfondo-leiria.json this wave
- distance_km: 148.1 -> 146.0 (organizer's own officially-announced, cancelled 2026 plan)
- elevation_m: 1981 -> 1478 (organizer's own officially-announced, cancelled 2026 plan; the 1,981/6,500ft figure on file appears to have been copy-pasted from the Coimbra predecessor profile, not independently sourced for Leiria)
- date: "2026: March 29" (a date the event was never actually held on) -> "2027: Spring TBD"
- Removed/softened unsupported course narrative claims (a "Leiria-to-Praia-do-Pedrogao out-and-back" and a "Pombal fortress finish" sprint) — the time trial is confirmed to start/finish at Praia do Pedrógão itself; no source supports a dramatic fortress-finish sprint
- eligibility.status: "cancelled" (unchanged, but refined with the spring-2027 postponement date and full source trail)

See also: research-dumps/gran-fondo-coimbra.md (the predecessor event's own research).
