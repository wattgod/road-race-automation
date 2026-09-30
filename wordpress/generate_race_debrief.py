#!/usr/bin/env python3
"""
Generate the Roadie Labs race debrief at /race-debrief/.

The road build of Gravel God's race debrief (gravel-race-automation
wordpress/season_review_variants.py RACE_DEBRIEF, rendered by
generate_season_review.py), the same way generate_goals_2027.py is the road
build of the goals page: same questions, Roadie Labs' own tokens and house
rules. It asks everyone who bought a plan (the TrainingPeaks marketplace
plans and the custom plans) how the race went and how the plan held up.

It posts to the shared multi-brand Cloudflare worker (fueling-lead-intake)
with brand=roadielabs and source=plan_debrief. A debrief is not a lead: the
worker and Mission Control strip any lead context, send Matti an alert
tagged [RL], store a consent record, and send the rider one receipt from
road_plan_debrief_v1. No FormSubmit backstop: the worker is the record.

Two optional hidden fields come from the link in the plan's notes: ?plan=
(a TP planId, marketplace notes) and ?ref= (an opaque id, custom-plan
notes). Both stay in the address (they are not personal, and GA4 counts
note clicks per plan from them), and the page, the worker and Mission
Control each accept a value only when the whole of it matches. When ?plan=
is valid, the thank-you screen invites the rider to rate the plan on its
TrainingPeaks page, whatever they answered (no review gating).

House rules that differ from the gravel page: no exclamation marks, no
descriptive subtitles under section headings (gravel's "On the Record" sub
is dropped), flat deadpan register. The copy is the gravel draft with the
brand names swapped; it is DRAFT until Matti has read it.

Usage:
    python wordpress/generate_race_debrief.py
    python wordpress/generate_race_debrief.py --output-dir ./output
"""

import argparse
import html
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from generate_neo_brutalist import SITE_BASE_URL, get_page_css  # noqa: E402
from brand_tokens import get_ga4_head_snippet, get_preload_hints  # noqa: E402
from shared_footer import get_mega_footer_html  # noqa: E402
from shared_header import get_site_header_html, get_site_header_js  # noqa: E402
from cookie_consent import get_consent_banner_html  # noqa: E402
from generate_coaching_apply import build_apply_css, build_progress_bar  # noqa: E402

OUTPUT_DIR = Path(__file__).parent / "output" / "race-debrief"

# The shared multi-brand lead worker (deployed from gravel-race-automation,
# workers/fueling-lead-intake), the same one the goals page posts to. The
# account subdomain is gravelgodCOACHING, not the site's name:
# fueling-lead-intake.gravelgodcycling.workers.dev does not exist.
LEAD_WORKER_URL = "https://fueling-lead-intake.gravelgodcoaching.workers.dev"
LEAD_SOURCE = "plan_debrief"
LEAD_BRAND = "roadielabs"
# The address every Roadie Labs page gives (goals, coaching, apply, legal).
CONTACT_EMAIL = "coach@roadielabs.com"
CANONICAL_URL = f"{SITE_BASE_URL}/race-debrief/"
STORAGE_KEY = "rl_race_debrief_v1"

# The plan's own TrainingPeaks page from its planId alone: resolves for every
# live GG and Roadie plan sampled on 2026-09-29 (23 of 23). Without
# "cycling/" TP shows its plan search instead.
TP_PLAN_URL = "https://www.trainingpeaks.com/training-plans/cycling/tp-"
# Whole-value patterns, the same in the worker and Mission Control.
PLAN_ID_PATTERN = r"^[0-9]{1,12}$"
PLAN_REF_PATTERN = r"^[A-Za-z0-9_-]{8,32}$"
# The worker and Mission Control keep 4000 characters of an answer; stop
# typing there so nothing stored is a quietly cut version of what was written.
MAX_ANSWER_LEN = 4000
# Posted as top-level keys, never as answers.
TOP_LEVEL_NAMES = ("name", "email", "athlete", "plan", "ref")
# A personalised link's ?name=&email=&athlete= come off the address before
# GA4 reads it; ?plan= and ?ref= stay.
PERSONAL_PARAMS = ("name", "email", "athlete")


# ── Question data ────────────────────────────────────────────
# DRAFT COPY: Matti's read pending before deploy (receipts spec §3.7: Matti writes every ask).
# The gravel page's questions (RACE_DEBRIEF), Roadie's house rules applied:
# no section subtitles, no exclamation marks; the site and social channel
# name Roadie Labs. The "On the Record" block is the gravel exit survey's
# approved wording with the coaching words changed for a plan buyer.

