# Research Dump: Maraton Franja BTC City

Wave: debt-sweep batch 7 (2026-07-24). Purpose: back-fill missing research dump
for a pre-campaign profile; verify UCI affiliation claims flagged by
`audit_fabricated_claims.py` (no dump previously existed).

## Eligibility

- **Status: active.** Confirmed via official site (franja.org) and the UCI Gran
  Fondo World Series (UCI GFWS) official calendar and event pages.
- The 45th Marathon Franja BTC City ran June 12-14, 2026 (Ljubljana, Slovenia) —
  already held for this year; 2027 dates not yet published by the organizer.
- Source: https://franja.org/ (official) — HTTP 200 verified.
- Source: https://ucigranfondoworldseries.com/en/franja-maraton-btc-city/ (UCI GFWS official event page) — HTTP 200 verified.
- Source: https://ucigranfondoworldseries.com/en/calendar/ (UCI GFWS 2026 calendar, 36 qualifiers) — HTTP 200 verified. Maraton Franja BTC City listed Fri Jun 12 - Sun Jun 14 2026, Ljubljana, Slovenia.

## Vitals

- Distance: two road routes, 158 km and 100 km, from Ljubljana (BTC City) through the Slovenian countryside.
- Time trial: 21.2 km flat out-and-back Ljubljana-Domžale-Ljubljana; serves as the official time-trial qualifier for the UCI Gran Fondo World Championships.
- Founded 1982; 2026 edition was the 45th.
- Source: https://www.granfondoguide.com/RaceDashboard/UCIGranFondoWorldSeries/1/9219/vesna-alegro-baznik-and-matic-gro%C5%A1elj-take-victory-at-the-2026-uci-maraton-franja-btc-city (race report, 2026 results) — corroborates active 2026 running.

## Flagged claim: [UCI affiliation] "UCI World Series founding member" (final_verdict.one_liner)

**TRUE.** GranFondoGuide's UCI GFWS coverage states: "First held in 1982, the
Slovenian classic has grown into one of Europe's most iconic Granfondos and
has been a cornerstone of the UCI Gran Fondo World Series since the series
launched in 2011. Maraton Franja BTC City (Slovenia) has been part of the
series since its inception." This directly supports "founding member" — the
race has been on the UCI GFWS calendar every year since the series began in
2011.
- Source: https://www.granfondoguide.com/Series/UCIGranFondoWorldChampionship — HTTP 200 verified.

## Flagged claim: [UCI affiliation] "well-organized UCI gran fondo qualifier" (final_verdict.should_you_race)

**TRUE.** Confirmed current member of the 2026 UCI GFWS 36-race calendar (see
Eligibility above); the race's 21.2 km time trial and the marathon distance
both serve as UCI World Championship qualifying routes (top-25% age-group
finish qualifies).

## Verdict

No text changes required — both flagged UCI claims verified true and current
as of 2026. No catalog_flags needed.
