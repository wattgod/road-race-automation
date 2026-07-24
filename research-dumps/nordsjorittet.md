# Nordsjørittet — Research Dump (2026-07-24)

Editorial wave 4 (batch of 4: nordsjorittet, highlands-gran-fondo,
amashova-national-classic, axel-merckx-gran-fondo). Research via
`codex --search exec -m gpt-5.6-sol` (web search enabled), read-only, run
2026-07-24. Compiled by editorial batch agent.

## KEY FINDING — this is a mixed-surface MTB/gravel "turritt," not a road fondo
The organizer's own site markets Nordsjørittet for cyclocross/gravel, MTB,
hybrid and e-bike participation, with entry categories of: timed 88km
(flat-bar bike), timed 88km CX/gravel (drop-bar), and untimed 88km (any bike
type, including e-bikes). It is materially different from a pure road
sportive. https://www.nordsjorittet.no/ (accessed 24 July 2026);
https://www.nordsjorittet.no/informasjon/early-bird-priser-n (2026 pricing
and categories, dated 23 June)

**Flag for human review**: this profile is in the Roadie Labs (road) database
but the current event is a mixed-surface MTB/gravel/CX touring ride
("turritt" in Norwegian), not a road race. Prior file's `terrain.surface`
("60% paved, 20% gravel/unpaved," incomplete at 80%) already hinted at this,
and `fondo_rating.road_surface` was already scored low (3) reflecting mixed
terrain. Whether this belongs in a pure road-race database is a taxonomy call
for a human, same class of question as flandrien-ride.json's identity
correction.