BADGE = "Race Debrief"
H1 = "How Did It Go?"
INTRO = ("Five minutes, less if you&#39;re quick. Apart from your name and email, only the first "
         "question is required. I read every one of these myself. It saves as you go.")
DONE = "That&#39;s everything. Send it when you&#39;re ready."
SUBMIT = "Send It to Matti"
SUCCESS = "Got it. I&#39;ll read every word."
TP_RATING = {"before": "If you have a minute, ", "link": "rate the plan on TrainingPeaks",
             "after": ", whatever score you&#39;d give it."}
FOOTER = ("Your answers come straight to me and are stored in my system. If you said I can share your "
          "words, nothing goes up until you&#39;ve approved the exact wording. Drafts are saved only in "
          f"this browser until you submit. Questions? Email {CONTACT_EMAIL}")

SECTIONS = [
    {"title": "You", "fields": [
        {"kind": "pair", "fields": [
            {"name": "name", "label": "Name", "kind": "text", "req": True, "ph": "First Last", "auto": "name"},
            {"name": "email", "label": "Email", "kind": "email", "req": True, "ph": "you@email.com", "auto": "email"},
        ]},
        {"name": "plan", "kind": "hidden", "param": "plan", "pattern": PLAN_ID_PATTERN},
        {"name": "ref", "kind": "hidden", "param": "ref", "pattern": PLAN_REF_PATTERN},
    ]},
    {"title": "Race Day", "fields": [
        {"name": "raced", "label": "Did you race it?", "kind": "radio", "req": True, "layout": "vertical",
         "options": [("finished", "Finished"),
                     ("dnf", "Started, didn&#39;t finish"),
                     ("dns", "Didn&#39;t start"),
                     ("later", "Not yet, it&#39;s still coming")]},
        {"name": "result", "label": "How did it go?", "kind": "text",
         "ph": "Time, placing, or how it felt."},
        {"name": "result_url", "label": "Link to the official results, if there are any", "kind": "text",
         "ph": "The timing company&#39;s page"},
        {"name": "goal_met", "label": "Against the goal you had going in?", "kind": "radio", "layout": "vertical",
         "options": [("hit", "Hit it"), ("close", "Close"), ("missed", "Missed"), ("none", "Didn&#39;t have one")]},
    ]},
    {"title": "The Plan", "fields": [
        {"name": "completion", "label": "How much of the plan did you do?", "kind": "radio", "layout": "vertical",
         "options": [("all", "Nearly all of it"), ("most", "Most of it"), ("half", "About half"),
                     ("less", "Less than half")]},
        {"name": "load", "label": "The training load was", "kind": "radio",
         "options": [("easy", "Too easy"), ("right", "About right"), ("hard", "Too much")]},
        {"name": "fit_week", "label": "Did it fit your week?", "kind": "radio",
         "options": [("yes", "Yes"), ("mostly", "Mostly"), ("no", "Not really")]},
        {"name": "worked", "label": "What worked best?", "kind": "area", "rows": 2},
        {"name": "change_one", "label": "What&#39;s one thing you&#39;d change?", "kind": "area", "rows": 2,
         "ph": "Be blunt. I&#39;d rather hear it from you than guess."},
        {"name": "recommend", "label": "How likely are you to recommend this plan to a rider doing this race?",
         "kind": "scale", "low": "Not likely", "high": "Already have"},
    ]},
    {"title": "On the Record", "fields": [
        {"name": "quote", "label": "If a rider doing this race asked about the plan, what would you tell them?",
         "kind": "area", "rows": 3, "ph": "In your words, the way you&#39;d say it. Good, bad or both."},
        {"name": "not_for", "label": "And who shouldn&#39;t buy it?", "kind": "text",
         "ph": "The rider this plan wouldn&#39;t work for"},
        {"name": "share_as", "label": "Can I share what you wrote above?", "kind": "radio", "layout": "vertical",
         "options": [("full", "Yes, with my full name"),
                     ("initial", "Yes, first name and last initial"),
                     ("age_group", "Yes, first name and age group"),
                     ("private", "No, keep it between us")]},
        {"name": "age_group", "label": "Your age group. It only shows if you picked first name and age group. "
                                       "If you&#39;re under 18, I&#39;ll need a parent&#39;s OK.",
         "kind": "select",
         "options": [("under_18", "Under 18"), ("18_29", "18&ndash;29"), ("30_39", "30&ndash;39"),
                     ("40_49", "40&ndash;49"), ("50_59", "50&ndash;59"), ("60_plus", "60+")]},
        {"name": "share_where", "label": "Where it can appear", "kind": "checks",
         "options": [("where_site", "roadielabs.com"),
                     ("where_social", "Roadie Labs social posts"),
                     ("where_email", "Emails to riders choosing a plan"),
                     ("where_tp", "The plan&#39;s TrainingPeaks page")]},
        {"name": "connection", "label": "Anything connecting us besides the plan? If so, I say so next to your words.",
         "kind": "radio", "layout": "vertical",
         "options": [("none", "No, only the plan"),
                     ("comped", "You gave me the plan free or at a discount"),
                     ("friend", "We&#39;re friends or ride together"),
                     ("work", "We&#39;ve worked together"),
                     ("family", "We&#39;re family")]},
        {"name": "reference", "label": "If someone deciding on this plan wants to talk to a real rider, "
                                       "can I introduce you by email?",
         "kind": "radio", "options": [("yes", "Yes"), ("ask", "Ask me first each time"), ("no", "No")]},
        {"name": "consent_note", "kind": "note",
         "text": "Before anything goes up, I&#39;ll send you the exact words and how they&#39;ll look, and "
                 "nothing runs until you say yes. I won&#39;t edit your words without asking. It stays up for "
                 "three years at most. Reply any time and it comes down within 7 days, though I can&#39;t pull "
                 "back screenshots, reposts or search-engine copies. If you&#39;re under 18, I&#39;ll need a "
                 "parent&#39;s OK too."},
    ]},
    {"title": "What&#39;s Next", "fields": [
        {"name": "next_race", "label": "Next race on the list?", "kind": "text"},
        {"name": "next_want", "label": "What do you want next?", "kind": "radio", "layout": "vertical",
         "options": [("another_plan", "Another plan"), ("custom", "A plan built around me"),
                     ("coaching", "Coaching"), ("break", "A break"), ("unsure", "Not sure yet")]},
        {"name": "last_word", "label": "Anything else?", "kind": "area", "rows": 3, "ph": "Last word&#39;s yours."},
    ]},
]


