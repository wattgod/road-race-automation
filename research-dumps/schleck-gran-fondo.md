# Research Dump: Schleck Gran Fondo

Wave: debt-sweep batch 7 (2026-07-24). Purpose: back-fill missing research
dump; verify UCI Gran Fondo affiliation claims flagged by
`audit_fabricated_claims.py` (no dump previously existed).

## Eligibility

- **Status: active.** 2026 edition ran May 30 (sold out); 2027 dates not yet
  announced.
- Source: https://schleck-x-perience.com/granfondo/ (official) — cited in existing profile eligibility, verified 2026-07-20.
- Source: https://ucigranfondoworldseries.com/en/calendar/ (2026 calendar) — HTTP 200 verified; "Schleck Granfondo" listed Sat 30 May 2026, Mondorf-les-Bains, Luxembourg.
- Source: https://ucigranfondoworldseries.com/en/schleck-granfondo/ — HTTP 200 verified (UCI GFWS official event page).

## Vitals

- 159 km route through the Luxembourg Ardennes, on roads used by Fränk and
  Andy Schleck's training rides; punchy, technical terrain (not high-mountain).
- Confirmed sells out quickly — sportpress.international and
  sportytravellers.com coverage both describe fast sellouts and high demand.

## Flagged claim: [UCI affiliation] tagline — "UCI qualifier that sells out fast"

**TRUE.** The event's own official page explicitly markets itself as a UCI
Gran Fondo World Series stop: "X-perience the thrill of a UCI Gran FONDO
WORLD SERIES event." It further details UCI qualification requirements
directly: "To qualify for the UCI Gran Fondo World Championships, riders must
be 19 (born before 01.01.2008) or older," and lays out UCI GFWS finals
qualification criteria by age category (M1-M7), plus a note that only riders
without UCI points can be classified.
- Source: https://schleck-x-perience.com/granfondo/ — HTTP 200 verified, quoted directly above.

## Flagged claim: [UCI affiliation] biased_opinion.verdict — "UCI Ardennes Beast"

**TRUE.** Same evidence as above — confirmed current UCI GFWS qualifying
event on the 2026 calendar.

## Flagged claim: [UCI affiliation] final_verdict.one_liner — "UCI glory for the gritty"

**TRUE.** Same evidence — active 2026 UCI GFWS calendar member.

## Verdict

No text changes required — all three flagged UCI claims verified true and
current as of 2026. Added one citation (UCI GFWS official calendar) to
strengthen the existing 3-citation array; all three original citations
(schleck-x-perience.com official page, sportpress.international, and
sportytravellers.com) remain valid and curl-verified.
