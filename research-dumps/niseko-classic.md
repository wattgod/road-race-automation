# Research Dump: Niseko Classic

Wave: debt-sweep batch 7 (2026-07-24). Purpose: back-fill missing research
dump; verify UCI World Championships qualifier claims flagged by
`audit_fabricated_claims.py` (no dump previously existed). Unlike the other
UCI-flagged races in this batch, this claim is STALE and required a text
correction.

## Eligibility

- **Status: cancelled** (already correctly set in profile, verified
  2026-07-22). The open-entry Niseko Classic gran fondo is NOT being held in
  2026.
- Source: https://nisekoclassic.com/en/info/faq — HTTP 200 verified. States
  explicitly: "This event will not be held in 2026."

## Flagged claim: [UCI affiliation] final_verdict.one_liner — "official qualifier for the 2026 UCI Gran Fondo World Championships"

## Flagged claim: [UCI affiliation] final_verdict.should_you_race — "status as the official 2026 UCI Gran Fondo World Championships qualifier"

**FALSE / STALE — corrected in race-data/niseko-classic.json.**

Findings via the organizer's own FAQ (nisekoclassic.com/en/info/faq):
1. The Niseko Classic open-entry gran fondo — the race this JSON profile
   describes (140 km road race, 2,000-2,370 m elevation, Niseko Panorama
   Line climb) — will NOT be held in 2026.
2. Niseko Classic WAS historically a UCI Gran Fondo World Series qualifying
   event (2014-2025, per the profile's own history.notable_moments and a
   2022 first-person YouTube description confirming "It is a UCI Gran Fondo
   world series qualifier").
3. For 2026, Niseko is instead hosting the UCI Gran Fondo World
   Championships itself (Aug 26-30, 2026) — a separate, qualifier-restricted
   event (top-25% age-group finish at an actual UCI GFWS qualifying race
   elsewhere is required to enter; there is no open registration).
4. Japan's UCI GFWS qualifier slot for 2026 has moved to a new event: the
   UCI Gran Fondo World Series Fukushima ("Tour de Fukushima"), held June
   13-14, 2026 in Fukushima Prefecture, explicitly described as replacing
   Niseko as the home qualifier for Japanese riders.
   Source (WebSearch, UCI GFWS 2026 calendar-expansion press coverage):
   "The Tour de Fukushima on 13 and 14 June. This event will replace Niseko
   as the home qualifier for Japanese riders for the UCI Gran Fondo World
   Championships."

So the profile's claim that Niseko Classic itself IS "the official qualifier
for the 2026 UCI Gran Fondo World Championships" conflates two different
things: (a) the open-entry Niseko Classic gran fondo, which is cancelled for
2026 and no longer serves as Japan's qualifier, and (b) the UCI Gran Fondo
World Championships, a separate invite/qualification-only event that happens
to be hosted at the Niseko venue in August 2026. It is stale — accurate for
past editions (2014-2025), false for 2026.

## Correction applied

`final_verdict.one_liner` and `final_verdict.should_you_race` rewritten to
state plainly that the open-entry Niseko Classic is not held in 2026, that
Niseko itself is hosting the UCI Gran Fondo World Championships as a
separate qualifier-only event, and that Japan's UCI GFWS qualifier slot has
moved to the new Tour de Fukushima. Register/tone matched to the existing
profile voice (data-forward, direct).

Residual note: `history.origin_story` ("now the official pre-event for the
2026 UCI Gran Fondo World Championships") and `biased_opinion.summary`
("As the official 2026 UCI Gran Fondo World Championships qualifier...")
carry the same stale framing but were NOT in this batch's flagged-claims list
and were left untouched per the surgical-fix scope; flagged in
catalog_flags.status_note for a future wave / human call on whether this
profile should be pulled from active listing entirely given the 2026
cancellation.

## Verdict

Claim corrected in `race-data/niseko-classic.json` (final_verdict.one_liner,
final_verdict.should_you_race). Eligibility block was already correctly set
to "cancelled" in a prior wave — no change needed there.