# ── Field rendering ───────────────────────────────────────────

def _attr(value: str) -> str:
    return html.escape(value, quote=True)


def _strip_tags(s: str) -> str:
    return re.sub(r"<[^>]+>", "", s)


def _req(field) -> str:
    return ' <span class="rl-apply-required">*</span>' if field.get("req") else ""


def _label(field, for_id: bool = True) -> str:
    if not field.get("label"):
        return ""
    target = f' for="{field["name"]}"' if for_id else ""
    # a scale is a radiogroup: it names itself by pointing at this label
    ident = f' id="{field["name"]}-q"' if field["kind"] == "scale" else ""
    return f'<label class="rl-apply-label"{ident}{target}>{field["label"]}{_req(field)}</label>'


SCALE = range(0, 11)
MAXLENGTH_ATTR = f' maxlength="{MAX_ANSWER_LEN}"'


def _scale(field) -> str:
    """0-10 in one row. Real radios (visually hidden, still focusable), so
    Tab reaches the group and the arrow keys move along it."""
    name = field["name"]
    low, high = field.get("low", ""), field.get("high", "")
    end_label = {SCALE[0]: low, SCALE[-1]: high}
    opts = []
    for n in SCALE:
        spoken = f"{n} ({html.unescape(end_label[n])})" if end_label.get(n) else str(n)
        opts.append(
            f'<label class="rl-apply-radio-option rl-debrief-scale-option">'
            f'<input type="radio" name="{name}" value="{n}" aria-label="{_attr(spoken)}">'
            f'<span class="rl-debrief-scale-n" aria-hidden="true">{n}</span></label>'
        )
    ends = (f'<div class="rl-debrief-scale-ends" aria-hidden="true"><span>{low}</span><span>{high}</span></div>'
            if low or high else "")
    return (f'<div class="rl-debrief-scale" role="radiogroup" aria-labelledby="{name}-q" data-radio="{name}">'
            f'<div class="rl-debrief-scale-row">{"".join(opts)}</div>{ends}</div>')


