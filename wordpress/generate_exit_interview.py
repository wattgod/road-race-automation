#!/usr/bin/env python3
"""Generate Roadie Labs' coached-athlete exit interview at /coaching/exit/."""

import argparse
import html
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from brand_tokens import get_ga4_head_snippet, get_preload_hints
from cookie_consent import get_consent_banner_html
from generate_coaching_apply import build_apply_css
from generate_neo_brutalist import get_page_css
from shared_footer import get_mega_footer_html
from shared_header import get_site_header_html, get_site_header_js

OUTPUT_DIR = Path(__file__).parent / "output" / "coaching-exit"
WORKER_URL = "https://fueling-lead-intake.gravelgodcoaching.workers.dev"
BRAND = "roadielabs"
CONTACT_EMAIL = "coach@roadielabs.com"
MAX_ANSWER_LEN = 4000


SECTIONS = [
    {"title": "You", "fields": [
        {"kind": "pair", "fields": [
            {"name": "name", "label": "Name", "kind": "text", "req": True, "auto": "name"},
            {"name": "email", "label": "Email", "kind": "email", "req": True, "auto": "email"},
        ]},
        {"name": "athlete", "kind": "hidden"},
    ]},
    {"title": "Why Now", "sub": "The real reason. There isn&#39;t a wrong one.", "fields": [
        {"name": "exit_reason", "label": "What&#39;s the main reason you&#39;re stopping?", "kind": "radio", "req": True,
         "options": [("done", "I got what I came for", "The race is done or the goal is hit"),
                     ("time", "Life got full", "Work, family, a move, the calendar"),
                     ("cost", "Cost", "The money needs to go elsewhere for now"),
                     ("health", "Injury or health"), ("break", "A break from structured training"),
                     ("diy", "Coaching myself from here", "Or riding off a plan"),
                     ("elsewhere", "Moving to another coach, team or app"),
                     ("fit", "The coaching wasn&#39;t the right fit"),
                     ("progress", "I wasn&#39;t seeing the progress I wanted"), ("other", "Something else")]},
        {"name": "exit_story", "label": "What tipped it, and when did you know?", "kind": "area", "rows": 3,
         "ph": "The week, the conversation, the race. Whatever it was."},
        {"name": "stay_lever", "label": "What, if anything, would have kept you?", "kind": "text",
         "ph": "“Nothing, it was time” is a fine answer."},
    ]},
    {"title": "The Report Card", "sub": "I&#39;ve graded you long enough. Your turn.", "fields": [
        {"name": "recommend", "label": "How likely are you to recommend me to a rider like you?", "kind": "scale",
         "low": "Not likely", "high": "Already have"},
        {"name": "keep_doing", "label": "What should I keep doing?", "kind": "area", "rows": 2},
        {"name": "change_one", "label": "What&#39;s one thing I should change?", "kind": "area", "rows": 2,
         "ph": "Be blunt. I&#39;d rather hear it from you than guess."},
        {"name": "what_changed", "label": "What changed for you while we worked together?", "kind": "area", "rows": 3,
         "ph": "Results, habits, how you think about training. “Not much” is worth knowing too."},
    ]},
    {"title": "On the Record", "sub": "Optional. Skip it and nothing changes.", "fields": [
        {"name": "quote", "label": "If a rider asked whether they should hire me, what would you tell them?", "kind": "area", "rows": 3,
         "ph": "In your words, the way you'd say it. Good, bad or both."},
        {"name": "not_for", "label": "And who shouldn&#39;t hire me?", "kind": "text", "ph": "The rider this wouldn't work for"},
        {"name": "share_as", "label": "Can I share what you wrote above?", "kind": "radio",
         "options": [("full", "Yes, with my full name"), ("initial", "Yes, first name and last initial"),
                     ("age_group", "Yes, first name and age group"), ("private", "No, keep it between us")]},
        {"name": "age_group", "label": "Your age group. It only shows if you picked first name and age group. If you&#39;re under 18, I&#39;ll need a parent&#39;s OK.",
         "kind": "select", "options": [("under_18", "Under 18"), ("18_29", "18–29"), ("30_39", "30–39"),
                                        ("40_49", "40–49"), ("50_59", "50–59"), ("60_plus", "60+")]},
        {"name": "share_where", "label": "Where it can appear", "kind": "checks",
         "options": [("where_site", "roadielabs.com"), ("where_social", "Roadie Labs social posts"),
                     ("where_email", "Emails to riders thinking about coaching"),
                     ("where_tp", "My TrainingPeaks coach profile")]},
        {"name": "connection", "label": "Anything connecting us besides coaching? If so, I say so next to your words.", "kind": "radio",
         "options": [("none", "No, just coaching"), ("comped", "You coached me free or at a discount"),
                     ("friend", "We&#39;re friends or ride together"), ("work", "We&#39;ve worked together"), ("family", "We&#39;re family")]},
        {"name": "reference", "label": "If someone thinking about coaching wants to talk to a real athlete, can I introduce you by email?", "kind": "radio",
         "options": [("yes", "Yes"), ("ask", "Ask me first each time"), ("no", "No")]},
        {"name": "consent_note", "kind": "note", "text": "Before anything goes up, I&#39;ll send you the exact words and how they&#39;ll look, and nothing runs until you say yes. I won&#39;t edit your words without asking. It stays up for three years at most. Reply any time and it comes down within 7 days, though I can&#39;t pull back screenshots, reposts or search-engine copies. If you&#39;re under 18, I&#39;ll need a parent&#39;s OK too."},
    ]},
    {"title": "Loose Ends", "fields": [
        {"name": "come_back", "label": "Would you come back one day?", "kind": "radio",
         "options": [("yes", "Probably"), ("maybe", "Maybe"), ("no", "Probably not")]},
        {"name": "checkin", "label": "Want me to check in later? Once, then I leave you alone.", "kind": "radio",
         "options": [("none", "No thanks"), ("3m", "In about three months"), ("6m", "In about six months"),
                     ("preseason", "Before next season")]},
        {"name": "needs", "label": "Anything you need from me before you go?", "kind": "checks",
         "options": [("need_zones", "A summary of my zones and latest tests"),
                     ("need_notes", "Notes for training on my own"),
                     ("need_billing", "Confirmation that billing has stopped"),
                     ("need_tp", "Help with my TrainingPeaks account")]},
        {"name": "last_word", "label": "Anything else?", "kind": "area", "rows": 3, "ph": "Last word&#39;s yours."},
    ]},
]


