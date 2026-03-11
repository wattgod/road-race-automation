#!/usr/bin/env python3
"""
Generate a standalone race finder quiz page.

Creates /race/quiz/index.html with a multi-step questionnaire that
recommends matching gravel races based on user preferences. Results
are email-gated for lead capture.

Targets queries like "which gravel race should I do", "best gravel
race for beginners", "gravel race finder", "find a gravel race".

Features:
  - 5-step quiz: difficulty, distance, terrain, location, timing
  - Client-side scoring against all races in race-index.json
  - Email-gated results (top 5 matches)
  - Sharable results URL (?results=slug1,slug2,slug3,slug4,slug5)
  - JSON-LD BreadcrumbList
  - GA4 event tracking per step + completion

Usage:
    python wordpress/generate_quiz.py
"""

import html as html_mod
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from brand_tokens import COLORS, get_font_face_css, get_ga4_head_snippet, get_tokens_css, SITE_BASE_URL
from cookie_consent import get_consent_banner_html

PROJECT_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR = Path(__file__).parent / "output" / "quiz"

FUELING_WORKER_URL = "https://fueling-lead-intake.TODO_ROADLABS_WORKERS.workers.dev"  # TODO: deploy Road Labs workers


def esc(text) -> str:
    return html_mod.escape(str(text)) if text else ""


def load_race_index() -> list:
    """Load the race index JSON."""
    path = PROJECT_ROOT / "web" / "race-index.json"
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data.get("races", data) if isinstance(data, dict) else data


