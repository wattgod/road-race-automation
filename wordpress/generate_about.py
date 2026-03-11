#!/usr/bin/env python3
"""
Generate the Road Labs About page in neo-brutalist style.

Tells the platform story: what we built, who's behind it, how we coach.
Loads race count dynamically from race-index.json. Reuses CSS/style patterns
from generate_neo_brutalist.py. Styling follows the brand guide component
library (principle cards, pullquotes, double-rule borders, tabs, stat cards).

Usage:
    python generate_about.py
    python generate_about.py --output-dir ./output
"""

import argparse
import html
import json
from pathlib import Path

from generate_neo_brutalist import (
    SITE_BASE_URL,
    SUBSTACK_URL,
    get_page_css,
    build_inline_js,
    write_shared_assets,
)
from brand_tokens import get_ab_head_snippet, get_ga4_head_snippet, get_preload_hints
from shared_footer import get_mega_footer_html
from shared_header import get_site_header_html
from cookie_consent import get_consent_banner_html

OUTPUT_DIR = Path(__file__).parent / "output"
PROJECT_ROOT = Path(__file__).resolve().parent.parent
RACE_INDEX_PATH = PROJECT_ROOT / "web" / "race-index.json"


def esc(text) -> str:
    """HTML-escape a string."""
    return html.escape(str(text)) if text else ""


def load_race_count() -> int:
    """Load the race count from race-index.json."""
    if RACE_INDEX_PATH.exists():
        data = json.loads(RACE_INDEX_PATH.read_text(encoding="utf-8"))
        return len(data)
    return 328  # fallback


# ── Page sections ─────────────────────────────────────────────


def build_nav() -> str:
    return get_site_header_html(active="about") + f'''
  <div class="rl-breadcrumb">
    <a href="{SITE_BASE_URL}/">Home</a>
    <span class="rl-breadcrumb-sep">&rsaquo;</span>
    <span class="rl-breadcrumb-current">About</span>
  </div>'''


def build_hero(race_count: int) -> str:
    return f'''<div class="rl-hero rl-about-hero">
    <div class="rl-hero-tier" style="background:var(--rl-color-orange)">ABOUT</div>
    <h1 data-text="{race_count} Gravel Races. Scored. Zero Sponsors.">{race_count} Gravel Races. Scored. Zero Sponsors.</h1>
    <p class="rl-hero-tagline">I scored every gravel race in America by hand, then paired it with coaching for people who have real jobs and limited PTO.</p>
  </div>'''


def build_why_this_exists() -> str:
    return '''<div class="rl-section" id="why">
    <div class="rl-section-header">
      <span class="rl-section-kicker">01</span>
      <h2 class="rl-section-title">Why This Exists</h2>
    </div>
    <div class="rl-section-body">
      <p class="rl-about-prose">Gravel race information lives in Instagram comments, Reddit threads, and word of mouth. You either trust a race organizer&#39;s marketing copy or cold-DM strangers who&#39;ve done the event. Course profiles are scattered across Strava segments nobody maintains. Registration costs, terrain breakdowns, and field quality are mysteries until you show up.</p>
      <div class="rl-about-highlight rl-about-highlight--gold">
        <p>I thought that was stupid. So I built a database.</p>
      </div>
    </div>
  </div>'''


def build_what_we_built(race_count: int) -> str:
    return f'''<div class="rl-section" id="what">
    <div class="rl-section-header">
      <span class="rl-section-kicker">02</span>
      <h2 class="rl-section-title">What I Built</h2>
    </div>
    <div class="rl-section-body">
      <div class="rl-about-stats">
        <div class="rl-about-stat">
          <span class="rl-about-stat-number">{race_count}</span>
          <span class="rl-about-stat-label">Races Rated</span>
        </div>
        <div class="rl-about-stat">
          <span class="rl-about-stat-number">14</span>
          <span class="rl-about-stat-label">Scoring Dimensions</span>
        </div>
        <div class="rl-about-stat">
          <span class="rl-about-stat-number">0</span>
          <span class="rl-about-stat-label">Sponsors</span>
        </div>
        <div class="rl-about-stat">
          <span class="rl-about-stat-number">42</span>
          <span class="rl-about-stat-label">States + Countries</span>
        </div>
      </div>

      <!-- Tabbed feature panels -->
      <div class="rl-about-tabs" data-about-tabs>
        <div class="rl-about-tabs-nav">
          <button class="rl-about-tab rl-about-tab--active" data-about-tab="profiles">Race Profiles</button>
          <button class="rl-about-tab" data-about-tab="prep">Prep Kits</button>
          <button class="rl-about-tab" data-about-tab="compare">Compare Tool</button>
        </div>
        <div class="rl-about-tab-panel rl-about-tab-panel--active" data-about-panel="profiles">
          <p>Every race scored across 15 dimensions. Course difficulty, field depth, logistics, prestige, value &mdash; the stuff that actually matters when you&#39;re deciding where to spend your registration fee and PTO days.</p>
        </div>
        <div class="rl-about-tab-panel" data-about-panel="prep">
          <p>Race-specific training guidance, pacing strategy, fueling plans, and gear recommendations. The pre-race homework you&#39;d do if you had 40 hours to research one event.</p>
        </div>
        <div class="rl-about-tab-panel" data-about-panel="compare">
          <p>Side-by-side radar charts for 2&ndash;4 races. Because &ldquo;which one should I do?&rdquo; is the most common question in gravel, and the answer is never &ldquo;whichever has the best Instagram.&rdquo;</p>
        </div>
      </div>

      <p style="margin-top:24px"><a href="{SITE_BASE_URL}/race/methodology/" class="rl-about-link" data-cta="methodology">See exactly how I score races &rarr;</a></p>
    </div>
  </div>'''


