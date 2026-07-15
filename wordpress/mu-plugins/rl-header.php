<?php
/**
 * Roadie Labs — Shared Dropdown Header for WordPress Pages
 *
 * Injects the 5-item dropdown nav (RACES, PRODUCTS, SERVICES, ARTICLES, ABOUT)
 * on WordPress-managed pages that don't use our static generators.
 *
 * Targets: /road-races/, /training-plans/, and any other WP page
 * that has the Astra theme header.
 *
 * Strategy:
 *   1. wp_head: output CSS to hide Astra's header and style our dropdown nav
 *   2. wp_body_open: inject our header HTML right after <body>
 *
 * Deployed via SCP to wp-content/mu-plugins/rl-header.php
 */

if ( ! defined( 'ABSPATH' ) ) {
    exit;
}

add_action( 'wp_head', 'rl_shared_header_css', 5 );
add_action( 'wp_head', 'rl_rss_feed_link', 6 );
add_action( 'wp_body_open', 'rl_shared_header_html', 1 );
add_filter( 'body_class', 'rl_add_neo_brutalist_class' );

/**
 * Add RSS feed discovery link to <head> on all pages.
 */
function rl_rss_feed_link() {
    echo '<link rel="alternate" type="application/rss+xml" title="Roadie Labs Race Database" href="https://roadielabs.com/feed/races.xml">' . "\n";
}

/**
 * Add rl-neo-brutalist-page class to body so existing Code Snippet overrides
 * (which use body:not(.rl-neo-brutalist-page)) don't apply teal link colors.
 */
function rl_add_neo_brutalist_class( $classes ) {
    if ( ! is_admin() && ! is_front_page() ) {
        $classes[] = 'rl-neo-brutalist-page';
    }
    return $classes;
}

/**
 * Check if current page should get our custom header.
 * Skip admin, static generated pages (they have their own header), and the homepage.
 */
function rl_should_inject_header() {
    if ( is_admin() ) {
        return false;
    }
    // Skip pages that already use our static header (served via Code Snippets overrides)
    if ( is_front_page() ) {
        return false;
    }
    // Only inject on WordPress pages/posts that use the Astra theme header
    return true;
}

