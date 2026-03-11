#!/usr/bin/env python3
"""
Generate the Road Labs Coaching Intake Form at /coaching/apply/.

Ports the 12-section athlete questionnaire from the archived
athlete-coaching-system repo. Features:
  - 12 sections: Basic Info, Goals, Fitness, Recovery, Equipment,
    Schedule, Work/Life, Health, Strength, Coaching Prefs, Mental Game, Other
  - Blindspot inference (12 patterns)
  - W/kg calculator with gender-specific categories
  - Progress bar tracking
  - Save/resume via localStorage
  - Google Form hybrid submission (fancy UI → hidden Google Form)
  - GA4 event tracking

Uses brand tokens exclusively — zero hardcoded hex, no border-radius,
no box-shadow, no bounce easing.

Usage:
    python generate_coaching_apply.py
    python generate_coaching_apply.py --output-dir ./output
"""

import argparse
import html
import json
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

# Formsubmit.co endpoint — sends email to this address on submission
FORMSUBMIT_EMAIL = "TODO_ROADLABS_EMAIL"  # TODO: Road Labs contact email
FORMSUBMIT_URL = f"https://formsubmit.co/{FORMSUBMIT_EMAIL}"


def esc(text) -> str:
    """HTML-escape a string."""
    return html.escape(str(text)) if text else ""


# ── Page sections ─────────────────────────────────────────────


def build_nav() -> str:
    return get_site_header_html(active="services") + f'''
  <div class="rl-breadcrumb">
    <a href="{SITE_BASE_URL}/">Home</a>
    <span class="rl-breadcrumb-sep">&rsaquo;</span>
    <a href="{SITE_BASE_URL}/coaching/">Coaching</a>
    <span class="rl-breadcrumb-sep">&rsaquo;</span>
    <span class="rl-breadcrumb-current">Apply</span>
  </div>'''


def build_header() -> str:
    return '''<div class="rl-apply-header">
    <div class="rl-apply-badge">Athlete Intake</div>
    <h1>Let&#39;s Get Started</h1>
    <p>This questionnaire helps me understand you as an athlete. The more detail you provide, the better I can tailor your coaching. Takes about 15 minutes.</p>
  </div>'''


def build_progress_bar() -> str:
    return '''<div class="rl-apply-progress">
    <div class="rl-apply-progress-bar">
      <div class="rl-apply-progress-fill" id="progress-fill"></div>
    </div>
    <div class="rl-apply-progress-text" id="progress-text">0% complete</div>
  </div>'''


def build_section_1_basic_info() -> str:
    return '''<div class="rl-apply-section-title">1. Basic Info</div>

      <div class="rl-apply-inline">
        <div class="rl-apply-group">
          <label class="rl-apply-label" for="name">Full Name <span class="rl-apply-required">*</span></label>
          <input type="text" id="name" name="name" required placeholder="First Last">
        </div>
        <div class="rl-apply-group">
          <label class="rl-apply-label" for="email">Email <span class="rl-apply-required">*</span></label>
          <input type="email" id="email" name="email" required placeholder="you@email.com">
        </div>
      </div>

      <div class="rl-apply-inline-4">
        <div class="rl-apply-group">
          <label class="rl-apply-label" for="sex">Sex <span class="rl-apply-required">*</span></label>
          <select id="sex" name="sex" required>
            <option value="">Select</option>
            <option value="male">Male</option>
            <option value="female">Female</option>
          </select>
        </div>
        <div class="rl-apply-group">
          <label class="rl-apply-label" for="age">Age <span class="rl-apply-required">*</span></label>
          <input type="number" id="age" name="age" required placeholder="35" min="16" max="90">
        </div>
        <div class="rl-apply-group">
          <label class="rl-apply-label" for="weight">Weight <span class="rl-apply-required">*</span></label>
          <div class="rl-apply-unit-wrap">
            <input type="number" id="weight" name="weight" required placeholder="165" min="80" max="350">
            <span class="rl-apply-unit">lbs</span>
          </div>
        </div>
        <div class="rl-apply-group">
          <label class="rl-apply-label">Height <span class="rl-apply-required">*</span></label>
          <div class="rl-apply-unit-wrap">
            <input type="number" id="height_ft" name="height_ft" required placeholder="5" min="4" max="7" style="width:50px">
            <span class="rl-apply-unit">&#39;</span>
            <input type="number" id="height_in" name="height_in" required placeholder="10" min="0" max="11" style="width:50px">
            <span class="rl-apply-unit">&#34;</span>
          </div>
        </div>
      </div>'''


def build_section_2_goals() -> str:
    return '''<div class="rl-apply-section-title">2. Goals</div>
      <p class="rl-apply-section-help">What are you training for? This shapes everything.</p>

      <div class="rl-apply-group">
        <label class="rl-apply-label">I&#39;m training for... <span class="rl-apply-required">*</span></label>
        <div class="rl-apply-radio-group">
          <label class="rl-apply-radio-option">
            <input type="radio" name="primary_goal" value="specific_race" required>
            <div class="rl-apply-radio-label">
              <div class="rl-apply-radio-title">Specific Race(s)</div>
              <div class="rl-apply-radio-desc">I have target events with dates</div>
            </div>
          </label>
          <label class="rl-apply-radio-option">
            <input type="radio" name="primary_goal" value="general_fitness">
            <div class="rl-apply-radio-label">
              <div class="rl-apply-radio-title">General Fitness</div>
              <div class="rl-apply-radio-desc">Get faster, no specific race</div>
            </div>
          </label>
          <label class="rl-apply-radio-option">
            <input type="radio" name="primary_goal" value="base_building">
            <div class="rl-apply-radio-label">
              <div class="rl-apply-radio-title">Base Building</div>
              <div class="rl-apply-radio-desc">Building aerobic foundation</div>
            </div>
          </label>
          <label class="rl-apply-radio-option">
            <input type="radio" name="primary_goal" value="return_from_injury">
            <div class="rl-apply-radio-label">
              <div class="rl-apply-radio-title">Return from Injury</div>
              <div class="rl-apply-radio-desc">Rebuilding after time off</div>
            </div>
          </label>
        </div>
      </div>

      <div id="race-details" class="rl-apply-conditional">
        <div class="rl-apply-group">
          <label class="rl-apply-label" for="race_list">List your race(s) <span class="rl-apply-required">*</span></label>
          <textarea id="race_list" name="race_list" placeholder="e.g., Unbound 200 (June 7, 2026) - A priority&#10;Mid South (March 14, 2026) - B priority&#10;Local gravel race (April 5) - C priority" rows="3"></textarea>
          <div class="rl-apply-help">Include name, date, and priority (A = main goal, B = important, C = fun/training)</div>
        </div>
        <div class="rl-apply-group">
          <label class="rl-apply-label" for="success_definition">What does success look like? <span class="rl-apply-required">*</span></label>
          <textarea id="success_definition" name="success_definition" placeholder="e.g., Finish Unbound under 14 hours, top 25% in age group, feel strong in final 50 miles" rows="2"></textarea>
        </div>
      </div>

      <div class="rl-apply-group">
        <label class="rl-apply-label" for="obstacles">What holds you back from your goals?</label>
        <textarea id="obstacles" name="obstacles" placeholder="e.g., Inconsistent training, poor fueling, fade in long events, time management" rows="2"></textarea>
        <div class="rl-apply-help">Be honest - this helps me address real issues</div>
      </div>'''


def build_section_3_fitness() -> str:
    return '''<div class="rl-apply-section-title">3. Current Fitness</div>
      <p class="rl-apply-section-help">Where you&#39;re starting from. Estimates are fine if you don&#39;t know exact numbers.</p>

      <div class="rl-apply-inline">
        <div class="rl-apply-group">
          <label class="rl-apply-label" for="years_cycling">Years Cycling <span class="rl-apply-required">*</span></label>
          <select id="years_cycling" name="years_cycling" required>
            <option value="">Select...</option>
            <option value="0-1">Less than 1 year</option>
            <option value="1-3">1-3 years</option>
            <option value="3-5">3-5 years</option>
            <option value="5-10">5-10 years</option>
            <option value="10+">10+ years</option>
          </select>
        </div>
        <div class="rl-apply-group">
          <label class="rl-apply-label" for="years_structured">Years Structured Training</label>
          <select id="years_structured" name="years_structured">
            <option value="">Select...</option>
            <option value="0">None</option>
            <option value="1">1 year</option>
            <option value="2-3">2-3 years</option>
            <option value="4+">4+ years</option>
          </select>
        </div>
      </div>

      <div class="rl-apply-group">
        <label class="rl-apply-label">Longest Ride in Last 4 Weeks <span class="rl-apply-required">*</span></label>
        <div class="rl-apply-radio-group rl-apply-radio-horizontal">
          <label class="rl-apply-radio-option">
            <input type="radio" name="longest_ride" value="under-2" required>
            <div class="rl-apply-radio-label"><div class="rl-apply-radio-title">&lt; 2 hrs</div></div>
          </label>
          <label class="rl-apply-radio-option">
            <input type="radio" name="longest_ride" value="2-4">
            <div class="rl-apply-radio-label"><div class="rl-apply-radio-title">2-4 hrs</div></div>
          </label>
          <label class="rl-apply-radio-option">
            <input type="radio" name="longest_ride" value="4-6">
            <div class="rl-apply-radio-label"><div class="rl-apply-radio-title">4-6 hrs</div></div>
          </label>
          <label class="rl-apply-radio-option">
            <input type="radio" name="longest_ride" value="6+">
            <div class="rl-apply-radio-label"><div class="rl-apply-radio-title">6+ hrs</div></div>
          </label>
        </div>
      </div>

      <div class="rl-apply-group">
        <label class="rl-apply-label">Power &amp; Heart Rate <span class="rl-apply-optional">(if known)</span></label>
        <div class="rl-apply-inline-4" style="margin-top:8px">
          <div class="rl-apply-group" style="margin-bottom:0">
            <div class="rl-apply-unit-wrap">
              <input type="number" id="ftp" name="ftp" placeholder="FTP" min="50" max="500">
              <span class="rl-apply-unit">W</span>
            </div>
          </div>
          <div class="rl-apply-group" style="margin-bottom:0">
            <div class="rl-apply-unit-wrap">
              <input type="number" id="hr_max" name="hr_max" placeholder="Max" min="120" max="220">
              <span class="rl-apply-unit">bpm</span>
            </div>
          </div>
          <div class="rl-apply-group" style="margin-bottom:0">
            <div class="rl-apply-unit-wrap">
              <input type="number" id="hr_threshold" name="hr_threshold" placeholder="LTHR" min="100" max="200">
              <span class="rl-apply-unit">bpm</span>
            </div>
          </div>
          <div class="rl-apply-group" style="margin-bottom:0">
            <div class="rl-apply-unit-wrap">
              <input type="number" id="hr_resting" name="hr_resting" placeholder="Rest" min="30" max="100">
              <span class="rl-apply-unit">bpm</span>
            </div>
          </div>
        </div>
        <div id="calc-display" class="rl-apply-calc hidden">
          <div class="rl-apply-calc-row">
            <span class="rl-apply-calc-label">Power-to-Weight:</span>
            <span class="rl-apply-calc-value rl-apply-calc-highlight" id="calc-wpkg">-</span>
          </div>
          <div class="rl-apply-calc-row">
            <span class="rl-apply-calc-label">Estimated Category:</span>
            <span class="rl-apply-calc-value" id="calc-category">-</span>
          </div>
        </div>
      </div>

      <div class="rl-apply-group">
        <label class="rl-apply-label" for="strengths">Your Strengths</label>
        <textarea id="strengths" name="strengths" placeholder="e.g., Climbing, mental toughness, consistency, technical skills" rows="2"></textarea>
      </div>

      <div class="rl-apply-group">
        <label class="rl-apply-label" for="weaknesses">Your Weaknesses</label>
        <textarea id="weaknesses" name="weaknesses" placeholder="e.g., Sprinting, time trials, heat tolerance, nutrition on the bike" rows="2"></textarea>
      </div>'''


