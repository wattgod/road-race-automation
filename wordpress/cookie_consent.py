"""Shared geo-gated cookie consent for all generated pages.

Provides the synchronous Consent Mode head script and the lightweight,
brand-consistent footer controls used by every generated page.

Ported from Gravel God's wordpress/cookie_consent.py (Matti's ruling,
2026-11-14: Roadie Labs uses the same consent model as gravelgodcycling.com).

Used by every generator that includes GA4 tracking.

Consent behavior:
- EEA/UK/CH timezones default analytics to denied and show the banner
- Other known timezones default analytics to granted without showing it
- Missing timezone data fails closed to the stricter EEA posture
- Existing accepted/declined cookies override the geographic default
- The footer Privacy choices link opens the banner in every region
- Accept → sets rl_consent=accepted, updates consent mode to 'granted'
- Decline → sets rl_consent=declined, updates consent mode to 'denied'
- Links to /cookies/ for full cookie policy

Hex values MUST match tokens.css (source of truth):
  --rl-color-coral: #555555
  --rl-color-silver: #d0d0c8
  --rl-color-signal-red: #202322
  --rl-color-white: #ffffff

Note: This module uses hardcoded hex because the banner renders inline
before tokens.css loads. The mu-plugin (rl-cookie-consent.php) also
hardcodes hex because mu-plugins have no access to :root tokens.
Parity between Python and PHP is enforced by test_cookie_consent_mu_plugin.py.
"""
from __future__ import annotations

import json
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


# Explicit IANA timezones for the EEA member states, United Kingdom, and
# Switzerland. Cyprus has both Europe/* and Asia/* IANA identifiers. The three
# Atlantic zones are the EEA island zones called out in the consent decision.
# Do not broaden this to all Europe/*: Istanbul, Moscow, Minsk, Belgrade, Kyiv,
# and other non-EEA European zones must remain outside the opt-in geo-gate.
EEA_UK_CH_TIMEZONES = (
    "Africa/Ceuta",
    "Asia/Famagusta",
    "Asia/Nicosia",
    "Atlantic/Azores",
    "Atlantic/Canary",
    "America/Cayenne",
    "America/Guadeloupe",
    "America/Marigot",
    "America/Martinique",
    "Arctic/Longyearbyen",
    "Atlantic/Faeroe",
    "Indian/Mayotte",
    "Indian/Reunion",
    "Atlantic/Reykjavik",  # Iceland — EEA/EFTA, GDPR applies
    "Atlantic/Faroe",  # Faroe Islands — strict-side inclusion (Danish realm)
    "Atlantic/Madeira",
    "Europe/Amsterdam",
    "Europe/Athens",
    "Europe/Belfast",
    "Europe/Berlin",
    "Europe/Bratislava",
    "Europe/Brussels",
    "Europe/Bucharest",
    "Europe/Budapest",
    "Europe/Busingen",
    "Europe/Copenhagen",
    "Europe/Dublin",
    "Europe/Helsinki",
    "Europe/Lisbon",
    "Europe/Ljubljana",
    "Europe/London",
    "Europe/Luxembourg",
    "Europe/Madrid",
    "Europe/Malta",
    "Europe/Mariehamn",
    "Europe/Nicosia",
    "Europe/Oslo",
    "Europe/Paris",
    "Europe/Prague",
    "Europe/Riga",
    "Europe/Rome",
    "Europe/Sofia",
    "Europe/Stockholm",
    "Europe/Tallinn",
    "Europe/Vaduz",
    "Europe/Vienna",
    "Europe/Vilnius",
    "Europe/Warsaw",
    "Europe/Zagreb",
    "Europe/Zurich",
)


def requires_explicit_consent(timezone: str | None) -> bool:
    """Return whether ``timezone`` uses the strict opt-in consent posture.

    ``Intl.DateTimeFormat`` only returns browser-known IANA zones. A missing
    or empty result means detection failed and therefore fails closed.
    """
    if not timezone:
        return True
    try:
        ZoneInfo(timezone)
    except (TypeError, ValueError, ZoneInfoNotFoundError):
        return True
    return timezone in EEA_UK_CH_TIMEZONES


def get_consent_head_script(ga_measurement_id: str) -> str:
    """Return the synchronous geo default and GA4 config in one script block.

    The timezone branch and Consent Mode default intentionally execute before
    ``gtag('config')`` in this exact block (Gravel God repo pitfall #31). The async gtag.js
    loader is composed around this by ``brand_tokens.get_ga4_head_snippet``.
    """
    timezone_json = json.dumps(EEA_UK_CH_TIMEZONES, separators=(",", ":"))
    return (
        "<script>window.dataLayer=window.dataLayer||[];"
        "function gtag(){dataLayer.push(arguments)}"
        f"var rlConsentStrictTimezones=new Set({timezone_json});"
        "var rlConsentTimezone='';var rlConsentTimezoneKnown=false;"
        "try{rlConsentTimezone=Intl.DateTimeFormat().resolvedOptions().timeZone||'';"
        "if(rlConsentTimezone){new Intl.DateTimeFormat('en-US',"
        "{timeZone:rlConsentTimezone});rlConsentTimezoneKnown=true}}"
        "catch(rlConsentTimezoneError){}"
        "var rlConsentRequiresOptIn=!rlConsentTimezoneKnown||"
        "rlConsentStrictTimezones.has(rlConsentTimezone);"
        "window.rlConsentRequiresOptIn=rlConsentRequiresOptIn;"
        "var rlConsentAccepted=/(^|; )rl_consent=accepted/.test(document.cookie);"
        "var rlConsentDeclined=/(^|; )rl_consent=declined/.test(document.cookie);"
        "var rlConsentAnalytics=rlConsentAccepted?'granted':"
        "rlConsentDeclined?'denied':rlConsentRequiresOptIn?'denied':'granted';"
        "gtag('consent','default',{'analytics_storage':rlConsentAnalytics,"
        "'ad_storage':'denied','ad_user_data':'denied',"
        "'ad_personalization':'denied','wait_for_update':500});"
        "gtag('js',new Date());"
        f"gtag('config','{ga_measurement_id}');</script>"
    )


def get_consent_banner_html() -> str:
    """Return the footer privacy control and consent banner HTML/CSS/JS.

    Place this right before </body> on every page.
    """
    return '''<style>
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
</script>'''
