#!/usr/bin/env python3
"""
Generate the Roadie Labs Consulting intake form at /consulting/intake/.

Fourteen questions, five minutes, save/resume via localStorage. Reads the
booking session ref and the athlete's private intake token from the URL
FRAGMENT (`#ref=...&t=...`) — never the query string, so neither value is
logged by servers or shows up in referrer headers. The token itself is only
ever emailed to the athlete in their welcome email; if it's missing (e.g.
someone lands here from the success page instead of the email), the page
still works and tells them to use the emailed link instead.

Submits `{ref, t, answers}` as JSON to the pipeline's /api/consult-intake
endpoint (token travels in the POST body, not a header or query param, to
keep the simple-CORS story intact).

Uses brand tokens exclusively — zero hardcoded hex, no border-radius, no
box-shadow, no bounce easing, no entrance animations.

Usage:
    python generate_consult_intake.py
    python generate_consult_intake.py --output-dir ./output
"""
from __future__ import annotations

import argparse
import html
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
from generate_consulting import PRIVACY_SENTENCE

OUTPUT_DIR = Path(__file__).parent / "output"

CONSULT_INTAKE_API = "https://athlete-custom-training-plan-pipeline-production.up.railway.app/api/consult-intake"


def esc(text) -> str:
    """HTML-escape a string."""
    return html.escape(str(text)) if text else ""


# ── Page sections ─────────────────────────────────────────────


def build_nav() -> str:
    return get_site_header_html(active="services") + f'''
  <div class="rl-breadcrumb">
    <a href="{SITE_BASE_URL}/">Home</a>
    <span class="rl-breadcrumb-sep">&rsaquo;</span>
    <a href="{SITE_BASE_URL}/consulting/">Consulting</a>
    <span class="rl-breadcrumb-sep">&rsaquo;</span>
    <span class="rl-breadcrumb-current">Intake</span>
  </div>'''


def build_header() -> str:
    return '''<div class="rl-intake-header">
    <div class="rl-intake-badge">Consult Intake</div>
    <h1>Twelve Questions, Five Minutes</h1>
    <p>Answer what you can. Skip what you don&rsquo;t know &mdash; &ldquo;don&rsquo;t know&rdquo; is a fine answer for FTP and LTHR. Save and come back if you need to.</p>
  </div>
  <div class="rl-intake-token-banner" id="token-banner" style="display:none">
    Can&rsquo;t find your booking reference? Use the link in your welcome email instead &mdash; it connects your answers to your consult automatically. You can still fill this out; I&rsquo;ll match it up.
  </div>'''


