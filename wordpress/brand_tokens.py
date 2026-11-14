"""
Brand token helpers for Roadie Labs CSS generation.

Provides CSS custom properties (:root block), @font-face declarations,
and color mapping from the Roadie Labs design system.
"""

from pathlib import Path

# ── Paths ─────────────────────────────────────────────────────
BRAND_DIR = Path(__file__).resolve().parent.parent.parent / "road-labs-brand"
BRAND_FONTS_DIR = BRAND_DIR / "assets" / "fonts"

# 8 woff2 font files to self-host. Timing Slip (Nov 2026): JetBrains Mono
# (numbers, labels, data) + Source Serif 4 (race names, prose). JetBrains Mono
# replaced Sometype Mono; the files are vendored in road-labs-brand/assets/fonts
# (OFL, from @fontsource-variable/jetbrains-mono 5.1.1).
FONT_FILES = [
    "JetBrainsMono-normal-latin.woff2",
    "JetBrainsMono-normal-latin-ext.woff2",
    "JetBrainsMono-italic-latin.woff2",
    "JetBrainsMono-italic-latin-ext.woff2",
    "SourceSerif4-normal-latin.woff2",
    "SourceSerif4-normal-latin-ext.woff2",
    "SourceSerif4-italic-latin.woff2",
    "SourceSerif4-italic-latin-ext.woff2",
]  # Unbounded removed Jul 2026 — never deployed on road (fonts were Sometype Mono + Source Serif 4 then); every page 404'd its preload


# ── Analytics ─────────────────────────────────────────────────
GA_MEASUREMENT_ID = "G-WQ7W8XN11N"  # Roadie Labs - GA4 (properties/540984732, created Jun 2026)


def get_ga4_head_snippet() -> str:
    """Return consent defaults + GA4 loading scripts for <head>."""
    return (
        "<script>window.dataLayer=window.dataLayer||[];"
        "function gtag(){dataLayer.push(arguments)}"
        "gtag('consent','default',{"
        "'analytics_storage':/(^|; )rl_consent=accepted/.test(document.cookie)?'granted':'denied',"
        "'ad_storage':'denied','ad_user_data':'denied',"
        "'ad_personalization':'denied','wait_for_update':500});</script>\n"
        f'  <script async src="https://www.googletagmanager.com/gtag/js?id={GA_MEASUREMENT_ID}"></script>\n'
        f"  <script>gtag('js',new Date());gtag('config','{GA_MEASUREMENT_ID}');</script>"
    )


# ── Site ──────────────────────────────────────────────────────
SITE_BASE_URL = "https://roadielabs.com"
BRAND_NAME = "Roadie Labs"


