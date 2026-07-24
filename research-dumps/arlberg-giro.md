# Arlberg Giro — Research Dump

Debt-sweep verification pass, 2026-07-24. All URLs curl-verified live (HTTP 200) on 2026-07-24 unless noted.

## Eligibility
- **Status: active.** St. Anton am Arlberg, Tyrol, Austria. Official rules page confirms 2026 (14th edition) event.
- Source: https://arlberg-giro.com/en/rules-of-participation (curl-verified live).

## UCI affiliation claim — checked, PRECISION FIX APPLIED (not a false-claim correction)
- Flagged claim: final_verdict.should_you_race, "If you are chasing UCI points, maximum vertical, or global prestige — the Maratona dles Dolomites or Otztaler Radmarathon may be better targets."
- Verification: Arlberg Giro does **not** appear anywhere on the UCI Gran Fondo World Series calendar (https://ucigranfondoworldseries.com/en/calendar/, curl-verified live, full-page text search for "Arlberg", "St. Anton", "Tyrol", and "Austria" all returned zero hits).
- The official Arlberg Giro site (home + route pages, both curl-verified live) contains zero mentions of "UCI" anywhere.
- This matches the profile's own pre-existing content: biased_opinion.weaknesses already states "Not UCI-sanctioned — lacks the international recognition of the Maratona or Otztaler," and biased_opinion.summary says "it is not the most prestigious (no UCI sanction, no lottery mania)."
- Conclusion: the flagged sentence was NOT factually false — it already correctly implied non-affiliation by steering UCI-seekers elsewhere. However, "chasing UCI points" mixes terminology from elite/pro racing (UCI ranking points) with what UCI GFWS gran fondos actually offer (age-group qualification slots for the UCI Gran Fondo World Championships, not "points"). Per sol's review, corrected for precision: "chasing UCI points" → "chasing UCI Gran Fondo World Championships qualification." This is a terminology fix, not a truth correction — the underlying claim (Arlberg Giro is non-UCI) was already accurate.

## Citations (existing, spot-checked live 2026-07-24)
- https://arlberg-giro.com/en/home — 200
- https://arlberg-giro.com/en/route — 200
- https://arlberg-giro.com/en/registration/entry-fees — 200
- https://www.cycloworld.cc/en/gran-fondo/austria/arlberg-giro/40246 — 200
- https://www.cycloworld.cc/en/article/why-the-arlberg-giro-belongs-on-your-bucket-list/5507 — 200
- https://www.granfondoguide.com/Events/Index/7167/arlberg-giro — 200
- https://www.stantonamarlberg.com/en/events/summer/arlberg-giro — 200
- https://cyclelivemagazine.com/en/arlberg-giro-2026-14th-edition-cycling-in-the-heart-of-the-alps/ — 200
- https://www.tyrol.com/things-to-do/sports/cycling/biketours/a-arlberg-giro — 404 (dead, not corrected this pass — 11 of 12 citations remain live, well above the 3-citation floor)
- https://climbfinder.com/en/climbs/arlbergpass-sankt-anton-am-arlberg — 200
- https://climbfinder.com/en/climbs/silvretta-hochalpenstrasse-partenen — 200
- https://www.explorer-hotels.com/en/blog/arlberg-giro-2025.html — 200

## Sol adversarial review
GPT-5.6-sol (read-only, foreground) reviewed this race. Verdict: CORRECT — non-GFWS status confirmed accurate, but flagged "chasing UCI points" as imprecise since GFWS confers World Championships qualification, not generic ranking points. Applied as a minimal wording fix; rejected the implication (if any) that the underlying claim was false — it was already correctly hedged.

## JSON changes made
- `final_verdict.should_you_race`: "chasing UCI points" → "chasing UCI Gran Fondo World Championships qualification"
- `eligibility.verified`: 2026-07-20 → 2026-07-24
- `eligibility.notes`: added (was previously absent), documents the non-UCI-affiliation check and the wording fix
- No fondo_rating changes
