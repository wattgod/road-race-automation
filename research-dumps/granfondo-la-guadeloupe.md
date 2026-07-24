# Research Dump: Granfondo La Guadeloupe

Verified 2026-07-24 via live web search (codex/gpt-5.6-sol) + direct curl verification of every URL below.

## Quick Facts
- Location: Capesterre-Belle-Eau, Guadeloupe (Basse-Terre side).
- Next edition date: December 6, 2026 (2026 UCI Gran Fondo World Series listing). Inaugural edition ran December 7, 2025.
- Course: 126 km per the live UCI calendar listing. The most recently *published* elevation figure (2,883 m) is from the 2025 inaugural route — no refreshed 2026 elevation profile has been published as of this verification, so the existing JSON's 124.0 km / 2,883.0 m should be read as "last confirmed" rather than a freshly-reconfirmed 2026 figure. Not flagged as wrong — no contradicting figure was found, just no newer one.

## UCI Gran Fondo World Series Status — VERIFIED TRUE
The tagline ("Tropical UCI Gran Fondo qualifier with Caribbean climbs and sea views") and one_liner ("Exotic UCI qualifier blending steep climbs and Caribbean allure") are confirmed accurate.

- The live UCI Gran Fondo World Series calendar lists "Granfondo La Guadeloupe," Capesterre-Belle-Eau, Sunday December 6, 2026. https://ucigranfondoworldseries.com/en/calendar/ (HTTP 200 via curl --resolve; ucigranfondoworldseries.com does not resolve via this sandbox's default DNS but resolves fine via `dig` — see note below)
- The race's own UCI GFWS profile pages (English and French) exist and are live: https://ucigranfondoworldseries.com/en/granfondo-la-guadeloupe/ and https://ucigranfondoworldseries.com/fr/granfondo-la-guadeloupe/ (both HTTP 200).
- The completed 2025 inaugural edition (Dec 7, 2025) was also an official UCI qualifier, corroborated independently by Granfondo Daily News's results report ("UCI Granfondo Guadeloupe Results: Mountain Goat Benjamin Le Ny Climbs to Victory") and by Battistrada's 2026 calendar listing.

## Data Quality Note — logistics.official_site is now dead (re-verified after adversarial review)
The profile's `logistics.official_site` field and one prior citation both pointed to `https://granfondo-iles-de-guadeloupe.com` — this domain now returns HTTP 404. A sol adversarial-review pass disputed this, claiming the domain "currently serves a full 2025 event page" — per the debt-sweep brief's instruction to verify sol's findings against live code before acting on them, I re-checked directly:

```
$ curl -sL -A "<full Chrome UA>" https://granfondo-iles-de-guadeloupe.com -o body.html -w "code=%{http_code}\n"
code=404
$ cat body.html
The deployment could not be found on Vercel.
DEPLOYMENT_NOT_FOUND
$ dig +short NS granfondo-iles-de-guadeloupe.com
ns1.vercel-dns.com.
ns2.vercel-dns.com.
```

This is unambiguous: the domain is DNS-live and hosted on Vercel, but the specific deployment behind it has been taken down/removed by the owner ("DEPLOYMENT_NOT_FOUND" is Vercel's own error page, not a generic 404). It is not currently serving an event page. Sol's contrary finding was not backed by a genuine live fetch — **rejected**.

Codex/sol also proposed a replacement URL, `https://www.ucigranfondoguadeloupe.com/`, which does NOT exist — confirmed via `dig` against both the local resolver and Google's public resolver (8.8.8.8): NXDOMAIN both times, no A record. This was never added to the JSON.

No live official-site replacement was found in this research pass; a currently-live organizer domain (`tourcyclo.com`) returns 404 on its root path too, so it was not used. **Flagging for a human/future pass**: `logistics.official_site` is stale and should be re-verified before the next content touch, but no corrected URL is being substituted here to avoid introducing an unverified guess. The dead citation URL (`granfondo-iles-de-guadeloupe.com`) has been swapped for the curl-verified Granfondo Daily News results report in the citations array of race-data/granfondo-la-guadeloupe.json — this swap stands, confirmed correct.

## Eligibility
- Status: active. Matches existing eligibility block (verified 2026-07-22, source ucigranfondoworldseries.com/en/calendar/). Confirmed still accurate as of 2026-07-24 — the 2026 edition is live on the calendar, not cancelled.

## Citations (curl-verified 2026-07-24)
1. UCI Gran Fondo World Series live calendar — https://ucigranfondoworldseries.com/en/calendar/ (HTTP 200, resolved via --resolve, DNS quirk noted above)
2. UCI Gran Fondo World Series race profile (EN) — https://ucigranfondoworldseries.com/en/granfondo-la-guadeloupe/ (HTTP 200)
3. UCI Gran Fondo World Series race profile (FR) — https://ucigranfondoworldseries.com/fr/granfondo-la-guadeloupe/ (HTTP 200)
4. Granfondo Daily News — 2025 inaugural edition results — https://granfondodailynews.com/2025/12/09/uci-granfondo-guadeloupe-results-mountain-goat-benjamin-le-ny-climbs-to-victory/ (HTTP 200)
5. Battistrada — independent 2026 calendar listing — https://battistrada.com/en/cycling-calendar/edition/granfondo-la-guadeloupe-2026/53924/ (HTTP 200)
6. Le Cycle.fr — "Un Granfondo UCI en Guadeloupe" — https://lecycle.fr/actualites/un-granfondo-uci-en-guadeloupe/63423/ (HTTP 200, pre-existing citation, re-verified)
7. Sportsnconnect.com registration/calendar pages — https://www.sportsnconnect.com/img/uploads/250605052917x9ee1ty820nw3ev4za5y6s7.pdf and https://www.sportsnconnect.com/calendrier-evenements/view/29239/gran-fondo-des-iles-de-guadeloupe (both HTTP 200, pre-existing citations, re-verified)

Note on sandbox DNS: `ucigranfondoworldseries.com` fails to resolve via this environment's default resolver (`curl: Could not resolve host`) but resolves correctly via `dig` (34.128.161.244). All ucigranfondoworldseries.com URLs cited above were confirmed HTTP 200 using `curl --resolve host:443:34.128.161.244`. This is a sandbox networking quirk, not evidence the domain is down.
