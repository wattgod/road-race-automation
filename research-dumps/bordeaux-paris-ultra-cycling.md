# Bordeaux-Paris Ultra Cycling Challenge — Editorial Wave 10 Research Notes

Source: codex exec (gpt-5.6-sol, web search), 2026-07-24.

## Status: active — but format is ultra-distance, not standard gran fondo
Real, currently organized amateur ultra-cycling revival — not fabricated, not a
continuation of the historic 1891-1988 professional classic under its original
rules (motor-paced professional racing). Cycling Weekly explicitly frames the
modern version as an amateur revival. Next edition announced for Friday, May 21,
2027 ("107th edition" is heritage numbering, not an unbroken run — amateur
revivals restarted intermittently in 2014 and 2022).
Official: https://bordeaux-paris.com/
2026 results: https://bordeaux-paris.com/edition/2026/

## TAXONOMY FLAG (catalog_flags, not a discipline-enum change)
This is a semi-autonomous/semi-supported ultra-distance event on open public
roads, not a supported, timed gran fondo. Riders navigate by GPX, carry
mandatory safety/repair gear, use an organizer tracker, and are self-sufficient
between official life bases. No competitive classification exists — individual
completion times only. Solo/duo/relay entries. The fondo_rating dimensions
(field_depth, prestige, organization, road_surface, etc.) were built for
supported gran fondos and don't map cleanly onto this format — flagging for a
human taxonomy call, per the flandrien-ride precedent.

## Verified current vitals (differ substantially from stub)
- Main route: 650 km / ~4,500 m (NOT the stub's 595.5km/370mi)
- Start/finish: Stadium Velodrome de Bordeaux (09:00) to Domaine de Coubertin,
  Saint-Remy-les-Chevreuse, southwest of Paris
- Secondary route: ~300-310km from Chateauroux, ~1,450m (organizer's own pages
  disagree on 300 vs 310km)
- Time limit: 50 hours for the main route
- Minimum age: 18 in event year
- Solo entry fee: EUR240 (650km); duo/relay categories also offered
Source: https://bordeaux-paris.com/journee/route/ ,
https://bordeaux-paris.com/infos-pratiques/

## Format detail
Semi-autonomous ultra-distance cycling: GPX navigation, mandatory safety/repair
kit, organizer-supplied tracker, self-sufficient between official life bases;
following vehicles prohibited; mid-course rest area with mattresses provided
for the 650km format. Unmarked, fully timed route, three feed stations, no
competitive classification.
Source: https://bordeaux-paris.com/infos-pratiques/

## Organizer & revival history
Extra Sports developed the modern revival from 2012, staged a 2014 mass-
participation cyclosportive (~1,000 entrants, ~610km) with Golazo Sports and
Girondins de Bordeaux. Returned in 2022 with the current ultra-distance/GPS/
40-hour framework. Current owner-organizer: Chablais Leman Sport Organisation
("CLSO by SMH"), a French FFC-affiliated nonprofit that acquired the event
after the Extra Sports period; former pro Pierre Rolland has been involved in
the revival (he won the 2026 edition per L'Equipe).
Source: https://www.cyclingweekly.com/news/former-monument-bordeaux-paris-to-return-as-amateur-event ,
https://www.bordeaux-paris.com/actualites/les-changements/ ,
https://www.lequipe.fr/Cyclisme-sur-route/Actualites/Retraite-depuis-2022-pierre-rolland-remporte-bordeaux-paris-course-d-ultra-cyclisme-de-650-km/1678439

## Credible criticisms
- The proposed 2023 and 2024 editions were CANCELLED — Le Cycle described this
  as leaving a poor image of the event; the new CLSO director acknowledged
  many prospective riders were unhappy and needed reassurance.
- A detailed 2022 finisher account (Extra Sports era, not necessarily current
  CLSO operation) criticized conflicting GPS directions, an understocked first
  feed station, a sparse finish meal, apparent support/group-size rule
  violations, and an unexpected rough/gravel section.
- Current site has internal inconsistencies: alternates 300/310km for the
  short route, rules page still shows 2026 documents, registration link
  retains a "2026" URL path even though 2027 is being sold.
Source: Le Cycle interview (library.wobook.com), Kikourou forum 2022 report

## youtube_data note
Purged 1 of 3 videos — GCN's "Can We Survive A Stage Of The 1903 Tour De
France?" is an unrelated historical-recreation video with no connection to
this event; it surfaced only via generic search terms. Kept two genuine 2014
Bordeaux-Paris videos (Team France Cyclisme Ultra-Distance, Jessy Langonnet),
which match the documented 2014 Extra Sports revival edition.