def build_section_4_recovery() -> str:
    return '''<div class="rl-apply-section-title">4. Recovery &amp; Baselines</div>
      <p class="rl-apply-section-help">These establish your personal baselines for monitoring recovery and readiness.</p>

      <div class="rl-apply-inline-3">
        <div class="rl-apply-group">
          <label class="rl-apply-label" for="rhr_baseline">Resting HR <span class="rl-apply-required">*</span></label>
          <div class="rl-apply-unit-wrap">
            <input type="number" id="rhr_baseline" name="rhr_baseline" required placeholder="55" min="30" max="100">
            <span class="rl-apply-unit">bpm</span>
          </div>
          <div class="rl-apply-help">Morning, before getting up</div>
        </div>
        <div class="rl-apply-group">
          <label class="rl-apply-label" for="sleep_hours_baseline">Typical Sleep <span class="rl-apply-required">*</span></label>
          <div class="rl-apply-unit-wrap">
            <input type="number" id="sleep_hours_baseline" name="sleep_hours_baseline" required placeholder="7" min="4" max="12" step="0.5">
            <span class="rl-apply-unit">hrs</span>
          </div>
          <div class="rl-apply-help">Average per night</div>
        </div>
        <div class="rl-apply-group">
          <label class="rl-apply-label" for="hrv_baseline">HRV <span class="rl-apply-optional">(if known)</span></label>
          <div class="rl-apply-unit-wrap">
            <input type="number" id="hrv_baseline" name="hrv_baseline" placeholder="45" min="10" max="200">
            <span class="rl-apply-unit">ms</span>
          </div>
          <div class="rl-apply-help">RMSSD from WHOOP/Garmin</div>
        </div>
      </div>

      <div class="rl-apply-group">
        <label class="rl-apply-label" for="sleep_quality">Sleep Quality <span class="rl-apply-required">*</span></label>
        <select id="sleep_quality" name="sleep_quality" required>
          <option value="">Select...</option>
          <option value="excellent">Excellent - 7-9 hrs, wake refreshed</option>
          <option value="good">Good - 6-7 hrs, mostly rested</option>
          <option value="fair">Fair - 5-6 hrs, often tired</option>
          <option value="poor">Poor - &lt; 5 hrs, always tired</option>
        </select>
      </div>

      <div class="rl-apply-group">
        <label class="rl-apply-label">Recovery Speed <span class="rl-apply-required">*</span></label>
        <div class="rl-apply-radio-group">
          <label class="rl-apply-radio-option">
            <input type="radio" name="recovery_speed" value="fast" required>
            <div class="rl-apply-radio-label">
              <div class="rl-apply-radio-title">Fast</div>
              <div class="rl-apply-radio-desc">Bounce back quickly, can handle back-to-back hard days</div>
            </div>
          </label>
          <label class="rl-apply-radio-option">
            <input type="radio" name="recovery_speed" value="normal">
            <div class="rl-apply-radio-label">
              <div class="rl-apply-radio-title">Normal</div>
              <div class="rl-apply-radio-desc">Need a day to recover from hard efforts</div>
            </div>
          </label>
          <label class="rl-apply-radio-option">
            <input type="radio" name="recovery_speed" value="slow">
            <div class="rl-apply-radio-label">
              <div class="rl-apply-radio-title">Slow</div>
              <div class="rl-apply-radio-desc">Need 2+ days to fully recover, older athlete or high life stress</div>
            </div>
          </label>
        </div>
      </div>

      <div class="rl-apply-group">
        <label class="rl-apply-label" for="overtraining_history">History of overtraining or burnout?</label>
        <select id="overtraining_history" name="overtraining_history">
          <option value="">Select...</option>
          <option value="never">Never</option>
          <option value="once">Yes, once</option>
          <option value="multiple">Yes, multiple times</option>
          <option value="currently">Currently dealing with it</option>
        </select>
      </div>'''


def build_section_5_equipment() -> str:
    return '''<div class="rl-apply-section-title">5. Equipment &amp; Data</div>
      <p class="rl-apply-section-help">What devices and platforms do you use? This enables automatic data sync.</p>

      <div class="rl-apply-group">
        <label class="rl-apply-label">Wearables &amp; Devices</label>
        <div class="rl-apply-checkbox-group rl-apply-checkbox-vertical">
          <label class="rl-apply-checkbox-option">
            <input type="checkbox" name="devices" value="whoop">
            <div class="rl-apply-checkbox-label">WHOOP <span class="rl-apply-checkbox-desc">- Enables HRV/recovery sync</span></div>
          </label>
          <label class="rl-apply-checkbox-option">
            <input type="checkbox" name="devices" value="garmin">
            <div class="rl-apply-checkbox-label">Garmin Watch/Head Unit</div>
          </label>
          <label class="rl-apply-checkbox-option">
            <input type="checkbox" name="devices" value="wahoo">
            <div class="rl-apply-checkbox-label">Wahoo Head Unit</div>
          </label>
          <label class="rl-apply-checkbox-option">
            <input type="checkbox" name="devices" value="power_meter">
            <div class="rl-apply-checkbox-label">Power Meter (on bike)</div>
          </label>
          <label class="rl-apply-checkbox-option">
            <input type="checkbox" name="devices" value="smart_trainer">
            <div class="rl-apply-checkbox-label">Smart Trainer (Zwift, etc.)</div>
          </label>
          <label class="rl-apply-checkbox-option">
            <input type="checkbox" name="devices" value="hr_strap">
            <div class="rl-apply-checkbox-label">HR Chest Strap</div>
          </label>
        </div>
      </div>

      <div class="rl-apply-group">
        <label class="rl-apply-label">Training Platform <span class="rl-apply-required">*</span></label>
        <select id="training_platform" name="training_platform" required>
          <option value="">Select...</option>
          <option value="intervals_icu">Intervals.icu (recommended - free)</option>
          <option value="trainingpeaks">TrainingPeaks</option>
          <option value="strava_only">Strava only</option>
          <option value="garmin_connect">Garmin Connect</option>
          <option value="other">Other</option>
          <option value="none">None currently</option>
        </select>
      </div>

      <div id="intervals-id-group" class="rl-apply-group rl-apply-conditional">
        <label class="rl-apply-label" for="intervals_athlete_id">Intervals.icu Athlete ID</label>
        <input type="text" id="intervals_athlete_id" name="intervals_athlete_id" placeholder="e.g., i12345 (found in Settings)">
        <div class="rl-apply-help">Found in Intervals.icu &rarr; Settings &rarr; Developer Settings. Use &quot;i0&quot; for your own account.</div>
      </div>

      <div class="rl-apply-inline">
        <div class="rl-apply-group">
          <label class="rl-apply-label" for="trainer_access">Indoor Trainer <span class="rl-apply-required">*</span></label>
          <select id="trainer_access" name="trainer_access" required>
            <option value="">Select...</option>
            <option value="smart">Smart trainer (ERG mode)</option>
            <option value="basic">Basic/dumb trainer</option>
            <option value="none">Outdoor only</option>
          </select>
        </div>
        <div class="rl-apply-group">
          <label class="rl-apply-label" for="indoor_tolerance">Indoor Tolerance</label>
          <select id="indoor_tolerance" name="indoor_tolerance">
            <option value="">Select...</option>
            <option value="love">Love it - prefer trainer</option>
            <option value="tolerate">Tolerate it when needed</option>
            <option value="hate">Hate it - last resort only</option>
          </select>
        </div>
      </div>'''