def build_who() -> str:
    return f'''<div class="rl-section" id="who">
    <div class="rl-section-header">
      <span class="rl-section-kicker">03</span>
      <h2 class="rl-section-title">Who&#39;s Behind This</h2>
    </div>
    <div class="rl-section-body">
      <div class="rl-about-bio">
        <div class="rl-about-bio-text">
          <p class="rl-about-prose">I&#39;m Matti. I&#39;ve spent 12 years at TrainingPeaks teaching coaches and athletes how to get the most out of their training. Before that I raced at the National level for Team Rio Grande &mdash; until the team folded and my third kid arrived in the same year. Turns out those two events have a way of reshuffling your priorities.</p>
          <p class="rl-about-prose">I&#39;ve coached 100+ athletes and sold over 1,000 training plans &mdash; mostly to people who have real jobs, real families, and a limited tolerance for training plans that assume you have nothing else going on.</p>
          <div class="rl-about-highlight">
            <p>I built Road Labs because I kept answering the same questions from my athletes: <em>Which race should I do? How hard is this one, actually? What do I need to know before I register?</em> The answers were always buried in six different places. Now they&#39;re in one.</p>
          </div>
        </div>
        <div class="rl-about-bio-sidebar">
          <img src="/about/matti-avatar.png" alt="Matti — cartoon portrait" class="rl-about-bio-avatar" width="280" height="280" loading="lazy">
          <div class="rl-about-bio-card">
            <div class="rl-about-bio-card-label">Background</div>
            <dl class="rl-about-bio-dl">
              <dt>TrainingPeaks</dt><dd>12 years (only 2 promotions tho)</dd>
              <dt>Racing</dt><dd>CAT 1 roadie (CAT 5 handling skills)</dd>
              <dt>Team</dt><dd>Rio Grande Elite (until it folded)</dd>
              <dt>Athletes coached</dt><dd>100+</dd>
              <dt>Plans sold</dt><dd>1,000+</dd>
            </dl>
          </div>
        </div>
      </div>
    </div>
  </div>'''


def build_coaching() -> str:
    return '''<div class="rl-section" id="coaching">
    <div class="rl-section-header">
      <span class="rl-section-kicker">04</span>
      <h2 class="rl-section-title">How I Coach</h2>
    </div>
    <div class="rl-section-body">
      <div class="rl-about-pillars">
        <div class="rl-about-pillar">
          <div class="rl-about-pillar-kicker">Principle 01</div>
          <h3>Life-First</h3>
          <p>Training has to survive real life. Jobs, kids, travel, the random Tuesday emergency. If a plan only works when everything goes perfectly, it doesn&#39;t work.</p>
        </div>
        <div class="rl-about-pillar">
          <div class="rl-about-pillar-kicker">Principle 02</div>
          <h3>Fundamentals Over Hype</h3>
          <p>Base fitness, pacing, fueling, recovery. The boring stuff that actually moves the needle. No secret workouts. No magic intervals. Just the things that compound over months.</p>
        </div>
        <div class="rl-about-pillar">
          <div class="rl-about-pillar-kicker">Principle 03</div>
          <h3>Execution Over Theory</h3>
          <p>A mediocre plan you actually follow beats the perfect plan you abandon in week three. I build around consistency, not optimization theater.</p>
        </div>
      </div>
    </div>
  </div>'''


