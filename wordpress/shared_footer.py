"""Shared mega-footer used by all generated pages.

Provides get_mega_footer_html() and get_mega_footer_css() for a consistent
6-column footer across homepage, race profiles, coaching, about, prep kits,
series hubs, and coaching apply pages.
"""
from __future__ import annotations

from datetime import date

SITE_BASE_URL = "https://roadlabs.cc"
SUBSTACK_URL = "https://TODO_ROADLABS_NEWSLETTER"  # TODO: Road Labs newsletter
CURRENT_YEAR = date.today().year


def get_mega_footer_html() -> str:
    """Return the shared mega-footer HTML block."""
    return f'''<footer class="rl-mega-footer">
  <div class="rl-mega-footer-grid">
    <div class="rl-mega-footer-col rl-mega-footer-brand">
      <h3 class="rl-mega-footer-brand-title">ROAD LABS</h3>
      <p class="rl-mega-footer-brand-tagline">Practical coaching and training for people with real lives who still want to go fast.</p>
    </div>
    <div class="rl-mega-footer-col">
      <h4 class="rl-mega-footer-heading">RACES</h4>
      <nav class="rl-mega-footer-links">
        <a href="{SITE_BASE_URL}/road-races/">All Road Races</a>
        <a href="{SITE_BASE_URL}/race/methodology/">How We Rate</a>
      </nav>
    </div>
    <div class="rl-mega-footer-col">
      <h4 class="rl-mega-footer-heading">PRODUCTS</h4>
      <nav class="rl-mega-footer-links">
        <a href="{SITE_BASE_URL}/products/training-plans/">Custom Training Plans</a>
        <a href="{SITE_BASE_URL}/guide/">Road Racing Handbook</a>
      </nav>
    </div>
    <div class="rl-mega-footer-col">
      <h4 class="rl-mega-footer-heading">SERVICES</h4>
      <nav class="rl-mega-footer-links">
        <a href="{SITE_BASE_URL}/coaching/">Coaching</a>
        <a href="{SITE_BASE_URL}/consulting/">Consulting</a>
      </nav>
    </div>
    <div class="rl-mega-footer-col">
      <h4 class="rl-mega-footer-heading">ARTICLES</h4>
      <nav class="rl-mega-footer-links">
        <a href="{SUBSTACK_URL}" target="_blank" rel="noopener">Slow Mid 38s</a>
        <a href="{SITE_BASE_URL}/articles/">Hot Takes</a>
        <a href="{SITE_BASE_URL}/insights/">The State of Road Racing</a>
        <a href="{SITE_BASE_URL}/fueling-methodology/">White Papers</a>
      </nav>
    </div>
    <div class="rl-mega-footer-col rl-mega-footer-newsletter">
      <h4 class="rl-mega-footer-heading">NEWSLETTER</h4>
      <p class="rl-mega-footer-newsletter-desc">Essays on training, meaning, and not majoring in the minors.</p>
      <a href="{SUBSTACK_URL}" class="rl-mega-footer-subscribe" target="_blank" rel="noopener" data-ga="subscribe_click" data-ga-label="mega_footer">SUBSCRIBE</a>
    </div>
  </div>
  <div class="rl-mega-footer-legal">
    <span>&copy; {CURRENT_YEAR} Road Labs. All rights reserved.</span>
    <nav class="rl-mega-footer-legal-links">
      <a href="{SITE_BASE_URL}/privacy/">Privacy</a>
      <a href="{SITE_BASE_URL}/terms/">Terms</a>
      <a href="{SITE_BASE_URL}/cookies/">Cookies</a>
    </nav>
  </div>
  <div class="rl-mega-footer-disclaimer">
    <p>This content is produced independently by Road Labs and is not affiliated with, endorsed by, or officially connected to any race organizer, event, or governing body mentioned on this page. All ratings, opinions, and assessments represent the editorial views of Road Labs based on publicly available information and community research. Race details are subject to change &mdash; always verify with official race sources.</p>
  </div>
</footer>'''


