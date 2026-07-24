# Research Dump: Gran Fondo Pirineus

Compiled 2026-07-24, editorial wave 5 (gpt-5.6-sol web search, foreground).

## Quick Facts
- Status: Active. Fourth consecutive edition ran June 28, 2026 in Camprodon (debuted July 2, 2023). No 2027 date published yet.
- Part of the three-event Gran Fondo 360 series.
- Three route lengths: 144 km/3,600m+ (long, includes Vallter 2000), 122 km/2,400m+ (medium, omits Vallter), 78 km/1,400m+ (short).
- Organizer's own regulations explicitly describe the event as NONCOMPETITIVE — roads stay open to traffic, no time lists produced — despite "gran fondo" branding and a finish-time format.

## Sources
- Gran Fondo 360 — official event page: https://www.granfondo360.com/gfpirineus (curl-verified 200, 2026-07-24)
- Official 2026 regulations PDF (noncompetitive status, cutoffs, entry): https://www.granfondo360.com/_files/ugd/f81f4e_8086550ee47a4be3bb37a831c9839c4f.pdf
- Official climb profiles by route length: https://www.granfondo360.com/puertosgfpirineos
- Federació Catalana de Ciclisme listing: https://www.ciclisme.cat/cursa/cicloturisme/gran-fondo-pirineus-0
- Onveló — first-edition (2023) participant report: https://www.onvelocycling.com/blog/marxa-cicloturista-gran-fondo-pirineos-1/
- RockTheSport — 2026 edition: https://www.rockthesport.com/es/evento/gran-fondo-pirineus-2026

## Course
Long route (144km): Coll de Capsacosta, Coll de Pera, Santigosa, Coll de Rocabruna, and Vallter 2000 from Setcases (~12km @ 7.18% avg, 14% max, ~900m gain) — the signature/hardest climb, exclusive to the long route. Medium (122km) omits Vallter. Short (78km) covers just Pera and Rocabruna. Route through Vall del Bac, Oix, Beget.

## Format check — noncompetitive, flagged via catalog_flags
Regulations explicitly state noncompetitive status: open roads, no time lists. "Race" framing in casual marketing is tolerable; presenting it as a timed competitive gran fondo would be dishonest. discipline left as "gran_fondo" per standing rule (never silently change discipline) — flagged in catalog_flags instead, consistent with flandrien-ride.json precedent.

## Data-quality corrections applied to race-data/gran-fondo-pirineus.json this wave
- distance_km: 143.2 -> 144 (organizer/federation both publish 144km; 143.2 looks like a GPX-track measurement)
- cutoff_time: "4 hours (must finish by 4:00 PM)" -> actual ~8hr window (08:00 start / 16:00 close) for long/medium routes — the on-file figure was simply wrong
- field_size: "N/A" -> null (2024 attendance reporting conflicts by source, 600 vs 1,000+; no reliable 2026 figure exists)
- Purged two YouTube videos (Cycl'n Vancouver "Ride 443"/"Ride 444") and their derived rider_intel — cross-race mislabeled content describing a personal multi-day Girona-Pyrenees-Costa Brava tour, not the organized Gran Fondo Pirineus event
- Removed the unsourced "SCOTT-sponsored" claim from final_verdict.one_liner (no source found)
- Field-size conflict correctly attributed: Generalitat de Catalunya (govern.cat, Jan 2026) reports 600 participants for the 2024 edition; Blanquerna (blanquerna.edu) independently reports over 1,000 for the same 2024 edition. (The Onvelo report separately covers 600+ riders at the 2023 debut — do not conflate the two.)
- Sol review (2026-07-24) flagged the initial "Marketed as a Race It Isn't" verdict framing as overstated accusation given the organizer is transparent about noncompetitive status in its own regulations — softened to "Openly Noncompetitive."