def build_section_6_schedule() -> str:
    return '''<div class="rl-apply-section-title">6. Schedule</div>
      <p class="rl-apply-section-help">Your real-life constraints. I&#39;ll build around YOUR week.</p>

      <div class="rl-apply-inline">
        <div class="rl-apply-group">
          <label class="rl-apply-label" for="hours_per_week">Weekly Training Hours <span class="rl-apply-required">*</span></label>
          <select id="hours_per_week" name="hours_per_week" required>
            <option value="">Select...</option>
            <option value="3-5">3-5 hours</option>
            <option value="5-7">5-7 hours</option>
            <option value="8-10">8-10 hours</option>
            <option value="10-12">10-12 hours</option>
            <option value="12-15">12-15 hours</option>
            <option value="15+">15+ hours</option>
          </select>
          <div class="rl-apply-help">Realistic weekly commitment</div>
        </div>
        <div class="rl-apply-group">
          <label class="rl-apply-label" for="current_volume">Current Weekly Hours</label>
          <select id="current_volume" name="current_volume">
            <option value="">Select...</option>
            <option value="0-2">0-2 hours</option>
            <option value="3-5">3-5 hours</option>
            <option value="5-7">5-7 hours</option>
            <option value="8-10">8-10 hours</option>
            <option value="10+">10+ hours</option>
          </select>
          <div class="rl-apply-help">What you&#39;re actually doing now</div>
        </div>
      </div>

      <div class="rl-apply-group">
        <label class="rl-apply-label">Best Day(s) for Long Rides <span class="rl-apply-required">*</span></label>
        <div class="rl-apply-help" style="margin-bottom:10px">Select all that work, or choose flexible</div>
        <div class="rl-apply-checkbox-group">
          <label class="rl-apply-checkbox-option rl-apply-flexible-option"><input type="checkbox" name="long_ride_days" value="flexible"> Flexible</label>
          <label class="rl-apply-checkbox-option"><input type="checkbox" name="long_ride_days" value="monday"> Mon</label>
          <label class="rl-apply-checkbox-option"><input type="checkbox" name="long_ride_days" value="tuesday"> Tue</label>
          <label class="rl-apply-checkbox-option"><input type="checkbox" name="long_ride_days" value="wednesday"> Wed</label>
          <label class="rl-apply-checkbox-option"><input type="checkbox" name="long_ride_days" value="thursday"> Thu</label>
          <label class="rl-apply-checkbox-option"><input type="checkbox" name="long_ride_days" value="friday"> Fri</label>
          <label class="rl-apply-checkbox-option"><input type="checkbox" name="long_ride_days" value="saturday"> Sat</label>
          <label class="rl-apply-checkbox-option"><input type="checkbox" name="long_ride_days" value="sunday"> Sun</label>
        </div>
      </div>

      <div class="rl-apply-group">
        <label class="rl-apply-label">Best Day(s) for Hard Intervals <span class="rl-apply-required">*</span></label>
        <div class="rl-apply-help" style="margin-bottom:10px">When do you feel freshest?</div>
        <div class="rl-apply-checkbox-group">
          <label class="rl-apply-checkbox-option rl-apply-flexible-option"><input type="checkbox" name="interval_days" value="flexible"> Flexible</label>
          <label class="rl-apply-checkbox-option"><input type="checkbox" name="interval_days" value="monday"> Mon</label>
          <label class="rl-apply-checkbox-option"><input type="checkbox" name="interval_days" value="tuesday"> Tue</label>
          <label class="rl-apply-checkbox-option"><input type="checkbox" name="interval_days" value="wednesday"> Wed</label>
          <label class="rl-apply-checkbox-option"><input type="checkbox" name="interval_days" value="thursday"> Thu</label>
          <label class="rl-apply-checkbox-option"><input type="checkbox" name="interval_days" value="friday"> Fri</label>
          <label class="rl-apply-checkbox-option"><input type="checkbox" name="interval_days" value="saturday"> Sat</label>
          <label class="rl-apply-checkbox-option"><input type="checkbox" name="interval_days" value="sunday"> Sun</label>
        </div>
      </div>

      <div class="rl-apply-group">
        <label class="rl-apply-label">Required Off Days</label>
        <div class="rl-apply-help" style="margin-bottom:10px">Days you absolutely cannot train</div>
        <div class="rl-apply-checkbox-group">
          <label class="rl-apply-checkbox-option"><input type="checkbox" name="off_days" value="monday"> Mon</label>
          <label class="rl-apply-checkbox-option"><input type="checkbox" name="off_days" value="tuesday"> Tue</label>
          <label class="rl-apply-checkbox-option"><input type="checkbox" name="off_days" value="wednesday"> Wed</label>
          <label class="rl-apply-checkbox-option"><input type="checkbox" name="off_days" value="thursday"> Thu</label>
          <label class="rl-apply-checkbox-option"><input type="checkbox" name="off_days" value="friday"> Fri</label>
          <label class="rl-apply-checkbox-option"><input type="checkbox" name="off_days" value="saturday"> Sat</label>
          <label class="rl-apply-checkbox-option"><input type="checkbox" name="off_days" value="sunday"> Sun</label>
        </div>
      </div>'''


def build_section_7_work_life() -> str:
    return '''<div class="rl-apply-section-title">7. Work &amp; Life</div>
      <p class="rl-apply-section-help">Life context affects training capacity. No judgment.</p>

      <div class="rl-apply-inline">
        <div class="rl-apply-group">
          <label class="rl-apply-label" for="work_hours">Work Hours/Week</label>
          <select id="work_hours" name="work_hours">
            <option value="">Select...</option>
            <option value="0">Not working</option>
            <option value="20">Part-time (~20)</option>
            <option value="40">Full-time (~40)</option>
            <option value="50">Heavy (~50)</option>
            <option value="60+">Intense (60+)</option>
          </select>
        </div>
        <div class="rl-apply-group">
          <label class="rl-apply-label" for="job_stress">Job Stress Level</label>
          <select id="job_stress" name="job_stress">
            <option value="">Select...</option>
            <option value="low">Low - Pretty chill</option>
            <option value="moderate">Moderate - Normal demands</option>
            <option value="high">High - Demanding</option>
            <option value="very_high">Very High - Crushing</option>
          </select>
        </div>
      </div>

      <div class="rl-apply-group">
        <label class="rl-apply-label" for="life_stress">Overall Life Stress <span class="rl-apply-required">*</span></label>
        <select id="life_stress" name="life_stress" required>
          <option value="">Select...</option>
          <option value="low">Low - Life is chill, training is my outlet</option>
          <option value="moderate">Moderate - Normal work/life demands</option>
          <option value="high">High - Demanding job, family obligations</option>
          <option value="very_high">Very High - Barely keeping head above water</option>
        </select>
        <div class="rl-apply-help">Be honest - this affects recovery capacity</div>
      </div>

      <div class="rl-apply-group">
        <label class="rl-apply-label" for="family_situation">Family Situation</label>
        <textarea id="family_situation" name="family_situation" placeholder="e.g., Married, 2 kids (ages 3, 5), partner supportive of training" rows="2"></textarea>
      </div>

      <div class="rl-apply-group">
        <label class="rl-apply-label" for="time_commitments">Other Regular Commitments</label>
        <textarea id="time_commitments" name="time_commitments" placeholder="e.g., Kids&#39; sports 3x/week, volunteer work, travel for work monthly" rows="2"></textarea>
      </div>'''


def build_section_8_health() -> str:
    return '''<div class="rl-apply-section-title">8. Health</div>
      <p class="rl-apply-section-help">Medical history and current limitations.</p>

      <div class="rl-apply-group">
        <label class="rl-apply-label" for="injuries">Current Injuries or Limitations</label>
        <textarea id="injuries" name="injuries" placeholder="e.g., Bad right knee (can&#39;t do deep squats), lower back tightness on long rides" rows="2"></textarea>
      </div>

      <div class="rl-apply-group">
        <label class="rl-apply-label" for="past_injuries">Past Injuries That Still Affect You</label>
        <textarea id="past_injuries" name="past_injuries" placeholder="e.g., ACL surgery 2020 (fully healed but careful with lateral movements)" rows="2"></textarea>
      </div>

      <div class="rl-apply-group">
        <label class="rl-apply-label" for="medical_conditions">Medical Conditions</label>
        <textarea id="medical_conditions" name="medical_conditions" placeholder="e.g., Asthma (well controlled), high blood pressure (on medication)" rows="2"></textarea>
      </div>

      <div class="rl-apply-group">
        <label class="rl-apply-label" for="medications">Medications</label>
        <textarea id="medications" name="medications" placeholder="e.g., Beta blocker for BP (affects HR), daily multivitamin" rows="2"></textarea>
        <div class="rl-apply-help">Include anything that might affect HR or recovery</div>
      </div>'''