def _testimonial_data() -> list:
    """50 athlete testimonials — name, quote, meta line."""
    return [
        ("Sarah K.", "I finished Unbound in 13:47 this year. Last year I DNF'd at mile 140 because I had no idea how to pace myself and ran out of food twice. Matti's plan was boring as hell but it worked.", "Unbound 200 finisher · 9 hrs/week · Elementary school teacher"),
        ("Chris M.", "I went from blowing up on every climb longer than 10 minutes to finishing SBT GRVL Black in the top third. The difference was pacing and fueling strategy, not some magic workout.", "SBT GRVL Black finisher · 10 hrs/week · Two kids under 5"),
        ("Dan R.", "Finished Belgian Waffle Ride in 9:12. My previous best was 10:45. The only thing that changed was how I ate and when I pushed.", "BWR finisher · 11 hrs/week · Software engineer"),
        ("Megan T.", "My first gravel race was Mid South and I finished middle of the pack on 7 hours a week of training. Matti convinced me that was enough and he was right.", "Mid South finisher · 7 hrs/week · Nurse practitioner"),
        ("Jason L.", "Cut 45 minutes off my Steamboat Gravel time by actually following a taper for once. I always used to hammer the last week before a race.", "Steamboat Gravel · 8 hrs/week · Restaurant owner"),
        ("Rachel P.", "I came back from a broken collarbone and finished Gravel Worlds 5 months later. The plan adapted every single week based on how I was recovering.", "Gravel Worlds finisher · 6 hrs/week · Physical therapist"),
        ("Tom W.", "I'm 54 and just had my best season ever. Three gravel races, three finishes, zero bonks. Turns out the secret is eating enough.", "Big Sugar finisher · 9 hrs/week · Age 54 · Attorney"),
        ("Katie B.", "Did Crusher in the Tushar on 8 hours a week. Everyone told me I needed more volume. I needed better pacing.", "Crusher in the Tushar · 8 hrs/week · Marketing director"),
        ("Mike D.", "Went from DNF to top 25% at Gravel Locos. Same fitness, completely different race execution.", "Gravel Locos · 10 hrs/week · Firefighter"),
        ("Jen H.", "The fueling plan alone was worth it. I used to cramp at mile 80 every single race. Haven't cramped once since.", "Unbound 200 finisher · 8 hrs/week · Accountant"),
        ("Brian S.", "I've bought training plans from four different coaches. This is the first one I actually finished.", "SBT GRVL Blue · 7 hrs/week · Three kids"),
        ("Amanda C.", "Finished DK200 in the rain and mud and never once thought about quitting. That's a first.", "DK 200 finisher · 9 hrs/week · Veterinarian"),
        ("Greg F.", "My wife noticed I was less stressed during race build. That's the real testimonial.", "BWR Waffle · 10 hrs/week · Finance · Married with 2 kids"),
        ("Nicole R.", "I PR'd Rule of Three by 38 minutes. The course hadn't changed. My preparation had.", "Rule of Three · 7 hrs/week · High school teacher"),
        ("Steve A.", "I'm a Cat 1 road racer and I thought I knew how to train. Gravel is a different sport. Matti showed me the gaps.", "Unbound XL finisher · 14 hrs/week · Cat 1 road"),
        ("Laura M.", "I train at 5 AM before my kids wake up. The plan was built around that constraint from day one.", "Mid South finisher · 6 hrs/week · Mom of 3 · Pharmacist"),
        ("Derek J.", "Leadville 100 MTB. Finished under 9 hours on 10 hours a week of training. My coach friends who train 15+ hours were behind me.", "Leadville 100 · 10 hrs/week · Age 41"),
        ("Carrie W.", "I was terrified of Unbound. Matti's prep kit and pacing plan made it feel manageable. Still hard as hell, but manageable.", "Unbound 200 finisher · 8 hrs/week · First-time 200-miler"),
        ("Paul N.", "The race-day pacing strategy was the game changer. I used to go out way too hard and pay for it at mile 120.", "Gravel Worlds finisher · 9 hrs/week · Civil engineer"),
        ("Heather L.", "I signed up for coaching because of the race database. Stayed because the training actually fit my life.", "SBT GRVL Black · 7 hrs/week · Working mom"),
        ("Ryan G.", "Four gravel races this season, four finishes, zero DNFs. Last year I DNF'd two out of three.", "Multi-race season · 11 hrs/week · Sales manager"),
        ("Trish K.", "My 10K trail run PR dropped by 3 minutes as a side effect of the gravel training. The base building works.", "Pisgah Monster Cross · 8 hrs/week · Trail runner crossover"),
        ("Mark E.", "I'm 62 and just finished my first Dirty Kanza distance event. Matti never once made me feel too old for this.", "DK 100 finisher · 7 hrs/week · Age 62 · Retired teacher"),
        ("Anna S.", "I thought I needed a power meter and a wind tunnel. I needed to eat more and sleep more. That's it.", "Lost and Found finisher · 6 hrs/week · Grad student"),
        ("Jake T.", "Finished Rooted Vermont in top 10%. The course profile breakdown and pacing zones were dialed.", "Rooted Vermont · 12 hrs/week · Bike shop employee"),
        ("Diane F.", "Three years of gravel racing and this was the first time I finished a race feeling like I had more in the tank.", "Gravel Locos finisher · 8 hrs/week · Age 48"),
        ("Luis R.", "I work 60-hour weeks in construction. The plan was 6 hours. It worked. I finished Mid South.", "Mid South finisher · 6 hrs/week · Construction foreman"),
        ("Emily P.", "The sodium loading protocol before Unbound was something I'd never seen before. Zero cramping for the first time ever.", "Unbound 200 · 9 hrs/week · Registered dietitian"),
        ("Nathan B.", "I gained 4 watts per kilo over 16 weeks eating more food and sleeping 30 minutes more per night. No secret intervals.", "BWR finisher · 10 hrs/week · Programmer"),
        ("Kara D.", "Finished Big Sugar 100 seven months postpartum. Matti built the plan around breastfeeding and sleep deprivation.", "Big Sugar 100 · 5 hrs/week · New mom"),
        ("Doug H.", "My third Steamboat and my fastest by over an hour. I finally learned to ride my own race.", "Steamboat Gravel · 9 hrs/week · Dentist"),
        ("Sierra J.", "I'm not fast. I'm not trying to be. Matti helped me finish what I start and enjoy it. That's enough.", "SBT GRVL Green · 6 hrs/week · Back-of-pack rider"),
        ("Phil C.", "The prep kit for Crusher told me exactly what to expect on every climb. No surprises on race day.", "Crusher in the Tushar · 11 hrs/week · Age 45"),
        ("Tanya M.", "I bought the Unbound plan, then the BWR plan, then just signed up for coaching because I was tired of doing this alone.", "Multi-race season · 8 hrs/week · Remote worker"),
        ("Rob L.", "I travel 3 weeks a month for work. Every hotel has a gym or a road. Matti made it work.", "Gravel Worlds · 7 hrs/week · Traveling consultant"),
        ("Lisa G.", "Dropped from 10:30 to 9:15 at Rebecca's Private Idaho with the same legs. Fueling and pacing, that's it.", "Rebecca's Private Idaho · 8 hrs/week · Teacher"),
        ("Kevin O.", "My wife and I both used Matti's plans for Unbound. We both finished. That was the deal and we held up our end.", "Unbound 200 · 9 hrs/week · Couple's plan"),
        ("Brooke A.", "I did Gravel Worlds 150 on a hardtail because Matti said my bike didn't matter as much as my prep. He was right.", "Gravel Worlds 150 · 7 hrs/week · Hardtail rider"),
        ("Tony V.", "I used to overtrain every spring and show up to my A-race cooked. This year I showed up fresh and went 40 minutes faster.", "BWR Waffle · 12 hrs/week · Cat 2 road crossover"),
        ("Maria K.", "English is my second language and the plan was still crystal clear. No jargon. No confusion. Just do this today.", "SBT GRVL Blue · 6 hrs/week · Originally from Colombia"),
        ("Will S.", "Finished The Last Best Ride in Montana on 7 hours a week. My buddy who trains double that finished 20 minutes ahead. Worth it.", "The Last Best Ride · 7 hrs/week · Architect"),
        ("Jess R.", "I was recovering from COVID and the plan adjusted week by week. No ego, no pressure, just smart rebuilding.", "Return to racing post-COVID · 5 hrs/week · Nurse"),
        ("Andrew T.", "The race database is how I picked Gravel Locos over Unbound for my first 150-miler. Best decision I made all year.", "Gravel Locos · 8 hrs/week · First-time 150"),
        ("Danielle B.", "I've done 4 Ironmans and gravel scared me more. Matti's prep kit made it approachable. Finished Land Run 100 with a smile.", "Land Run 100 · 10 hrs/week · Triathlete crossover"),
        ("Scott P.", "I stopped chasing FTP and started chasing consistency. Went from 3 rides a week to 5 shorter ones. Everything got better.", "Steamboat Gravel · 8 hrs/week · Age 50"),
        ("Olivia N.", "The course description for BWR was more accurate than anything the race organizer published. I knew every climb before I got there.", "BWR finisher · 9 hrs/week · Data analyst"),
        ("Marcus W.", "I'm a big rider, 210 lbs. Matti never once tried to make me a climber. He made me a finisher.", "Unbound 200 · 8 hrs/week · 210 lbs · Clydesdale"),
        ("Erin M.", "My training plan had me doing less in the last 3 weeks than I wanted. I was furious. Then I had the best race of my life.", "Mid South finisher · 7 hrs/week · Type-A personality"),
        ("Carl J.", "Finished Grinduro with the best combined time I've ever posted. The interval work was minimal but targeted.", "Grinduro · 9 hrs/week · MTB background"),
        ("Stephanie H.", "I signed up after reading the Unbound race profile. The detail convinced me this person knows gravel. The coaching confirmed it.", "Unbound 200 · 8 hrs/week · Found via race database"),
    ]


