<?php
/**
 * Plugin Name: Roadie Labs Cookie Consent
 * Description: Geo-gated cookie consent banner with Google Consent Mode v2.
 * Version: 1.2
 *
 * Deployed via: python3 scripts/push_wordpress.py --sync-consent
 *
 * Injects a consent banner + Consent Mode defaults before GA4 fires.
 * Same model as gravelgodcycling.com (Matti's ruling, 2026-11-14):
 * EEA/UK/CH browser timezones (and unknown timezones) default analytics to
 * denied and see the banner; other timezones default to granted. An
 * rl_consent=accepted/declined cookie overrides the regional default, and
 * the footer "Privacy choices" link reopens the banner everywhere.
 *
 * Works alongside rl-ga4.php — GA4 fires on every page but with consent mode
 * controlling what data is actually collected. No script blocking needed.
 *
 * IMPORTANT: Hex values must match tokens.css (source of truth).
 * Mu-plugins can't use var() tokens — hardcode hex with !important.
 * Parity with cookie_consent.py enforced by test_cookie_consent_mu_plugin.py.
 */

if ( ! defined( 'ABSPATH' ) ) {
    exit;
}

/**
 * Set Google Consent Mode defaults BEFORE gtag loads.
 * Must fire at priority 0 (before rl_ga4_tracking at priority 1).
 */
add_action( 'wp_head', 'rl_consent_mode_defaults', 0 );

function rl_consent_mode_defaults() {
    if ( is_admin() ) return;
    if ( current_user_can( 'edit_posts' ) ) return;
    ?>
<script>
window.dataLayer=window.dataLayer||[];function gtag(){dataLayer.push(arguments)}
var rlConsentStrictTimezones=new Set(["Africa/Ceuta","Asia/Famagusta","Asia/Nicosia","Atlantic/Azores","Atlantic/Canary","America/Cayenne","America/Guadeloupe","America/Marigot","America/Martinique","Arctic/Longyearbyen","Atlantic/Faeroe","Indian/Mayotte","Indian/Reunion","Atlantic/Reykjavik","Atlantic/Faroe","Atlantic/Madeira","Europe/Amsterdam","Europe/Athens","Europe/Belfast","Europe/Berlin","Europe/Bratislava","Europe/Brussels","Europe/Bucharest","Europe/Budapest","Europe/Busingen","Europe/Copenhagen","Europe/Dublin","Europe/Helsinki","Europe/Lisbon","Europe/Ljubljana","Europe/London","Europe/Luxembourg","Europe/Madrid","Europe/Malta","Europe/Mariehamn","Europe/Nicosia","Europe/Oslo","Europe/Paris","Europe/Prague","Europe/Riga","Europe/Rome","Europe/Sofia","Europe/Stockholm","Europe/Tallinn","Europe/Vaduz","Europe/Vienna","Europe/Vilnius","Europe/Warsaw","Europe/Zagreb","Europe/Zurich"]);
var rlConsentTimezone='';var rlConsentTimezoneKnown=false;
try{rlConsentTimezone=Intl.DateTimeFormat().resolvedOptions().timeZone||'';if(rlConsentTimezone){new Intl.DateTimeFormat('en-US',{timeZone:rlConsentTimezone});rlConsentTimezoneKnown=true}}catch(rlConsentTimezoneError){}
var rlConsentRequiresOptIn=!rlConsentTimezoneKnown||rlConsentStrictTimezones.has(rlConsentTimezone);
window.rlConsentRequiresOptIn=rlConsentRequiresOptIn;
var rlConsentAccepted=/(^|; )rl_consent=accepted/.test(document.cookie);
var rlConsentDeclined=/(^|; )rl_consent=declined/.test(document.cookie);
var rlConsentAnalytics=rlConsentAccepted?'granted':rlConsentDeclined?'denied':rlConsentRequiresOptIn?'denied':'granted';
gtag('consent','default',{'analytics_storage':rlConsentAnalytics,'ad_storage':'denied','ad_user_data':'denied','ad_personalization':'denied','wait_for_update':500});
</script>
    <?php
}

/**
 * Inject the privacy-choices footer control and consent banner.
 */
add_action( 'wp_footer', 'rl_cookie_consent_banner', 99 );