def build_section_9_strength() -> str:
    return '''<div class="rl-apply-section-title">9. Strength Training</div>

      <div class="rl-apply-group">
        <label class="rl-apply-label">Current Strength Training <span class="rl-apply-required">*</span></label>
        <div class="rl-apply-radio-group">
          <label class="rl-apply-radio-option">
            <input type="radio" name="strength_current" value="none" required>
            <div class="rl-apply-radio-label">
              <div class="rl-apply-radio-title">None</div>
              <div class="rl-apply-radio-desc">No strength work currently</div>
            </div>
          </label>
          <label class="rl-apply-radio-option">
            <input type="radio" name="strength_current" value="occasional">
            <div class="rl-apply-radio-label">
              <div class="rl-apply-radio-title">Occasional</div>
              <div class="rl-apply-radio-desc">Once a week or less</div>
            </div>
          </label>
          <label class="rl-apply-radio-option">
            <input type="radio" name="strength_current" value="regular">
            <div class="rl-apply-radio-label">
              <div class="rl-apply-radio-title">Regular</div>
              <div class="rl-apply-radio-desc">1-2x per week, consistent</div>
            </div>
          </label>
          <label class="rl-apply-radio-option">
            <input type="radio" name="strength_current" value="dedicated">
            <div class="rl-apply-radio-label">
              <div class="rl-apply-radio-title">Dedicated</div>
              <div class="rl-apply-radio-desc">2-3x per week, structured</div>
            </div>
          </label>
        </div>
      </div>

      <div class="rl-apply-inline">
        <div class="rl-apply-group">
          <label class="rl-apply-label">Include Strength?</label>
          <select id="strength_want" name="strength_want">
            <option value="">Select...</option>
            <option value="yes">Yes - Include strength</option>
            <option value="no">No - Cycling only</option>
            <option value="coach_decides">You decide</option>
          </select>
        </div>
        <div class="rl-apply-group">
          <label class="rl-apply-label">Equipment Access</label>
          <select id="strength_equipment" name="strength_equipment">
            <option value="">Select...</option>
            <option value="full_gym">Full gym</option>
            <option value="home_weights">Home weights (DB/KB)</option>
            <option value="minimal">Minimal (bands/bodyweight)</option>
            <option value="none">None</option>
          </select>
        </div>
      </div>'''


def build_section_10_coaching_prefs() -> str:
    return '''<div class="rl-apply-section-title">10. Coaching Preferences</div>
      <p class="rl-apply-section-help">How do you want to work together?</p>

      <div class="rl-apply-inline">
        <div class="rl-apply-group">
          <label class="rl-apply-label" for="checkin_frequency">Check-in Frequency <span class="rl-apply-required">*</span></label>
          <select id="checkin_frequency" name="checkin_frequency" required>
            <option value="">Select...</option>
            <option value="daily">Daily briefings</option>
            <option value="few_times_week">Few times a week</option>
            <option value="weekly">Weekly summary only</option>
          </select>
        </div>
        <div class="rl-apply-group">
          <label class="rl-apply-label" for="feedback_detail">Feedback Detail <span class="rl-apply-required">*</span></label>
          <select id="feedback_detail" name="feedback_detail" required>
            <option value="">Select...</option>
            <option value="minimal">Minimal - Just tell me what to do</option>
            <option value="moderate">Moderate - Key points only</option>
            <option value="comprehensive">Comprehensive - Explain everything</option>
          </select>
        </div>
      </div>

      <div class="rl-apply-group">
        <label class="rl-apply-label">Autonomy Preference <span class="rl-apply-required">*</span></label>
        <div class="rl-apply-radio-group">
          <label class="rl-apply-radio-option">
            <input type="radio" name="autonomy" value="prescriptive" required>
            <div class="rl-apply-radio-label">
              <div class="rl-apply-radio-title">Tell Me Exactly</div>
              <div class="rl-apply-radio-desc">Precise workouts, I&#39;ll execute as written</div>
            </div>
          </label>
          <label class="rl-apply-radio-option">
            <input type="radio" name="autonomy" value="guided">
            <div class="rl-apply-radio-label">
              <div class="rl-apply-radio-title">General Guidance</div>
              <div class="rl-apply-radio-desc">Goals and guidelines, I&#39;ll adapt to the day</div>
            </div>
          </label>
          <label class="rl-apply-radio-option">
            <input type="radio" name="autonomy" value="high">
            <div class="rl-apply-radio-label">
              <div class="rl-apply-radio-title">High Autonomy</div>
              <div class="rl-apply-radio-desc">Weekly targets, I decide the details</div>
            </div>
          </label>
        </div>
      </div>

      <div class="rl-apply-group">
        <label class="rl-apply-label" for="communication_style">Communication Style</label>
        <select id="communication_style" name="communication_style">
          <option value="">Select...</option>
          <option value="direct">Direct / No-BS</option>
          <option value="encouraging">Encouraging / Supportive</option>
          <option value="data_driven">Data-Driven / Analytical</option>
          <option value="flexible">Mix - You decide</option>
        </select>
      </div>'''


def build_section_11_mental_game() -> str:
    return '''<div class="rl-apply-section-title">11. Mental Game</div>
      <p class="rl-apply-section-help">These help me understand how you tick. Answer honestly.</p>

      <div class="rl-apply-group">
        <label class="rl-apply-label">When you miss a planned workout, what do you usually do? <span class="rl-apply-required">*</span></label>
        <div class="rl-apply-radio-group">
          <label class="rl-apply-radio-option">
            <input type="radio" name="missed_workout_response" value="make_up" required>
            <div class="rl-apply-radio-label">
              <div class="rl-apply-radio-title">Make It Up ASAP</div>
              <div class="rl-apply-radio-desc">Even if it means back-to-back hard days</div>
            </div>
          </label>
          <label class="rl-apply-radio-option">
            <input type="radio" name="missed_workout_response" value="move_on">
            <div class="rl-apply-radio-label">
              <div class="rl-apply-radio-title">Move On</div>
              <div class="rl-apply-radio-desc">Trust the process, one workout won&#39;t matter</div>
            </div>
          </label>
          <label class="rl-apply-radio-option">
            <input type="radio" name="missed_workout_response" value="guilt">
            <div class="rl-apply-radio-label">
              <div class="rl-apply-radio-title">Feel Guilty</div>
              <div class="rl-apply-radio-desc">Beat myself up but eventually let it go</div>
            </div>
          </label>
          <label class="rl-apply-radio-option">
            <input type="radio" name="missed_workout_response" value="spiral">
            <div class="rl-apply-radio-label">
              <div class="rl-apply-radio-title">Spiral</div>
              <div class="rl-apply-radio-desc">Start questioning everything</div>
            </div>
          </label>
        </div>
      </div>

      <div class="rl-apply-group">
        <label class="rl-apply-label" for="best_training_block">Describe your best training period ever. What made it work?</label>
        <textarea id="best_training_block" name="best_training_block" placeholder="e.g., Spring 2024 - consistent schedule, no travel, riding with a group weekly, slept well, wasn&#39;t stressed about work" rows="3"></textarea>
        <div class="rl-apply-help">This reveals your success conditions</div>
      </div>

      <div class="rl-apply-group">
        <label class="rl-apply-label" for="quit_triggers">What would make you quit or lose motivation?</label>
        <textarea id="quit_triggers" name="quit_triggers" placeholder="e.g., Injury, work getting crazy, feeling like I&#39;m not improving, too much time on trainer" rows="2"></textarea>
        <div class="rl-apply-help">Helps me identify risk factors early</div>
      </div>

      <div class="rl-apply-group">
        <label class="rl-apply-label" for="accountability_style">Who knows about your race goal?</label>
        <select id="accountability_style" name="accountability_style">
          <option value="">Select...</option>
          <option value="public">Everyone - Posted on social media</option>
          <option value="friends">Close friends and family</option>
          <option value="private">Just me and my coach</option>
          <option value="secret">Nobody yet</option>
        </select>
        <div class="rl-apply-help">Reveals your accountability style</div>
      </div>'''


def build_section_12_other() -> str:
    return '''<div class="rl-apply-section-title">12. Anything Else</div>

      <div class="rl-apply-group">
        <label class="rl-apply-label" for="previous_coach">Have you worked with a coach before?</label>
        <textarea id="previous_coach" name="previous_coach" placeholder="If yes, what did you like or dislike about the experience?" rows="2"></textarea>
      </div>

      <div class="rl-apply-group">
        <label class="rl-apply-label" for="anything_else">Anything else I should know?</label>
        <textarea id="anything_else" name="anything_else" placeholder="Travel plans, upcoming life changes, specific concerns, questions..." rows="3"></textarea>
      </div>'''


def build_submit_buttons() -> str:
    return '''<div class="rl-apply-actions">
        <button type="button" class="rl-apply-save-btn" id="save-btn">Save Progress</button>
        <button type="submit" class="rl-apply-submit-btn" id="submit-btn">
          Submit Questionnaire
        </button>
      </div>'''


def build_footer() -> str:
    return f'''<div class="rl-apply-confidential-wrap">
    <p class="rl-apply-confidential">Your information is kept confidential and used only for coaching purposes. Questions? Email TODO_ROADLABS_EMAIL</p>
  </div>
  ''' + get_mega_footer_html()


def build_jsonld() -> str:
    """JSON-LD structured data for the application page."""
    data = {
        "@context": "https://schema.org",
        "@type": "WebPage",
        "name": "Coaching Application | Road Labs",
        "description": "Apply for personalized gravel cycling coaching. 12-section athlete intake with blindspot inference.",
        "url": f"{SITE_BASE_URL}/coaching/apply/",
        "isPartOf": {
            "@type": "WebSite",
            "name": "Road Labs",
            "url": f"{SITE_BASE_URL}/",
        },
        "breadcrumb": {
            "@type": "BreadcrumbList",
            "itemListElement": [
                {"@type": "ListItem", "position": 1, "name": "Home", "item": f"{SITE_BASE_URL}/"},
                {"@type": "ListItem", "position": 2, "name": "Coaching", "item": f"{SITE_BASE_URL}/coaching/"},
                {"@type": "ListItem", "position": 3, "name": "Apply"},
            ],
        },
    }
    return f'<script type="application/ld+json">{json.dumps(data, separators=(",", ":"))}</script>'


# ── CSS ────────────────────────────────────────────────────────