def _control(field) -> str:
    name, kind = field["name"], field["kind"]
    req = " required" if field.get("req") else ""
    ph = f' placeholder="{field["ph"]}"' if field.get("ph") else ""
    if kind in ("text", "email"):
        auto = f' autocomplete="{field["auto"]}"' if field.get("auto") else ""
        cap = MAXLENGTH_ATTR if kind == "text" else ""
        return f'<input type="{kind}" id="{name}" name="{name}"{req}{ph}{auto}{cap}>'
    if kind == "area":
        return f'<textarea id="{name}" name="{name}" rows="{field.get("rows", 3)}"{req}{ph}{MAXLENGTH_ATTR}></textarea>'
    if kind == "select":
        opts = '<option value="">Select...</option>' + "".join(
            f'<option value="{_attr(v)}">{t}</option>' for v, t in field["options"]
        )
        return f'<select id="{name}" name="{name}"{req}>{opts}</select>'
    if kind == "radio":
        opts = "".join(
            f'<label class="rl-apply-radio-option"><input type="radio" name="{name}" value="{o[0]}"'
            f'{req if i == 0 else ""}><div class="rl-apply-radio-label"><div class="rl-apply-radio-title">{o[1]}</div>'
            "</div></label>"
            for i, o in enumerate(field["options"])
        )
        layout = "" if field.get("layout") == "vertical" else " rl-apply-radio-horizontal"
        return f'<div class="rl-apply-radio-group{layout}" data-radio="{name}">{opts}</div>'
    if kind == "scale":
        return _scale(field)
    if kind == "checks":
        opts = "".join(
            f'<label class="rl-apply-checkbox-option"><input type="checkbox" name="{n}" value="yes">'
            f'<span class="rl-apply-checkbox-label">{t}</span></label>'
            for n, t in field["options"]
        )
        return f'<div class="rl-apply-checkbox-vertical">{opts}</div>'
    if kind == "hidden":
        # filled from that URL param by the page script, only on a whole match
        return (f'<input type="hidden" id="{name}" name="{name}" data-param="{_attr(field["param"])}" '
                f'data-pattern="{_attr(field["pattern"])}">')
    raise ValueError(f"unknown field kind {kind!r}")


def render_field(field, context_title: str = "") -> str:
    if field["kind"] == "hidden":
        return _control(field)
    if field["kind"] == "note":
        # explanation, not a question: no input and no data-q
        return f'<p class="rl-debrief-note">{field["text"]}</p>'
    if field["kind"] == "pair":
        inner = "".join(render_field(f, context_title) for f in field["fields"])
        return f'<div class="rl-apply-inline">{inner}</div>'
    q = field.get("label") or context_title
    head = _label(field, for_id=field["kind"] not in ("radio", "checks", "scale"))
    return (f'<div class="rl-apply-group" data-q="{_attr(html.unescape(_strip_tags(q)))}">'
            f"{head}{_control(field)}</div>")


def render_sections() -> str:
    out = []
    for n, sec in enumerate(SECTIONS, start=1):
        fields = "".join(render_field(f, sec["title"]) for f in sec["fields"])
        # No `sub` line under a section title (house rule).
        out.append(f'<div data-section-n="{n}" class="rl-apply-section-title">{n}. {sec["title"]}</div>\n      {fields}')
    return "\n      ".join(out)


def _input_names(field) -> list[str]:
    kind = field["kind"]
    if kind == "pair":
        return [n for f in field["fields"] for n in _input_names(f)]
    if kind == "checks":
        return [key for key, _ in field["options"]]
    if kind == "note":
        return []
    return [field["name"]]


def input_names() -> list[str]:
    return [n for sec in SECTIONS for f in sec["fields"] for n in _input_names(f)]


def answer_keys() -> list[str]:
    """The goal_answers keys a full submission can carry."""
    return [n for n in input_names() if n not in TOP_LEVEL_NAMES]


def check_unique_names() -> None:
    """Two inputs with one name post one value and lose the other, silently."""
    names = input_names()
    dupes = sorted({n for n in names if names.count(n) > 1})
    if dupes:
        raise ValueError(f"race debrief reuses input names: {dupes}")


# ── Page pieces ───────────────────────────────────────────────

def build_header() -> str:
    return f'''<div class="rl-apply-header">
    <div class="rl-apply-badge">{BADGE}</div>
    <h1>{H1}</h1>
    <p>{INTRO}</p>
  </div>'''