def get_tokens_css() -> str:
    """Return the :root CSS custom properties block.

    Roadie Labs "Timing Slip" palette (Nov 2026): paper and ink, with four
    role colours that each mean one thing and nothing else:
      score   Maillot Red  #b3302a  the Lab Score and course ratings only
      opinion Col Blue     #2d5f8b  editorial / rider opinion ratings
      offer   Sprint Green #2e7a4f  the training offer only
      gold    Jersey Gold  #d99a1e  Tier 1 fill only, always with ink text
    Legacy token names (navy, signal-red, orange...) are kept so existing
    generators keep working; they now resolve to ink and graphite, never to a
    role colour. Depth (radius, raised, well) is opt-in per component via the
    --rl-radius-* / --rl-shadow-* tokens; --rl-border-radius stays 0.
    """
    return """:root {
  /* color — Roadie Labs "Timing Slip" palette */
  --rl-color-ink: #202322;
  --rl-color-paper: #fafaf8;
  --rl-color-graphite: #555555;
  --rl-color-score: #b3302a;
  --rl-color-opinion: #2d5f8b;
  --rl-color-offer: #2e7a4f;
  --rl-color-offer-dark: #276b46;
  --rl-color-tier-gold: #d99a1e;
  --rl-color-well: #efefea;
  --rl-color-zebra: #f2f2ed;
  --rl-color-dark-navy: #202322;
  --rl-color-primary-navy: #202322;
  --rl-color-secondary-blue: #555555;
  --rl-color-steel: #999999;
  --rl-color-light-steel: #b8b8b0;
  --rl-color-silver: #d0d0c8;
  --rl-color-cool-white: #fafaf8;
  --rl-color-signal-red: #202322;
  --rl-color-coral: #555555;
  --rl-color-orange: #555555;
  --rl-color-light-orange: #999999;
  --rl-color-near-black: #202322;
  --rl-color-white: #ffffff;
  --rl-color-error: #8b1a1a;
  --rl-color-tier-1: #202322;
  --rl-color-tier-2: #4a4a4a;
  --rl-color-tier-3: #6b6b6b;
  --rl-color-tier-4: #8a8a85;

  /* depth — Timing Slip raised card, sunken well, glyph tile */
  --rl-radius-sm: 5px;
  --rl-radius-md: 10px;
  --rl-radius-lg: 14px;
  --rl-shadow-raised: 0 0 0 1px rgba(0,0,0,0.08), inset 0 1px 0 #fff, 0 2px 4px rgba(0,0,0,0.05), 0 10px 24px rgba(0,0,0,0.07);
  --rl-shadow-raised-sm: 0 0 0 1px rgba(0,0,0,0.12), inset 0 1px 0 #fff, 0 1px 2px rgba(0,0,0,0.08);
  --rl-shadow-well: inset 0 1px 3px rgba(0,0,0,0.14), 0 1px 0 #fff;
  --rl-shadow-offer: inset 0 1px 0 rgba(255,255,255,0.3), 0 1px 2px rgba(0,0,0,0.2), 0 6px 14px rgba(46,122,79,0.22);
  --rl-gradient-raised: linear-gradient(180deg, #ffffff 0%, #f1f1ec 100%);
  --rl-gradient-offer: linear-gradient(180deg, #33885a 0%, #276b46 100%);

  /* font */
  --rl-font-data: 'JetBrains Mono', monospace;
  --rl-font-editorial: 'Source Serif 4', Georgia, serif;
  --rl-font-size-2xs: 10px;
  --rl-font-size-xs: 13px;
  --rl-font-size-sm: 14px;
  --rl-font-size-base: 16px;
  --rl-font-size-md: 18px;
  --rl-font-size-lg: 20px;
  --rl-font-size-xl: 24px;
  --rl-font-size-2xl: 28px;
  --rl-font-size-3xl: 42px;
  --rl-font-size-4xl: 48px;
  --rl-font-size-5xl: 56px;
  --rl-font-weight-regular: 400;
  --rl-font-weight-semibold: 600;
  --rl-font-weight-bold: 700;
  --rl-font-weight-black: 900;

  /* line-height */
  --rl-line-height-tight: 1.1;
  --rl-line-height-normal: 1.5;
  --rl-line-height-relaxed: 1.7;
  --rl-line-height-prose: 1.75;

  /* letter-spacing */
  --rl-letter-spacing-tight: -0.5px;
  --rl-letter-spacing-normal: 0;
  --rl-letter-spacing-wide: 1px;
  --rl-letter-spacing-wider: 2px;
  --rl-letter-spacing-ultra-wide: 3px;
  --rl-letter-spacing-extreme: 4px;
  --rl-letter-spacing-display: 6px;

  /* spacing */
  --rl-spacing-2xs: 4px;
  --rl-spacing-xs: 8px;
  --rl-spacing-sm: 12px;
  --rl-spacing-md: 16px;
  --rl-spacing-lg: 24px;
  --rl-spacing-xl: 32px;
  --rl-spacing-2xl: 48px;
  --rl-spacing-3xl: 64px;
  --rl-spacing-4xl: 96px;

  /* border */
  --rl-border-width-subtle: 2px;
  --rl-border-width-standard: 3px;
  --rl-border-width-heavy: 4px;
  --rl-border-color-default: #202322;
  --rl-border-color-brand: #202322;
  --rl-border-color-secondary: #555555;
  --rl-border-color-accent: #202322;
  --rl-border-radius: 0;

  /* animation */
  --rl-animation-duration-instant: 0ms;
  --rl-animation-duration-fast: 150ms;
  --rl-animation-duration-normal: 300ms;
  --rl-animation-duration-slow: 500ms;
  --rl-animation-easing-sharp: cubic-bezier(0.4, 0, 0.2, 1);
}

/* Composite tokens (derived) */
:root {
  --rl-border-subtle: var(--rl-border-width-subtle) solid var(--rl-border-color-default);
  --rl-border-standard: var(--rl-border-width-standard) solid var(--rl-border-color-default);
  --rl-border-heavy: var(--rl-border-width-heavy) solid var(--rl-border-color-default);
  --rl-border-double: var(--rl-border-width-heavy) double var(--rl-border-color-default);
  --rl-border-accent: var(--rl-border-width-standard) solid var(--rl-border-color-accent);
  --rl-border-brand: var(--rl-border-width-standard) solid var(--rl-border-color-brand);
  --rl-border-secondary: var(--rl-border-width-standard) solid var(--rl-border-color-secondary);
  --rl-transition-hover: var(--rl-animation-duration-normal) var(--rl-animation-easing-sharp);
}"""


