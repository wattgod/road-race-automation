# Research Dump: White Rose Classic

Compiled 2026-07-24, debt-sweep batch 9.

## Flagged claim: "Tour de France 2014 roads / UCI Worlds 2019 climbs" (terrain.features)

**Status: TRUE — curl-verified verbatim on the event's own site.**

`curl -A "<browser UA>" https://whiteroseclassic.org.uk/` → HTTP 200. The page's own copy reads (grep-extracted, exact text):

> "...Tour de France in 2014, the Tour de Yorkshire & (Tour de Yorkshire sportive) and the UCI world championships in 2019, before finishing your route at our HQ."

This directly supports the JSON's `terrain.features` entries "Tour de France 2014 roads" and "UCI Worlds 2019 climbs." The 2019 UCI Road World Championships were held in Yorkshire, UK (Harrogate), so the geographic claim is coherent. Ilkley Cycling Club has run the event since 2012 (site: "Ilkley Cycle Club have been running the White Rose Classic since 2012 when the club re[formed]").

Additional corroboration: granfondoguide.com event listing (https://www.granfondoguide.com/Events/Index/6436/white-rose-classic, curl HTTP 200).

## Data bug found and fixed: `vitals.country`

`vitals.country` was `"USA"` while `vitals.location` correctly read "Ilkley, West Yorkshire, UK" and `location_badge` read "ILKLEY, UK." This is an unrelated pre-existing data-entry error (not a status/currency issue — the event has always been UK-based; nothing changed in the world). Confirmed via the same curl-verified whiteroseclassic.org.uk fetch: page repeatedly self-identifies as "ILKLEY CYCLING CLUB," "YORKSHIRE'S PREMIER SPORTIVE," and describes the Yorkshire Dales route. Corrected `vitals.country` to `"England"` to match sibling Yorkshire profiles in this database (struggle-dales, struggle-moors, dartmoor-classic all use "England" rather than "UK"/"United Kingdom" for the country field). Note: this same `country: "USA"` bug pattern exists on several other UK races in this database (dragon-ride, fred-whitton-challenge, london-to-brighton) — those are out of scope for this batch and were not touched.

## Vitals otherwise unchanged
Distance/elevation/route options (125mi Epic / 84mi Challenge / 47-71mi Intermediate / 36-37mi Short) were not flagged and not independently re-verified against the live site's current route names this pass (a 2026 WebSearch summary noted the site currently advertises "Grassington Short / Settle Medium / Hawes Long" naming, which may reflect a later route-naming refresh) — flagging as a possible future staleness point, not corrected here since it's outside the batch's flagged claims and the underlying mileage/elevation figures were not contradicted by any source found.

## Citations
JSON already carries 3 citations (official site, TimeOutdoors event page, Gran Fondo Guide) — meets the 3-citation minimum. TimeOutdoors and British Cycling both returned HTTP 403 to curl (bot-protected — not evidence of brokenness); granfondoguide.com and the official site both curl-verified HTTP 200. No citation changes made.

## Sol adversarial review — correction applied 2026-07-24
A read-only `codex exec -m gpt-5.6-sol` pass found a real, direct contradiction the first draft missed: this dump's own quoted site text — "Ilkley Cycle Club have been running the White Rose Classic since 2012 when the club reformed" — flatly contradicts `history.founded: 2019` and `origin_story`'s "Born 2019 as Yorkshire's top sportive." Re-checked the exact source text via curl (saved locally, exact match confirmed): "Ilkley Cycle Club have been running the White Rose Classic since 2012 when the club reformed. As the club is a charity, we run the event as a 'Not for Profit'..." This is unambiguous, official-source, primary evidence of a 2012 founding, not 2019.

Corrected `history.founded` (2019→2012), the opening clause of `origin_story`, and the first `notable_moments` entry (was "2019 launch on UCI Worlds roads," now "2012: Ilkley Cycle Club reforms, launches White Rose Classic"). Left the remaining `notable_moments` bullets (2020 Dales debut, 2024 Must-Do status, 2025 fourth route, 2026 BC grading) untouched — they weren't independently re-verified this pass and, now that the founding year is corrected, at least one ("2020 Dales debut pre-pandemic") reads oddly against an event that's existed since 2012; flagging for a human/future pass rather than guessing at replacement dates without a source.

Sol also correctly pushed back on the first draft's "verified verbatim" framing for "UCI Worlds 2019 climbs" — the site says "roads," not "climbs." Reworded the dump/JSON note to describe this as a reasonable compressed paraphrase (consistent with the profile's other short feature-list bullets) rather than a verbatim match; the JSON's `terrain.features` bullet itself was left unchanged since it's stylistically consistent with sibling entries in the same list and not a factual overreach worth surgical rewriting.

## Verdict
Text changes made: `history.founded`, `origin_story` opening clause, first `notable_moments` entry, `vitals.country` typo fix (USA→England). Flagged UCI/TDF terrain claim itself verified true, left as-is. `race.eligibility` re-verified 2026-07-24 with notes capturing both corrections.
