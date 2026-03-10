"""
Brand token helpers for Road Labs CSS generation.

Provides CSS custom properties (:root block), @font-face declarations,
and color mapping from the Road Labs design system.
"""

from pathlib import Path

# ── Paths ─────────────────────────────────────────────────────
BRAND_DIR = Path(__file__).resolve().parent.parent.parent / "road-labs-brand"
BRAND_FONTS_DIR = BRAND_DIR / "assets" / "fonts"

# 10 woff2 font files to self-host (same typefaces as Gravel God — shared DNA)
FONT_FILES = [
    "SometypeMono-normal-latin.woff2",
    "SometypeMono-normal-latin-ext.woff2",
    "SometypeMono-italic-latin.woff2",
    "SometypeMono-italic-latin-ext.woff2",
    "SourceSerif4-normal-latin.woff2",
    "SourceSerif4-normal-latin-ext.woff2",
    "SourceSerif4-italic-latin.woff2",
    "SourceSerif4-italic-latin-ext.woff2",
    "Unbounded-900-latin.woff2",
    "Unbounded-900-latin-ext.woff2",
]


# ── Analytics ─────────────────────────────────────────────────
GA_MEASUREMENT_ID = "G-PLACEHOLDER"  # TODO: Create Road Labs GA4 property


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
SITE_BASE_URL = "https://roadlabs.cc"
BRAND_NAME = "Road Labs"


def get_tokens_css() -> str:
    """Return the :root CSS custom properties block.

    Road Labs palette: clinical, precise, technical.
    Deep navy + steel blue + signal red. Cool white background.
    Same neo-brutalist rules: no border-radius, no box-shadow, solid borders.
    """
    return """:root {
  /* color — Road Labs palette */
  --rl-color-dark-navy: #0d1117;
  --rl-color-primary-navy: #1a1a2e;
  --rl-color-secondary-blue: #3d5a80;
  --rl-color-steel: #5c7a99;
  --rl-color-light-steel: #a3bfdb;
  --rl-color-silver: #d1dce6;
  --rl-color-cool-white: #f8f9fa;
  --rl-color-signal-red: #e63946;
  --rl-color-coral: #ff6b6b;
  --rl-color-orange: #f77f00;
  --rl-color-light-orange: #fcbf49;
  --rl-color-near-black: #0d1117;
  --rl-color-white: #ffffff;
  --rl-color-error: #c0392b;
  --rl-color-tier-1: #1a1a2e;
  --rl-color-tier-2: #3d5a80;
  --rl-color-tier-3: #6c757d;
  --rl-color-tier-4: #adb5bd;

  /* font */
  --rl-font-display: 'Unbounded', sans-serif;
  --rl-font-data: 'Sometype Mono', monospace;
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
  --rl-border-color-default: #0d1117;
  --rl-border-color-brand: #1a1a2e;
  --rl-border-color-secondary: #3d5a80;
  --rl-border-color-accent: #e63946;
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
    return f"""/* Sometype Mono — Normal — Latin Extended */