def get_font_face_css(font_path_prefix: str = "/race/assets/fonts") -> str:
    """Return @font-face declarations for self-hosted fonts."""
    p = font_path_prefix.rstrip("/")
    return f"""/* JetBrains Mono — Normal — Latin Extended */
@font-face {{
  font-family: 'JetBrains Mono';
  font-style: normal;
  font-weight: 100 800;
  font-display: swap;
  src: url('{p}/JetBrainsMono-normal-latin-ext.woff2') format('woff2');
  unicode-range: U+0100-02AF, U+0304, U+0308, U+0329, U+1E00-1E9F, U+1EF2-1EFF, U+2020, U+20A0-20AB, U+20AD-20C0, U+2113, U+2C60-2C7F, U+A720-A7FF;
}}
/* JetBrains Mono — Normal — Latin */
@font-face {{
  font-family: 'JetBrains Mono';
  font-style: normal;
  font-weight: 100 800;
  font-display: swap;
  src: url('{p}/JetBrainsMono-normal-latin.woff2') format('woff2');
  unicode-range: U+0000-00FF, U+0131, U+0152-0153, U+02BB-02BC, U+02C6, U+02DA, U+02DC, U+0304, U+0308, U+0329, U+2000-206F, U+2074, U+20AC, U+2122, U+2191, U+2193, U+2212, U+2215, U+FEFF, U+FFFD;
}}
/* JetBrains Mono — Italic — Latin Extended */
@font-face {{
  font-family: 'JetBrains Mono';
  font-style: italic;
  font-weight: 100 800;
  font-display: swap;
  src: url('{p}/JetBrainsMono-italic-latin-ext.woff2') format('woff2');
  unicode-range: U+0100-02AF, U+0304, U+0308, U+0329, U+1E00-1E9F, U+1EF2-1EFF, U+2020, U+20A0-20AB, U+20AD-20C0, U+2113, U+2C60-2C7F, U+A720-A7FF;
}}
/* JetBrains Mono — Italic — Latin */
@font-face {{
  font-family: 'JetBrains Mono';
  font-style: italic;
  font-weight: 100 800;
  font-display: swap;
  src: url('{p}/JetBrainsMono-italic-latin.woff2') format('woff2');
  unicode-range: U+0000-00FF, U+0131, U+0152-0153, U+02BB-02BC, U+02C6, U+02DA, U+02DC, U+0304, U+0308, U+0329, U+2000-206F, U+2074, U+20AC, U+2122, U+2191, U+2193, U+2212, U+2215, U+FEFF, U+FFFD;
}}
/* Source Serif 4 — Normal — Latin Extended */
@font-face {{
  font-family: 'Source Serif 4';
  font-style: normal;
  font-weight: 400 700;
  font-display: swap;
  src: url('{p}/SourceSerif4-normal-latin-ext.woff2') format('woff2');
  unicode-range: U+0100-02BA, U+02BD-02C5, U+02C7-02CC, U+02CE-02D7, U+02DD-02FF, U+0304, U+0308, U+0329, U+1D00-1DBF, U+1E00-1E9F, U+1EF2-1EFF, U+2020, U+20A0-20AB, U+20AD-20C0, U+2113, U+2C60-2C7F, U+A720-A7FF;
}}
/* Source Serif 4 — Normal — Latin */
@font-face {{
  font-family: 'Source Serif 4';
  font-style: normal;
  font-weight: 400 700;
  font-display: swap;
  src: url('{p}/SourceSerif4-normal-latin.woff2') format('woff2');
  unicode-range: U+0000-00FF, U+0131, U+0152-0153, U+02BB-02BC, U+02C6, U+02DA, U+02DC, U+0304, U+0308, U+0329, U+2000-206F, U+20AC, U+2122, U+2191, U+2193, U+2212, U+2215, U+FEFF, U+FFFD;
}}
/* Source Serif 4 — Italic — Latin Extended */
@font-face {{
  font-family: 'Source Serif 4';
  font-style: italic;
  font-weight: 400 700;
  font-display: swap;
  src: url('{p}/SourceSerif4-italic-latin-ext.woff2') format('woff2');
  unicode-range: U+0100-02BA, U+02BD-02C5, U+02C7-02CC, U+02CE-02D7, U+02DD-02FF, U+0304, U+0308, U+0329, U+1D00-1DBF, U+1E00-1E9F, U+1EF2-1EFF, U+2020, U+20A0-20AB, U+20AD-20C0, U+2113, U+2C60-2C7F, U+A720-A7FF;
}}
/* Source Serif 4 — Italic — Latin */
@font-face {{
  font-family: 'Source Serif 4';
  font-style: italic;
  font-weight: 400 700;
  font-display: swap;
  src: url('{p}/SourceSerif4-italic-latin.woff2') format('woff2');
  unicode-range: U+0000-00FF, U+0131, U+0152-0153, U+02BB-02BC, U+02C6, U+02DA, U+02DC, U+0304, U+0308, U+0329, U+2000-206F, U+20AC, U+2122, U+2191, U+2193, U+2212, U+2215, U+FEFF, U+FFFD;
}}
"""


