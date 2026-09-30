"""Two <style> blocks that exist only on the live roadielabs.com pages.

Provenance: both were applied in place on the server (SiteGround static
HTML), not produced by any generator; their source branch is not in this repo
(the first one's own comment names `codex/desktop-width-road`). They are
copied here VERBATIM from the live HTML fetched 2026-09-30 so that
regenerating a page from main reproduces what is live:

  - ROAD_DESKTOP_WIDTH_STYLE (`road-desktop-width-20260909`) — appended to
    /coaching/, /coaching/apply/, /coaching/welcome/, /training-plans/success/,
    /consulting/confirmed/, /privacy/, /terms/ (not /cookies/).
  - ROADIE_APPROVED_LOGO_STYLE (`roadie-approved-logo`) — appended to all of
    the above and /cookies/.

Both overlap rules main now ships natively (the 1200px desktop measure from
ce48ffa and the header-mark sizing from #73/#76), so they are expected to be
redundant; drop them only after a visual check, in their own change.

sha256 (verbatim content):
  ROAD_DESKTOP_WIDTH_STYLE   ce8feba610b58fe1141df1c96a9890f93075a03526bbfabbdcdadc2eca919da0
  ROADIE_APPROVED_LOGO_STYLE 6d67383d320f2625abb62b3ac4f4e5ee91e90342f8eb8a2a0c26630487da532c
"""
from __future__ import annotations

ROAD_DESKTOP_WIDTH_STYLE = """<style id="road-desktop-width-20260909">
/* Roadie Labs desktop shell normalization — source parity with codex/desktop-width-road.
   Append only to eligible static HTML after preserving its existing content and assets. */

/* Shared chrome */
.rl-site-header-inner,
.rl-mega-footer-grid,
.rl-mega-footer-legal,
.rl-mega-footer-disclaimer {
  max-width: 1200px !important;
}

/* Homepage bands */
.rl-hp-hero-inner,
.rl-hp-ladder-inner,
.rl-hp-stats-inner,
.rl-hp-content-grid,
.rl-hp-latest-takes,
.rl-hp-how-it-works,
.rl-hp-coming-up,
.rl-hp-training-cta-full,
.rl-hp-guide,
.rl-hp-testimonials,
.rl-hp-email {
  max-width: 1200px !important;
}

/* Race-profile shell */
.rl-neo-brutalist-page,
.rl-sticky-cta-inner,
.rl-status-notice {
  max-width: 1200px !important;
}
.rl-neo-brutalist-page .rl-prose {
  max-width: 68ch !important;
}

/* Training-plan shell; component widths remain defined by their own selectors. */
.rl-breadcrumb,
.rl-tp-section,
.rl-tp-hero {
  max-width: 1200px !important;
}
/* The generic section rule above must not box the source full-bleed variants. */
.rl-tp-section.rl-tp-section-alt {
  max-width: none !important;
}
/* Existing alternate sections have this finite direct-child contract. */
.rl-tp-section-alt > .rl-tp-section-label,
.rl-tp-section-alt > h2,
.rl-tp-section-alt > .rl-tp-process,
.rl-tp-section-alt > .rl-tp-steps,
.rl-tp-section-alt > .rl-tp-audience-grid,
.rl-tp-section-alt > .rl-tp-faq-list {
  max-width: 1200px !important;
}
.rl-tp-deliverable-content p,
.rl-tp-step p {
  max-width: 68ch !important;
}

/* Other generated page shells using the shared header and footer. */
.rl-hub-page,
.rl-cal-page,
.rl-pr-page,
.rl-state-page,
.rl-vs-page,
.rl-pk-index-main,
.rl-ins-breadcrumb,
.rl-ins-hero,
.rl-ins-section,
.rl-ins-closing {
  max-width: 1200px !important;
}
.rl-ins-section--alt {
  /* Preserve the source generator's full-bleed alternate band. */
  max-width: none !important;
  padding-left: max(var(--rl-spacing-xl), calc((100% - 1200px) / 2 + var(--rl-spacing-xl))) !important;
  padding-right: max(var(--rl-spacing-xl), calc((100% - 1200px) / 2 + var(--rl-spacing-xl))) !important;
}

</style>"""

ROADIE_APPROVED_LOGO_STYLE = '<style id="roadie-approved-logo">.rl-site-header-mark{display:block;height:48px;width:auto;flex:none}@media(max-width:600px){.rl-site-header-mark{height:42px}}</style>'


def get_live_head_patches(desktop_width: bool = True) -> str:
    """Exact bytes the server-side patch placed immediately before </head>."""
    if desktop_width:
        return "\n" + ROAD_DESKTOP_WIDTH_STYLE + "\n" + ROADIE_APPROVED_LOGO_STYLE + "\n"
    return ROADIE_APPROVED_LOGO_STYLE + "\n"


def apply_live_head_patches(html: str, desktop_width: bool = True) -> str:
    """Insert the live-only style blocks right before the first </head>."""
    marker = "</head>"
    if marker not in html:
        raise ValueError("page has no </head>")
    return html.replace(marker, get_live_head_patches(desktop_width) + marker, 1)
