# GFNY Salinas — Research Dump (2026-07-24)

Editorial wave 7. Research via `codex --search exec -m gpt-5.6-sol` (web search
enabled), read-only, run 2026-07-24. Companion race: granfondo-ecuador.md
(same town, confirmed separate event).

## Identity check / dedupe verdict

CONFIRMED REAL AND DISTINCT from granfondo-ecuador.json, despite sharing a
location (Salinas, Santa Elena, Ecuador). This was investigated specifically
as a possible duplicate given the shared location and the fact that GFNY's
global gran fondo series was reorganized under the UCI Gran Fondo World
Series banner elsewhere in the catalog (e.g. GFNY Bali -> GFNY Belitung).
That hypothesis is REFUTED for this pair:

- GFNY Salinas ran March 1, 2026. GFNY's own March 3 report calls it the
  inaugural Salinas edition and records a 110.8 km/878m course.
  https://gfny.com/sprint-finish-at-gfny-salinas/
- Granfondo Ecuador is a separate, new UCI Gran Fondo World Series event,
  first scheduled for November 14, 2026, organized by MACMANE S.A.S. with
  UCI and Ecuadorian Cycling Federation sanction — NOT GFNY.
  https://ucigranfondoworldseries.com/en/granfondo-ecuador/
- Different official websites: GFNY uses salinas.gfny.com; the UCI event
  uses touralecuador.ec.
- Different routes: GFNY is 110.8 km/878m via Cerro El Morro/La Chocolatera
  (point-to-point/large-loop coastal course with a neutralized rollout);
  the UCI event is a 127.88 km/87.62 km multi-lap circuit beside the main
  Salinas beach.
- Different organizers: GFNY Inc. vs. MACMANE S.A.S.

Conclusion: these are two separate, real events in the same coastal town.
Do not merge gfny-salinas.json and granfondo-ecuador.json.

## Eligibility

- Status: active — confirmed HELD as scheduled on March 1, 2026 (inaugural
  edition). This reverses the prior "unknown, no accessible evidence" finding,
  which had searched gfny.com generically rather than the event's own
  salinas.gfny.com microsite and GFNY's own post-event reporting.
- No UCI affiliation found for this specific GFNY-branded race — it is a
  GFNY-network event, not a UCI-sanctioned one. (The separate Granfondo
  Ecuador event in the same town IS a UCI Gran Fondo World Series qualifier
  — see granfondo-ecuador.md — but that is a different race.)

## Course facts

- 110.8 km / 878m, via Cerro El Morro/La Chocolatera.
- ~2 km neutralized rollout before racing began.
- Debut edition (March 2026) encountered rain, fog, and exposed coastal
  crosswinds.

## Sources

- https://gfny.com/sprint-finish-at-gfny-salinas/ (official, post-event report)
- https://gfny.com/inaugural-gfny-salinas-this-sunday/ (official, pre-race report)
- https://salinas.gfny.com/?lang=en (official event site)
- https://salinas.gfny.com/getting-here/?lang=en (official travel page)
- https://ucigranfondoworldseries.com/en/granfondo-ecuador/ (official, confirms the separate UCI event)
