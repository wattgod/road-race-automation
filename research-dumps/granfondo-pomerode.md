# Research Dump: UCI Gran Fondo Brasil (slug: granfondo-pomerode)

Verified 2026-07-24 via live web search (codex/gpt-5.6-sol) + direct curl verification of every URL below.

## Quick Facts
- Current name: UCI Gran Fondo Brasil / Granfondo Brazil.
- Current location: Timbó, Santa Catarina, Brazil — start/finish at Parque Henry Paul. The race MOVED from Pomerode (its original host city, hence the legacy slug `granfondo-pomerode`) to nearby Timbó for its **November 9, 2025 (third) edition** — NOT the 2026 edition. Confirmed via a UCI GFWS calendar-updates article dated 9 July 2025 (fetched and grepped directly, 2026-07-24): "UCI Granfondo Brazil who took place in Pomerode in the past two years will relocate to the nearby city of Timbo on November 9th." This matches the pre-existing `history.notable_moments` entry "2025: Third edition held November 9." **CORRECTION APPLIED**: an earlier draft of this dump and `catalog_flags.taxonomy_note` / `history.origin_story` incorrectly said the move happened "for its 2026 edition" — corrected to 2025 in both the JSON and this dump after an adversarial sol review caught the error and I re-verified it directly against the live UCI article. The JSON's display_name "UCI Gran Fondo Brasil" and location "Timbó, Santa Catarina, Brazil" were already correct pre-edit.
- Date: November 8, 2026 (event activities Nov 6-8).
- Course: organizer's current published route map shows 108 km Gran Fondo / 80 km Mediofondo — matches the JSON's distance_km 108.0 exactly. The organizer's regulations PDF separately gives nominal figures of 120 km/+1,000m and 80 km/+600m with up to ±20% adjustment permitted. The JSON's elevation_m 1000 matches the regulation figure. No correction needed — both figures come from the same organizer, just different documents (route map vs. regulations), and the JSON already uses the more specific/current one for distance.

## UCI Gran Fondo World Series Status — VERIFIED TRUE
The display_name ("UCI Gran Fondo Brasil"), tagline ("South America's Premier UCI Gran Fondo Qualifier"), one_liner ("Brazil's UCI Gran Fondo World Series qualifier"), and should_you_race ("UCI Gran Fondo Brasil delivers authentic UCI-sanctioned gran fondo racing with a qualification pathway to the 2027 World Championships") claims are all confirmed accurate.

- Live UCI Gran Fondo World Series calendar lists "Granfondo Brazil, Timbó, November 8, 2026" under "Qualifiers 2026-2027." https://ucigranfondoworldseries.com/en/calendar/ (HTTP 200 via curl --resolve)
- UCI GFWS calendar-updates page documents the event's move from Pomerode to Timbó. https://ucigranfondoworldseries.com/en/uci-gran-fondo-world-series-calendar-updates/ (HTTP 200)
- Organizer's own route map and regulations PDF confirm the current course and confirm the qualification structure. https://www.ucigranfondobrasil.com.br/mapas (HTTP 200) and https://www.ucigranfondobrasil.com.br/_files/ugd/a46ac5_42f40434c2ba4de5b14b6507aa3f26f8.pdf (HTTP 200)
- UCI GFWS regulations page confirms the qualification mechanism: the first 25% of finishing starters in each age-group category (plus the top 3 finishers per official category) qualify for the World Championships. https://ucigranfondoworldseries.com/en/regulations/ (HTTP 200). Note: the organizer's own May 2026 PDF inconsistently states "20%" in one place but gives a worked example consistent with 25% — the controlling UCI regulation is 25%, and the profile does not cite a specific percentage, so no JSON change needed.

## Taxonomy Note
The slug `granfondo-pomerode` and some pre-existing citation labels reference the race's original host city (Pomerode), while the race itself, its display_name, and its current location field already correctly reflect the 2026 host city (Timbó). This is a legacy-slug situation, not a data error — flagging via `catalog_flags.taxonomy_note` in the JSON so a future slug/URL migration doesn't lose this context, per the debt-sweep brief's guidance to record naming quirks rather than change the discipline/slug directly.

## Eligibility
- Status: active. Matches existing eligibility block (verified 2026-07-17, source ucigranfondobrasil.com.br). Reconfirmed live via the UCI GFWS 2026-2027 calendar.

## Citations (curl-verified 2026-07-24)
1. UCI Gran Fondo World Series live calendar — https://ucigranfondoworldseries.com/en/calendar/ (HTTP 200)
2. UCI GFWS calendar-updates page (documents Pomerode → Timbó move) — https://ucigranfondoworldseries.com/en/uci-gran-fondo-world-series-calendar-updates/ (HTTP 200)
3. Organizer route map — https://www.ucigranfondobrasil.com.br/mapas (HTTP 200)
4. Organizer 2026 regulations PDF — https://www.ucigranfondobrasil.com.br/_files/ugd/a46ac5_42f40434c2ba4de5b14b6507aa3f26f8.pdf (HTTP 200)
5. UCI Gran Fondo World Series regulations (qualification mechanism) — https://ucigranfondoworldseries.com/en/regulations/ (HTTP 200)

Note on sandbox DNS: `ucigranfondoworldseries.com` fails to resolve via this environment's default resolver but resolves via `dig`. All ucigranfondoworldseries.com URLs above were confirmed HTTP 200 using `curl --resolve host:443:<resolved-ip>`.