def build_quiz_page(races: list) -> str:
    """Build the complete quiz HTML page."""

    # Pre-compute race data JS array (only fields needed for scoring)
    race_js_items = []
    for r in races:
        slug = r.get("slug", "")
        name = r.get("name", "")
        tier = r.get("tier", 4)
        score = r.get("final_score", 0)
        location = r.get("location", "")
        state = r.get("state", "")
        region = r.get("region", "")
        country = r.get("country", "US")
        distance_mi = r.get("distance_mi", 0) or 0
        elevation_ft = r.get("elevation_ft", 0) or 0
        month_num = r.get("month_num", 0) or 0
        difficulty = r.get("difficulty_composite", 0) or 0
        technicality = r.get("technicality", 0) or 0
        terrain = r.get("terrain_primary", "")
        discipline = r.get("discipline", "gravel")

        race_js_items.append(
            f'{{"s":"{esc(slug)}","n":"{esc(name)}","t":{tier},'
            f'"sc":{score},"loc":"{esc(location)}","st":"{esc(state)}",'
            f'"rg":"{esc(region)}","co":"{esc(country)}",'
            f'"dm":{distance_mi},"ef":{elevation_ft},'
            f'"mn":{month_num},"df":{difficulty:.1f},'
            f'"tc":{technicality},"tp":"{esc(terrain)}",'
            f'"di":"{esc(discipline)}"}}'
        )

    races_json = "[" + ",\n".join(race_js_items) + "]"

    tokens_css = get_tokens_css()
    font_css = get_font_face_css("/race/assets/fonts")

    breadcrumb_jsonld = json.dumps({
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Home", "item": SITE_BASE_URL},
            {"@type": "ListItem", "position": 2, "name": "Gravel Races", "item": f"{SITE_BASE_URL}/gravel-races/"},
            {"@type": "ListItem", "position": 3, "name": "Race Finder Quiz", "item": f"{SITE_BASE_URL}/race/quiz/"},
        ]
    })

    race_count = len(races)
    faq_jsonld = json.dumps({
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": [
            {
                "@type": "Question",
                "name": "How does the Road Labs race finder quiz work?",
                "acceptedAnswer": {
                    "@type": "Answer",
                    "text": f"The quiz asks 5 questions about your fitness level, preferred distance, terrain type, location, and timing. It then scores all {race_count} gravel races in our database and recommends your top 5 matches."
                }
            },
            {
                "@type": "Question",
                "name": "How many gravel races are in the database?",
                "acceptedAnswer": {
                    "@type": "Answer",
                    "text": f"The Road Labs database includes {race_count} gravel races across the United States, each rated on 15 dimensions including difficulty, technicality, elevation, logistics, and more."
                }
            },
            {
                "@type": "Question",
                "name": "What gravel race should a beginner do?",
                "acceptedAnswer": {
                    "@type": "Answer",
                    "text": "Select 'Easy Going' for difficulty and 'Short' for distance in our quiz. The algorithm will match you with beginner-friendly events under 60 miles with manageable terrain and elevation."
                }
            },
            {
                "@type": "Question",
                "name": "What is the hardest gravel race?",
                "acceptedAnswer": {
                    "@type": "Answer",
                    "text": "Select 'Brutal' difficulty in the quiz to find the hardest gravel races. Top results typically include Unbound Gravel 200, SBT GRVL, and Mid South 100 — all Tier 1 events with extreme difficulty ratings."
                }
            }
        ]
    })

    return f'''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Race Finder Quiz — Which Gravel Race Should You Do? | Road Labs</title>
  <meta name="description" content="Answer 5 questions to find your perfect gravel race. Personalized recommendations from {race_count} races ranked by the Road Labs rating system.">
  <link rel="canonical" href="{SITE_BASE_URL}/race/quiz/">
  <meta property="og:title" content="Race Finder Quiz — Which Gravel Race Should You Do?">
  <meta property="og:description" content="Answer 5 questions to find your perfect gravel race from {race_count} options.">
  <meta property="og:url" content="{SITE_BASE_URL}/race/quiz/">
  <meta property="og:type" content="website">
  <meta property="og:site_name" content="Road Labs">
  <script type="application/ld+json">{breadcrumb_jsonld}</script>
  <script type="application/ld+json">{faq_jsonld}</script>
  <style>
{font_css}
{tokens_css}
{build_quiz_css()}
  </style>
  {get_ga4_head_snippet()}
</head>
<body>
<div class="rl-quiz-page">
  <header class="rl-quiz-header">
    <a href="/gravel-races/" class="rl-quiz-back">&larr; All Races</a>
    <div class="rl-quiz-badge">RACE FINDER</div>
    <h1 class="rl-quiz-title">Which Gravel Race<br>Should You Do?</h1>
    <p class="rl-quiz-subtitle">5 questions. 328 races. Your perfect match.</p>
  </header>

  <div class="rl-quiz-progress" id="rl-quiz-progress">
    <div class="rl-quiz-progress-bar" id="rl-quiz-progress-bar" style="width:0%"></div>
  </div>

  <!-- Step 1: Difficulty -->
  <div class="rl-quiz-step" data-step="1">
    <div class="rl-quiz-step-num">01</div>
    <h2 class="rl-quiz-question">How hard do you want it?</h2>
    <p class="rl-quiz-hint">Think about your fitness level and how much you want to suffer.</p>
    <div class="rl-quiz-options">
      <button class="rl-quiz-option" data-field="difficulty" data-value="easy">
        <span class="rl-quiz-option-label">EASY GOING</span>
        <span class="rl-quiz-option-desc">Under 60 miles, manageable climbing. Great for first-timers.</span>
      </button>
      <button class="rl-quiz-option" data-field="difficulty" data-value="moderate">
        <span class="rl-quiz-option-label">MODERATE</span>
        <span class="rl-quiz-option-desc">60-100 miles, solid climbing. You train regularly.</span>
      </button>
      <button class="rl-quiz-option" data-field="difficulty" data-value="hard">
        <span class="rl-quiz-option-label">HARD</span>
        <span class="rl-quiz-option-desc">100+ miles or serious elevation. You&rsquo;re fit and motivated.</span>
      </button>
      <button class="rl-quiz-option" data-field="difficulty" data-value="brutal">
        <span class="rl-quiz-option-label">BRUTAL</span>
        <span class="rl-quiz-option-desc">The hardest races on earth. You live for Type 2 fun.</span>
      </button>
    </div>
  </div>

  <!-- Step 2: Distance -->
  <div class="rl-quiz-step" data-step="2" style="display:none">
    <div class="rl-quiz-step-num">02</div>
    <h2 class="rl-quiz-question">How far do you want to ride?</h2>
    <p class="rl-quiz-hint">Approximate race distance.</p>
    <div class="rl-quiz-options">
      <button class="rl-quiz-option" data-field="distance" data-value="short">
        <span class="rl-quiz-option-label">SHORT</span>
        <span class="rl-quiz-option-desc">Under 60 miles — a hard day, not an epic.</span>
      </button>
      <button class="rl-quiz-option" data-field="distance" data-value="medium">
        <span class="rl-quiz-option-label">MEDIUM</span>
        <span class="rl-quiz-option-desc">60-100 miles — the classic gravel distance.</span>
      </button>
      <button class="rl-quiz-option" data-field="distance" data-value="long">
        <span class="rl-quiz-option-label">LONG</span>
        <span class="rl-quiz-option-desc">100-150 miles — a proper endurance event.</span>
      </button>
      <button class="rl-quiz-option" data-field="distance" data-value="ultra">
        <span class="rl-quiz-option-label">ULTRA</span>
        <span class="rl-quiz-option-desc">150+ miles — multi-day or dawn-to-dark.</span>
      </button>
    </div>
  </div>

  <!-- Step 3: Terrain -->
  <div class="rl-quiz-step" data-step="3" style="display:none">
    <div class="rl-quiz-step-num">03</div>
    <h2 class="rl-quiz-question">What kind of terrain?</h2>
    <p class="rl-quiz-hint">Your surface preference.</p>
    <div class="rl-quiz-options">
      <button class="rl-quiz-option" data-field="terrain" data-value="smooth">
        <span class="rl-quiz-option-label">SMOOTH GRAVEL</span>
        <span class="rl-quiz-option-desc">Hardpack dirt roads. Road bike with wide tires works.</span>
      </button>
      <button class="rl-quiz-option" data-field="terrain" data-value="mixed">
        <span class="rl-quiz-option-label">MIXED SURFACE</span>
        <span class="rl-quiz-option-desc">Gravel, pavement, maybe some singletrack. Versatile bike.</span>
      </button>
      <button class="rl-quiz-option" data-field="terrain" data-value="technical">
        <span class="rl-quiz-option-label">TECHNICAL</span>
        <span class="rl-quiz-option-desc">Rough gravel, sand, rocks. Proper gravel or MTB bike.</span>
      </button>
      <button class="rl-quiz-option" data-field="terrain" data-value="any">
        <span class="rl-quiz-option-label">ANYTHING</span>
        <span class="rl-quiz-option-desc">Surprise me. I&rsquo;ll ride whatever&rsquo;s under my tires.</span>
      </button>
    </div>
  </div>

  <!-- Step 4: Location -->
  <div class="rl-quiz-step" data-step="4" style="display:none">
    <div class="rl-quiz-step-num">04</div>
    <h2 class="rl-quiz-question">Where do you want to race?</h2>
    <p class="rl-quiz-hint">Region preference. Races can be worth traveling for.</p>
    <div class="rl-quiz-options">
      <button class="rl-quiz-option" data-field="region" data-value="west">
        <span class="rl-quiz-option-label">WESTERN US</span>
        <span class="rl-quiz-option-desc">California, Colorado, Oregon, Utah, and more.</span>
      </button>
      <button class="rl-quiz-option" data-field="region" data-value="central">
        <span class="rl-quiz-option-label">CENTRAL US</span>
        <span class="rl-quiz-option-desc">Kansas, Iowa, Texas, and the Midwest heartland.</span>
      </button>
      <button class="rl-quiz-option" data-field="region" data-value="east">
        <span class="rl-quiz-option-label">EASTERN US</span>
        <span class="rl-quiz-option-desc">Vermont, Virginia, North Carolina, and the Northeast.</span>
      </button>
      <button class="rl-quiz-option" data-field="region" data-value="any">
        <span class="rl-quiz-option-label">ANYWHERE</span>
        <span class="rl-quiz-option-desc">Show me the best races regardless of location.</span>
      </button>
    </div>
  </div>

  <!-- Step 5: Timing -->
  <div class="rl-quiz-step" data-step="5" style="display:none">
    <div class="rl-quiz-step-num">05</div>
    <h2 class="rl-quiz-question">When do you want to race?</h2>
    <p class="rl-quiz-hint">Preferred time of year.</p>
    <div class="rl-quiz-options">
      <button class="rl-quiz-option" data-field="timing" data-value="spring">
        <span class="rl-quiz-option-label">SPRING</span>
        <span class="rl-quiz-option-desc">March - May. Early season fitness builder.</span>
      </button>
      <button class="rl-quiz-option" data-field="timing" data-value="summer">
        <span class="rl-quiz-option-label">SUMMER</span>
        <span class="rl-quiz-option-desc">June - August. Peak season, longest days.</span>
      </button>
      <button class="rl-quiz-option" data-field="timing" data-value="fall">
        <span class="rl-quiz-option-label">FALL</span>
        <span class="rl-quiz-option-desc">September - November. Cool weather, peak fitness.</span>
      </button>
      <button class="rl-quiz-option" data-field="timing" data-value="any">
        <span class="rl-quiz-option-label">ANYTIME</span>
        <span class="rl-quiz-option-desc">I&rsquo;ll train for whenever the best race is.</span>
      </button>
    </div>
  </div>

  <!-- Email Gate -->
  <div class="rl-quiz-gate" id="rl-quiz-gate" style="display:none">
    <div class="rl-quiz-gate-badge">YOUR MATCHES ARE READY</div>
    <h2 class="rl-quiz-gate-title">Enter your email to see your top 5 races</h2>
    <p class="rl-quiz-gate-text">We&rsquo;ll also send you the free prep kit for your top match.</p>
    <form class="rl-quiz-gate-form" id="rl-quiz-gate-form" autocomplete="off">
      <input type="hidden" name="source" value="race_quiz">
      <input type="hidden" name="website" value="">
      <div class="rl-quiz-gate-row">
        <input type="email" name="email" required placeholder="your@email.com" class="rl-quiz-gate-input" aria-label="Email">
        <button type="submit" class="rl-quiz-gate-btn">SEE MY RACES</button>
      </div>
    </form>
    <p class="rl-quiz-gate-fine">No spam. Unsubscribe anytime.</p>
  </div>

  <!-- Results -->
  <div class="rl-quiz-results" id="rl-quiz-results" style="display:none">
    <div class="rl-quiz-results-badge">YOUR TOP 5 MATCHES</div>
    <div class="rl-quiz-results-list" id="rl-quiz-results-list"></div>
    <div class="rl-quiz-results-cta">
      <a href="/gravel-races/" class="rl-quiz-btn rl-quiz-btn--secondary">BROWSE ALL 328 RACES</a>
      <button class="rl-quiz-btn" id="rl-quiz-restart">TAKE QUIZ AGAIN</button>
    </div>
  </div>

  <footer class="rl-quiz-footer">
    <p>Powered by the <a href="/gravel-races/">Road Labs</a> rating system &mdash; 328 races, 15 dimensions, zero BS.</p>
  </footer>
</div>

<script>
var RACES={races_json};
var WORKER_URL='{FUELING_WORKER_URL}';
{build_quiz_js()}
</script>
{get_consent_banner_html()}
</body>
</html>'''


