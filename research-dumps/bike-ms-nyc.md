# Bike MS: New York City — Research Dump

Debt-sweep verification pass, 2026-07-24. All URLs curl-verified live (HTTP 200) on 2026-07-24 unless noted.

## Eligibility
- **Status: active.** Manhattan, NYC. 2026 edition scheduled October 18.
- Source: https://events.nationalmssociety.org/2778 (curl-verified live).

## Size claim ("world's largest cycling fundraising series") — CONFIRMED TRUE
- Flagged claims: tagline, final_verdict.one_liner, history.origin_story, history.reputation — all reference "the world's largest cycling fundraising series."
- Direct verification: the National MS Society's own official "About Bike MS: How It Works" page (https://events.nationalmssociety.org/index.cfm?fuseaction=cms.page&id=1227, curl-verified live) states: "Bike MS raises more money than any other cycling series for any other cause." That is the organization's own framing of the same substantive claim (largest by fundraising dollars, not rider count) — supports the tagline/one_liner/origin_story claims as written. No literal string "largest" found on that specific page, but the substantive claim is the org's own stated position.
- Conclusion: "world's largest cycling fundraising series" claim is adequately supported. Left unchanged.

## "Flagship" claim — UNSUPPORTED, CORRECTED
- Two instances flagged in this batch's scope (tagline, history.reputation): "The flagship edition of the world's largest cycling fundraising series" / "The flagship urban edition of the world's largest cycling fundraising series."
- Checked every curl-verified citation (About Bike MS page, NYC 2026 event page id 2778, page 10039, CBS News NYC 2025 coverage) — the word "flagship" does not appear anywhere in any of them. National MS Society's own materials describe NYC as one of ~70 annual Bike MS events nationwide (per the profile's own history.origin_story: "75,000 annual riders across approximately 70 events nationwide"), with no source calling NYC specifically the flagship/premier edition.
- Corrected both instances from "flagship edition" / "flagship urban edition" to "New York City edition" — removes the unsupported superlative while keeping the well-supported "world's largest cycling fundraising series" claim intact, matching the surrounding register.
- Note (out of batch scope, not corrected): "flagship" also appears in `biased_opinion.summary` and `history.notable_moments[2]` ("growing into the series' flagship urban event"). Per the brief's explicit rule against wholesale biased_opinion rewrites, and because these fields were not part of this batch's flagged claims (only tagline and history.reputation were flagged), these were left untouched. Flagging for a human call on whether to extend the same fix there.

## Citations (existing, spot-checked live 2026-07-24)
- https://events.nationalmssociety.org/pages/10039 — 200
- https://events.nationalmssociety.org/events/2403 — 200
- https://events.nationalmssociety.org/pages/8341 — 200
- https://www.cbsnews.com/newyork/news/bike-ms-nyc-street-closures-2025/ — 200
- https://hoodline.com/2025/10/new-york-city-pedals-for-multiple-sclerosis-awareness-in-bike-ms-2025-charity-ride/ — 200
- https://events.nationalmssociety.org/index.cfm?fuseaction=cms.page&id=1227 — 200 (source for size-claim verification)
- https://unlimitedbiking.com/events/bike-ms-new-york-city-bike-rentals/ — 403 (bot-blocked in one check; not treated as dead)

## Sol adversarial review
GPT-5.6-sol (read-only, foreground) reviewed this race alongside the rest of the batch. Verdict: CONFIRM on the size claim (adequately supported when read as "largest by fundraising"). Sol additionally flagged, unprompted, that "flagship edition" wording is NOT supported by any Society page found — this matched my own independent check exactly. Applied the correction.

## JSON changes made
- `tagline`: "The flagship edition of" → "The New York City edition of"
- `history.reputation`: "The flagship urban edition of" → "The New York City edition of"
- `eligibility.verified`: 2026-07-20 → 2026-07-24
- `eligibility.notes`: added (was previously absent), documents both the size-claim verification and the flagship correction
- No fondo_rating changes
