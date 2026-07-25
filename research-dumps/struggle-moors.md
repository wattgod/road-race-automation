# Struggle Moors / Struggle:NYM — straggler re-review research (2026-07-24)

Sources: prior editorial wave 9 research (11b2e96, already committed to race-data/struggle-moors.json)
+ live spot-check this pass (2026-07-24) of the current event page and British Cycling listing
(both curl 200). Not every citation in the committed JSON was individually re-curled this pass.

## Identity
Real, standalone sportive in the Struggle Events series (alongside Struggle Dales and Struggle
Borderlands), run by Struggle Events Limited, a Harrogate company founded 2016 by Matt and
Victoria Mannakee in the wake of the 2014 Tour de France Grand Depart in Yorkshire. Not a route
option nested inside a larger event — it has its own inaugural date and edition history.
- https://find-and-update.company-information.service.gov.uk/company/10387871 (Companies House,
  organizer record)

## History / format overhaul
Launched July 9, 2017 as Struggle Moors, from Ampleforth Abbey, ~174km, estimated field ~1,000.
For 2026 the organizer rebranded it Struggle:NYM (North York Moors), moved the start to Sutton
Bank National Park Centre, and replaced the old single-distance format with three distances:
130km Short (1,957m), 189km Classic (3,144m), 250km Ultra (3,906m) — an expansion from 2025's
two-distance format (100/161km per British Cycling's 2025 listing). Delivered in partnership
with the North York Moors National Park Authority.
- https://ridethestruggle.com/pages/struggle-nym-2026 (current, curl 200)
- https://www.britishcycling.org.uk/events/details/337221/Struggle-NYM (curl 200)
- https://www.britishcycling.org.uk/events/details/158539/Struggle-Moors (2017 inaugural listing)
- https://www.northyorkmoors.org.uk/__data/assets/pdf_file/0026/196316/Full-NPA-Agenda-15-December.pdf
  (NPA agenda confirming the partnership)

## Status verification
2026 edition confirmed held July 5, 2026 from Sutton Bank. Organizer's own site is internally
inconsistent in places (stale "165KM"/"120KM" labels alongside correctly updated 189/130km body
copy) — the final rider road book and British Cycling's listing agree on 130/189/250km, and those
figures are what's on file. No confirmed 2027 date; organizer floats a 2027 return as marketing
language only.
- https://mcusercontent.com/365f3d950d1a39f8b5b871c02/files/ec491f3a-6be6-e0aa-6e9d-45640351df78/Struggle_NYM_Road_Book_2026_.pdf
- https://sportive.com/2026/02/06/ready-for-3906m-of-climbing-the-north-york-moors-want-a-word/
- https://my.raceresult.com/408444/ (curl 200 — results portal live, finisher totals not
  independently confirmed)

## Verdict for eligibility.status
"active" — real, currently running event, just rebranded. race.name/display_name updated to
current branding ("Struggle:NYM") with former name preserved in tagline/history for continuity;
slug intentionally left unchanged (struggle-moors) to avoid breaking existing URLs, flagged in
catalog_flags.

## Scoring
Not re-derived this pass. scoring_notes on file flags that dimensions were left as inherited
despite the 2026 route overhaul (130/189/250km replacing the old single-distance format) —
this is a real gap worth a human call (the Ultra distance/climbing figures materially exceed
what the current fondo_rating dimensions — distance=3, climbing=4, descent_technicality=2, ...
— reflect) but is outside this delegated pass's authority to silently reshuffle; documented,
not resolved unilaterally.