def build_fields() -> str:
    return '''<div class="rl-intake-group">
      <label class="rl-intake-label" for="goal_event">Goal event</label>
      <input type="text" id="goal_event" name="goal_event" placeholder="Race or event name">
    </div>
    <div class="rl-intake-group">
      <label class="rl-intake-label" for="goal_date">Date</label>
      <input type="date" id="goal_date" name="goal_date">
    </div>
    <div class="rl-intake-inline">
      <div class="rl-intake-group">
        <label class="rl-intake-label" for="hours_typical">Typical weekly hours</label>
        <input type="text" id="hours_typical" name="hours_typical" placeholder="e.g. 8">
      </div>
      <div class="rl-intake-group">
        <label class="rl-intake-label" for="hours_max">Max weekly hours</label>
        <input type="text" id="hours_max" name="hours_max" placeholder="e.g. 12">
      </div>
    </div>
    <div class="rl-intake-group">
      <label class="rl-intake-label" for="years_training">Years training</label>
      <input type="text" id="years_training" name="years_training" placeholder="e.g. 3">
    </div>
    <div class="rl-intake-inline">
      <div class="rl-intake-group">
        <label class="rl-intake-label" for="ftp">Your threshold power (FTP), if you know it</label>
        <input type="text" id="ftp" name="ftp" placeholder="Watts, or &quot;don't know&quot;">
      </div>
      <div class="rl-intake-group">
        <label class="rl-intake-label" for="lthr">Your threshold heart rate (LTHR), if you know it</label>
        <input type="text" id="lthr" name="lthr" placeholder="BPM, or &quot;don't know&quot;">
      </div>
    </div>
    <div class="rl-intake-group">
      <label class="rl-intake-label" for="top_question">The one question you most want answered</label>
      <textarea id="top_question" name="top_question" rows="3"></textarea>
    </div>
    <div class="rl-intake-group">
      <label class="rl-intake-label" for="whats_gone_wrong">What&rsquo;s gone wrong this year</label>
      <textarea id="whats_gone_wrong" name="whats_gone_wrong" rows="3"></textarea>
    </div>
    <div class="rl-intake-group">
      <label class="rl-intake-label" for="injuries_limits">Injuries or limits</label>
      <textarea id="injuries_limits" name="injuries_limits" rows="2"></textarea>
    </div>
    <div class="rl-intake-group">
      <label class="rl-intake-label" for="tp_email">The email you sign in to TrainingPeaks with (or &quot;no TP&quot;)</label>
      <input type="text" id="tp_email" name="tp_email" placeholder="you@example.com, or &quot;no TP&quot;">
    </div>
    <div class="rl-intake-inline">
      <div class="rl-intake-group">
        <span class="rl-intake-label">Power meter?</span>
        <div class="rl-intake-radio-row">
          <label class="rl-intake-radio-option"><input type="radio" name="power_meter" value="yes"> Yes</label>
          <label class="rl-intake-radio-option"><input type="radio" name="power_meter" value="no"> No</label>
        </div>
      </div>
      <div class="rl-intake-group">
        <span class="rl-intake-label">HR strap?</span>
        <div class="rl-intake-radio-row">
          <label class="rl-intake-radio-option"><input type="radio" name="hr_strap" value="yes"> Yes</label>
          <label class="rl-intake-radio-option"><input type="radio" name="hr_strap" value="no"> No</label>
        </div>
      </div>
    </div>
    <div class="rl-intake-group">
      <label class="rl-intake-label" for="coaching_history">Coaching or plan history</label>
      <textarea id="coaching_history" name="coaching_history" rows="2"></textarea>
    </div>
    <div class="rl-intake-group">
      <label class="rl-intake-label" for="anything_else">Anything else</label>
      <textarea id="anything_else" name="anything_else" rows="2"></textarea>
    </div>'''


def build_submit_buttons() -> str:
    return '''<div class="rl-intake-buttons">
      <button type="button" id="save-btn" class="rl-intake-save-btn">Save Progress</button>
      <button type="submit" id="submit-btn" class="rl-intake-submit-btn">Submit</button>
    </div>'''


def build_success_state() -> str:
    return '''<div id="intake-success" class="rl-intake-success" style="display:none">
    <h2>Got it &mdash; I&rsquo;ll have your read done before we talk.</h2>
  </div>'''


def build_privacy() -> str:
    return f'''<p class="rl-intake-privacy">{PRIVACY_SENTENCE}</p>'''


def build_footer() -> str:
    return get_mega_footer_html()


def build_jsonld() -> str:
    return f'''<script type="application/ld+json">
{{
  "@context": "https://schema.org",
  "@type": "WebPage",
  "name": "Consulting Intake",
  "url": "{SITE_BASE_URL}/consulting/intake/"
}}
</script>'''


