# Research Dump: GFNY Colombia (Bogotá edition)

## Eligibility
- **Status: defunct (Bogotá edition).** Confirmed: GFNY is returning to Colombia with a NEW event, GFNY Villavicencio, April 25, 2027 — a different host city, explicitly framed by GFNY as a return "after a three-year absence," not a continuation of the Bogotá race.
- Source: https://gfny.com/gfny-is-back-in-colombia/ (official GFNY announcement — confirms Villavicencio 2027, references the prior Bogotá-era gap). Matches existing file eligibility, which is correct and unchanged.

## Flagged claim: [size claim] history.origin_story — "attracted 1,700 starters — making it the largest cycling race in Colombian history at the time"
**FALSE/unsupported as written — corrected.**
- Verified: GFNY's own 3rd-edition (2017) results reporting is headlined "GFNY Colombia Sets Record With 1700 Riders" (granfondo.com, already cited in file) — this is a record **for GFNY Colombia itself**, not a claim about Colombian cycling history broadly.
- GFNY's own "GFNY is back in Colombia" announcement (2026) describes the brand as "the first organization to stage a mass-participation cycling race in Colombia in 2015" — a real, verifiable superlative (first of its kind format), but no GFNY or press source claims the 2017 Bogotá field was the largest cycling race in Colombian *history*. Colombia has a deep national cycling culture (Vuelta a Colombia, regional gran fondos, church/charity rides) with no comprehensive historical field-size database to support or refute an absolute "largest ever" claim — it is unverifiable and reads as marketing overreach.
- **CORRECTED** the sentence to the verifiable framing: "attracted 1,700 starters — a new participation record for the event at the time" (drops the unverifiable national-history superlative, keeps the sourced record claim).

## Citations
- Existing 14 citations are extensive and already cover eligibility, vitals, and history; the granfondo.com "Sets Record" citation already on file is the direct source for the corrected claim. No additions needed.
- Note: https://www.granfondo.com/cycling-news/534065/gfny-colombia-sets-record-with-1700-riders returns 404/405 to raw curl (bot-protection on granfondo.com), but content was independently confirmed live via a rendering fetch (title, byline, and "1,700 riders" record language all present). Pre-existing citation, left in place.

## Vitals correction (found via sol adversarial review, not the original flag set)
- File's vitals (121km / 2,563m) described the **pre-2023 Guatavita / La Cuchilla course** (start/finish Guatavita, 2,725m, climb to La Cuchilla summit 3,365m twice — confirmed via a 2022-era course description). But `vitals.location` already said "Zipaquira" (the post-2023 course) and `route_options` already carried the post-2023 figures (~101km / ~2,321m, Aguila summit finish) — the origin_story text explicitly documents the 2023 move to the Salt Cathedral of Zipaquira and El Aguila, but vitals hadn't been updated to match.
- Confirmed the correct current/final (event is defunct as of this pass) course figures via a 2023 event listing: **101.1 km, 2,321m elevation gain, finish atop El Águila** (15km final climb at 3.3%, 523m gain), start inside the Salt Cathedral of Zipaquirá at 2,650m. Source: ahotu.com/event/gfny-bogota (2023 listing), cross-checked against the pre-existing `route_options` figures already in the file.
- **CORRECTED** vitals.distance_km/mi and elevation_m/ft to 101.1km/62.8mi, 2,321m/7,615ft.

## Sources used this pass
- https://gfny.com/gfny-is-back-in-colombia/
- https://www.granfondo.com/cycling-news/534065/gfny-colombia-sets-record-with-1700-riders (pre-existing citation, re-verified)
- https://www.ahotu.com/event/gfny-bogota (2023 course figures, cross-check for vitals correction)
