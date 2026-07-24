# Granfondo Ecuador — Research Dump (2026-07-24)

Editorial wave 7. Research via `codex --search exec -m gpt-5.6-sol` (web search
enabled), read-only, run 2026-07-24. Companion race: gfny-salinas.md (same
town, confirmed separate event).

## Identity check / dedupe verdict

Confirmed real, but the "this is a GFNY rebrand" hypothesis is REFUTED.
Granfondo Ecuador and GFNY Salinas are two separate events held in the same
city (Salinas, Santa Elena, Ecuador) in 2026:

- Granfondo Ecuador is a NEW UCI Gran Fondo World Series qualifier, first
  scheduled for November 14, 2026. Organizer: MACMANE S.A.S., with UCI and
  Ecuadorian Cycling Federation sanction.
  https://ucigranfondoworldseries.com/en/granfondo-ecuador/
  https://ucigranfondoworldseries.com/en/calendar/
- Official site: touralecuador.ec (distinct from GFNY's salinas.gfny.com).
- GFNY Salinas actually ran March 1, 2026, as a separate GFNY-network event
  (organizer: GFNY Inc.) — see gfny-salinas.md and
  https://gfny.com/sprint-finish-at-gfny-salinas/
- Different routes: Granfondo Ecuador is a 127.88 km (3-lap)/87.62 km
  (2-lap) circuit beside the main Salinas beach; GFNY Salinas is a 110.8 km
  point-to-point/loop course via Cerro El Morro/La Chocolatera.
- Different organizers, different official sites, different dates (Nov 14
  vs. Mar 1).

Conclusion: two separate, real events in the same coastal town. Do not merge
granfondo-ecuador.json and gfny-salinas.json.

## Eligibility

- Status: active/announced — first edition has not yet occurred as of this
  research date (2026-07-24); scheduled November 14, 2026.
- UCI affiliation: CONFIRMED. This is a UCI Gran Fondo World Series
  qualifier event, organized by MACMANE S.A.S. with Ecuadorian Cycling
  Federation sanction. Source:
  https://ucigranfondoworldseries.com/en/granfondo-ecuador/ (official UCI
  Gran Fondo World Series profile page for this event) and
  https://www.touralecuador.ec/REGLAMENTO/REGLAMENTO%20GENERAL%20UCI%20GF%20WS%20SALINAS.pdf
  (official regulations PDF, titled "REGLAMENTO GENERAL UCI GF WS SALINAS").
- Note: the event's own regulations PDF repeatedly labels the 87.62 km
  distance "non-qualifying," while the UCI series calendar page assigns
  that distance to older age categories in what is otherwise described as a
  qualifier event — an internal contradiction, flagged in the profile's
  biased_opinion, not resolved by this research pass.

## Course facts

- Long: 127.88 km, 3 circuits, men 19-59 / women 19-49.
- Short: 87.62 km, 2 circuits, older age categories.
- Elevation: UCI page states 184m per lap; no unambiguous event-total figure
  published. Do not treat a naive per-lap multiplication as a verified total.
- Start/finish: adjacent to Salinas's main beach.
- Field cap: 1,000 cyclists.
- Entry fee: $89 early bird -> $99 -> $109 (Jun 15-Aug 16) -> $119 final phase.

## Sources

- https://ucigranfondoworldseries.com/en/granfondo-ecuador/ (official)
- https://ucigranfondoworldseries.com/en/calendar/ (official)
- https://www.touralecuador.ec/ (official organizer site)
- https://www.touralecuador.ec/Reglamentos-y-categorias.html (official)
- https://www.touralecuador.ec/REGLAMENTO/REGLAMENTO%20GENERAL%20UCI%20GF%20WS%20SALINAS.pdf (official)
- https://gfny.com/sprint-finish-at-gfny-salinas/ (confirms the separate GFNY event)