def build_intake_css() -> str:
    return '''<style>
.rl-intake-container {
  max-width: 640px;
  margin: 0 auto;
  padding: var(--rl-spacing-xl) var(--rl-spacing-xl) var(--rl-spacing-2xl);
}
.rl-intake-header {
  text-align: center;
  margin-bottom: var(--rl-spacing-lg);
}
.rl-intake-badge {
  display: inline-block;
  font-family: var(--rl-font-data);
  font-size: var(--rl-font-size-2xs);
  font-weight: var(--rl-font-weight-bold);
  letter-spacing: var(--rl-letter-spacing-wide);
  text-transform: uppercase;
  color: var(--rl-color-secondary-blue);
  margin-bottom: var(--rl-spacing-sm);
}
.rl-intake-header h1 {
  font-family: var(--rl-font-editorial);
  font-size: clamp(24px, 4vw, 32px);
  font-weight: var(--rl-font-weight-bold);
  color: var(--rl-color-dark-navy);
  margin: 0 0 var(--rl-spacing-sm) 0;
}
.rl-intake-header p {
  font-family: var(--rl-font-editorial);
  font-size: var(--rl-font-size-sm);
  line-height: var(--rl-line-height-prose);
  color: var(--rl-color-signal-red);
  margin: 0;
}
.rl-intake-token-banner {
  font-family: var(--rl-font-data);
  font-size: var(--rl-font-size-xs);
  line-height: var(--rl-line-height-normal);
  color: var(--rl-color-dark-navy);
  background: var(--rl-color-silver);
  border: 2px solid var(--rl-color-orange);
  padding: var(--rl-spacing-md);
  margin-bottom: var(--rl-spacing-lg);
}
.rl-intake-form-card {
  background: var(--rl-color-cool-white);
  border: 3px solid var(--rl-color-dark-navy);
  padding: var(--rl-spacing-xl);
}
.rl-intake-inline {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--rl-spacing-md);
}
.rl-intake-group {
  margin-bottom: var(--rl-spacing-md);
}
.rl-intake-label {
  display: block;
  font-family: var(--rl-font-data);
  font-size: var(--rl-font-size-xs);
  font-weight: var(--rl-font-weight-bold);
  letter-spacing: var(--rl-letter-spacing-wide);
  text-transform: uppercase;
  color: var(--rl-color-dark-navy);
  margin-bottom: var(--rl-spacing-xs);
}
.rl-intake-group input[type="text"],
.rl-intake-group input[type="date"],
.rl-intake-group textarea {
  display: block;
  width: 100%;
  padding: var(--rl-spacing-sm) var(--rl-spacing-md);
  font-family: var(--rl-font-data);
  font-size: var(--rl-font-size-sm);
  color: var(--rl-color-dark-navy);
  background: var(--rl-color-white);
  border: 2px solid var(--rl-color-dark-navy);
  box-sizing: border-box;
  resize: vertical;
}
.rl-intake-group input:focus,
.rl-intake-group textarea:focus {
  outline: none;
  border-color: var(--rl-color-orange);
}
.rl-intake-radio-row {
  display: flex;
  gap: var(--rl-spacing-md);
}
.rl-intake-radio-option {
  display: flex;
  align-items: center;
  gap: var(--rl-spacing-2xs);
  font-family: var(--rl-font-data);
  font-size: var(--rl-font-size-sm);
  color: var(--rl-color-signal-red);
  cursor: pointer;
}
.rl-intake-honeypot {
  position: absolute;
  left: -9999px;
}
.rl-intake-buttons {
  display: flex;
  gap: var(--rl-spacing-md);
  margin-top: var(--rl-spacing-lg);
}
.rl-intake-submit-btn,
.rl-intake-save-btn {
  flex: 1;
  padding: var(--rl-spacing-sm) var(--rl-spacing-lg);
  font-family: var(--rl-font-data);
  font-size: var(--rl-font-size-xs);
  font-weight: var(--rl-font-weight-bold);
  letter-spacing: var(--rl-letter-spacing-ultra-wide);
  text-transform: uppercase;
  cursor: pointer;
  border: 3px solid var(--rl-color-dark-navy);
  transition: background-color var(--rl-transition-hover), border-color var(--rl-transition-hover);
}
.rl-intake-submit-btn {
  color: var(--rl-color-dark-navy);
  background: var(--rl-color-light-orange);
}
.rl-intake-submit-btn:hover {
  background-color: var(--rl-color-orange);
  border-color: var(--rl-color-orange);
}
.rl-intake-submit-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}
.rl-intake-save-btn {
  color: var(--rl-color-signal-red);
  background: var(--rl-color-white);
}
.rl-intake-save-btn:hover {
  background-color: var(--rl-color-silver);
}
.rl-intake-message {
  margin-top: var(--rl-spacing-md);
  font-family: var(--rl-font-data);
  font-size: var(--rl-font-size-xs);
  text-align: center;
}
.rl-intake-message.info {
  color: var(--rl-color-coral);
}
.rl-intake-message.error {
  color: var(--rl-color-error);
  border: 2px solid var(--rl-color-error);
  padding: var(--rl-spacing-sm) var(--rl-spacing-md);
  background: var(--rl-color-silver);
}
.rl-intake-message.hidden {
  display: none;
}
.rl-intake-success {
  text-align: center;
  padding: var(--rl-spacing-2xl) var(--rl-spacing-xl);
  background: var(--rl-color-cool-white);
  border: 3px solid var(--rl-color-coral);
}
.rl-intake-success h2 {
  font-family: var(--rl-font-editorial);
  font-size: clamp(22px, 4vw, 28px);
  font-weight: var(--rl-font-weight-bold);
  color: var(--rl-color-dark-navy);
  margin: 0;
}
.rl-intake-privacy {
  font-family: var(--rl-font-data);
  font-size: var(--rl-font-size-2xs);
  color: var(--rl-color-secondary-blue);
  text-align: center;
  line-height: var(--rl-line-height-normal);
  margin-top: var(--rl-spacing-xl);
}
@media (max-width: 600px) {
  .rl-intake-container { padding: var(--rl-spacing-lg) var(--rl-spacing-md) var(--rl-spacing-xl); }
  .rl-intake-form-card { padding: var(--rl-spacing-lg); }
  .rl-intake-inline { grid-template-columns: 1fr; }
  .rl-intake-buttons { flex-direction: column; }
}
</style>'''


