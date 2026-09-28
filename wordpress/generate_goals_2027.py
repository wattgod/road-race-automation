#!/usr/bin/env python3
"""
Generate the Roadie Labs 2027 Goals page at /goals/.

The road build of Gravel God's "2027 goals funnel" (gravel-race-automation
wordpress/generate_season_review.py + season_review_variants.py, variant
goal_2027; docs/specs/goals-2027-funnel-spec.md D13). Same structure and the
same shared question blocks (WOOP: one measurable goal, a named inner
obstacle with an if-then plan, one daily habit) as the gravel page, in
Roadie Labs' own brand tokens and voice — road racing, gran fondos, crits,
sportives, time trials, club rides, climbs. No FTP or other training-number
questions (those come from data, never a form).

A stranger's answers, not a coached athlete's: this is the public lead
magnet, not the coaching intake (/coaching/apply/). It posts to the shared
multi-brand Cloudflare worker (fueling-lead-intake) with brand=roadielabs
and source=goal_2027; Mission Control stores the answers, renders the paper
poster (mission_control/services/goal_poster.py, brand-aware as of the road
build) and emails it, then a single check-in a week later
(road_goal_2027_v1). No email backstop and no FormSubmit here — the worker
is the record (goals-2027-funnel-spec.md D8).

House rules that differ from the gravel page: no exclamation marks, no
descriptive subtitles under section headings (the `sub` field gravel's
version sets on 3 of its 6 sections is dropped here), flat deadpan register.

The offer beneath the results is Race Plan only — Roadie Labs has no Season
Plan product (that's a Gravel God-only ruling, D2/D15). No dead links: the
Race Plan CTA goes to the real, working /questionnaire/ checkout
(web/training-plans-form.js posts to the shared Motoren pipeline's
/api/create-checkout, same $15/week $249-cap pricing as gravel).

Usage:
    python wordpress/generate_goals_2027.py
    python wordpress/generate_goals_2027.py --output-dir ./output
"""

import argparse
import html
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from generate_neo_brutalist import SITE_BASE_URL, _safe_json_for_script, get_page_css  # noqa: E402
from brand_tokens import COLORS, get_ga4_head_snippet, get_preload_hints  # noqa: E402
from shared_footer import get_mega_footer_html  # noqa: E402
from shared_header import get_site_header_html, get_site_header_js  # noqa: E402
from cookie_consent import get_consent_banner_html  # noqa: E402
from generate_coaching_apply import build_apply_css, build_progress_bar  # noqa: E402

OUTPUT_DIR = Path(__file__).parent / "output" / "goals"

# The shared multi-brand lead worker (deployed from gravel-race-automation,
# workers/fueling-lead-intake). Roadie Labs pages post here too — see
# generate_quiz.py's WORKER_URL for the existing precedent in this repo.
LEAD_WORKER_URL = "https://fueling-lead-intake.gravelgodcoaching.workers.dev"
LEAD_SOURCE = "goal_2027"
LEAD_BRAND = "roadielabs"
CONTACT_EMAIL = "coach@roadielabs.com"

SEASON = 2026
NEXT = SEASON + 1
CANONICAL_URL = f"{SITE_BASE_URL}/goals/"


# ── Question data ────────────────────────────────────────────
# Field kinds: text, email, date, area (textarea), select, radio, checks,
# whychain (five whys), pair (two fields side by side), timed (textarea with
# a countdown, used only in the deep-dive modules), hidden.
# Optional keys: req, ph, rows, options, minutes, swap (start/stop prompt
# swap keyed off habit_direction), lift (a radio value that makes other
# fields optional).

AREAS = [
    ("endurance", "Endurance / late-race durability"),
    ("climbing", "Climbing"),
    ("top_end", "Top end / surges"),
    ("fueling", "Fueling & hydration"),
    ("skills", "Bike handling & skills"),
    ("strength", "Strength & mobility"),
    ("body_comp", "Body composition"),
    ("recovery", "Sleep & recovery"),
    ("consistency", "Consistency"),
    ("mental", "Head game / pacing"),
    ("other", "Something else"),
]

# Verbatim from the Self Authoring Present Authoring lists (same source
# gravel's version uses — these are personality traits, not cycling facts).
STRENGTHS = [
    "Do what I say I am going to do",
    "Make plans and stick to them",
    "Am very goal-oriented",
    "Have seen my tendency for hard work pay off",
    "Am always learning new things",
    "Am not bothered when things don't go according to plan",
    "Calm down quickly when I do get upset",
    "Am rarely or never stopped from doing what I want by my fears",
    "Watch what I eat carefully",
    "Am comfortable alone",
    "Enjoy time in natural surroundings",
    "Make other people laugh and have fun",
]
FAULTS = [
    "Am too perfectionistic",
    "Feel that I am being unproductive if I relax",
    "Seriously dislike having my routine or schedule upset",
    "Often procrastinate",
    "Frequently make excuses",
    "Have no stable daily routine for sleeping or eating",
    "Pursue too many activities at the same time",
    "May spend too much time pursuing fun and excitement",
    "Am often too optimistic",
    "Often take counterproductive or unnecessary risks",
    "Compare myself unfavorably to other people",
    "Let my fears stop me from doing things I want to do",
    "Get stressed out easily",
    "Cannot negotiate for myself very well",
]

DEAD_HABIT_REASONS = [
    ("dead_obvious", "No set time or place"),
    ("dead_attractive", "Nothing in it I looked forward to"),
    ("dead_easy", "Too much hassle to start"),
    ("dead_satisfying", "Couldn't see it working"),
]

HABIT_SWAP_FIELDS = [
    {"name": "habit_direction", "label": "Will you start or stop a habit?", "kind": "radio", "req": True,
     "options": [("do", "Start"), ("reduce", "Stop")]},
    {"name": "habit", "label": "What will you do every day?", "kind": "text", "req": True,
     "swap": {"do": {"label": "What will you do every day?", "ph": "e.g., 10 minutes of hip mobility"},
              "reduce": {"label": "What will you stop doing?", "ph": "e.g., Phone in the bedroom"}}},
    {"name": "habit_when", "label": "When and where will it happen?", "kind": "text", "req": True,
     "swap": {"do": {"label": "When and where will it happen?", "ph": "e.g., After I close the laptop, on the mat by the trainer"},
              "reduce": {"label": "What will you change so it doesn't happen?", "ph": "e.g., Charger lives in the kitchen"}}},
    {"name": "habit_min", "label": "What is the smallest version that counts?", "kind": "text", "req": True,
     "swap": {"do": {"label": "What is the smallest version that counts?", "ph": "e.g., One stretch"},
              "reduce": {"label": "What will you do instead?", "ph": "e.g., Read the book on the nightstand"}}},
]

