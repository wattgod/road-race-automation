# Cyprus Gran Fondo — Research Dump

Debt-sweep verification pass, 2026-07-24. All URLs curl-verified live (HTTP 200) on 2026-07-24 unless noted.

## Eligibility
- **Status: active** (rescheduled to 2027, not cancelled). Paphos, Cyprus.
- Source: https://www.activatecyprus.com/granfondocyprus (curl-verified live).

## UCI affiliation claim — CONFIRMED TRUE
- Flagged claims: display_name "UCI Cyprus Gran Fondo"; tagline "3-day UCI Gran Fondo World Series qualifier in Mediterranean paradise"; final_verdict.one_liner "Strong T2 UCI stage race - qualification + tourism excellence."
- The registration page (https://www.activatecyprus.com/gran-fondo-cyprus-registration, curl-verified live) itself has **zero mentions** of the string "UCI" anywhere in its visible text (the one apparent "uci" match on that page is a false positive inside "St. Lucia" in a country-code dropdown).
- However, the organizer's main event page, https://www.activatecyprus.com/granfondocyprus (curl-verified live), explicitly states: "**UCI World Series Qualifier:** Secure your spot for the World..." and "Join the UCI Gran Fondo World Series in Cyprus." This directly and unambiguously supports the display_name/tagline/one_liner UCI claims — added as a citation and as the eligibility.source this pass, since it's a more precise match for the flagged claim than the registration page.
- The UCI GFWS calendar (https://ucigranfondoworldseries.com/en/calendar/, curl-verified live) lists "Cyprus Granfondo," Paphos, with status **"Postponed"** — same pattern as CRC-506 in this batch: a rescheduled (not cancelled) listing whose calendar date field hasn't caught up.
- Conclusion: claim is TRUE. No text correction needed.

## Date discrepancy noted (not corrected — used the stronger signal)
- The granfondocyprus page's `og:description`/meta tags say "Join the UCI Gran Fondo World Series in Cyprus (April 3-5, 2026)" — this appears to be a stale, uncorrected meta tag from an earlier version of the page.
- The same page's **visible H2 heading** reads "**2-4 APRIL 2027**," which matches the profile's existing `vitals.date_specific` ("2027: April 2-4") exactly. Treated the visible heading as the authoritative, current-intent source over the stale meta description; no vitals change made since the existing field was already correct.

## Citations (existing + added, spot-checked live 2026-07-24)
- https://www.activatecyprus.com/gran-fondo-cyprus-registration — 200 (registration page; confirmed the 2027 date, but no "UCI" text)
- https://www.activatecyprus.com/ — 200
- https://ucigranfondoworldseries.com/ — 200
- https://www.activatecyprus.com/granfondocyprus — 200 (new, added this pass — direct "UCI World Series Qualifier" language)

## Sol adversarial review
GPT-5.6-sol (read-only, foreground) reviewed this race. Verdict: CONFIRM — sol independently found the same granfondocyprus page with explicit "UCI World Series Qualifier" language and recommended leaving display_name as-is since the organizer's current materials (that page, at least) still use UCI branding, even though the specific registration-flow page dropped it. Applied — no text change; added the stronger citation.

## JSON changes made
- `eligibility.verified`: 2026-07-20 → 2026-07-24
- `eligibility.source`: activatecyprus.com/gran-fondo-cyprus-registration → activatecyprus.com/granfondocyprus (more precise match for the UCI claim)
- `eligibility.notes`: added (was previously absent), documents the UCI-language gap between the two organizer pages and the meta-tag date discrepancy
- Added one citation (activatecyprus.com/granfondocyprus)
- No claim text changes (flagged claims verified TRUE)
- No fondo_rating changes