def build_intake_js() -> str:
    return f'''<script>
(function(){{
  var API_URL = "{CONSULT_INTAKE_API}";
  var STORAGE_KEY = "consult_intake_progress";

  /* ── Parse ref/t from the URL FRAGMENT only — never the query string ── */
  function parseFragment(){{
    var hash = window.location.hash || "";
    if (hash.indexOf("#") === 0) {{ hash = hash.slice(1); }}
    var params = new URLSearchParams(hash);
    return {{ ref: params.get("ref") || "", t: params.get("t") || "" }};
  }}
  var frag = parseFragment();

  if (!frag.t) {{
    var banner = document.getElementById("token-banner");
    if (banner) {{ banner.style.display = "block"; }}
  }}

  var form = document.getElementById("intake-form");
  var msgEl = document.getElementById("intake-message");
  var submitBtn = document.getElementById("submit-btn");
  var successEl = document.getElementById("intake-success");

  function showMessage(type, text){{
    if (!msgEl) return;
    msgEl.className = "rl-intake-message " + type;
    msgEl.textContent = text;
  }}

  /* ── Save progress ── */
  var saveBtn = document.getElementById("save-btn");
  if (saveBtn) {{
    saveBtn.addEventListener("click", function(){{
      var data = {{}};
      new FormData(form).forEach(function(value, key){{
        if (key === "_honeypot") return;
        data[key] = value;
      }});
      localStorage.setItem(STORAGE_KEY, JSON.stringify(data));
      showMessage("info", "Progress saved. Come back anytime.");
      if (typeof gtag === "function") {{ gtag("event", "consult_intake_progress_saved", {{}}); }}
    }});
  }}

  /* ── Restore progress ── */
  function restoreProgress(){{
    var saved = localStorage.getItem(STORAGE_KEY);
    if (!saved) return;
    try {{
      var data = JSON.parse(saved);
      Object.keys(data).forEach(function(key){{
        var elements = form.querySelectorAll('[name="' + key + '"]');
        elements.forEach(function(el){{
          if (el.type === "radio") {{ el.checked = (el.value === data[key]); }}
          else {{ el.value = data[key]; }}
        }});
      }});
    }} catch (e) {{ /* ignore corrupt localStorage */ }}
  }}

  /* ── Submit ── */
  if (form) {{
    form.addEventListener("submit", function(e){{
      e.preventDefault();
      var honeypot = form.querySelector('input[name="_honeypot"]').value;
      if (honeypot) return;

      submitBtn.disabled = true;
      submitBtn.textContent = "Submitting...";
      showMessage("info", "");

      var answers = {{}};
      new FormData(form).forEach(function(value, key){{
        if (key === "_honeypot") return;
        answers[key] = value;
      }});

      var payload = {{ ref: frag.ref, t: frag.t, answers: answers }};

      fetch(API_URL, {{
        method: "POST",
        headers: {{ "Content-Type": "application/json" }},
        body: JSON.stringify(payload)
      }}).then(function(r){{
        if (!r.ok) throw new Error("Server error (" + r.status + ")");
        return r.json();
      }}).then(function(){{
        localStorage.removeItem(STORAGE_KEY);
        if (typeof gtag === "function") {{ gtag("event", "consult_intake_submitted", {{}}); }}
        form.style.display = "none";
        if (successEl) {{ successEl.style.display = "block"; successEl.scrollIntoView({{ behavior: "smooth", block: "center" }}); }}
      }}).catch(function(err){{
        /* Keep the draft in localStorage — do NOT clear it on error */
        showMessage("error", "Something went wrong. Your answers are saved on this device — try again, or reply to your welcome email.");
        submitBtn.disabled = false;
        submitBtn.textContent = "Submit";
        if (typeof gtag === "function") {{ gtag("event", "consult_intake_error", {{ error: err.message || "unknown" }}); }}
      }});
    }});
  }}

  if (typeof gtag === "function") {{ gtag("event", "consult_intake_page_view", {{}}); }}

  restoreProgress();
}})();
</script>'''


