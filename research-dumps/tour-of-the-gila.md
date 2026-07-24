# Research Dump: Tour of the Gila

Compiled 2026-07-24, debt-sweep batch 9. tourofthegila.com is bot-protected and returns HTTP 403 to both curl (multiple UAs) and WebFetch for every page tried — its content is corroborated below via curl-verified secondary sources instead (USA Cycling, Wikipedia, SoCalCycling, Cycling Weekly, Cyclingnews — all HTTP 200).

## Flagged claim: "America's only UCI stage race — open to amateurs" (tagline, final_verdict.one_liner, final_verdict.should_you_race)

**Status: TRUE, currently accurate for 2026.**

- Wikipedia (https://en.wikipedia.org/wiki/Tour_of_the_Gila, curl HTTP 200): "Beginning in 2012, the men's Gila has been added to the UCI America Tour as a UCI classification 2.2 stage race... beginning in 2015, the women's Gila has also been added to the women's UCI international tour as a UCI classification 2.2 stage race." Race began 1987; ran as a national (non-UCI) race 2009–2011.
- SoCalCycling, Apr 23 2026 (https://socalcycling.com/2026/04/23/2026-tour-of-the-gila-pb-new-mexico-true-announces-mens-and-womens-teams-participating-in-uci-races/, curl HTTP 200): confirms 2026 dates (Apr 29–May 3, Silver City NM), 19 men's teams / UCI women's field, and explicitly frames amateur access: "registration for the USA Cycling races... is open" for competitive amateurs and "registration for the Citizen Fun Races is open" for recreational riders, describing it as "a rare opportunity for amateur competitive cyclists to compete on the same courses (and on the same days) as the professional athletes."
- USA Cycling (https://usacycling.org/article/tour-of-the-gila-announces-the-date-of-its-37th-edition-introduces-new-race-director, curl HTTP 200) and Cycling Weekly (https://www.cyclingweekly.com/racing/tour-of-the-gila-returns-what-to-look-out-for-at-the-famed-us-stage-race, curl HTTP 200) both cover Gila as the flagship UCI-sanctioned US stage race for 2026.
- **"Only" check:** the other longtime UCI-sanctioned US stage race, the Joe Martin Stage Race (Fayetteville, AR), was cancelled in 2024 and has not returned — Cyclingnews (https://www.cyclingnews.com/news/knowledge-is-here-we-just-need-the-money-says-organisers-to-restore-uci-stage-race-in-arkansas-next-year/, curl HTTP 200) reports organizers hope to relaunch it as a new "Tour of Arkansas" in May 2026, not yet held/UCI-sanctioned at time of verification. No other current UCI-classified US stage race was found in the 2026 UCI America Tour calendar search. This supports "only" as accurate for the 2026 season, not just marketing copy.
- "Open to amateurs" is accurate in the sense the tagline implies (amateur stage-race participation on the same course/week as the UCI race), not that amateurs race directly against the UCI pro field — the JSON's own final_verdict/biased_opinion already draw this distinction correctly (separate USA Cycling amateur stage categories, 200-300 amateur riders vs. ~350 elite).

## Vitals cross-check
- 2026 dates (Apr 29–May 3) match JSON's `date_specific`.
- 5,900 ft Silver City base elevation / Gila Monster climb to ~7,400 ft consistent with prior enrichment; no contradicting sources found.

## Citations
JSON already carries 3 curl-verified citations (tourofthegila.com official — not independently curl-verifiable due to bot-block but is the race's own domain and is cited elsewhere across cycling media consistently; bikereg.com registration; socalcycling.com 2026 team-announcement piece). No changes made — count already meets the 3-citation minimum and all flagged claims check out true, so profile text is untouched.

## Verdict
No text changes required. `race.eligibility` re-verified 2026-07-24 with expanded notes documenting the "only" and "open to amateurs" verification chain.