function rl_shared_header_css() {
    if ( ! rl_should_inject_header() ) {
        return;
    }
    ?>
<style id="rl-shared-header-css">
/* Hide Astra theme header — our header replaces it */
.ast-above-header-wrap,
.ast-main-header-wrap,
.ast-below-header-wrap,
#ast-desktop-header,
#masthead,
.site-header,
header.site-header,
.ast-mobile-header-wrap { display: none !important; }

/* ── Shared Site Header (uses !important to override Astra theme) ── */
@import url('https://fonts.googleapis.com/css2?family=Sometype+Mono:wght@400;700&family=Source+Serif+4:wght@400;700&display=swap');

.rl-site-header { padding: 16px 24px !important; border-bottom: 2px solid #333333 !important; background: #f5f5f0 !important; }
.rl-site-header-inner { display: flex !important; align-items: center !important; justify-content: space-between !important; max-width: 960px !important; margin: 0 auto !important; }
.rl-site-header-logo { display: block !important; color: #1a1a1a !important; }
.rl-site-header-logo svg { display: block !important; height: 58px !important; width: auto !important; }
.rl-site-header-nav { display: flex !important; gap: 24px !important; align-items: center !important; }
.rl-site-header-nav > a,
.rl-site-header-nav > a:link,
.rl-site-header-nav > a:visited,
.rl-site-header-item > a,
.rl-site-header-item > a:link,
.rl-site-header-item > a:visited { color: #1a1a1a !important; text-decoration: none !important; font-family: 'Sometype Mono', monospace !important; font-size: 11px !important; font-weight: 700 !important; letter-spacing: 2px !important; text-transform: uppercase !important; transition: color 0.2s !important; }
.rl-site-header-nav > a:hover,
.rl-site-header-item > a:hover { color: #333333 !important; }
.rl-site-header-nav > a[aria-current="page"],
.rl-site-header-item > a[aria-current="page"] { color: #333333 !important; }
.rl-site-header-item { position: relative !important; }
.rl-site-header-dropdown { display: none; position: absolute !important; top: 100% !important; left: 0 !important; min-width: 200px !important; padding: 8px 0 !important; background: #f5f5f0 !important; border: 2px solid #1a1a1a !important; z-index: 1000 !important; }
.rl-site-header-item:hover .rl-site-header-dropdown,
.rl-site-header-item:focus-within .rl-site-header-dropdown { display: block !important; }
.rl-site-header-dropdown a,
.rl-site-header-dropdown a:link,
.rl-site-header-dropdown a:visited { display: block !important; padding: 8px 16px !important; font-family: 'Sometype Mono', monospace !important; font-size: 11px !important; font-weight: 400 !important; letter-spacing: 1px !important; color: #1a1a1a !important; text-decoration: none !important; transition: color 0.2s !important; }
.rl-site-header-dropdown a:hover { color: #333333 !important; }

/* ── Training Plans page fix: entrance animation doesn't fire in WP ── */
.tp-hero h1,
.tp-hero-sub,
.tp-hero-cta,
.tp-hero-bar { opacity: 1 !important; transform: none !important; }

@media (max-width: 600px) {
  .rl-site-header { padding: 12px 16px !important; }
  .rl-site-header-inner { flex-wrap: wrap !important; justify-content: center !important; gap: 10px !important; }
  .rl-site-header-logo svg { height: 46px !important; }
  .rl-site-header-nav { gap: 12px !important; flex-wrap: wrap !important; justify-content: center !important; }
  .rl-site-header-nav > a,
  .rl-site-header-item > a { font-size: 10px !important; letter-spacing: 1.5px !important; }
  .rl-site-header-dropdown { display: none !important; }
}
</style>
    <?php
}

function rl_shared_header_html() {
    if ( ! rl_should_inject_header() ) {
        return;
    }

    // Determine active nav item from current URL
    $uri = $_SERVER['REQUEST_URI'] ?? '';
    $active = '';
    if ( strpos( $uri, '/road-races' ) !== false || strpos( $uri, '/race/' ) !== false ) {
        $active = 'races';
    } elseif ( strpos( $uri, '/products/' ) !== false ) {
        $active = 'products';
    } elseif ( strpos( $uri, '/coaching' ) !== false || strpos( $uri, '/consulting' ) !== false ) {
        $active = 'services';
    } elseif ( strpos( $uri, '/articles' ) !== false || strpos( $uri, '/blog' ) !== false || strpos( $uri, '/insights' ) !== false ) {
        $active = 'articles';
    } elseif ( strpos( $uri, '/about' ) !== false ) {
        $active = 'about';
    }

    $base = 'https://roadielabs.com';
    $substack = 'https://roadlabs.substack.com';

    $aria = function( $key ) use ( $active ) {
        return $active === $key ? ' aria-current="page"' : '';
    };
    ?>
<header class="rl-site-header">
  <div class="rl-site-header-inner">
    <a href="<?php echo $base; ?>/" class="rl-site-header-logo" aria-label="Roadie Labs">
      <svg class="rl-site-header-mark" viewBox="0 0 800 1200" aria-hidden="true" focusable="false">
        <defs><mask id="rl-wp-tread-sipes"><rect width="800" height="1200" fill="white"/><path d="M286 368H382V398H286ZM418 608H514V638H418Z" fill="black"/></mask></defs>
        <g fill="currentColor">
          <path d="M224 96 322 72 322 174 214 198ZM478 72 576 96 586 198 478 174ZM152 236 254 210 266 304 160 332ZM546 210 648 236 640 332 534 304ZM130 414 230 390 244 482 138 510ZM570 390 670 414 662 510 556 482ZM136 690 238 714 224 806 128 782ZM562 714 664 690 672 782 576 806ZM166 876 268 900 252 996 154 970ZM532 900 634 876 646 970 548 996ZM230 1040 330 1062 330 1130 244 1112ZM470 1062 570 1040 556 1112 470 1130Z"/>
          <g mask="url(#rl-wp-tread-sipes)">
            <path d="M126 178 220 154V1046L126 1018ZM178 154H350L382 184V268H178ZM302 228 382 248V492L302 516ZM178 454H350L382 486V562H178ZM238 522H328L410 998 316 1028Z"/>
            <path d="M418 144H514V944H678V1032L418 1082Z"/>
          </g>
        </g>
      </svg>
    </a>
    <nav class="rl-site-header-nav">
      <div class="rl-site-header-item">
        <a href="<?php echo $base; ?>/road-races/"<?php echo $aria('races'); ?>>RACES</a>
        <div class="rl-site-header-dropdown">
          <a href="<?php echo $base; ?>/road-races/">All Road Races</a>
          <a href="<?php echo $base; ?>/race/methodology/">How We Rate</a>
        </div>
      </div>
      <div class="rl-site-header-item">
        <a href="<?php echo $base; ?>/training-plans/"<?php echo $aria('products'); ?>>PRODUCTS</a>
        <div class="rl-site-header-dropdown">
          <a href="<?php echo $base; ?>/training-plans/">Custom Training Plans</a>
          <a href="<?php echo $base; ?>/guide/">Road Cycling Handbook</a>
        </div>
      </div>
      <div class="rl-site-header-item">
        <a href="<?php echo $base; ?>/coaching/"<?php echo $aria('services'); ?>>SERVICES</a>
        <div class="rl-site-header-dropdown">
          <a href="<?php echo $base; ?>/coaching/">Coaching</a>
          <a href="<?php echo $base; ?>/consulting/">Consulting</a>
        </div>
      </div>
      <div class="rl-site-header-item">
        <a href="<?php echo $base; ?>/articles/"<?php echo $aria('articles'); ?>>ARTICLES</a>
        <div class="rl-site-header-dropdown">
          <a href="<?php echo $substack; ?>" target="_blank" rel="noopener">Slow Mid 38s</a>
          <a href="<?php echo $base; ?>/articles/">Hot Takes</a>
          <a href="<?php echo $base; ?>/insights/">Insights</a>
          <a href="<?php echo $base; ?>/fueling-methodology/">White Papers</a>
        </div>
      </div>
      <a href="<?php echo $base; ?>/about/"<?php echo $aria('about'); ?>>ABOUT</a>
    </nav>
  </div>
</header>
    <?php
}