@font-face {{
  font-family: 'Sometype Mono';
  font-style: normal;
  font-weight: 400 700;
  font-display: swap;
  src: url('{p}/SometypeMono-normal-latin-ext.woff2') format('woff2');
  unicode-range: U+0100-02BA, U+02BD-02C5, U+02C7-02CC, U+02CE-02D7, U+02DD-02FF, U+0304, U+0308, U+0329, U+1D00-1DBF, U+1E00-1E9F, U+1EF2-1EFF, U+2020, U+20A0-20AB, U+20AD-20C0, U+2113, U+2C60-2C7F, U+A720-A7FF;
}}
/* Sometype Mono — Normal — Latin */
@font-face {{
  font-family: 'Sometype Mono';
  font-style: normal;
  font-weight: 400 700;
  font-display: swap;
  src: url('{p}/SometypeMono-normal-latin.woff2') format('woff2');
  unicode-range: U+0000-00FF, U+0131, U+0152-0153, U+02BB-02BC, U+02C6, U+02DA, U+02DC, U+0304, U+0308, U+0329, U+2000-206F, U+20AC, U+2122, U+2191, U+2193, U+2212, U+2215, U+FEFF, U+FFFD;
}}
/* Sometype Mono — Italic — Latin Extended */
@font-face {{
  font-family: 'Sometype Mono';
  font-style: italic;
  font-weight: 400 700;
  font-display: swap;
  src: url('{p}/SometypeMono-italic-latin-ext.woff2') format('woff2');
  unicode-range: U+0100-02BA, U+02BD-02C5, U+02C7-02CC, U+02CE-02D7, U+02DD-02FF, U+0304, U+0308, U+0329, U+1D00-1DBF, U+1E00-1E9F, U+1EF2-1EFF, U+2020, U+20A0-20AB, U+20AD-20C0, U+2113, U+2C60-2C7F, U+A720-A7FF;
}}
/* Sometype Mono — Italic — Latin */
@font-face {{
  font-family: 'Sometype Mono';
  font-style: italic;
  font-weight: 400 700;
  font-display: swap;
  src: url('{p}/SometypeMono-italic-latin.woff2') format('woff2');
  unicode-range: U+0000-00FF, U+0131, U+0152-0153, U+02BB-02BC, U+02C6, U+02DA, U+02DC, U+0304, U+0308, U+0329, U+2000-206F, U+20AC, U+2122, U+2191, U+2193, U+2212, U+2215, U+FEFF, U+FFFD;
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
/* Unbounded — 900 (Black) — Latin Extended */
@font-face {{
  font-family: 'Unbounded';
  font-style: normal;
  font-weight: 900;
  font-display: swap;
  src: url('{p}/Unbounded-900-latin-ext.woff2') format('woff2');
  unicode-range: U+0100-02BA, U+02BD-02C5, U+02C7-02CC, U+02CE-02D7, U+02DD-02FF, U+0304, U+0308, U+0329, U+1D00-1DBF, U+1E00-1E9F, U+1EF2-1EFF, U+2020, U+20A0-20AB, U+20AD-20C0, U+2113, U+2C60-2C7F, U+A720-A7FF;
}}
/* Unbounded — 900 (Black) — Latin */
@font-face {{
  font-family: 'Unbounded';
  font-style: normal;
  font-weight: 900;
  font-display: swap;
  src: url('{p}/Unbounded-900-latin.woff2') format('woff2');
  unicode-range: U+0000-00FF, U+0131, U+0152-0153, U+02BB-02BC, U+02C6, U+02DA, U+02DC, U+0304, U+0308, U+0329, U+2000-206F, U+20AC, U+2122, U+2191, U+2193, U+2212, U+2215, U+FEFF, U+FFFD;
}}"""


def get_preload_hints(font_path_prefix: str = "/race/assets/fonts") -> str:
    """Return <link rel=preload> tags for the Latin (most common) font subsets."""
    p = font_path_prefix.rstrip("/")
    return f"""<link rel="preload" href="{p}/SometypeMono-normal-latin.woff2" as="font" type="font/woff2" crossorigin>
  <link rel="preload" href="{p}/SourceSerif4-normal-latin.woff2" as="font" type="font/woff2" crossorigin>
  <link rel="preload" href="{p}/Unbounded-900-latin.woff2" as="font" type="font/woff2" crossorigin>"""


# ── Color mapping for SVG attributes (can't use CSS vars) ────

COLORS = {
    "dark_navy": "#0d1117",
    "primary_navy": "#1a1a2e",
    "secondary_blue": "#3d5a80",
    "steel": "#5c7a99",
    "light_steel": "#a3bfdb",
    "silver": "#d1dce6",
    "cool_white": "#f8f9fa",
    "signal_red": "#e63946",
    "coral": "#ff6b6b",
    "orange": "#f77f00",
    "light_orange": "#fcbf49",
    "near_black": "#0d1117",
    "white": "#ffffff",
    "tier_1": "#1a1a2e",
    "tier_2": "#3d5a80",
    "tier_3": "#6c757d",
    "tier_4": "#adb5bd",
    # Compatibility aliases (mapped from Gravel God names used in generators)
    "primary_brown": "#1a1a2e",
    "secondary_brown": "#3d5a80",
    "warm_brown": "#5c7a99",
    "tan": "#d1dce6",
    "sand": "#e9ecef",
    "warm_paper": "#f8f9fa",
    "gold": "#f77f00",
    "light_gold": "#fcbf49",
    "teal": "#e63946",
    "light_teal": "#ff6b6b",
    "dark_brown": "#0d1117",
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
TIER_NAMES = {1: "The Icons", 2: "Elite", 3: "Solid", 4: "Grassroots"}

TIER_DESCS = {
    1: "The definitive road events. World-class fields, iconic courses, bucket-list status.",
    2: "Established races with strong reputations and competitive fields. The next tier of must-ride events.",
    3: "Regional favorites and emerging events. Strong local scenes, genuine road racing character.",
    4: "Up-and-coming events and local rides. Small fields, raw vibes, grassroots road cycling.",
}
