# Korea Epic Ride — Editorial Wave 10 Research Notes

Source: codex exec (gpt-5.6-sol, web search), 2026-07-24.

## MAJOR IDENTITY CORRECTION
The stub's identity was substantially wrong. Korea Epic Ride is real, but:
- Based at Songjeon Beach, Sonyang-myeon, Yangyang-gun, Gangwon-do — NOT Incheon.
- An ULTRA-DISTANCE, SELF-SUPPORTED BIKEPACKING event, not a conventional
  supported gran fondo or timed road race. Riders arrange their own food,
  accommodation, navigation, repairs, and medical response.
- None of the current official routes is ~100km/62mi. The only close match was
  a 109km short option offered in 2022, no longer part of the current route set.
Official: https://www.koreaepicride.kr/intro

Unquestionably distinct from Yangyang Gran Fondo (also in this database):
Korea Epic Ride is founder Kiseok Uhm's self-supported June bikepacking ride;
Yangyang Gran Fondo is a Yangyang County-hosted, chip-timed road marathon with
traffic management, medals, and supported courses (151/68km, latest edition
documented as April 26, 2025 — the sibling profile's "October" date also
appears stale and should be checked in that profile's own wave pass).

## Status: cancelled (2026 edition)
Organizer explicitly states the 2026 Korea Epic Ride is cancelled on its own
event page, which also defines it as a self-supported group ride, emphatically
"not a race." Page retains intended registration/schedule/payment details
beneath the cancellation notice.
Source: https://www.koreaepicride.kr/intro

## Verified current route specs (all self-supported ultra-distance)
- Epic Road 1000: 1,024 km, 17,670 m climbing, fully paved/road-bike compatible
- Epic Offroad 500: 500 km, 12,240 m; 276km unpaved, 221km paved, 3km by ferry
- Epic Offroad 300: 328 km, 8,004 m; ~194km unpaved, 134km paved, est. 2-5 day
  completion
Last completed edition: June 6, 2025 (three routes then ~1,046km/18,700m,
678km/16,100m, 324km; entry fee KRW100,000).
Before cancellation, 2026 was to start 07:00 June 6, fee KRW100,000/US$75.
Source: https://www.koreaepicride.kr/epicroad1000 ,
https://www.koreaepicride.kr/epicoffroad500 ,
https://www.koreaepicride.kr/epicoffroad300 ,
https://www.bikem.co.kr/article/read.php?num=15652

## TAXONOMY FLAG (catalog_flags, not a discipline-enum change)
Mountainous ultra-bikepacking through Gangwon-do — remote forest roads, rural
mountain settlements, major passes (25km Hangyeoryeong ascent, Dolsanryeong,
Haesanryeong, Manhangjae, Anbandegi), East Sea coast. Off-road routes include
gradients exceeding 15%, rough gravel descents, forest roads vulnerable to
landslides/washouts. Simultaneous grand depart, no timing stops or organizer
support; navigation/compliance rely on GPS and rider honesty. This is not a
road gran fondo in any sense the fondo_rating dimensions were built for
(road_surface, organization, field_depth, etc. assume a supported timed race).
Flagging for a human call on database placement, per the flandrien-ride
precedent — discipline enum left unchanged.

## Organizer & history
Founded 2020 by Kiseok Uhm, also founder of Seorak Gran Fondo. 2025 edition
was the sixth running. Purpose: introduce riders to remote Korean landscapes
while forcing self-reliance. In 2022, 16 riders attempted the full 536km
course; 8 completed it.
Source: https://bikepacking.com/plog/2022-korea-epic-ride-event-recap/

## Credible criticisms
No substantiated scandal, but real documented limitations: no organizer
support or event insurance (riders assume full responsibility for navigation,
logistics, medical care, accidents); forest roads may be washed
out/impassable with riders finding their own detours; a detailed 2022 rider
account reports three days of rain, GPS failure, long stretches without
supplies, dangerous after-dark fatigue, and no organizer present at the
finish. The official site is also internally inconsistent about maximum
elevation (overview says Road 1000 tops at 1,030m; the route page places
Manhangjae at 1,300m). The cancelled-event page still displays prospective
registration/payment info and a no-refund statement, which creates avoidable
post-cancellation ambiguity.
Source: https://bikepacking.com/plog/2022-korea-epic-ride-event-recap/ ,
https://www.koreaepicride.kr/rule
