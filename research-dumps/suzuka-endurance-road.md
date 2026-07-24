# suzuka-endurance-road — editorial wave 5 research evidence (2026-07-24)

Source: codex gpt-5.6-sol foreground web research, log: ed5_d_suzuka-endurance-road_research.log

## Bottom line

The current profile is materially conflated with the motorcycle Suzuka 8 Hours.

A genuine bicycle event exists at Suzuka Circuit, but it is officially called the **Suzuka 8 Hours Enduro** (スズカ8時間エンデューロ), not “Suzuka Endurance Road.” It is an amateur bicycle circuit-enduro festival with several timed and distance formats—not a 100-mile gran fondo. The real bicycle event is active: the 27th edition is scheduled for **November 14, 2026**, with registration open July 17–October 5. [Official bicycle-event website](https://suzuka8h.powertag.jp/)

The profile’s **July 3–5, 2026** dates belong exactly to the **47th FIM Suzuka 8 Hours motorcycle race**. Suzuka Circuit describes that event as 2–3 riders taking turns on **one motorcycle** for eight hours. [Official motorcycle-event explanation](https://www.suzukacircuit.jp/eng/8tai/guide/step1/), [official 2026 event listing](https://www.suzukacircuit.jp/eng/result_s/)

## 1. Current status

- **Underlying bicycle event:** **Active.** The 27th Suzuka 8 Hours Enduro is scheduled for November 14, 2026. [Official event website](https://suzuka8h.powertag.jp/)
- **Latest completed edition:** The 26th edition took place on **November 1, 2025**, drawing more than 4,000 participants across the 4-hour enduro, 8-hour enduro and Attack 240. [Official 2025 event report](https://suzuka8h.powertag.jp/report/2025/index.html)
- **Exact database name “Suzuka Endurance Road”:** No authoritative source found using that name. It appears to be a synthetic hybrid of the bicycle “Suzuka 8 Hours Enduro” and the motorcycle “Suzuka 8 Hours Endurance Road Race.”
- **Best single source:** [https://suzuka8h.powertag.jp/](https://suzuka8h.powertag.jp/)

Recommended eligibility status: **active only after renaming and rebuilding the profile around the bicycle enduro**. As currently written, quarantine it as an invalid/conflated profile.

## 2. Correct bicycle course facts

| Field | Best-supported value |
|---|---|
| Event type | Bicycle circuit enduro with multiple categories, not a gran fondo. [Official formats](https://suzuka8h.powertag.jp/2026/01_1.html) |
| Venue | Suzuka Circuit International Racing Course, Mie Prefecture. [Official event site](https://suzuka8h.powertag.jp/) |
| Date | November 14, 2026. [Official event site](https://suzuka8h.powertag.jp/) |
| Lap | 5.807 km, ridden counterclockwise—opposite normal motorsport direction. [Official event program](https://suzuka8h.powertag.jp/2024/pdf/2024_program.pdf) |
| Formats | 4-hour and 8-hour “most laps” enduros, plus Attack 240. [Official formats](https://suzuka8h.powertag.jp/2026/01_1.html) |
| Fixed distance | Attack 240 is actually **40 × 5.807 km = 232.28 km**, with an eight-hour limit. [Official rules](https://suzuka8h.powertag.jp/2026/03_1.html) |
| Other distances | Variable: the timed races have no fixed total. The 2025 8-hour leader completed 58 laps, approximately 336.8 km. [Official 2025 result](https://suzuka8h.powertag.jp/2025/result/8h_sogo.pdf) |
| Surface | Fully paved racetrack, 10–16 metres wide—not mixed surface. [Suzuka Circuit course specification](https://www.suzukacircuit.jp/eng/course_s/) |
| Elevation | No authoritative cumulative-gain figure is published. The organizer provides a rolling lap profile, but total gain depends on laps completed. Leave `elevation_m` null rather than inventing a total. [Official course profile/program](https://suzuka8h.powertag.jp/2024/pdf/2024_program.pdf) |
| Route features | Figure-eight circuit with the chicane, West Straight, Spoon, hairpin, 25R–Degner, NIPPO corner and descending S-curves. These are technical circuit features, not named road climbs. [Official course guidance](https://suzuka8h.powertag.jp/2026/05_1.html) |
| Field | More than 4,000 participants across all formats in 2025. For 2026, the official table lists 220 places for the combined 8-hour solo/Attack 240 entry and 350 teams across the 8-hour team categories. [2025 report](https://suzuka8h.powertag.jp/report/2025/index.html), [2026 entry table](https://suzuka8h.powertag.jp/2026/01_1.html) |
| Entry format | Solo or relay team. Team riders exchange an ankle-band timing transponder in the pit; only one team rider may be on course. The start is rolling behind a motorcycle. [Official competition rules](https://suzuka8h.powertag.jp/2026/03_1.html) |
| Eligibility | Most 8-hour and Attack 240 classes are open from junior-high-school age; 8-hour teams have 2–6 riders, with separate 45+ and mixed-gender classes. The 4-hour program includes road, women, flat-bar/recumbent, city-bike and family classes. [Official category table](https://suzuka8h.powertag.jp/2026/01_1.html) |
| History | The bicycle enduro began in **2000** as an early Japanese cycle-enduro; the 8-hour race was added at the third edition. [Official 25th-edition program](https://suzuka8h.powertag.jp/2024/pdf/2024_program.pdf), [official 20th-edition report](https://suzuka8h.powertag.jp/report/2019/01_1.html) |

## 3. Profile corrections

- `name`: Change to **Suzuka 8 Hours Enduro**.
- `date`: Change from `2026 July 3-5` to **2026 November 14**. July 3–5 is indisputably the motorcycle race. [Official motorcycle dates](https://www.suzukacircuit.jp/eng/result_s/)
- `distance_km=160.9`: **Wrong.** There is no official 100-mile format. Use variable distance for timed enduros and a route option of **232.28 km** for Attack 240. [Official formats](https://suzuka8h.powertag.jp/2026/01_1.html)
- `elevation_m=null`: Appropriate until a defensible per-lap ascent is obtained; do not render it as zero.
- `field_size='Hundreds of teams'`: Directionally true for the 8-hour team field but incomplete. Prefer **“4,000+ participants across all formats in 2025; 2026 8-hour team capacity 350 teams.”**
- `cutoff_time`: Replace “e.g., 4 or 8 hours” with exact formats: **four-hour and eight-hour timed enduros; Attack 240 has an eight-hour limit.**
- `surface='Paved roads'`: Correct, although “fully paved racing circuit” is more precise.
- `terrain.primary='Mixed terrain'`: Wrong. Different bicycle types are allowed, but the course itself is entirely paved.
- `discipline='gran_fondo'`: Wrong. This is a **timed circuit enduro/team relay**. If your schema cannot represent circuit enduros, the event should be excluded instead of mislabeled as a gran fondo.
- Any motorcycle videos, rider quotations, heat-management advice, history since 1978, manufacturer prestige or FIM EWC material must be removed. Those belong to the separate motorcycle race. [Official motorcycle description](https://www.suzukacircuit.jp/eng/8tai/guide/step1/)

Also avoid confusing it with the separate **Shimano Suzuka Road**, another active bicycle festival at the same circuit, scheduled for September 26–27, 2026. [Official Shimano Suzuka Road overview](https://suzukaroad.shimano.com/2026/under/speech/)
tokens used
155,125
## Bottom line

The current profile is materially conflated with the motorcycle Suzuka 8 Hours.

A genuine bicycle event exists at Suzuka Circuit, but it is officially called the **Suzuka 8 Hours Enduro** (スズカ8時間エンデューロ), not “Suzuka Endurance Road.” It is an amateur bicycle circuit-enduro festival with several timed and distance formats—not a 100-mile gran fondo. The real bicycle event is active: the 27th edition is scheduled for **November 14, 2026**, with registration open July 17–October 5. [Official bicycle-event website](https://suzuka8h.powertag.jp/)

The profile’s **July 3–5, 2026** dates belong exactly to the **47th FIM Suzuka 8 Hours motorcycle race**. Suzuka Circuit describes that event as 2–3 riders taking turns on **one motorcycle** for eight hours. [Official motorcycle-event explanation](https://www.suzukacircuit.jp/eng/8tai/guide/step1/), [official 2026 event listing](https://www.suzukacircuit.jp/eng/result_s/)

## 1. Current status

- **Underlying bicycle event:** **Active.** The 27th Suzuka 8 Hours Enduro is scheduled for November 14, 2026. [Official event website](https://suzuka8h.powertag.jp/)
- **Latest completed edition:** The 26th edition took place on **November 1, 2025**, drawing more than 4,000 participants across the 4-hour enduro, 8-hour enduro and Attack 240. [Official 2025 event report](https://suzuka8h.powertag.jp/report/2025/index.html)
- **Exact database name “Suzuka Endurance Road”:** No authoritative source found using that name. It appears to be a synthetic hybrid of the bicycle “Suzuka 8 Hours Enduro” and the motorcycle “Suzuka 8 Hours Endurance Road Race.”
- **Best single source:** [https://suzuka8h.powertag.jp/](https://suzuka8h.powertag.jp/)

Recommended eligibility status: **active only after renaming and rebuilding the profile around the bicycle enduro**. As currently written, quarantine it as an invalid/conflated profile.

## 2. Correct bicycle course facts

| Field | Best-supported value |
|---|---|
| Event type | Bicycle circuit enduro with multiple categories, not a gran fondo. [Official formats](https://suzuka8h.powertag.jp/2026/01_1.html) |
| Venue | Suzuka Circuit International Racing Course, Mie Prefecture. [Official event site](https://suzuka8h.powertag.jp/) |
| Date | November 14, 2026. [Official event site](https://suzuka8h.powertag.jp/) |
| Lap | 5.807 km, ridden counterclockwise—opposite normal motorsport direction. [Official event program](https://suzuka8h.powertag.jp/2024/pdf/2024_program.pdf) |
| Formats | 4-hour and 8-hour “most laps” enduros, plus Attack 240. [Official formats](https://suzuka8h.powertag.jp/2026/01_1.html) |
| Fixed distance | Attack 240 is actually **40 × 5.807 km = 232.28 km**, with an eight-hour limit. [Official rules](https://suzuka8h.powertag.jp/2026/03_1.html) |
| Other distances | Variable: the timed races have no fixed total. The 2025 8-hour leader completed 58 laps, approximately 336.8 km. [Official 2025 result](https://suzuka8h.powertag.jp/2025/result/8h_sogo.pdf) |
| Surface | Fully paved racetrack, 10–16 metres wide—not mixed surface. [Suzuka Circuit course specification](https://www.suzukacircuit.jp/eng/course_s/) |
| Elevation | No authoritative cumulative-gain figure is published. The organizer provides a rolling lap profile, but total gain depends on laps completed. Leave `elevation_m` null rather than inventing a total. [Official course profile/program](https://suzuka8h.powertag.jp/2024/pdf/2024_program.pdf) |
| Route features | Figure-eight circuit with the chicane, West Straight, Spoon, hairpin, 25R–Degner, NIPPO corner and descending S-curves. These are technical circuit features, not named road climbs. [Official course guidance](https://suzuka8h.powertag.jp/2026/05_1.html) |
| Field | More than 4,000 participants across all formats in 2025. For 2026, the official table lists 220 places for the combined 8-hour solo/Attack 240 entry and 350 teams across the 8-hour team categories. [2025 report](https://suzuka8h.powertag.jp/report/2025/index.html), [2026 entry table](https://suzuka8h.powertag.jp/2026/01_1.html) |
| Entry format | Solo or relay team. Team riders exchange an ankle-band timing transponder in the pit; only one team rider may be on course. The start is rolling behind a motorcycle. [Official competition rules](https://suzuka8h.powertag.jp/2026/03_1.html) |
| Eligibility | Most 8-hour and Attack 240 classes are open from junior-high-school age; 8-hour teams have 2–6 riders, with separate 45+ and mixed-gender classes. The 4-hour program includes road, women, flat-bar/recumbent, city-bike and family classes. [Official category table](https://suzuka8h.powertag.jp/2026/01_1.html) |
| History | The bicycle enduro began in **2000** as an early Japanese cycle-enduro; the 8-hour race was added at the third edition. [Official 25th-edition program](https://suzuka8h.powertag.jp/2024/pdf/2024_program.pdf), [official 20th-edition report](https://suzuka8h.powertag.jp/report/2019/01_1.html) |

## 3. Profile corrections

- `name`: Change to **Suzuka 8 Hours Enduro**.
- `date`: Change from `2026 July 3-5` to **2026 November 14**. July 3–5 is indisputably the motorcycle race. [Official motorcycle dates](https://www.suzukacircuit.jp/eng/result_s/)
- `distance_km=160.9`: **Wrong.** There is no official 100-mile format. Use variable distance for timed enduros and a route option of **232.28 km** for Attack 240. [Official formats](https://suzuka8h.powertag.jp/2026/01_1.html)
- `elevation_m=null`: Appropriate until a defensible per-lap ascent is obtained; do not render it as zero.
- `field_size='Hundreds of teams'`: Directionally true for the 8-hour team field but incomplete. Prefer **“4,000+ participants across all formats in 2025; 2026 8-hour team capacity 350 teams.”**
- `cutoff_time`: Replace “e.g., 4 or 8 hours” with exact formats: **four-hour and eight-hour timed enduros; Attack 240 has an eight-hour limit.**
- `surface='Paved roads'`: Correct, although “fully paved racing circuit” is more precise.
- `terrain.primary='Mixed terrain'`: Wrong. Different bicycle types are allowed, but the course itself is entirely paved.
- `discipline='gran_fondo'`: Wrong. This is a **timed circuit enduro/team relay**. If your schema cannot represent circuit enduros, the event should be excluded instead of mislabeled as a gran fondo.
- Any motorcycle videos, rider quotations, heat-management advice, history since 1978, manufacturer prestige or FIM EWC material must be removed. Those belong to the separate motorcycle race. [Official motorcycle description](https://www.suzukacircuit.jp/eng/8tai/guide/step1/)

Also avoid confusing it with the separate **Shimano Suzuka Road**, another active bicycle festival at the same circuit, scheduled for September 26–27, 2026. [Official Shimano Suzuka Road overview](https://suzukaroad.shimano.com/2026/under/speech/)