def build_tp_rating() -> str:
    """Hidden until a stored submission with a valid ?plan=; the page script
    points the link at that plan's TrainingPeaks page."""
    return (f'<p id="tp-rating" class="rl-debrief-rating" hidden>{TP_RATING["before"]}'
            f'<a id="tp-rating-link" href="https://www.trainingpeaks.com/training-plans/" target="_blank" rel="noopener">'
            f'{TP_RATING["link"]}</a>{TP_RATING["after"]}</p>')


def build_submit_buttons() -> str:
    return f'''<p class="rl-debrief-done">{DONE}</p><div class="rl-apply-actions">
        <button type="button" class="rl-apply-save-btn rl-debrief-save">Save Progress</button>
        <button type="submit" class="rl-apply-submit-btn rl-debrief-submit" id="debrief-submit">{SUBMIT}</button>
      </div>'''


def build_footer() -> str:
    return f'''<div class="rl-apply-confidential-wrap">
    <p class="rl-apply-confidential">{FOOTER} &middot; <a href="/privacy/">Privacy Policy</a></p>
  </div>
  ''' + get_mega_footer_html()


# ── CSS ──────────────────────────────────────────────────────

def build_debrief_css() -> str:
    return '''<style>
.rl-debrief-done {
  font-family: var(--rl-font-editorial);
  font-size: var(--rl-font-size-sm);
  color: var(--rl-color-secondary-blue);
  margin: var(--rl-spacing-xl) 0 0;
}
.rl-debrief-rating {
  font-family: var(--rl-font-editorial);
  font-size: var(--rl-font-size-sm);
  margin: 0 0 var(--rl-spacing-lg);
}
/* A note: explanation between questions, no input */
.rl-debrief-note {
  font-family: var(--rl-font-editorial);
  font-size: var(--rl-font-size-xs);
  line-height: var(--rl-line-height-relaxed);
  color: var(--rl-color-secondary-blue);
  border-left: 3px solid var(--rl-color-silver);
  padding-left: var(--rl-spacing-md);
  margin: 0 0 var(--rl-spacing-lg);
}
/* A 0-10 scale: eleven buttons in one row, down to a 390px phone. The
   buttons share borders instead of a gap, which keeps each one wider than
   24px (WCAG 2.5.8) at that width. */
.rl-debrief-scale-row { display: flex; }
.rl-apply-radio-option.rl-debrief-scale-option {
  position: relative;
  flex: 1 1 0;
  min-width: 0;
  padding: 0;
  gap: 0;
  align-items: stretch;
}
.rl-apply-radio-option.rl-debrief-scale-option + .rl-debrief-scale-option { margin-left: -2px; }
.rl-apply-radio-option.rl-debrief-scale-option.selected,
.rl-debrief-scale-option:focus-within { z-index: 1; }
.rl-debrief-scale-option input {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  margin: 0;
  opacity: 0;
  cursor: pointer;
}
.rl-debrief-scale-n {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 44px;
  font-family: var(--rl-font-data);
  font-size: var(--rl-font-size-sm);
  font-weight: var(--rl-font-weight-bold);
  font-variant-numeric: tabular-nums;
}
.rl-debrief-scale-option input:checked + .rl-debrief-scale-n {
  background: var(--rl-color-near-black);
  color: var(--rl-color-white);
}
.rl-debrief-scale-option input:focus-visible + .rl-debrief-scale-n {
  outline: 3px solid var(--rl-color-signal-red);
  outline-offset: -3px;
}
.rl-debrief-scale-ends {
  display: flex;
  justify-content: space-between;
  gap: var(--rl-spacing-md);
  margin-top: var(--rl-spacing-xs);
  font-family: var(--rl-font-data);
  font-size: var(--rl-font-size-2xs);
  color: var(--rl-color-secondary-blue);
}
.rl-debrief-scale-ends span:last-child { text-align: right; }
@media (max-width: 600px) {
  .rl-apply-actions { flex-direction: column-reverse; align-items: stretch; gap: var(--rl-spacing-sm); }
  .rl-apply-save-btn { margin-right: 0; }
}
</style>'''


# ── JavaScript ────────────────────────────────────────────────

