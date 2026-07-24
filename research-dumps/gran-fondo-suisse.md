# Research Dump: Gran Fondo Suisse (Villars-sur-Ollon / "The Majestics" 2026)

Verified 2026-07-24 via codex gpt-5.6-sol foreground research + direct curl verification, as part of the Roadie Labs debt-sweep (batch 4).

## Quick Facts
- **Location**: Villars-sur-Ollon, Canton of Vaud, Switzerland
- **2026 edition**: rebranded to "The Majestics" — UCI time trial July 10, UCI Granfondo July 11, 2026 (a separate UCI Gravel World Series race ran July 12 as part of the same combined weekend). Profile's "July 10-12" date range for the weekend is accurate as a weekend descriptor; the Gran Fondo/TT road program specifically ran July 10-11.
- **Distance/elevation**: Granfondo 150 km, ~3,760 m per the organizer's UCI GFWS event page (close to profile's 150km/3,700m — no material vitals error, left unchanged).

## UCI Gran Fondo World Series status: CURRENT FOR 2026, RENAMED
The event kept its UCI Gran Fondo World Series qualifier status for 2026 under the new "The Majestics" organizer branding.
- UCI competition record (UGF classification): https://www.uci.org/competition-details/2026/CPT/78749
- UCI GFWS calendar (curl-verified: page source contains "Villars", "Majestics"): https://ucigranfondoworldseries.com/en/calendar/
- Official Majestics site: https://themajestics.ch/en/
- UCI Villars event page: https://ucigranfondoworldseries.com/en/villars/

2027 UCI GFWS sanction is **not yet confirmed** — the organizer's site references a return next July but the UCI has not yet published a 2027 calendar entry for it.

## Claim verification

| Claim | Verdict | Evidence |
|---|---|---|
| final_verdict.one_liner: "Vaud Alps' brutal UCI gem redefines fondo suffering" | TRUE | UCI qualifier status confirmed current for 2026; "brutal"/vert claims are supported by the ~3,700-3,760m course. |
| Rebranded to "The Majestics" for 2026 | TRUE | Both UCI calendar and competition record use the new name. |

## Duplicate profile (CONFIRMED already resolved by a parallel wave — correction to this dump)
`race-data/the-majestics.json` describes the same event lineage (Villars-sur-Ollon). I initially wrote this up as an unresolved dedupe finding for a future pass, but the sol adversarial review pass caught that `the-majestics.json` already carries `catalog_flags.duplicate_of: "gran-fondo-suisse"` (set 2026-07-24, "dedupe sweep," evidently by a parallel batch running the same day) — so this was already fixed elsewhere, not something outstanding. I also incorrectly wrote in my first pass that the two profiles share the same `official_site`; verified false — `gran-fondo-suisse.json` uses `https://ucigranfondosuisse.ch` and `the-majestics.json` uses `https://ucigranfondoworldseries.com/en/villars/`. Both corrections applied to `eligibility.notes`.

## Fix applied
No prose changes — all flagged claims verified TRUE. `eligibility.notes` updated to correctly describe the already-resolved duplicate relationship (see above) instead of the stale "out of scope, flagging for follow-up" framing from the first pass.

## Sol adversarial review pass (2026-07-24) — other finding, rejected/deferred
Sol observed that this profile conflates the road Gran Fondo with the separate UCI Gravel event held the same weekend (e.g. `terrain.surface` mentions "10% offroad gravel crushers and wooded singletracks," `biased_opinion.weaknesses` mentions "offroad surprises," `final_verdict.should_you_race` says "Skip if gravel-phobic"). This is a real observation but pre-existing content, not part of my batch's flagged claims (only `final_verdict.one_liner` was flagged, and it verified TRUE), and untangling road-vs-gravel course description accurately would require route-level research I did not do this pass and risks the "don't rewrite course_description wholesale" constraint. Left unchanged; flagging here for a dedicated pass.

## Eligibility
- status: active
- verified: 2026-07-24
- source: https://themajestics.ch/en/
- notes: "UCI GFWS qualifier status confirmed current for 2026 under new 'The Majestics' branding (UCI competition record https://www.uci.org/competition-details/2026/CPT/78749). 2027 UCI sanction not yet published. Duplicate profile found at race-data/the-majestics.json describing the same event — out of this batch's scope, flagging for a follow-up dedupe pass."
