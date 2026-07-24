# Axel Merckx Gran Fondo (Okanagan Granfondo) — Research Dump (2026-07-24)

Editorial wave 4 (batch of 4: nordsjorittet, highlands-gran-fondo,
amashova-national-classic, axel-merckx-gran-fondo). Research via
`codex --search exec -m gpt-5.6-sol` (web search enabled), read-only, run
2026-07-24. Compiled by editorial batch agent.

## CRITICAL FINDING — THE EVENT IS DISCONTINUED, NOT ACTIVE
The task brief assumed this was a "currently-active mass-participation gran
fondo." That premise is factually wrong. **There was no 2026 edition.** The
organizer formally discontinued the road granfondo on **2 October 2025**,
identifying the **13 July 2025** ride (13th edition) as the final one. The
brief's "14th edition Jul 12 2026" is a phantom edition — an old Race Roster
listing still displays 12 July 2026, but registration is closed and it
directly conflicts with the organizer's own discontinuation notice.
- Official organizer discontinuation notice, 2 Oct 2025: https://okanagangranfondo.com/OkanaganGranfondoNewsReleaseOct2.pdf
- City of Penticton 2025 traffic/route notice, created 24 June 2025: https://www.penticton.ca/sites/default/files/2025-07/2025%20Okanagan%20Granfondo%20Traffic%20notice.pdf
- Orphaned Race Roster 2026 listing (closed registration), accessed 24 July 2026: https://raceroster.com/events/2026/60204/okanagan-granfondo

The event was also **renamed "Okanagan Granfondo" in 2022**, dropping both
"Prospera" and "Axel Merckx" from the current/final name.
- PentictonNow, 7 July 2022: https://www.pentictonnow.com/watercooler/news/news/Penticton/Renamed_modified_and_busier_than_ever_Granfondo_s_back_in_town

**Editorial recommendation**: mark `eligibility.status: "defunct"`. Keep the
profile (real historical race, real data), but the biased_opinion and
final_verdict must not tell a 2026 reader to go race this — it's gone. This
mirrors the flandrien-ride.json precedent (catalog_flags block flagging an
identity/status issue for human review) rather than silently rewriting the
profile as if it's still active.

## Verified facts (final/most recent edition = 2025, 13th)

| Fact | Finding | Source |
|---|---|---|
| Final distance/elevation | **155 km / 1,700+ m** (2025 long route) | City of Penticton route notice, 24 June 2025: https://www.penticton.ca/sites/default/files/2025-07/2025%20Okanagan%20Granfondo%20Traffic%20notice.pdf ; route announcement 28 Nov 2024: https://www.granfondoguide.com/Contents/IndexFull/8238/register-now-for-the-2025-okanagan-granfondo ; completed-ride GPS record 13 July 2025 (99.4mi/159.9km, 5,690ft/1,734m): https://ridewithgps.com/trips/309000665 |
| Final date/start | **Sunday 13 July 2025**, 6:30am, Skaha Lake Park Promenade (not downtown) | Same City of Penticton notice above |
| Field size (final years) | 2025: City permit for 2,000, on-site report ~1,700 starters. 2024: ~2,300. 2022 (record rebound): 3,000 registrants — this is the origin of the prior file's "3000+" | 2025: https://www.penticton.ca/sites/default/files/2025-07/2025%20Okanagan%20Granfondo%20Traffic%20notice.pdf and https://www.kelownanow.com/watercooler/news/news/Penticton/The_beauty_and_the_abject_heartbreak_of_the_2025_Okanagan_Granfondo/ (14 July 2025); 2024: https://granfondodailynews.com/2024/07/16/bold-40km-attack-earns-local-lee-agur-win-at-okanagan-gran-fondo/; 2022: https://globalnews.ca/news/8982575/okanagan-grandfondo-2022/ |
| Route options (final, 2025) | Four distances: Granfondo 155km, Velocefondo 120km, Mediofondo 85km, Cortofondo 35km (not three as the prior file implied) | City of Penticton notice, 24 June 2025; results report 14 July 2025: https://www.granfondoguide.com/Contents/IndexFull/8626/winkler-and-agur-fastest-at-the-13th-edition-of-the-okanagan-granfondo |
| Entry fee (last published, now closed) | CA$225 + Race Roster fee + taxes (Granfondo/Velocefondo/Mediofondo); CA$150 + fees/taxes (Cortofondo) | Orphaned 2026 Race Roster listing: https://raceroster.com/events/2026/60204/okanagan-granfondo |
| Official website | Final domain **okanagangranfondo.com** now carries the farewell/discontinuation notice. **granfondoaxelmerckx.com** was the historical Axel Merckx/Prospera-era domain. | https://okanagangranfondo.com/ (discontinuation notice, Oct 2025) |

