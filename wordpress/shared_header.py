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
    <a href="{SITE_BASE_URL}/" class="rl-site-header-logo">
      <img src="data:image/svg+xml,%3Csvg%20xmlns%3D%27http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%27%20viewBox%3D%270%200%2050%2050%27%3E%3Crect%20width%3D%2750%27%20height%3D%2750%27%20fill%3D%27%231a1a1a%27%2F%3E%3Ctext%20x%3D%2725%27%20y%3D%2737%27%20text-anchor%3D%27middle%27%20font-family%3D%27serif%27%20font-size%3D%2734%27%20font-weight%3D%27700%27%20fill%3D%27%23f5f5f0%27%3ER%3C%2Ftext%3E%3C%2Fsvg%3E" alt="Roadie Labs" width="50" height="50">
    </a>
    <nav class="rl-site-header-nav">
      <div class="rl-site-header-item">
        <a href="{SITE_BASE_URL}/road-races/"{_aria("races")}>RACES</a>
        <div class="rl-site-header-dropdown">
          <a href="{SITE_BASE_URL}/road-races/">All Road Races</a>
          <a href="{SITE_BASE_URL}/race/methodology/">How We Rate</a>
        </div>
      </div>
      <div class="rl-site-header-item">
        <a href="{SITE_BASE_URL}/products/training-plans/"{_aria("products")}>PRODUCTS</a>
        <div class="rl-site-header-dropdown">
          <a href="{SITE_BASE_URL}/products/training-plans/">Custom Training Plans</a>
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
.rl-site-header { padding: 16px 24px; border-bottom: 2px solid var(--rl-color-orange); }
.rl-site-header-inner { display: flex; align-items: center; justify-content: space-between; max-width: 960px; margin: 0 auto; }
.rl-site-header-logo img { display: block; height: 50px; width: auto; }
.rl-site-header-nav { display: flex; gap: 24px; align-items: center; }
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

/* Mobile: flat nav, no dropdowns */
@media (max-width: 600px) {
  .rl-site-header { padding: 12px 16px; }
  .rl-site-header-inner { flex-wrap: wrap; justify-content: center; gap: 10px; }
  .rl-site-header-logo img { height: 40px; }
  .rl-site-header-nav { gap: 12px; flex-wrap: wrap; justify-content: center; }
  .rl-site-header-nav > a,
  .rl-site-header-item > a { font-size: 10px; letter-spacing: 1.5px; }
  .rl-site-header-dropdown { display: none !important; }
}
"""