def build_testimonials() -> str:
    testimonials = _testimonial_data()
    cards = []
    for name, quote, meta in testimonials:
        cards.append(
            f'<blockquote class="rl-about-testimonial">'
            f'<p>{esc(quote)}</p>'
            f'<footer><strong>{esc(name)}</strong>'
            f'<span class="rl-about-testimonial-meta">{meta}</span>'
            f'</footer></blockquote>'
        )
    inner = "\n        ".join(cards)
    return f'''<div class="rl-section" id="results">
    <div class="rl-section-header">
      <span class="rl-section-kicker">05</span>
      <h2 class="rl-section-title">Athlete Results</h2>
    </div>
    <div class="rl-section-body" style="position:relative">
      <div class="rl-about-carousel" id="rl-testimonial-carousel">
        <div class="rl-about-carousel-track">
        {inner}
        </div>
      </div>
      <div class="rl-about-carousel-nav">
        <button class="rl-about-carousel-btn" id="rl-carousel-prev" aria-label="Previous testimonials">&larr;</button>
        <span class="rl-about-carousel-count" id="rl-carousel-count"></span>
        <button class="rl-about-carousel-btn" id="rl-carousel-next" aria-label="Next testimonials">&rarr;</button>
      </div>
    </div>
  </div>'''


def build_ctas() -> str:
    return f'''<div class="rl-section" id="cta">
    <div class="rl-section-body">
      <div class="rl-about-ctas">
        <div class="rl-about-cta">
          <h3>Training Plans</h3>
          <p data-ab="training_price">Race-specific. Built for your target event. Less than your race hotel &mdash; $2/day.</p>
          <a href="{SITE_BASE_URL}/questionnaire/" class="rl-about-cta-btn rl-about-cta-btn--gold" data-cta="training_plans" data-ab="training_cta_btn">BUILD MY PLAN</a>
        </div>
        <div class="rl-about-cta">
          <h3>1:1 Coaching</h3>
          <p data-ab="coaching_scarcity">A human in your corner. Adapts week to week. Limited spots &mdash; opens quarterly.</p>
          <a href="{SITE_BASE_URL}/coaching/apply/" class="rl-about-cta-btn rl-about-cta-btn--teal" data-cta="coaching_apply">APPLY</a>
        </div>
        <div class="rl-about-cta">
          <h3>Newsletter</h3>
          <p>Slow, Mid, 38s &mdash; essays on training, meaning, and not majoring in the minors.</p>
          <a href="{SUBSTACK_URL}" target="_blank" rel="noopener" class="rl-about-cta-btn" data-cta="newsletter">SUBSCRIBE</a>
        </div>
      </div>
    </div>
  </div>'''


def build_footer() -> str:
    return get_mega_footer_html()


