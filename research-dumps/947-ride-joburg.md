# Research Dump: 947 Ride Joburg

Verified: 2026-08-15

## Identity, date, and format

- **Active:** Sunday, November 22, 2026.
- **Current organizer name:** Ride Joburg Road Race; `947 Ride Joburg` remains
  the stable catalog identity.
- **Edition:** 29th.
- **Course:** 97 km from Kyalami through Johannesburg, returning for the
  event's first finishing lap inside Kyalami Grand Prix Circuit.
- **Format:** seeded racing groups plus unseeded mass-participation waves.
- **Eligibility:** riders must be older than 15 on race day. E-bike entrants
  must be 19 or older and enter the designated category.
- **Current field size:** not published. Historical editions have drawn very
  large fields, but no historical number is presented as a 2026 commitment.

Sources:

- https://www.ridejoburg.co.za/road.html
- https://ridejoburg.co.za/blog.html?p=kyalami-2026
- https://ridejoburg.co.za/rules.html

## Current route and unresolved elevation discrepancy

The organizer's 2026 road page publishes **97 km, 1,398 m of elevation gain,
and eight water points**. The official downloadable route PDF also says 97 km
and eight water points, but displays **1,304** beside a mislabeled `km`
elevation unit. This is not silently normalized: 1,398 m drives the catalog
and training plan because it is the explicit value on the current road page,
while athletes are told to train to the higher figure and download the final
route file during race week.

The 2026 announcement says the revised course puts the toughest climbing
early, followed by a faster, more flowing run toward the finish. The mapped
route links Kyalami, Fourways, Sandton, Zoo Lake, Nelson Mandela Bridge, FNB
Stadium, and the M1 before the circuit finish. The organizer reserves the
right to alter the route for safety, traffic, construction, or other
constraints.

Sources:

- https://www.ridejoburg.co.za/road.html
- https://ridejoburg.co.za/blog.html?p=kyalami-2026
- https://ridejoburg.co.za/documents/Ride_Joburg_Route_26.pdf
- https://ridejoburg.co.za/rules.html

## Water points, timing, and race rules

The route PDF maps eight water points:

1. Monte Casino, 9.25 km.
2. Cash Converters, 19 km.
3. Pantry (Sasol) Rosebank, 30.2 km.
4. Gold Reef City Boysen off-ramp, 40 km.
5. Sasol Riverlea, 59 km.
6. M1 southbound, 68 km.
7. M1 southbound before the Sandton off-ramp, 76 km.
8. World of Golf, 84.5 km.

The map legend marks mechanical and Netcare nursing support at water points,
but the organizer has not published a guaranteed 2026 food or drink menu.
Athletes should carry the calories they need rather than assume a product will
be available.

The rules require an approved helmet, a number pinned to the jersey, and the
event timing chip. Personal audio/radio devices and cellular-phone use while
cycling are prohibited. Triathlon bars, aerobars, clip-ons, prayer bars, and
other unconventional handlebars are prohibited; disc brakes are permitted.
Riders must obey officers and marshals, keep left when instructed, and may be
stopped at controlled intersections. Riders have six hours after the last
start group departs to qualify as finishers and receive a medal.

Sources:

- https://ridejoburg.co.za/documents/Ride_Joburg_Route_26.pdf
- https://ridejoburg.co.za/rules.html

## Registration and race-week logistics

- Entry: **R810**, including VAT and the CSA rider levy.
- Seeded entries close: October 4, 2026.
- Preliminary seeding: October 8, 2026.
- Seeding-query and substitution deadline: October 21, 2026.
- Unseeded road-entry deadline: November 1, 2026.
- Number-collection dates and times: communicated to entrants later; no
  current public schedule should be inferred from a prior edition.
- Individual start groups and start times: communicated by email/SMS and
  available from October 8.

The road page and rules disagree slightly on the result window used to
calculate seeding: the page says through October 21, while the rules say
through October 31. That difference does not affect the training plan, but an
entrant disputing seeding should use the organizer's direct instructions.

Sources:

- https://www.ridejoburg.co.za/road.html
- https://ridejoburg.co.za/rules.html

## Regrade

Applied `config/dimensions.json` directly to current evidence:

- distance 2: 97 km.
- climbing 2: 1,398 m on the road page; the route PDF conflict is disclosed.
- descent technicality 1: broad paved city/highway course without a current
  technical-descent warning.
- road surface 2: paved route without a current pavement-condition audit.
- climate 3: warm late-spring conditions, high UV, and wind/thunderstorm
  exposure are plausible planning risks at Johannesburg altitude.
- altitude 3: Johannesburg riding near 1,700 m.
- logistics 2: major-city lodging with OR Tambo roughly 30-60 minutes away,
  offset by event-day road access and transport planning.
- prestige 4: 29th edition, established name, cash prizes, elite categories,
  and strong media/history footprint.
- organization 4: seeded groups, professional chip timing, eight mapped water
  points, traffic control, medical coverage, and mechanical coverage.
- scenic experience 3: memorable city landmarks and the Kyalami setting,
  rather than scenery throughout.
- community culture 4: a long-running Johannesburg mass-participation event.
- field depth 4: seeded racing groups, licensed categories, and cash prizes.
- value 3: R810 is a fair fee for the timed city event, but the organizer does
  not currently promise a jersey, meal, photos, or similar extras.
- expenses 4: an international destination trip can require flights and
  hotels even though local entry is inexpensive.
- cultural impact 4: a durable Johannesburg sporting institution without a
  claim to world-championship or monument status.

Total: 45 / 70 = 64, Tier 2. The Tier 2 seven-plan ladder remains unchanged.
The authenticated TrainingPeaks clone receipts show that all seven live plans
descend from the All-Rounder master family, so `data/tp-sku-map.json` preserves
`road-allrounder` rather than reclassifying the already-built fleet from a
generic demand-vector heuristic.
