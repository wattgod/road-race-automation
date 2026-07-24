# Research Dump: Gran Fondo Samoëns / "Gran Fondo & Ultra Raid Samoëns"

## Quick Facts
- "Gran Fondo & Ultra Raid" is a **tourism-office umbrella listing** (samoens.com/gran-fondo-ultra-raid/) for a shared weekend, branded "Baroudeurs des Alpes," bundling TWO separate, differently-organized events with separate official sites, courses, and results:
  1. **Gran Fondo Samoëns – Montagnes du Giffre** (road cycling, granfondo-samoens.com)
  2. **Ultra Raid Samoëns – Grand Massif** (high-mountain MTB stage race, distinct organizer relationship via ultra-raid-series.com)
- 2026 was the **inaugural edition** for both (per organizer registration copy and press interviews) — not an established multi-year event.
- Status: active/held. The 2026 edition ran and completed; results were published; a 2027 edition (June 4-6, 2027) is already listed by the Samoëns tourism office.
- Legal organizer: ULTRA RAID ASBL (Belgian nonprofit; Ultra Raid Series rules reference ASBL URD3V), with the Samoëns Office de Tourisme as local host/volunteer coordinator.

## Road event: Gran Fondo Samoëns (the actual road-cycling product)
A genuine competitive road cyclosportive, but its flagship concept is a **two-day stage format with a combined general classification** — riders can enter Saturday only, Sunday only, or both days for the GC.

| Option | 2026 distance/climbing | Route |
|---|---|---|
| Gran Fondo, Saturday | 130 km / 3,800 m D+ | Samoëns → Joux Plane → Joux Verte/Avoriaz → Col de la Ramaz → finish Le Praz-de-Lys |
| Gran Fondo, Sunday | 155 km / 4,300 m D+ | Samoëns → Les Esserts → summit finish Samoëns 1600 |
| Two-day combined | 285 km / 8,100 m D+ | Sum of both stages, combined GC |
| Medio Fondo, Saturday | 85 km / 3,000 m D+ | Joux Plane, Joux Verte, La Ramaz; Samoëns → Le Praz-de-Lys |
| Medio Fondo, Sunday | 112 km / 3,000 m D+ | Samoëns → Samoëns 1600 |
| Medio two-day combined | 197 km / 6,000 m D+ | Sum of both Medio stages |

- Surface: paved mountain roads throughout, courses partially open to normal traffic with normal road-code obligations and selected closures — no gravel/MTB component in the Gran Fondo routes.
- 2026 entry fees: two-day Gran Fondo €115/€125/€140 (tiered by registration date); one-day Gran Fondo €60/€70/€80; two-day Medio €95/€105/€120; one-day Medio €50/€60/€70.
- Field size: no consolidated organizer total published. A partial results file shows 62 ranked Saturday-stage finishers, but that excludes Medio/ride-libre/Sunday-only entrants — not a usable total field figure.
- Road event ran **June 6-7, 2026** (not June 5, which belongs to the separate Ultra Raid).

## Ultra Raid Samoëns (separate MTB event — NOT part of this road profile)
A three-day XC-marathon/MTB stage raid, solo and duo classifications, technical alpine mountain biking (natural singletrack, bike-park/enduro-style sections) — explicitly "Mountain Bike only" per Trailforks' route classification. NOT gravel, NOT road.

| Format | Published stages | Total |
|---|---|---|
| Ultra 4000 | 25/35/30 km | 90 km / 3,500 m |
| Ultra 5000 | 25/60/50 km | 135 km / 5,500 m |
| Ultra 7000 | 25/75/75 km | 175 km / 7,200 m |
| Ultra Ultime (Sat only) | single stage | 125 km / 6,700 m |

Ran June 5-7, 2026. This is a wholly separate event from the road Gran Fondo — different courses, different surface (MTB trail vs. paved road), and the timing company (ARTIMING) treats them as two distinct results sets.