def build_personal_link_js() -> str:
    """Runs first in <head>, before the GA snippet: keeps ?name=&email=&athlete=
    for the prefill and removes only those three from the address, so GA4's
    page_location never carries them. ?plan=, ?ref=, utm_* and the hash stay."""
    keys = ", ".join(f'"{k}"' for k in PERSONAL_PARAMS)
    return r'''<script>
(function() {
  var KEYS = [__KEYS__], found = {}, kept = [], removed = false;
  try {
    var params = new URLSearchParams(window.location.search);
    window.location.search.replace(/^\?/, "").split("&").forEach(function(part) {
      if (!part) { return; }
      var raw = part.split("=")[0], key = raw;
      try { key = decodeURIComponent(raw.replace(/\+/g, " ")); } catch (e) { /* keep raw */ }
      if (KEYS.indexOf(key) === -1) { kept.push(part); return; }
      removed = true;
      if (!(key in found)) { found[key] = params.get(key) || ""; }
    });
    if (removed) {
      history.replaceState(history.state, "",
        window.location.pathname + (kept.length ? "?" + kept.join("&") : "") + window.location.hash);
    }
  } catch (e) { /* a browser this old keeps the link as it came */ }
  window.rlPersonalLink = found;
})();
</script>'''.replace("__KEYS__", keys)


