# Round Denmark Bike Race — Research Dump (Editorial Wave 8, 2026-07-24)

Research conducted via codex gpt-5.6-sol foreground web search, checked 2026-07-24.

## 1. Identity and organizer

Round Denmark Bike Race is real and is NOT a name variant of Race Around Denmark. It is operated by an
independent, non-profit volunteer team; current race director publicly known only as "Lone." Race
Around Denmark is a different 1,600 km event run by Uggi Kaldan's RAD team, with supported and
unsupported divisions and WUCA/RAAM-qualifier status. Neither is Danmark Rundt, the five-stage UCI
ProSeries professional race (July 29-August 2, 2026).
Source: https://www.rounddenmarkbikerace.dk/, https://racearounddenmark.org/,
https://racearounddenmark.org/about-rad, https://www.uci.org/competition-details/2026/ROA/78320

## 2. Format and current vitals

Fixed-route, self-supported ultra-distance bikepacking time trial, not a gran fondo. Continuous clock
(riders may stop/sleep); mandatory organizer GPX, not rider-chosen routing. Private resupply, support
cars, private lodging and outside navigation help prohibited; ordinary commercial services equally
available to all riders are allowed. Current advertised 2026 road figures: 1,964 km / 8,658 m (database's
1,965/8,659 were one-unit rounding errors). 2026 start advertised for 08:00 July 5 at Kronborg Castle,
Helsingør.
Source: https://www.rounddenmarkbikerace.dk/, https://www.rounddenmarkbikerace.dk/rules.html,
https://rounddenmarkbikerace.dk/athletesguide.html

## 3. Eligibility/status

Active — based on current 2026 event materials, registration, route figures, athlete guide; no
cancellation/closure notice found. As of the July 24 check, the advertised start date had passed but
the site had not yet posted 2026 results (latest Hall of Fame entries: 2023 road, 2024 gravel).
Catalog-wise: not eligible as gran_fondo — should be understood as ultra-distance/self-supported
bikepacking.
Source: https://www.rounddenmarkbikerace.dk/registration.html, https://www.rounddenmarkbikerace.dk/halloffame.html

## 4. Course character

Broadly circles the major parts of Denmark, but "circumnavigation" should not imply tracing every km of
coastline or returning to the exact start — it starts in Helsingør and finishes near Farum. Crosses
Zealand and Denmark's southern islands, follows Jutland's coasts and inland roads, requires five
ferries. The road edition still contains roughly 122-130 km of gravel, about 1 km of cobbles, plus
occasional dirt and sand. Denmark's modest gradients are not the central difficulty — the real load is
1,964 km, exposed coastal wind, rain/temperature swings, accumulated sleep loss, self-managed food and
repairs, and timing ferry schedules.
Source: https://www.rounddenmarkbikerace.dk/, https://www.rounddenmarkbikerace.dk/route.html

## 5. Field and entry rules

The "30" figure is a road-race cap, not a demonstrated field size; the gravel edition is capped at 20,
and historical starts have usually been much smaller. Entry requires completing a rules/guide test,
supplying evidence of a recent outdoor ride of at least 100 km, attending the mandatory briefing,
signing the waiver/conduct declaration, carrying a live SPOT tracker and prescribed safety/repair
equipment, and accepting sole responsibility for navigation, sleep, nutrition, repairs and safety.
Solo riders must be 18; riders as young as 15 may enter a pair with an experienced parent.
Source: https://www.rounddenmarkbikerace.dk/registration.html, https://www.rounddenmarkbikerace.dk/rules.html

## 6. History and prestige

Conceived spring 2017, inaugural edition 2018 (16 starters), 12 starters in 2019, road course record
5d 5h 27m from 2023. A legitimate but deliberately small, grassroots ultra — a 2022 Transcontinental
Race finisher chose it as a lower-profile fixed-route alternative. No evidence of WUCA championship or
RAAM-qualifier status; that distinction belongs to the separate Race Around Denmark.
Source: https://www.rounddenmarkbikerace.dk/halloffame.html, https://jkbsbikeride.com/2022/12/07/round-denmark-bike-race-part-1-10-07-22-13-07-22/

## Database correction applied (2026-07-24)

- distance_km 1965.0 -> 1964.0; elevation_m 8659 -> 8658 (organizer's current advertised figures)
- location corrected to reflect the actual Helsingør-to-Farum loop, not a literal circumnavigation
- field_size corrected to note the 30-cap is road-course-specific, historically much smaller
- feed_zones and cutoff_time corrected to reflect actual self-supported rules
- discipline enum NOT changed (still gran_fondo per pipeline convention) — catalog_flags taxonomy note
  added instead, matching race-across-germany.json / race-around-poland.json precedent
- Full GOLD editorial written; no fondo_rating dimension changes
