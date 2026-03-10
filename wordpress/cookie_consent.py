"""Shared cookie consent banner for all generated pages.

Provides get_consent_banner_html() for a lightweight, brand-consistent
consent banner with Google Consent Mode v2 integration.

Used by all generators that include GA4 tracking (~24 generators).

The banner:
- Shows only if no rl_consent cookie exists
- Accept → sets rl_consent=accepted, updates consent mode to 'granted'
- Decline → sets rl_consent=declined, updates consent mode to 'denied'
- Links to /cookies/ for full cookie policy

Hex values MUST match tokens.css (source of truth):
  --rl-color-primary-brown: #59473c
  --rl-color-secondary-brown: #8c7568
  --rl-color-tan: #d4c5b9
  --rl-color-teal: #1A8A82
  --rl-color-light-teal: #4ECDC4
  --rl-color-gold: #B7950B
  --rl-color-white: #ffffff

Note: This module uses hardcoded hex because the banner renders inline
before tokens.css loads. The mu-plugin (rl-cookie-consent.php) also
hardcodes hex because mu-plugins have no access to :root tokens.
Parity between Python and PHP is enforced by test_cookie_consent_mu_plugin.py.
"""
from __future__ import annotations


def get_consent_banner_html() -> str:
    """Return the cookie consent banner HTML + inline CSS + JS.

    Place this right before </body> on every page.
    """
    return '''<style>
.rl-consent-banner{position:fixed;bottom:0;left:0;right:0;z-index:9999;background:#59473c;border-top:3px solid #B7950B;padding:16px 24px;display:none;align-items:center;justify-content:center;gap:16px;flex-wrap:wrap;font-family:'Sometype Mono',monospace}
.rl-consent-banner.rl-consent-show{display:flex}
.rl-consent-text{color:#d4c5b9;font-size:13px;line-height:1.5;max-width:640px}
.rl-consent-text a{color:#4ECDC4;text-decoration:none}
.rl-consent-text a:hover{color:#ffffff}
.rl-consent-btn{padding:8px 20px;font-family:'Sometype Mono',monospace;font-size:12px;font-weight:700;letter-spacing:1px;text-transform:uppercase;cursor:pointer;border:2px solid;transition:background-color .3s,color .3s,border-color .3s}
.rl-consent-btn:focus-visible{outline:2px solid #4ECDC4;outline-offset:2px}
.rl-consent-accept{background:#1A8A82;color:#ffffff;border-color:#1A8A82}
.rl-consent-accept:hover{background:#59473c;border-color:#1A8A82;color:#1A8A82}
.rl-consent-decline{background:transparent;color:#d4c5b9;border-color:#8c7568}
.rl-consent-decline:hover{border-color:#d4c5b9;color:#ffffff}
@media(max-width:600px){.rl-consent-banner{flex-direction:column;text-align:center;padding:12px 16px}.rl-consent-text{font-size:12px}}
@media(prefers-reduced-motion:reduce){.rl-consent-btn{transition:none}}
</style>
<div class="rl-consent-banner" id="rl-consent-banner" role="dialog" aria-label="Cookie consent" aria-describedby="rl-consent-desc">
  <p class="rl-consent-text" id="rl-consent-desc">We use cookies for analytics to improve this site. No ads, no tracking across sites. <a href="/cookies/">Learn more</a>.</p>
  <button class="rl-consent-btn rl-consent-accept" id="rl-consent-accept">Accept</button>
  <button class="rl-consent-btn rl-consent-decline" id="rl-consent-decline">Decline</button>
</div>
<script>
(function(){
  var b=document.getElementById('rl-consent-banner');
  if(!b)return;
  if(/(^|; )rl_consent=/.test(document.cookie))return;
  b.classList.add('rl-consent-show');
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