def build_apply_css() -> str:
    """Build all CSS for the coaching apply form. All rl-apply-* prefix. Brand tokens only."""
    return '''<style>
/* ── Layout ────────────────────────────────────────── */
.rl-apply-container {
  max-width: 720px;
  margin: 0 auto;
  padding: var(--rl-spacing-3xl) var(--rl-spacing-lg);
}

/* ── Header ────────────────────────────────────────── */
.rl-apply-header {
  text-align: center;
  margin-bottom: var(--rl-spacing-3xl);
}
.rl-apply-badge {
  display: inline-block;
  background: var(--rl-color-light-orange);
  color: var(--rl-color-near-black);
  padding: var(--rl-spacing-xs) var(--rl-spacing-lg);
  font-family: var(--rl-font-data);
  font-size: var(--rl-font-size-2xs);
  font-weight: var(--rl-font-weight-bold);
  text-transform: uppercase;
  letter-spacing: var(--rl-letter-spacing-wider);
  border: 3px solid var(--rl-color-near-black);
  margin-bottom: var(--rl-spacing-lg);
}
.rl-apply-header h1 {
  font-family: var(--rl-font-editorial);
  font-size: var(--rl-font-size-2xl);
  font-weight: var(--rl-font-weight-bold);
  color: var(--rl-color-near-black);
  margin-bottom: var(--rl-spacing-sm);
}
.rl-apply-header p {
  font-family: var(--rl-font-editorial);
  color: var(--rl-color-secondary-blue);
  font-size: var(--rl-font-size-sm);
  max-width: 520px;
  margin: 0 auto;
}

/* ── Progress bar ──────────────────────────────────── */
.rl-apply-progress {
  background: var(--rl-color-white);
  border: 2px solid var(--rl-color-near-black);
  padding: var(--rl-spacing-md) var(--rl-spacing-lg);
  margin-bottom: var(--rl-spacing-lg);
}
.rl-apply-progress-bar {
  height: 8px;
  background: var(--rl-color-silver);
  border: 1px solid var(--rl-color-near-black);
  margin-bottom: var(--rl-spacing-xs);
}
.rl-apply-progress-fill {
  height: 100%;
  background: var(--rl-color-signal-red);
  width: 0%;
  transition: width 0.3s;
}
.rl-apply-progress-text {
  font-family: var(--rl-font-data);
  font-size: var(--rl-font-size-2xs);
  color: var(--rl-color-secondary-blue);
  text-align: center;
}

/* ── Form card ─────────────────────────────────────── */
.rl-apply-form-card {
  background: var(--rl-color-white);
  border: 3px solid var(--rl-color-near-black);
  padding: var(--rl-spacing-xl);
  margin-bottom: var(--rl-spacing-lg);
}

/* ── Section titles ────────────────────────────────── */
.rl-apply-section-title {
  font-family: var(--rl-font-data);
  font-size: var(--rl-font-size-sm);
  font-weight: var(--rl-font-weight-bold);
  text-transform: uppercase;
  letter-spacing: var(--rl-letter-spacing-wide);
  color: var(--rl-color-near-black);
  padding-bottom: var(--rl-spacing-xs);
  border-bottom: 2px solid var(--rl-color-near-black);
  margin-bottom: var(--rl-spacing-lg);
  margin-top: var(--rl-spacing-xl);
}
.rl-apply-section-title:first-of-type {
  margin-top: 0;
}
.rl-apply-section-help {
  font-family: var(--rl-font-editorial);
  font-size: var(--rl-font-size-xs);
  color: var(--rl-color-secondary-blue);
  margin-top: calc(-1 * var(--rl-spacing-md));
  margin-bottom: var(--rl-spacing-lg);
  line-height: 1.5;
}

/* ── Form groups ───────────────────────────────────── */
.rl-apply-group {
  margin-bottom: var(--rl-spacing-lg);
}
.rl-apply-label {
  display: block;
  font-family: var(--rl-font-data);
  font-size: var(--rl-font-size-sm);
  font-weight: var(--rl-font-weight-semibold);
  margin-bottom: var(--rl-spacing-xs);
  color: var(--rl-color-near-black);
}
.rl-apply-required {
  color: var(--rl-color-error);
}
.rl-apply-optional {
  font-weight: var(--rl-font-weight-regular);
  color: var(--rl-color-secondary-blue);
  font-size: var(--rl-font-size-2xs);
}
.rl-apply-help {
  font-family: var(--rl-font-editorial);
  font-size: var(--rl-font-size-2xs);
  color: var(--rl-color-secondary-blue);
  margin-top: var(--rl-spacing-2xs);
}

/* ── Inputs ────────────────────────────────────────── */
.rl-apply-form-card input[type="text"],
.rl-apply-form-card input[type="email"],
.rl-apply-form-card input[type="number"],
.rl-apply-form-card input[type="date"],
.rl-apply-form-card input[type="time"],
.rl-apply-form-card select,
.rl-apply-form-card textarea {
  width: 100%;
  padding: var(--rl-spacing-sm) var(--rl-spacing-sm);
  border: 2px solid var(--rl-color-near-black);
  background: var(--rl-color-white);
  color: var(--rl-color-near-black);
  font-family: var(--rl-font-data);
  font-size: var(--rl-font-size-sm);
  transition: border-color var(--rl-transition-hover);
}
.rl-apply-form-card input:focus,
.rl-apply-form-card select:focus,
.rl-apply-form-card textarea:focus {
  outline: none;
  border-color: var(--rl-color-signal-red);
}
.rl-apply-form-card input.error,
.rl-apply-form-card select.error {
  border-color: var(--rl-color-error);
}
.rl-apply-form-card textarea {
  min-height: 80px;
  resize: vertical;
}
.rl-apply-form-card select {
  cursor: pointer;
  appearance: none;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 12 12'%3E%3Cpath fill='%231a1613' d='M6 8L1 3h10z'/%3E%3C/svg%3E");
  background-repeat: no-repeat;
  background-position: right 12px center;
  padding-right: 36px;
}

/* ── Inline field layouts ──────────────────────────── */
.rl-apply-inline {
  display: flex;
  gap: var(--rl-spacing-md);
}
.rl-apply-inline .rl-apply-group {
  flex: 1;
}
.rl-apply-inline-3 {
  display: flex;
  gap: var(--rl-spacing-sm);
}
.rl-apply-inline-3 .rl-apply-group {
  flex: 1;
}
.rl-apply-inline-4 {
  display: flex;
  gap: var(--rl-spacing-xs);
}
.rl-apply-inline-4 .rl-apply-group {
  flex: 1;
}
.rl-apply-unit-wrap {
  display: flex;
  align-items: center;
  gap: var(--rl-spacing-xs);
}
.rl-apply-unit-wrap input {
  flex: 1;
}
.rl-apply-unit {
  font-family: var(--rl-font-data);
  font-size: var(--rl-font-size-xs);
  color: var(--rl-color-secondary-blue);
  white-space: nowrap;
}

/* ── W/kg calculator display ───────────────────────── */
.rl-apply-calc {
  background: var(--rl-color-silver);
  border: 2px solid var(--rl-color-near-black);
  padding: var(--rl-spacing-sm) var(--rl-spacing-md);
  margin-top: var(--rl-spacing-sm);
  font-family: var(--rl-font-data);
  font-size: var(--rl-font-size-xs);
}
.rl-apply-calc-row {
  display: flex;
  justify-content: space-between;
  margin: var(--rl-spacing-2xs) 0;
}
.rl-apply-calc-label {
  color: var(--rl-color-secondary-blue);
}
.rl-apply-calc-value {
  font-weight: var(--rl-font-weight-bold);
  color: var(--rl-color-near-black);
}
.rl-apply-calc-highlight {
  color: var(--rl-color-signal-red);
}

/* ── Radio groups ──────────────────────────────────── */
.rl-apply-radio-group {
  display: flex;
  flex-direction: column;
  gap: var(--rl-spacing-xs);
}
.rl-apply-radio-horizontal {
  flex-direction: row;
  flex-wrap: wrap;
  gap: var(--rl-spacing-xs);
}
.rl-apply-radio-option {
  display: flex;
  align-items: flex-start;
  gap: var(--rl-spacing-xs);
  padding: var(--rl-spacing-sm) var(--rl-spacing-md);
  border: 2px solid var(--rl-color-near-black);
  cursor: pointer;
  transition: background-color var(--rl-transition-hover), border-color var(--rl-transition-hover);
}
.rl-apply-radio-horizontal .rl-apply-radio-option {
  flex: 1;
  min-width: 100px;
}
.rl-apply-radio-option:hover {
  background-color: var(--rl-color-silver);
}
.rl-apply-radio-option.selected {
  background-color: var(--rl-color-silver);
  border-color: var(--rl-color-signal-red);
}
.rl-apply-radio-option input {
  margin-top: 2px;
  accent-color: var(--rl-color-signal-red);
}
.rl-apply-radio-label {
  flex: 1;
}
.rl-apply-radio-title {
  font-family: var(--rl-font-data);
  font-weight: var(--rl-font-weight-semibold);
  font-size: var(--rl-font-size-sm);
}
.rl-apply-radio-desc {
  font-family: var(--rl-font-editorial);
  font-size: var(--rl-font-size-2xs);
  color: var(--rl-color-secondary-blue);
  margin-top: 2px;
}

/* ── Checkbox groups ───────────────────────────────── */
.rl-apply-checkbox-group {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(90px, 1fr));
  gap: var(--rl-spacing-xs);
}
.rl-apply-checkbox-vertical {
  display: flex;
  flex-direction: column;
  gap: var(--rl-spacing-xs);
}
.rl-apply-checkbox-option {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--rl-spacing-xs);
  padding: var(--rl-spacing-xs) var(--rl-spacing-sm);
  border: 2px solid var(--rl-color-near-black);
  cursor: pointer;
  font-family: var(--rl-font-data);
  font-size: var(--rl-font-size-xs);
  transition: background-color var(--rl-transition-hover), border-color var(--rl-transition-hover);
  min-height: 40px;
}
.rl-apply-checkbox-vertical .rl-apply-checkbox-option {
  justify-content: flex-start;
}
.rl-apply-checkbox-option:hover {
  background-color: var(--rl-color-silver);
}
.rl-apply-checkbox-option.selected {
  background-color: var(--rl-color-silver);
  border-color: var(--rl-color-signal-red);
}
.rl-apply-checkbox-option input {
  accent-color: var(--rl-color-signal-red);
}
.rl-apply-checkbox-label {
  flex: 1;
}
.rl-apply-checkbox-desc {
  font-size: var(--rl-font-size-2xs);
  color: var(--rl-color-secondary-blue);
}
.rl-apply-flexible-option {
  background-color: var(--rl-color-silver);
  border-style: dashed;
}

/* ── Conditional sections ──────────────────────────── */
.rl-apply-conditional {
  display: none;
}
.rl-apply-conditional.show {
  display: block;
}

/* ── Buttons ───────────────────────────────────────── */
.rl-apply-actions {
  display: flex;
  align-items: center;
  margin-top: var(--rl-spacing-lg);
}
.rl-apply-submit-btn {
  flex: 1;
  display: block;
  background: var(--rl-color-signal-red);
  color: var(--rl-color-near-black);
  padding: var(--rl-spacing-md) var(--rl-spacing-xl);
  font-family: var(--rl-font-data);
  font-size: var(--rl-font-size-base);
  font-weight: var(--rl-font-weight-bold);
  text-transform: uppercase;
  letter-spacing: var(--rl-letter-spacing-wide);
  border: 3px solid var(--rl-color-near-black);
  cursor: pointer;
  transition: background-color var(--rl-transition-hover), color var(--rl-transition-hover);
}
.rl-apply-submit-btn:hover {
  background-color: var(--rl-color-near-black);
  color: var(--rl-color-signal-red);
}
.rl-apply-submit-btn:disabled {
  cursor: not-allowed;
  background-color: var(--rl-color-silver);
  color: var(--rl-color-secondary-blue);
}
.rl-apply-save-btn {
  background: var(--rl-color-silver);
  color: var(--rl-color-near-black);
  padding: var(--rl-spacing-sm) var(--rl-spacing-lg);
  font-family: var(--rl-font-data);
  font-size: var(--rl-font-size-xs);
  font-weight: var(--rl-font-weight-semibold);
  border: 2px solid var(--rl-color-near-black);
  cursor: pointer;
  margin-right: var(--rl-spacing-sm);
  transition: background-color var(--rl-transition-hover);
}
.rl-apply-save-btn:hover {
  background-color: var(--rl-color-white);
}

/* ── Messages ──────────────────────────────────────── */
.rl-apply-message {
  padding: var(--rl-spacing-md) var(--rl-spacing-lg);
  margin-bottom: var(--rl-spacing-lg);
  border: 3px solid;
  font-family: var(--rl-font-editorial);
  font-size: var(--rl-font-size-sm);
}
.rl-apply-message.success {
  background-color: var(--rl-color-silver);
  border-color: var(--rl-color-signal-red);
  color: var(--rl-color-dark-navy);
}
.rl-apply-message.error {
  background-color: var(--rl-color-cool-white);
  border-color: var(--rl-color-error);
  color: var(--rl-color-dark-navy);
}
.rl-apply-message.info {
  background-color: var(--rl-color-silver);
  border-color: var(--rl-color-signal-red);
  color: var(--rl-color-dark-navy);
}

/* ── Utility ───────────────────────────────────────── */
.hidden { display: none !important; }
.rl-apply-honeypot { position: absolute; left: -9999px; }

/* ── Confidential footer ───────────────────────────── */
.rl-apply-confidential {
  font-family: var(--rl-font-editorial);
  font-size: var(--rl-font-size-xs);
  color: var(--rl-color-secondary-blue);
  text-align: center;
  max-width: 520px;
  margin: 0 auto var(--rl-spacing-md);
  line-height: 1.7;
}

/* ── Responsive ────────────────────────────────────── */
@media (max-width: 600px) {
  .rl-apply-container {
    padding: var(--rl-spacing-lg) var(--rl-spacing-md);
  }
  .rl-apply-form-card {
    padding: var(--rl-spacing-lg) var(--rl-spacing-lg);
  }
  .rl-apply-inline,
  .rl-apply-inline-3,
  .rl-apply-inline-4 {
    flex-direction: column;
    gap: 0;
  }
  .rl-apply-radio-horizontal {
    flex-direction: column;
  }
  .rl-apply-radio-horizontal .rl-apply-radio-option {
    min-width: auto;
  }
  .rl-apply-header h1 {
    font-size: var(--rl-font-size-xl);
  }
}
</style>'''