def get_mega_footer_css() -> str:
    """Return the mega-footer CSS using var(--rl-*) design tokens."""
    return """
/* ── Mega Footer ───────────────────────────────────────── */
.rl-mega-footer { background: var(--rl-color-dark-navy); border-top: var(--rl-border-gold); margin-top: var(--rl-spacing-xl); }
.rl-mega-footer-grid { display: grid; grid-template-columns: 1.5fr 1fr 1fr 1fr 1fr 1fr; gap: var(--rl-spacing-lg); padding: var(--rl-spacing-2xl) var(--rl-spacing-xl); max-width: 960px; margin: 0 auto; }
.rl-mega-footer-brand-title { font-family: var(--rl-font-data); font-size: var(--rl-font-size-sm); font-weight: var(--rl-font-weight-bold); letter-spacing: var(--rl-letter-spacing-ultra-wide); color: var(--rl-color-white); margin: 0 0 var(--rl-spacing-sm) 0; }
.rl-mega-footer-brand-tagline { font-family: var(--rl-font-editorial); font-size: var(--rl-font-size-xs); line-height: var(--rl-line-height-prose); color: var(--rl-color-silver); margin: 0; }
.rl-mega-footer-heading { font-family: var(--rl-font-data); font-size: var(--rl-font-size-2xs); font-weight: var(--rl-font-weight-bold); letter-spacing: var(--rl-letter-spacing-ultra-wide); text-transform: uppercase; color: var(--rl-color-orange); margin: 0 0 var(--rl-spacing-md) 0; }
.rl-mega-footer-links { display: flex; flex-direction: column; gap: var(--rl-spacing-xs); }
.rl-mega-footer-links a { color: var(--rl-color-silver); font-family: var(--rl-font-data); font-size: 12px; text-decoration: none; transition: color var(--rl-transition-hover); }
.rl-mega-footer-links a:hover { color: var(--rl-color-white); }
.rl-mega-footer-newsletter-desc { font-family: var(--rl-font-editorial); font-size: var(--rl-font-size-xs); color: var(--rl-color-silver); line-height: var(--rl-line-height-prose); margin: 0 0 var(--rl-spacing-md) 0; }
.rl-mega-footer-subscribe { display: inline-block; padding: var(--rl-spacing-xs) var(--rl-spacing-lg); font-family: var(--rl-font-data); font-size: 11px; font-weight: var(--rl-font-weight-bold); letter-spacing: var(--rl-letter-spacing-wider); background: var(--rl-color-signal-red); color: var(--rl-color-white); text-decoration: none; border: var(--rl-border-width-standard) solid var(--rl-color-signal-red); transition: background-color var(--rl-transition-hover), border-color var(--rl-transition-hover); }
.rl-mega-footer-subscribe:hover { background: transparent; border-color: var(--rl-color-signal-red); }
.rl-mega-footer-legal { padding: var(--rl-spacing-md) var(--rl-spacing-xl); border-top: 1px solid var(--rl-color-primary-navy); text-align: center; font-family: var(--rl-font-data); font-size: var(--rl-font-size-2xs); color: var(--rl-color-secondary-blue); letter-spacing: var(--rl-letter-spacing-wide); max-width: 960px; margin: 0 auto; display: flex; justify-content: center; align-items: center; gap: var(--rl-spacing-md); flex-wrap: wrap; }
.rl-mega-footer-legal-links { display: flex; gap: var(--rl-spacing-md); }
.rl-mega-footer-legal-links a { color: var(--rl-color-secondary-blue); text-decoration: none; transition: color var(--rl-transition-hover); }
.rl-mega-footer-legal-links a:hover { color: var(--rl-color-silver); }
.rl-mega-footer-disclaimer { padding: var(--rl-spacing-sm) var(--rl-spacing-xl) var(--rl-spacing-lg); max-width: 960px; margin: 0 auto; }
.rl-mega-footer-disclaimer p { font-family: var(--rl-font-editorial); font-size: var(--rl-font-size-2xs); color: var(--rl-color-secondary-blue); line-height: var(--rl-line-height-relaxed); margin: 0; text-align: center; }

/* Tablet: 3-column */
@media (max-width: 900px) {
  .rl-mega-footer-grid { grid-template-columns: 1fr 1fr 1fr; }
}

/* Mobile: 1-column */
@media (max-width: 600px) {
  .rl-mega-footer-grid { grid-template-columns: 1fr; gap: var(--rl-spacing-lg); padding: var(--rl-spacing-xl) var(--rl-spacing-md); }
  .rl-mega-footer-legal { padding: var(--rl-spacing-sm) var(--rl-spacing-md); }
  .rl-mega-footer-disclaimer { padding: var(--rl-spacing-sm) var(--rl-spacing-md) var(--rl-spacing-md); }
}
"""