def build_debrief_js() -> str:
    js = r'''<script>
(function() {
  "use strict";

  var STORAGE_KEY = "__STORAGE_KEY__";
  var SUCCESS = "__SUCCESS__";
  var SUBMIT_LABEL = "__SUBMIT_LABEL__";
  var TOP_LEVEL = __TOP_LEVEL__;
  var TP_PLAN_URL = "__TP_PLAN_URL__";

  var form = document.getElementById("debrief-form");

  /* ?plan= and ?ref= from the plan's notes: used only when the whole value
     matches the field's pattern (the worker and Mission Control check again).
     They stay in the address; GA4 counts note clicks per plan from them. */
  var URL_FIELDS = Array.prototype.slice.call(form.querySelectorAll("input[data-param]"));
  function matches(el, value) {
    try { return new RegExp(el.getAttribute("data-pattern")).test(value); } catch (e) { return false; }
  }
  function fillFromAddress() {
    var params = null;
    try { params = new URLSearchParams(window.location.search); } catch (e) { return; }
    /* A link that names a plan or a ref sets the whole context: a draft
       saved from another plan's link must not carry that plan over. Only a
       bare address (a resumed draft) keeps the draft's own values. */
    var fromLink = URL_FIELDS.some(function(el) { return params.has(el.getAttribute("data-param")); });
    URL_FIELDS.forEach(function(el) {
      var v = params.get(el.getAttribute("data-param")) || "";
      if (v && matches(el, v)) { el.value = v; }
      else if (fromLink || (el.value && !matches(el, el.value))) { el.value = ""; }
    });
  }
  /* Whether each one is there, never its value: has_plan / has_ref. */
  function withPresence(params) {
    URL_FIELDS.forEach(function(el) { params["has_" + el.name] = el.value ? "yes" : "no"; });
    return params;
  }
  function ga4(name, params) {
    if (typeof gtag === "function") { gtag("event", name, params || {}); }
  }

  /* ── Radio and checkbox styling ─────────────────── */
  function radioChanged(input) {
    form.querySelectorAll("input[name=\"" + input.name + "\"]").forEach(function(inp) {
      inp.closest(".rl-apply-radio-option").classList.toggle("selected", inp.checked);
    });
  }
  form.addEventListener("click", function(e) {
    var t = e.target;
    var box = t.closest(".rl-apply-checkbox-option");
    if (box) {
      var cb = box.querySelector("input");
      if (t !== cb) { cb.checked = !cb.checked; e.preventDefault(); }
      box.classList.toggle("selected", cb.checked);
      queueSave();
      return;
    }
    var opt = t.closest(".rl-apply-radio-option");
    if (opt) {
      var input = opt.querySelector("input");
      input.checked = true;
      radioChanged(input);
      queueSave();
      updateProgress();
    }
  });

  var started = false;
  function onEdit(e) {
    if (!started) { started = true; ga4("debrief_start", withPresence({ variant: "race_debrief" })); }
    if (e && e.target.type === "radio" && e.target.checked) { radioChanged(e.target); }
    queueSave();
    updateProgress();
  }
  form.addEventListener("input", onEdit);
  form.addEventListener("change", onEdit);

  /* ── Progress ────────────────────────────────────── */
  function updateProgress() {
    var names = {};
    form.querySelectorAll("[required]").forEach(function(el) { names[el.name] = true; });
    var keys = Object.keys(names);
    var filled = keys.filter(function(n) {
      var el = form.querySelector("[name=\"" + n + "\"]");
      if (el.type === "radio") { return !!form.querySelector("input[name=\"" + n + "\"]:checked"); }
      return !!el.value.trim();
    }).length;
    var pct = keys.length ? Math.round(filled / keys.length * 100) : 0;
    document.getElementById("progress-fill").style.width = pct + "%";
    document.getElementById("progress-text").textContent = pct + "% complete";
  }

  /* ── Collect ─────────────────────────────────────── */
  function collect() {
    var data = {};
    new FormData(form).forEach(function(value, key) {
      if (key === "website") { return; }
      if (String(value).trim()) { data[key] = String(value).trim(); }
    });
    return data;
  }

  /* ── Save / restore ──────────────────────────────── */
  var submitted = false;
  var saveTimer = null;
  var saveOk = true;
  var saveWarned = false;
  function save(silent) {
    if (submitted) { return; }
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(collect()));
      saveOk = true;
      if (!silent) { showMessage("info", "Saved in this browser. Close the page and come back any time."); }
    } catch (err) {
      saveOk = false;
      if (!silent || !saveWarned) {
        saveWarned = true;
        showMessage("error", "This browser won't let me save. Keep the page open until you submit.");
      }
    }
  }
  function queueSave() {
    clearTimeout(saveTimer);
    saveTimer = setTimeout(function() { save(true); }, 800);
  }

  function restore() {
    var saved = null;
    try { saved = JSON.parse(localStorage.getItem(STORAGE_KEY) || "null"); } catch (err) { saved = null; }
    if (saved) {
      Object.keys(saved).forEach(function(key) {
        form.querySelectorAll("[name=\"" + key + "\"]").forEach(function(el) {
          if (el.type === "checkbox") {
            el.checked = saved[key] === el.value;
            el.closest(".rl-apply-checkbox-option").classList.toggle("selected", el.checked);
          } else if (el.type === "radio") {
            if (el.value === saved[key]) { el.checked = true; radioChanged(el); }
          } else {
            el.value = saved[key];
          }
        });
      });
      showMessage("info", "Picked up where you left off.");
    }
    /* personalised links: read (and taken out of the address) by the head
       script before analytics loaded */
    var prefill = window.rlPersonalLink || {};
    ["name", "email"].forEach(function(k) {
      var el = document.getElementById(k);
      if (el && prefill[k] && !el.value) { el.value = prefill[k]; }
    });
    if (prefill.name || prefill.email) { save(true); }
    /* ?plan= / ?ref= win over a restored draft */
    fillFromAddress();
    updateProgress();
  }

  form.querySelectorAll(".rl-debrief-save").forEach(function(b) {
    b.addEventListener("click", function() { save(false); });
  });
  window.addEventListener("beforeunload", function() { save(true); });

  /* ── Submit: the worker is the record, no email backstop ── */
  function setButtons(disabled, label) {
    form.querySelectorAll(".rl-debrief-submit").forEach(function(b) { b.disabled = disabled; b.textContent = label; });
  }

  /* Every marketplace buyer sees this, whatever they answered: a rating ask
     gated on a good score would be review gating (receipts spec §5.6). */
  function showRating(d) {
    var rating = document.getElementById("tp-rating");
    var plan = form.querySelector("input[name=\"plan\"][data-pattern]");
    if (!rating || !plan || !d.plan || !matches(plan, d.plan)) { return; }
    document.getElementById("tp-rating-link").href = TP_PLAN_URL + d.plan;
    rating.hidden = false;
  }

  form.addEventListener("submit", function(e) {
    e.preventDefault();
    if (form.querySelector(".rl-debrief-submit").disabled) { return; }
    if (form.querySelector("[name=website]").value) {
      showMessage("error", "Something filled a hidden field. Clear your browser's autofill for this page and try again.");
      return;
    }
    var d = collect();
    setButtons(true, "Submitting...");
    save(true);

    var ctrl = typeof AbortController === "function" ? new AbortController() : null;
    var killer = setTimeout(function() { if (ctrl) { ctrl.abort(); } }, 25000);

    var answers = {};
    Object.keys(d).forEach(function(k) {
      if (TOP_LEVEL.indexOf(k) === -1 && typeof d[k] === "string") { answers[k] = d[k]; }
    });
    var body = { source: "__LEAD_SOURCE__", brand: "__LEAD_BRAND__", email: d.email, name: d.name || "",
                 goal_answers: answers, website: "" };
    URL_FIELDS.forEach(function(el) { if (d[el.name]) { body[el.name] = d[el.name]; } });
    fetch("__LEAD_WORKER_URL__", {
      method: "POST",
      headers: { "Content-Type": "application/json", "Accept": "application/json" },
      body: JSON.stringify(body),
      signal: ctrl ? ctrl.signal : undefined
    }).then(function(r) {
      return r.json().then(function() { return r.ok; }).catch(function() { return r.ok; });
    }).catch(function() { return false; })
      .then(function(ok) {
        clearTimeout(killer);
        if (!ok) { throw new Error("worker transport failed"); }
        submitted = true;
        clearTimeout(saveTimer);
        try { localStorage.removeItem(STORAGE_KEY); } catch (err) { /* ignore */ }
        ga4("debrief_submit", withPresence({ variant: "race_debrief" }));
        showMessage("success", SUCCESS);
        showRating(d);
        setButtons(true, "Submitted");
      })
      .catch(function() {
        clearTimeout(killer);
        showMessage("error", saveOk
          ? "That didn't go through. Your answers are saved in this browser. Try again, or email __CONTACT_EMAIL__."
          : "That didn't go through, and this browser can't save. Keep this page open and try again, or email __CONTACT_EMAIL__.");
        setButtons(false, SUBMIT_LABEL);
      });
  });

  function showMessage(type, text) {
    var m = document.getElementById("message");
    m.className = "rl-apply-message " + type;
    m.textContent = text;
    m.classList.remove("hidden");
    m.scrollIntoView({ behavior: "smooth", block: "center" });
  }

  restore();
})();
</script>'''
    js_str = lambda s: html.unescape(s).replace("\\", "\\\\").replace('"', '\\"')
    return (
        js.replace("__STORAGE_KEY__", STORAGE_KEY)
        .replace("__SUCCESS__", js_str(SUCCESS))
        .replace("__SUBMIT_LABEL__", js_str(SUBMIT))
        .replace("__TOP_LEVEL__", json.dumps(list(TOP_LEVEL_NAMES)))
        .replace("__TP_PLAN_URL__", TP_PLAN_URL)
        .replace("__LEAD_WORKER_URL__", LEAD_WORKER_URL)
        .replace("__LEAD_SOURCE__", LEAD_SOURCE)
        .replace("__LEAD_BRAND__", LEAD_BRAND)
        .replace("__CONTACT_EMAIL__", CONTACT_EMAIL)
    )


