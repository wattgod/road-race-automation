# Seorak GranFondo — Research Dump (Editorial Wave 4)

Researched: 2026-07-24 via codex gpt-5.6-sol foreground web research.

## Date correction (critical fix)

Prior DB value: "2026: September TBD" — WRONG. Correct chronology:
1. Originally scheduled for **30 May 2026**.
2. On **20 Feb 2026**, organizer formally moved it to **20 June 2026** because 30 May conflicted with early voting and the road closures the race needs. Source: https://granfondo.co.kr/news1/news/view/315 (official date-change notice, dated 2026-02-20, prints both dates).
3. Official homepage now shows "Jun 20th 2026": https://granfondo.co.kr/
4. Inje County confirmed the June 20 date and expected field two days before the event: https://www.yna.co.kr/view/AKR20260618085200062 (Yonhap, 2026-06-18)
5. On race day (June 20), severe weather (up to 223mm rain recorded at Misiryeong) forced cancellation of the 208km Granfondo course — only the 105km Mediofondo ran. Source: https://granfondo.co.kr/courseinfo5 (official course-reduction status); https://en.yna.co.kr/view/AEN20260620000851315 (Yonhap, 2026-06-20)

No evidence the event runs twice a year. The "September TBD" figure is likely legacy contamination from the pandemic-disrupted 2020 edition, which was promoted for September 19, 2020 (https://www.granfondoguide.com/Events/Index/5168/giant-seorak-granfondo; https://www.zwift.com/events/view/1002301) — this is an inference, not a confirmed root cause, and is flagged as such.

Note: the raceplan.co.kr/rallys/view?crid=5196 URL cited in the prior eligibility record returned HTTP 403 to the research tool and could not be directly re-verified; its previously captured May 30 date was accurate for the ORIGINAL schedule but was superseded by the organizer's dated Feb 20 change notice.

## Distance, elevation, and climbs

- Distance: 208km (official course spec: https://granfondo.co.kr/courseinfo1_3 — 12hr limit, four Cat 2 climbs, two Cat 4 climbs, one HC climb, 5 feed stations). Prior DB value 207.6km unconfirmed.
- Elevation: ~3,800m per current secondary course database (K-Fondo: https://www.kfondo.cc/seorak). No organizer-published exact total ascent found. Corroborating data points: a 2016 organizer-hosted report called the course 208km/3,500m (https://seorak.raceplan.co.kr/news2/media/view/7?p=2&stx=&sty=); a 2018 rider's Garmin recorded 3,569m (https://taiwanpulse.com/tw/blog/24, explicitly noting the organizer hadn't published a cumulative figure). Prior DB value 3,505m is plausible as an old device-derived total but not certified.
- Climb table (all from official per-climb pages):
  - Guryongryeong: 6.4km, 395m gain, 6.1% avg, Cat 2 — https://granfondo.co.kr/courseinfo4
  - Jochimnyeong: 4.3km, 464m gain, 10.9% avg, Cat 2 — https://granfondo.co.kr/courseinfo4_2
  - Sseurijae: 6.3km, 335m gain, 5.2% avg, Cat 2 — https://granfondo.co.kr/courseinfo4_3
  - Pillye-Hangyeryeong: 10.5km, 487m gain, 4.4% avg, Cat 2 (final 2km reported at 10-15%) — https://granfondo.co.kr/courseinfo4_4
  - Reverse Guryongryeong: 20.5km, 870m gain, 4.2% avg, HC — https://granfondo.co.kr/courseinfo4_5
- The prior DB's "20km at km 180 with 10%+ pitches" description of the HC climb is NOT supported by official data (organizer gives 20.5km at 4.2% average) — removed from the updated profile.
- Two Cat 4 climbs are counted by the organizer but not individually named on current pages — not invented/named in the profile.

## Field size

- 2026 pre-event field: 4,497 (3,210 Granfondo + 1,287 Mediofondo). Source: https://www.yna.co.kr/view/AKR20260618085200062. These are entries/registrations, not verified starters/finishers, and the Granfondo course was subsequently canceled on race day — so these should not be described as riders who completed or started the 208km route.
- For scale: 2024 edition filled 5,213 places in 4 minutes (https://www.seoul.co.kr/news/society/2024/05/16/20240516500062).

## Course character

Inland Baekdudaegan mountain-pass circuit starting/finishing near Sangnam-myeon, Inje-gun — NOT a coastal Seoraksan gran fondo despite the name. Route crosses Saldun Pass, Guryongryeong, Jochimnyeong, Sseurijae, Hangyeryeong before returning. Source: https://www.yna.co.kr/view/AKR20260618085200062. Hangyeryeong-Osaek sits in the southern Seorak (Nam-Seorak) area per Korea National Park Service: https://www.knps.or.kr/front/portal/visit/visitCourseMain.do?menuNo=7020093&parkId=120400.

## History

"Founded 2015" (prior DB value) is incorrect. Correct timeline:
- June 5, 2010: 10 riders attempt a 265km, 7-pass club challenge — organizer calls this "the beginning of Seorak GranFondo." Source: official 2025 event book https://file.raceplan.co.kr/files/seorak/images/ebook_2025.pdf
- 2011: follow-up under name "Granfondo Gangwon," still an unsupported club ride. https://granfondo.co.kr/history7
- 2014: first scaled mass-participation edition with Giant Korea support (562 total: 309 Granfondo, 253 Mediofondo). https://granfondo.co.kr/history4
- Contemporary reporting treats 2014 as "the first race" even though the concept traces to 2010.

## Weaknesses/criticisms

- Weather cancellation is a proven, recent operational risk (2026 race-day cancellation of the long course).
- No nearby rail station: Jinbu KTX ~65km away, Chuncheon ~76km; Dong-Seoul buses ~1h50m, Hongcheon connection only once daily. https://granfondo.co.kr/conven3
- Race-morning logistics car-dependent: limited/prohibited parking near venue, bibs mail only within Korea. https://granfondo.co.kr/info4
- Language barrier real (Korean-first site, untranslated transport/parking/climb pages) but not absolute — foreigner admission and an official travel agency are listed. https://granfondo.co.kr/, https://granfondo.co.kr/conven3
- Heat risk historically documented: 2016 report describes a heat advisory, temps to 33°C. https://seorak.raceplan.co.kr/news2/media/view/7?p=2&stx=&sty=
- Traffic/construction exposure on Jochimnyeong specifically warned by organizer (cars, dump trucks, collision risk on the 10.9% climb). https://granfondo.co.kr/courseinfo4_2
- No credible evidence found for a "bad road surface" claim — not included in weaknesses.

## Yangyang Gran Fondo dedupe check (confirmed distinct)

Seorak GranFondo (this profile) is based in Sangnam-myeon, Inje-gun; standard courses 208km/105km; inland Baekdudaegan mountain-pass identity. Yangyang Gran Fondo (yangyang-gran-fondo.json, out of scope for this batch) is based at Yangyang Welcome Center in Yangyang-gun; latest confirmed edition April 26, 2025, 151km/68km courses, ~2,000 entrants, route starts at Naksan Bridge on the East Sea coast before turning toward Hangyeryeong/Inje. Source: https://www.yna.co.kr/view/AKR20250424072700062 (Yonhap, 2025-04-24); official site https://www.ygranfondo.com/ per https://www.kwnews.co.kr/page/view/2025011311283177701. These are confirmed genuinely distinct events, not duplicates — no changes made to yangyang-gran-fondo.json (out of this batch's scope).

## Sources consulted

- https://granfondo.co.kr/ and subpages (courseinfo1_3, courseinfo4 through courseinfo4_5, courseinfo5, history4, history7, conven3, info4, news1/news/view/315)
- https://raceplan.co.kr/rallys/view?crid=5196 (could not re-verify directly, HTTP 403 to research tool)
- https://www.yna.co.kr/view/AKR20260618085200062 (Yonhap 2026-06-18)
- https://en.yna.co.kr/view/AEN20260620000851315 (Yonhap 2026-06-20, weather)
- https://www.kfondo.cc/seorak (secondary course database)
- https://seorak.raceplan.co.kr/news2/media/view/7?p=2&stx=&sty= (2016 organizer-hosted report)
- https://taiwanpulse.com/tw/blog/24 (2018 international rider report)
- https://www.seoul.co.kr/news/society/2024/05/16/20240516500062 (2024 field-size report)
- https://file.raceplan.co.kr/files/seorak/images/ebook_2025.pdf (official 2025 event book/history)
- https://www.knps.or.kr/front/portal/visit/visitCourseMain.do?menuNo=7020093&parkId=120400 (Korea National Park Service)
- https://www.granfondoguide.com/Events/Index/5168/giant-seorak-granfondo, https://www.zwift.com/events/view/1002301 (2020 pandemic-year listings, "September TBD" origin inference)