SECTIONS = [
    {"title": "You", "fields": [{"kind": "pair", "fields": [
        {"name": "name", "label": "Name", "kind": "text", "req": True, "ph": "First Last", "auto": "name"},
        {"name": "email", "label": "Email", "kind": "email", "req": True, "ph": "you@email.com", "auto": "email"},
    ]}]},
    {"title": "The Highlight Reel", "fields": [
        {"name": "proudest", "label": f"What are you proudest of from {SEASON}?", "kind": "area", "req": True, "rows": 3},
        {"name": "last_goal", "label": "What did you say you&#39;d do this year?", "kind": "text", "req": True,
         "ph": "The goal you wrote down in January, not the one you&#39;ve since decided you meant"},
        {"name": "last_goal_result", "label": "And?", "kind": "radio", "req": True,
         "options": [("hit", "Nailed it"), ("close", "Close"), ("missed", "Missed"), ("dropped", "Quietly abandoned"), ("none", "Never set one")],
         "lift": {"when": "none", "fields": ["last_goal", "last_goal_why"]}},
        {"name": "last_goal_why", "label": "What decided it?", "kind": "text", "req": True, "ph": "A puncture only explains so much"},
    ]},
    {"title": "The Blooper Reel", "fields": [
        {"name": "hardest", "label": "Worst moment of the season. How much of it was on you?", "kind": "area", "req": True, "rows": 3,
         "ph": "Some of it, probably. That&#39;s the good news. It means you can fix it."},
        {"name": "missed_workout", "label": "When you miss a planned workout, you&hellip;", "kind": "radio", "req": True,
         "options": [("make_up", "Make it up", "Even if it wrecks the next two days"),
                     ("move_on", "Move on", "One workout won&#39;t matter"),
                     ("guilt", "Feel guilty", "Beat myself up, eventually let it go"),
                     ("spiral", "Spiral", "Start questioning the whole plan"),
                     ("disappear", "Quietly disappear", "Go dark for a week and hope nobody notices")]},
        {"name": "competing_wants", "label": "What do you love that&#39;s quietly making you slower?", "kind": "text", "req": True,
         "ph": "Mine&#39;s the post-ride party. Two days wrecked, twenty times a year. Do the math."},
    ]},
    {"title": f"{NEXT}", "fields": [
        {"name": "outcome_goal", "label": f"By the end of {NEXT}, I will&hellip;", "kind": "text", "req": True,
         "ph": "e.g., Finish Maratona dles Dolomites under 8 hours. Measurable. If it can&#39;t fail, it&#39;s not a goal, it&#39;s a vibe."},
        {"name": "outcome_measure", "label": "How will we know you did it?", "kind": "text", "req": True},
        {"name": "outcome_scary", "label": "Say it out loud. Does it scare you?", "kind": "radio",
         "options": [("yes", "Yes"), ("a_bit", "A little"), ("no", "No (so make it bigger)")]},
        {"name": "not_yet", "label": "So why haven&#39;t you done it yet?", "kind": "text", "req": True, "ph": "Not the excuse. The reason."},
        {"name": "outcome_why", "label": "Why do you want it? The real answer, not the Strava caption.", "kind": "whychain", "req": True},
        {"name": "goal_audience", "label": "Who knows about this goal?", "kind": "radio", "req": True,
         "options": [("public", "Everyone", "I posted it"), ("friends", "Friends and family"),
                     ("coach", "Just me and you"), ("nobody", "Nobody yet", "Including, until now, me")]},
        {"kind": "pair", "fields": [
            {"name": "a_race", "label": "The race it all points at", "kind": "text", "ph": "e.g., Maratona dles Dolomites"},
            {"name": "a_race_date", "label": "Date", "kind": "date"},
        ]},
    ]},
    {"title": "Your Biggest Obstacle Is You", "fields": [
        {"name": "inner_obstacle", "label": "What in you is most likely to screw this up?", "kind": "text", "req": True,
         "ph": "e.g., I skip the Tuesday club ride after a bad week at work"},
        {"name": "obstacle_plan", "label": "When that shows up, you&#39;ll&hellip;", "kind": "text", "req": True,
         "ph": "Specific. &ldquo;Try harder&rdquo; isn&#39;t a plan."},
    ]},
    {"title": "What Would A Fast Rider Do?", "fields": [
        {"name": "area", "label": "What&#39;s the one thing that most needs to get better?", "kind": "select", "req": True, "options": AREAS},
        *[dict(f) for f in HABIT_SWAP_FIELDS[:3]],
        {"name": "habit_min", "label": "The smallest version that still counts", "kind": "text", "req": True,
         "swap": {"do": {"label": "The smallest version that still counts", "ph": "The one you&#39;ll still do on your worst Tuesday"},
                  "reduce": {"label": "What you&#39;ll do instead", "ph": "e.g., Read the book on the nightstand like an adult"}}},
        {"name": "habit_2", "label": "A second daily habit, and when (optional)", "kind": "text",
         "ph": "e.g., Lights out by 10, phone charging in the kitchen"},
    ]},
]

MODULES = [
    {"key": "ideal", "title": "The season you want", "minutes": "15 min", "fields": [
        {"name": "ideal_season", "kind": "timed", "minutes": 15, "rows": 12,
         "label": f"It&#39;s December {NEXT} and it went perfectly. Write it like a race report: where, who, how it felt. Don&#39;t stop to edit."}]},
    {"key": "avoid", "title": "The season you&#39;re scared of", "minutes": "5 min", "fields": [
        {"name": "avoid_season", "kind": "timed", "minutes": 5, "rows": 7,
         "label": f"Now the other one. December {NEXT}, it went sideways. What happened, and what was your part?"}]},
    {"key": "best", "title": "Your best stretch ever", "minutes": "3 min", "fields": [
        {"name": "best_block", "label": "Describe the best stretch of training you&#39;ve ever had. What made it work?", "kind": "area", "rows": 3,
         "ph": "Those are your success conditions. We&#39;re going to rebuild them on purpose."}]},
    {"key": "quit", "title": "What would make you quit", "minutes": "2 min", "fields": [
        {"name": "quit_triggers", "label": "What would make you quit, or quietly stop caring?", "kind": "area", "rows": 2}]},
    {"key": "traits", "title": "Your faults, itemized", "minutes": "5 min", "fields": [
        {"name": "fault", "label": "Pick the one that cost you most", "kind": "select", "options": [(t, t) for t in FAULTS]},
        {"name": "fault_when", "label": "When did it bite you?", "kind": "area", "rows": 2},
        {"name": "strength", "label": "Fine, and the one that carried you", "kind": "select", "options": [(t, t) for t in STRENGTHS]}]},
    {"key": "dead_habit", "title": "The habit that died", "minutes": "2 min", "fields": [
        {"name": "dead_habit", "label": "One you swore you&#39;d keep this year", "kind": "text", "ph": "e.g., Mobility after every ride (lol)"},
        {"name": "dead_reasons", "label": "Cause of death", "kind": "checks", "options": DEAD_HABIT_REASONS}]},
]

