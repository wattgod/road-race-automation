# Research Dump: Granfondo Tre Valli Varesine

Verified 2026-07-24 via live web search (codex/gpt-5.6-sol) + direct curl verification of every URL below.

## Quick Facts
- Location: Varese, Lombardy, Italy.
- 2026 dates: October 3-4, 2026 (matches the existing "2026: October 4" date_specific for the main Gran Fondo day; October 3 is a companion time-trial day).
- Course: 126 km Gran Fondo / 1,993 m gain; 100 km Medio Fondo / 1,447 m gain — matches existing JSON vitals.
- Additional 2026 status: Varese is also hosting the 2026 UEC Gran Fondo European Championships alongside the UCI World Series stop.

## UCI Gran Fondo World Series Status — VERIFIED TRUE
The tagline ("A 126 km UCI World Series qualifier with 1,993m of climbing"), biased_opinion.verdict ("Prestige-driven UCI qualifier with legitimate teeth"), final_verdict.one_liner, and final_verdict.should_you_race ("targeting UCI World Championships qualifiers") claims are all confirmed accurate.

- Live UCI Gran Fondo World Series calendar lists Tre Valli Varesine under "Qualifiers 2026-2027" for October 3-4, 2026, Varese. https://ucigranfondoworldseries.com/en/calendar/ (HTTP 200 via curl --resolve). Direct-search confirmed "Tre Valli Varesine" and "Varese" both appear on the live calendar page.
- A UCI GFWS announcement confirms the event "remains a qualifier for the UCI Gran Fondo World Championships" for 2026, separate from and in addition to the UEC European Championships being co-hosted the same weekend. https://ucigranfondoworldseries.com/en/uec-granfondo-european-championships-awarded-to-varese-on-3-4-october/ (HTTP 200)
- UCI Gran Fondo World Series regulations page (qualification mechanism, general reference). https://ucigranfondoworldseries.com/en/regulations/ (HTTP 200)

## "Official World Championships Qualifier" / 2018 Worlds Host Claim — VERIFIED TRUE
The `history.origin_story` claim that Varese "joined the UCI Gran Fondo World Series as an official World Championships qualifier" and hosted the "2018 UCI Gran Fondo World Championships" is confirmed:

- UCI's own post-event report on the 2018 UCI Gran Fondo World Championships confirms it was held in Varese/Italy, with "more than 2,500 qualified riders from 60 nations" racing for age-group world titles. https://www.uci.org/article/2018-uci-gran-fondo-world-champions-crowned-in-italy/74arFHp2FvngpaNUrvDJz1 (HTTP 200)

## Minor Precision Note (not corrected — outside this batch's flagged scope)
The UCI GFWS 2026 UEC-championships announcement describes the format as "22 km time trial; 101 km mediofondo; 126 km granfondo" — the existing JSON vitals/route_options use 100 km for the Medio Fondo (a pre-existing, pre-batch figure, matching trevallivaresine.info). This 1 km difference is immaterial and not one of the batch's flagged UCI-affiliation claims, so no JSON change was made — noting it here for a future vitals-precision pass.

## Eligibility
- Status: active. Matches existing eligibility block (verified 2026-07-17, source trevallivaresine.info). Reconfirmed live via the UCI GFWS calendar and the 2026 UEC-championships announcement.

## Citations (curl-verified 2026-07-24)
1. UCI Gran Fondo World Series live calendar — https://ucigranfondoworldseries.com/en/calendar/ (HTTP 200)
2. UCI GFWS announcement — UEC Gran Fondo European Championships awarded to Varese, 3-4 October — https://ucigranfondoworldseries.com/en/uec-granfondo-european-championships-awarded-to-varese-on-3-4-october/ (HTTP 200)
3. UCI.org — 2018 UCI Gran Fondo World Champions Crowned in Italy — https://www.uci.org/article/2018-uci-gran-fondo-world-champions-crowned-in-italy/74arFHp2FvngpaNUrvDJz1 (HTTP 200)
4. UCI Gran Fondo World Series regulations page — https://ucigranfondoworldseries.com/en/regulations/ (HTTP 200)

Note on sandbox DNS: `ucigranfondoworldseries.com` and `www.uci.org` fail to resolve via this environment's default resolver (`curl: Could not resolve host`) but resolve via `dig`. All such URLs above were confirmed HTTP 200 using `curl --resolve host:443:<resolved-ip>`.