def build_about_css() -> str:
    """Additional CSS specific to the about page — brand guide component patterns."""
    return '''<style>
/* ── About hero — light sandwash override ────────── */
.rl-neo-brutalist-page .rl-about-hero {
  background: var(--rl-color-cool-white);
  border-bottom: 3px double var(--rl-color-dark-navy);
}
.rl-neo-brutalist-page .rl-about-hero h1 {
  color: var(--rl-color-dark-navy);
}
.rl-neo-brutalist-page .rl-about-hero .rl-hero-tagline {
  color: var(--rl-color-secondary-blue);
}

/* ── About page — prose ─────────────────────────── */
.rl-neo-brutalist-page .rl-about-prose {
  font-family: var(--rl-font-editorial);
  font-size: var(--rl-font-size-base);
  line-height: var(--rl-line-height-prose);
  color: var(--rl-color-dark-navy);
  margin-bottom: var(--rl-spacing-md);
  max-width: 640px;
}

/* ── Highlighted paragraph (brand guide pattern) ─── */
.rl-neo-brutalist-page .rl-about-highlight {
  border-left: 4px solid var(--rl-color-signal-red);
  padding: var(--rl-spacing-md) var(--rl-spacing-lg);
  background: var(--rl-color-silver);
  margin: var(--rl-spacing-lg) 0;
}
.rl-neo-brutalist-page .rl-about-highlight--gold {
  border-left-color: var(--rl-color-orange);
}
.rl-neo-brutalist-page .rl-about-highlight p {
  font-family: var(--rl-font-editorial);
  font-size: var(--rl-font-size-md);
  font-weight: var(--rl-font-weight-semibold);
  line-height: var(--rl-line-height-relaxed);
  color: var(--rl-color-dark-navy);
  margin: 0;
}

/* ── Stat cards — light sandwash ─────────────────── */
.rl-neo-brutalist-page .rl-about-stats {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 0;
  background: var(--rl-color-cool-white);
  border: var(--rl-border-standard);
  border-top: 3px double var(--rl-color-dark-navy);
  border-bottom: 3px double var(--rl-color-dark-navy);
  margin-bottom: var(--rl-spacing-xl);
}
.rl-neo-brutalist-page .rl-about-stat {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: var(--rl-spacing-lg) var(--rl-spacing-sm);
  border-right: 1px solid var(--rl-color-silver);
}
.rl-neo-brutalist-page .rl-about-stat:last-child {
  border-right: none;
}
.rl-neo-brutalist-page .rl-about-stat-number {
  font-family: var(--rl-font-editorial);
  font-size: var(--rl-font-size-3xl);
  font-weight: var(--rl-font-weight-bold);
  color: var(--rl-color-dark-navy);
  line-height: var(--rl-line-height-tight);
  letter-spacing: var(--rl-letter-spacing-tight);
}
.rl-neo-brutalist-page .rl-about-stat-label {
  font-family: var(--rl-font-data);
  font-size: var(--rl-font-size-2xs);
  font-weight: var(--rl-font-weight-bold);
  color: var(--rl-color-secondary-blue);
  text-transform: uppercase;
  letter-spacing: var(--rl-letter-spacing-wider);
  margin-top: var(--rl-spacing-xs);
}

/* ── Tabbed features — light with gold underline ─── */
.rl-neo-brutalist-page .rl-about-tabs {
  border: var(--rl-border-standard);
  background: var(--rl-color-cool-white);
}
.rl-neo-brutalist-page .rl-about-tabs-nav {
  display: flex;
  background: var(--rl-color-silver);
  border-bottom: 3px double var(--rl-color-dark-navy);
}
.rl-neo-brutalist-page .rl-about-tab {
  padding: var(--rl-spacing-sm) var(--rl-spacing-lg);
  font-family: var(--rl-font-data);
  font-size: var(--rl-font-size-2xs);
  font-weight: var(--rl-font-weight-bold);
  letter-spacing: var(--rl-letter-spacing-wider);
  text-transform: uppercase;
  color: var(--rl-color-secondary-blue);
  background: transparent;
  border: none;
  border-bottom: 3px solid transparent;
  cursor: pointer;
  transition: border-color var(--rl-transition-hover),
              color var(--rl-transition-hover);
}
.rl-neo-brutalist-page .rl-about-tab:hover {
  color: var(--rl-color-dark-navy);
}
.rl-neo-brutalist-page .rl-about-tab--active {
  color: var(--rl-color-dark-navy);
  border-bottom-color: var(--rl-color-orange);
}
.rl-neo-brutalist-page .rl-about-tab-panel {
  display: none;
  padding: var(--rl-spacing-lg);
}
.rl-neo-brutalist-page .rl-about-tab-panel--active {
  display: block;
}
.rl-neo-brutalist-page .rl-about-tab-panel p {
  font-family: var(--rl-font-editorial);
  font-size: var(--rl-font-size-sm);
  line-height: var(--rl-line-height-prose);
  color: var(--rl-color-dark-navy);
  margin: 0;
  max-width: 640px;
}

/* ── Bio layout with sidebar card ──────────────── */
.rl-neo-brutalist-page .rl-about-bio {
  display: grid;
  grid-template-columns: 1fr 280px;
  gap: var(--rl-spacing-xl);
  align-items: start;
}
.rl-neo-brutalist-page .rl-about-bio-avatar {
  display: block;
  width: 100%;
  max-width: 280px;
  height: auto;
  border: var(--rl-border-standard);
  background: var(--rl-color-cool-white);
  margin-bottom: var(--rl-spacing-md);
}
.rl-neo-brutalist-page .rl-about-bio-card {
  border: var(--rl-border-standard);
  background: var(--rl-color-silver);
}
.rl-neo-brutalist-page .rl-about-bio-card-label {
  padding: var(--rl-spacing-xs) var(--rl-spacing-md);
  background: var(--rl-color-primary-navy);
  font-family: var(--rl-font-data);
  font-size: var(--rl-font-size-2xs);
  font-weight: var(--rl-font-weight-bold);
  letter-spacing: var(--rl-letter-spacing-extreme);
  text-transform: uppercase;
  color: var(--rl-color-cool-white);
  border-bottom: var(--rl-border-standard);
}
.rl-neo-brutalist-page .rl-about-bio-dl {
  padding: var(--rl-spacing-md);
}
.rl-neo-brutalist-page .rl-about-bio-dl dt {
  font-family: var(--rl-font-data);
  font-size: var(--rl-font-size-2xs);
  font-weight: var(--rl-font-weight-bold);
  letter-spacing: var(--rl-letter-spacing-wider);
  text-transform: uppercase;
  color: var(--rl-color-orange);
  margin-top: var(--rl-spacing-sm);
}
.rl-neo-brutalist-page .rl-about-bio-dl dt:first-child {
  margin-top: 0;
}
.rl-neo-brutalist-page .rl-about-bio-dl dd {
  font-family: var(--rl-font-data);
  font-size: var(--rl-font-size-sm);
  color: var(--rl-color-dark-navy);
  margin-top: var(--rl-spacing-2xs);
}

/* ── Coaching pillars (brand guide principle-card) ── */
.rl-neo-brutalist-page .rl-about-pillars {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: var(--rl-spacing-md);
}
.rl-neo-brutalist-page .rl-about-pillar {
  border: var(--rl-border-standard);
  padding: var(--rl-spacing-lg);
  background: var(--rl-color-cool-white);
  transition: border-color var(--rl-transition-hover);
}
.rl-neo-brutalist-page .rl-about-pillar:hover {
  border-color: var(--rl-color-orange);
}
.rl-neo-brutalist-page .rl-about-pillar-kicker {
  font-family: var(--rl-font-data);
  font-size: var(--rl-font-size-2xs);
  font-weight: var(--rl-font-weight-bold);
  letter-spacing: var(--rl-letter-spacing-extreme);
  text-transform: uppercase;
  color: var(--rl-color-orange);
  margin-bottom: var(--rl-spacing-sm);
}
.rl-neo-brutalist-page .rl-about-pillar h3 {
  font-family: var(--rl-font-editorial);
  font-size: var(--rl-font-size-lg);
  font-weight: var(--rl-font-weight-bold);
  color: var(--rl-color-dark-navy);
  margin: 0 0 var(--rl-spacing-sm) 0;
  line-height: var(--rl-line-height-tight);
}
.rl-neo-brutalist-page .rl-about-pillar p {
  font-family: var(--rl-font-editorial);
  font-size: var(--rl-font-size-sm);
  line-height: var(--rl-line-height-relaxed);
  color: var(--rl-color-dark-navy);
  margin: 0;
}

/* ── Testimonial carousel ────────────────────────── */
.rl-neo-brutalist-page .rl-about-carousel {
  overflow-x: auto;
  scroll-snap-type: x mandatory;
  -webkit-overflow-scrolling: touch;
  scrollbar-width: none;
}
.rl-neo-brutalist-page .rl-about-carousel::-webkit-scrollbar {
  display: none;
}
.rl-neo-brutalist-page .rl-about-carousel-track {
  display: flex;
  gap: var(--rl-spacing-md);
}
.rl-neo-brutalist-page .rl-about-testimonial {
  flex: 0 0 calc(50% - 8px);
  scroll-snap-align: start;
  background: var(--rl-color-cool-white);
  border: var(--rl-border-standard);
  padding: var(--rl-spacing-lg) var(--rl-spacing-lg) var(--rl-spacing-md);
  margin: 0;
  position: relative;
  min-height: 200px;
  display: flex;
  flex-direction: column;
}
.rl-neo-brutalist-page .rl-about-testimonial p {
  font-family: var(--rl-font-editorial);
  font-size: var(--rl-font-size-sm);
  font-style: italic;
  line-height: var(--rl-line-height-prose);
  color: var(--rl-color-dark-navy);
  margin: 0 0 var(--rl-spacing-md) 0;
  flex: 1;
}
.rl-neo-brutalist-page .rl-about-testimonial footer {
  display: flex;
  flex-direction: column;
  gap: var(--rl-spacing-2xs);
  border-top: 1px solid var(--rl-color-silver);
  padding-top: var(--rl-spacing-sm);
}
.rl-neo-brutalist-page .rl-about-testimonial footer strong {
  font-family: var(--rl-font-data);
  font-size: var(--rl-font-size-sm);
  font-weight: var(--rl-font-weight-bold);
  color: var(--rl-color-dark-navy);
  letter-spacing: var(--rl-letter-spacing-wide);
}
.rl-neo-brutalist-page .rl-about-testimonial-meta {
  font-family: var(--rl-font-data);
  font-size: var(--rl-font-size-2xs);
  color: var(--rl-color-secondary-blue);
  letter-spacing: var(--rl-letter-spacing-wide);
}
/* Carousel nav */
.rl-neo-brutalist-page .rl-about-carousel-nav {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--rl-spacing-md);
  margin-top: var(--rl-spacing-md);
}
.rl-neo-brutalist-page .rl-about-carousel-btn {
  background: var(--rl-color-silver);
  border: var(--rl-border-standard);
  width: 40px;
  height: 40px;
  font-size: 18px;
  line-height: 1;
  color: var(--rl-color-dark-navy);
  cursor: pointer;
  transition: background-color var(--rl-transition-hover),
              border-color var(--rl-transition-hover);
}
.rl-neo-brutalist-page .rl-about-carousel-btn:hover {
  background-color: var(--rl-color-cool-white);
  border-color: var(--rl-color-orange);
}
.rl-neo-brutalist-page .rl-about-carousel-count {
  font-family: var(--rl-font-data);
  font-size: var(--rl-font-size-2xs);
  font-weight: var(--rl-font-weight-bold);
  color: var(--rl-color-secondary-blue);
  letter-spacing: var(--rl-letter-spacing-wider);
  text-transform: uppercase;
  min-width: 80px;
  text-align: center;
}

/* ── CTA grid ────────────────────────────────────── */
.rl-neo-brutalist-page .rl-about-ctas {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: var(--rl-spacing-lg);
}
.rl-neo-brutalist-page .rl-about-cta {
  border: var(--rl-border-standard);
  padding: var(--rl-spacing-lg);
  background: var(--rl-color-cool-white);
  display: flex;
  flex-direction: column;
  transition: border-color var(--rl-transition-hover);
}
.rl-neo-brutalist-page .rl-about-cta:hover {
  border-color: var(--rl-color-orange);
}
.rl-neo-brutalist-page .rl-about-cta h3 {
  font-family: var(--rl-font-data);
  font-size: var(--rl-font-size-xs);
  font-weight: var(--rl-font-weight-bold);
  text-transform: uppercase;
  letter-spacing: var(--rl-letter-spacing-wider);
  color: var(--rl-color-primary-navy);
  margin: 0 0 var(--rl-spacing-xs) 0;
}
.rl-neo-brutalist-page .rl-about-cta p {
  font-family: var(--rl-font-editorial);
  font-size: var(--rl-font-size-sm);
  line-height: var(--rl-line-height-relaxed);
  color: var(--rl-color-dark-navy);
  margin: 0 0 var(--rl-spacing-md) 0;
  flex: 1;
}
.rl-neo-brutalist-page .rl-about-cta-btn {
  display: inline-block;
  background: var(--rl-color-primary-navy);
  color: var(--rl-color-cool-white);
  font-family: var(--rl-font-data);
  font-size: var(--rl-font-size-2xs);
  font-weight: var(--rl-font-weight-bold);
  text-transform: uppercase;
  letter-spacing: var(--rl-letter-spacing-wider);
  padding: var(--rl-spacing-sm) var(--rl-spacing-lg);
  border: 3px solid var(--rl-color-primary-navy);
  text-decoration: none;
  text-align: center;
  transition: background-color var(--rl-transition-hover),
              border-color var(--rl-transition-hover),
              color var(--rl-transition-hover);
}
.rl-neo-brutalist-page .rl-about-cta-btn:hover {
  background-color: var(--rl-color-dark-navy);
  border-color: var(--rl-color-dark-navy);
}
.rl-neo-brutalist-page .rl-about-cta-btn--gold {
  background: var(--rl-color-orange);
  color: var(--rl-color-cool-white);
  border-color: var(--rl-color-orange);
}
.rl-neo-brutalist-page .rl-about-cta-btn--gold:hover {
  background-color: var(--rl-color-dark-navy);
  border-color: var(--rl-color-dark-navy);
  color: var(--rl-color-cool-white);
}
.rl-neo-brutalist-page .rl-about-cta-btn--teal {
  background: var(--rl-color-signal-red);
  color: var(--rl-color-cool-white);
  border-color: var(--rl-color-signal-red);
}
.rl-neo-brutalist-page .rl-about-cta-btn--teal:hover {
  background-color: var(--rl-color-dark-navy);
  border-color: var(--rl-color-dark-navy);
  color: var(--rl-color-cool-white);
}

/* ── Methodology link ────────────────────────────── */
.rl-neo-brutalist-page .rl-about-link {
  color: var(--rl-color-signal-red);
  font-family: var(--rl-font-data);
  font-size: var(--rl-font-size-sm);
  font-weight: var(--rl-font-weight-bold);
  text-decoration: none;
  letter-spacing: var(--rl-letter-spacing-wide);
  border-bottom: 2px solid var(--rl-color-signal-red);
  padding-bottom: 2px;
  transition: border-color var(--rl-transition-hover),
              color var(--rl-transition-hover);
}
.rl-neo-brutalist-page .rl-about-link:hover {
  color: var(--rl-color-orange);
  border-color: var(--rl-color-orange);
}

/* ── Responsive ──────────────────────────────────── */
@media (max-width: 768px) {
  .rl-neo-brutalist-page .rl-about-stats {
    grid-template-columns: repeat(2, 1fr);
  }
  .rl-neo-brutalist-page .rl-about-stat {
    border-right: none;
    border-bottom: 1px solid var(--rl-color-silver);
  }
  .rl-neo-brutalist-page .rl-about-stat:nth-child(odd) {
    border-right: 1px solid var(--rl-color-silver);
  }
  .rl-neo-brutalist-page .rl-about-stat:nth-last-child(-n+2) {
    border-bottom: none;
  }
  .rl-neo-brutalist-page .rl-about-bio {
    grid-template-columns: 1fr;
  }
  .rl-neo-brutalist-page .rl-about-pillars {
    grid-template-columns: 1fr;
  }
  .rl-neo-brutalist-page .rl-about-testimonial {
    flex: 0 0 calc(100% - 16px);
  }
  .rl-neo-brutalist-page .rl-about-ctas {
    grid-template-columns: 1fr;
  }
  .rl-neo-brutalist-page .rl-about-tabs-nav {
    flex-wrap: wrap;
  }
}
</style>'''


