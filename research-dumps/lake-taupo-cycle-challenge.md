# Lake Taupō Cycle Challenge — Research Dump

Debt-sweep verification pass (batch 6), 2026-07-24.

## Eligibility
- **Status: active.** Taupō, New Zealand. 160 km circumnavigation of Lake Taupō, held late November annually (2026: November 28), celebrating its 48th running in 2026.
- Source: https://www.cyclechallenge.com/ (official organizer site).

## Size claim — CONFIRMED TRUE
Flagged claim: history.origin_story — "Walter's ride became New Zealand's largest cycling event — and one of the Southern Hemisphere's greatest."

- Independently corroborated by four sources found via WebSearch:
  - lovetaupo.com (official Taupō tourism site): "the Lake Taupō Cycle Challenge, New Zealand's largest cycling event"
  - Te Ara Encyclopedia of New Zealand (teara.govt.nz, NZ government reference): confirms the event's scale and history
  - Wikipedia (Lake Taupo Cycle Challenge): consistent history
  - sportzhub.com: "The Lake Taupō Cycle Challenge: A Rich Legacy of Endurance and Community"
- History details corroborated: founded 1977 by Taupō schoolteacher Walter de Bont with 26 riders (all 26 finished — the only time that's happened); peaked at 10,000+ riders in the late 2000s; drew ~4,000 riders + 6,000 spectators by the time Walter died 39 years after the first ride; more than 200,000 people have now ridden around the lake.
- No correction needed — the size claim and surrounding history are accurate as written.

## Citations
Profile already carries 8 citations (well above the 3-minimum), including Wikipedia, teara.govt.nz-adjacent lovetaupo.com, sportzhub.com, and the official site. No additions needed.

## Sol adversarial review (2026-07-24, gpt-5.6-sol, read-only, foreground)
The "largest cycling event" claim itself was independently verified true before the sol pass ran, and sol raised no contrary finding on that point. However, sol caught a real issue elsewhere in the same file that I'd missed: **applied** — `biased_opinion.summary` ("Every last Saturday of November since 1977...") and `biased_opinion.strengths[0]` ("47 years of unbroken tradition") both asserted unbroken annual continuity. RNZ (rnz.co.nz, verified via WebFetch) confirms the event was cancelled in 2020, 2021, and again in February 2022 due to the Covid-19 red traffic light setting — a documented three-year gap, not unbroken tradition. Corrected both fields to acknowledge the Covid-era cancellations rather than claim continuity; added the RNZ citation. No findings rejected.

## JSON changes made
- `eligibility.verified`: 2026-07-17 → 2026-07-24
- `eligibility.notes`: added, documenting the four-source corroboration of the "largest cycling event" claim
- No text/vitals corrections needed — all flagged and vitals content verified accurate
- No fondo_rating changes (rubric-lock held)
