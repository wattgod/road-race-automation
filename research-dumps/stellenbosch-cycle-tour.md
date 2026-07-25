# Stellenbosch Cycle Tour — straggler re-review research (2026-07-24)

Sources: prior editorial wave 9 research (11b2e96, already committed to race-data/stellenbosch-cycle-tour.json)
+ live spot-check this pass (2026-07-24) of the current Pedal Power road calendar and the
former official domain (both curl 200). Not every citation in the committed JSON was
individually re-curled this pass.

## Identity
Real, historically distinct Western Cape road race — NOT a mislabeled duplicate of the much
larger Cape Town Cycle Tour, though the two share organizational roots (both under the
Cape Town Cycle Tour Trust / Pedal Power Association ecosystem) and Stellenbosch functioned
as a seeding race for Cape Town. Separate city, separate event, separate history.
- https://www.capetowncycletour.com/events/the-cape-town-cycle-tour (disambiguation)
- https://pedalpower.org.za/product/medihelp-stellenbosch-cycle-tour/

## History / lineage
Descended from Die Burger Cycle Tour (Stellenbosch High School base, ran through at least
2013, ~92km). Renamed Stellenbosch Cycle Tour in 2014 (~95km). Sponsored as Medihelp
Stellenbosch Cycle Tour from 2016 (~97km, 102km for the 2019 edition run from Val de Vie
Estate). Course and distance moved across eras — no single fixed course to describe.
- https://www.doitnow.co.za/content/stellenbosch-cycle-tour-road-closures-and-potential-delays-sunday-30-november-2014

## Status verification
- Last completed edition: 2019.
- Jan 2020 edition (Stellenbosch High School, 3,000+ entries) cancelled race-morning after
  forecast ~95km/h winds.
- 2021 edition cancelled outright for COVID-19, per Pedal Power Association's own 2021 AGM
  events report.
- No edition has appeared on Pedal Power Association's road calendar since — re-verified live
  2026-07-24, current https://pedalpower.org.za/mec-category/road/ listing has no Stellenbosch
  entry (curl 200, page checked).
- Former official domain stellenboschcycletour.co.za resolves to a parked-domain placeholder
  (curl 200, confirmed live 2026-07-24 — page loads but content is a parking page, not the
  event site).
- https://social-tv.co.za/sports-and-art/medihelp-stellenbosch-cycle-tour-canceled-due-to-unsafe-weather-conditions/
- https://pedalpower.org.za/wp-content/uploads/2021/08/Events-AGM-Report-2021.pdf

## Verdict for eligibility.status
"defunct" — closest fit within the fixed status enum (active/defunct/cancelled/unknown).
No formal organizer announcement of permanent closure exists, just a 5+ year absence (2020
race-morning cancellation, 2021 COVID cancellation, then total silence through 2026) with no
revival evidence on the organizer's own current calendar. Comparable precedent: Birkebeinerrittet
road profile (dormant/defunct register), not deletion — a real, once-active event kept as an
honest historical entry per standing ruling against deleting dormant-but-real races.

## Scoring
Not re-derived this pass — identity was RIGHT (a real, distinct event), only status/format
nuance (dormant since 2019) changed, so per ruling #3 in the straggler brief, numerics are left
untouched. scoring_notes on file already documents this explicitly ("NOT re-scored this wave --
dimensions untouched despite the event's dormant/defunct status, per policy against silent score
changes").

## Data-hygiene fix this pass
vitals.elevation_ft was 0.0 while elevation_m was null — a dual-unit inconsistency that falsely
implied a verified zero-climbing course rather than genuinely unknown elevation. Corrected
elevation_ft to null to match elevation_m (2026-07-24, straggler re-review). Not a rescore —
fondo_rating.climbing (already 3, "Rolling") is unaffected; this is representation-only.
