# Research Dump: Gran Fondo Loutraki (UCI Gran Fondo Greece)

Verified 2026-07-24 via codex gpt-5.6-sol foreground research + direct curl verification, as part of the Roadie Labs debt-sweep (batch 4).

## Quick Facts
- **Location**: Loutraki, Isthmus of Corinth, Greece
- **2026 edition**: November 1, 2026 (2nd edition — the inaugural was November 2, 2025)
- **Distance/elevation**: 112 km, 1,360 m — confirmed matching the profile's vitals via the official 2026 event page.
- **Organizer**: KYVERNITIS Travel S.A., in partnership with the Municipality of Loutraki and the Hellenic Cycling Federation.

## UCI Gran Fondo World Series status: CURRENT
Loutraki appears on the official UCI Gran Fondo World Series calendar for the 2026 season and has a UCI competition record. Curl-verified: `https://ucigranfondoworldseries.com/en/calendar/` returns the literal strings "Loutraki" and "loutraki" (link to `/en/loutraki/`) in its page source.
- UCI GFWS calendar: https://ucigranfondoworldseries.com/en/calendar/
- Official 2026 event page (curl-verified 200, `<title>UCI Gran Fondo Greece 2026 - KYVERNITIS Travel S.A.</title>`, page text contains "112km", "1360", "November 1", "2026"): https://kyvernitis.gr/sports-and-events/uci-gran-fondo-greece-2026/

## Claim verification

| Claim | Verdict | Evidence |
|---|---|---|
| Display name "UCI Gran Fondo Loutraki" | TRUE | Organizer branding matches; UCI calendar shortens to "Gran Fondo Greece" but the event identity is the same race. |
| Tagline: "Greece's inaugural UCI Gran Fondo qualifier" | TRUE for 2025 origin / STALE as unqualified 2026 wording — 2026 is explicitly the 2nd edition, not the current year's inaugural | 2025 official roadbook confirms first-ever status: https://kyvernitis.gr/wp-content/uploads/2025/10/UCI-ROADBOOK-ENG-V5.pdf ; UCI GFWS report on the 2025 inaugural winners: https://ucigranfondoworldseries.com/en/panagiotis-chionis-and-varvara-fasoi-crowned-first-winners-of-granfondo-loutraki/ |
| final_verdict: "UCI World Series qualifier" / "genuine world championship qualification opportunities" | TRUE | Official 2026 site publishes top-25%-per-category + top-3 automatic qualification rules: https://kyvernitis.gr/sports-and-events/uci-gran-fondo-greece-2026/ |
| final_verdict: "Greece's first UCI Gran Fondo World Series event" | TRUE | 2025 roadbook states it was the first UCI Gran Fondo Series race held in Greece (see above). |
| final_verdict: "integration into the prestigious UCI Gran Fondo World Series calendar" | TRUE | Confirmed live on the 2026 UCI GFWS calendar (curl-verified above). |

## Fix applied
Tagline softened from "Greece's inaugural UCI Gran Fondo qualifier" to "Greece's UCI Gran Fondo qualifier" to avoid implying 2026 (2nd edition) is still the inaugural year; the inaugural-2025 framing is preserved accurately, in past tense, in `history.origin_story` and `history.notable_moments`, which already correctly say "organized for the first time in 2025" and "2025: November 2 - Inaugural." No other text changed.

## Eligibility
- status: active
- verified: 2026-07-24
- source: https://kyvernitis.gr/sports-and-events/uci-gran-fondo-greece-2026/

## Sol adversarial review pass (2026-07-24)
- **Applied**: `logistics.official_site` was pointing at the old (non-2026-dated) URL — updated to the verified 2026 event page.
- **Rejected/deferred**: sol flagged that `youtube_data.rider_intel.search_text` wrongly describes Lorne, Australia / Great Ocean Road surf-coast content for this Greece race (contamination from a mismatched YouTube video about the UCI Gran Fondo World Championships in Lorne). This is a real data-quality issue but it's pre-existing YouTube-enrichment content, not part of this batch's flagged UCI-affiliation claims, and out of the debt-sweep's eligibility/claims scope. Left unchanged; flagging here for a YouTube-enrichment cleanup pass.
