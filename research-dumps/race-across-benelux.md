# Race Across Benelux (and the retired Race Across Belgium) — Research Dump (Editorial Wave 4, 2026-07-24)

Research conducted via codex gpt-5.6-sol foreground web search, checked 2026-07-24. This dump covers both race-across-benelux.json (canonical) and race-across-belgium.json (retired name, flagged catalog_flags.duplicate_of).

## The core question: same event renamed, or two distinct races?

**Verdict: SAME EVENT RENAMED/EXPANDED — 99% confidence**, per the official organizer's own language.

Race Across Belgium was the event's name from its inaugural 2021 edition through 2025. For 2026, the organizer renamed it Race Across Benelux and expanded the flagship course into the Netherlands and Luxembourg. There is no second, concurrently active Race Across Belgium on the official 2026 calendar.

## 1. Current official listing (checked 24 Jul 2026)

- [2026 Race Across Series calendar (FR)](https://www.raceacrossseries.com/nos-evenements-2026) lists **Race Across Benelux, May 27-31, 2026** and states: "La Race Across Belgium évolue et devient la Race Across Benelux."
- [English calendar](https://en.raceacrossseries.com/nos-evenements-2026) — same, Benelux only.
- Site destination navigation contains Race Across Benelux only, no separate Belgium destination.
- [Official 2026 rules](https://www.raceacrossseries.com/reglement) list Race Across Benelux, May 27-31, with 200/300/500/1,000 km classes. No separate Belgium event.
- Most decisive: the live [Race Across Benelux event page](https://www.raceacrossseries.com/race-across-belgique-2025) still occupies the **old `/race-across-belgique-2025` URL** and states outright: **"La Race Across Belgium change de nom et devient la Race Across Benelux."**

## 2. Event-name history

- **First edition: August 19, 2021.** [TV Lux report](https://www.tvlux.be/actu/sport/cyclisme/la-premiere-course-belge-d-ultra-cyclisme-est-partie-d-arlon-ce-jeudi-matin_38220) from the Arlon start: first Race Across Belgium, first Belgian ultra-cycling race, initially 300/600/1,000 km courses. Initiator: Michel Mussot.
- [Race Across Series official history](https://en.raceacrossseries.com/notre-histoire-2025) places Belgium's entry into the series calendar in 2021.
- May 2023 race independently confirmed as the **third edition** by [3bikes.fr (27 Apr 2023)](https://www.3bikes.fr/2023/04/27/la-race-across-belgium-3e-edition-du-rendez-vous-du-cyclisme-ultra-distance/).
- Still officially named Race Across Belgium in 2025: [organizer's retrospective (18 Sep 2025)](https://www.raceacrossseries.com/blog/une-course-de-vlo-mmorable-en-belgique-2025) describes the 2025 flagship as approximately **1,015 km and 7,200 m**, Arlon to Braine-l'Alleud.
- [2026-season announcement (20 Oct 2025)](https://natlawreview.com/press-releases/race-across-series-2026-registration-now-open) describes Race Across Benelux as "formerly Race Across Belgium," now expanded to Belgium, Netherlands and Luxembourg.
- [Regional announcement (2 Nov 2025)](https://www.info-lux.com/arlon-race-across-benelux/actualites/) — Race Across Belgium "leaves room for" Race Across Benelux, national → cross-border course.
- Rename occurred at the launch of the 2026 season, ~October-November 2025, effective with the May 2026 edition.

## 3. Confirmed 2026 flagship route and vitals

[Official detailed 2026 route post](https://www.raceacrossseries.com/blog/rab-2026-ultra-cycling-les-parcours):

| Field | Value |
|---|---|
| Dates | May 27-31, 2026 |
| Format | Amsterdam → Arlon → Arlon (point-to-point leg + Arlon loop) |
| Start | Amsterdam Olympic Stadium |
| Finish/base | Place Léopold, Arlon |
| Countries | Netherlands → Belgium → Luxembourg |
| Total distance | **1,048 km** (headline) |
| Total climbing | **~11,900 m D+** |
| Leg 1 | Amsterdam → Arlon: 533.5 km, ~4,700 m |
| Leg 2 | Arlon loop: 515.3 km, 7,165 m |

Internal inconsistencies noted in the source article itself: the two legs sum to 1,048.8 km vs the 1,048 km headline; a later section gives 533.5 km/7,206 m vs 533 km/7,165 m for the second loop in different places. Article also states routes remained subject to authorization/reconnaissance changes before final GPX release. **Defensible database values: 1,048 km / ~11,900 m, not the 999.4 km previously on file.**

## 4. Calendar vs legacy labels

- [Results archive](https://en.raceacrossseries.com/resultats-2026) still groups 2022-2026 under the historical heading "Race Across Belgium." Its 2026 entry opens the [timing event titled "Race Across Benelux 2026"](https://my.raceresult.com/399580/), dated May 27-31, 2026. This is legacy taxonomy continuity, not evidence of two races.

## Database recommendation (applied 2026-07-24)

- **race-across-benelux.json** is canonical: vitals corrected to 1,048 km / 11,900 m (elevation was already correct at 11,900 m; only distance_km was the placeholder error), full GOLD editorial written, catalog_flags taxonomy note added.
- **race-across-belgium.json** is retained as the historical record: catalog_flags.duplicate_of = "race-across-benelux", eligibility.status = "defunct" (name retired), vitals corrected from the placeholder duplicate (999.4/11,900, identical to Benelux) to the real final 2025 Belgium-only edition figures (1,015 km / 7,200 m, Arlon to Braine-l'Alleud) per the organizer's own 18 Sep 2025 retrospective. No new full editorial written on the duplicate, per established pipeline convention (see gfny-la-vaujany-alpe-dhuez.json precedent).

## Follow-up sol adversarial review corrections (2026-07-24)

A second-pass sol review, verified via direct live-page browser check, caught two blockers on race-across-benelux.json:

1. **entry_fee and cutoff_time were incorrectly left null/"not published."** Both are in fact published: the 2026 official rules (https://www.raceacrossseries.com/reglement) state the 1,000 km class has a 96-hour cutoff; the event page (https://www.raceacrossseries.com/race-across-belgique-2025) publishes solo 1,000 km pricing of EUR 289 (waiting list) / 309 (standard) / 359 (last-chance), taxes included, platform fees excluded. Both fields corrected.
2. **Prospective/future-tense wording was stale.** The 2026 edition ran May 27-31 and is now complete (today's check is 2026-07-24), but course_description, biased_opinion.weaknesses and final_verdict.should_you_race still described the route as "provisional until the final GPX ships" and advised riders to "confirm before training" — appropriate language for a future event, not a completed one. Reworded to past tense with an honest caveat: these were the organizer's pre-race published planning figures, and no post-event public final-GPX audit was found to confirm the exact ridden distance.
3. Softened "safer than a pure unsupported race" to "more organizer-provided support and monitoring" per GOLD-register voice critique (unsupported comparative safety claim), matching the same fix applied to race-across-spain.json.
