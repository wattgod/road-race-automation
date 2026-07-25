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

LOGO_SVG = '''<svg class="rl-site-header-mark" viewBox="0 0 800 1600" aria-hidden="true" focusable="false">
  <defs><mask id="rl-slick-grooves"><rect width="800" height="1600" fill="white"/><path d="M400 188V1412" fill="none" stroke="black" stroke-width="10" stroke-linecap="round"/><g fill="none" stroke="black" stroke-width="20" stroke-linecap="round"><path d="M270 380 300 390M310 380 340 390M350 380 380 390M270 470 300 480M350 470 380 480M270 560 300 570M350 560 380 570M270 650 300 660M310 650 340 660M350 650 380 660M270 740 300 750M310 740 340 750M270 830 300 840M350 830 380 840M270 920 300 930M350 920 380 930M270 1010 300 1020M350 1010 380 1020M270 1100 300 1110M350 1100 380 1110M270 1190 300 1200M350 1190 380 1200"/><path d="M420 390 450 380M420 480 450 470M420 570 450 560M420 660 450 650M420 750 450 740M420 840 450 830M420 930 450 920M420 1020 450 1010M420 1110 450 1100M420 1200 450 1190M460 1200 490 1190M500 1200 530 1190"/></g></mask></defs>
  <path fill="currentColor" mask="url(#rl-slick-grooves)" d="M400 24C490 24 535 140 552 320 570 520 570 1080 552 1280 535 1460 490 1576 400 1576S265 1460 248 1280C230 1080 230 520 248 320 265 140 310 24 400 24Z"/>
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
