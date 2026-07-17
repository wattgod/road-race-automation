#!/usr/bin/env python3
"""Generate the Roadie Labs training-plan questionnaire page (static).

Ported from gravel-race-automation's WordPress-block questionnaire
(web/training-plans-questionnaire.html) as a full static page, restyled for
the Roadie Labs monochrome brand (no box-shadow, heavy borders, inverted
fills for active states).

IMPORTANT: the form element IDs, classes, and input names are the `gg-*`
contract expected by web/training-plans-form.js (shared verbatim with the
gravel site — brand differences are injected via window.__TP_FORM_CONFIG).
Do NOT rename them to rl-*; the JS and the Railway webhook parser both
depend on these names.

Output: wordpress/output/questionnaire/index.html
Deploy: python3 scripts/push_wordpress.py --sync-questionnaire wordpress/output/questionnaire
"""

import argparse
from pathlib import Path

from generate_neo_brutalist import (
    SITE_BASE_URL,
    get_page_css,
    build_inline_js,
    write_shared_assets,
)
from brand_tokens import get_ab_head_snippet, get_ga4_head_snippet, get_preload_hints
from shared_footer import get_mega_footer_html
from shared_header import get_site_header_html
from cookie_consent import get_consent_banner_html

OUTPUT_DIR = Path(__file__).parent / "output"

CANONICAL_URL = f"{SITE_BASE_URL}/questionnaire/"

# Form JS is deployed alongside the page (same directory) so the static page
# has no dependency on wp-content/uploads or mu-plugins.
FORM_JS_SRC = "/questionnaire/training-plans-form.js"


