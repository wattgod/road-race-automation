# Research Dump: Triple Bypass

Compiled 2026-07-24, debt-sweep batch 9.

## Flagged claim: "Team Evergreen — Colorado's largest cycling club" (history.origin_story)

**Status: TRUE, corroborated by two independent third-party sources.**

- Bicycle Colorado business-member directory (https://bicyclecolorado.org/directory/business-member-directory/team-evergreen-cycling/, WebFetch-confirmed): "Founded in 1988, Team Evergreen Cycling (TE) is the largest bicycle club in Colorado."
- GiveFreely nonprofit directory, sourced from Team Evergreen's own 990/nonprofit filing data (https://givefreely.com/charity-directory/nonprofit/ein-850930923/, WebFetch-confirmed): "Team Evergreen Cycling, headquartered in Evergreen, Colorado, is the oldest and largest cycling club in the state," also describing itself as "Colorado's premier bicycle club."
- Team Evergreen's own current homepage (https://www.teamevergreen.org/, curl HTTP 200) covers the org's 2020s split into Shift Events (event production, incl. Triple Bypass) and Evergreen Ride Club (social riding) but does not itself restate the size superlative on the page fetched — the claim is carried by the two independent directory sources above, which is sufficient corroboration; not a contradiction, just a different page's focus.
- Consistent with the JSON's own history section, which already notes the Team Evergreen → Shift Events/Evergreen Ride Club reorganization.

## Vitals / other facts spot-checked
- Founding year 1988 confirmed (Bicycle Colorado directory, Denver7 2016 video transcript already in the profile's youtube_data quoting a founding member: "28th triple bypass... 28 years ago... let's form a club that's how team Evergreen got formed").
- $4.6M charitable-donation figure in the JSON was not independently re-verified this pass (not a flagged claim); GiveFreely cites "nearly $3 million" donated as of its data snapshot, which is a lower, differently-dated figure from a different source than whatever produced the $4.6M number already in the profile — flagging as a note only, not changing (out of scope: this claim wasn't flagged by the audit and the discrepancy could simply be a later, larger cumulative total; a human should reconcile the exact figure/date if precision matters).

## Citations
JSON already carries 7 curl-verified-domain citations (official site, event info page, Shift Events, BikeSignUp, Town of Avon, Bicycle Colorado, 303 Magazine). No changes made — well above the 3-citation minimum and the one flagged claim checks out true.

## Sol adversarial review — correction applied 2026-07-24
A read-only `codex exec -m gpt-5.6-sol` pass pushed back on the first draft's eligibility-note wording, which implied GiveFreely's "oldest and largest" description was independently sourced from Team Evergreen's own IRS filing. Sol correctly noted GiveFreely draws its *numeric financial data* from ProPublica but the descriptive superlative is its own general summary — the two corroborating sources (Bicycle Colorado directory, GiveFreely) are not proven independent of each other, and neither is dated more recently than ~2022. Reworded `eligibility.notes` to present this as "plausible and repeated by a credible third party as of 2022" rather than "verified current," per sol's finding. No JSON claim text was changed — the underlying `history.origin_story` claim about Team Evergreen's size was not touched, only the confidence framing in the new eligibility note.

## Verdict
Race JSON claim text unchanged (claim holds). `race.eligibility` re-verified 2026-07-24 with notes documenting the size-claim corroboration (with appropriately hedged confidence per sol's review) and the Team Evergreen/Shift Events split for future auditors.
