"""Shared site header used by all generated pages.

Provides get_site_header_html() and get_site_header_css() for a consistent
6-item dropdown nav (RACES, PRODUCTS, COURSES, SERVICES, ARTICLES, ABOUT) across
homepage, race profiles, coaching, about, prep kits, series hubs, guide,
methodology, state hubs, vs pages, power rankings, calendar, tier hubs,
and coaching apply pages.
"""
from __future__ import annotations

SITE_BASE_URL = "https://roadielabs.com"
SUBSTACK_URL = "https://gravelgodcycling.substack.com"  # TODO: Roadie Labs newsletter

LOGO_SVG = '''<svg class="rl-site-header-mark" viewBox="0 0 800 1200" aria-hidden="true" focusable="false">
  <defs><mask id="rl-slick-grooves"><rect width="800" height="1200" fill="white"/><g fill="none" stroke="black" stroke-width="16" stroke-linecap="round"><path d="M206 220 274 264M184 328 258 372M174 450 250 492M174 750 250 708M184 872 258 828M206 980 274 936"/><path d="M594 220 526 264M616 328 542 372M626 450 550 492M626 750 550 708M616 872 542 828M594 980 526 936"/></g><g fill="none" stroke="black" stroke-width="23" stroke-linecap="round" stroke-linejoin="round"><path d="M278 302 278 886"/><path d="M278 316H326C382 316 402 354 402 405 402 456 378 492 326 492H278"/><path d="M328 492 410 886"/><path d="M476 302 476 886 580 848"/></g><g fill="none" stroke="black" stroke-width="11" stroke-linecap="round"><path d="M306 608 354 582M318 682 367 656M330 756 380 730"/><path d="M505 438 548 416M505 534 552 510M505 630 556 604M505 726 560 698"/></g></mask></defs>
  <path fill="currentColor" mask="url(#rl-slick-grooves)" d="M400 30C510 30 572 101 602 226 631 347 635 853 602 974 568 1099 510 1170 400 1170S232 1099 198 974C165 853 169 347 198 226 228 101 290 30 400 30Z"/>
</svg>'''


def get_site_header_html(active: str | None = None) -> str:
    """Return the shared site header HTML block.

    Args:
        active: Which top-level nav item is current. One of:
                "races", "products", "courses", "services", "articles", "about".
                Adds aria-current="page" to the matching top-level link.
    """

    def _aria(key: str) -> str:
        return ' aria-current="page"' if active == key else ""

    return f'''<header class="rl-site-header">
  <div class="rl-site-header-inner">
    <a href="{SITE_BASE_URL}/" class="rl-site-header-logo" aria-label="Roadie Labs">
      {LOGO_SVG}
    </a>
    <button class="rl-site-header-toggle" type="button" aria-controls="rl-site-header-nav" aria-expanded="false" aria-label="Open navigation">
      <span></span><span></span><span></span>
    </button>
    <nav class="rl-site-header-nav" id="rl-site-header-nav">
      <div class="rl-site-header-item">
        <a href="{SITE_BASE_URL}/road-races/"{_aria("races")}>RACES</a>
        <div class="rl-site-header-dropdown">
          <a href="{SITE_BASE_URL}/road-races/">All Road Races</a>
          <a href="{SITE_BASE_URL}/race/methodology/">How We Rate</a>
        </div>
      </div>
      <div class="rl-site-header-item">
        <a href="{SITE_BASE_URL}/training-plans/"{_aria("products")}>PRODUCTS</a>
        <div class="rl-site-header-dropdown">
          <a href="{SITE_BASE_URL}/training-plans/">Custom Training Plans</a>
          <a href="{SITE_BASE_URL}/courses/">Courses</a>
        </div>
      </div>
      <a href="{SITE_BASE_URL}/courses/"{_aria("courses")}>COURSES</a>
      <a href="{SITE_BASE_URL}/coaching/"{_aria("services")}>SERVICES</a>
      <a href="{SUBSTACK_URL}" target="_blank" rel="noopener"{_aria("articles")}>ARTICLES</a>
      <a href="{SITE_BASE_URL}/about/"{_aria("about")}>ABOUT</a>
    </nav>
  </div>
</header>'''


