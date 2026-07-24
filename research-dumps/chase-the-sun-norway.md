# Research Dump: Chase the Sun Norway

## Quick Facts
- No organized cycling event named "Chase the Sun Norway," "Jag Sola," "Jage Sola," "Jakten på sola," or similar has ever existed under the real Chase the Sun organization or independently.
- The real Chase the Sun organizer (chasethesun.org) runs UK South (from 2008), UK North, Ireland, and Italia editions. Its 2026 results and route inventory list only these four — no Norway, and no historical Norway edition either.
- 2027 expansion is announced for Japan, not Norway.

## Identity check — FABRICATED / FRANKENSTEIN PROFILE
This profile is not a real event. It appears assembled by combining three unrelated real sources into a plausible-looking but non-existent Norwegian race:
1. **Distance/elevation (450.6 km / 3,300 m)**: copied from Chase the Sun Italia's real course (280 km / 3,300 m, Cesenatico–Tirrenia) — the 280 was misread as miles and converted to 450.6 km, producing the exact figure on file. This is a textbook unit-conversion hallucination.
2. **Date (June 20, 2026) and package details (grab-and-go snacks, mechanic, lunch, finish food, baggage service, ~17.5-hour riding window)**: copied from Chase the Sun UK North/South's real 2026 offerings (UK North's official window was 04:27-22:05, 17h38m, closely matching the profile's "~17.5 hours").
3. **Entry fee (£79 solo / £210 three-rider team)**: the exact 2026 UK North pricing.
4. **Location (Bergen to Kristiansand)**: a real geographic corridor — the Norwegian section of EuroVelo 12/Nordsjøruta, a cycle-touring route — but promoted for tourism, not as an organized one-day timed event. A published Bergen-Kristiansand cycling itinerary runs ~701 km over 8 days with 8,420 m of climbing and warns parts aren't suited to narrow road tires — nothing like a 450.6 km one-day paved event.

No Norwegian field-size data exists because no Norwegian edition exists; official 2026 results list 199 (Ireland), 595 (UK North), 1,063 (UK South), 210 (Italia) starters — no Norway line. The genuine Chase the Sun concept began in the UK in 2008 and describes its events as non-competitive challenges with no timing/ranking — so even the real editions are rides, not races.

## Dedupe determination
Not a duplicate of another slug in the corpus — this is a fabricated profile with no genuine underlying event to redirect to (distinct from the flandrien-ride precedent, where a real event existed under a different framing). Real, unrelated events with similar-sounding names: `haleakala-cycle-to-the-sun` (Hawaii climb, unrelated), `letape-norway` (real ASO event, unrelated), `midnight-sun-randonnee` (different Nordic ride, unrelated). None of these are the source of the fabrication — the source is Chase the Sun Italia + UK North, per above.

## Recommendation
Per sol's own recommendation: this should not be marked "cancelled" or "defunct" (both imply a real event once existed and later stopped). A first draft used a custom `eligibility.status: "fabricated"` value, but the wave-6 sol voice/fact review caught that this repo's own `scripts/eligibility_audit.py` and `qc/plan_readiness.py` both silently coerce any status outside `{active, defunct, cancelled, unknown}` back to `"unknown"` — so a non-enum value would not actually behave as a distinct status anywhere downstream, only create a false sense of one. Final treatment: `eligibility.status: "unknown"` (the real enum), with the full fabrication finding carried in `eligibility.notes`, `catalog_flags`, and `biased_opinion.verdict: "Fabricated Profile — No Real Event Exists"` (free text, not enum-constrained). `catalog_flags` recommends a human decide whether to delete the file outright (the research's own stated preference) or keep it flagged as a corrected data-integrity record, and notes that real tooling support for a fabricated/quarantine status would need a schema change outside this wave's scope.

## Sources
- Official Chase the Sun organizer — 2026 results (no Norway line): https://www.chasethesun.org/live/
- Official Chase the Sun route inventory: https://www.chasethesun.org/
- Official Chase the Sun Italia route page (source of the 280 km/3,300 m figures): https://www.chasethesun.org/italia/
- Official Chase the Sun UK North page (source of date, fee, package details): https://www.chasethesun.org/uk-north/
- Official Chase the Sun UK South page: https://www.chasethesun.org/uk-south/
- Official Chase the Sun historical records (event list by year/location, no Norway): https://www.chasethesun.org/records/
- EuroVelo 12 Norway section (real touring corridor, not an event): https://en.eurovelo.com/ev12/norway
- Komoot — North Sea Cycle Path Bergen-Kristiansand itinerary (701 km/8 days/8,420 m, contradicts profile's one-day paved claim): https://www.komoot.com/collection/376/the-north-sea-cycle-path-from-bergen-to-kristiansand
- timeanddate.com — Bergen sun table, June (daylight-hours check): https://www.timeanddate.com/sun/norway/bergen?month=6
- timeanddate.com — Kristiansand sun table, June: https://www.timeanddate.com/sun/norway/kristiansand?month=6

## Notes
Research conducted 2026-07-24 via codex gpt-5.6-sol foreground web search as part of the Roadie Labs editorial wave 6, batch A. This is a prior-wave-trap match: fabricated event, confirmed by cross-referencing every individual vitals field against real Chase the Sun sources and finding each one traces to a different real edition.
