<?php
/**
 * Plugin Name: Road Labs Noindex
 * Description: Add noindex to junk pages that waste Google crawl budget.
 * Version: 1.0
 *
 * Deployed via: python3 scripts/push_wordpress.py --sync-noindex
 * Targets: date archives, pagination, categories, WooCommerce, LearnDash, feeds
 *
 * Google merges multiple robots meta tags using the most restrictive directive,
 * so this coexists safely with AIOSEO's existing robots meta tag.
 */

function rl_noindex_junk_pages() {
    $dominated = false;

    // WordPress template conditionals
    if (is_date()) $dominated = true;
    if (is_paged()) $dominated = true;
    if (is_category()) $dominated = true;
    if (is_tag()) $dominated = true;
    if (is_feed()) $dominated = true;
    if (is_search()) $dominated = true;

    // WooCommerce pages (check function exists for non-WC installs)
    if (function_exists('is_cart') && is_cart()) $dominated = true;
    if (function_exists('is_account_page') && is_account_page()) $dominated = true;

    // URL-pattern matching for WooCommerce, LearnDash, xAPI, dashboard, junk pages
    $uri = $_SERVER['REQUEST_URI'] ?? '';
    $noindex_patterns = [
        '/cart',
        '/my-account',
        '/lesson',
        '/courses/',
        '/gb_xapi_content/',
        '/dashboard',
        '/student-registration',
        '/instructor-registration',
        '/questionnaire',
        '/coaching/apply',
        'wc-ajax=',
    ];

    // Noindex search page with query params (e.g. ?region=Midwest) to avoid
    // duplicate content — the canonical /road-races/ is the only one to index
    if (strpos($uri, '/road-races/') !== false && !empty($_SERVER['QUERY_STRING'])) {
        $dominated = true;
    }

    // Noindex blog preview pages (/blog/{slug}/) — thin content that duplicates
    // race profiles. Keep /blog/ index, roundups, and recaps indexed.
    // Structural regex mirrors Python classify_blog_slug(): roundups start with
    // "roundup-", recaps end with "-recap". All other /blog/{slug}/ are noindexed.
    if (preg_match('#^/blog/[a-z0-9-]+/?$#', $uri)
        && !preg_match('#^/blog/roundup-#', $uri)
        && !preg_match('#-recap/?$#', $uri)) {
        $dominated = true;
    }
    foreach ($noindex_patterns as $pattern) {
        if (strpos($uri, $pattern) !== false) {
            $dominated = true;
            break;
        }
    }

    if ($dominated) {
        echo '<meta name="robots" content="noindex, follow" />' . "\n";
    }
}
add_action('wp_head', 'rl_noindex_junk_pages', 1);

/**
 * Inject JSON-LD schema on /road-races/ page.
 * BreadcrumbList + CollectionPage for rich snippets in Google SERPs.
 */
function rl_search_page_schema() {
    $uri = $_SERVER['REQUEST_URI'] ?? '';
    if (strpos($uri, '/road-races') === false) return;

    $breadcrumb = [
        '@context' => 'https://schema.org',
        '@type' => 'BreadcrumbList',
        'itemListElement' => [
            ['@type' => 'ListItem', 'position' => 1, 'name' => 'Home', 'item' => 'https://roadlabs.cc/'],
            ['@type' => 'ListItem', 'position' => 2, 'name' => 'Road Races', 'item' => 'https://roadlabs.cc/road-races/'],
        ],
    ];

    $collection = [
        '@context' => 'https://schema.org',
        '@type' => 'CollectionPage',
        'name' => 'Find Your Road Race',
        'description' => 'Search and filter 427 road races worldwide by tier, distance, region, terrain, and date. Find your next road cycling event with the Road Labs race database.',
        'url' => 'https://roadlabs.cc/road-races/',
        'numberOfItems' => 427,
        'publisher' => [
            '@type' => 'Organization',
            'name' => 'Road Labs',
            'url' => 'https://roadlabs.cc/',
        ],
    ];

    echo '<script type="application/ld+json">' . json_encode($breadcrumb, JSON_UNESCAPED_SLASHES) . '</script>' . "\n";
    echo '<script type="application/ld+json">' . json_encode($collection, JSON_UNESCAPED_SLASHES) . '</script>' . "\n";
}
add_action('wp_head', 'rl_search_page_schema', 5);
