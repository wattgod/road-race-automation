# Race Across Portugal — Research Dump (Editorial Wave 8, 2026-07-24)

Research conducted via codex gpt-5.6-sol foreground web search, checked 2026-07-24.

## 1. Actual format / discipline

Race Across Portugal is a continuous, timed, semi-autonomous ultra-distance road race — NOT a gran
fondo, audax, supported stage race, or fully unsupported Transcontinental-style race. Organizer specs:
open public roads, mandatory organizer-supplied GPX, continuous timing with a 96-hour limit for the
nominal 1,000 km class (no daily stages), solo/duo/four-rider categories starting individually at
30-second intervals, GPS tracking, compulsory 4-hour rest every 36 hours, self-sufficiency between
bases with outside assistance prohibited except at the designated basecamp, public shops permitted,
drafting prohibited except between registered teammates. Unlike the Transcontinental, it provides
substantial infrastructure: staffed basecamp, food, showers, cots, charging, baggage storage, medical/
operations support and family assistance at the base.
Source: https://en.raceacrossseries.com/reglement, https://en.raceacrossseries.com/race-across-portugal-2026

## 2. Organizer, status, corrected vitals

Organizer/brand: Race Across Series. Legal promoter: Across and Beyond Endurance AG (founder/CEO Arnaud
Manzanini). Technical/commercial operator: Miles Republic. Status: active; inaugural edition completed
2026. Appears on official results archive; acknowledged post-event by Amarante municipality. No 2027
edition confirmed publicly yet — "2026 completed, renewal pending," not defunct/cancelled.
Date: March 25-29, 2026 is correct but is the continuous event window, not five stages; 1,000 km riders
began 20:00 March 25. Location: Vila Meã, Amarante, Porto District — same start/finish/basecamp.
Published class: nominal 1,000 km/96 hours. Post-race finisher report gives actual ridden flagship
route as ~1,024 km/12,500+ m — the best available completed-edition figure; the prior database
999.4 km/11,100 m was stale/unsupported.
Source: https://en.raceacrossseries.com/resultats-2026,
https://www.cm-amarante.pt/wp-content/uploads/2026/04/Ata-7_07_04_2026_signed.pdf,
https://www.diariodelaltoaragon.es/noticias/deportes/2026/04/01/samuel-porcel-completa-race-across-portugal-territorio-hostil-2008837.html

## 3. Course character and surface

Three loops centered on Vila Meã; nominal 1,000 km race combines 500/200/300 km loops, returning to
the single basecamp between loops. Organizer descriptions place it in northern Portugal: Porto
hinterland, Douro Valley, Atlantic landscapes, Peneda-Gerês National Park. Terrain rolling-to-
mountainous, steep Douro/Gerês roads contributing ~12,500 m of climbing. No trustworthy public source
names individual signature climbs — do not assert specific pass names without the final GPX. Officially
categorized Road; no evidence of gravel/mixed-surface course. The unrelated GCN Portugal gravel-touring
video previously in this file's youtube_data has zero connection to this specific race and was removed.

## 4. Field, entry, history, prestige

Field: Amarante announced ~150 participants across all four distances, drawing riders from 16
countries. Distances: 200/300/500/1,000 km. Entry: public registration; 1,000 km requires proof of
experience (recent Race Across finish or equivalent 300 km within 24h). Founded: debuted 2026; parent
series traces to Race Across France (2018, 42 riders). Prestige: established organizer, but this
specific race is first-year with a modest field and no demonstrated championship/RAAM-qualifier/
long-standing ultra prestige — a new Race Across Series destination, not yet comparable in stature to
the Transcontinental Race. Naming caution: Race Around Denmark is NOT part of Race Across Series;
similar "Race Across/Around" naming does not imply common ownership.

## Database correction applied (2026-07-24)

- distance_km 999.4 -> 1024.0; elevation_m 11100 -> 12500
- location "Porto region, Portugal" -> "Vila Meã, Amarante, Porto District, Portugal"
- field_size, cutoff_time, feed_zones corrected to match organizer's actual format
- discipline enum NOT changed (still gran_fondo per pipeline convention) — catalog_flags taxonomy note
  added instead, matching race-across-germany.json / race-around-poland.json precedent
- Removed irrelevant/mislabeled youtube_data block (generic Portugal cycling-tourism videos with no
  connection to this specific ultra race)
- Full GOLD editorial written; no fondo_rating dimension changes