def _attr(value: str) -> str:
    return html.escape(str(value), quote=True)


def _control(field: dict) -> str:
    kind, name = field["kind"], field.get("name", "")
    required = " required" if field.get("req") else ""
    placeholder = f' placeholder="{_attr(field["ph"])}"' if field.get("ph") else ""
    if kind == "hidden":
        return f'<input type="hidden" id="{name}" name="{name}">'
    if kind in ("text", "email"):
        auto = f' autocomplete="{field["auto"]}"' if field.get("auto") else ""
        limit = f' maxlength="{MAX_ANSWER_LEN}"' if kind == "text" else ""
        return f'<input type="{kind}" id="{name}" name="{name}"{required}{placeholder}{auto}{limit}>'
    if kind == "area":
        return f'<textarea id="{name}" name="{name}" rows="{field.get("rows", 3)}" maxlength="{MAX_ANSWER_LEN}"{required}{placeholder}></textarea>'
    if kind == "select":
        options = '<option value="">Select...</option>' + "".join(
            f'<option value="{_attr(value)}">{label}</option>' for value, label in field["options"])
        return f'<select id="{name}" name="{name}"{required}>{options}</select>'
    if kind == "radio":
        options = "".join(
            f'<label class="rl-apply-radio-option"><input type="radio" name="{name}" value="{_attr(option[0])}"'
            f'{required if index == 0 else ""}><div class="rl-apply-radio-label">'
            f'<div class="rl-apply-radio-title">{option[1]}</div>'
            + (f'<div class="rl-apply-radio-desc">{option[2]}</div>' if len(option) > 2 else "")
            + '</div></label>' for index, option in enumerate(field["options"]))
        return f'<div class="rl-apply-radio-group" data-radio="{name}">{options}</div>'
    if kind == "checks":
        options = "".join(
            f'<label class="rl-apply-checkbox-option"><input type="checkbox" name="{_attr(value)}" value="yes">'
            f'<span class="rl-apply-checkbox-label">{label}</span></label>' for value, label in field["options"])
        return f'<div class="rl-apply-checkbox-vertical">{options}</div>'
    if kind == "scale":
        options = "".join(
            f'<label class="rl-exit-scale-option"><input type="radio" name="{name}" value="{number}" aria-label="{number}">'
            f'<span>{number}</span></label>' for number in range(11))
        return (f'<div class="rl-exit-scale" role="radiogroup" aria-labelledby="{name}-label">{options}</div>'
                f'<div class="rl-exit-scale-ends"><span>{field["low"]}</span><span>{field["high"]}</span></div>')
    if kind == "note":
        return f'<div class="rl-exit-note">{field["text"]}</div>'
    raise ValueError(kind)