OFFER = {
    "kicker": "Step two",
    "variants": [
        {"key": "A", "h": "You&#39;ve written it down. Historically, this is where it dies.",
         "p": "Step two is a plan built around the hours you actually have, not the ones you promised."},
        {"key": "B", "h": "Goals are free. The doing is the product.",
         "p": "You&#39;ve done the thinking. The rest is a calendar and your real hours."},
        {"key": "C", "h": "Writing it down isn&#39;t training.",
         "p": f"A custom plan for your {NEXT}, built from what you just told me."},
    ],
    # Roadie Labs sells one plan product today: the custom Race Plan
    # (/questionnaire/, a real Stripe checkout via the shared Motoren
    # pipeline). No Season Plan card here — that is a Gravel God-only
    # product (docs/specs/goals-2027-funnel-spec.md D2/D15); linking one
    # for Roadie Labs would be a dead product, not a dead link, which is the
    # same failure this task's spec forbids.
    "plans": [
        {"key": "race", "price": "Race Plan: priced by the week from your race date",
         "cta": f"Build my {NEXT} plan", "cta_href": "/questionnaire/?src=goals"},
    ],
    "decline": "Just the poster, thanks",
    "terms": "I build every plan myself. You see the number before you pay.",
}

RESULTS = {
    "title": f"Your {NEXT}, on paper.",
    "lead": "Print it. Tape it where you&#39;ll see it in February. A copy is on its way to your inbox.",
    "download": "Download the poster",
}


# ── Field rendering ───────────────────────────────────────────

def _attr(value: str) -> str:
    return html.escape(value, quote=True)


def _req(field) -> str:
    return ' <span class="rl-apply-required">*</span>' if field.get("req") else ""


def _label(field, for_id: bool = True) -> str:
    if not field.get("label"):
        return ""
    swap = field.get("swap", {})
    data = "".join(
        f' data-lbl-{d}="{_attr(v["label"])}"' for d, v in swap.items() if "label" in v
    )
    target = f' for="{field["name"]}"' if for_id else ""
    return f'<label class="rl-apply-label"{target}{data}>{field["label"]}{_req(field)}</label>'


def _control(field) -> str:
    name, kind = field["name"], field["kind"]
    req = " required" if field.get("req") else ""
    ph = f' placeholder="{field["ph"]}"' if field.get("ph") else ""
    swap = field.get("swap", {})
    ph_data = "".join(f' data-ph-{d}="{_attr(v["ph"])}"' for d, v in swap.items() if "ph" in v)
    if kind in ("text", "email", "date"):
        auto = f' autocomplete="{field["auto"]}"' if field.get("auto") else ""
        return f'<input type="{kind}" id="{name}" name="{name}"{req}{ph}{ph_data}{auto}>'
    if kind == "area":
        return f'<textarea id="{name}" name="{name}" rows="{field.get("rows", 3)}"{req}{ph}></textarea>'
    if kind == "select":
        opts = '<option value="">Select...</option>' + "".join(
            f'<option value="{_attr(v)}">{t}</option>' for v, t in field["options"]
        )
        return f'<select id="{name}" name="{name}"{req}>{opts}</select>'
    if kind == "radio":
        lift = field.get("lift")
        lift_attr = (
            f' data-lift-when="{lift["when"]}" data-lift="{",".join(lift["fields"])}"' if lift else ""
        )
        opts = "".join(
            f'<label class="rl-apply-radio-option"><input type="radio" name="{name}" value="{o[0]}"'
            f'{req if i == 0 else ""}><div class="rl-apply-radio-label"><div class="rl-apply-radio-title">{o[1]}</div>'
            + (f'<div class="rl-apply-radio-desc">{o[2]}</div>' if len(o) > 2 else "")
            + "</div></label>"
            for i, o in enumerate(field["options"])
        )
        layout = "" if any(len(o) > 2 for o in field["options"]) else " rl-apply-radio-horizontal"
        return f'<div class="rl-apply-radio-group{layout}" data-radio="{name}"{lift_attr}>{opts}</div>'
    if kind == "checks":
        opts = "".join(
            f'<label class="rl-apply-checkbox-option"><input type="checkbox" name="{n}" value="yes">'
            f'<span class="rl-apply-checkbox-label">{t}</span></label>'
            for n, t in field["options"]
        )
        return f'<div class="rl-apply-checkbox-vertical">{opts}</div>'
    if kind == "timed":
        return f'<textarea id="{name}" name="{name}" rows="{field.get("rows", 10)}" class="rl-goals-long"></textarea>'
    raise ValueError(f"unknown field kind {kind!r}")


WHY_NAMES = ["outcome_why", "why_2", "why_3", "why_4", "why_5"]


def render_why_chain(field) -> str:
    """Five whys. Each box appears once the one before has an answer, and
    its question quotes that answer back (filled in by the page script)."""
    groups = []
    for i, name in enumerate(WHY_NAMES):
        label = field["label"] if i == 0 else "And why does that matter?"
        req = " required" if field.get("req") and i == 0 else ""
        star = ' <span class="rl-apply-required">*</span>' if req else ""
        hidden = " hidden" if i else ""
        groups.append(
            f'<div class="rl-apply-group rl-goals-why" data-q="{_attr(_strip_tags(html.unescape(label)))}" data-why="{i}"{hidden}>'
            f'<label class="rl-apply-label" for="{name}">{label}{star}</label>'
            f'<input type="text" id="{name}" name="{name}"{req}'
            + (f' placeholder="{field["ph"]}"' if i == 0 and field.get("ph") else "")
            + "></div>"
        )
    return f'<div class="rl-goals-whys">{"".join(groups)}</div>'


def render_field(field, context_title: str = "") -> str:
    if field["kind"] == "whychain":
        return render_why_chain(field)
    if field["kind"] == "pair":
        inner = "".join(render_field(f, context_title) for f in field["fields"])
        return f'<div class="rl-apply-inline">{inner}</div>'
    # data-q is the question as it appears in the console formatter used by
    # the walkthrough helper on the results screen's answer summary.
    q = field.get("label") or context_title
    head = _label(field, for_id=field["kind"] not in ("radio", "checks"))
    if field["kind"] == "timed":
        head = (
            f'<div class="rl-goals-label-row">{head}'
            f'<button type="button" class="rl-goals-timer" data-minutes="{field["minutes"]}" data-target="{field["name"]}">'
            f'Start {field["minutes"]}:00</button></div>'
        )
    return (
        f'<div class="rl-apply-group" data-q="{_attr(html.unescape(_strip_tags(q)))}">'
        f"{head}{_control(field)}</div>"
    )


def _strip_tags(s: str) -> str:
    import re
    return re.sub(r"<[^>]+>", "", s)