## Taxonomy / identity finding — the previous database record conflated the two
- The prior stored vitals (173.8 km / 5,000 m, "June 5-7," surface "Paved roads" over "Mixed terrain") matched **neither** the road Gran Fondo (max verified 285 km two-day / 155 km one-day) **nor** the MTB Ultra Raid (closest is Ultra 7000 at 175 km/7,200 m, or Ultra 5000 at 135 km/5,500 m) cleanly — it appears to be an averaged/garbled merge of the two separate events under one profile.
- This profile is corrected to describe **only the road Gran Fondo Samoëns** — the event that actually belongs in a road-cycling database. The Ultra Raid MTB event is out of scope for Roadie Labs entirely and should not be represented in this profile's vitals.
- Taxonomy flag (per pipeline policy, discipline enum not changed): the road Gran Fondo's own flagship format is a **two-day stage cyclosportive with combined GC**, which sits closer to `multi_stage` than a standard single-day `gran_fondo`. Flagged in `catalog_flags`, `fondo_rating.discipline` left as `gran_fondo` per policy.
- Identity flag: `race.name`/`display_name` previously read "Gran Fondo & Ultra Raid Samoëns," which is the tourism-umbrella branding, not the actual road event's own name. Corrected to "Gran Fondo Samoëns – Montagnes du Giffre" (the organizer's own event name) following the flandrien-ride.json precedent — slug left unchanged to preserve the existing URL.

## Dedupe determination
No duplicate slug in the existing 425-race corpus for either "Gran Fondo Samoëns" or "Ultra Raid Samoëns" alone — this is a single profile that needed an internal identity/taxonomy correction, not a cross-file dedupe case.

## Sources
- Official Samoëns tourism umbrella listing: https://www.samoens.com/gran-fondo-ultra-raid/
- Official Gran Fondo Samoëns site: https://www.granfondo-samoens.com/
- Official Gran Fondo course page: https://www.granfondo-samoens.com/gran-fondo-item
- Official Medio Fondo course page: https://www.granfondo-samoens.com/gran-fondo-item-1
- Official Gran Fondo registration/pricing: https://www.granfondo-samoens.com/registrations
- Official Gran Fondo terms (organizer of record: ULTRA RAID ASBL): https://www.granfondo-samoens.com/terms-and-conditions
- Baroudeurs des Alpes event hub (both events split out): https://www.baroudeursdesalpes.com/les-courses
- Regional destination agenda (Gran Fondo fees/dates): https://destination-montagnesdugiffre.fr/agenda/baroudeurs-des-alpes-gran-fondo-samoens-montagnes-du-giffre/
- Regional destination agenda (Ultra Raid stages/fees): https://destination-montagnesdugiffre.fr/agenda/baroudeurs-des-alpes-ulra-raid-samoens-grand-massif/
- Published Saturday-stage classification (62 finishers): https://www.velo-ouest.com/saison-2026/resultats-2026/cyclosportive-granfondo-samoens.html
- Ultra Raid Series rules (ASBL URD3V): https://www.ultra-raid-series.com/copie-de-r%C3%A9glement
- Trailforks Ultra Raid route classification ("Mountain Bike only"): https://www.trailforks.com/event/20167/
- ARTIMING 2026 event list (separate results entries): https://artiming.com/fr/course-2026/
- Ultra Raid 2026 recap (Vojo Mag): https://www.vojomag.nl/ultra-raid-samoens-2026-met-pretlichtjes-in-de-ogen-pijn-in-de-benen/
- 2027 edition listing (June 4-6): https://www.samoens.com/baroudeurs-des-alpes/

## Notes
Research conducted 2026-07-24 via codex gpt-5.6-sol foreground web search as part of the Roadie Labs editorial wave 6 (batch D). This is the assigned "ultra/raid" taxonomy-flag case for this batch per the wave dispatch instructions.