def generate_intake_page(external_assets: dict = None) -> str:
    canonical_url = f"{SITE_BASE_URL}/consulting/intake/"

    nav = build_nav()
    header = build_header()
    fields = build_fields()
    buttons = build_submit_buttons()
    success = build_success_state()
    privacy = build_privacy()
    footer = build_footer()
    jsonld = build_jsonld()
    intake_css = build_intake_css()
    intake_js = build_intake_js()

    if external_assets:
        page_css = external_assets['css_tag']
        inline_js = external_assets['js_tag']
    else:
        page_css = get_page_css()
        inline_js = build_inline_js()

    preload = get_preload_hints()

    return f'''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Consulting Intake | Roadie Labs</title>
  <meta name="description" content="Twelve questions before your consult call — five minutes, save and come back.">
  <meta name="robots" content="noindex, follow">
  <link rel="canonical" href="{esc(canonical_url)}">
  <link rel="preconnect" href="https://www.googletagmanager.com" crossorigin>
  {preload}
  {jsonld}
  {page_css}
  {intake_css}
  {get_ga4_head_snippet()}
  {get_ab_head_snippet()}
</head>
<body>

<div class="rl-neo-brutalist-page">
  {nav}

  <div class="rl-intake-container">
    {header}
    <form id="intake-form" class="rl-intake-form-card" novalidate>
      <input type="text" name="_honeypot" class="rl-intake-honeypot" tabindex="-1" autocomplete="off">
      {fields}
      {buttons}
      <div id="intake-message" class="rl-intake-message hidden"></div>
    </form>
    {success}
    {privacy}
  </div>

  {footer}
</div>

{inline_js}
{intake_js}

{get_consent_banner_html()}
</body>
</html>'''


def main():
    parser = argparse.ArgumentParser(description="Generate Roadie Labs consulting intake page")
    parser.add_argument("--output-dir", default=str(OUTPUT_DIR), help="Output directory")
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    assets = write_shared_assets(output_dir)

    html_content = generate_intake_page(external_assets=assets)
    output_file = output_dir / "consult-intake.html"
    output_file.write_text(html_content, encoding="utf-8")
    print(f"Generated {output_file} ({len(html_content):,} bytes)")


if __name__ == "__main__":
    main()