# ── JavaScript ─────────────────────────────────────────────────


def build_apply_js() -> str:
    """Build all JS for the coaching apply form. Includes W/kg calculator,
    blindspot inference, progress tracking, save/resume, Google Form hybrid
    submission, and GA4 event tracking."""
    return '''<script>
(function() {
  "use strict";

  /* ── W/kg category thresholds ────────────────────── */
  var CATEGORIES_MALE = [
    { min: 5.0, cat: "Pro / Cat 1", desc: "Elite level" },
    { min: 4.2, cat: "Cat 2", desc: "Very strong amateur" },
    { min: 3.7, cat: "Cat 3", desc: "Strong recreational" },
    { min: 3.2, cat: "Cat 4", desc: "Fit recreational" },
    { min: 2.5, cat: "Cat 5", desc: "Beginner racer" },
    { min: 0, cat: "Recreational", desc: "Building fitness" }
  ];
  var CATEGORIES_FEMALE = [
    { min: 4.3, cat: "Pro / Cat 1", desc: "Elite level" },
    { min: 3.6, cat: "Cat 2", desc: "Very strong amateur" },
    { min: 3.2, cat: "Cat 3", desc: "Strong recreational" },
    { min: 2.8, cat: "Cat 4", desc: "Fit recreational" },
    { min: 2.2, cat: "Cat 5", desc: "Beginner racer" },
    { min: 0, cat: "Recreational", desc: "Building fitness" }
  ];

  /* ── GA4 helper ──────────────────────────────────── */
  function ga4(name, params) {
    if (typeof gtag === "function") {
      gtag("event", name, params || {});
    }
  }

  /* ── Progress tracking ───────────────────────────── */
  function updateProgress() {
    var form = document.getElementById("intake-form");
    var required = form.querySelectorAll("[required]");
    var filled = 0;
    var uniqueRequired = {};
    required.forEach(function(el) {
      uniqueRequired[el.name] = true;
      if (el.type === "radio") {
        if (form.querySelector("input[name=\\"" + el.name + "\\"]:checked")) {
          filled++;
        }
      } else if (el.value) {
        filled++;
      }
    });
    var total = Object.keys(uniqueRequired).length;
    var percent = Math.round((filled / total) * 100);
    document.getElementById("progress-fill").style.width = percent + "%";
    document.getElementById("progress-text").textContent = percent + "% complete";
  }

  /* ── Calculate W/kg and category ─────────────────── */
  function calculateMetrics() {
    var ftp = parseFloat(document.getElementById("ftp").value);
    var weight = parseFloat(document.getElementById("weight").value);
    var sex = document.getElementById("sex").value;
    var calcDisplay = document.getElementById("calc-display");
    var wpkgEl = document.getElementById("calc-wpkg");
    var catEl = document.getElementById("calc-category");

    if (ftp && weight && sex) {
      var weightKg = weight * 0.453592;
      var wpkg = (ftp / weightKg).toFixed(2);
      var categories = sex === "female" ? CATEGORIES_FEMALE : CATEGORIES_MALE;
      var category = null;
      for (var i = 0; i < categories.length; i++) {
        if (wpkg >= categories[i].min) { category = categories[i]; break; }
      }
      wpkgEl.textContent = wpkg + " W/kg";
      catEl.textContent = category ? category.cat + " (" + category.desc + ")" : "-";
      document.getElementById("watts_per_kg").value = wpkg;
      document.getElementById("estimated_category").value = category ? category.cat : "";
      calcDisplay.classList.remove("hidden");
      ga4("apply_wpkg_calculated", { wpkg: wpkg, category: category ? category.cat : "unknown" });
    } else {
      calcDisplay.classList.add("hidden");
    }
  }

  /* ── Blindspot and trait inference ────────────────── */
  function inferTraits() {
    var blindspots = [];
    var traits = [];

    var sleep = document.getElementById("sleep_quality").value;
    if (sleep === "poor" || sleep === "fair") { blindspots.push("Recovery Deficit"); }

    var stress = document.getElementById("life_stress").value;
    if (stress === "high" || stress === "very_high") { blindspots.push("Life Stress Overload"); }

    var strength = document.querySelector("input[name=\\"strength_current\\"]:checked");
    if (strength && (strength.value === "none" || strength.value === "occasional")) {
      blindspots.push("Movement Quality Gap");
    }

    var injuries = document.getElementById("injuries").value;
    if (injuries && injuries.trim().length > 0) { blindspots.push("Injury Management"); }

    var hours = document.getElementById("hours_per_week").value;
    if (hours === "3-5" || hours === "5-7") { blindspots.push("Time-Crunched"); }

    var age = parseInt(document.getElementById("age").value);
    if (age >= 45) { blindspots.push("Masters Recovery"); }
    if (age >= 55) { blindspots.push("Extended Recovery Needs"); }

    var overtrain = document.getElementById("overtraining_history").value;
    if (overtrain === "multiple" || overtrain === "currently") { blindspots.push("Overtraining Risk"); }

    var obstacles = (document.getElementById("obstacles") ? document.getElementById("obstacles").value : "").toLowerCase();
    var pastInjuries = (document.getElementById("past_injuries") ? document.getElementById("past_injuries").value : "").toLowerCase();
    var medicalConditions = (document.getElementById("medical_conditions") ? document.getElementById("medical_conditions").value : "").toLowerCase();
    var quitTriggers = (document.getElementById("quit_triggers") ? document.getElementById("quit_triggers").value : "").toLowerCase();
    var allText = obstacles + " " + pastInjuries + " " + medicalConditions + " " + quitTriggers;

    if (/alcohol|drinking|beer|wine|drink/.test(allText)) { blindspots.push("Alcohol Recovery Impact"); }
    if (/diet|dieting|weight|too heavy|too fat|losing weight/.test(allText)) { blindspots.push("Weight Management Stress"); }
    if (/caffeine|coffee/.test(allText)) { blindspots.push("Caffeine Dependency"); }
    if (/sleep.*medication|insomnia|sleep apnea/.test(allText)) { blindspots.push("Sleep Disorder"); }

    var missedResponse = document.querySelector("input[name=\\"missed_workout_response\\"]:checked");
    if (missedResponse) {
      if (missedResponse.value === "make_up") { traits.push("Perfectionist tendency"); }
      else if (missedResponse.value === "move_on") { traits.push("Healthy flexibility"); }
      else if (missedResponse.value === "spiral") { traits.push("Needs reassurance"); }
    }

    var accountability = document.getElementById("accountability_style").value;
    if (accountability === "public") { traits.push("External accountability"); }
    else if (accountability === "secret" || accountability === "private") { traits.push("Internal accountability"); }

    document.getElementById("blindspots").value = blindspots.join(",");
    document.getElementById("inferred_traits").value = traits.join(",");
  }

  /* ── Conditional fields ──────────────────────────── */
  function handleConditionals() {
    var goalRadio = document.querySelector("input[name=\\"primary_goal\\"]:checked");
    var raceDetails = document.getElementById("race-details");
    if (goalRadio && goalRadio.value === "specific_race") {
      raceDetails.classList.add("show");
    } else {
      raceDetails.classList.remove("show");
    }

    var platform = document.getElementById("training_platform").value;
    var intervalsGroup = document.getElementById("intervals-id-group");
    if (platform === "intervals_icu") {
      intervalsGroup.classList.add("show");
    } else {
      intervalsGroup.classList.remove("show");
    }
  }

  /* ── Radio option selection styling ──────────────── */
  document.querySelectorAll(".rl-apply-radio-option").forEach(function(option) {
    option.addEventListener("click", function() {
      var input = this.querySelector("input");
      var name = input.name;
      document.querySelectorAll(".rl-apply-radio-option input[name=\\"" + name + "\\"]").forEach(function(inp) {
        inp.closest(".rl-apply-radio-option").classList.remove("selected");
      });
      this.classList.add("selected");
      input.checked = true;
      updateProgress();
      handleConditionals();
    });
  });

  /* ── Checkbox option selection styling ───────────── */
  document.querySelectorAll(".rl-apply-checkbox-option").forEach(function(option) {
    option.addEventListener("click", function(e) {
      var input = this.querySelector("input");
      if (e.target.tagName !== "INPUT") { input.checked = !input.checked; }

      var name = input.name;
      var value = input.value;
      var isChecked = input.checked;

      if (value === "flexible" && isChecked) {
        document.querySelectorAll("input[name=\\"" + name + "\\"]").forEach(function(inp) {
          if (inp.value !== "flexible") {
            inp.checked = false;
            var opt = inp.closest(".rl-apply-checkbox-option");
            if (opt) { opt.classList.remove("selected"); }
          }
        });
      } else if (value !== "flexible" && isChecked) {
        var flexibleInput = document.querySelector("input[name=\\"" + name + "\\"][value=\\"flexible\\"]");
        if (flexibleInput) {
          flexibleInput.checked = false;
          var flexOpt = flexibleInput.closest(".rl-apply-checkbox-option");
          if (flexOpt) { flexOpt.classList.remove("selected"); }
        }
      }

      if (input.checked) { this.classList.add("selected"); }
      else { this.classList.remove("selected"); }
      updateProgress();
    });
  });

  /* ── Event listeners ─────────────────────────────── */
  document.getElementById("ftp").addEventListener("input", calculateMetrics);
  document.getElementById("weight").addEventListener("input", calculateMetrics);
  document.getElementById("sex").addEventListener("change", calculateMetrics);
  document.getElementById("training_platform").addEventListener("change", handleConditionals);

  document.querySelectorAll("input, select, textarea").forEach(function(el) {
    el.addEventListener("change", updateProgress);
    el.addEventListener("input", updateProgress);
  });

  /* ── Save progress to localStorage ───────────────── */
  document.getElementById("save-btn").addEventListener("click", function() {
    var form = document.getElementById("intake-form");
    var formData = new FormData(form);
    var data = {};
    formData.forEach(function(value, key) {
      if (data[key]) {
        if (Array.isArray(data[key])) { data[key].push(value); }
        else { data[key] = [data[key], value]; }
      } else {
        data[key] = value;
      }
    });
    localStorage.setItem("athlete_questionnaire_progress", JSON.stringify(data));
    showMessage("info", "Progress saved! You can close this page and return later.");
    ga4("apply_progress_saved", {});
  });

  /* ── Restore progress from localStorage ──────────── */
  function restoreProgress() {
    var saved = localStorage.getItem("athlete_questionnaire_progress");
    if (!saved) { return; }
    try {
      var data = JSON.parse(saved);
      Object.keys(data).forEach(function(key) {
        var value = data[key];
        var elements = document.querySelectorAll("[name=\\"" + key + "\\"]");
        elements.forEach(function(el) {
          if (el.type === "checkbox") {
            var values = Array.isArray(value) ? value : [value];
            el.checked = values.indexOf(el.value) !== -1;
            if (el.checked) {
              var opt = el.closest(".rl-apply-checkbox-option");
              if (opt) { opt.classList.add("selected"); }
            }
          } else if (el.type === "radio") {
            el.checked = el.value === value;
            if (el.checked) {
              var ropt = el.closest(".rl-apply-radio-option");
              if (ropt) { ropt.classList.add("selected"); }
            }
          } else {
            el.value = value;
          }
        });
      });
      updateProgress();
      handleConditionals();
      calculateMetrics();
      showMessage("info", "Previous progress restored. Continue where you left off.");
    } catch (e) {
      /* ignore corrupt localStorage */
    }
  }

  /* ── Format submission for Google Form / email ───── */
  function formatSubmission(data) {
    var lines = [];
    lines.push("# Athlete Intake: " + data.name);
    lines.push("Email: " + data.email);
    lines.push("Submitted: " + new Date().toISOString());
    lines.push("");
    lines.push("## Basic Info");
    lines.push("- Age: " + data.age);
    lines.push("- Sex: " + data.sex);
    lines.push("- Weight: " + data.weight + " lbs");
    lines.push("- Height: " + data.height_ft + "'" + data.height_in + '"');
    lines.push("");
    lines.push("## Goals");
    lines.push("- Primary Goal: " + data.primary_goal);
    if (data.race_list) { lines.push("- Races: " + data.race_list); }
    if (data.success_definition) { lines.push("- Success: " + data.success_definition); }
    if (data.obstacles) { lines.push("- Obstacles: " + data.obstacles); }
    lines.push("");
    lines.push("## Current Fitness");
    lines.push("- Years Cycling: " + data.years_cycling);
    lines.push("- Years Structured: " + (data.years_structured || "N/A"));
    lines.push("- Longest Recent Ride: " + data.longest_ride);
    lines.push("- FTP: " + (data.ftp || "Unknown") + " W");
    lines.push("- W/kg: " + (data.watts_per_kg || "Unknown"));
    lines.push("- Estimated Category: " + (data.estimated_category || "Unknown"));
    if (data.strengths) { lines.push("- Strengths: " + data.strengths); }
    if (data.weaknesses) { lines.push("- Weaknesses: " + data.weaknesses); }
    lines.push("");
    lines.push("## Recovery & Baselines");
    lines.push("- Resting HR: " + data.rhr_baseline + " bpm");
    lines.push("- Typical Sleep: " + data.sleep_hours_baseline + " hrs");
    lines.push("- HRV Baseline: " + (data.hrv_baseline || "Unknown") + " ms");
    lines.push("- Sleep Quality: " + data.sleep_quality);
    lines.push("- Recovery Speed: " + data.recovery_speed);
    lines.push("- Overtraining History: " + (data.overtraining_history || "N/A"));
    lines.push("");
    lines.push("## Equipment & Data");
    var devicesStr = Array.isArray(data.devices) ? data.devices.join(", ") : (data.devices || "None");
    lines.push("- Devices: " + devicesStr);
    lines.push("- Platform: " + data.training_platform);
    lines.push("- Intervals.icu ID: " + (data.intervals_athlete_id || "N/A"));
    lines.push("- Indoor Trainer: " + data.trainer_access);
    lines.push("- Indoor Tolerance: " + (data.indoor_tolerance || "N/A"));
    lines.push("");
    lines.push("## Schedule");
    lines.push("- Weekly Hours Available: " + data.hours_per_week);
    lines.push("- Current Volume: " + (data.current_volume || "N/A"));
    var longDays = Array.isArray(data.long_ride_days) ? data.long_ride_days.join(", ") : data.long_ride_days;
    lines.push("- Long Ride Days: " + longDays);
    var intDays = Array.isArray(data.interval_days) ? data.interval_days.join(", ") : data.interval_days;
    lines.push("- Interval Days: " + intDays);
    var offDays = Array.isArray(data.off_days) ? data.off_days.join(", ") : "Flexible";
    lines.push("- Off Days: " + offDays);
    lines.push("");
    lines.push("## Work & Life");
    lines.push("- Work Hours: " + (data.work_hours || "N/A"));
    lines.push("- Job Stress: " + (data.job_stress || "N/A"));
    lines.push("- Life Stress: " + data.life_stress);
    if (data.family_situation) { lines.push("- Family: " + data.family_situation); }
    if (data.time_commitments) { lines.push("- Commitments: " + data.time_commitments); }
    lines.push("");
    lines.push("## Health");
    lines.push("- Current Injuries: " + (data.injuries || "None"));
    if (data.past_injuries) { lines.push("- Past Injuries: " + data.past_injuries); }
    if (data.medical_conditions) { lines.push("- Medical Conditions: " + data.medical_conditions); }
    if (data.medications) { lines.push("- Medications: " + data.medications); }
    lines.push("");
    lines.push("## Strength");
    lines.push("- Current: " + data.strength_current);
    lines.push("- Include: " + (data.strength_want || "N/A"));
    lines.push("- Equipment: " + (data.strength_equipment || "N/A"));
    lines.push("");
    lines.push("## Coaching Preferences");
    lines.push("- Check-in Frequency: " + data.checkin_frequency);
    lines.push("- Feedback Detail: " + data.feedback_detail);
    lines.push("- Autonomy: " + data.autonomy);
    lines.push("- Communication Style: " + (data.communication_style || "N/A"));
    lines.push("");
    lines.push("## Mental Game");
    lines.push("- Missed Workout Response: " + data.missed_workout_response);
    if (data.best_training_block) { lines.push("- Best Training Block: " + data.best_training_block); }
    if (data.quit_triggers) { lines.push("- Quit Triggers: " + data.quit_triggers); }
    lines.push("- Accountability Style: " + (data.accountability_style || "N/A"));
    lines.push("");
    lines.push("## Additional");
    if (data.previous_coach) { lines.push("- Previous Coach: " + data.previous_coach); }
    if (data.anything_else) { lines.push("- Other: " + data.anything_else); }
    lines.push("");
    lines.push("## Inferred");
    lines.push("- Blindspots: " + (data.blindspots || "None identified"));
    lines.push("- Traits: " + (data.inferred_traits || "None identified"));
    return lines.join("\\n");
  }

  /* ── Form submission — Formsubmit.co ──────────────── */
  document.getElementById("intake-form").addEventListener("submit", function(e) {
    e.preventDefault();
    var submitBtn = document.getElementById("submit-btn");
    inferTraits();
    submitBtn.disabled = true;
    submitBtn.textContent = "Submitting...";

    var formData = new FormData(this);
    var data = {};
    formData.forEach(function(value, key) { data[key] = value; });
    data.devices = formData.getAll("devices");
    data.long_ride_days = formData.getAll("long_ride_days");
    data.interval_days = formData.getAll("interval_days");
    data.off_days = formData.getAll("off_days");

    /* Honeypot check */
    if (data.website) {
      showMessage("error", "Submission blocked.");
      submitBtn.disabled = false;
      submitBtn.textContent = "Submit Questionnaire";
      return;
    }

    /* Validate required checkboxes */
    if (!data.long_ride_days || data.long_ride_days.length === 0) {
      showMessage("error", "Please select at least one day for long rides.");
      submitBtn.disabled = false;
      submitBtn.textContent = "Submit Questionnaire";
      return;
    }
    if (!data.interval_days || data.interval_days.length === 0) {
      showMessage("error", "Please select at least one day for intervals.");
      submitBtn.disabled = false;
      submitBtn.textContent = "Submit Questionnaire";
      return;
    }

    var output = formatSubmission(data);

    /* Submit via Formsubmit.co — sends email to TODO_ROADLABS_EMAIL */
    var FORMSUBMIT_URL = "''' + FORMSUBMIT_URL + '''";
    var payload = new FormData();
    payload.append("_subject", "Coaching Application: " + data.name);
    payload.append("_replyto", data.email);
    payload.append("_captcha", "false");
    payload.append("_template", "box");
    payload.append("name", data.name);
    payload.append("email", data.email);
    payload.append("message", output);
    payload.append("_honey", "");

    fetch(FORMSUBMIT_URL, {
      method: "POST",
      body: payload,
      headers: { "Accept": "application/json" }
    }).then(function(response) {
      if (response.ok) {
        localStorage.removeItem("athlete_questionnaire_progress");
        ga4("apply_form_submitted", {
          blindspot_count: (data.blindspots || "").split(",").filter(function(b) { return b; }).length,
          has_ftp: data.ftp ? "yes" : "no",
          primary_goal: data.primary_goal
        });
        showMessage("success", "Application submitted! I&#39;ll review your questionnaire and get back to you within 24 hours.");
        submitBtn.textContent = "Submitted";
      } else {
        throw new Error("Server returned " + response.status);
      }
    }).catch(function(err) {
      /* Fallback: open email client with formatted body */
      var subject = encodeURIComponent("Coaching Application: " + data.name);
      var body = encodeURIComponent(output);
      window.location.href = "mailto:TODO_ROADLABS_EMAIL?subject=" + subject + "&body=" + body;
      ga4("apply_form_fallback", { method: "mailto" });
    });
  });

  /* ── Show message ────────────────────────────────── */
  function showMessage(type, text) {
    var messageDiv = document.getElementById("message");
    messageDiv.className = "rl-apply-message " + type;
    messageDiv.innerHTML = text;
    messageDiv.classList.remove("hidden");
    messageDiv.scrollIntoView({ behavior: "smooth", block: "center" });
  }

  /* ── GA4 page view ───────────────────────────────── */
  ga4("apply_page_view", {});

  /* ── Scroll depth tracking ───────────────────────── */
  var scrollMilestones = {};
  window.addEventListener("scroll", function() {
    var scrollPercent = Math.round((window.scrollY / (document.documentElement.scrollHeight - window.innerHeight)) * 100);
    [25, 50, 75, 100].forEach(function(milestone) {
      if (scrollPercent >= milestone && !scrollMilestones[milestone]) {
        scrollMilestones[milestone] = true;
        ga4("apply_scroll_depth", { percent: milestone });
      }
    });
  });

  /* ── Initialize ──────────────────────────────────── */
  restoreProgress();
  updateProgress();
  handleConditionals();
})();
</script>'''