def build_quiz_css() -> str:
    """Build CSS for the quiz page."""
    return """
.rl-quiz-page{max-width:640px;margin:0 auto;padding:24px 20px;background:var(--rl-color-cool-white);color:var(--rl-color-near-black);font-family:var(--rl-font-editorial);min-height:100vh}

/* Header */
.rl-quiz-header{text-align:center;padding:32px 0 24px;margin-bottom:24px}
.rl-quiz-back{font-family:var(--rl-font-data);font-size:12px;color:var(--rl-color-signal-red);text-decoration:none;letter-spacing:1px;text-transform:uppercase}
.rl-quiz-back:hover{text-decoration:underline}
.rl-quiz-badge{display:inline-block;font-family:var(--rl-font-data);font-size:11px;font-weight:700;letter-spacing:3px;text-transform:uppercase;background:var(--rl-color-near-black);color:var(--rl-color-cool-white);padding:4px 12px;margin:16px 0 12px}
.rl-quiz-title{font-family:var(--rl-font-data);font-size:28px;font-weight:700;text-transform:uppercase;letter-spacing:1px;margin:0 0 8px;color:var(--rl-color-near-black);line-height:1.2}
.rl-quiz-subtitle{font-family:var(--rl-font-data);font-size:13px;color:var(--rl-color-secondary-blue);margin:0;letter-spacing:1px}

/* Progress */
.rl-quiz-progress{height:4px;background:var(--rl-color-silver);margin-bottom:32px}
.rl-quiz-progress-bar{height:100%;background:var(--rl-color-signal-red);transition:width 0.4s ease}

/* Steps */
.rl-quiz-step{margin-bottom:32px;animation:rl-quiz-slide-in 0.3s ease}
.rl-quiz-step-num{font-family:var(--rl-font-data);font-size:13px;font-weight:700;color:var(--rl-color-signal-red);letter-spacing:2px;margin-bottom:8px}
.rl-quiz-question{font-family:var(--rl-font-data);font-size:20px;font-weight:700;text-transform:uppercase;letter-spacing:1px;margin:0 0 8px;color:var(--rl-color-near-black)}
.rl-quiz-hint{font-family:var(--rl-font-editorial);font-size:13px;color:var(--rl-color-secondary-blue);margin:0 0 20px;line-height:1.5}

/* Options */
.rl-quiz-options{display:flex;flex-direction:column;gap:10px}
.rl-quiz-option{display:block;width:100%;text-align:left;padding:16px 20px;border:3px solid var(--rl-color-near-black);background:var(--rl-color-white);cursor:pointer;transition:all 0.15s;font-family:inherit}
.rl-quiz-option:hover{background:var(--rl-color-silver);border-color:var(--rl-color-signal-red)}
.rl-quiz-option.is-selected{background:var(--rl-color-near-black);border-color:var(--rl-color-near-black);color:var(--rl-color-cool-white)}
.rl-quiz-option.is-selected .rl-quiz-option-desc{color:var(--rl-color-silver)}
.rl-quiz-option-label{display:block;font-family:var(--rl-font-data);font-size:14px;font-weight:700;text-transform:uppercase;letter-spacing:2px;margin-bottom:4px}
.rl-quiz-option-desc{display:block;font-family:var(--rl-font-editorial);font-size:12px;color:var(--rl-color-secondary-blue);line-height:1.4}

/* Email gate */
.rl-quiz-gate{text-align:center;padding:40px 20px;border:3px solid var(--rl-color-near-black);background:var(--rl-color-white);margin-bottom:32px;animation:rl-quiz-slide-in 0.3s ease}
.rl-quiz-gate-badge{display:inline-block;font-family:var(--rl-font-data);font-size:11px;font-weight:700;letter-spacing:3px;text-transform:uppercase;background:var(--rl-color-signal-red);color:var(--rl-color-white);padding:4px 12px;margin-bottom:16px}
.rl-quiz-gate-title{font-family:var(--rl-font-data);font-size:18px;font-weight:700;text-transform:uppercase;letter-spacing:1px;margin:0 0 8px;color:var(--rl-color-near-black)}
.rl-quiz-gate-text{font-family:var(--rl-font-editorial);font-size:13px;color:var(--rl-color-secondary-blue);margin:0 0 20px;line-height:1.5}
.rl-quiz-gate-row{display:flex;gap:0;max-width:400px;margin:0 auto 10px}
.rl-quiz-gate-input{flex:1;font-family:var(--rl-font-data);font-size:13px;padding:12px 14px;border:3px solid var(--rl-color-near-black);border-right:none;background:var(--rl-color-cool-white);color:var(--rl-color-near-black);min-width:0}
.rl-quiz-gate-input:focus{outline:none;border-color:var(--rl-color-signal-red)}
.rl-quiz-gate-btn{font-family:var(--rl-font-data);font-size:12px;font-weight:700;text-transform:uppercase;letter-spacing:2px;padding:12px 18px;background:var(--rl-color-near-black);color:var(--rl-color-cool-white);border:3px solid var(--rl-color-near-black);cursor:pointer;white-space:nowrap;transition:background 0.2s}
.rl-quiz-gate-btn:hover{background:var(--rl-color-signal-red);border-color:var(--rl-color-signal-red)}
.rl-quiz-gate-fine{font-family:var(--rl-font-data);font-size:10px;color:var(--rl-color-secondary-blue);letter-spacing:1px;margin:0}

/* Results */
.rl-quiz-results{margin-bottom:32px;animation:rl-quiz-slide-in 0.3s ease}
.rl-quiz-results-badge{display:inline-block;font-family:var(--rl-font-data);font-size:11px;font-weight:700;letter-spacing:3px;text-transform:uppercase;background:var(--rl-color-signal-red);color:var(--rl-color-white);padding:4px 12px;margin-bottom:20px}
.rl-quiz-result-card{display:flex;align-items:center;gap:16px;padding:16px 20px;border:3px solid var(--rl-color-near-black);background:var(--rl-color-white);margin-bottom:10px;text-decoration:none;color:inherit;transition:background 0.15s}
.rl-quiz-result-card:hover{background:var(--rl-color-silver)}
.rl-quiz-result-rank{font-family:var(--rl-font-data);font-size:28px;font-weight:700;color:var(--rl-color-signal-red);min-width:36px;text-align:center}
.rl-quiz-result-info{flex:1}
.rl-quiz-result-name{font-family:var(--rl-font-data);font-size:14px;font-weight:700;text-transform:uppercase;letter-spacing:1px;color:var(--rl-color-near-black);margin:0 0 4px}
.rl-quiz-result-meta{font-family:var(--rl-font-data);font-size:11px;color:var(--rl-color-secondary-blue);letter-spacing:1px}
.rl-quiz-result-score{font-family:var(--rl-font-data);font-size:11px;font-weight:700;color:var(--rl-color-primary-navy);letter-spacing:1px;text-transform:uppercase}
.rl-quiz-result-arrow{font-size:18px;color:var(--rl-color-signal-red)}

/* Buttons */
.rl-quiz-results-cta{display:flex;gap:10px;margin-top:24px}
.rl-quiz-btn{display:inline-block;font-family:var(--rl-font-data);font-size:12px;font-weight:700;text-transform:uppercase;letter-spacing:2px;padding:12px 24px;background:var(--rl-color-near-black);color:var(--rl-color-cool-white);border:3px solid var(--rl-color-near-black);cursor:pointer;text-decoration:none;text-align:center;transition:background 0.2s;flex:1}
.rl-quiz-btn:hover{background:var(--rl-color-signal-red);border-color:var(--rl-color-signal-red)}
.rl-quiz-btn--secondary{background:transparent;color:var(--rl-color-near-black)}
.rl-quiz-btn--secondary:hover{background:var(--rl-color-near-black);color:var(--rl-color-cool-white)}

/* Footer */
.rl-quiz-footer{text-align:center;padding:24px 0;border-top:2px solid var(--rl-color-silver);margin-top:40px}
.rl-quiz-footer p{font-family:var(--rl-font-data);font-size:11px;color:var(--rl-color-secondary-blue);letter-spacing:1px;margin:0}
.rl-quiz-footer a{color:var(--rl-color-signal-red);text-decoration:underline}

/* Animation */
@keyframes rl-quiz-slide-in{from{opacity:0;transform:translateY(16px)}to{opacity:1;transform:translateY(0)}}

/* Responsive */
@media (max-width:600px){
  .rl-quiz-title{font-size:22px}
  .rl-quiz-gate-row{flex-direction:column;gap:8px}
  .rl-quiz-gate-input{border-right:3px solid var(--rl-color-near-black)}
  .rl-quiz-results-cta{flex-direction:column}
  .rl-quiz-result-card{gap:12px;padding:12px 16px}
}
"""


