# Sovev Jerusalem — straggler re-review research (2026-07-24)

Sources: prior editorial wave 7 research (f645e5a, already committed to race-data/sovev-jerusalem.json)
+ codex/gpt-5.6-sol follow-up correction (documented in file's eligibility.notes,
"UPDATED 2026-07-24, codex gpt-5.6-sol") + live spot-check this pass (2026-07-24) of the
registration and Pedal Power-equivalent official pages: RegSovevJrs.aspx returns 302 on a
direct request, resolving to 200 when redirects are followed (-L) — a normal server-side
redirect, not a broken link. Not every citation in the committed JSON was individually
re-curled this pass.

## Identity / discipline
Real, large, well-supported mass-participation cycling event through Jerusalem — Old City
walls, City of David National Park, Emek Tzurim, Mount Scopus, Nahal Tzofim, Nahal Sorek Park,
Cedar Park, Jerusalem Hills, Aminadav Forest, Biblical Zoo, Railway Park. Starts at the First
Station complex. Four distances: 50/30/15/8km.

CRITICAL FINDING: the organizer's own official registration page explicitly states the courses
combine road and off-road riding, that road and city bicycles are unsuitable, and recommends
mountain bikes. This is a mixed-surface/off-road event, not a conventional road gran fondo.
- https://www.sovevjerusalem.co.il/RegSovevJrs.aspx (curl 302 direct / 200 after following
  redirect, confirms MTB requirement in organizer's own copy — re-verified live 2026-07-24)
- https://www.sovevjerusalem.co.il/Categories.aspx?Id=9234

## Date correction
Original file-on-record date was May 8, 2026; sonar-pro eligibility_audit flagged a
conflict, and the codex gpt-5.6-sol follow-up pass confirmed the correct 2026 date is
May 29, 2026. Both the date correction and the MTB-requirement finding are already reflected
in the committed profile's eligibility.notes.
- https://itraveljerusalem.com/event/surrounding-jerusalem
- https://t.me/s/jerusalemtelgram?before=787 (municipality announcement)

## Field-size conflict
Sources disagree: municipal estimate 5,000+, tourism estimate 7,000, media estimate "3,000+
cyclists, 5,000 overall." Documented as a conflict rather than resolved to a single number.
- https://jerusalem-online.co.il/en/israels-biggest-cycling-event-over-5000-riders-in-jerusalem/

## YouTube purge
4 previously-attached videos removed this wave: 2 were "GFNY Jerusalem" (a different, separate
event, not evidenced as current/related), 1 was an unrelated Dead Sea charity ride, 1 could not
be confirmed to depict this specific event. None were verifiably Sovev Jerusalem footage —
documented as purge_note rather than silently deleted.

## Verdict / discipline_mismatch
Per ruling #4 in the straggler brief (taxonomy is FLAG-ONLY — never change the discipline
enum), this profile carries catalog_flags.status_note flagging the taxonomy mismatch for a
human call, rather than silently reclassifying or removing it. The organizer's own guidance
(MTB recommended, road bikes discouraged) is unambiguous: this requires off-road-capable
equipment and is not a pure road event. discipline_mismatch language already present in
catalog_flags.status_note ("Not changing the discipline enum per editorial-wave scope —
flagging for a human taxonomy decision on whether this profile belongs in a pure road-cycling
database at all").

## Scoring
Not re-derived. terrain.surface was already corrected in a prior wave to "Mixed road and
off-road..."; the scoring_notes text on file previously still claimed terrain.surface='Paved
roads', which was stale and self-contradictory — corrected this pass (2026-07-24) to name the
real remaining contradiction: fondo_rating.road_surface=1, which still scores this as a
fully-paved course against the organizer's own mixed-surface/MTB guidance. Numbers left
untouched pending the human taxonomy decision — consistent with "if identity was RIGHT and only
status/format nuance changed, leave numerics alone and flag" (ruling #3), since the event's
existence/date/identity are confirmed correct; only its road-vs-offroad classification is in
question.
