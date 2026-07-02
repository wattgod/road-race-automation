# Roadie Labs Email Marketing — pointer

Roadie Labs' email sequences do NOT live in this repo. They live in
**gravel-race-automation** (Mission Control serves both brands, brand-routed):

- Sequence definitions: `gravel-race-automation/mission_control/sequences/road_*.py`
- Templates (monochrome deadpan): `gravel-race-automation/mission_control/templates/emails/sequences/road_*.html`
- Voice bible: `gravel-race-automation/docs/email-voice-model.md`
- Conversion principles: `gravel-race-automation/docs/email-conversion-principles.md`
- Weeks-to-race trigger spec: `gravel-race-automation/docs/specs/race-countdown-trigger.md`
  — NOTE: that spec requires a `scripts/generate_race_dates.py` + deployed
  `web/race-dates.json` in THIS repo (parses `vitals.date_specific` from
  `race-data/*.json`; omit unparseable dates, never guess).

Sending: Resend, `matti@roadielabs.com` (domain verified Jul 2026 —
DKIM/SPF/MX live in Cloudflare DNS). Lead intake: the shared
`fueling-lead-intake` Cloudflare worker (gravel repo) tags `brand:'roadielabs'`.

Voice in one line: deadpan, clinical, zero profanity, zero winks; the joke
budget is one flat parenthetical; a verdict sentence ("No.") replaces every
swear; urgency only as audit-finding arithmetic built from true mechanics.