def render_sections() -> str:
    out, n = [], 0
    for sec in SECTIONS:
        n += 1
        title = f"{n}. {sec['title']}"
        num_attr = f'data-section-n="{n}" '
        fields = "".join(render_field(f, sec["title"]) for f in sec["fields"])
        # No `sub` line under the section title — house rule: no descriptive
        # subtitles under headings (unlike the gravel page, which sets one
        # on 3 of its 6 sections).
        out.append(f'<div {num_attr}class="rl-apply-section-title">{title}</div>\n      {fields}')
    return "\n      ".join(out)


def render_modules() -> str:
    mods = []
    for m in MODULES:
        fields = "".join(render_field(f, m["title"]) for f in m["fields"])
        mods.append(
            f'<details class="rl-goals-deeper" data-module="{m["key"]}">'
            f'<summary>{m["title"]} <span class="rl-apply-optional">({m["minutes"]})</span></summary>'
            f"{fields}</details>"
        )
    return '<div class="rl-goals-part">Extra credit &mdash; for the obsessive</div>\n      ' + "\n      ".join(mods)


# ── Page pieces ───────────────────────────────────────────────

def build_nav() -> str:
    return get_site_header_html()


def build_header() -> str:
    return '''<div class="rl-apply-header">
    <div class="rl-apply-badge">The 2027 Goal Autopsy</div>
    <h1>So. 2026.</h1>
    <p>Fifteen minutes. Don&#39;t write what you&#39;d post. Write what you&#39;d admit after the second beer. You leave with a 2027 goal poster and the one thing most likely to wreck it. It saves as you go.</p>
  </div>'''


def build_results() -> str:
    """Shown after submitting: the poster first, the offer underneath it."""
    plans_html = "".join(
        f'<div class="rl-goals-offer-plan">'
        f'<p class="rl-goals-offer-plan-price">{plan["price"]}</p>'
        f'<a class="rl-goals-offer-cta" href="{plan["cta_href"]}" data-offer-cta data-plan-type="{plan["key"]}">{plan["cta"]}</a>'
        f"</div>"
        for plan in OFFER["plans"]
    )
    cards = "".join(
        f'<div class="rl-goals-offer" data-offer-variant="{v["key"]}" hidden>'
        f'<div class="rl-goals-offer-kicker">{OFFER["kicker"]}</div>'
        f'<h3 class="rl-goals-offer-h">{v["h"]}</h3>'
        f'<p class="rl-goals-offer-p">{v["p"]}</p>'
        f'<div class="rl-goals-offer-plans">{plans_html}</div>'
        f'<p class="rl-goals-offer-terms">{OFFER["terms"]}</p>'
        f'<a class="rl-goals-offer-decline" href="#" data-offer-decline>{OFFER["decline"]}</a>'
        f"</div>"
        for v in OFFER["variants"]
    )
    return f'''<section id="results" class="rl-goals-results" hidden>
    <div class="rl-goals-results-head">
      <h2>{RESULTS["title"]}</h2>
      <p>{RESULTS["lead"]}</p>
    </div>
    <canvas id="poster-canvas" width="1080" height="1440" class="rl-goals-poster" aria-label="Your 2027 goal poster"></canvas>
    <a id="poster-download" class="rl-goals-download" href="#" download="2027-goal-poster.png">{RESULTS["download"]}</a>
    {cards}
  </section>'''


def build_submit_buttons() -> str:
    lead_html = '<p class="rl-goals-done">That&#39;s it. Hit submit and your poster is on its way &mdash; or keep digging first.</p>'
    return f'''{lead_html}<div class="rl-apply-actions">
        <button type="button" class="rl-apply-save-btn rl-goals-save">Save Progress</button>
        <button type="submit" class="rl-apply-submit-btn rl-goals-submit" id="goals-submit">Make My Poster</button>
      </div>'''


def build_footer() -> str:
    # A stranger, not a client: say exactly what happens and nothing more
    # (mirrors gravel's worker-transport footer — docs/specs/goals-2027-funnel-spec.md D17).
    return f'''<div class="rl-apply-confidential-wrap">
    <p class="rl-apply-confidential">Your answers are stored so I can make your poster and email it to you, and I&#39;ll send one short check-in a week later. Unsubscribe from either with the link in the email. Nothing is sold or shared; the <a href="/privacy/">Privacy Policy</a> has the detail. Your draft stays in this browser until you submit. Questions? Email {CONTACT_EMAIL}</p>
  </div>
  ''' + get_mega_footer_html()


# ── CSS ──────────────────────────────────────────────────────