## Distance/elevation reconciliation across eras (why the old file was internally inconsistent)
- **2017**: nominal 160km course, Castanet News reported 1,600m elevation gain for that era's route. https://www.youtube.com/watch?v=Vpw6fnoBsr4 (9 July 2017)
- **2022**: organizers removed the opening "Vancouver Hill" section, shortening the long route to 153km. https://www.pentictonnow.com/watercooler/news/news/Penticton/Renamed_modified_and_busier_than_ever_Granfondo_s_back_in_town (7 July 2022); Sportstats results confirm "Granfondo (153 KM)": https://sportstats.one/event/okanagan-granfondo/leaderboard/116055
- **2023**: a temporary Summerland-slide reroute produced a 121km course with 1,200+ m climbing — likely origin of the prior file's 1,200m figure. https://www.granfondoguide.com/Contents/Index/7467/thousands-of-cyclists-take-part-in-the-11th-okanagan-granfondo
- **2024**: restored 153km course, downtown start near Main Street/Lakeshore Drive, via Summerland. https://www.penticton.ca/sites/default/files/2024-07/2024%20Granfondo%20public%20notice.pdf (July 2024)
- **2025 (final)**: fully redesigned routes; long course became 155km / 1,700+m, Skaha Lake Park start. https://www.granfondoguide.com/Contents/IndexFull/8238/register-now-for-the-2025-okanagan-granfondo (28 Nov 2024)

The prior file's 160.9km/1,200m combined incompatible route vintages (distance
from the old nominal 100-mile course, elevation most plausibly from the
shortened 2023 course). Use 155km/1,700+m as the honest final-edition figure.

## Feature-status clarification
- **Summerland KOM climb**: historical only — was part of the course through 2017-2024 editions (2017: Peach Orchard Road, ~1.7km at 7%, ~km 25), but the final 2025 course dropped the Summerland leg for a Skaha Lake Park routing. https://okanagangranfondo.com/newsletter/july2017riderinfo/ (July 2017)
- **Downtown Penticton start, Okanagan Lake**: historical main-event features through 2024; the final 2025 route explicitly replaced the downtown/Summerland opening with a Skaha Lake Park start. https://www.kelownanow.com/watercooler/news/news/Penticton/The_beauty_and_the_abject_heartbreak_of_the_2025_Okanagan_Granfondo/ (14 July 2025)
- **Skaha Lake, wine country, Osoyoos**: valid for the final 2025 long course, which ran Eastside Road through Okanagan Falls, Highway 97 through Oliver and Osoyoos, Highway 3 through Cawston/Keremeos, and back via Twin Lakes, White Lake, the observatory and Kaleden. Included a timed KOM/QOM ~38km in. https://www.penticton.ca/sites/default/files/2025-07/2025%20Okanagan%20Granfondo%20Traffic%20notice.pdf (24 June 2025)

## Bottom line for the profile
Defensible current status: **inactive/defunct**. Final edition: 13 July 2025
(13th). Final long-route distance/elevation: 155km / 1,700+m. Final field:
~1,700-2,000. The organizer, city notices, and orphaned registration listing
are all mutually consistent on this — there is no live source claiming a 2026
race actually happened.

## Sol adversarial review addendum (2026-07-24)
Reviewed via `codex --search exec -m gpt-5.6-sol`, cross-checking the written profile against fresh web search, with specific focus on independently re-verifying the load-bearing discontinuation claim.
- **Discontinuation claim CONFIRMED independently** — sol found an additional corroborating source, Global News reporting the cancellation: https://globalnews.ca/news/11462713/okanagan-granfondo-cancelled/ — alongside the organizer's own 2 Oct 2025 notice and the stale/closed Race Roster listing already in the primary research. High confidence.
- **Founded year corrected: 2011, not 2013.** Sol found the original 2011 launch announcement (https://cyclingmagazine.ca/sections/news/granfondo-axel-merckx-okanagan-announced-for-july-10-2011/). This is independently consistent with the profile's own youtube_data: a 2019-uploaded video invites riders to "the 10th ... Granfondo Axel Merckx Okanagan (PGAMO)" on 12 July 2020 — 2020 minus 9 years (for a 10th edition) lands on 2011, confirming sol's correction against data already in the file. Corrected `history.founded` and all "13-year"/"2013-2025" framing to "13 held editions, 2011-2025."
- **Original title sponsor corrected**: launched as the "Valley First Granfondo Axel Merckx Okanagan," not "Prospera" — Prospera became title sponsor later in the event's run. Source: https://globalnews.ca/news/71045/granfondo-gets-title-sponsor/. Corrected origin_story.
- Removed an over-specific, unsupported claim that the km-38 timed KOM/QOM sits specifically "on the Highway 3 climb toward Keremeos" — the source only confirms "after 38km," not the exact climb/road. Reworded course_description to avoid asserting an unconfirmed location.
- Reworded field_size to avoid mixing the ~1,700 observed 2025 starter count with the city's 2,000-rider permit ceiling as if both were the same figure.
- Removed "RBC GranFondo Banff" from final_verdict.alternatives — sol flagged it as not confirmed currently active (most recent located notice was archived from 2016); replaced with guidance to verify any Canadian gran fondo's current status individually rather than naming a second possibly-stale race.
- Softened unsupported "well-regarded"/trust language per sol's voice note.
