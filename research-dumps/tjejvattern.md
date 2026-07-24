# Research Dump: TjejVättern

## Quick Facts
- Women-only 100 km recreational road ride in Motala, Sweden, part of Vätternrundan Bike Week — a genuinely separate registered event, not a category within the main Vätternrundan
- Founded 1991 (official Tjejvättern history: continuous participation since that year; the main Vätternrundan history separately calls it "newly launched" in 1992 — treat 1991 as the sourced founding year)
- 2026 edition: held June 6, 2026 (completed, not upcoming as of this research), 07:30 first start, 2,131 starters / 2,118 finishers
- Minimum age: 12 in the participation year
- Next edition already scheduled: June 12, 2027 — confirms the event remains active
- Distance: official/marketed value is 100 km / 62.1 mi (organizer consistently uses this); a 2018 rider GPS trace measured 100.37 km. The previously-filed 99.8 km figure could not be independently verified — use 100 km/62.1 mi as the defensible value
- Elevation: the organizer does not publish a numeric total-climbing figure in accessible course material. Best available route-specific measurement: ~325 m/1,066 ft from a rider-recorded 2018 GPS track — treat as approximate/secondary-sourced, not official. The previously-filed elevation_ft: 0.0 (with elevation_m: null) was wrong either way — do not present as "no climbing"
- 2026 entry fee: adults SEK 712 (early bird) to SEK 1,100 (on-site); ages 12-14 SEK 356-525 depending on tier
- Aid stations: Borghamn (32 km), Rök (55 km), Skänninge (79 km)

## Course Profile
Starts in Motala, travels south through Vadstena and Omberg, then returns inland across the Östergötland plain through Rök and Skänninge back to Motala. Runs alongside Lake Vättern but does NOT circumnavigate it (unlike the full Vätternrundan). Generally flat to rolling; Omberg supplies the notable climbing section, described by the organizer as challenging but not a mountain stage. Surface is 100% paved public road/asphalt, open to ordinary traffic per official rules.

## Event-Family Identity (dedupe-critical)
TjejVättern is a genuinely SEPARATE, distinctly-registered event, not a women's category folded into another event:
- Its own event page, registration product, women-only eligibility, start window, and results feed
- Vätternrundan 100 km (a different, mixed-gender/e-bike-eligible event) starts later in the day (12:30 in 2026) and shares some course infrastructure/timing checkpoints, but is a separate registered product
- Halvvättern is a separately registered 150 km event
- The full Vätternrundan is currently 315 km (not the commonly-cited "300 km" — that figure is historical/colloquial) and is the event that actually circles the lake
- This database already correctly carries three separate profiles: `tjejvattern.json` (this one), `vatternrundan.json`, and `halvvattern.json` — matching the organizer's own taxonomy. No dedupe/merge action needed.
- No rebrand found beyond older material using the spelling "Tjej-Vättern" (current official style: "Tjejvättern") and an older 90 km distance reference — historical styling/distance drift, not a different event.

## YouTube / Rider-Intel Identity Check — PURGE REQUIRED
All 5 videos currently filed under this TjejVättern profile are wrong-event content and must be purged:
| Video ID | Actual subject | Verdict |
|---|---|---|
| auSQO4RP9xw | Support-vehicle vlog explicitly describing Vätternrundan 2017 (male riders, overnight support ops) | Purge |
| uuf-irIv7kE | Vätternrundan 2009, explicitly described as "300 km around the lake" | Purge |
| vC12m5ARvQ4 | Promotional clip following Motala AIF CK during Vätternrundan 2016 | Purge |
| uKoQd7Pqt7k | Explicitly "Halvvättern 2015, 150 km" | Purge |
| 7CdREoxymPw | Explicitly "Vätternrundan 2013, 300 km" | Purge |

The associated `rider_intel` (race_day_tips, additional_quotes, search_text) was derived entirely from auSQO4RP9xw (a Vätternrundan video), not TjejVättern — must be purged alongside the videos. The generated "garbage zone every kilometer" claim in the existing rider_intel appears to be a misreading of the source transcript's "a garbage zone in one kilometer" and should not be retained regardless.

## Sources
- Official 2026 results (Tjejvättern 100 km listed separately, date): https://result.vatternrundan.se/search/tv
- Official Bike Week 2026 schedule (07:30 start): https://www.vatternrundan.se/en/news/opening-bike-week-2026
- Official Tjejvättern event page (women-only, age 12+, next edition 2027-06-12): https://www.vatternrundan.se/en/races/tjejvattern-100km
- Official course description (route via Vadstena, Omberg, Rök, Skänninge): https://vatternrundan.se/tjejvattern/om-loppet/banan/
- Official 2026 guide (aid stations): https://www.vatternrundan.se/en/guide
- Official press release (2,131 starters, field-size confirmation): https://press.vatternrundan.se/posts/pressreleases/over-8-000-till-start-under-cykelveckans-fors
- Official archived 2026 fee schedule: https://old.vatternrundan.se/en/registration/payment/
- Official Tjejvättern history (founded 1991): https://vatternrundan.se/tjejvattern/sv/historik/harlig-blandning-av-veteraner-och-forstagangscyklister/
- Official Vätternrundan history (1992 reference, for comparison): https://www.vatternrundan.se/en/our-story
- Official rules (paved roads, open to traffic): https://www.vatternrundan.se/en/rules
- Official Vätternrundan 100 km page (separate event, distinct from Tjejvättern): https://www.vatternrundan.se/en/races/vatternrundan-100km
- Official Vätternrundan 315 km page (full lake circuit, current distance): https://www.vatternrundan.se/en/races/vatternrundan-315km
- Official Halvvättern page (separate 150 km event): https://www.vatternrundan.se/en/races/halvvattern-150km
- 2018 rider GPS trace (100.37 km, ~325 m elevation): https://www.wikiloc.com/cycling-trails/tjejvattern-100-km-28494672
- Course surface listing (100% asphalt): https://www.jogg.se/Tavling/Tavling.aspx?id=643672
- Older 90 km distance reference (historical): https://www.utsidan.se/cldoc/vatternrundan-2009-byter-startplats_11659.htm

## Notes
Research conducted 2026-07-24 via codex gpt-5.6-sol foreground web search, editorial wave 6 batch C. Primary finding requiring action: purge all youtube_data and rider_intel — every piece of that content describes a different event in the same organizer's family (Vätternrundan or Halvvättern), not TjejVättern itself. This is exactly the "wrong-product profile" trap flagged in the shared pipeline reference.
