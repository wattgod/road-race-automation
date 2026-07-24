# Race Across Germany — Research Dump (Editorial Wave 4, 2026-07-24)

Research conducted via codex gpt-5.6-sol foreground web search, checked 2026-07-24 (post-event).

## 1. Organizer identity — NOT Race Across Series

- The [Race Across Germany Impressum](https://raceacrossgermany.de/impressum) names **ULTRAGRÜN GmbH**, Altenauer Straße 35, Clausthal-Zellerfeld, represented by managing director **Fritz Geers**. German register number HRB 207190, VAT ID DE318227162.
- The [Race Across Series legal notice](https://www.raceacrossseries.com/mentionslegales) instead identifies **Across and Beyond Endurance AG**, Switzerland, represented by **Arnaud Manzanini**. Its [2026 event list](https://en.raceacrossseries.com/) includes Portugal, Paris, Benelux, France, GRAAALPS, Switzerland, Québec and Spain — **Germany is absent**.
- Race Across Germany's own homepage says no large agency is behind the event, describing a small team of experienced ultracyclists.
- **Conclusion: Race Across Germany shares only a naming convention with race-across-france.json, race-across-spain.json and race-across-benelux.json — it is a completely separate organizer, not part of the Race Across Series.**

## 2. 2026 route, dates, format

- Route: Flensburg to Garmisch-Partenkirchen. Dates: **2-5 July 2026**.
- Official canonical vitals: **1,100 km / 7,500 m** — published consistently on the [official homepage](https://raceacrossgermany.de/).
- Staggered starts: 2 July 18:00-18:58 and 3 July 07:00-11:18, up to two solo riders or one team every two minutes.
- Official time stations: Lauenburg, Bilderlahe, Berka, Kitzingen, Mauren, Moorenweis.
- **Fixed course, not rider-chosen routing.** The [nonsupported rules](https://raceacrossgermany.de/nonsupported) and [supported rules](https://raceacrossgermany.de/supported) require riders to follow the organizer-provided route in full; deviations permitted only for closures/accidents/construction, with shortest return to the prescribed course required. GPS evidence required; deliberate shortcuts penalized.
- Written briefing arrives ~4 weeks before; final GPX ~1 week before the start (not 4 weeks as previously on file).
- Support format: **Nonsupported** (genuinely self-supported — no private crew/caches, resupply only via public services) or **Supported** (rider's own crew/vehicle). This is NOT the Race Across Series "staffed life-base" semi-autonomy model — no staffed food/sleep bases at time stations.

## 3. German Ultracycling Championships + RAAM Qualifier

- Official 2026 event page states Flensburg-Garmisch hosted the **2026 German Ultracycling Championships** (Solo Supported and Solo Nonsupported), awarded by age category. [2026 results](https://raceacrossgermany.de/finisher?race=2026-flensburg-garmisch) mark riders "Deutscher Meister 2026" (Sebastian Mayr, Stefan Rüther, Sascha Hubbert, Niels Piecha, Lisa Brömmel, others).
- Independent recognition: on 8 July 2026, Radsportverband Schleswig-Holstein (radsport-sh.de, a Bund Deutscher Radfahrer member) reported Britta Wilms as German champion.
- No independent German Cycling/BDR national championship technical guide or calendar entry found sanctioning the event at the federation level — safe phrasing is "hosted the German Ultracycling Championships," not "the official German Cycling/UCI national championship."
- **RAAM qualifier: firmly verified.** [World UltraCycling Association 2026 calendar](https://ultracycling.com/venue/race-start/?eventDisplay=past) explicitly categorizes Race Across Germany N-S as a RAAM Qualifier. Official event page publishes category-specific qualifying time limits (48-51h supported solo, 49-52h nonsupported solo). 2026 results mark "RAAM Qualified" status per rider.

## 4. Registration, fee, field size

- Registration: public but document-request based via the [participation page](https://raceacrossgermany.de/teilnahme) (name/email/year/route/message request). No selection criteria or résumé requirement found — open enrollment, not curated application.
- Entry fee: no exact public 2026 figure found; fees vary by category/registration date, shown only during registration. Left null in the database rather than estimated.
- Capacity: official 2026 cap **300 slots** Flensburg-Garmisch, **50 slots** Eschwege-Garmisch (from [2026 event listing](https://raceacrossgermany.de/en/north-south)).
- 2026 live-tracking feed reported **236 starters** on the long-course field (secondary/tracking-derived figure, not an audited static count).
- 2025 comparison: [NDR (11 Jul 2025)](https://www.ndr.de/nachrichten/schleswig-holstein/radrennen-durch-deutschland-von-flensburg-in-sueden%2Cregionflensburgnews-300.html) reported 142 solo entrants and relay teams.

## 5. Shorter route confirmed active for 2026

- **Eschwege-Garmisch / "Bavaria Extrem"**: 4-5 July 2026, 550 km, 4,100 m elevation gain, max 50 slots, shares the southern portion and four time stations (Berka, Kitzingen, Mauren, Moorenweis) with the flagship but is a separately entered distance.

## 6. Vitals correction

- Organizer canonical: **1,100 km / 7,500 m** (used as core database vitals — 1,099.2 km on file was false precision from a mi→km back-conversion of the rounded 683-mile figure).
- Post-race edition-specific measurement: [Radsportverband Schleswig-Holstein (8 Jul 2026)](https://www.radsport-sh.de/) described the completed 2026 course as **1,129 km / 7,800 m**; a post-race report on Sebastian Mayr stated 1,128 km. GPS elevation totals vary more by device/correction method.
- History correction: official site says the event dates to **1999**, not 2010 as previously on file.

## Database recommendation (applied 2026-07-24)

- distance_km 1099.2 → 1100.0; elevation_m unchanged at 7500
- history.founded 2010 → 1999
- Added route_options: flagship + Eschwege-Garmisch/Bavaria Extrem 550km option
- Documented organizer-vs-Race-Across-Series disambiguation prominently in history.origin_story, biased_opinion, and eligibility.notes
- Documented German Championships (careful phrasing) + verified RAAM-qualifier status
- Left entry_fee null (no public figure found)

## Follow-up sol adversarial review corrections (2026-07-24)

A second-pass sol review caught two blockers, verified against the live site with browser control:

1. **Cutoff time was mislabeled.** The initial draft's cutoff_time field (48-51h/49-52h) actually described the faster RAAM-qualifying time limits, not the true overall finisher/classification cutoffs, which are longer: Supported M50- 56h/48h (classification/RAAM), M50+ 57h/49h, M60+ 58h/50h; F50- 57h/49h, F50+ 58h/50h, F60+ 59h/51h. Nonsupported M50- 57h/49h, M50+ 58h/50h, M60+ 59h/51h; F50- 58h/50h, F50+ 59h/51h, F60+ 60h/52h. Source: https://raceacrossgermany.de/en/north-south (verified via live browser check).
2. **The site had rolled forward to the next edition.** As of 2026-07-24 the official "Next date" is July 8-11, 2027 (registration opens 27 May 2026) — the 2026 edition (July 2-5) is complete. date/date_specific fields updated accordingly.
3. Citation URL fixed: /finisher?race=... → /en/finishers?race=... (correct path).
4. Added a direct citation for the post-race ~1,129 km/7,800 m distance claim (previously asserted without a matching citation): https://rst-luebeck.de/ultradistanz/race-across-germany-2026-britta-wilms-wieder-deutsche-meisterin/
5. Softened "not a marketing claim" / "real...not a marketing claim" phrasing per GOLD-register voice critique (defensive-adjacent).