def render_field(field: dict) -> str:
    if field["kind"] == "hidden":
        return _control(field)
    if field["kind"] == "pair":
        return '<div class="rl-apply-inline">' + "".join(render_field(item) for item in field["fields"]) + '</div>'
    label = ""
    if field.get("label"):
        star = ' <span class="rl-apply-required">*</span>' if field.get("req") else ""
        target = f' for="{field["name"]}"' if field["kind"] not in ("radio", "checks", "scale") else ""
        ident = f' id="{field["name"]}-label"' if field["kind"] == "scale" else ""
        label = f'<label class="rl-apply-label"{ident}{target}>{field["label"]}{star}</label>'
    return f'<div class="rl-apply-group">{label}{_control(field)}</div>'


def render_sections() -> str:
    blocks = []
    for number, section in enumerate(SECTIONS, 1):
        sub = f'<p class="rl-exit-section-sub">{section["sub"]}</p>' if section.get("sub") else ""
        fields = "".join(render_field(field) for field in section["fields"])
        blocks.append(f'<div class="rl-apply-section-title">{number}. {section["title"]}</div>{sub}{fields}')
    return "\n".join(blocks)


def build_css() -> str:
    return """<style>
.rl-exit-section-sub { margin:-10px 0 22px; color:var(--rl-color-secondary-blue); font-family:var(--rl-font-editorial); }
.rl-exit-note { border:2px solid var(--rl-color-near-black); background:var(--rl-color-cool-white); padding:16px; font-family:var(--rl-font-editorial); line-height:1.55; }
.rl-exit-scale { display:grid; grid-template-columns:repeat(11,minmax(36px,1fr)); gap:4px; overflow-x:auto; padding-bottom:4px; }
.rl-exit-scale-option { cursor:pointer; min-width:36px; }
.rl-exit-scale-option input { position:absolute; opacity:0; }
.rl-exit-scale-option span { display:flex; min-height:44px; align-items:center; justify-content:center; border:2px solid var(--rl-color-near-black); background:var(--rl-color-white); font-family:var(--rl-font-data); font-weight:700; }
.rl-exit-scale-option input:checked + span { background:var(--rl-color-signal-red); color:var(--rl-color-white); }
.rl-exit-scale-option input:focus-visible + span { outline:3px solid var(--rl-color-signal-red); outline-offset:2px; }
.rl-exit-scale-ends { display:flex; justify-content:space-between; color:var(--rl-color-secondary-blue); font-family:var(--rl-font-data); font-size:var(--rl-font-size-2xs); }
.rl-exit-success { border:var(--rl-border-standard); background:var(--rl-color-white); padding:var(--rl-spacing-xl); margin-bottom:var(--rl-spacing-xl); }
.rl-exit-success h2 { margin:0 0 8px; font-family:var(--rl-font-editorial); font-size:var(--rl-font-size-2xl); }
.rl-exit-success[hidden] { display:none; }
@media (max-width:600px) {
  .rl-exit-scale { grid-template-columns:repeat(11,minmax(24px,1fr)); }
  .rl-exit-scale-option { min-width:24px; }
}
</style>"""


def build_exit_personal_link_js() -> str:
    """Read private prefills from the URL fragment, which never reaches the server."""
    return r"""<script>
(function() {
  var keys = ['name','email','athlete'], found = {};
  try {
    var params = new URLSearchParams(window.location.hash.replace(/^#\??/, ''));
    keys.forEach(function(key) {
      if (params.has(key)) found[key] = params.get(key) || '';
    });
    if (Object.keys(found).length) {
      history.replaceState(history.state, '', window.location.pathname + window.location.search);
    }
  } catch (error) {}
  window.rlPersonalLink = found;
})();
</script>"""