## Key corrections
- `distance_km`: **88.0** (was 154.5) — organizer's 2026 registration page states the course is 88km ±5%
- `elevation_m`: **no current reliable figure** — set to null; the file's prior 1,494m is unsupported. Historical figures range from 770m (2021, 91km course) to 1,030m (2010, 91km course) — neither is a valid 2026 substitute, and the 2026 course specifically dropped the Vandavatn section (formerly the most technically demanding part), so old elevation data doesn't transfer.
- `field_size`: **approximately 1,200 starters (2026, all distances)** — was unsourced "12,500 riders," which is the race's 2013 boom-era figure (Stavanger Aftenblad, 2013), not current.
- Event is mixed-surface MTB/gravel/CX, not primarily road — corrected terrain/course framing.
- Date: June 13, 2026 has already passed (today's research date is 24 July 2026); official site currently shows **12 June 2027** as the next edition.

## 1. Distance and elevation
- Organizer's 2026 registration page: **88 km, ±5%**. https://www.nordsjorittet.no/informasjon/early-bird-priser-n (dated 23 June; registration opened 24 June 2025; accessed 24 July 2026)
- Fjord Norway currently lists 87 km (likely a rounded presentation of the same course): https://www.fjordnorway.com/en/see-and-do/nordsjorittet-myyj8fnnsawctpwkdvxgkg (undated, accessed 24 July 2026)
- No current official elevation-gain figure is published on the accessible 2026 organizer or Fjord Norway pages.
- Historical elevation data (not valid current substitutes): 2010 official route PDF gave 1,030m for a 91km course (https://gammel.nordsjorittet.no/2010kart.pdf); a 2021 rider report measured 770m over 91km (https://nordictrailblazer.cc/races/nordsjorittet-grvl/, Sept 2021).
- The 2026 route specifically bypassed the Vandavatn forest section (formerly its most technically demanding part), per the official 2026 participant briefing (https://www.nordsjorittet.no/informasjon/alt-du-trenger-vite-om-nordsjrittet-2026, 14 April 2026) and Stavanger Aftenblad's course preview (https://www.aftenbladet.no/sport/i/XMd5bn/over-1000-paamelde-her-er-alt-du-treng-aa-vite-foer-nordsjoerittet, 12 June 2026).
- A secondary route guide (not organizer-stated) gives 60% asphalt / 20% gravel / 20% paths-singletrack: https://www.ski-nordique.net/nordsjoerittet-2026-resultater-live-sandnes-rogaland.6747689-72348.html (10 June 2026) — flagged as approximate/secondary.

## 2. Event type / surface
Primarily a mixed-surface MTB/gravel event, not a conventional road sportive.
- Organizer advertises cyclocross/gravel, MTB, hybrid and e-bike participation: https://www.nordsjorittet.no/ (accessed 24 July 2026)
- 2026 entry categories: timed 88km (flat-bar), timed 88km CX/gravel (drop-bar), untimed 88km (any bike incl. e-bikes): https://www.nordsjorittet.no/informasjon/early-bird-priser-n

## 3. Field size / recent participation
- 2026: 1,000+ registered day before the event; ~1,200 started across three distances. Stavanger Aftenblad (12 June 2026): https://www.aftenbladet.no/sport/i/XMd5bn/over-1000-paamelde-her-er-alt-du-treng-aa-vite-foer-nordsjoerittet ; Kondis results (14 June 2026): https://www.kondis.no/resultater/resultater-nordsjorittet-2026/1573846
- 2025 timed long route: 734 ordinary + 200 CX/gravel = 934 recorded timed participants (excludes untimed/shorter routes): https://www.turritt.com/index.php?Order=Plassering&Turritt=3223&current=2&dir=ASC&page=resultat&su=2 ; https://www.turritt.com/index.php?Order=Plassering&Turritt=3224&current=2&dir=ASC&page=resultat&su=2
- 2024 timed long route: 725 ordinary + 111 CX = 836 recorded timed participants.
- 2023: Norwegian Cycling Federation reported 2,312 participants across five distances (up 555 from 2022): https://sykling.no/nyheter/nordsjorittet-med-deltaker-okning-i-25-ars-jubileet/
- 12,500 figure is from the race's boom era — Stavanger Aftenblad reported 12,500 riders for the 91km event in 2013: https://www.aftenbladet.no/lokalt/i/Gjy8V/skal-syklistene-bare-legge-igjen-bananskall

## 4. Entry fee and registration
2026 timed 88km or 43km (half-distance) entries: NOK 690 (24 Jun-31 Jul 2025) → NOK 890 (1 Aug 2025-31 Jan 2026) → NOK 990 (1 Feb-31 May 2026) → NOK 1,190 (1-12 Jun 2026) → NOK 1,400 (race day 13 Jun 2026). Untimed entries: NOK 649 → NOK 790 → NOK 990 (same windows, one fewer tier). https://www.nordsjorittet.no/informasjon/early-bird-priser-n
Timed riders aged 13-79 require an NCF (Norwegian Cycling Federation) annual or one-day licence, not included in entry fee: https://www.nordsjorittet.no/informasjon/regler

## 5. Competitive vs recreational
Not recreational-only — timed standard and timed CX/gravel categories run alongside an untimed recreational class (e-bikes untimed only). CX/gravel riders use the same route, get a separate NCF-required results list, and remain eligible for first-woman/first-man prizes. First finishers get prizes; everyone gets a finisher medal. https://www.nordsjorittet.no/informasjon/nordsjrittet-hel-og-halv-cx/gravel (dated 12 March); https://www.nordsjorittet.no/informasjon/alt-du-trenger-vite-om-nordsjrittet-2026 (14 April 2026)

## 6. Course features
- Route runs north from Egersund through coastal Jæren via Nordsjøveien/North Sea Road, Den Vestlandske Hovedveg/Western Main Highway and Kongevegen/King's Road — forests, coastal rock, beaches, farmland: https://www.fjordnorway.com/en/see-and-do/nordsjorittet-myyj8fnnsawctpwkdvxgkg
- Landmarks: Hellvik (~9km), Hølland Farm (~19km), Hå Gamle Prestegård (~54km), Tubakken (~68km): https://www.nordsjorittet.no/informasjon/alt-du-trenger-vite-om-nordsjrittet-2026 (14 April 2026)
- Tubakken is the signature late climb/spectator point — historically ~450m at ~10% (2014 measurement, not a fresh 2026 survey): https://www.aftenbladet.no/lokalt/i/MjddJ/sykkelbaluba-i-tubakken-for-femte-aar-paa-rad (6 June 2014). Remained competitively decisive in 2026 — winner Fredrik Dversnes attacked there: https://www.kondis.no/idrett/fredrik-dversnes-lavik-innfridde-i-nordsjorittet/1573855 (14 June 2026)
- 2026 course bypassed Vandavatn, eliminating what the race director called its most demanding technical section.

## 7. Official website / best citations
- Official site: https://www.nordsjorittet.no/ (currently showing 12 June 2027 as next edition; accessed 24 July 2026)
- Best 2026 distance/fees/formats citation: https://www.nordsjorittet.no/informasjon/early-bird-priser-n
- Best 2026 route/prizes/cutoff citation: https://www.nordsjorittet.no/informasjon/alt-du-trenger-vite-om-nordsjrittet-2026
- Tourism citation: https://www.fjordnorway.com/en/see-and-do/nordsjorittet-myyj8fnnsawctpwkdvxgkg

## Sol adversarial review addendum (2026-07-24)
Reviewed via `codex --search exec -m gpt-5.6-sol`, cross-checking the written profile against fresh web search. Findings applied:
- **Founded 1980 was wrong** — organizer's own "omoss"/about page states the first event was 1998 (organizing company established 2008). Corrected `history.founded` to 1998 and reworded all "1980" references.
- **"Mass start" was wrong** — 2026 used 11 staggered waves (10:00-10:40), including separate CX/gravel and MTB waves, not a single mass start. Corrected `vitals.start_format` and `logistics.transport`.
- **"2013 peak" was overstated** — 12,500-rider fields were reported for at least two consecutive editions, 2013 AND 2014 (2012-14 era), not uniquely 2013. Reworded to "2012-2014 peak era" throughout.
- Removed name-dropped "alternatives" (Styrkeprøven, Birkebeinerrittet road edition) — sol found Styrkeprøven was cancelled in 2026 and Birkebeinerrittet has no road edition (it's MTB-only). Replaced with generic, non-stale guidance.
- Softened the 60/20/20 surface-split claim and removed an unsupported "pure road bike would struggle" line — the split is from a secondary, non-organizer source and not confirmed for the revised 2026 route.
- Labeled entry fees explicitly as "2026 fee schedule" since the profile's forward-looking date is now 2027.
- Trimmed repeated 12,500-to-1,200 decline framing to reduce redundancy per sol's voice note.
