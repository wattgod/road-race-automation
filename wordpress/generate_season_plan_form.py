#!/usr/bin/env python3
"""
Generate /season-plan/ — the Season Plan's own intake form.

A new page (Matti ruling, 2026-09-23, docs/specs/goals-2027-funnel-spec.md
D9), NOT the Elementor /questionnaire/ page (whose widget drifts from this
repo — see repo CLAUDE.md). The /goals/ offer's Season Plan CTA links here,
carrying ?t=<poster_token> when the visitor arrived from a saved /goals/
submission (see mission_control/routers/season_plan_prefill.py); the form
works blank with no token.

What it asks (matching field names web/training-plans-form.js and the
Railway checkout server already understand, so Motoren can build from the
stored intake — see docs/specs/goals-2027-funnel-spec.md D9):
  - name, email (prefilled from the token when present)
  - every race for the year, A/B/C priority + date (races[], add/remove
    rows, at least one A race required)
  - hours per week, days NOT available to train (off_days — same field the
    race-plan questionnaire uses)
  - equipment: power meter / HR monitor / smart trainer (yes/no each)
  - health/injury notes
  - strength preference + equipment
  - TrainingPeaks delivery email (if different from the account email)

No FTP or other training-number questions — those come from data (Matti
ruling), not asked here.

Posts to the SAME Railway create-checkout endpoint as the race plan, with
product: "season_plan" plus offer_variant/entry_src/race_slug attribution.
Price is read from data/pricing.json, never hardcoded.

Usage:
    python generate_season_plan_form.py
    python generate_season_plan_form.py --output-dir ./output
"""
from __future__ import annotations

import argparse
from pathlib import Path

from generate_neo_brutalist import (
    SITE_BASE_URL, _safe_json_for_script, get_page_css, write_shared_assets,
)
from brand_tokens import get_ga4_head_snippet, get_preload_hints
from shared_footer import get_mega_footer_html
from shared_header import get_site_header_html, get_site_header_js
from cookie_consent import get_consent_banner_html
from generate_coaching_apply import build_apply_css
from pricing import SEASON_PLAN_PRICE_CENTS, SEASON_PLAN_PRICE_DISPLAY, SEASON_PLAN_DELIVERY_DAYS

OUTPUT_DIR = Path(__file__).parent / "output"

PAGE_URL = SITE_BASE_URL + "/season-plan/"
FORMSUBMIT_EMAIL = "coach@roadielabs.com"

WEEKLY_HOURS_OPTIONS = [
    "<5 hrs", "5-7 hrs", "7-10 hrs", "10-13 hrs", "13-16 hrs", "16+ hrs",
]
DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


def build_nav() -> str:
    return get_site_header_html(active="products") + f'''
  <div class="rl-breadcrumb">
    <a href="{SITE_BASE_URL}/">Home</a>
    <span class="rl-breadcrumb-sep">&rsaquo;</span>
    <span class="rl-breadcrumb-current">Season Plan</span>
  </div>'''


def build_header() -> str:
    return f'''<div class="rl-apply-header">
    <h1>The Season Plan</h1>
    <p>{SEASON_PLAN_PRICE_DISPLAY}. I build it myself; it's in your TrainingPeaks within {SEASON_PLAN_DELIVERY_DAYS} days of payment.</p>
  </div>'''


def build_prefill_box(field_id: str, label: str) -> str:
    # Hidden until the page's own JS confirms a valid token resolved a real
    # value — never rendered with server-side data (this is a static
    # generated page; the token lookup happens client-side against
    # Mission Control). Toggling to an editable field is a page-JS concern;
    # the box itself is read-only display.
    return (
        f'<div class="rl-sp-onfile" id="{field_id}" hidden>'
        f'<span class="rl-sp-onfile-label">{label}, already on file</span>'
        f'<span class="rl-sp-onfile-value" data-prefill-value></span>'
        f"</div>"
    )


def build_you_section() -> str:
    return f'''<div class="rl-apply-section-title" data-section-n="1">1. You</div>
      <div class="rl-apply-inline">
        <div class="rl-apply-group">
          <label class="rl-apply-label" for="name">Name <span class="rl-apply-required">*</span></label>
          <input type="text" id="name" name="name" required placeholder="Your name">
        </div>
        <div class="rl-apply-group">
          <label class="rl-apply-label" for="email">Email <span class="rl-apply-required">*</span></label>
          <input type="email" id="email" name="email" required placeholder="you@email.com">
        </div>
      </div>
      {build_prefill_box("rl-sp-goal-onfile", "Goal")}
      {build_prefill_box("rl-sp-habits-onfile", "Habits")}'''