# ── Page assembly ─────────────────────────────────────────────

def generate_race_debrief_page(external_assets: dict = None) -> str:
    check_unique_names()
    page_css = external_assets["css_tag"] if external_assets else get_page_css()
    title = "How Did It Go? | Roadie Labs"
    return f'''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  {build_personal_link_js()}
  <title>{title}</title>
  <meta name="robots" content="noindex, nofollow">
  <link rel="canonical" href="{CANONICAL_URL}">
  <meta property="og:title" content="{title}">
  <meta property="og:type" content="website">
  <meta property="og:url" content="{CANONICAL_URL}">
  <meta property="og:site_name" content="Roadie Labs">
  <link rel="icon" type="image/svg+xml" href="/race/assets/rl-logo.svg">
  {get_preload_hints()}
  {page_css}
  <!-- GA4 -->
  {get_ga4_head_snippet()}
  {build_apply_css()}
  {build_debrief_css()}
</head>
<body class="rl-neo-brutalist-page" style="background:var(--rl-color-cool-white);color:var(--rl-color-near-black);font-family:var(--rl-font-data);font-size:var(--rl-font-size-sm);line-height:1.7;min-height:100vh">
  {get_site_header_html()}
  <div class="rl-apply-container">
    {build_header()}
    {build_progress_bar()}
    <div id="message" class="rl-apply-message hidden"></div>
    {build_tp_rating()}
    <form id="debrief-form" class="rl-apply-form-card">
      <input type="text" name="website" class="rl-apply-honeypot" tabindex="-1" autocomplete="off">
      {render_sections()}
      {build_submit_buttons()}
    </form>
  </div>
  {build_footer()}
  {get_consent_banner_html()}
  <script>{get_site_header_js()}</script>
  {build_debrief_js()}
</body>
</html>'''


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", default=str(OUTPUT_DIR))
    args = parser.parse_args()

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    html_content = generate_race_debrief_page()
    (out_dir / "index.html").write_text(html_content, encoding="utf-8")
    print(f"Wrote {out_dir / 'index.html'} ({len(html_content):,} bytes)")


if __name__ == "__main__":
    main()