function rl_cookie_consent_banner() {
    if ( is_admin() ) return;
    if ( current_user_can( 'edit_posts' ) ) return;
    ?>
<style>
.rl-privacy-choices-footer{padding:8px 16px;background:#555555;font-family:'JetBrains Mono',monospace;display:flex;justify-content:center;gap:12px;flex-wrap:wrap}
.rl-privacy-choices{color:#d0d0c8;font-size:10px;letter-spacing:1px;text-transform:uppercase;text-decoration:underline;text-underline-offset:3px}
.rl-privacy-choices:hover{color:#ffffff}
.rl-privacy-choices:focus-visible{outline:2px solid #ffffff;outline-offset:2px}
.rl-consent-banner{position:fixed;bottom:0;left:0;right:0;z-index:9999;background:#555555;border-top:3px solid #202322;padding:16px 24px;display:none;align-items:center;justify-content:center;gap:16px;flex-wrap:wrap;font-family:'JetBrains Mono',monospace}
.rl-consent-banner.rl-consent-show{display:flex}
.rl-consent-text{color:#d0d0c8;font-size:13px;line-height:1.5;max-width:640px}
.rl-consent-text a{color:#ffffff;text-decoration:underline;text-underline-offset:3px}
.rl-consent-text a:hover{color:#d0d0c8}
.rl-consent-btn{padding:8px 20px;font-family:'JetBrains Mono',monospace;font-size:12px;font-weight:700;letter-spacing:1px;text-transform:uppercase;cursor:pointer;border:2px solid;transition:background-color .3s,color .3s,border-color .3s}
.rl-consent-btn:focus-visible{outline:2px solid #ffffff;outline-offset:2px}
.rl-consent-accept{background:#202322;color:#ffffff;border-color:#202322}
.rl-consent-accept:hover{background:#555555;border-color:#202322;color:#ffffff}
.rl-consent-decline{background:transparent;color:#d0d0c8;border-color:#d0d0c8}
.rl-consent-decline:hover{border-color:#ffffff;color:#ffffff}
@media(max-width:600px){.rl-consent-banner{flex-direction:column;text-align:center;padding:12px 16px}.rl-consent-text{font-size:12px}}
@media(prefers-reduced-motion:reduce){.rl-consent-btn{transition:none}}
</style>
<footer class="rl-privacy-choices-footer" aria-label="Legal"><a class="rl-privacy-choices" id="rl-privacy-choices" href="/cookies/#privacy-choices">Privacy choices</a><a class="rl-privacy-choices" href="/privacy/">Privacy</a><a class="rl-privacy-choices" href="/terms/">Terms</a></footer>
<div class="rl-consent-banner" id="rl-consent-banner" role="dialog" aria-label="Cookie consent" aria-describedby="rl-consent-desc">
  <p class="rl-consent-text" id="rl-consent-desc">We use cookies for analytics to improve this site. No ads, no tracking across sites. <a href="/cookies/">Learn more</a>.</p>
  <button class="rl-consent-btn rl-consent-accept" id="rl-consent-accept">Accept</button>
  <button class="rl-consent-btn rl-consent-decline" id="rl-consent-decline">Decline</button>
</div>
<script>
(function(){
  var b=document.getElementById('rl-consent-banner');
  var p=document.getElementById('rl-privacy-choices');
  if(!b)return;
  var tid;var autoPending=false;
  function cancelAutoShow(){
    if(!autoPending)return;autoPending=false;
    clearTimeout(tid);
    window.removeEventListener('scroll',showBanner);
  }
  function showBanner(){
    cancelAutoShow();
    b.classList.add('rl-consent-show');
  }
  if(p){p.addEventListener('click',function(e){e.preventDefault();showBanner()})}
  if(!/(^|; )rl_consent=/.test(document.cookie)&&window.rlConsentRequiresOptIn!==false){
    /* Delay showing: 3s timeout OR first scroll, whichever comes first */
    autoPending=true;
    window.addEventListener('scroll',showBanner,{passive:true,once:true});
    tid=setTimeout(showBanner,3000);
  }
  document.getElementById('rl-consent-accept').addEventListener('click',function(){
    document.cookie='rl_consent=accepted;path=/;max-age=31536000;SameSite=Lax;Secure';
    if(typeof gtag==='function'){gtag('consent','update',{'analytics_storage':'granted'})}
    b.classList.remove('rl-consent-show');
  });
  document.getElementById('rl-consent-decline').addEventListener('click',function(){
    document.cookie='rl_consent=declined;path=/;max-age=31536000;SameSite=Lax;Secure';
    if(typeof gtag==='function'){gtag('consent','update',{'analytics_storage':'denied'})}
    b.classList.remove('rl-consent-show');
  });
})();
</script>
    <?php
}