def build_races_section() -> str:
    return '''<div class="rl-apply-section-title" data-section-n="2">2. Your season</div>
      <div id="season-races-container"></div>
      <button type="button" id="season-add-race-btn" class="rl-sp-add-race-btn">+ Add another race</button>'''


def build_capacity_section() -> str:
    hours_opts = "".join(f'<option value="{o}">{o}</option>' for o in WEEKLY_HOURS_OPTIONS)
    days_boxes = "".join(
        f'<label class="rl-apply-checkbox-option"><input type="checkbox" name="off_days" value="{d}">'
        f'<span class="rl-apply-checkbox-label">{d[:3]}</span></label>'
        for d in DAYS
    )
    return f'''<div class="rl-apply-section-title" data-section-n="3">3. Training capacity</div>
      <div class="rl-apply-group">
        <label class="rl-apply-label" for="hours_per_week">Hours per week, on average <span class="rl-apply-required">*</span></label>
        <select id="hours_per_week" name="hours_per_week" required><option value="">Select...</option>{hours_opts}</select>
      </div>
      <div class="rl-apply-group">
        <label class="rl-apply-label">Days you are generally NOT available to train</label>
        <div class="rl-apply-checkbox-vertical rl-sp-days-row">{days_boxes}</div>
      </div>'''


def _yes_no_radio(name: str, label: str) -> str:
    return f'''<div class="rl-apply-group">
        <label class="rl-apply-label">{label}</label>
        <div class="rl-apply-radio-group rl-apply-radio-horizontal" data-radio="{name}">
          <label class="rl-apply-radio-option"><input type="radio" name="{name}" value="yes"><div class="rl-apply-radio-label"><div class="rl-apply-radio-title">Yes</div></div></label>
          <label class="rl-apply-radio-option"><input type="radio" name="{name}" value="no"><div class="rl-apply-radio-label"><div class="rl-apply-radio-title">No</div></div></label>
        </div>
      </div>'''


def build_equipment_section() -> str:
    return f'''<div class="rl-apply-section-title" data-section-n="4">4. Equipment</div>
      {_yes_no_radio("has_power_meter", "Power meter")}
      {_yes_no_radio("has_hr_monitor", "Heart rate monitor")}
      {_yes_no_radio("has_trainer", "Smart trainer")}'''


def build_health_section() -> str:
    return '''<div class="rl-apply-section-title" data-section-n="5">5. Health &amp; notes</div>
      <div class="rl-apply-group">
        <label class="rl-apply-label" for="notes">Anything I should know — injuries, health notes, constraints</label>
        <textarea id="notes" name="notes" rows="3" placeholder="Optional"></textarea>
      </div>'''


def build_strength_section() -> str:
    return '''<div class="rl-apply-section-title" data-section-n="6">6. Strength</div>
      <div class="rl-apply-group">
        <label class="rl-apply-label" for="strength_want">Include a strength track in the plan?</label>
        <select id="strength_want" name="strength_want">
          <option value="">Select...</option>
          <option value="yes">Yes</option>
          <option value="no">No</option>
          <option value="maybe">Not sure</option>
        </select>
      </div>
      <div class="rl-apply-group">
        <label class="rl-apply-label" for="strength_equipment">Strength equipment available</label>
        <input type="text" id="strength_equipment" name="strength_equipment" placeholder="e.g., full gym, dumbbells only, none">
      </div>'''


def build_delivery_section() -> str:
    return '''<div class="rl-apply-section-title" data-section-n="7">7. TrainingPeaks delivery</div>
      <div class="rl-apply-group">
        <label class="rl-apply-label" for="tp_email">TrainingPeaks account email, if different from above</label>
        <input type="email" id="tp_email" name="tp_email" placeholder="Optional">
      </div>'''


def build_footer() -> str:
    return f'''<div class="rl-apply-confidential-wrap">
    <p class="rl-apply-confidential">I build every plan myself. You see the number before
    you pay. Your answers are used to build and coach this plan as described in the
    <a href="/privacy/">Privacy Policy</a>. Questions? Email {FORMSUBMIT_EMAIL}</p>
  </div>
  ''' + get_mega_footer_html()