def build_about_js() -> str:
    """Interactive JS for about page tabs and testimonial carousel."""
    return '''<script>
// About page tabs
document.querySelectorAll('[data-about-tabs]').forEach(function(tabs) {
  tabs.querySelectorAll('.rl-about-tab').forEach(function(tab) {
    tab.addEventListener('click', function() {
      tabs.querySelectorAll('.rl-about-tab').forEach(function(t) { t.classList.remove('rl-about-tab--active'); });
      tabs.querySelectorAll('.rl-about-tab-panel').forEach(function(p) { p.classList.remove('rl-about-tab-panel--active'); });
      tab.classList.add('rl-about-tab--active');
      var panel = tabs.querySelector('[data-about-panel="' + tab.getAttribute('data-about-tab') + '"]');
      if (panel) panel.classList.add('rl-about-tab-panel--active');
      if (typeof gtag === 'function') gtag('event', 'about_tab_click', { tab_name: tab.getAttribute('data-about-tab') });
    });
  });
});

// Testimonial carousel
(function() {
  var carousel = document.getElementById('rl-testimonial-carousel');
  var prev = document.getElementById('rl-carousel-prev');
  var next = document.getElementById('rl-carousel-next');
  var counter = document.getElementById('rl-carousel-count');
  if (!carousel || !prev || !next) return;
  var cards = carousel.querySelectorAll('.rl-about-testimonial');
  var total = cards.length;
  var perPage = window.innerWidth <= 768 ? 1 : 2;

  function getPage() {
    var scrollLeft = carousel.scrollLeft;
    var cardWidth = cards[0].offsetWidth + 16;
    return Math.round(scrollLeft / (cardWidth * perPage));
  }
  function totalPages() {
    return Math.ceil(total / perPage);
  }
  function updateCounter() {
    if (counter) counter.textContent = (getPage() + 1) + ' / ' + totalPages();
  }
  function scrollToPage(page) {
    var cardWidth = cards[0].offsetWidth + 16;
    carousel.scrollTo({ left: page * perPage * cardWidth, behavior: 'smooth' });
  }
  prev.addEventListener('click', function() {
    var page = getPage();
    if (page > 0) scrollToPage(page - 1);
    else scrollToPage(totalPages() - 1);
  });
  next.addEventListener('click', function() {
    var page = getPage();
    if (page < totalPages() - 1) scrollToPage(page + 1);
    else scrollToPage(0);
  });
  carousel.addEventListener('scroll', function() { updateCounter(); });
  window.addEventListener('resize', function() {
    perPage = window.innerWidth <= 768 ? 1 : 2;
    updateCounter();
  });
  updateCounter();

  // Auto-rotate every 5 seconds, pause on hover or manual interaction
  var autoTimer = null;
  var paused = false;
  function autoAdvance() {
    if (paused) return;
    var page = getPage();
    if (page < totalPages() - 1) scrollToPage(page + 1);
    else scrollToPage(0);
  }
  function startAuto() { autoTimer = setInterval(autoAdvance, 5000); }
  function stopAuto() { clearInterval(autoTimer); }
  carousel.addEventListener('mouseenter', function() { paused = true; });
  carousel.addEventListener('mouseleave', function() { paused = false; });
  prev.addEventListener('click', function() { stopAuto(); startAuto(); if (typeof gtag === 'function') gtag('event', 'about_carousel', { action: 'prev' }); });
  next.addEventListener('click', function() { stopAuto(); startAuto(); if (typeof gtag === 'function') gtag('event', 'about_carousel', { action: 'next' }); });
  startAuto();
})();

// CTA click tracking
document.querySelectorAll('[data-cta]').forEach(function(el) {
  el.addEventListener('click', function() {
    if (typeof gtag === 'function') gtag('event', 'about_cta_click', { cta_name: el.getAttribute('data-cta') });
  });
});

// Scroll depth milestones
(function() {
  if (typeof gtag !== 'function' || !('IntersectionObserver' in window)) return;
  var sections = [
    { id: 'why', label: 'why_this_exists' },
    { id: 'what', label: 'what_i_built' },
    { id: 'who', label: 'whos_behind_this' },
    { id: 'coaching', label: 'how_i_coach' },
    { id: 'results', label: 'athlete_results' },
    { id: 'cta', label: 'cta_section' }
  ];
  sections.forEach(function(s) {
    var el = document.getElementById(s.id);
    if (!el) return;
    new IntersectionObserver(function(entries, obs) {
      if (entries[0].isIntersecting) {
        gtag('event', 'about_scroll_depth', { section: s.label });
        obs.unobserve(el);
      }
    }, { threshold: 0.3 }).observe(el);
  });
})();
</script>'''