# ── Page assembly ──────────────────────────────────────────────


def generate_apply_page(external_assets=None):
    """Generate the complete coaching apply page HTML."""
    if external_assets:
        page_css = external_assets['css_tag']
    else:
        page_css = get_page_css()

    return f'''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Coaching Application | Road Labs</title>
  <meta name="description" content="Apply for personalized gravel cycling coaching. 12-section athlete intake with blindspot inference, W/kg calculator, and save/resume.">
  <meta name="robots" content="noindex, follow">
  <link rel="canonical" href="{SITE_BASE_URL}/coaching/apply/">
  <meta property="og:title" content="Coaching Application | Road Labs">
  <meta property="og:description" content="Apply for personalized gravel cycling coaching. 12-section athlete intake with blindspot inference, W/kg calculator, and save/resume.">
  <meta property="og:type" content="website">
  <meta property="og:url" content="{SITE_BASE_URL}/coaching/apply/">
  <meta property="og:image" content="{SITE_BASE_URL}/og/homepage.jpg">
  <meta property="og:image:width" content="1200">
  <meta property="og:image:height" content="630">
  <meta property="og:site_name" content="Road Labs">
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:image" content="{SITE_BASE_URL}/og/homepage.jpg">
  <link rel="icon" href="https://roadlabs.cc/wp-content/uploads/2021/09/cropped-Gravel-God-logo-32x32.png" sizes="32x32"><!-- TODO: replace with Road Labs favicon -->
  {get_preload_hints()}
  {page_css}
  {get_ab_head_snippet()}
  <!-- GA4 -->
  {get_ga4_head_snippet()}
  {build_apply_css()}
</head>
<body class="rl-neo-brutalist-page" style="background:var(--rl-color-cool-white);color:var(--rl-color-near-black);font-family:var(--rl-font-data);font-size:var(--rl-font-size-sm);line-height:1.7;min-height:100vh">
  {build_nav()}
  <div class="rl-apply-container">
    {build_header()}
    {build_progress_bar()}
    <div id="message" class="rl-apply-message hidden"></div>
    <form id="intake-form" class="rl-apply-form-card">
      <input type="text" name="website" class="rl-apply-honeypot" tabindex="-1" autocomplete="off">
      <input type="hidden" name="form_type" value="coaching_intake">
      <input type="hidden" name="watts_per_kg" id="watts_per_kg" value="">
      <input type="hidden" name="estimated_category" id="estimated_category" value="">
      <input type="hidden" name="blindspots" id="blindspots" value="">
      <input type="hidden" name="inferred_traits" id="inferred_traits" value="">
      {build_section_1_basic_info()}
      {build_section_2_goals()}
      {build_section_3_fitness()}
      {build_section_4_recovery()}
      {build_section_5_equipment()}
      {build_section_6_schedule()}
      {build_section_7_work_life()}
      {build_section_8_health()}
      {build_section_9_strength()}
      {build_section_10_coaching_prefs()}
      {build_section_11_mental_game()}
      {build_section_12_other()}
      {build_submit_buttons()}
    </form>
  </div>
  {build_footer()}
  {build_jsonld()}
  {build_apply_js()}
{get_consent_banner_html()}
</body>
</html>'''


def main():
    parser = argparse.ArgumentParser(description="Generate coaching apply page")
    parser.add_argument("--output-dir", default=str(OUTPUT_DIR))
    args = parser.parse_args()

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    # Write shared CSS/JS assets
    assets = write_shared_assets(out_dir)

    html_content = generate_apply_page(external_assets=assets)
    out_path = out_dir / "coaching-apply.html"
    out_path.write_text(html_content, encoding="utf-8")
    print(f"Generated {out_path} ({len(html_content):,} bytes)")


if __name__ == "__main__":
    main()
