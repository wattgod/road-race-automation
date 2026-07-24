# L'Etape Denmark by Tour de France — Research Dump

Debt-sweep verification pass (batch 6), 2026-07-24.

## Eligibility — RESOLVED from "unknown" to "active"
- The prior pass had flagged eligibility as "unknown," reasoning that the DGI Hærvejsløbet site (sites.dgi.dk/haervejsloebet) confirmed a June 26, 2027 date for the underlying road event, but that "the page no longer clearly carries L'Etape/ASO branding, and ASO's own letapeseries.com calendar does not clearly list a 2027 Denmark edition."
- **This pass resolves the uncertainty**: direct curl + WebFetch of the official https://denmark.letapeseries.com/ (ASO's own dedicated subdomain for this event, curl-verified 200) confirms the **2026 edition ran under full L'Etape by Tour de France / ASO branding on June 27, 2026** — page text: "DGI Hærvejsløbet - L'Étape Denmark afholdes 27. juni 2026," with full TdF jersey-classification language ("ikoniske Tour de France-førertrøjer"). The page is now archived/post-event: registration is closed, marked sold out, and a "look back" recap blog post is dated June 28, 2026 — i.e. this is a live confirmation the branded event actually happened one month before this research pass (today: 2026-07-24).
- This directly answers the open question: the ASO/L'Etape partnership was confirmably live through the most recent (2026) edition. **Status upgraded to "active."**
- 2027 caveat: the DGI Hærvejsløbet site's June 26, 2027 date is confirmed for the *underlying* event, but denmark.letapeseries.com has not yet published a 2027-specific page, so branding continuation for 2027 specifically (as opposed to 2026, which is now confirmed) is probable-but-not-independently-confirmed. Documented as such in eligibility.notes rather than asserted as certain.

## Age claim ("Denmark's oldest cycling road") — CONFIRMED TRUE
Flagged claim: history.origin_story — "The marriage of Denmark's oldest cycling road with the world's most famous cycling brand..."

- Confirmed via WebSearch: VisitSønderjylland's official tourism page states plainly, "Hærvejen is Denmark's oldest highway, which since ancient times has carried soldiers and people from Danevirke in the south to Viborg in the north." Multiple additional Danish tourism-board sources (visitdenmark.com, haervej.dk, visitherning.com) independently corroborate the "Ancient Road" framing and a documented history stretching back ~4,000 years, formalized as a route in the early Middle Ages.
- No correction needed — the claim is accurate and well-supported.

## Citations
- Added: https://www.visitsonderjylland.com/tourist/experiences/active-together/haervejen (age-claim verification source). Profile already had 6 citations before this addition (now 7), comfortably above the 3-minimum.

## Sol adversarial review (2026-07-24, gpt-5.6-sol, read-only, foreground)
Sol agreed the "active" upgrade was well-supported, but caught one internal inconsistency: **applied** — `vitals.date_specific` unconditionally said "2027: June 26," while `eligibility.notes` (correctly) hedged that only the underlying DGI Hærvejsløbet event is confirmed for that date and L'Etape/ASO branding continuation for 2027 specifically is unconfirmed. Rewrote `date_specific` to lead with the confirmed 2026 edition and carry the same 2027 hedge that eligibility.notes already had, so the two fields no longer contradict each other in confidence level. No findings rejected.

## JSON changes made
- `eligibility.status`: "unknown" → "active"
- `eligibility.source`: sites.dgi.dk/haervejsloebet → denmark.letapeseries.com (stronger, ASO-official primary source for the resolved question)
- `eligibility.verified`: 2026-07-22 → 2026-07-24; `eligibility.note`/`notes` rewritten to document the resolution and the remaining 2027-branding caveat
- `vitals.date_specific`: rewritten to carry the same 2026-confirmed/2027-hedged framing as eligibility.notes
- `citations`: added VisitSønderjylland source
- No text corrections needed to the flagged age claim — verified accurate as written
- No fondo_rating changes (rubric-lock held)
