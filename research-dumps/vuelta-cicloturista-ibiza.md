# Vuelta Cicloturista a Ibiza Campagnolo — Editorial Wave 10 Research Notes

Source: codex exec (gpt-5.6-sol, web search), 2026-07-24.

## Vitals correction (major)

On-file 280km/2,000m never matched a real single-day figure or the organizer's documented
cumulative total. The 2026 event (XXIII edition) is a 3-day multi-stage format:

- Stage 1: ~60km, 1,100m+ (Ibiza Town → Sant Antoni via Es Cubells, Cala Molí)
- Stage 2: ~107km, 1,650m+ (Sant Josep → Sant Antoni via Sant Llorenç, Portinatx, Santa Agnès)
- Stage 3: 4.4km individual time trial (Sant Antoni de Portmany)
- Cumulative: 171.4km / 2,750m+ (TT elevation not published, so 2,750m is a documented minimum)

## 2026 status: ACTIVE

Dates: October 9-12, 2026 (Oct 9 registration/presentation, riding Oct 10-12). Live
registration open via RockTheSport, €140 standard rising to €150 Sept 1.

- Official: https://www.ibizabtt.com/vuelta-cicloturista-a-ibiza-campagnolo/2026
- Routes: https://www.ibizabtt.com/vuelta-cicloturista-a-ibiza-campagnolo/2026/recorridos
- Registration: https://www.rockthesport.com/es/evento/vuelta-cicloturista-a-ibiza-campagnolo

## Identity check: confirmed NOT conflated with Mallorca

This event is entirely Ibiza-based (Ibiza Town, Sant Josep, Sant Antoni, Sant Llorenç,
Portinatx). Confirmed distinct from Mallorca 312 (separate one-day April event, Playa de Muro,
Mallorca) and Cinturón Ciclista Internacional a Mallorca (separate Mallorca elite stage race).

## Taxonomy note

Official FAQ describes this as effectively a multi-stage event (two mass-start road stages +
individual TT), which may fit `multi_stage` discipline better than `gran_fondo` — flagged via
catalog_flags, discipline enum left unchanged per policy (never edit discipline directly).

## History

Project created by Bartolo Planells in 2002; first held edition 2004 (~200 riders, 3 routes
across Ibiza/Formentera). Organized by Club Esportiu Ibiza Sport (Ibiza Bike S.C.P.); Bartolo's
brother Juanjo Planells is the current organizer. 2021 edition featured a dedicated
women's/adapted-cycling category (360+ participants), honoring Paralympic medalist Ricardo Ten.

## Course

Punchy Mediterranean island climbing — Stage 1 averages ~18.3m/km, Stage 2 ~15.4m/km (dense,
repeated climbing, not one big summit). Roads open to normal traffic throughout. Only timed
sectors and the final TT determine classification; most riding is social group touring. Timed
sectors: Stage 1 = Camí de Cas Coll and Cala Vedella; Stage 2 = Cala Sant Vicent ascent and Ses
Marrades. Route tours five Ibiza municipalities. Feed zones: Stage 1 = 2 (Es Cubells, Cala
Molí); Stage 2 = 3 (Sant Llorenç, Portinatx, Santa Agnès); none on the TT. No fixed pace
cutoff published; broom-vehicle removal, scheduled finishes 13:00 (Stage 1) / 15:00 (Stage 2).
Entry fee €140 standard (through Aug 31) / €150 from Sept 1, plus registration-platform
commission. Field: DGT's provisional event reservation lists ~500 (planned/authorized capacity,
not a confirmed-entry count).

Mallorca 312 (the identity-check comparison event) runs 312/226/167km route options from Playa
de Muro in April, per its official regulations.

## Credible criticisms

- Roads open to normal traffic (not closed) — the regulations themselves flag this as the
  primary safety consideration
- Organizer (Juanjo Planells) has publicly apologized for resident/traffic disruption from a
  past three-day edition
- Official "provisional" 2026 regulations have visible errors: page headed XXIII but Article 2
  calls it XXII, image-rights clause references the 2025 event
- Strict withdrawal terms: 50% refund Sept 1-15, no refund after Sept 16

## youtube_data: kept as-is

All 3 videos match the event by title (2018, 2016 teaser, 2021 edition recap) — no purge needed.
