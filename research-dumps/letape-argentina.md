# L'Etape Argentina by Tour de France — Research Dump

Debt-sweep verification pass (batch 6), 2026-07-24.

## Eligibility
- **Status: active.** Córdoba, Argentina. L'Etape Argentina ran March 22, 2026 at Estadio Mario Alberto Kempes (long route 134 km / 2,067m, short route 64 km).
- Source: https://cordobaturismo.gov.ar/evento/letape-argentina-by-tour-de-france-2026/ (official Córdoba tourism board).

## National championship co-location claim — TRUE per official source, but dates are unstable across sources
Flagged claim: final_verdict.should_you_race — "...the historic co-location with the Argentine National Championship appeals." Also present in tagline and history.origin_story.

- **Direct official-source backing found**: the Córdoba provincial tourism board's own event page for the Campeonato Argentino de Ciclismo de Ruta (https://cordobaturismo.gov.ar/evento/campeonato-argentino-de-ciclismo-de-ruta/, curl-verified 200) states explicitly: *"Este campeonato se celebrará en simultáneo con L'Étape Argentina by Tour de France, que tendrá lugar el 22 de marzo"* ("This championship will be held simultaneously with L'Étape Argentina by Tour de France, which will take place on March 22"). Both events also share the same finish venue (Estadio Mario Alberto Kempes) and both are part of the province's push to position Córdoba as a cycling hub after the Championship's 25-year absence from the region.
- **Date instability found**: the *specific* Championship dates conflict across every source checked:
  - derechadiario.com.ar (already cited in the profile): March 26-29
  - ayacuchoaldia.com.ar: March 19-21
  - cordobaturismo.gov.ar's own event page (the very page asserting "simultáneo"): **April 16-19**
  - This strongly suggests the Championship has been rescheduled multiple times (one source's headline literally translates to "the Argentine Road Championship changes date").
- **Initial decision (SUPERSEDED — see Sol review below)**: my first pass left the claim text unchanged, reasoning that an official government source used the word "simultáneo" and the shared promotional framing supported co-location despite date conflicts across sources. **This was wrong** — see below.

## Sol adversarial review (2026-07-24, gpt-5.6-sol, read-only, foreground) — MAJOR CORRECTION, verified before applying
Sol rejected my "leave it as date instability" call and provided definitive primary evidence resolving the conflict: the Argentine Cycling Federation's (FACPyR) own program page and post-race results report. **I independently verified both before applying the correction** (per the brief's "verify sol's findings against live code before acting" mandate):
- WebFetch of https://ciclismoarg.com.ar/programa-campeonato-argentino-de-ruta-elite/ confirms: "los días 16, 17, 18 y 19 de abril de 2026" at "RÍO CUARTO – CÓRDOBA 2026."
- WebFetch of https://ciclismoarg.com.ar/nicolas-tivani-se-consagro-campeon-argentino-de-ruta/ (the actual results report) confirms the championship "se disputó en el autódromo de la ciudad de Río Cuarto" and concluded "este domingo" — i.e. it definitively ran at the Río Cuarto autodrome, not Córdoba capital / Kempes Stadium.
- Río Cuarto is a distinct city roughly 200km from Córdoba capital. L'Etape Argentina ran March 22 at Estadio Mario Alberto Kempes in Córdoba capital. The two events are neither in the same city nor the same month — **not co-located, not concurrent, not "running alongside."**
- **Applied**: corrected every field that asserted co-location/concurrency — `tagline`, `terrain.features[7]`, `history.origin_story`, `history.notable_moments[4]`, `history.reputation`, `biased_opinion.summary`, `biased_opinion.strengths[3]`, `biased_opinion.bottom_line`, `final_verdict.one_liner`, `final_verdict.should_you_race` — to accurately describe the two events as separate, both happening to return to Córdoba province in 2026 but a month apart in different cities. Also fixed `history.reputation`'s "The 2026 edition will define..." (future tense for an event eligibility already confirms already ran) to past tense.
- Also verified and rejected the weaker parts of sol's framing before applying: sol's review draft implied the original Cordoba-tourism-page "simultáneo" claim was simply "stale promotional copy" with no basis — that's a fair characterization given the FACPyR primary source directly contradicts it, so I kept sol's substantive finding but wrote the correction to explain *why* the promotional framing was wrong (misleading city-level "Córdoba province" framing conflated with "Córdoba capital"), rather than just asserting it was false.

## Citations
Profile already carries 10 citations (well above the 3-minimum). Added 2 more: the FACPyR program page and results report (the definitive sources for the correction above) — now 12 total.

## JSON changes made
- `tagline`, `terrain.features[7]`, `history.origin_story`, `history.notable_moments[4]`, `history.reputation`, `biased_opinion.summary`, `biased_opinion.strengths[3]`, `biased_opinion.bottom_line`, `final_verdict.one_liner`, `final_verdict.should_you_race`: all corrected to remove false co-location/concurrency framing
- `eligibility.verified`: 2026-07-23 → 2026-07-24; `eligibility.notes` rewritten with the definitive FACPyR-sourced correction
- `citations`: added 2 FACPyR sources (now 12 total)
- No fondo_rating changes (rubric-lock held)