def build_goals_css() -> str:
    return '''<style>
.rl-goals-part {
  font-family: var(--rl-font-data);
  font-size: var(--rl-font-size-2xs);
  font-weight: var(--rl-font-weight-bold);
  text-transform: uppercase;
  letter-spacing: var(--rl-letter-spacing-wider);
  background: var(--rl-color-near-black);
  color: var(--rl-color-white);
  padding: var(--rl-spacing-xs) var(--rl-spacing-md);
  margin: var(--rl-spacing-2xl) 0 var(--rl-spacing-md);
}
.rl-goals-deeper {
  border: 2px dashed var(--rl-color-near-black);
  padding: var(--rl-spacing-md);
  margin-bottom: var(--rl-spacing-sm);
}
.rl-goals-done {
  font-family: var(--rl-font-editorial);
  font-size: var(--rl-font-size-sm);
  color: var(--rl-color-secondary-blue);
  margin: var(--rl-spacing-xl) 0 0;
}
.rl-goals-deeper[open] { border-style: solid; background: var(--rl-color-cool-white); }
.rl-goals-deeper summary {
  cursor: pointer;
  font-family: var(--rl-font-data);
  font-size: var(--rl-font-size-sm);
  font-weight: var(--rl-font-weight-bold);
  text-transform: uppercase;
  letter-spacing: var(--rl-letter-spacing-wide);
}
.rl-goals-deeper[open] summary { margin-bottom: var(--rl-spacing-lg); }
.rl-goals-deeper .rl-apply-group:last-child { margin-bottom: 0; }

.rl-goals-label-row {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: var(--rl-spacing-sm);
}
.rl-goals-label-row .rl-apply-label { flex: 1; }
.rl-goals-timer {
  flex-shrink: 0;
  margin-bottom: var(--rl-spacing-xs);
  background: var(--rl-color-white);
  border: 2px solid var(--rl-color-near-black);
  font-family: var(--rl-font-data);
  font-size: var(--rl-font-size-xs);
  font-weight: var(--rl-font-weight-bold);
  font-variant-numeric: tabular-nums;
  padding: 4px var(--rl-spacing-sm);
  min-width: 96px;
  cursor: pointer;
}
.rl-goals-timer:hover { background: var(--rl-color-cool-white); }
.rl-goals-timer.running { background: var(--rl-color-signal-red); color: var(--rl-color-white); }
.rl-goals-timer.done { background: var(--rl-color-near-black); color: var(--rl-color-white); }
.rl-goals-why + .rl-goals-why { padding-left: var(--rl-spacing-lg); border-left: 3px solid var(--rl-color-signal-red); }
.rl-apply-form-card textarea.rl-goals-long {
  font-family: var(--rl-font-editorial);
  font-size: var(--rl-font-size-base);
  line-height: var(--rl-line-height-relaxed);
}

/* Results: the poster first, the offer under it */
.rl-goals-results {
  scroll-margin-top: 114px;
  border: var(--rl-border-standard);
  background: var(--rl-color-white);
  padding: var(--rl-spacing-xl);
  margin-bottom: var(--rl-spacing-lg);
}
.rl-goals-results-head h2 {
  font-family: var(--rl-font-editorial);
  font-size: var(--rl-font-size-2xl);
  font-weight: var(--rl-font-weight-bold);
  margin: 0 0 var(--rl-spacing-xs);
}
.rl-goals-results-head p {
  font-family: var(--rl-font-editorial);
  color: var(--rl-color-secondary-blue);
  margin: 0 0 var(--rl-spacing-lg);
  max-width: 46ch;
}
.rl-goals-poster {
  display: block;
  width: 100%;
  height: auto;
  border: var(--rl-border-standard);
  background: var(--rl-color-near-black);
}
.rl-goals-download {
  display: block;
  text-align: center;
  margin-top: var(--rl-spacing-md);
  padding: var(--rl-spacing-md);
  background: var(--rl-color-near-black);
  color: var(--rl-color-white);
  font-family: var(--rl-font-data);
  font-size: var(--rl-font-size-sm);
  font-weight: var(--rl-font-weight-bold);
  letter-spacing: var(--rl-letter-spacing-wide);
  text-transform: uppercase;
  text-decoration: none;
  border: var(--rl-border-standard);
}
.rl-goals-download:hover { background: var(--rl-color-white); color: var(--rl-color-near-black); }
.rl-goals-offer {
  border: var(--rl-border-standard);
  background: var(--rl-color-cool-white);
  padding: var(--rl-spacing-lg);
  margin-top: var(--rl-spacing-2xl);
}
.rl-goals-offer-kicker {
  font-family: var(--rl-font-data);
  font-size: var(--rl-font-size-2xs);
  font-weight: var(--rl-font-weight-bold);
  letter-spacing: var(--rl-letter-spacing-wider);
  text-transform: uppercase;
  color: var(--rl-color-signal-red);
}
.rl-goals-offer-h {
  font-family: var(--rl-font-editorial);
  font-size: var(--rl-font-size-xl);
  font-weight: var(--rl-font-weight-bold);
  line-height: 1.1;
  margin: var(--rl-spacing-xs) 0 var(--rl-spacing-sm);
}
.rl-goals-offer-p {
  font-family: var(--rl-font-editorial);
  font-size: var(--rl-font-size-base);
  margin: 0 0 var(--rl-spacing-md);
}
.rl-goals-offer-terms {
  font-family: var(--rl-font-data);
  font-size: var(--rl-font-size-2xs);
  line-height: 1.6;
  color: var(--rl-color-secondary-blue);
  border-top: 2px solid var(--rl-color-silver);
  padding-top: var(--rl-spacing-sm);
  margin: 0 0 var(--rl-spacing-md);
}
.rl-goals-offer-cta {
  display: block;
  text-align: center;
  padding: var(--rl-spacing-md);
  background: var(--rl-color-signal-red);
  color: var(--rl-color-white);
  border: var(--rl-border-standard);
  font-family: var(--rl-font-data);
  font-weight: var(--rl-font-weight-bold);
  letter-spacing: var(--rl-letter-spacing-wide);
  text-transform: uppercase;
  text-decoration: none;
}
.rl-goals-offer-cta:hover { background: var(--rl-color-near-black); color: var(--rl-color-white); }
.rl-goals-offer-plans {
  display: flex;
  gap: var(--rl-spacing-md);
  margin: 0 0 var(--rl-spacing-md);
}
.rl-goals-offer-plan { flex: 1; }
.rl-goals-offer-plan-price {
  font-family: var(--rl-font-data);
  font-size: var(--rl-font-size-2xs);
  color: var(--rl-color-secondary-blue);
  margin: 0 0 var(--rl-spacing-xs);
  text-align: center;
}
.rl-goals-offer-decline {
  display: block;
  text-align: center;
  margin-top: var(--rl-spacing-sm);
  font-family: var(--rl-font-data);
  font-size: var(--rl-font-size-xs);
  color: var(--rl-color-secondary-blue);
}

@media (max-width: 600px) {
  .rl-goals-label-row { flex-direction: column; align-items: stretch; }
  .rl-goals-timer { align-self: flex-start; }
  .rl-apply-actions { flex-direction: column-reverse; align-items: stretch; gap: var(--rl-spacing-sm); }
  .rl-apply-save-btn { margin-right: 0; }
  .rl-goals-offer-plans { flex-direction: column; }
}
</style>'''


# ── JavaScript ────────────────────────────────────────────────

