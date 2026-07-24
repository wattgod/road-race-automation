# Research Dump: Granfondo Bogotá (UCI Granfondo Bogotá, 2025 edition — DEFUNCT, succeeded by Granfondo Colombia/Medellín)

Verified 2026-07-24 via codex gpt-5.6-sol foreground research + direct curl verification, as part of the Roadie Labs debt-sweep (batch 4).

## Quick Facts
- The profile's own `eligibility` block, already on file before this pass, correctly states: status "defunct," notes "First edition Bogotá Dec 7 2025. Successor: Granfondo Colombia, relocated to Medellín — Nov 29 2026 (UCI Gran Fondo World Series)." This pass **confirms that finding independently** and corrects the remaining present-tense prose in the body of the profile that still reads as if Bogotá is an active, upcoming event.

## Confirmed: Bogotá relocated to Medellín for 2026, does not run in Bogotá again
Curl-verified directly from the UCI's own Colombia event page:

> "Granfondo Colombia Date Sunday 29.11.2026 Distances 120 km City Medellin Country Colombia... UCI Gran Fondo Colombia relocates for its second edition to the city of Medellin after a first race in Bogota in december 2025." — https://ucigranfondoworldseries.com/en/uci-gran-fondo-colombia-2026/ (curl-verified 200)

This repo already has a separate profile for the successor event: `race-data/gran-fondo-medellin.json` (display_name "UCI Gran Fondo Colombia (Medellín)"), independently verified and updated 2026-07-24 as part of a parallel wave — confirms this is a **relocation, not a rename of the same slug**; the Bogotá profile and the Medellín profile are correctly two separate race-data files (different host cities, different course).

- UCI Colombia 2026 event page (curl-verified, quoted above): https://ucigranfondoworldseries.com/en/uci-gran-fondo-colombia-2026/
- Successor profile (out of this batch's scope, not touched): `race-data/gran-fondo-medellin.json`

## Claim verification

| Claim | Verdict | Evidence |
|---|---|---|
| display_name: "UCI Granfondo Bogotá" | TRUE as historical identity — this profile specifically documents the one-off 2025 Bogotá edition, distinct from the Medellín successor | Left unchanged; it accurately names the race that ran, once, in Bogotá. |
| tagline: "High-altitude UCI qualifier in Colombia's cycling capital" | **STALE** — present tense implies an ongoing/current event; the race no longer runs in Bogotá | UCI Colombia 2026 page confirms relocation to Medellín (quoted above) |
| final_verdict.should_you_race: "...UCI prestige meets local fire—must-do for qualifiers" | **STALE** — "must-do" is an actionable present-tense recommendation for an event that no longer exists in this city | Same source |

## Fix applied
- `tagline`: "High-altitude UCI qualifier in Colombia's cycling capital" → reworded to past-tense framing noting the one-off Bogotá edition and the Medellín relocation.
- `final_verdict.should_you_race`: "UCI prestige meets local fire—must-do for qualifiers." → corrected to note the race relocated to Medellín, pointing qualifier-seekers to the successor event instead of implying Bogotá is still actionable.
- `display_name` and `biased_opinion` left unchanged — they're framed as historical narrative about the 2025 race (consistent with `eligibility.status: defunct` already on file) and don't assert current availability.
- No catalog_flags change needed — the existing `eligibility` block already correctly captures the defunct/relocated status; this pass only aligns the body prose with it.

## Eligibility
(unchanged from what was already on file — confirmed correct, verified date refreshed)
- status: defunct
- verified: 2026-07-24
- source: https://ucigranfondoworldseries.com/en/uci-gran-fondo-colombia-2026/
- notes: unchanged — "First edition Bogotá Dec 7 2025. Successor: Granfondo Colombia, relocated to Medellín — Nov 29 2026 (UCI Gran Fondo World Series)."

## Sol adversarial review pass (2026-07-24)
- **Applied — vitals contradiction**: top-level `vitals.distance_km`/`elevation_m` (109.4 km / 1,500 m) contradicted the profile's own `route_options` (128 km / 1,276 m) AND my own edited `final_verdict.should_you_race` text (which already said "128km with 1,276m gain," matching sol's independently-confirmed historical Bogotá vitals). Corrected top-level vitals to 128.0 km / 79.5 mi / 1,276 m / 4,186 ft to match.
- **Applied**: `logistics.transport` still described the race as "a new event" awaiting updates, inconsistent with `eligibility.status: defunct` — reworded to past-tense, one-off-edition framing.
- **Applied — overreach walked back**: my first-pass edit to `should_you_race` said "this Bogotá edition will not run again," which sol correctly flagged as overreaching — the UCI source proves the 2nd edition relocated to Medellín for 2026, not that Bogotá can categorically never host a future edition. Reworded to "the event does not run in Bogotá in 2026."
- **Applied**: added the UCI Colombia 2026 relocation page as a citation (previously only referenced in prose, not in the `citations` array).
- **Deferred**: sol also flagged `biased_opinion.summary`'s closing line ("Perfect for altitude junkies chasing qualifiers in cycling-mad Colombia") and `final_verdict.one_liner` ("Elite high-altitude road qualifier with massive suffering potential") as present-tense-flavored. Left unchanged — neither was in this batch's flagged claims, `biased_opinion` is explicitly protected from wholesale rewrites per the brief, and both read as generic historical/descriptive framing rather than actionable "go do this" claims (unlike `should_you_race`, which is the section specifically meant to tell a reader what to do next and where the "must-do for qualifiers" language actually lived).