def esc(text) -> str:
    if text is None or text == "":
        return ""
    return (str(text).replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;"))


def build_nav() -> str:
    return get_site_header_html(active="training-plans") + f'''
  <div class="rl-breadcrumb">
    <a href="{SITE_BASE_URL}/">Home</a>
    <span class="rl-breadcrumb-sep">&rsaquo;</span>
    <a href="{SITE_BASE_URL}/training-plans/">Training Plans</a>
    <span class="rl-breadcrumb-sep">&rsaquo;</span>
    <span class="rl-breadcrumb-current">Questionnaire</span>
  </div>'''


def build_questionnaire_css() -> str:
    """Questionnaire form CSS — gg-* selectors (JS contract), RL styling.

    Style mapping from the gravel original: cream/brown/teal → newsprint
    monochrome; offset box-shadows removed (RL brand: no box-shadow);
    checked/focus states use inverted fills and the charcoal accent.
    """
    return '''<style>
.tp-questionnaire-page {
  font-family: var(--rl-font-data);
  max-width: 900px;
  margin: 0 auto;
  padding: 0 1.5rem;
}

.tp-questionnaire-page * { box-sizing: border-box; }

.tp-questionnaire-hero {
  padding: 2.5rem 0 2rem;
  border-bottom: var(--rl-border-standard);
  margin-bottom: 2.5rem;
}

.tp-questionnaire-hero h1 {
  font-family: var(--rl-font-data);
  font-size: 2rem;
  font-weight: var(--rl-font-weight-bold);
  text-transform: uppercase;
  letter-spacing: 0.04em;
  line-height: var(--rl-line-height-tight);
  color: var(--rl-color-near-black);
  margin: 0 0 0.75rem 0;
}

.tp-questionnaire-hero p {
  font-family: var(--rl-font-data);
  font-size: 0.85rem;
  color: var(--rl-color-signal-red);
  line-height: var(--rl-line-height-relaxed);
  margin: 0;
  max-width: 600px;
}

.gg-form-container {
  font-family: var(--rl-font-data);
  max-width: 800px;
  margin: 0 auto;
  padding: 2.5rem;
  background: var(--rl-color-white);
  border: var(--rl-border-heavy);
  color: var(--rl-color-near-black);
}

.gg-form-container * { box-sizing: border-box; }

.gg-form-header {
  text-align: center;
  margin-bottom: 2rem;
  padding-bottom: 1.5rem;
  border-bottom: var(--rl-border-standard);
}

.gg-form-badge {
  display: inline-block;
  background: var(--rl-color-near-black);
  color: var(--rl-color-cool-white);
  padding: 0.4rem 1rem;
  font-size: 0.75rem;
  font-weight: var(--rl-font-weight-bold);
  text-transform: uppercase;
  letter-spacing: var(--rl-letter-spacing-wide);
  border: var(--rl-border-subtle);
  margin-bottom: 1rem;
}

.gg-form-header h2 {
  font-size: 1.75rem;
  font-weight: var(--rl-font-weight-bold);
  color: var(--rl-color-near-black);
  margin: 0 0 0.75rem 0;
  text-transform: uppercase;
  letter-spacing: var(--rl-letter-spacing-wide);
}

.gg-form-header p {
  color: var(--rl-color-signal-red);
  font-size: 0.9rem;
  margin: 0 auto;
  max-width: 500px;
}

.gg-form-section {
  margin-bottom: 2rem;
  padding-bottom: 1.5rem;
  border-bottom: 2px solid var(--rl-color-silver);
}

.gg-form-section:last-of-type {
  border-bottom: none;
  margin-bottom: 1rem;
}

.gg-section-header {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin-bottom: 0.5rem;
}

.gg-section-number {
  background: var(--rl-color-near-black);
  color: var(--rl-color-cool-white);
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.85rem;
  font-weight: var(--rl-font-weight-bold);
}

.gg-section-title {
  font-size: 1rem;
  font-weight: var(--rl-font-weight-bold);
  color: var(--rl-color-near-black);
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin: 0;
}

.gg-section-desc {
  font-size: 0.8rem;
  color: var(--rl-color-coral);
  margin: 0 0 1rem 0;
  padding-left: 40px;
}

.gg-form-row {
  display: flex;
  gap: 1.25rem;
  margin-bottom: 1rem;
}

.gg-form-row.triple { flex-wrap: wrap; }
.gg-form-row.triple .gg-form-group { flex: 1 1 30%; min-width: 150px; }
.gg-form-row.quad { flex-wrap: wrap; }
.gg-form-row.quad .gg-form-group { flex: 1 1 22%; min-width: 120px; }

.gg-form-group {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.gg-form-group.full-width { flex: 1 1 100%; }

.gg-form-group label {
  font-size: 0.8rem;
  font-weight: var(--rl-font-weight-semibold);
  color: var(--rl-color-near-black);
  margin-bottom: 0.4rem;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.gg-form-group label .required { color: var(--rl-color-error); }

.gg-form-group input,
.gg-form-group select,
.gg-form-group textarea {
  padding: 0.75rem 1rem;
  font-family: var(--rl-font-data);
  font-size: 0.9rem;
  border: var(--rl-border-standard);
  border-radius: 0;
  background: var(--rl-color-cool-white);
  color: var(--rl-color-near-black);
  transition: border-color var(--rl-animation-duration-fast), background var(--rl-animation-duration-fast);
}

.gg-form-group input:focus,
.gg-form-group select:focus,
.gg-form-group textarea:focus {
  outline: 3px solid var(--rl-color-signal-red);
  outline-offset: 2px;
}

.gg-form-group input::placeholder,
.gg-form-group textarea::placeholder {
  color: var(--rl-color-steel);
  font-style: italic;
}

.gg-form-group select {
  cursor: pointer;
  appearance: none;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='14' height='14' fill='%231a1a1a' viewBox='0 0 16 16'%3E%3Cpath d='M8 12L2 6h12l-6 6z'/%3E%3C/svg%3E");
  background-repeat: no-repeat;
  background-position: right 1rem center;
  padding-right: 2.5rem;
}

.gg-form-group textarea {
  resize: vertical;
  min-height: 100px;
}

.gg-height-row {
  display: flex;
  gap: 0.5rem;
  align-items: center;
}

.gg-height-row input { width: 70px; text-align: center; }
.gg-height-row span { font-size: 0.9rem; color: var(--rl-color-near-black); }

.gg-radio-group {
  display: flex;
  flex-wrap: wrap;
  gap: 0.75rem;
  margin-top: 0.25rem;
}

.gg-radio-option { position: relative; }
.gg-radio-option input { position: absolute; opacity: 0; width: 0; height: 0; }

.gg-radio-option label {
  display: block;
  padding: 0.65rem 1.25rem;
  background: var(--rl-color-cool-white);
  border: var(--rl-border-standard);
  cursor: pointer;
  transition: all var(--rl-animation-duration-fast);
  text-transform: none;
  font-weight: 500;
}

.gg-radio-option input:checked + label {
  background: var(--rl-color-near-black);
  color: var(--rl-color-cool-white);
}

.gg-radio-option input:focus-visible + label {
  outline: 3px solid var(--rl-color-signal-red);
  outline-offset: 2px;
}

.gg-radio-option label:hover { background: var(--rl-color-silver); }
.gg-radio-option input:checked + label:hover { background: var(--rl-color-near-black); }

.gg-checkbox-group {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  margin-top: 0.25rem;
}

.gg-checkbox-option { position: relative; }
.gg-checkbox-option input { position: absolute; opacity: 0; width: 0; height: 0; }

.gg-checkbox-option label {
  display: block;
  padding: 0.5rem 0.85rem;
  background: var(--rl-color-cool-white);
  border: var(--rl-border-subtle);
  cursor: pointer;
  transition: all var(--rl-animation-duration-fast);
  text-transform: none;
  font-weight: 500;
  font-size: 0.85rem;
}

.gg-checkbox-option input:checked + label {
  background: var(--rl-color-near-black);
  color: var(--rl-color-cool-white);
}

.gg-checkbox-option input:focus-visible + label {
  outline: 3px solid var(--rl-color-signal-red);
  outline-offset: 2px;
}

.gg-checkbox-option label:hover { background: var(--rl-color-silver); }
.gg-checkbox-option input:checked + label:hover { background: var(--rl-color-near-black); }

.gg-race-entry {
  background: var(--rl-color-cool-white);
  border: var(--rl-border-subtle);
  padding: 1rem;
  margin-bottom: 1rem;
  position: relative;
}

.gg-race-entry-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.75rem;
}

.gg-race-number {
  font-weight: var(--rl-font-weight-bold);
  font-size: 0.85rem;
  color: var(--rl-color-near-black);
  text-transform: uppercase;
}

.gg-remove-race {
  background: none;
  border: 2px solid var(--rl-color-near-black);
  color: var(--rl-color-near-black);
  padding: 0.25rem 0.5rem;
  font-family: var(--rl-font-data);
  font-size: 0.75rem;
  font-weight: var(--rl-font-weight-semibold);
  cursor: pointer;
  transition: all var(--rl-animation-duration-fast);
}

.gg-remove-race:hover {
  background: var(--rl-color-near-black);
  color: var(--rl-color-cool-white);
}

.gg-race-fields {
  display: grid;
  grid-template-columns: 2fr 1fr 1fr 1fr 1fr;
  gap: 0.75rem;
  align-items: end;
}

.gg-race-fields .gg-form-group { margin-bottom: 0; }

.gg-race-fields input,
.gg-race-fields select {
  padding: 0.6rem 0.75rem;
  font-size: 0.85rem;
}

.gg-add-race-btn {
  background: var(--rl-color-white);
  border: 2px dashed var(--rl-color-near-black);
  color: var(--rl-color-near-black);
  padding: 0.75rem 1.5rem;
  font-family: var(--rl-font-data);
  font-size: 0.85rem;
  font-weight: var(--rl-font-weight-semibold);
  cursor: pointer;
  transition: all var(--rl-animation-duration-fast);
  width: 100%;
  text-transform: uppercase;
}

.gg-add-race-btn:hover {
  background: var(--rl-color-near-black);
  color: var(--rl-color-cool-white);
  border-style: solid;
}

.gg-add-race-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.gg-calculated {
  background: var(--rl-color-silver);
  border: 2px solid var(--rl-color-near-black);
  padding: 0.75rem 1rem;
  margin-top: 0.75rem;
  font-size: 0.85rem;
}

.gg-calculated strong { color: var(--rl-color-near-black); }

.gg-hp-field {
  position: absolute;
  left: -9999px;
  opacity: 0;
  height: 0;
  width: 0;
}

.gg-submit-btn {
  width: 100%;
  padding: 1.1rem 2rem;
  font-family: var(--rl-font-data);
  font-size: 1rem;
  font-weight: var(--rl-font-weight-bold);
  text-transform: uppercase;
  letter-spacing: var(--rl-letter-spacing-wide);
  color: var(--rl-color-cool-white);
  background: var(--rl-color-near-black);
  border: var(--rl-border-heavy);
  cursor: pointer;
  transition: background var(--rl-animation-duration-fast), color var(--rl-animation-duration-fast);
  margin-top: 1rem;
}

.gg-submit-btn:hover {
  background: var(--rl-color-white);
  color: var(--rl-color-near-black);
}

.gg-submit-btn:disabled {
  background: var(--rl-color-silver);
  color: var(--rl-color-coral);
  cursor: not-allowed;
}

.gg-form-message {
  padding: 1rem;
  margin-top: 1.25rem;
  text-align: center;
  font-weight: var(--rl-font-weight-semibold);
  border: 3px solid;
}

.gg-form-message.success {
  background: var(--rl-color-cool-white);
  color: var(--rl-color-near-black);
  border-color: var(--rl-color-near-black);
}

.gg-form-message.error {
  background: var(--rl-color-cool-white);
  color: var(--rl-color-error);
  border-color: var(--rl-color-error);
}

.gg-form-footer {
  text-align: center;
  margin-top: 1.25rem;
  font-size: 0.75rem;
  color: var(--rl-color-coral);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.gg-trust-strip {
  margin-top: 1.5rem;
  padding-top: 1.5rem;
  border-top: var(--rl-border-standard);
}

.gg-trust-badges {
  display: flex;
  justify-content: center;
  gap: 0.75rem;
  flex-wrap: wrap;
}

.gg-trust-badge {
  font-size: 0.7rem;
  font-weight: var(--rl-font-weight-bold);
  text-transform: uppercase;
  letter-spacing: 0.5px;
  color: var(--rl-color-near-black);
  background: var(--rl-color-cool-white);
  border: 2px solid var(--rl-color-near-black);
  padding: 0.4rem 0.75rem;
}

@media (max-width: 700px) {
  .gg-form-container { padding: 1.5rem; }
  .gg-form-row,
  .gg-form-row.triple,
  .gg-form-row.quad {
    flex-direction: column;
    gap: 1rem;
  }
  .gg-form-row.triple .gg-form-group,
  .gg-form-row.quad .gg-form-group {
    flex: 1 1 100%;
    min-width: unset;
  }
  .gg-form-header h2 { font-size: 1.35rem; }
  .gg-radio-group { flex-direction: column; }
  .gg-race-fields { grid-template-columns: 1fr; }
  .tp-questionnaire-hero h1 { font-size: 1.5rem; }
}
</style>'''


def build_form_html() -> str:
    """The questionnaire form markup — gg-* IDs/names are the JS contract."""
    return '''
  <div class="tp-questionnaire-hero">
    <h1>Build Your Plan</h1>
    <p>Five minutes. Be thorough. The plan is only as good as the data.
    Same-day delivery to your TrainingPeaks calendar.</p>
  </div>

  <div class="gg-form-container">
    <div class="gg-form-header">
      <span class="gg-form-badge">Custom Training Plan</span>
      <h2>Build Your Plan</h2>
      <p>Fill out this form, pay securely via Stripe, and your plan will be delivered to your TrainingPeaks calendar same day.</p>
    </div>

    <form id="gg-training-form">
      <!-- Honeypot -->
      <input type="text" name="_honeypot" class="gg-hp-field" tabindex="-1" autocomplete="off">

      <!-- Section 1: Contact Info (email first for abandonment recovery) -->
      <div class="gg-form-section">
        <div class="gg-section-header">
          <span class="gg-section-number">1</span>
          <h3 class="gg-section-title">Contact Info</h3>
        </div>
        <p class="gg-section-desc">Where should we send your plan?</p>
        <div class="gg-form-row">
          <div class="gg-form-group">
            <label>Email <span class="required">*</span></label>
            <input type="email" name="email" required placeholder="you@email.com">
          </div>
          <div class="gg-form-group">
            <label>Name <span class="required">*</span></label>
            <input type="text" name="name" required placeholder="Your name">
          </div>
        </div>
      </div>

      <!-- Section 2: About You -->
      <div class="gg-form-section">
        <div class="gg-section-header">
          <span class="gg-section-number">2</span>
          <h3 class="gg-section-title">About You</h3>
        </div>
        <p class="gg-section-desc">Basic info to help calibrate your plan. Used for zone calculations and recovery planning.</p>

        <div class="gg-form-row quad">
          <div class="gg-form-group">
            <label>Sex <span class="required">*</span></label>
            <select name="sex" required>
              <option value="">Select</option>
              <option value="male">Male</option>
              <option value="female">Female</option>
            </select>
          </div>
          <div class="gg-form-group">
            <label>Age <span class="required">*</span></label>
            <input type="number" name="age" required min="16" max="90" placeholder="35">
          </div>
          <div class="gg-form-group">
            <label>Weight (lbs) <span class="required">*</span></label>
            <input type="number" name="weight" required min="80" max="350" placeholder="165">
          </div>
          <div class="gg-form-group">
            <label>Height <span class="required">*</span></label>
            <div class="gg-height-row">
              <input type="number" name="heightFeet" required min="4" max="7" placeholder="5">
              <span>ft</span>
              <input type="number" name="heightInches" required min="0" max="11" placeholder="10">
              <span>in</span>
            </div>
          </div>
        </div>

        <!-- Menstrual cycle — shown only when sex = female -->
        <div class="gg-form-row dual" id="cycle-row" style="display: none;">
          <div class="gg-form-group">
            <label>Menstrual Cycle Status</label>
            <select name="cycleStatus">
              <option value="">Select</option>
              <option value="regular">Regular cycle</option>
              <option value="irregular">Irregular cycle</option>
              <option value="hormonal-bc">Hormonal birth control</option>
              <option value="iud">IUD (hormonal)</option>
              <option value="iud-copper">IUD (copper / non-hormonal)</option>
              <option value="perimenopause">Perimenopause</option>
              <option value="postmenopause">Postmenopause</option>
              <option value="prefer-not">Prefer not to say</option>
            </select>
          </div>
          <div class="gg-form-group">
            <label>Track Your Cycle?</label>
            <select name="cycleTracking">
              <option value="">Select</option>
              <option value="yes-app">Yes (app)</option>
              <option value="yes-manual">Yes (manual)</option>
              <option value="no">No</option>
            </select>
          </div>
        </div>

        <div class="gg-form-row triple">
          <div class="gg-form-group">
            <label>Years Cycling <span class="required">*</span></label>
            <select name="yearsCycling" required>
              <option value="">Select</option>
              <option value="<1">&lt;1 year</option>
              <option value="1-2">1-2 years</option>
              <option value="3-5">3-5 years</option>
              <option value="5-10">5-10 years</option>
              <option value="10+">10+ years</option>
            </select>
          </div>
          <div class="gg-form-group">
            <label>Typical Sleep <span class="required">*</span></label>
            <select name="typicalSleep" required>
              <option value="">Select</option>
              <option value="excellent">Excellent (8+ hrs)</option>
              <option value="good">Good (7-8 hrs)</option>
              <option value="fair">Fair (6-7 hrs)</option>
              <option value="poor">Poor (&lt;6 hrs)</option>
            </select>
          </div>
          <div class="gg-form-group">
            <label>Life Stress Level <span class="required">*</span></label>
            <select name="stressLevel" required>
              <option value="">Select</option>
              <option value="low">Low</option>
              <option value="moderate">Moderate</option>
              <option value="high">High</option>
              <option value="very-high">Very High</option>
            </select>
          </div>
        </div>

        <div class="gg-form-row dual">
          <div class="gg-form-group">
            <label>Prior Structured Plan Experience</label>
            <select name="priorPlanExperience">
              <option value="">Select</option>
              <option value="none">Never followed a plan</option>
              <option value="generic">Used a generic/free plan</option>
              <option value="app">Used an app (TrainerRoad, Zwift, etc.)</option>
              <option value="coached">Worked with a coach</option>
              <option value="custom">Had a custom plan built before</option>
            </select>
          </div>
          <div class="gg-form-group">
            <label>Travel During Training Block?</label>
            <select name="travelDuringPlan">
              <option value="">Select</option>
              <option value="none">No significant travel</option>
              <option value="short">Short trip (2-4 days)</option>
              <option value="week">Week-long trip</option>
              <option value="multi">Multiple trips</option>
              <option value="frequent">Frequent travel (work)</option>
            </select>
          </div>
        </div>
      </div>

      <!-- Section 3: Race Calendar -->
      <div class="gg-form-section">
        <div class="gg-section-header">
          <span class="gg-section-number">3</span>
          <h3 class="gg-section-title">Race Calendar</h3>
        </div>
        <p class="gg-section-desc">Add your target events for the season. Mark your priority: A = main goal, B = important, C = training race.</p>

        <div id="races-container"></div>
        <button type="button" id="add-race-btn" class="gg-add-race-btn">+ Add Race</button>
      </div>

      <!-- Section 4: Current Fitness -->
      <div class="gg-form-section">
        <div class="gg-section-header">
          <span class="gg-section-number">4</span>
          <h3 class="gg-section-title">Current Fitness</h3>
        </div>
        <p class="gg-section-desc">Helps me understand your starting point. Don't worry if you don't have power data.</p>

        <div class="gg-form-group" style="margin-bottom: 1rem;">
          <label>Current USA Cycling Road Category</label>
          <select name="roadCategory">
            <option value="">Select (optional)</option>
            <option value="unlicensed">Unlicensed / not sure</option>
            <option value="cat_5">Novice / Cat 5</option>
            <option value="cat_4">Cat 4</option>
            <option value="cat_3">Cat 3</option>
            <option value="cat_2">Cat 2</option>
            <option value="cat_1">Cat 1</option>
          </select>
          <small>License category is based on racing experience and results, not W/kg.</small>
        </div>

        <div class="gg-form-group">
          <label>Longest ride in the past month? <span class="required">*</span></label>
          <div class="gg-radio-group">
            <div class="gg-radio-option">
              <input type="radio" name="recentRideDuration" id="ride-2" value="<2hrs" required>
              <label for="ride-2">&lt;2 hrs</label>
            </div>
            <div class="gg-radio-option">
              <input type="radio" name="recentRideDuration" id="ride-3" value="2-3hrs">
              <label for="ride-3">2-3 hrs</label>
            </div>
            <div class="gg-radio-option">
              <input type="radio" name="recentRideDuration" id="ride-4" value="3-4hrs">
              <label for="ride-4">3-4 hrs</label>
            </div>
            <div class="gg-radio-option">
              <input type="radio" name="recentRideDuration" id="ride-5" value="4-5hrs">
              <label for="ride-5">4-5 hrs</label>
            </div>
            <div class="gg-radio-option">
              <input type="radio" name="recentRideDuration" id="ride-6" value="5-6hrs">
              <label for="ride-6">5-6 hrs</label>
            </div>
            <div class="gg-radio-option">
              <input type="radio" name="recentRideDuration" id="ride-6plus" value="6+hrs">
              <label for="ride-6plus">6+ hrs</label>
            </div>
          </div>
        </div>

        <div class="gg-form-group" style="margin-top: 1rem;">
          <label>Do you train with power or heart rate?</label>
          <div class="gg-radio-group">
            <div class="gg-radio-option">
              <input type="radio" name="powerOrHr" id="metric-power" value="power">
              <label for="metric-power">Power</label>
            </div>
            <div class="gg-radio-option">
              <input type="radio" name="powerOrHr" id="metric-hr" value="hr">
              <label for="metric-hr">Heart Rate</label>
            </div>
            <div class="gg-radio-option">
              <input type="radio" name="powerOrHr" id="metric-both" value="both">
              <label for="metric-both">Both</label>
            </div>
            <div class="gg-radio-option">
              <input type="radio" name="powerOrHr" id="metric-neither" value="rpe">
              <label for="metric-neither">Neither</label>
            </div>
          </div>
        </div>

        <div id="powerFields" style="display: none; margin-top: 1rem;">
          <div class="gg-form-row">
            <div class="gg-form-group">
              <label>FTP (watts)</label>
              <input type="number" name="ftp" id="ftpInput" min="50" max="500" placeholder="e.g., 250">
            </div>
          </div>
          <div id="pwCalc" class="gg-calculated" style="display: none;">
            <strong>Estimated W/kg:</strong> <span id="wkgValue">--</span> &nbsp;|&nbsp;
            <strong>Power band:</strong> <span id="catValue">--</span>
          </div>
        </div>

        <div id="hrFields" style="display: none; margin-top: 1rem;">
          <div class="gg-form-row triple">
            <div class="gg-form-group">
              <label>Max HR (bpm)</label>
              <input type="number" name="maxHr" min="100" max="220" placeholder="e.g., 185">
            </div>
            <div class="gg-form-group">
              <label>Threshold HR (bpm)</label>
              <input type="number" name="lthr" min="80" max="200" placeholder="e.g., 165">
            </div>
            <div class="gg-form-group">
              <label>Resting HR (bpm)</label>
              <input type="number" name="restingHr" min="30" max="100" placeholder="e.g., 52">
            </div>
          </div>
        </div>
      </div>

      <!-- Section 5: Your Schedule -->
      <div class="gg-form-section">
        <div class="gg-section-header">
          <span class="gg-section-number">5</span>
          <h3 class="gg-section-title">Your Schedule</h3>
        </div>
        <p class="gg-section-desc">Tell me when and how much you can train.</p>

        <div class="gg-form-row">
          <div class="gg-form-group">
            <label>Weekly Training Hours <span class="required">*</span></label>
            <select name="weeklyHours" required>
              <option value="">Select</option>
              <option value="3-5">3-5 hours</option>
              <option value="5-7">5-7 hours</option>
              <option value="7-10">7-10 hours</option>
              <option value="10-12">10-12 hours</option>
              <option value="12-15">12-15 hours</option>
              <option value="15+">15+ hours</option>
            </select>
          </div>
          <div class="gg-form-group">
            <label>Indoor Trainer Access <span class="required">*</span></label>
            <select name="trainerType" required>
              <option value="">Select</option>
              <option value="smart">Smart Trainer</option>
              <option value="basic">Basic Trainer</option>
              <option value="outdoor">Outdoor Only</option>
            </select>
          </div>
        </div>

        <div class="gg-form-group">
          <label>Preferred Long Ride Day(s) <span class="required">*</span></label>
          <div class="gg-checkbox-group" id="longRideDays">
            <div class="gg-checkbox-option"><input type="checkbox" name="longRideDays" id="long-mon" value="Monday"><label for="long-mon">Mon</label></div>
            <div class="gg-checkbox-option"><input type="checkbox" name="longRideDays" id="long-tue" value="Tuesday"><label for="long-tue">Tue</label></div>
            <div class="gg-checkbox-option"><input type="checkbox" name="longRideDays" id="long-wed" value="Wednesday"><label for="long-wed">Wed</label></div>
            <div class="gg-checkbox-option"><input type="checkbox" name="longRideDays" id="long-thu" value="Thursday"><label for="long-thu">Thu</label></div>
            <div class="gg-checkbox-option"><input type="checkbox" name="longRideDays" id="long-fri" value="Friday"><label for="long-fri">Fri</label></div>
            <div class="gg-checkbox-option"><input type="checkbox" name="longRideDays" id="long-sat" value="Saturday"><label for="long-sat">Sat</label></div>
            <div class="gg-checkbox-option"><input type="checkbox" name="longRideDays" id="long-sun" value="Sunday"><label for="long-sun">Sun</label></div>
            <div class="gg-checkbox-option"><input type="checkbox" name="longRideDays" id="long-flex" value="Flexible"><label for="long-flex">Flexible</label></div>
          </div>
        </div>

        <div class="gg-form-group" style="margin-top: 1rem;">
          <label>Preferred Hard Interval Day(s) <span class="required">*</span></label>
          <div class="gg-checkbox-group" id="intervalDays">
            <div class="gg-checkbox-option"><input type="checkbox" name="intervalDays" id="int-mon" value="Monday"><label for="int-mon">Mon</label></div>
            <div class="gg-checkbox-option"><input type="checkbox" name="intervalDays" id="int-tue" value="Tuesday"><label for="int-tue">Tue</label></div>
            <div class="gg-checkbox-option"><input type="checkbox" name="intervalDays" id="int-wed" value="Wednesday"><label for="int-wed">Wed</label></div>
            <div class="gg-checkbox-option"><input type="checkbox" name="intervalDays" id="int-thu" value="Thursday"><label for="int-thu">Thu</label></div>
            <div class="gg-checkbox-option"><input type="checkbox" name="intervalDays" id="int-fri" value="Friday"><label for="int-fri">Fri</label></div>
            <div class="gg-checkbox-option"><input type="checkbox" name="intervalDays" id="int-sat" value="Saturday"><label for="int-sat">Sat</label></div>
            <div class="gg-checkbox-option"><input type="checkbox" name="intervalDays" id="int-sun" value="Sunday"><label for="int-sun">Sun</label></div>
            <div class="gg-checkbox-option"><input type="checkbox" name="intervalDays" id="int-flex" value="Flexible"><label for="int-flex">Flexible</label></div>
          </div>
        </div>

        <div class="gg-form-group" style="margin-top: 1rem;">
          <label>Required Off Days (if any)</label>
          <div class="gg-checkbox-group" id="daysOff">
            <div class="gg-checkbox-option"><input type="checkbox" name="daysOff" id="off-mon" value="Monday"><label for="off-mon">Mon</label></div>
            <div class="gg-checkbox-option"><input type="checkbox" name="daysOff" id="off-tue" value="Tuesday"><label for="off-tue">Tue</label></div>
            <div class="gg-checkbox-option"><input type="checkbox" name="daysOff" id="off-wed" value="Wednesday"><label for="off-wed">Wed</label></div>
            <div class="gg-checkbox-option"><input type="checkbox" name="daysOff" id="off-thu" value="Thursday"><label for="off-thu">Thu</label></div>
            <div class="gg-checkbox-option"><input type="checkbox" name="daysOff" id="off-fri" value="Friday"><label for="off-fri">Fri</label></div>
            <div class="gg-checkbox-option"><input type="checkbox" name="daysOff" id="off-sat" value="Saturday"><label for="off-sat">Sat</label></div>
            <div class="gg-checkbox-option"><input type="checkbox" name="daysOff" id="off-sun" value="Sunday"><label for="off-sun">Sun</label></div>
          </div>
        </div>
      </div>

      <!-- Section 6: Strength Training -->
      <div class="gg-form-section">
        <div class="gg-section-header">
          <span class="gg-section-number">6</span>
          <h3 class="gg-section-title">Strength Training</h3>
        </div>

        <div class="gg-form-group">
          <label>Current Strength Training <span class="required">*</span></label>
          <div class="gg-radio-group">
            <div class="gg-radio-option"><input type="radio" name="currentStrength" id="str-none" value="none" required><label for="str-none">None</label></div>
            <div class="gg-radio-option"><input type="radio" name="currentStrength" id="str-occasional" value="occasional"><label for="str-occasional">Occasional</label></div>
            <div class="gg-radio-option"><input type="radio" name="currentStrength" id="str-1x" value="1x-week"><label for="str-1x">1x/week</label></div>
            <div class="gg-radio-option"><input type="radio" name="currentStrength" id="str-2x" value="2x-week"><label for="str-2x">2x/week</label></div>
            <div class="gg-radio-option"><input type="radio" name="currentStrength" id="str-dedicated" value="dedicated"><label for="str-dedicated">Dedicated Program</label></div>
          </div>
        </div>

        <div class="gg-form-row" style="margin-top: 1rem;">
          <div class="gg-form-group">
            <label>Include Strength in Plan? <span class="required">*</span></label>
            <select name="includeStrength" required>
              <option value="">Select</option>
              <option value="yes">Yes, include it</option>
              <option value="no">No, I'll handle it separately</option>
              <option value="your-call">Your call</option>
            </select>
          </div>
          <div class="gg-form-group">
            <label>Equipment Available</label>
            <select name="strengthEquipment">
              <option value="">Select</option>
              <option value="full-gym">Full Gym</option>
              <option value="home-basic">Home - Basic (dumbbells, bands)</option>
              <option value="home-full">Home - Full Setup</option>
              <option value="bodyweight">Bodyweight Only</option>
              <option value="none">None</option>
            </select>
          </div>
        </div>
      </div>

      <!-- Section 7: Additional Notes -->
      <div class="gg-form-section">
        <div class="gg-section-header">
          <span class="gg-section-number">7</span>
          <h3 class="gg-section-title">Additional Notes</h3>
        </div>

        <div class="gg-form-group">
          <label>Injuries or Limitations</label>
          <textarea name="injuries" placeholder="Any current or past injuries, physical limitations, or health considerations I should know about?"></textarea>
        </div>

        <div class="gg-form-group" style="margin-top: 1rem;">
          <label>Anything Else?</label>
          <textarea name="additionalNotes" placeholder="Other context, goals, concerns, or questions..."></textarea>
        </div>
      </div>

      <!-- Trust signals before checkout -->
      <div class="gg-trust-strip">
        <div class="gg-trust-badges">
          <span class="gg-trust-badge">7-Day Full Refund</span>
          <span class="gg-trust-badge">Secure Checkout via Stripe</span>
          <span class="gg-trust-badge">Same-Day Delivery</span>
        </div>
      </div>

      <button type="submit" class="gg-submit-btn">Submit &amp; Pay</button>
    </form>

    <div id="gg-form-message" class="gg-form-message" style="display: none;"></div>

    <div class="gg-form-footer">
      Not satisfied? Full refund within 7 days, no questions asked.
    </div>
  </div>'''


def generate_questionnaire_page(external_assets: dict = None) -> str:
    nav = build_nav()
    form_css = build_questionnaire_css()
    form_html = build_form_html()
    footer = get_mega_footer_html()

    if external_assets:
        page_css = external_assets['css_tag']
        inline_js = external_assets['js_tag']
    else:
        page_css = get_page_css()
        inline_js = build_inline_js()

    meta_desc = (
        "Build your custom road cycling training plan. Five-minute questionnaire, "
        "same-day delivery to TrainingPeaks. $15/week, capped at $249."
    )

    og_tags = f'''<meta property="og:title" content="Build Your Training Plan | Roadie Labs">
  <meta property="og:description" content="{esc(meta_desc)}">
  <meta property="og:type" content="website">
  <meta property="og:url" content="{esc(CANONICAL_URL)}">
  <meta property="og:image" content="{SITE_BASE_URL}/og/homepage.jpg">
  <meta property="og:site_name" content="Roadie Labs">
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:title" content="Build Your Training Plan | Roadie Labs">
  <meta name="twitter:description" content="{esc(meta_desc)}">'''

    # Brand config consumed by training-plans-form.js (shared with gravel)
    form_config = f'''<script>window.__TP_FORM_CONFIG = {{
  racePlaceholder: "e.g., Maratona dles Dolomites",
  source: "roadielabs.com/questionnaire",
  showRoadFields: true
}};</script>
<script src="{FORM_JS_SRC}" defer></script>'''

    return f'''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Build Your Training Plan | Roadie Labs</title>
  <meta name="description" content="{esc(meta_desc)}">
  <meta name="robots" content="noindex, follow">
  <link rel="canonical" href="{esc(CANONICAL_URL)}">
  <link rel="preconnect" href="https://www.googletagmanager.com" crossorigin>
  {get_preload_hints()}
  {og_tags}
  {page_css}
  {form_css}
  {get_ga4_head_snippet()}
  {get_ab_head_snippet()}
</head>
<body>

<div class="rl-neo-brutalist-page">
  {nav}

<div class="tp-questionnaire-page">
{form_html}
</div>

  {footer}
</div>

{inline_js}
{form_config}

{get_consent_banner_html()}
</body>
</html>'''


def main():
    parser = argparse.ArgumentParser(description="Generate Roadie Labs questionnaire page")
    parser.add_argument("--output-dir", default=str(OUTPUT_DIR), help="Output directory")
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    q_dir = output_dir / "questionnaire"
    q_dir.mkdir(parents=True, exist_ok=True)

    assets = write_shared_assets(output_dir)

    html_content = generate_questionnaire_page(external_assets=assets)
    output_file = q_dir / "index.html"
    output_file.write_text(html_content, encoding="utf-8")
    print(f"Generated {output_file} ({len(html_content):,} bytes)")

    # Form JS deploys alongside the page
    form_js = Path(__file__).parent.parent / "web" / "training-plans-form.js"
    if form_js.exists():
        (q_dir / "training-plans-form.js").write_text(
            form_js.read_text(encoding="utf-8"), encoding="utf-8")
        print(f"Copied {form_js.name} → {q_dir / 'training-plans-form.js'}")
    else:
        print(f"WARNING: {form_js} not found — questionnaire will not submit. "
              f"Copy it from gravel-race-automation/web/.")


if __name__ == "__main__":
    main()