def build_season_plan_css() -> str:
    return '''<style>
.rl-sp-onfile[hidden] { display: none; }
.rl-sp-onfile { display: flex; align-items: baseline; gap: 8px; margin: -8px 0 16px; padding: 10px 12px; background: var(--rl-color-silver); border: 2px solid var(--rl-color-dark-navy); font-size: 13px; }
.rl-sp-onfile-label { font-weight: 700; text-transform: uppercase; letter-spacing: .03em; color: var(--rl-color-primary-navy); }
.rl-sp-onfile-value { color: var(--rl-color-near-black); }
.rl-sp-race-entry { border: 2px solid var(--rl-color-dark-navy); padding: 16px; margin-bottom: 12px; background: var(--rl-color-cool-white); }
.rl-sp-race-entry-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; }
.rl-sp-race-number { font-weight: 700; text-transform: uppercase; font-size: 12px; letter-spacing: .03em; }
.rl-sp-remove-race { background: none; border: 2px solid var(--rl-color-dark-navy); padding: 4px 10px; font: 700 11px/1 var(--rl-font-data); text-transform: uppercase; cursor: pointer; }
.rl-sp-race-fields { display: flex; flex-wrap: wrap; gap: 12px; }
.rl-sp-race-fields .rl-apply-group { flex: 1 1 150px; margin-bottom: 0; }
.rl-sp-add-race-btn { display: block; width: 100%; padding: 12px; background: none; border: 2px dashed var(--rl-color-dark-navy); font: 700 13px/1 var(--rl-font-data); text-transform: uppercase; cursor: pointer; margin-bottom: 24px; }
.rl-sp-days-row { display: flex; flex-wrap: wrap; gap: 8px; }
</style>'''


def build_season_plan_js() -> str:
    # sol review: repr() on a data/pricing.json string is the banned
    # script-breakout pattern (repo CLAUDE.md) even though the current
    # SEASON_PLAN_PRICE_DISPLAY value is harmless — repr() doesn't escape
    # "</", so a future price display string containing it would break
    # out of the <script> tag. _safe_json_for_script() is the repo's
    # sanctioned safe serializer.
    js_template = (Path(__file__).parent.parent / "web" / "season-plan-form.js").read_text()
    js = (
        js_template
        .replace("__SEASON_PLAN_PRICE_DISPLAY__", _safe_json_for_script(SEASON_PLAN_PRICE_DISPLAY))
        .replace("__SEASON_PLAN_PRICE_CENTS_DOLLARS__", str(SEASON_PLAN_PRICE_CENTS / 100))
    )
    return f"<script>\n{js}\n</script>"


def generate_season_plan_page(external_assets=None) -> str:
    page_css = external_assets["css_tag"] if external_assets else get_page_css()
    title = "Season Plan | Roadie Labs"
    description = (
        f"{SEASON_PLAN_PRICE_DISPLAY} flat. Every A/B/C race of your year periodised, "
        "four scheduled rebuilds. I build every plan myself."
    )
    return f'''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{title}</title>
  <meta name="robots" content="index, follow">
  <link rel="canonical" href="{PAGE_URL}">
  <meta property="og:title" content="{title}">
  <meta name="description" content="{description}">
  <meta property="og:description" content="{description}">
  <meta property="og:type" content="website">
  <meta property="og:url" content="{PAGE_URL}">
  <meta property="og:image" content="{SITE_BASE_URL}/og/homepage.jpg">
  <link rel="icon" href="/race/assets/rl-logo.svg" type="image/svg+xml">
  {get_preload_hints()}
  {page_css}
  {get_ga4_head_snippet()}
  {build_apply_css()}
  {build_season_plan_css()}
</head>
<body class="rl-neo-brutalist-page" style="background:var(--rl-color-cool-white);color:var(--rl-color-near-black);font-family:var(--rl-font-data);font-size:var(--rl-font-size-sm);line-height:1.7;min-height:100vh">
  {build_nav()}
  <div class="rl-apply-container">
    {build_header()}
    <div id="rl-season-message" class="rl-apply-message hidden"></div>
    <form id="rl-season-form" class="rl-apply-form-card">
      <input type="text" name="website" class="rl-apply-honeypot" tabindex="-1" autocomplete="off">
      {build_you_section()}
      {build_races_section()}
      {build_capacity_section()}
      {build_equipment_section()}
      {build_health_section()}
      {build_strength_section()}
      {build_delivery_section()}
      <div class="rl-apply-actions">
        <button type="submit" class="rl-apply-submit-btn" id="season-submit-btn">Submit &amp; Pay — {SEASON_PLAN_PRICE_DISPLAY}</button>
      </div>
    </form>
  </div>
  {build_footer()}
  {build_season_plan_js()}
  <script>{get_site_header_js()}</script>
  {get_consent_banner_html()}
</body>
</html>'''


def main():
    parser = argparse.ArgumentParser(description="Generate the /season-plan/ page")
    parser.add_argument("--output-dir", default=str(OUTPUT_DIR))
    args = parser.parse_args()

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    assets = write_shared_assets(out_dir)

    html = generate_season_plan_page(external_assets=assets)
    out_path = out_dir / "season-plan.html"
    out_path.write_text(html)
    print(f"Wrote {out_path}")


if __name__ == "__main__":
    main()