def get_preload_hints(font_path_prefix: str = "/race/assets/fonts") -> str:
    """Return <link rel=preload> tags for the Latin (most common) font subsets."""
    p = font_path_prefix.rstrip("/")
    return f"""<link rel="preload" href="{p}/JetBrainsMono-normal-latin.woff2" as="font" type="font/woff2" crossorigin>
  <link rel="preload" href="{p}/SourceSerif4-normal-latin.woff2" as="font" type="font/woff2" crossorigin>"""


# ── Color mapping for SVG attributes (can't use CSS vars) ────

COLORS = {
    "ink": "#202322",
    "paper": "#fafaf8",
    "graphite": "#555555",
    "score": "#b3302a",
    "opinion": "#2d5f8b",
    "offer": "#2e7a4f",
    "offer_dark": "#276b46",
    "tier_gold": "#d99a1e",
    "well": "#efefea",
    "zebra": "#f2f2ed",
    "dark_navy": "#202322",
    "primary_navy": "#202322",
    "secondary_blue": "#555555",
    "steel": "#999999",
    "light_steel": "#b8b8b0",
    "silver": "#d0d0c8",
    "cool_white": "#fafaf8",
    "signal_red": "#202322",
    "coral": "#555555",
    "orange": "#555555",
    "light_orange": "#999999",
    "near_black": "#202322",
    "white": "#ffffff",
    "tier_1": "#202322",
    "tier_2": "#4a4a4a",
    "tier_3": "#6b6b6b",
    "tier_4": "#8a8a85",
    # Legacy aliases
    "dark_brown": "#202322",
    "primary_brown": "#202322",
    "warm_paper": "#fafaf8",
}


# ── A/B Testing ──────────────────────────────────────────────


def get_ab_bootstrap_js() -> str:
    """Return the minified inline bootstrap JS."""
    return (
        '(function(){var s=localStorage.getItem("rl_ab_assign");'
        'if(!s)return;try{var a=JSON.parse(s);'
        'var c=localStorage.getItem("rl_ab_cache");'
        'if(!c)return;var cache=JSON.parse(c);'
        'for(var eid in a){if(!cache[eid])continue;'
        'var el=document.querySelector(cache[eid].sel);'
        'if(el)el.textContent=cache[eid].txt;}'
        '}catch(e){}})();'
    )


def get_ab_js_filename() -> str:
    """Return the cache-busted AB JS filename based on content hash."""
    import hashlib
    js_path = Path(__file__).resolve().parent.parent / "web" / "rl-ab-tests.js"
    if not js_path.exists():
        return "rl-ab-tests.js"
    content = js_path.read_text()
    js_hash = hashlib.md5(content.encode()).hexdigest()[:8]
    return f"rl-ab-tests.{js_hash}.js"


def get_ab_head_snippet() -> str:
    """Return inline bootstrap + deferred script tag for A/B tests."""
    bootstrap = get_ab_bootstrap_js()
    js_filename = get_ab_js_filename()
    return (
        f'<script>{bootstrap}</script>\n'
        f'  <script defer src="/ab/{js_filename}"></script>'
    )


# ── Racer Rating ─────────────────────────────────────────────
RACER_RATING_THRESHOLD = 3


# ── Tier Names ──────────────────────────────────────────────
# Canonical road tier names — must match the homepage (generate_homepage.py
# tier_labels). Were gravel leftovers ("The Icons"/"Grassroots").
TIER_NAMES = {1: "Elite", 2: "Contender", 3: "Rising", 4: "Local"}

TIER_DESCS = {
    1: "The definitive road events — the deepest fields and the courses that anchor the calendar.",
    2: "Established races with strong reputations and competitive fields. The next tier of must-ride events.",
    3: "Regional favorites and emerging events. Strong local scenes, genuine road racing character.",
    4: "Up-and-coming events and local rides. Small fields, raw vibes, grassroots road cycling.",
}