def get_site_header_css() -> str:
    """Return the site header CSS using var(--rl-*) design tokens."""
    return """
/* ── Site Header ──────────────────────────────────────── */
.rl-site-header { position: sticky; top: 0; z-index: 900; padding: 16px 24px; border-bottom: 2px solid var(--rl-color-orange); background: var(--rl-color-cool-white); }
.rl-site-header-inner { display: flex; align-items: center; justify-content: space-between; max-width: 960px; margin: 0 auto; }
.rl-site-header-logo { display: block; color: var(--rl-color-dark-navy); }
.rl-site-header-logo svg { display: block; height: 58px; width: auto; }
.rl-site-header-nav { display: flex; gap: 24px; align-items: center; }
.rl-site-header-toggle { display: none; width: 44px; height: 44px; padding: 10px; border: 2px solid var(--rl-color-dark-navy); background: var(--rl-color-cool-white); cursor: pointer; }
.rl-site-header-toggle span { display: block; width: 100%; height: 2px; background: var(--rl-color-dark-navy); margin: 5px 0; transition: background-color 0.2s; }
.rl-site-header-toggle:hover { background: var(--rl-color-silver); }
.rl-site-header-nav > a,
.rl-site-header-item > a { color: var(--rl-color-dark-navy); text-decoration: none; font-family: var(--rl-font-data); font-size: 11px; font-weight: 700; letter-spacing: 2px; text-transform: uppercase; transition: color 0.2s; }
.rl-site-header-nav > a:hover,
.rl-site-header-item > a:hover { color: var(--rl-color-orange); }
.rl-site-header-nav > a[aria-current="page"],
.rl-site-header-item > a[aria-current="page"] { color: var(--rl-color-orange); }

/* Dropdown container */
.rl-site-header-item { position: relative; }
.rl-site-header-dropdown { display: none; position: absolute; top: 100%; left: 0; min-width: 200px; padding: 8px 0; background: var(--rl-color-cool-white); border: 2px solid var(--rl-color-dark-navy); z-index: 1000; }
.rl-site-header-item:hover .rl-site-header-dropdown,
.rl-site-header-item:focus-within .rl-site-header-dropdown { display: block; }
.rl-site-header-dropdown a { display: block; padding: 8px 16px; font-family: var(--rl-font-data); font-size: 11px; font-weight: 400; letter-spacing: 1px; color: var(--rl-color-dark-navy); text-decoration: none; transition: color 0.2s; }
.rl-site-header-dropdown a:hover { color: var(--rl-color-orange); }

@media (max-width: 600px) {
  .rl-site-header { padding: 8px 16px; }
  .rl-site-header-inner { flex-wrap: wrap; justify-content: space-between; gap: 8px; }
  .rl-site-header-logo svg { height: 46px; }
  .rl-site-header-toggle { display: inline-flex; flex-direction: column; align-items: center; justify-content: center; }
  .rl-site-header-nav { display: none; width: 100%; flex-direction: column; align-items: stretch; gap: 0; border-top: 2px solid var(--rl-color-dark-navy); padding-top: 8px; }
  .rl-site-header-nav.is-open { display: flex; }
  .rl-site-header-item { width: 100%; }
  .rl-site-header-nav > a,
  .rl-site-header-item > a { display: flex; align-items: center; min-height: 44px; padding: 0 4px; font-size: 11px; letter-spacing: 1.5px; }
  .rl-site-header-dropdown { display: block; position: static; min-width: 0; padding: 0 0 8px 12px; border: 0; background: transparent; }
  .rl-site-header-dropdown a { min-height: 44px; display: flex; align-items: center; padding: 0 4px; font-size: 11px; }
}
"""


def get_site_header_js() -> str:
    """Return the shared header behavior without inline handlers."""
    return """
(function() {
  var toggle = document.querySelector('.rl-site-header-toggle');
  var nav = document.getElementById('rl-site-header-nav');
  if (!toggle || !nav) return;
  toggle.addEventListener('click', function() {
    var expanded = toggle.getAttribute('aria-expanded') === 'true';
    toggle.setAttribute('aria-expanded', expanded ? 'false' : 'true');
    toggle.setAttribute('aria-label', expanded ? 'Open navigation' : 'Close navigation');
    nav.classList.toggle('is-open', !expanded);
  });
})();
"""