def build_js() -> str:
    return f"""<script>
(function() {{
  'use strict';
  var STORAGE_KEY = 'roadielabs_athlete_exit_v1';
  var form = document.getElementById('exit-form');
  var message = document.getElementById('message');
  var submit = document.getElementById('exit-submit');
  var saveTimer = null;
  var submitted = false;

  function show(kind, text) {{
    message.className = 'rl-apply-message ' + kind;
    message.textContent = text;
    message.classList.remove('hidden');
  }}
  function collect() {{
    var data = {{}};
    new FormData(form).forEach(function(value, key) {{
      if (key !== 'website' && String(value).trim()) data[key] = String(value).trim();
    }});
    return data;
  }}
  function save(silent) {{
    try {{
      localStorage.setItem(STORAGE_KEY, JSON.stringify(collect()));
      if (!silent) show('info', 'Saved in this browser. Close the page and come back any time.');
      return true;
    }} catch (error) {{
      if (!silent) show('error', 'This browser will not let me save. Keep the page open until you submit.');
      return false;
    }}
  }}
  function updateProgress() {{
    var required = Array.prototype.slice.call(form.querySelectorAll('[required]'));
    var names = required.filter(function(el, i, all) {{ return all.findIndex(function(x) {{ return x.name === el.name; }}) === i; }});
    var filled = names.filter(function(el) {{
      return el.type === 'radio' ? !!form.querySelector('input[name="' + el.name + '"]:checked') : !!el.value.trim();
    }}).length;
    var pct = names.length ? Math.round(filled / names.length * 100) : 0;
    document.getElementById('progress-fill').style.width = pct + '%';
    document.getElementById('progress-text').textContent = pct + '% complete';
  }}
  function paintChoices() {{
    form.querySelectorAll('.rl-apply-radio-option,.rl-apply-checkbox-option').forEach(function(label) {{
      var input = label.querySelector('input');
      label.classList.toggle('selected', !!(input && input.checked));
    }});
  }}
  function restore() {{
    var saved = null;
    try {{ saved = JSON.parse(localStorage.getItem(STORAGE_KEY) || 'null'); }} catch (error) {{}}
    var personal = window.rlPersonalLink || {{}};
    if (saved) {{
      Object.keys(saved).forEach(function(key) {{
        form.querySelectorAll('[name="' + key + '"]').forEach(function(el) {{
          if (el.type === 'radio' || el.type === 'checkbox') el.checked = el.value === saved[key];
          else el.value = saved[key];
        }});
      }});
      show('info', 'Picked up where you left off.');
    }}
    ['name','email','athlete'].forEach(function(key) {{
      var el = document.getElementById(key);
      if (el && personal[key]) el.value = personal[key];
    }});
    if (Object.keys(personal).length) save(true);
    paintChoices(); updateProgress();
  }}
  form.addEventListener('input', function() {{ clearTimeout(saveTimer); saveTimer = setTimeout(function() {{ save(true); }}, 700); paintChoices(); updateProgress(); }});
  form.addEventListener('change', function() {{ paintChoices(); updateProgress(); }});
  document.getElementById('exit-save').addEventListener('click', function() {{ save(false); }});
  window.addEventListener('beforeunload', function() {{ if (!submitted && !form.hidden) save(true); }});
  form.addEventListener('submit', function(event) {{
    event.preventDefault();
    if (form.website.value) {{ show('error', 'Something filled a hidden field. Clear autofill and try again.'); return; }}
    var data = collect();
    var answers = {{}};
    Object.keys(data).forEach(function(key) {{ if (!['name','email','athlete'].includes(key)) answers[key] = data[key]; }});
    submit.disabled = true; submit.textContent = 'Submitting…';
    var draftSaved = save(true);
    var controller = typeof AbortController === 'function' ? new AbortController() : null;
    var timeout = setTimeout(function() {{ if (controller) controller.abort(); }}, 25000);
    fetch('{WORKER_URL}', {{
      method:'POST', headers:{{'Content-Type':'application/json','Accept':'application/json'}},
      body:JSON.stringify({{source:'athlete_exit',brand:'{BRAND}',name:data.name,email:data.email,athlete:data.athlete || '',goal_answers:answers,website:''}}),
      signal:controller ? controller.signal : undefined
    }}).then(function(response) {{
      if (!response.ok) throw new Error('worker failed');
      clearTimeout(timeout); clearTimeout(saveTimer);
      submitted = true;
      try {{ localStorage.removeItem(STORAGE_KEY); }} catch (error) {{}}
      form.hidden = true; message.classList.add('hidden');
      document.getElementById('exit-success').hidden = false;
      document.getElementById('exit-success').scrollIntoView({{behavior:'smooth',block:'start'}});
      if (typeof gtag === 'function') gtag('event','athlete_exit_submitted',{{brand:'{BRAND}'}});
    }}).catch(function() {{
      clearTimeout(timeout); submit.disabled = false; submit.textContent = 'Send It to Matti';
      show('error', draftSaved
        ? 'That did not go through. Your answers are saved in this browser. Try again, or email {CONTACT_EMAIL}.'
        : 'That did not go through, and this browser could not save a draft. Keep this page open and try again, or email {CONTACT_EMAIL}.');
    }});
  }});
  restore();
}})();
</script>"""


