# Le Race — Research Dump

Debt-sweep verification pass (batch 6), 2026-07-24.

## Eligibility
- **Status: active.** Christchurch to Akaroa, New Zealand. 100 km one-day road classic, held annually (third Saturday of March; 2027: March 20).
- Source: https://lerace.co.nz/ (official site).

## World Championship / Olympic claim — CONFIRMED TRUE
Flagged claim: history.origin_story — "the Hall of Fame quickly accumulated names that would go on to Olympic and World Championship honours."

- Confirmed via direct curl + WebFetch of the official Hall of Fame page: https://lerace.co.nz/hall-of-fame/ (curl-verified 200; page title "Hall of fame | Le Race").
- Raw-content grep of the fetched HTML confirms the names Fowler, Roulston, McIlroy, and Villumsen all appear on the page.
- WebSearch corroboration of the page's own framing: "the Hall of Fame includes a long list of world champions, Olympic medallists and Commonwealth Games winners like Brian Fowler, Hayden Roulston and Kate McIlroy... Some of those competed in the heyday of their careers, while other young New Zealand talents used Le Race as a stepping stone to a professional career on the cycling world tour" — i.e. the Hall of Fame explicitly includes both riders who arrived already decorated and riders who used Le Race as a stepping stone, matching the profile's "go on to" framing either way.
- Specific credentials cross-checked: Linda Villumsen — first NZer to win a world road title (2015 World Champion); Hayden Roulston — double Olympic Games track medallist. Both are separately documented (Wikipedia, PressReader) as Le Race participants.
- No correction needed — claim is accurate and well-sourced.

## Other history spot-checked (not flagged, verified in passing)
- Founded 1999; the 2001 death of competitor Vanessa Caldwell and the subsequent legal case against organizer Astrid Anderson (2003 conviction, 2004 Court of Appeal overturn) is corroborated by Wikipedia. Not touched — already accurate in the profile.

## Citations
Profile already carries 10 citations (well above the 3-minimum), including Wikipedia, the official site, ccc.govt.nz, and race reports. Added no new citations — the Hall of Fame page itself (lerace.co.nz/hall-of-fame/) is the same domain already cited via lerace.co.nz, so no new citation entry was needed.

## Sol adversarial review (2026-07-24, gpt-5.6-sol, read-only, foreground)
The general Hall of Fame / "Olympic and World Championship honours" claim itself was verified true and sol did not dispute it, but sol caught a real specific-attribution error I'd missed: **applied** — `biased_opinion.strengths[1]` said "Hall of Fame includes Olympic medalists Hayden Roulston and Kate McIlroy." Verified via WebSearch + olympic.org.nz: Kate McIlroy competed at the 2012 Olympics (triathlon, 10th place) and the 2006 Commonwealth Games (3000m steeplechase, 5th place) but won no medal at either — she is an Olympian, not an Olympic medallist. She IS a genuine World Champion (2005 World Mountain Running Championships) and was named NZ Sportswoman of the Year. Corrected the line to "Olympic medalist Hayden Roulston, world champion Kate McIlroy" — Roulston's "Olympic medalist" label is independently confirmed accurate (double Olympic track medallist) and was left as-is. Added an olympic.org.nz citation. No findings rejected.

## JSON changes made
- `eligibility.verified`: 2026-07-22 → 2026-07-24
- `eligibility.notes`: added, documenting the Hall of Fame page verification
- No text/vitals corrections needed — flagged claim verified accurate
- No fondo_rating changes (rubric-lock held)