def build_goals_js() -> str:
    js = r'''<script>
(function() {
  "use strict";

  var STORAGE_KEY = "rl_goals_2027_v1";
  var HAS_RESULTS = document.getElementById("results") !== null;
  var SEASON = __SEASON__;
  var SUCCESS = "Got it. Your 2027 poster is on its way to your inbox.";
  var lastStored = false;

  var form = document.getElementById("goals-form");

  /* Entry attribution: the homepage and the race-page goal card
     (generate_neo_brutalist.py build_goal_card) both link here as
     /goals/?src=home or /goals/?src=race&race=<slug>. Read the same params
     so the funnel — and the lead itself — can be attributed to the same
     surface. Validated so a malformed value never lands in an event or a
     stored lead. */
  var ENTRY_SRC = (function() {
    var v = "";
    try { v = new URLSearchParams(window.location.search).get("src") || ""; } catch (e) {}
    return /^[a-z_]{1,24}$/.test(v) ? v : "";
  })();
  var RACE_SLUG = (function() {
    var v = "";
    try { v = new URLSearchParams(window.location.search).get("race") || ""; } catch (e) {}
    return /^[a-z0-9-]{1,80}$/.test(v) ? v : "";
  })();
  // Which goal the visitor tapped on the race-page goal card before
  // landing here — ?goal_type=. Fixed set only, same discipline as
  // ENTRY_SRC/RACE_SLUG: a malformed value never lands in an event, a
  // stored lead, or the outcome_goal prefill below.
  var GOAL_TYPE = (function() {
    var v = "";
    try { v = new URLSearchParams(window.location.search).get("goal_type") || ""; } catch (e) {}
    return /^(finish|beat_time|race_it|same|bigger)$/.test(v) ? v : "";
  })();

  function ga4(name, params) {
    params = params || {};
    if (ENTRY_SRC) { params.src = ENTRY_SRC; }
    if (RACE_SLUG) { params.race_slug = RACE_SLUG; }
    if (typeof gtag === "function") { gtag("event", name, params); }
  }

  /* ── Start / stop swaps the habit prompts ────────── */
  function setDirection(dir) {
    form.querySelectorAll("[data-ph-" + dir + "]").forEach(function(el) {
      el.placeholder = el.getAttribute("data-ph-" + dir);
    });
    form.querySelectorAll("[data-lbl-" + dir + "]").forEach(function(el) {
      var star = el.querySelector(".rl-apply-required");
      el.textContent = el.getAttribute("data-lbl-" + dir);
      if (star) { el.appendChild(document.createTextNode(" ")); el.appendChild(star); }
      var group = el.closest("[data-q]");
      if (group) { group.setAttribute("data-q", el.getAttribute("data-lbl-" + dir)); }
    });
  }

  /* ── Radio side effects: styling, start/stop, lifted requirements ── */
  function radioChanged(input) {
    form.querySelectorAll("input[name=\"" + input.name + "\"]").forEach(function(inp) {
      inp.closest(".rl-apply-radio-option").classList.toggle("selected", inp.checked);
    });
    if (input.name === "habit_direction") { setDirection(input.value); }
    var group = input.closest("[data-lift]");
    if (group) {
      var lifted = input.value === group.getAttribute("data-lift-when");
      group.getAttribute("data-lift").split(",").forEach(function(id) {
        var el = document.getElementById(id);
        if (!el) { return; }
        el.required = !lifted;
        var star = form.querySelector("label[for=" + id + "] .rl-apply-required");
        if (star) { star.hidden = lifted; }
      });
    }
  }

  /* ── Writing timers (end time, so they survive a backgrounded tab) ── */
  var timer = null;
  var timerBtn = null;
  function resetTimer(btn) {
    btn.classList.remove("running", "done");
    btn.textContent = "Start " + btn.getAttribute("data-minutes") + ":00";
  }
  function toggleTimer(btn) {
    if (timer) {
      clearInterval(timer);
      timer = null;
      var same = timerBtn === btn;
      resetTimer(timerBtn);
      if (same) { return; }
    }
    timerBtn = btn;
    var endsAt = Date.now() + Number(btn.getAttribute("data-minutes")) * 60000;
    btn.classList.remove("done");
    btn.classList.add("running");
    document.getElementById(btn.getAttribute("data-target")).focus();
    function paint() {
      var left = Math.max(0, Math.round((endsAt - Date.now()) / 1000));
      if (left === 0) {
        clearInterval(timer);
        timer = null;
        btn.classList.remove("running");
        btn.classList.add("done");
        btn.textContent = "Time";
        return;
      }
      var m = Math.floor(left / 60), s = left % 60;
      btn.textContent = m + ":" + (s < 10 ? "0" : "") + s;
    }
    paint();
    timer = setInterval(paint, 500);
  }

  /* ── Events ──────────────────────────────────────── */
  form.addEventListener("click", function(e) {
    var t = e.target;
    var tb = t.closest(".rl-goals-timer");
    if (tb) { toggleTimer(tb); return; }

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

  /* five whys: reveal the next box and quote the previous answer back */
  function updateWhys() {
    var groups = form.querySelectorAll(".rl-goals-why");
    for (var i = 1; i < groups.length; i++) {
      var prev = groups[i - 1].querySelector("input").value.trim();
      var shown = !groups[i - 1].hidden && prev.length > 0;
      var own = groups[i].querySelector("input").value.trim();
      groups[i].hidden = !(shown || own);
      if (prev) {
        var quoted = prev.length > 60 ? prev.slice(0, 57).trim() + "..." : prev;
        groups[i].querySelector("label").textContent = "Why does “" + quoted + "” matter?";
        groups[i].setAttribute("data-q", groups[i].querySelector("label").textContent);
      }
    }
  }

  /* Chosen before submit so it rides along with the answers — a test whose
     result lives only in analytics is a test you cannot read later. */
  var OFFER_VARIANT = (function() {
    var cards = document.querySelectorAll("[data-offer-variant]");
    if (!cards.length) { return ""; }
    return cards[Math.floor(Math.random() * cards.length)].getAttribute("data-offer-variant");
  })();

  var started = false;
  function onEdit(e) {
    if (!started) { started = true; ga4("goal_start", {}); }
    if (e && e.target.type === "radio" && e.target.checked) { radioChanged(e.target); }
    if (e && e.target.closest && e.target.closest(".rl-goals-why")) { updateWhys(); }
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

  /* Set while restore() may still be driving a programmatic scroll (its
     own "Picked up where you left off" message smooth-scrolls into view),
     so that scroll is never mistaken for the genuine interaction that
     starts goal_section tracking. */
  var restoringDraft = false;

  function restore() {
    restoringDraft = true;
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
      form.querySelectorAll(".rl-goals-deeper").forEach(function(mod) {
        var used = Array.prototype.some.call(mod.querySelectorAll("[name]"), function(el) { return !!saved[el.name]; });
        if (used) { mod.open = true; }
      });
      showMessage("info", "Picked up where you left off.");
    }
    updateWhys();
    /* personalised links: ?name=&email= */
    var params = new URLSearchParams(window.location.search);
    ["name", "email"].forEach(function(k) {
      var el = document.getElementById(k);
      if (el && params.get(k) && !el.value) { el.value = params.get(k); }
    });
    /* Prefill from the race-page goal card's tap: ?goal_type= carries which
       goal the visitor already picked there. The line templates mirror
       GOAL_CARD_COPY.goal_lines in generate_neo_brutalist.py's
       build_goal_card — update both if the copy changes. Only fills the
       field when it is still empty: a returning visitor's own typed
       answer, or a restored draft, is never overwritten. */
    if (GOAL_TYPE) {
      var goalLineTemplates = {
        finish: "Finish {race}.",
        beat_time: "Finish {race} faster than last time.",
        race_it: "Race {race}, not just ride it.",
        same: "Ride {race} again, and ride it better.",
        bigger: "Take on something bigger than {race}."
      };
      var raceLabel = RACE_SLUG
        ? RACE_SLUG.split("-").filter(Boolean).map(function(w) {
            return w.charAt(0).toUpperCase() + w.slice(1);
          }).join(" ")
        : "it";
      var goalField = document.getElementById("outcome_goal");
      if (goalField && !goalField.value.trim()) {
        goalField.value = goalLineTemplates[GOAL_TYPE].replace("{race}", raceLabel);
      }
    }
    updateProgress();
    setTimeout(function() { restoringDraft = false; }, 800);
  }

  form.querySelectorAll(".rl-goals-save").forEach(function(b) {
    b.addEventListener("click", function() { save(false); });
  });
  window.addEventListener("beforeunload", function() { save(true); });

  /* ── Submit ──────────────────────────────────────── */
  function setButtons(disabled, label) {
    form.querySelectorAll(".rl-goals-submit").forEach(function(b) { b.disabled = disabled; b.textContent = label; });
  }

  form.addEventListener("submit", function(e) {
    e.preventDefault();
    if (form.querySelector(".rl-goals-submit").disabled) { return; }
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
      if (k !== "name" && k !== "email" && typeof d[k] === "string") { answers[k] = d[k]; }
    });
    fetch("__LEAD_WORKER_URL__", {
      method: "POST",
      headers: { "Content-Type": "application/json", "Accept": "application/json" },
      body: JSON.stringify({
        source: "__LEAD_SOURCE__", brand: "__LEAD_BRAND__", email: d.email, name: d.name || "",
        goal_answers: answers, website: "",
        offer_variant: OFFER_VARIANT, race_slug: RACE_SLUG, entry_src: ENTRY_SRC,
        goal_type: GOAL_TYPE
      }),
      signal: ctrl ? ctrl.signal : undefined
    }).then(function(r) {
      return r.json().then(function() { return r.ok; }).catch(function() { return r.ok; });
    }).catch(function() { return false; })
      .then(function(ok) {
        clearTimeout(killer);
        lastStored = ok;
        if (!ok) { throw new Error("worker transport failed"); }
      })
      .then(function() {
        submitted = true;
        if (HAS_RESULTS) { showResults(d); }
        clearTimeout(saveTimer);
        try { localStorage.removeItem(STORAGE_KEY); } catch (err) { /* ignore */ }
        ga4("goal_submit", {});
        if (!HAS_RESULTS) { showMessage("success", SUCCESS); }
        setButtons(true, "Submitted");
      })
      .catch(function(err) {
        clearTimeout(killer);
        showMessage("error", saveOk
          ? "That didn't go through. Your answers are saved in this browser. Try again, or email __CONTACT_EMAIL__."
          : "That didn't go through, and this browser can't save. Keep this page open and try again, or email __CONTACT_EMAIL__.");
        setButtons(false, "Make My Poster");
      });
  });

  /* ── The results screen ──────────────────────────── */
  var POSTER = __POSTER_COLORS__;

  /* The emailed poster trims to these lengths
     (mission_control/services/goal_poster.py) — match them so the two
     copies read the same. */
  function posterClean(value, limit) {
    return String(value || "").split(/\s+/).join(" ").trim().slice(0, limit);
  }

  function wrapText(ctx, text, maxWidth) {
    var words = String(text).split(/\s+/), lines = [], line = "";
    words.forEach(function(word) {
      var next = line ? line + " " + word : word;
      if (ctx.measureText(next).width <= maxWidth || !line) { line = next; }
      else { lines.push(line); line = word; }
    });
    if (line) { lines.push(line); }
    return lines;
  }

  /* Same design and layout algorithm as the emailed poster: the goal
     shrinks to fit rather than running into the frame below it. */
  function drawPoster(d) {
    var canvas = document.getElementById("poster-canvas");
    var ctx = canvas.getContext("2d");
    var W = canvas.width, H = canvas.height, pad = 84, inner = W - pad * 2;
    ctx.fillStyle = POSTER.paper;
    ctx.fillRect(0, 0, W, H);
    ctx.textBaseline = "top";

    ctx.font = "700 26px 'Sometype Mono', monospace";
    ctx.fillStyle = POSTER.accent;
    ctx.fillText((SEASON + 1) + " · GOAL FILE", pad, pad);
    ctx.fillStyle = POSTER.ink;
    ctx.textAlign = "right";
    ctx.fillText("ROADIE LABS", W - pad, pad);
    ctx.textAlign = "left";
    ctx.font = "22px 'Sometype Mono', monospace";
    ctx.fillStyle = POSTER.grey;
    ctx.fillText("ROADIELABS.COM", pad, H - pad - 20);

    var habit = posterClean(d.habit, 120);
    if (habit && d.habit_when) { habit += " — " + posterClean(d.habit_when, 120); }
    var rows = [[d.habit_direction === "reduce" ? "STOPPING" : "EVERY DAY", habit],
                ["ALSO EVERY DAY", posterClean(d.habit_2, 150)],
                ["WATCH FOR", posterClean(d.inner_obstacle, 150)]]
      .filter(function(r) { return r[1]; })
      .map(function(r) {
        ctx.font = "30px 'Sometype Mono', monospace";
        return [r[0], wrapText(ctx, r[1], inner).slice(0, 2)];
      });
    var framed = rows.reduce(function(h, r) { return h + 56 + r[1].length * 38; }, 0);
    var frameTop = H - pad - 60 - framed;
    var y = frameTop;
    rows.forEach(function(row) {
      ctx.font = "700 24px 'Sometype Mono', monospace";
      ctx.fillStyle = POSTER.accent;
      ctx.fillText(row[0], pad, y);
      ctx.font = "30px 'Sometype Mono', monospace";
      ctx.fillStyle = POSTER.ink;
      row[1].forEach(function(line, i) { ctx.fillText(line, pad, y + 34 + i * 38); });
      y += 56 + row[1].length * 38;
    });

    ctx.font = "italic 38px 'Source Serif 4', Georgia, serif";
    var why = posterClean([d.why_5, d.why_4, d.why_3, d.why_2, d.outcome_why]
      .filter(function(w) { return w && String(w).trim(); })[0], 200);
    var whyLines = why ? wrapText(ctx, "“" + why + "”", inner).slice(0, 3) : [];
    var whyHeight = whyLines.length * 50 + (whyLines.length ? 30 : 0);

    var labelY = pad + 200;
    var available = frameTop - whyHeight - labelY - 120;
    var goal = posterClean(d.outcome_goal, 180) || "[your goal]";
    if (!/[.!?]$/.test(goal)) { goal += "."; }
    var size = 104, goalLines = [];
    [104, 92, 80, 68, 58, 48].forEach(function(candidate) {
      if (goalLines.length && goalLines.length * Math.round(size * 1.06) <= available) { return; }
      size = candidate;
      ctx.font = "700 " + size + "px 'Source Serif 4', Georgia, serif";
      goalLines = wrapText(ctx, goal, inner);
    });

    ctx.font = "26px 'Sometype Mono', monospace";
    ctx.fillStyle = POSTER.grey;
    ctx.fillText("BY THE END OF " + (SEASON + 1) + ", " + (posterClean(d.name, 40) || "I").toUpperCase() + " WILL", pad, labelY);

    ctx.font = "700 " + size + "px 'Source Serif 4', Georgia, serif";
    ctx.fillStyle = POSTER.ink;
    y = labelY + 60;
    goalLines.slice(0, 6).forEach(function(line) {
      ctx.fillText(line, pad, y);
      y += Math.round(size * 1.06);
    });
    ctx.fillStyle = POSTER.accent;
    ctx.fillRect(pad, y + 24, 150, 6);

    ctx.font = "italic 38px 'Source Serif 4', Georgia, serif";
    ctx.fillStyle = POSTER.grey;
    y = frameTop - whyHeight;
    whyLines.forEach(function(line) { ctx.fillText(line, pad, y); y += 50; });
  }

  function showResults(d) {
    var results = document.getElementById("results");
    var message = document.getElementById("message");
    if (message) { message.classList.add("hidden"); }
    form.hidden = true;
    results.hidden = false;
    try { drawPoster(d); } catch (err) { /* the emailed copy is the real one */ }
    var link = document.getElementById("poster-download");
    try { link.href = document.getElementById("poster-canvas").toDataURL("image/png"); }
    catch (err) { link.hidden = true; }
    link.addEventListener("click", function() { ga4("goal_poster_download", {}); });

    var pick = results.querySelector("[data-offer-variant=\"" + OFFER_VARIANT + "\"]");
    if (pick) {
      pick.hidden = false;
      var key = OFFER_VARIANT;
      pick.querySelectorAll("[data-offer-cta]").forEach(function(cta) {
        var planType = cta.getAttribute("data-plan-type") || "race";
        try {
          var ctaUrl = new URL(cta.getAttribute("href"), window.location.href);
          ctaUrl.searchParams.set("offer_variant", key);
          if (RACE_SLUG) { ctaUrl.searchParams.set("race", RACE_SLUG); }
          if (ENTRY_SRC) { ctaUrl.searchParams.set("entry_src", ENTRY_SRC); }
          cta.href = ctaUrl.pathname + ctaUrl.search;
        } catch (err) { /* keep the static href */ }
        ga4("goal_offer_view", { offer_variant: key, plan_type: planType });
        cta.addEventListener("click", function() {
          ga4("goal_offer_click", { offer_variant: key, plan_type: planType });
        });
      });
      var decline = pick.querySelector("[data-offer-decline]");
      if (decline) {
        decline.addEventListener("click", function(e) {
          e.preventDefault();
          pick.hidden = true;
          ga4("goal_offer_declined", { offer_variant: key });
        });
      }
    }
    ga4("goal_results_view", {});
    results.scrollIntoView({ behavior: "smooth", block: "start" });
  }

  function showMessage(type, text) {
    var m = document.getElementById("message");
    m.className = "rl-apply-message " + type;
    m.textContent = text;
    m.classList.remove("hidden");
    m.scrollIntoView({ behavior: "smooth", block: "center" });
  }

  /* goal_section: fired once per numbered section the visitor actually
     scrolls to (a real action), never on a timer. */
  function watchGoalSections() {
    if (typeof IntersectionObserver !== "function") { return; }
    var targets = Array.prototype.slice.call(form.querySelectorAll("[data-section-n]"));
    if (!targets.length) { return; }
    var seen = {};
    var observer = new IntersectionObserver(function(entries) {
      entries.forEach(function(entry) {
        if (!entry.isIntersecting) { return; }
        var n = entry.target.getAttribute("data-section-n");
        if (!n || seen[n]) { return; }
        seen[n] = true;
        ga4("goal_section", { number: Number(n) });
      });
    }, { threshold: 0.5 });
    targets.forEach(function(t) { observer.observe(t); });
  }

  var goalSectionsStarted = false;
  function startWatchingGoalSectionsOnce() {
    if (goalSectionsStarted || restoringDraft) { return; }
    goalSectionsStarted = true;
    watchGoalSections();
  }
  ["pointerdown", "keydown", "wheel", "touchstart"].forEach(function(evt) {
    window.addEventListener(evt, startWatchingGoalSectionsOnce, { once: true, passive: true });
  });
  restore();
})();
</script>'''
    return (
        js.replace("__LEAD_WORKER_URL__", LEAD_WORKER_URL)
        .replace("__LEAD_SOURCE__", LEAD_SOURCE)
        .replace("__LEAD_BRAND__", LEAD_BRAND)
        .replace("__SEASON__", str(SEASON))
        .replace("__CONTACT_EMAIL__", CONTACT_EMAIL)
        # Poster canvas colors sourced from brand_tokens.COLORS, not
        # hardcoded hex (CLAUDE.md, sol review 2026-09-27).
        .replace("__POSTER_COLORS__", _safe_json_for_script({
            "ink": COLORS["near_black"], "paper": COLORS["cool_white"],
            "accent": COLORS["signal_red"], "grey": COLORS["secondary_blue"],
        }))
    )


