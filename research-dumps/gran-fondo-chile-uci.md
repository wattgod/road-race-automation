# Gran Fondo Chile — Research Dump (GOLD wave, 2026-07-24, batch C)

## Identity resolution

Prior data conflated this event with L'Etape Chile by pointing its registration
URL at chile.letapeseries.com. Live web research (codex/gpt-5.6-sol + direct
curl verification) confirms these are two distinct, real 2026 events:

- **Gran Fondo Chile** — genuine UCI Gran Fondo World Series stop, inaugural
  edition, Sunday October 4, 2026, in Lago Ranco, Los Rios, Chile (roughly a
  2-hour drive southeast of Valdivia). Organized by Riders Sports (Juliano
  Salvadori), the group behind Granfondo Brazil and Granfondo Colombia.
  Distances: Gran Fondo 114km / 1,554m; Medio Fondo 80km / 723m.
- **L'Etape Chile by Tour de France** (separate profile, letape-chile.json) —
  Sunday November 1, 2026, Valdivia/Niebla/Cayumapu, 30/60/110km routes,
  organized by World Centric Group. No UCI affiliation found anywhere on its
  official site.

## Sources checked directly

- https://ucigranfondoworldseries.com/en/uci-gran-fondo-chile/ — official
  event page. Quote: "Gran Fondo Chile is a new event on the UCI calendar and
  will take place for the first time in October 2026." Lists "Sunday
  04.10.2026," "80 - 114 km," "Lago Ranco, Valdivia, Los Rios," 114km course
  with 1,554m climbing (Gran Fondo) and 80km/723m (Medio Fondo).
- https://ucigranfondoworldseries.com/en/calendar/ — independently lists
  "Granfondo Chile — Lago Ranco, Valdivia, Los Rios — Sunday 04 Oct 2026."
  Confirmed via direct curl of this page (matched "Granfondo Chile" /
  "Lago Ranco, Valdivia, Los Rios" in the HTML).
- https://www.uci.org/competition-details/2026/CPT/78757 — official UCI
  competition record. Confirmed via direct curl: identifies "GRANFONDO CHILE,"
  "LAGO RANCO," class "UGF" (UCI Gran Fondo World Series), and lists
  ucigranfondochile.com as the event's own domain.
- https://www.ucigranfondobrasil.com.br/ — organizer reference (Riders /
  Riders Sports, Juliano Salvadori), the same team credited with organizing
  Gran Fondo Chile per the UCI World Series page.
- https://chile.letapeseries.com/ (and /stages, /route/18, /registration) —
  official L'Etape Chile site. No "UCI" or "Lago Ranco" reference found
  anywhere on the site. Organizer listed as World Centric Group, host city
  Municipalidad de Valdivia. Distances 30/60/110km, elevations 372/1,292/1,804m.

## Unverified / open items

- No live registration page found for Gran Fondo Chile as of 2026-07-24 —
  ucigranfondochile.com returned an HTTP 504 on direct check. Do not present
  chile.letapeseries.com as this event's registration; that is the other race.
- No published segment-by-segment route map or named climbs for the Lago
  Ranco course — this is a first edition with no prior-year report to draw on.
- Field size, entry fee, and organization quality are all unproven (inaugural
  event).

## Sol review corrections (2026-07-24, post-write verification pass)

Direct curl of https://ucigranfondoworldseries.com/en/uci-gran-fondo-chile/ confirms:
"The 114km Granfondo is the qualifier distance for all men 19-59 and women 19-49...
The Mediofondo as qualifier for all men 60+ and women 50+ is 80km long... for a
total elevation of 723m." Both distances are qualifying distances, split by age
category — the Medio Fondo is NOT a "non-qualifying" option as an earlier draft
of this profile stated. Corrected.

A July 8, 2026 Chilean Cycling Federation announcement
(https://fdnciclismochile.cl/blogs/noticias/chile-sera-sede-por-primera-vez-de-una-fecha-de-la-uci-gravel-world-series-y-uci-gran-fondo-world-series)
confirms an official public launch event in Lago Ranco with federation president
Jorge Espinoza, organizer Salvadori (Riders Sports), and municipal officials
present, for both a UCI Gravel World Series round (Oct 3, 105/85km) and the UCI
Gran Fondo World Series round (Oct 4). This same article gives different course
figures than the GFWS page — roughly 120km/2,000m+ (Gran Fondo) and 80km/900m+
(Medio Fondo) — and states official routes would be finalized later. Both
figure sets are now presented in the profile as a genuine open discrepancy
rather than treating either as final.

## Disposition

Both gran-fondo-chile-uci and letape-chile are genuine, separate events.
Neither is a catalog_flags duplicate of the other. gran-fondo-chile-uci's
vitals/location/registration/citations were corrected to match the real UCI
Gran Fondo World Series stop in Lago Ranco.
