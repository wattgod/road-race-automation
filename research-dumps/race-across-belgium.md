# Race Across Belgium — Research Dump (Editorial Wave 4, 2026-07-24)

**This slug is a retired/duplicate record.** Full research and citations live in `research-dumps/race-across-benelux.md` — this file is the slug-matched pointer required for `audit_fabricated_claims.py` (which matches research dumps by filename prefix against `race.slug`).

## Summary

Research conducted via codex gpt-5.6-sol foreground web search, checked 2026-07-24, determined with 99% confidence that "Race Across Belgium" and "Race Across Benelux" are the **same event, renamed and geographically expanded**, not two coincidentally-similar distinct races:

- Race Across Belgium launched 19 August 2021 in Arlon — the first Belgian ultra-cycling race, initiated by Michel Mussot. [TV Lux founding report](https://www.tvlux.be/actu/sport/cyclisme/la-premiere-course-belge-d-ultra-cyclisme-est-partie-d-arlon-ce-jeudi-matin_38220).
- It ran under that name through five editions (2021-2025). The final 2025 flagship (Arlon to Braine-l'Alleud) measured approximately **1,015 km / 7,200 m** per the organizer's own [18 Sep 2025 retrospective](https://www.raceacrossseries.com/blog/une-course-de-vlo-mmorable-en-belgique-2025).
- For the 2026 season (announced Oct-Nov 2025), the organizer renamed and geographically expanded the event into **Race Across Benelux**, extending the route from Belgium-only into a Netherlands-Belgium-Luxembourg crossing (Amsterdam start, ~1,048 km / ~11,900 m).
- The official event page — still hosted on the legacy `race-across-belgique-2025` URL — [states outright](https://www.raceacrossseries.com/race-across-belgique-2025): "La Race Across Belgium change de nom et devient la Race Across Benelux."
- The 2026 official calendar and rules pages list Benelux only; there is no separate active "Race Across Belgium" event as of this research.

## Database action taken (2026-07-24)

This profile (race-across-belgium.json) is flagged `catalog_flags.duplicate_of: "race-across-benelux"` and `eligibility.status: "defunct"` (name retired, event continues under the new name). Its previously placeholder vitals (999.4 km / 11,900 m — an exact copy-paste duplicate of race-across-benelux.json's own placeholder) were corrected to the real final 2025 Belgium-only edition figures (1,015 km / 7,200 m). No new full GOLD editorial (biased_opinion) was written on this duplicate record, consistent with the established no-further-editorial-on-dupes convention used for gfny-la-vaujany-alpe-dhuez.json. race-across-benelux.json is the canonical, actively maintained profile going forward.

Full citation list, route-by-route vitals, and the complete rename evidence chain are documented in `research-dumps/race-across-benelux.md`.