def build_jsonld(race_count: int) -> str:
    """Build WebPage + Person JSON-LD for the about page."""
    webpage = {
        "@context": "https://schema.org",
        "@type": "WebPage",
        "name": "About Road Labs — Race Intelligence & Coaching for Gravel Cyclists",
        "description": f"The story behind the internet's most comprehensive gravel race database. {race_count} races scored across 15 dimensions, plus coaching that works for people with real lives.",
        "url": f"{SITE_BASE_URL}/about/",
        "isPartOf": {
            "@type": "WebSite",
            "name": "Road Labs",
            "url": SITE_BASE_URL,
        },
    }
    person = {
        "@context": "https://schema.org",
        "@type": "Person",
        "name": "Matti Rowe",
        "jobTitle": "Head Coach",
        "worksFor": {
            "@type": "Organization",
            "name": "Road Labs",
            "url": SITE_BASE_URL,
        },
    }
    wp_tag = f'<script type="application/ld+json">{json.dumps(webpage, separators=(",", ":"))} </script>'
    person_tag = f'<script type="application/ld+json">{json.dumps(person, separators=(",", ":"))} </script>'
    return f'{wp_tag}\n  {person_tag}'


# ── Assemble page ──────────────────────────────────────────────


def generate_about_page(external_assets: dict = None) -> str:
    race_count = load_race_count()
    canonical_url = f"{SITE_BASE_URL}/about/"

    nav = build_nav()
    hero = build_hero(race_count)
    why = build_why_this_exists()
    what = build_what_we_built(race_count)
    who = build_who()
    coaching = build_coaching()
    testimonials = build_testimonials()
    ctas = build_ctas()
    footer = build_footer()
    about_css = build_about_css()
    about_js = build_about_js()
    jsonld = build_jsonld(race_count)

    if external_assets:
        page_css = external_assets['css_tag']
        inline_js = external_assets['js_tag']
    else:
        page_css = get_page_css()
        inline_js = build_inline_js()

    meta_desc = f"The story behind the internet&#39;s most comprehensive gravel race database. {race_count} races scored across 15 dimensions, plus coaching that works for people with real lives."

    og_tags = f'''<meta property="og:title" content="About Road Labs — Race Intelligence &amp; Coaching for Gravel Cyclists">
  <meta property="og:description" content="The story behind the internet&#39;s most comprehensive gravel race database. {race_count} races scored across 15 dimensions.">
  <meta property="og:type" content="website">
  <meta property="og:url" content="{esc(canonical_url)}">
  <meta property="og:image" content="{SITE_BASE_URL}/og/homepage.jpg">
  <meta property="og:image:width" content="1200">
  <meta property="og:image:height" content="630">
  <meta property="og:site_name" content="Road Labs">
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:title" content="About Road Labs — Race Intelligence &amp; Coaching for Gravel Cyclists">
  <meta name="twitter:description" content="{race_count} gravel races scored across 15 dimensions. Zero sponsors. Plus coaching that works for people with real lives.">
  <meta name="twitter:image" content="{SITE_BASE_URL}/og/homepage.jpg">'''

    preload = get_preload_hints()

    return f'''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>About Road Labs — Race Intelligence &amp; Coaching for Gravel Cyclists</title>
  <meta name="description" content="{meta_desc}">
  <meta name="robots" content="index, follow">
  <link rel="canonical" href="{esc(canonical_url)}">
  <link rel="preconnect" href="https://www.googletagmanager.com" crossorigin>
  {preload}
  {og_tags}
  {jsonld}
  {page_css}
  {about_css}
  {get_ga4_head_snippet()}
  {get_ab_head_snippet()}
</head>
<body>

<div class="rl-neo-brutalist-page">
  {nav}

  {hero}

  {why}

  {what}

  {who}

  {coaching}

  {testimonials}

  {ctas}

  {footer}
</div>

{inline_js}
{about_js}

{get_consent_banner_html()}
</body>
</html>'''


def main():
    parser = argparse.ArgumentParser(description="Generate Road Labs about page")
    parser.add_argument("--output-dir", default=str(OUTPUT_DIR), help="Output directory")
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Reuse shared assets if they exist, otherwise write them
    assets = write_shared_assets(output_dir)

    html_content = generate_about_page(external_assets=assets)
    output_file = output_dir / "about.html"
    output_file.write_text(html_content, encoding="utf-8")
    print(f"Generated {output_file} ({len(html_content):,} bytes)")


if __name__ == "__main__":
    main()
