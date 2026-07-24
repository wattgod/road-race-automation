# two-volcano-sprint — editorial wave 5 research evidence (2026-07-24)

Source: codex gpt-5.6-sol foreground web research, log: ed5_d_two-volcano-sprint_research.log

## 1. Status and date

**Best-evidence status: active, but no future edition is officially scheduled yet.** The race ran on April 26, 2026, and the organizer has published 2026 results. I found no official 2027 announcement; the official page still refers to the now-completed 2026 edition. It is one recurring event, not a category of products. [Official Two Volcano Sprint site](https://www.twovolcanosprint.com/)

**Most recent confirmed edition:** April 26, 2026. The official GPS provider independently records that start date and the completed race. [Follow My Challenge event record](https://followmychallenge.com/event/1440/), [2026 live results](https://www.followmychallenge.com/live/2vs26/)

**Single best source URL:** https://www.twovolcanosprint.com/

**Date conflict resolved:** April 26, 2026 is correct. It is supported by the organizer, the actual GPS-tracked event, the registration announcement, and Apidura’s ultra calendar. [Organizer](https://www.twovolcanosprint.com/), [GPS provider](https://followmychallenge.com/event/1440/), [2026 registration announcement](https://www.amalficoast.com/en/lifestyle-9/registrations-open-for-the-two-volcano-sprint-2026-2074/article), [Apidura calendar](https://www.apidura.com/bikepacking-events/)

The October 1 date comes from a secondary German bikepacking directory that also gives an obsolete 1,000 km distance. It is contradicted by the organizer and actual race tracking and should be rejected. [Erroneous October listing](https://www.bikepackers.de/bikepacking-events/2vs-volcano-sprint/)

A directory currently displays April 26, 2027, but that date is not confirmed by the organizer and should not be entered as an official next edition. [Unconfirmed 2027 directory listing](https://gravelevents.com/events/two-volcano-sprint)

## 2. Course and profile corrections

| Field | Best-supported finding | Profile action |
|---|---|---|
| Distance | The 2026 tracking course measured **1,221.01 km / approximately 758.7 mi**. Contemporary previews rounded it to 1,200–1,225 km. [2026 GPS course](https://www.followmychallenge.com/live/2vs26/), [1,225 km preview](https://cyclismepourtous.com/velo-concept/cyclisme-ultra/page/2/) | Replace **1,200.6 km / 746 mi** with **1,221 km / 759 mi** for the 2026 edition. |
| Elevation | Current reporting conflicts between approximately **25,000 m** and **26,000 m**. The familiar 24,000 m figure describes earlier roughly 1,100 km editions and appears to have been carried forward. [2026 rider coverage: 25,000 m](https://www.merkur.de/sport/lokalsport/miesbach/andreas-lenz-vollendet-two-volcano-sprint-trotz-teampartner-ausfall-miesbach-radsport-94299001.html), [2026 preview: 26,000 m](https://cyclismepourtous.com/velo-concept/cyclisme-ultra/page/2/), [2019 official report: 1,100 km/24,000 m](https://www.twovolcanosprint.com/race-report-2019/) | **24,000 m is probably stale for 2026.** Store approximately **25,000–26,000 m**, with an uncertainty flag, until the organizer releases the GPX elevation total. |
| Start/finish | The current direction is Vesuvius south to Etna, finishing in **Nicolosi**, not central Catania. Nicolosi is in the Catania area. [2026 report](https://www.merkur.de/sport/lokalsport/miesbach/andreas-lenz-vollendet-two-volcano-sprint-trotz-teampartner-ausfall-miesbach-radsport-94299001.html), [official route history](https://www.twovolcanosprint.com/race-report-2019/) | Prefer **“Mt Vesuvius/Ercolano area to Mt Etna/Nicolosi, Italy.”** |
| Route | The race launches onto Vesuvius, follows the Amalfi/Cilento side of southern Italy, crosses the Apennines and the Pollino, Sila and Aspromonte areas, uses the Villa San Giovanni–Messina ferry, climbs through Sicily, ascends Etna and descends to the finish. [Official route description](https://www.twovolcanosprint.com/race-report-2019/), [detailed 2026 rider account](https://gregortowers.substack.com/p/2-volcano-sprint-my-best-ultra-cycling) | Add the regions and ferry crossing; “Vesuvius to Etna” alone undersells the course structure. |
| Principal climbs | The 2026 account identifies the opening Vesuvius ascent, **Monte Gelbison**—about 30 km with sections above 12%—Cristo Redentore at Maratea, prolonged Pollino/Sila/Aspromonte climbing, a 38 km ascent from the Sicilian coast and the final approximately 22 km Etna climb to about 2,000 m. [2026 rider account](https://gregortowers.substack.com/p/2-volcano-sprint-my-best-ultra-cycling) | Populate `climb_profile`; the current empty placeholder is materially incomplete. |
| Surface | Specialist listings call it **road** or **all-road**, not MTB. Nevertheless, the 2026 rider report describes rough and farm tracks, broken pavement, technical descents and Calabria potholes reportedly reaching 30 cm. [Road classification](https://ultracyclingraces.com/races/two-volcano-sprint-2026), [all-road classification](https://www.apidura.com/bikepacking-events/), [2026 surface report](https://gregortowers.substack.com/p/2-volcano-sprint-my-best-ultra-cycling) | Do **not** promise “fully paved roads.” Best label: **road/all-road, predominantly paved but exceptionally rough and degraded, with farm/rough-track sections**. `technical_rating=1` is also indefensible. |
| Field size | The 2026 tracker contains **77 non-DNS solo positions, 31 pair-rider positions and 4 outside-classification riders—112 non-DNS rider entries—plus 13 solo DNS listings**. The organizer’s published classification lists 62 solo finishers, 20 pair participants and 2 outside-classification participants. [2026 tracker](https://www.followmychallenge.com/live/2vs26/), [official results](https://www.twovolcanosprint.com/) | Replace vague “Small” with approximately **112 starters/non-DNS tracked riders in 2026**. That is small relative to a fondo, but sizeable for unsupported ultracycling. |
| Entry format | Riders enter **solo or as a pair**, follow a compulsory GPX, carry an always-on GPS tracker and may not draft unless entered as a pair. Riders carry their equipment and obtain food, water and lodging from commercially available services. [Organizer rules](https://www.twovolcanosprint.com/) | Use **fixed-route, GPS-tracked, solo/pair, self-supported entry**. I found no current evidence of a formal qualifying standard. |
| Feed zones | The rules require commercial self-resupply, so there is no normal gran-fondo feed-zone network. A 2026 rider nevertheless mentions a sponsored food stop. [Organizer rules](https://www.twovolcanosprint.com/), [2026 rider account](https://gregortowers.substack.com/p/2-volcano-sprint-my-best-ultra-cycling) | Better wording: **“No standard organizer feed-zone network; commercial self-resupply, with occasional event/trail-angel stops possible.”** |
| Cutoff | A current ultracycling listing gives **168 hours / seven days**. Earlier editions used a 110-hour classification deadline, so `N/A` is clearly misleading even if the exact 2026 official rule is no longer visible on the organizer page. [2026 listing](https://ultracyclingraces.com/races/two-volcano-sprint-2026), [earlier 110-hour rule](https://www.ansa.it/sito/notizie/speciali/editoriali/2020/07/26/two-volcano-sprint_91c05005-f694-4a2a-a19d-e0a5971bba5f.html) | Enter **“168h reported; official confirmation needed”**, not `N/A`. |
| Eligibility | Older organizer reporting described it as open to riders willing to attempt it, while the format and 2026 field clearly attract experienced Transcontinental/Badlands-level racers. [ANSA event description](https://www.ansa.it/sito/notizie/speciali/editoriali/2020/07/26/two-volcano-sprint_91c05005-f694-4a2a-a19d-e0a5971bba5f.html), [2026 field account](https://gregortowers.substack.com/p/2-volcano-sprint-my-best-ultra-cycling) | Do not turn “experienced field” into an unsupported claim that previous ultra results are mandatory. |

## Notable history

The inaugural race was held in 2019 with 17 starters; six reached the classification finish, and Ulrich Bartholmoes won the approximately 1,100 km/24,000 m route in 59 hours 58 minutes. [Official 2019 report](https://www.twovolcanosprint.com/race-report-2019/)

The planned 2023 edition was cancelled because the organizer lacked enough checkpoint volunteers, but GPS results confirm the race returned in 2024 and again in 2026. [2023 cancellation account](https://fiabciclocittavarese.it/2024/02/03/basilicata-bike-trail/), [2024 tracking](https://www.followmychallenge.com/live/2vs24/), [2026 tracking](https://www.followmychallenge.com/live/2vs26/)

Bruno Wicht won the 2026 solo race in 59 hours 23 minutes according to the organizer. [Official 2026 results](https://www.twovolcanosprint.com/)

The event is operated as a not-for-profit environmental fundraiser: after tracker costs, entry fees support an annual sustainability/community grant. It is therefore a paid race entry, not a commercial guided tour package. [Organizer explanation](https://www.twovolcanosprint.com/)

## 3. Format verdict

**This is categorically not a gran fondo.** It is a single-stage, fixed-route, GPS-tracked, self-supported ultracycling race in the Transcontinental tradition: riders manage their own food, water, sleeping, navigation and mechanical problems; outside assistance and solo drafting are prohibited. [Organizer rules](https://www.twovolcanosprint.com/)

It is also:

- **Not a guided tour or travel product:** the entry fee funds race tracking and the nonprofit program; lodging and resupply remain the rider’s responsibility. [Organizer](https://www.twovolcanosprint.com/)
- **Not virtual or Strava-based:** it has a physical mass start, compulsory trackers and a live real-world leaderboard. [Follow My Challenge](https://www.followmychallenge.com/live/2vs26/)
- **Not primarily MTB/gravel:** specialist sources classify it as road or all-road, although “fully paved” is too confident given the documented farm tracks and severely broken surfaces. [Ultracycling Races](https://ultracyclingraces.com/races/two-volcano-sprint-2026), [Apidura](https://www.apidura.com/bikepacking-events/), [2026 rider report](https://gregortowers.substack.com/p/2-volcano-sprint-my-best-ultra-cycling)

**Blunt database recommendation:** `discipline=gran_fondo` is dishonest. Reclassify it as `ultra_distance` / `unsupported_road_ultra` / `bikepacking_ultra`. If Roadie Labs cannot represent ultracycling separately, exclude or quarantine the profile rather than presenting it to readers as a gran fondo. The organizer’s own description leaves no ambiguity about the format. [Official event definition and rules](https://www.twovolcanosprint.com/)
tokens used
189,221
## 1. Status and date

**Best-evidence status: active, but no future edition is officially scheduled yet.** The race ran on April 26, 2026, and the organizer has published 2026 results. I found no official 2027 announcement; the official page still refers to the now-completed 2026 edition. It is one recurring event, not a category of products. [Official Two Volcano Sprint site](https://www.twovolcanosprint.com/)

**Most recent confirmed edition:** April 26, 2026. The official GPS provider independently records that start date and the completed race. [Follow My Challenge event record](https://followmychallenge.com/event/1440/), [2026 live results](https://www.followmychallenge.com/live/2vs26/)

**Single best source URL:** https://www.twovolcanosprint.com/

**Date conflict resolved:** April 26, 2026 is correct. It is supported by the organizer, the actual GPS-tracked event, the registration announcement, and Apidura’s ultra calendar. [Organizer](https://www.twovolcanosprint.com/), [GPS provider](https://followmychallenge.com/event/1440/), [2026 registration announcement](https://www.amalficoast.com/en/lifestyle-9/registrations-open-for-the-two-volcano-sprint-2026-2074/article), [Apidura calendar](https://www.apidura.com/bikepacking-events/)

The October 1 date comes from a secondary German bikepacking directory that also gives an obsolete 1,000 km distance. It is contradicted by the organizer and actual race tracking and should be rejected. [Erroneous October listing](https://www.bikepackers.de/bikepacking-events/2vs-volcano-sprint/)

A directory currently displays April 26, 2027, but that date is not confirmed by the organizer and should not be entered as an official next edition. [Unconfirmed 2027 directory listing](https://gravelevents.com/events/two-volcano-sprint)

## 2. Course and profile corrections

| Field | Best-supported finding | Profile action |
|---|---|---|
| Distance | The 2026 tracking course measured **1,221.01 km / approximately 758.7 mi**. Contemporary previews rounded it to 1,200–1,225 km. [2026 GPS course](https://www.followmychallenge.com/live/2vs26/), [1,225 km preview](https://cyclismepourtous.com/velo-concept/cyclisme-ultra/page/2/) | Replace **1,200.6 km / 746 mi** with **1,221 km / 759 mi** for the 2026 edition. |
| Elevation | Current reporting conflicts between approximately **25,000 m** and **26,000 m**. The familiar 24,000 m figure describes earlier roughly 1,100 km editions and appears to have been carried forward. [2026 rider coverage: 25,000 m](https://www.merkur.de/sport/lokalsport/miesbach/andreas-lenz-vollendet-two-volcano-sprint-trotz-teampartner-ausfall-miesbach-radsport-94299001.html), [2026 preview: 26,000 m](https://cyclismepourtous.com/velo-concept/cyclisme-ultra/page/2/), [2019 official report: 1,100 km/24,000 m](https://www.twovolcanosprint.com/race-report-2019/) | **24,000 m is probably stale for 2026.** Store approximately **25,000–26,000 m**, with an uncertainty flag, until the organizer releases the GPX elevation total. |
| Start/finish | The current direction is Vesuvius south to Etna, finishing in **Nicolosi**, not central Catania. Nicolosi is in the Catania area. [2026 report](https://www.merkur.de/sport/lokalsport/miesbach/andreas-lenz-vollendet-two-volcano-sprint-trotz-teampartner-ausfall-miesbach-radsport-94299001.html), [official route history](https://www.twovolcanosprint.com/race-report-2019/) | Prefer **“Mt Vesuvius/Ercolano area to Mt Etna/Nicolosi, Italy.”** |
| Route | The race launches onto Vesuvius, follows the Amalfi/Cilento side of southern Italy, crosses the Apennines and the Pollino, Sila and Aspromonte areas, uses the Villa San Giovanni–Messina ferry, climbs through Sicily, ascends Etna and descends to the finish. [Official route description](https://www.twovolcanosprint.com/race-report-2019/), [detailed 2026 rider account](https://gregortowers.substack.com/p/2-volcano-sprint-my-best-ultra-cycling) | Add the regions and ferry crossing; “Vesuvius to Etna” alone undersells the course structure. |
| Principal climbs | The 2026 account identifies the opening Vesuvius ascent, **Monte Gelbison**—about 30 km with sections above 12%—Cristo Redentore at Maratea, prolonged Pollino/Sila/Aspromonte climbing, a 38 km ascent from the Sicilian coast and the final approximately 22 km Etna climb to about 2,000 m. [2026 rider account](https://gregortowers.substack.com/p/2-volcano-sprint-my-best-ultra-cycling) | Populate `climb_profile`; the current empty placeholder is materially incomplete. |
| Surface | Specialist listings call it **road** or **all-road**, not MTB. Nevertheless, the 2026 rider report describes rough and farm tracks, broken pavement, technical descents and Calabria potholes reportedly reaching 30 cm. [Road classification](https://ultracyclingraces.com/races/two-volcano-sprint-2026), [all-road classification](https://www.apidura.com/bikepacking-events/), [2026 surface report](https://gregortowers.substack.com/p/2-volcano-sprint-my-best-ultra-cycling) | Do **not** promise “fully paved roads.” Best label: **road/all-road, predominantly paved but exceptionally rough and degraded, with farm/rough-track sections**. `technical_rating=1` is also indefensible. |
| Field size | The 2026 tracker contains **77 non-DNS solo positions, 31 pair-rider positions and 4 outside-classification riders—112 non-DNS rider entries—plus 13 solo DNS listings**. The organizer’s published classification lists 62 solo finishers, 20 pair participants and 2 outside-classification participants. [2026 tracker](https://www.followmychallenge.com/live/2vs26/), [official results](https://www.twovolcanosprint.com/) | Replace vague “Small” with approximately **112 starters/non-DNS tracked riders in 2026**. That is small relative to a fondo, but sizeable for unsupported ultracycling. |
| Entry format | Riders enter **solo or as a pair**, follow a compulsory GPX, carry an always-on GPS tracker and may not draft unless entered as a pair. Riders carry their equipment and obtain food, water and lodging from commercially available services. [Organizer rules](https://www.twovolcanosprint.com/) | Use **fixed-route, GPS-tracked, solo/pair, self-supported entry**. I found no current evidence of a formal qualifying standard. |
| Feed zones | The rules require commercial self-resupply, so there is no normal gran-fondo feed-zone network. A 2026 rider nevertheless mentions a sponsored food stop. [Organizer rules](https://www.twovolcanosprint.com/), [2026 rider account](https://gregortowers.substack.com/p/2-volcano-sprint-my-best-ultra-cycling) | Better wording: **“No standard organizer feed-zone network; commercial self-resupply, with occasional event/trail-angel stops possible.”** |
| Cutoff | A current ultracycling listing gives **168 hours / seven days**. Earlier editions used a 110-hour classification deadline, so `N/A` is clearly misleading even if the exact 2026 official rule is no longer visible on the organizer page. [2026 listing](https://ultracyclingraces.com/races/two-volcano-sprint-2026), [earlier 110-hour rule](https://www.ansa.it/sito/notizie/speciali/editoriali/2020/07/26/two-volcano-sprint_91c05005-f694-4a2a-a19d-e0a5971bba5f.html) | Enter **“168h reported; official confirmation needed”**, not `N/A`. |
| Eligibility | Older organizer reporting described it as open to riders willing to attempt it, while the format and 2026 field clearly attract experienced Transcontinental/Badlands-level racers. [ANSA event description](https://www.ansa.it/sito/notizie/speciali/editoriali/2020/07/26/two-volcano-sprint_91c05005-f694-4a2a-a19d-e0a5971bba5f.html), [2026 field account](https://gregortowers.substack.com/p/2-volcano-sprint-my-best-ultra-cycling) | Do not turn “experienced field” into an unsupported claim that previous ultra results are mandatory. |

## Notable history

The inaugural race was held in 2019 with 17 starters; six reached the classification finish, and Ulrich Bartholmoes won the approximately 1,100 km/24,000 m route in 59 hours 58 minutes. [Official 2019 report](https://www.twovolcanosprint.com/race-report-2019/)

The planned 2023 edition was cancelled because the organizer lacked enough checkpoint volunteers, but GPS results confirm the race returned in 2024 and again in 2026. [2023 cancellation account](https://fiabciclocittavarese.it/2024/02/03/basilicata-bike-trail/), [2024 tracking](https://www.followmychallenge.com/live/2vs24/), [2026 tracking](https://www.followmychallenge.com/live/2vs26/)

Bruno Wicht won the 2026 solo race in 59 hours 23 minutes according to the organizer. [Official 2026 results](https://www.twovolcanosprint.com/)

The event is operated as a not-for-profit environmental fundraiser: after tracker costs, entry fees support an annual sustainability/community grant. It is therefore a paid race entry, not a commercial guided tour package. [Organizer explanation](https://www.twovolcanosprint.com/)

## 3. Format verdict

**This is categorically not a gran fondo.** It is a single-stage, fixed-route, GPS-tracked, self-supported ultracycling race in the Transcontinental tradition: riders manage their own food, water, sleeping, navigation and mechanical problems; outside assistance and solo drafting are prohibited. [Organizer rules](https://www.twovolcanosprint.com/)

It is also:

- **Not a guided tour or travel product:** the entry fee funds race tracking and the nonprofit program; lodging and resupply remain the rider’s responsibility. [Organizer](https://www.twovolcanosprint.com/)
- **Not virtual or Strava-based:** it has a physical mass start, compulsory trackers and a live real-world leaderboard. [Follow My Challenge](https://www.followmychallenge.com/live/2vs26/)
- **Not primarily MTB/gravel:** specialist sources classify it as road or all-road, although “fully paved” is too confident given the documented farm tracks and severely broken surfaces. [Ultracycling Races](https://ultracyclingraces.com/races/two-volcano-sprint-2026), [Apidura](https://www.apidura.com/bikepacking-events/), [2026 rider report](https://gregortowers.substack.com/p/2-volcano-sprint-my-best-ultra-cycling)

**Blunt database recommendation:** `discipline=gran_fondo` is dishonest. Reclassify it as `ultra_distance` / `unsupported_road_ultra` / `bikepacking_ultra`. If Roadie Labs cannot represent ultracycling separately, exclude or quarantine the profile rather than presenting it to readers as a gran fondo. The organizer’s own description leaves no ambiguity about the format. [Official event definition and rules](https://www.twovolcanosprint.com/)
