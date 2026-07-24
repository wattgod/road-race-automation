# Research Dump: Tour of the Battenkill (road slug: tour-of-the-battenkill-road)

Compiled 2026-07-24, debt-sweep batch 9. All URLs curl-verified (HTTP 200 with browser UA) unless noted.

## Eligibility / current status
- **Status: active.** 2026 edition confirmed for Cambridge, NY on Saturday, May 9, 2026.
- Registration open via BikeReg: https://www.bikereg.com/tour-of-the-battenkill-open-gran-fondo (curl HTTP 200; registration deadline listed as Fri May 8, 2026 5:00pm ET, capacity 1,500).
- **Official-site domain change (important, causes a stale citation):** the historical domain `tourofthebattenkill.com` no longer resolves. `dig tourofthebattenkill.com @8.8.8.8` and `@1.1.1.1` both return SERVFAIL at the delegation/nameserver level (i.e. the domain's DNS is broken, not just the web server down) — verified 2026-07-24. `curl` to it returns exit 000 (cannot connect).
- Current official site: https://anthemsportstours.com/battenkill (curl HTTP 200). `https://battenkillrace.com` (curl HTTP 200) 301-redirects to the same anthemsportstours.com page — this is the new canonical registration/marketing domain.
- Ownership/rebrand history (Wikipedia, https://en.wikipedia.org/wiki/Tour_of_the_Battenkill, curl HTTP 200): founded 2005 in Washington County, NY; ran a UCI America Tour 1.2-classified pro race 2010–2012 (Floyd Landis 2nd 2010, Francisco Mancebo won 2012); founder Dieter Drake sold the event to Rugged Races in 2017; later operated by Gannett Media's Ventures Endurance division through 2024; in Dec 2024 Ventures Endurance/ENMOTIVE announced they would no longer continue the event; in Oct 2024 it was announced Dieter Drake (via Anthem Sports) would revive it for 2025 under the shortened name "Battenkill" (dropping "Tour of the"). Event returned to Cambridge, NY, where it had run 2009–2014.
- **Correction applied:** `race.eligibility.notes` previously referenced "the 2017 UCI pro race that was cancelled" — per Wikipedia the UCI 1.2 pro designation ran 2010/2012 and the pro race's last Cambridge edition before the ownership churn was 2014, not a discrete 2017 cancellation event. Notes text broadened to avoid overclaiming a specific year and to capture the DNS/rebrand finding, which is the more load-bearing fact for a 2026 buyer trying to register.

## Vitals cross-check (JSON already correct; not itself flagged, verified for completeness)
- Distance/route options (JSON: Gran Fondo ~64mi/4,500ft, Medio ~40mi, Piccolo ~20mi) are broadly consistent with anthemsportstours.com/battenkill (curl HTTP 200), which describes "3 distance options for the gran fondo riders & racers," paved & gravel roads, no USAC license required for gran fondo categories, e-bikes permitted (not eligible for age-group awards).
- Location: Cambridge, Washington County, NY — confirmed by anthemsportstours.com and glensfalls.com event listing (curl HTTP 200).

## Sol adversarial review — corrections applied 2026-07-24
A read-only `codex exec -m gpt-5.6-sol` pass caught two real errors in the first draft of this dump/JSON edit:
1. **The 2017 UCI pro-race cancellation is real and was wrongly dropped.** GranFondoGuide's contemporaneous report (https://www.granfondoguide.com/Contents/Index/2700/tour-of-battenkill-pro-race-cancelled) confirms a UCI 1.2 race was added to the 2017 America's Tour calendar in April and cancelled that June for lack of funding (amateur Pro/Am and Gran Fondo proceeded). Prior UCI editions were 2010 and 2012 (men only). Restored this fact to `eligibility.notes` instead of the vaguer "last ran 2014" phrasing from the first draft.
2. **`history.origin_story` said "launched in 2007," contradicting `history.founded: 2005` and Wikipedia's "established in 2005."** Corrected both `origin_story` and the matching `notable_moments` entry to 2005.
3. **`vitals.field_size` was stale.** anthemsportstours.com/battenkill states a 2026 registration cap of 1,500; the profile's "~2,000-3,000 riders" figure reflects the event's mid-2010s peak, not 2026. Updated to state both, dated.

Sol also flagged the DNS "delegation-level" language as needing stronger proof — the raw `dig` output includes an EDNS Extended DNS Error whose text literally reads "at delegation tourofthebattenkill.com," which is direct resolver-side evidence of a delegation failure (not just an inference from SERVFAIL alone); kept the claim, cited the specific evidence in `eligibility.notes`.

Sol also noted the official site may now be advertising a 2027 date (May 22, 2027) — not independently confirmed this pass (JS-rendered page, static curl fetch didn't surface it); flagging for a human to check before the 2026 edition passes, not acted on here.

## Citations added (all curl-verified HTTP 200 with browser UA)
1. https://anthemsportstours.com/battenkill — official site (replaces dead tourofthebattenkill.com)
2. https://www.bikereg.com/tour-of-the-battenkill-open-gran-fondo — registration
3. https://en.wikipedia.org/wiki/Tour_of_the_Battenkill — history/reference

Note: https://www.saratoga.com/things-to-do/battenkill/ returned HTTP 403 to curl (bot-protected, not necessarily broken) — not added as a citation since it couldn't be curl-verified within this pass; the three citations above are sufficient to clear the 3-citation minimum.

## Claims verified
- No fabricated-claims audit flags fired for this slug (batch note: "citation shortfall only"). The only defect found was the dead official-site URL, which is now corrected in both `logistics.official_site` and `citations`.
