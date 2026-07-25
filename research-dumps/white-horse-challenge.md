# White Horse Challenge — straggler re-review research (2026-07-24)

Sources: prior editorial wave 9 research (11b2e96, already committed to race-data/white-horse-challenge.json)
+ live spot-check this pass (2026-07-24) of the entry page and British Cycling listing (both
curl 200). Not every citation in the committed JSON was individually re-curled this pass.

## Identity
Real, long-running charity sportive starting/finishing at Shrivenham Memorial Hall
(Oxfordshire), running through Oxfordshire, Wiltshire, and Berkshire since 2007. Name refers to
the several chalk-hill white horses on the route (Uffington, Broad Town, Cherhill, Hackpen on
the long route), not solely the famous Uffington figure — though Uffington (Britain's oldest
scientifically dated chalk hill figure) is the signature climax on the long course.
Independently organized by Fergal McGrath (with Sarah McGrath historically); no organizing
cycling club identified, no evidence the organizing team is itself a registered charity.
- https://www.whitehorsechallenge.com/route.htm (curl 200)
- https://road.cc/content/feature/17042-riding-white-horses (2010 ride report, independently
  corroborates 4th edition / 2007 founding)

## History
Grew out of Ride the Ridgeway, a 2004 fundraising ride by Fergal McGrath and friends after a
Kilimanjaro trip, which evolved into White Horse Challenge in 2007. Over GBP170,000 raised
across its history, most for WaterAid (long-standing beneficiary); beneficiary changed to
Prospect Hospice for 2025-26.
- https://www.wateraid.org/uk/sites/g/files/jkxoof211/files/2025-01/WaterAid%20fundraising%20guide.pdf

## Status verification
2026 edition confirmed held as scheduled April 19, 2026 (photo gallery / results-pending page).
Two distances: 145km/90mi long (~1,400m climbing per organizer) and ~112km/70mi short
(~1,194m). Elevation figures vary by source (organizer "about 1,400m" vs. third-party GPS
figures ~1,194-1,429m across both routes) — treated as approximate, not exact.

Prior profile version carried an "8 hours" course cutoff stated as a firm deadline. That framing
does not hold up under verification: British Cycling's 2022-23 listings show "8hr"/"9hr"
duration fields for long/short routes, but neither the organizer nor British Cycling labels
these as finishing deadlines. vitals.cutoff_time was corrected, not removed — it still contains
an explanatory string ("No explicit rider cutoff confirmed...treat as approximate ride-time
estimates, not a confirmed cutoff") so the field stays honest rather than silently blanked;
also documented in eligibility.notes.
- https://whitehorsechallenge.eventrac.co.uk/e/white-horse-challenge-13802 (curl 200)
- https://www.britishcycling.org.uk/events/details/325406/White-Horse-Challenge (curl 200)

## Verdict for eligibility.status
"active" — confirmed real and currently running, 2026 edition held as scheduled. No identity
correction needed (unlike stellenbosch/struggle-moors/race-around-ireland in this same wave);
the only material fix was removing an unverifiable cutoff-time claim and noting the
beneficiary-charity change.

## Scoring
Not re-derived this pass — scoring_notes on file states only vitals/course_description/
citations were enriched, dimensions unchanged. Identity/format were not materially wrong here
(this is the mildest of the five straggler cases — a real, active, correctly-identified event
that just needed a fact cleanup, not an identity resolution), so per ruling #3 numerics are
left untouched.
