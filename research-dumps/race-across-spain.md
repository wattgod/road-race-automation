# Race Across Spain — Research Dump (Editorial Wave 4, 2026-07-24)

Research conducted via codex gpt-5.6-sol foreground web search, checked 2026-07-24.

## Bottom line

The existing profile mixed the inaugural 2025 route (Santander to Valencia) with the substantially changed 2026 edition. The 2026 route is **Águilas (Murcia) to Santander (Cantabria)** — the reverse direction and a different southern terminus entirely.

## 1. Route, distance, elevation, dates

- 2026 1,000 km route starts at the Auditorio y Palacio de Congresos in **Águilas, Murcia**, finishes at the Palacio de los Deportes in **Santander, Cantabria**. NOT Santander → Valencia (that was the 2025 inaugural route).
- 1,000 km class starts 20:00 on September 16; event concludes September 20, 2026. [Official page](https://en.raceacrossseries.com/race-across-spain-2025) (still hosted on the 2025 URL slug — confirmed current for 2026).
- Registration platform publishes **1,000 km and 14,000 m+** for all three 1000 km categories (solo/duo/team). [Miles Republic — official registration](https://fr.milesrepublic.com/event/race-across-spain-12384). No decimal-precision GPX distance published yet.
- Organizer distributes GPX files a few weeks before the race — do not invent a more precise decimal distance before that release.

## 2. Format, registration, fees, history

- **Semi-autonomous**, not fully unsupported: self-sufficient between staffed life-bases; outside assistance prohibited except at bases; public shops permitted; bases provide food/rest/showers/charging/bags. Every rider gets a GPS beacon; PGO (24h operational management post) monitors/assists. [Official rules, updated 3 Jun 2026](https://en.raceacrossseries.com/reglement); [official event page](https://en.raceacrossseries.com/race-across-spain-2025).
- Registration is public (not lottery) but the 1,000 km class is **qualification-validated**: applicants must show a recent Race Across finish or equivalent (e.g., 300 km within 24h); organizer validates 1000/2500 km entries no later than 30 days before the event. Registration opened 16 Oct 2025, closes 14 Sep 2026.
- 1,000 km fee schedule: Solo €289 priority / €309 standard / €359 last-chance; Duo €259/€279/€319 per rider; Team of 4 €249/€259/€309 per rider. Taxes included, platform fees extra. As of 24 Jul 2026 the registration page shows last-chance pricing.
- History: **2025 was the first Race Across Spain; 2026 is the second edition.** [Official series history](https://en.raceacrossseries.com/notre-histoire-2025) confirms. Registration page reports **150 participants in 2025** (across all distances — do not use as a 2026 field cap; no 2026 cap published).

## 3. Fixed course, not free routing

- **Fixed course.** Rules require riders to complete the organizer-defined course following the supplied GPS track — not a checkpoint event with rider-designed routing. GPX released shortly before the event. [Official rules](https://en.raceacrossseries.com/reglement).

## 4. Current 2026 status

- Active and scheduled: official 2026 calendar lists Sept 16-20 as the second edition; active registration link; official rules include 200/300/500/1000 km cutoffs; registration open until 14 Sep 2026. No cancellation/discontinuation indication. [Official 2026 calendar](https://en.raceacrossseries.com/nos-evenements-2026).

## 5. Signature climbs — 2025 route only, NOT confirmed for 2026

- Portillo de la Lunada, Puerto de Almedíjar, Puerto del Oronet, Sierra de la Demanda, Sierra Cebollera, Sierra de Gúdar-Javalambre are all real, organizer-published features — but they belong to the **2025 Santander → Riba-roja de Túria/Valencia route**. [2025 route article](https://en.raceacrossseries.com/blog/une-course-de-vlo-pique-travers-lespagne).
- The 2026 route is Águilas → Santander; the organizer had **not yet published a named-climb description or final public GPX** for that course as of this research. These climbs should be labeled 2025-route history, not presented as confirmed 2026 terrain — applied in course_description.suffering_zones.

## Database recommendation (applied 2026-07-24)

- distance_km 999.4 → 1000.0 (nominal); elevation_m 10668 → 14000
- location "Santander to Valencia" → "Águilas to Santander"
- date "2026: September 16" → "2026: September 16-20"
- field_size, entry_fee, cutoff_time, registration all populated from research (previously null)
- course_description rewritten to flag the 2025→2026 route reversal explicitly and demote the old named climbs to labeled 2025 history
- eligibility.notes documents the full correction chain

## Follow-up sol adversarial review correction (2026-07-24)

A second-pass sol review, verified via direct live-page browser check, caught that `climate.description` was never updated when the route was flipped: it still read "starting cool/green in Cantabria, warming to dry Mediterranean south" — describing the OLD 2025 Santander-to-Valencia direction. Since the corrected 2026 route runs Águilas (Mediterranean, south) to Santander (Atlantic, north) — the reverse — this sentence was backwards. Verified directly on https://en.raceacrossseries.com/race-across-spain-2025: the live page describes departure at Águilas and arrival at Santander, with generic "mild climate"/"Mediterranean ambience" wording and no route-specific temperature progression. climate.description corrected accordingly. Also softened "safer infrastructure than a pure unsupported race" to "more organizer-provided support and monitoring" per GOLD-register voice critique (unsupported comparative safety claim).