# ── Hero click tracking (home / race entry points) ─────────────
# The homepage and the race-page goal card fire goal_hero_click themselves
# (they own the click, this page owns everything after the visitor lands)
# — nothing to add here.


def generate_goals_page(external_assets: dict = None) -> str:
    if external_assets:
        page_css = external_assets['css_tag']
    else:
        page_css = get_page_css()

    nav = build_nav()
    header = build_header()
    progress = build_progress_bar()
    sections = render_sections()
    modules = render_modules()
    submit = build_submit_buttons()
    results = build_results()
    footer = build_footer()

    title = f"Your {NEXT} Goal, On Paper | Roadie Labs"
    description = (f"Fifteen minutes on the season you had and the one you want. You leave "
                    f"with a {NEXT} goal poster and the one thing most likely to wreck it.")

    return f'''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{title}</title>
  <meta name="description" content="{description}">
  <meta name="robots" content="index, follow">
  <link rel="canonical" href="{CANONICAL_URL}">
  <meta property="og:title" content="{title}">
  <meta property="og:description" content="{description}">
  <meta property="og:type" content="website">
  <meta property="og:url" content="{CANONICAL_URL}">
  <meta property="og:site_name" content="Roadie Labs">
  <meta name="twitter:card" content="summary_large_image">
  <link rel="icon" type="image/svg+xml" href="/race/assets/rl-logo.svg">
  {get_preload_hints()}
  {page_css}
  <!-- GA4 -->
  {get_ga4_head_snippet()}
  {build_apply_css()}
  {build_goals_css()}
</head>
<body class="rl-neo-brutalist-page" style="background:var(--rl-color-cool-white);color:var(--rl-color-near-black);font-family:var(--rl-font-data);font-size:var(--rl-font-size-sm);line-height:1.7;min-height:100vh">
  {nav}
  <div class="rl-apply-container">
    {header}
    {progress}
    <div id="message" class="rl-apply-message hidden"></div>
    <form id="goals-form" class="rl-apply-form-card">
      <input type="text" name="website" class="rl-apply-honeypot" tabindex="-1" autocomplete="off">
      {sections}
      {submit}
      {modules}
    </form>
    {results}
  </div>
  {footer}
  {get_consent_banner_html()}
  {get_site_header_js()}
  {build_goals_js()}
</body>
</html>'''


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", default=str(OUTPUT_DIR))
    args = parser.parse_args()

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    html_content = generate_goals_page()
    (out_dir / "index.html").write_text(html_content, encoding="utf-8")
    print(f"Wrote {out_dir / 'index.html'} ({len(html_content):,} bytes)")


if __name__ == "__main__":
    main()
