# L'Etape Portugal by Tour de France — Research Dump

Debt-sweep verification pass (batch 6), 2026-07-24.

## UCI-sanctioned comparison claim — CONFIRMED CONSISTENT, no correction
Flagged claim: final_verdict.should_you_race — "Skip if you expect the depth and intensity of UCI-sanctioned gran fondos."

- This is a comparative statement, not a claim that L'Etape Portugal itself is UCI-sanctioned. Research confirms L'Etape Portugal is an ASO/Podium Events franchise sportive (the L'Etape series is ASO's own private branding, distinct from the UCI Gran Fondo World Series). No UCI competition record was found for L'Etape Portugal.
- The comparison is therefore accurate: the profile correctly implies L'Etape Portugal does NOT carry UCI sanctioning, using that fact as a "skip if" caveat for readers specifically chasing UCI-caliber competitive depth. No correction needed.

## Eligibility — DOWNGRADED from "active" to "unknown"
Not part of the specifically flagged claim, but surfaced during verification of the eligibility source (required per brief item 3) and is a material finding:

- The prior eligibility.source, https://portugal.letapebytourdefrance.com/participant-information, is now **dead**: its TLS certificate expired **Feb 12, 2026** (`openssl s_client` verified: `notAfter=Feb 12 23:59:59 2026 GMT`), and the site returns HTTP 500 even with certificate validation disabled (`curl -sk`). This has been broken for over 5 months as of this research pass (2026-07-24).
- The organizer's own event page — podi1.com/event/letape-portugal/ (Podium Events, the local franchise operator, already cited in the profile) — currently shows only a placeholder: "Pardon our dust! We're working on something amazing — check back soon!" Not live event content.
- L'Etape Portugal is **absent** from letapeseries.com's main hub country listing (checked via raw HTML grep — no "portugal" match found anywhere in the page) and absent from battistrada.com's 2026 L'Etape by Tour de France circuit listing page.
- battistrada.com's own event page (battistrada.com/en/event/letape-portugal/13576/) confirms the last edition ran **Sept 28, 2025** and states plainly: "the next edition of the gran fondo hasn't been announced yet."
- **No explicit cancellation/discontinuation statement was found either.** This is genuine ambiguity, not a confirmed defunct event — dead official site + absent from current circuit/hub listings + no 2026 date, but also no organizer statement saying it's over. Per the eligibility enum, this is the textbook case for **"unknown"** rather than "active" or "defunct."

## Citations
- Added: https://battistrada.com/en/event/letape-portugal/13576/ (new eligibility source, documents last-edition-2025 / next-not-announced). Profile already had 10 citations before this addition (now 11), comfortably above the 3-minimum.

## Sol adversarial review (2026-07-24, gpt-5.6-sol, read-only, foreground)
Sol agreed the "unknown" downgrade was reasonable and confirmed the UCI-comparison claim was fine, but caught two direct contradictions I'd left behind after downgrading eligibility. Both applied:
- **Applied**: `vitals.registration` still instructed readers to register via portugal.letapebytourdefrance.com, the exact site the new eligibility.notes says is dead (expired cert, HTTP 500). Corrected to lead with the current dead-site status, historical registration process follows.
- **Applied**: `history.notable_moments[4]` still said "2025: Fourth edition scheduled for September 28" in future tense, even though the new evidence (and the profile's own eligibility.notes) confirms that edition already ran. Corrected to past tense and added a "next edition not yet announced" note.
- **Applied**: `vitals.date` said "Late September annually" unconditionally, implying continued recurrence despite no 2026 date being found. Corrected to note the last confirmed edition and that the next hasn't been announced.
No findings rejected.

## JSON changes made
- `eligibility.status`: "active" → "unknown"
- `eligibility.source`: portugal.letapebytourdefrance.com/participant-information (dead, expired cert) → battistrada.com/en/event/letape-portugal/13576/
- `eligibility.verified`: 2026-07-23 → 2026-07-24; `eligibility.notes` rewritten to document the dead official site, the organizer placeholder page, absence from current circuit listings, and the confirmed UCI-comparison claim
- `vitals.registration`, `vitals.date`, `history.notable_moments[4]`: corrected to stop asserting live/future-tense status inconsistent with the eligibility downgrade
- `citations`: added battistrada.com event-page source
- No text corrections to should_you_race/tagline — flagged UCI-comparison claim verified accurate as written
- No fondo_rating changes (rubric-lock held)
