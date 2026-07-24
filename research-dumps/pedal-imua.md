# pedal-imua — editorial wave 5 research evidence (2026-07-24)

Source: codex gpt-5.6-sol foreground web research, log: ed5_d_pedal-imua_research.log

## Bottom line

**Status: active, with the exact 2026 date still provisional.** Pedal IMUA is not defunct and is not a product category. The strongest current listing is the Aloha State Bicycle Racing Association calendar, which schedules it for **Saturday, December 5, 2026 at 7:00 a.m. in Kahului**. A second cycling-team calendar also says December 5. [ASBRA 2026 calendar](https://asbra.org/calendar/), [Tradewind Cycling Team calendar](https://tradewindcyclingteam.com/ride-calendar)

There is a genuine date conflict: Gran Fondo World Tour says **December 6, 2026**, while Hawai‘i Bicycling League prints “12/6 (SAT)”—but December 6 is Sunday. Meanwhile, the organizer’s own page is stale and still calls December 6, 2025 the “next” event. [Gran Fondo World Tour](https://www.granfondoworldtour.com/), [HBL statewide calendar](https://hbl.org/lets-ride/events-across-hawaii/), [official Pedal IMUA page](https://discoverimua.com/pedal/)

Therefore:

- Keep `eligibility.status=active`.
- Keeping `date=2026: December TBD` is defensible until Discover Imua updates its page.
- If you store a provisional date, use **2026-12-05**, marked unconfirmed by the organizer.
- **Most recent confirmed edition: December 6, 2025.** A post-event foundation recap shows the 2025 start, and a participant report records completion of 63.37 miles around West Maui. [Stable Road Foundation 2025 recap](https://www.stableroadfoundation.org/year-end-wrap-2025), [Saint Louis School participant report](https://saintlouishawaii.org/pdf/weeklyBulletinArchive/2025-2026/Saint%20Louis%20Dec15%202025.pdf)
- **Single best current-status source:** [https://asbra.org/calendar/](https://asbra.org/calendar/)

## Course and profile audit

| Profile field | Evidence and recommended treatment |
|---|---|
| Location | “Maui, Hawaii, USA” is correct but imprecise. The 2025 event started and finished at Imua Family Services, **161 S. Wakea Avenue, Kahului**, and the ASBRA 2026 listing again says Kahului. Earlier editions used Wailuku, so the venue has changed. [2025 registration page](https://secure.qgiv.com/for/pedalimua2025/event/pedalimua2025/), [ASBRA](https://asbra.org/calendar/) |
| Full distance | The organizer advertises **100 km / 60 miles**; it also offers a **50 km / 30-mile half ride**. Your 99.8 km/62 mi is a reasonable metric-century conversion, not a serious error, although it does not match the organizer’s advertised 60-mile label. A 2025 participant recorded 63.37 miles, showing that GPS/start-position totals can be longer. [Official ride details](https://discoverimua.com/pedal/), [2025 participant report](https://saintlouishawaii.org/pdf/weeklyBulletinArchive/2025-2026/Saint%20Louis%20Dec15%202025.pdf) |
| Route options | The empty `route_options` is wrong/incomplete. Add full **100 km/60 mi** and half **50 km/30 mi** routes; both permit e-bikes. [Official ride details](https://discoverimua.com/pedal/) |
| Elevation | **The current 5,800 ft / 1,768 m is unsupported and materially too high.** The organizer publishes **4,173 ft**, approximately **1,272 m**. Battistrada independently lists roughly 4,100 ft/1,250 m. A 2025 participant recorded 4,752 ft, plausibly reflecting GPS and route variation, but no credible source found supports 5,800 ft. Use **4,173 ft / 1,272 m** as the official vital. [Official ride details](https://discoverimua.com/pedal/), [Battistrada 2025 route](https://battistrada.com/en/cycling-calendar/edition/pedal-imua-gran-fondo-2025/45169/), [2025 participant report](https://saintlouishawaii.org/pdf/weeklyBulletinArchive/2025-2026/Saint%20Louis%20Dec15%202025.pdf) |
| Route | It circles the West Maui Mountains, passing through **Lahaina and Kahakuloa**. The inaugural edition ran clockwise; do not assume that direction is permanently fixed without a current route file. [2025 registration page](https://secure.qgiv.com/for/pedalimua2025/event/pedalimua2025/), [2019 event report](https://www.mauinews.com/news/local-news/2019/12/cyclists-help-make-dreams-come-true/) |
| Climbs | This is rolling, punchy coastal climbing rather than one long mountain pass. The West Maui Loop’s best-known steep feature is locally called **“Mr. Steepy,”** and clockwise riding makes its uphill sections steeper. First-person Pedal IMUA footage also describes several short, steep northern climbs and narrow-road sections. [West Maui Cycles route description](https://www.westmauicycles.com/blog/2014/1/17/the-best-maui-road-bike-rides-the-west-maui-loop), [2023 participant video](https://www.youtube.com/watch?v=vV0Ij-0DhsQ) |
| Surface | `terrain.surface=Paved roads` is correct. This is a road-bike route on paved public highways, although Kahekili Highway includes narrow, rough, sometimes single-lane pavement with little shoulder. It is **not mixed-surface in the gravel sense**. [West Maui Cycles](https://www.westmauicycles.com/blog/2014/1/17/the-best-maui-road-bike-rides-the-west-maui-loop), [current West Maui Loop road description](https://www.komoot.com/smarttour/e1369592914/boucle-de-west-maui-via-honoapi-ilani-highway-comte-de-maui) |
| Field size | Use approximately **100 riders**, not a hard capacity. The inaugural ride registered about 100; organizers expected more than 100 in 2023; and the 2025 road advisory said nearly 100 cyclists. No current entry cap was published. [2019 report](https://www.mauinews.com/news/local-news/2019/12/cyclists-help-make-dreams-come-true/), [2023 announcement](https://mauinow.com/2023/10/29/fifth-annual-pedal-imua-announces-60-mile-bike-ride-around-west-maui-mountains/), [2025 road advisory](https://mauinow.com/2025/12/05/road-advisory-6th-annual-pedal-imua-takes-place-saturday-morning/) |
| Start/road format | Historically it used a **7:00 a.m. mass start**. More recent instructions require riders to remain on the right side of open highways, obey normal traffic laws, and finish by noon. This is not a closed-road race. [Inaugural ride announcement](https://mauinow.com/2019/10/04/inaugural-pedal-imua-gran-fondo-benefit-planned/), [2025 road advisory](https://mauinow.com/2025/12/05/road-advisory-6th-annual-pedal-imua-takes-place-saturday-morning/) |
| Support | Hydration/rest stops, food zones, bicycle support, a tail vehicle and post-ride brunch are provided. It is therefore not self-supported. [Official ride details](https://discoverimua.com/pedal/) |
| Eligibility | Open to all ages; minors require a parent or guardian’s waiver. E-bikes are accepted on both distances. Remote participation is offered as an additional option. [Official ride details](https://discoverimua.com/pedal/) |
| Entry fee | For 2025, registration was **$100 before Thanksgiving or $125 on the day**, subject to availability. Do not reuse this as the 2026 price until registration is updated. [2025 registration page](https://secure.qgiv.com/for/pedalimua2025/event/pedalimua2025) |
| Founded | **`founded=2016` is wrong. Pedal IMUA launched in 2019.** Contemporary sources explicitly call the December 1, 2019 event the first/inaugural Pedal IMUA Gran Fondo. The 2016 date likely came from the much older Paddle IMUA event. [2019 launch announcement](https://mauinow.com/2019/10/04/inaugural-pedal-imua-gran-fondo-benefit-planned/), [inaugural-event report](https://www.mauinews.com/news/local-news/2019/12/cyclists-help-make-dreams-come-true/) |

The annual numbering is messy: both the 2024 announcement and 2025 registration called their event the “sixth annual.” Store the 2019 founding year and actual dates rather than asserting an edition number. [2024 announcement](https://mauinow.com/2024/11/26/registration-now-open-for-6th-annual-pedal-imua-on-dec-7/), [2025 registration](https://secure.qgiv.com/for/pedalimua2025/event/pedalimua2025)

## Format verdict

**Best classification: a supported, mass-participation, non-competitive charity road gran fondo/sportive.** `discipline=gran_fondo` is honest if your database includes gran fondo-style rides. Calling it a competitive “race” would be misleading: participants ride on open roads under ordinary traffic rules, e-bikes and a half route are accepted, and the published materials emphasize support, fundraising and brunch rather than timing, categories, winners or results. [Official page](https://discoverimua.com/pedal/), [2025 road advisory](https://mauinow.com/2025/12/05/road-advisory-6th-annual-pedal-imua-takes-place-saturday-morning/)

It is:

- Not a self-supported ultra.
- Not a paid cycling tour or travel package.
- Not virtual-only—the remote challenge is an optional parallel participation method.
- Not MTB or gravel.
- Not a family of products masquerading as one race.

Gran Fondo World Tour currently displays Pedal IMUA under a “Gravel” card, but that is evidently bad catalog metadata. **Aloha Gravel** is the separate gravel/singletrack event held the preceding weekend; its own organizer explicitly distinguishes it from the later Pedal IMUA road gran fondo. [Gran Fondo World Tour](https://www.granfondoworldtour.com/), [Aloha Gravel announcement](https://www.alohagravel.com/blog/announcement-aloha-gravel-on-maui-all-proceeds-from-new-graveloff-road-cycling-event-to-benefit-imua-family-services)

Recommended core corrections: change founded year to **2019**, replace elevation with **1,272 m / 4,173 ft**, add the **50 km/30 mi** route, keep the surface paved, describe the field as roughly **100**, and use “charity gran fondo/ride” rather than “race.”
tokens used
147,634
## Bottom line

**Status: active, with the exact 2026 date still provisional.** Pedal IMUA is not defunct and is not a product category. The strongest current listing is the Aloha State Bicycle Racing Association calendar, which schedules it for **Saturday, December 5, 2026 at 7:00 a.m. in Kahului**. A second cycling-team calendar also says December 5. [ASBRA 2026 calendar](https://asbra.org/calendar/), [Tradewind Cycling Team calendar](https://tradewindcyclingteam.com/ride-calendar)

There is a genuine date conflict: Gran Fondo World Tour says **December 6, 2026**, while Hawai‘i Bicycling League prints “12/6 (SAT)”—but December 6 is Sunday. Meanwhile, the organizer’s own page is stale and still calls December 6, 2025 the “next” event. [Gran Fondo World Tour](https://www.granfondoworldtour.com/), [HBL statewide calendar](https://hbl.org/lets-ride/events-across-hawaii/), [official Pedal IMUA page](https://discoverimua.com/pedal/)

Therefore:

- Keep `eligibility.status=active`.
- Keeping `date=2026: December TBD` is defensible until Discover Imua updates its page.
- If you store a provisional date, use **2026-12-05**, marked unconfirmed by the organizer.
- **Most recent confirmed edition: December 6, 2025.** A post-event foundation recap shows the 2025 start, and a participant report records completion of 63.37 miles around West Maui. [Stable Road Foundation 2025 recap](https://www.stableroadfoundation.org/year-end-wrap-2025), [Saint Louis School participant report](https://saintlouishawaii.org/pdf/weeklyBulletinArchive/2025-2026/Saint%20Louis%20Dec15%202025.pdf)
- **Single best current-status source:** [https://asbra.org/calendar/](https://asbra.org/calendar/)

## Course and profile audit

| Profile field | Evidence and recommended treatment |
|---|---|
| Location | “Maui, Hawaii, USA” is correct but imprecise. The 2025 event started and finished at Imua Family Services, **161 S. Wakea Avenue, Kahului**, and the ASBRA 2026 listing again says Kahului. Earlier editions used Wailuku, so the venue has changed. [2025 registration page](https://secure.qgiv.com/for/pedalimua2025/event/pedalimua2025/), [ASBRA](https://asbra.org/calendar/) |
| Full distance | The organizer advertises **100 km / 60 miles**; it also offers a **50 km / 30-mile half ride**. Your 99.8 km/62 mi is a reasonable metric-century conversion, not a serious error, although it does not match the organizer’s advertised 60-mile label. A 2025 participant recorded 63.37 miles, showing that GPS/start-position totals can be longer. [Official ride details](https://discoverimua.com/pedal/), [2025 participant report](https://saintlouishawaii.org/pdf/weeklyBulletinArchive/2025-2026/Saint%20Louis%20Dec15%202025.pdf) |
| Route options | The empty `route_options` is wrong/incomplete. Add full **100 km/60 mi** and half **50 km/30 mi** routes; both permit e-bikes. [Official ride details](https://discoverimua.com/pedal/) |
| Elevation | **The current 5,800 ft / 1,768 m is unsupported and materially too high.** The organizer publishes **4,173 ft**, approximately **1,272 m**. Battistrada independently lists roughly 4,100 ft/1,250 m. A 2025 participant recorded 4,752 ft, plausibly reflecting GPS and route variation, but no credible source found supports 5,800 ft. Use **4,173 ft / 1,272 m** as the official vital. [Official ride details](https://discoverimua.com/pedal/), [Battistrada 2025 route](https://battistrada.com/en/cycling-calendar/edition/pedal-imua-gran-fondo-2025/45169/), [2025 participant report](https://saintlouishawaii.org/pdf/weeklyBulletinArchive/2025-2026/Saint%20Louis%20Dec15%202025.pdf) |
| Route | It circles the West Maui Mountains, passing through **Lahaina and Kahakuloa**. The inaugural edition ran clockwise; do not assume that direction is permanently fixed without a current route file. [2025 registration page](https://secure.qgiv.com/for/pedalimua2025/event/pedalimua2025/), [2019 event report](https://www.mauinews.com/news/local-news/2019/12/cyclists-help-make-dreams-come-true/) |
| Climbs | This is rolling, punchy coastal climbing rather than one long mountain pass. The West Maui Loop’s best-known steep feature is locally called **“Mr. Steepy,”** and clockwise riding makes its uphill sections steeper. First-person Pedal IMUA footage also describes several short, steep northern climbs and narrow-road sections. [West Maui Cycles route description](https://www.westmauicycles.com/blog/2014/1/17/the-best-maui-road-bike-rides-the-west-maui-loop), [2023 participant video](https://www.youtube.com/watch?v=vV0Ij-0DhsQ) |
| Surface | `terrain.surface=Paved roads` is correct. This is a road-bike route on paved public highways, although Kahekili Highway includes narrow, rough, sometimes single-lane pavement with little shoulder. It is **not mixed-surface in the gravel sense**. [West Maui Cycles](https://www.westmauicycles.com/blog/2014/1/17/the-best-maui-road-bike-rides-the-west-maui-loop), [current West Maui Loop road description](https://www.komoot.com/smarttour/e1369592914/boucle-de-west-maui-via-honoapi-ilani-highway-comte-de-maui) |
| Field size | Use approximately **100 riders**, not a hard capacity. The inaugural ride registered about 100; organizers expected more than 100 in 2023; and the 2025 road advisory said nearly 100 cyclists. No current entry cap was published. [2019 report](https://www.mauinews.com/news/local-news/2019/12/cyclists-help-make-dreams-come-true/), [2023 announcement](https://mauinow.com/2023/10/29/fifth-annual-pedal-imua-announces-60-mile-bike-ride-around-west-maui-mountains/), [2025 road advisory](https://mauinow.com/2025/12/05/road-advisory-6th-annual-pedal-imua-takes-place-saturday-morning/) |
| Start/road format | Historically it used a **7:00 a.m. mass start**. More recent instructions require riders to remain on the right side of open highways, obey normal traffic laws, and finish by noon. This is not a closed-road race. [Inaugural ride announcement](https://mauinow.com/2019/10/04/inaugural-pedal-imua-gran-fondo-benefit-planned/), [2025 road advisory](https://mauinow.com/2025/12/05/road-advisory-6th-annual-pedal-imua-takes-place-saturday-morning/) |
| Support | Hydration/rest stops, food zones, bicycle support, a tail vehicle and post-ride brunch are provided. It is therefore not self-supported. [Official ride details](https://discoverimua.com/pedal/) |
| Eligibility | Open to all ages; minors require a parent or guardian’s waiver. E-bikes are accepted on both distances. Remote participation is offered as an additional option. [Official ride details](https://discoverimua.com/pedal/) |
| Entry fee | For 2025, registration was **$100 before Thanksgiving or $125 on the day**, subject to availability. Do not reuse this as the 2026 price until registration is updated. [2025 registration page](https://secure.qgiv.com/for/pedalimua2025/event/pedalimua2025) |
| Founded | **`founded=2016` is wrong. Pedal IMUA launched in 2019.** Contemporary sources explicitly call the December 1, 2019 event the first/inaugural Pedal IMUA Gran Fondo. The 2016 date likely came from the much older Paddle IMUA event. [2019 launch announcement](https://mauinow.com/2019/10/04/inaugural-pedal-imua-gran-fondo-benefit-planned/), [inaugural-event report](https://www.mauinews.com/news/local-news/2019/12/cyclists-help-make-dreams-come-true/) |

The annual numbering is messy: both the 2024 announcement and 2025 registration called their event the “sixth annual.” Store the 2019 founding year and actual dates rather than asserting an edition number. [2024 announcement](https://mauinow.com/2024/11/26/registration-now-open-for-6th-annual-pedal-imua-on-dec-7/), [2025 registration](https://secure.qgiv.com/for/pedalimua2025/event/pedalimua2025)

## Format verdict

**Best classification: a supported, mass-participation, non-competitive charity road gran fondo/sportive.** `discipline=gran_fondo` is honest if your database includes gran fondo-style rides. Calling it a competitive “race” would be misleading: participants ride on open roads under ordinary traffic rules, e-bikes and a half route are accepted, and the published materials emphasize support, fundraising and brunch rather than timing, categories, winners or results. [Official page](https://discoverimua.com/pedal/), [2025 road advisory](https://mauinow.com/2025/12/05/road-advisory-6th-annual-pedal-imua-takes-place-saturday-morning/)

It is:

- Not a self-supported ultra.
- Not a paid cycling tour or travel package.
- Not virtual-only—the remote challenge is an optional parallel participation method.
- Not MTB or gravel.
- Not a family of products masquerading as one race.

Gran Fondo World Tour currently displays Pedal IMUA under a “Gravel” card, but that is evidently bad catalog metadata. **Aloha Gravel** is the separate gravel/singletrack event held the preceding weekend; its own organizer explicitly distinguishes it from the later Pedal IMUA road gran fondo. [Gran Fondo World Tour](https://www.granfondoworldtour.com/), [Aloha Gravel announcement](https://www.alohagravel.com/blog/announcement-aloha-gravel-on-maui-all-proceeds-from-new-graveloff-road-cycling-event-to-benefit-imua-family-services)

Recommended core corrections: change founded year to **2019**, replace elevation with **1,272 m / 4,173 ft**, add the **50 km/30 mi** route, keep the surface paved, describe the field as roughly **100**, and use “charity gran fondo/ride” rather than “race.”