def build_quiz_js() -> str:
    """Build JS for the quiz interactions."""
    return """
(function(){
  var answers={};
  var currentStep=1;
  var totalSteps=5;

  /* Score a race against user answers */
  function scoreRace(r,ans){
    var s=0;
    /* Only score gravel races */
    if(r.di!=='gravel') return -999;

    /* Difficulty match */
    if(ans.difficulty){
      var df=r.df||2.5;
      if(ans.difficulty==='easy') s+=(df<=2)?20:(df<=3)?10:0;
      else if(ans.difficulty==='moderate') s+=(df>2&&df<=3.5)?20:(df>1.5&&df<=4)?10:0;
      else if(ans.difficulty==='hard') s+=(df>3&&df<=4.5)?20:(df>2.5)?10:0;
      else if(ans.difficulty==='brutal') s+=(df>4)?20:(df>3.5)?10:0;
    }

    /* Distance match */
    if(ans.distance){
      var dm=r.dm||0;
      if(ans.distance==='short') s+=(dm>0&&dm<60)?15:(dm<80)?8:0;
      else if(ans.distance==='medium') s+=(dm>=60&&dm<=100)?15:(dm>=40&&dm<=120)?8:0;
      else if(ans.distance==='long') s+=(dm>100&&dm<=150)?15:(dm>80&&dm<=180)?8:0;
      else if(ans.distance==='ultra') s+=(dm>150)?15:(dm>120)?8:0;
    }

    /* Terrain match */
    if(ans.terrain&&ans.terrain!=='any'){
      var tc=r.tc||2;
      if(ans.terrain==='smooth') s+=(tc<=2)?12:(tc<=3)?6:0;
      else if(ans.terrain==='mixed') s+=(tc>=2&&tc<=3)?12:(tc>=1&&tc<=4)?6:0;
      else if(ans.terrain==='technical') s+=(tc>=4)?12:(tc>=3)?6:0;
    } else if(ans.terrain==='any') s+=6;

    /* Region match */
    if(ans.region&&ans.region!=='any'){
      var rg=(r.rg||'').toLowerCase();
      var st=(r.st||'').toLowerCase();
      var west=['west','california','colorado','oregon','utah','washington','montana','idaho','arizona','nevada','wyoming','new mexico'];
      var central=['midwest','south','kansas','iowa','texas','arkansas','oklahoma','nebraska','missouri','minnesota','wisconsin','illinois','indiana','ohio','michigan','tennessee','alabama','georgia','mississippi','louisiana','kentucky'];
      var east=['northeast','virginia','north carolina','vermont','new york','pennsylvania','maryland','connecticut','massachusetts','maine','new hampshire','south carolina','florida','new jersey','delaware','west virginia'];
      if(ans.region==='west') s+=(west.some(function(w){return rg.indexOf(w)>=0||st.indexOf(w)>=0}))?10:0;
      else if(ans.region==='central') s+=(central.some(function(w){return rg.indexOf(w)>=0||st.indexOf(w)>=0}))?10:0;
      else if(ans.region==='east') s+=(east.some(function(w){return rg.indexOf(w)>=0||st.indexOf(w)>=0}))?10:0;
    } else if(ans.region==='any') s+=5;

    /* Timing match */
    if(ans.timing&&ans.timing!=='any'){
      var mn=r.mn||0;
      if(ans.timing==='spring') s+=(mn>=3&&mn<=5)?10:(mn===2||mn===6)?5:0;
      else if(ans.timing==='summer') s+=(mn>=6&&mn<=8)?10:(mn===5||mn===9)?5:0;
      else if(ans.timing==='fall') s+=(mn>=9&&mn<=11)?10:(mn===8||mn===12)?5:0;
    } else if(ans.timing==='any') s+=5;

    /* Bonus for higher-tier races */
    if(r.t===1) s+=5;
    else if(r.t===2) s+=3;

    /* Tiebreaker: overall score */
    s+=r.sc/20;

    return s;
  }

  function showStep(n){
    document.querySelectorAll('.rl-quiz-step').forEach(function(el){
      el.style.display=(parseInt(el.getAttribute('data-step'))===n)?'block':'none';
    });
    var pct=((n-1)/totalSteps)*100;
    document.getElementById('rl-quiz-progress-bar').style.width=pct+'%';
    if(typeof gtag==='function') gtag('event','quiz_step',{step:n});
  }

  function showResults(top5){
    document.getElementById('rl-quiz-gate').style.display='none';
    document.getElementById('rl-quiz-results').style.display='block';
    document.getElementById('rl-quiz-progress-bar').style.width='100%';
    var list=document.getElementById('rl-quiz-results-list');
    list.innerHTML='';
    top5.forEach(function(r,i){
      var tier=['','ELITE','CONTENDER','SOLID','ROSTER'][r.t]||'';
      var card=document.createElement('a');
      card.href='/race/'+r.s+'/';
      card.className='rl-quiz-result-card';
      card.innerHTML='<span class="rl-quiz-result-rank">'+(i+1)+'</span>'
        +'<div class="rl-quiz-result-info">'
        +'<div class="rl-quiz-result-name">'+r.n+'</div>'
        +'<div class="rl-quiz-result-meta">'+r.loc+(r.dm?' &middot; '+r.dm+' mi':'')+'</div>'
        +'</div>'
        +'<span class="rl-quiz-result-score">'+tier+'</span>'
        +'<span class="rl-quiz-result-arrow">&rarr;</span>';
      list.appendChild(card);
    });

    /* Update URL for sharing */
    var slugs=top5.map(function(r){return r.s;}).join(',');
    history.replaceState(null,'',window.location.pathname+'?results='+slugs);

    if(typeof gtag==='function') gtag('event','quiz_complete',{top_race:top5[0]?top5[0].s:''});
  }

  function computeAndGate(){
    /* Score all races */
    var scored=RACES.map(function(r){return{race:r,score:scoreRace(r,answers)};});
    scored.sort(function(a,b){return b.score-a.score;});
    var top5=scored.slice(0,5).map(function(s){return s.race;});

    /* Check if already has email cached */
    var LS_KEY='rl-pk-fueling';
    try{
      var cached=JSON.parse(localStorage.getItem(LS_KEY)||'null');
      if(cached&&cached.email&&cached.exp>Date.now()){
        showResults(top5);
        return;
      }
    }catch(e){}

    /* Show email gate */
    document.querySelectorAll('.rl-quiz-step').forEach(function(el){el.style.display='none';});
    document.getElementById('rl-quiz-gate').style.display='block';
    document.getElementById('rl-quiz-progress-bar').style.width='100%';

    var gateForm=document.getElementById('rl-quiz-gate-form');
    gateForm.addEventListener('submit',function(ev){
      ev.preventDefault();
      var email=gateForm.email.value.trim();
      if(!email||!/^[^\\s@]+@[^\\s@]+\\.[^\\s@]+$/.test(email)){alert('Please enter a valid email.');return;}
      if(gateForm.website&&gateForm.website.value) return;
      /* Cache */
      try{localStorage.setItem(LS_KEY,JSON.stringify({email:email,exp:Date.now()+90*86400000}));}catch(ex){}
      /* POST */
      var payload={email:email,source:'race_quiz',race_slug:top5[0]?top5[0].s:'',race_name:top5[0]?top5[0].n:'',website:gateForm.website.value};
      fetch(WORKER_URL,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)}).catch(function(){});
      if(typeof gtag==='function') gtag('event','email_capture',{source:'race_quiz'});
      showResults(top5);
    });
  }

  /* Option click handlers */
  document.querySelectorAll('.rl-quiz-option').forEach(function(btn){
    btn.addEventListener('click',function(){
      var step=this.closest('.rl-quiz-step');
      var field=this.getAttribute('data-field');
      var value=this.getAttribute('data-value');
      answers[field]=value;

      /* Visual selection */
      step.querySelectorAll('.rl-quiz-option').forEach(function(o){o.classList.remove('is-selected');});
      this.classList.add('is-selected');

      /* Advance after brief delay */
      setTimeout(function(){
        currentStep++;
        if(currentStep>totalSteps){
          computeAndGate();
        }else{
          showStep(currentStep);
        }
      },300);
    });
  });

  /* Restart */
  document.getElementById('rl-quiz-restart').addEventListener('click',function(){
    answers={};
    currentStep=1;
    document.getElementById('rl-quiz-results').style.display='none';
    document.getElementById('rl-quiz-gate').style.display='none';
    document.querySelectorAll('.rl-quiz-option').forEach(function(o){o.classList.remove('is-selected');});
    showStep(1);
    history.replaceState(null,'',window.location.pathname);
  });

  /* Check for shared results URL — still requires email gate */
  var params=new URLSearchParams(window.location.search);
  var resultSlugs=params.get('results');
  if(resultSlugs){
    var slugArr=resultSlugs.split(',');
    var matched=[];
    slugArr.forEach(function(slug){
      var found=RACES.find(function(r){return r.s===slug;});
      if(found) matched.push(found);
    });
    if(matched.length>0){
      /* Check if email is cached — if yes, show results directly */
      var hasCachedEmail=false;
      try{
        var cached=JSON.parse(localStorage.getItem('rl-pk-fueling')||'null');
        if(cached&&cached.email&&cached.exp>Date.now()) hasCachedEmail=true;
      }catch(e){}
      document.querySelectorAll('.rl-quiz-step').forEach(function(el){el.style.display='none';});
      document.querySelector('.rl-quiz-header .rl-quiz-subtitle').textContent='Shared results';
      if(hasCachedEmail){
        showResults(matched);
      }else{
        /* Show email gate for shared results too */
        document.getElementById('rl-quiz-gate').style.display='block';
        document.getElementById('rl-quiz-progress-bar').style.width='100%';
        var gateForm=document.getElementById('rl-quiz-gate-form');
        gateForm.addEventListener('submit',function(ev){
          ev.preventDefault();
          var email=gateForm.email.value.trim();
          if(!email||!/^[^\\s@]+@[^\\s@]+\\.[^\\s@]+$/.test(email)){alert('Please enter a valid email.');return;}
          if(gateForm.website&&gateForm.website.value) return;
          try{localStorage.setItem('rl-pk-fueling',JSON.stringify({email:email,exp:Date.now()+90*86400000}));}catch(ex){}
          var payload={email:email,source:'quiz_shared',race_slug:matched[0]?matched[0].s:'',race_name:matched[0]?matched[0].n:'',website:gateForm.website.value};
          fetch(WORKER_URL,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)}).catch(function(){});
          if(typeof gtag==='function') gtag('event','email_capture',{source:'quiz_shared'});
          showResults(matched);
        });
      }
    }
  }
})();
"""


def main():
    """Generate the quiz page."""
    races = load_race_index()
    print(f"Loaded {len(races)} races")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    page_html = build_quiz_page(races)

    out_file = OUTPUT_DIR / "index.html"
    out_file.write_text(page_html, encoding="utf-8")
    print(f"Generated: {out_file}")
    print(f"URL: /race/quiz/")


if __name__ == "__main__":
    sys.exit(main())