def generate_page() -> str:
    return f"""<!DOCTYPE html>
<html lang="en"><head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Before You Go | Roadie Labs</title>
<meta name="description" content="A private exit interview for Roadie Labs coaching athletes.">
<meta name="robots" content="noindex, nofollow"><link rel="canonical" href="https://roadielabs.com/coaching/exit/">
<link rel="icon" type="image/svg+xml" href="/race/assets/rl-logo.svg">
{build_exit_personal_link_js()}{get_preload_hints()}{get_page_css()}{get_ga4_head_snippet()}{build_apply_css()}{build_css()}
</head><body class="rl-neo-brutalist-page" style="background:var(--rl-color-cool-white);color:var(--rl-color-near-black);font-family:var(--rl-font-data);font-size:var(--rl-font-size-sm);line-height:1.7;min-height:100vh">
{get_site_header_html()}
<main class="rl-apply-container">
  <div class="rl-apply-header"><div class="rl-apply-badge">Exit Interview</div><h1>Before You Go</h1>
  <p>Five minutes, less if you&#39;re quick. Apart from your name and email, only the first question is required. I read every one of these myself. It isn&#39;t anonymous, so say it straight. It saves as you go.</p></div>
  <div class="rl-apply-progress" aria-live="polite"><div class="rl-apply-progress-bar"><div class="rl-apply-progress-fill" id="progress-fill"></div></div><div class="rl-apply-progress-text" id="progress-text">0% complete</div></div>
  <div id="message" class="rl-apply-message hidden"></div>
  <form id="exit-form" class="rl-apply-form-card">
    <input type="text" name="website" class="rl-apply-honeypot" tabindex="-1" autocomplete="off">
    {render_sections()}
    <p class="rl-exit-section-sub">That&#39;s everything. Send it when you&#39;re ready.</p>
    <div class="rl-apply-actions"><button type="button" id="exit-save" class="rl-apply-save-btn">Save Progress</button><button type="submit" id="exit-submit" class="rl-apply-submit-btn">Send It to Matti</button></div>
  </form>
  <section id="exit-success" class="rl-exit-success" hidden><h2>Got it.</h2><p>I&#39;ll read every word, and I&#39;ll come back to you on anything you asked for above. A receipt is on its way to your inbox.</p></section>
  <div class="rl-apply-confidential-wrap"><p class="rl-apply-confidential">Your answers come straight to me and are stored in my system. They aren&#39;t anonymous. If you said I can share your words, nothing goes up until you&#39;ve approved the exact wording. Drafts are saved only in this browser until you submit. Questions? Email {CONTACT_EMAIL}</p></div>
</main>
{get_mega_footer_html()}{get_consent_banner_html()}<script>{get_site_header_js()}</script>{build_js()}
</body></html>"""


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate Roadie Labs /coaching/exit/")
    parser.add_argument("--output-dir", default=str(OUTPUT_DIR))
    args = parser.parse_args()
    output = Path(args.output_dir) / "index.html"
    output.parent.mkdir(parents=True, exist_ok=True)
    content = generate_page()
    output.write_text(content, encoding="utf-8")
    print(f"Wrote {output} ({len(content):,} bytes)")


if __name__ == "__main__":
    main()
