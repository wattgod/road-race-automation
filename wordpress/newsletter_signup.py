"""Roadie Labs newsletter sign-up form (RL-16).

Roadie has its own list. A sign-up posts to the shared lead-intake Worker
(gravel-race-automation/workers/fueling-lead-intake) with
source=newsletter_subscribe and brand=roadielabs; Mission Control enrolls it
in road_welcome_v1. The Worker refuses newsletter_subscribe without a brand,
so a Roadie rider never lands on a Gravel God list.

Every surface uses newsletter_form_html(placement). Each form carries its own
small script, so a page needs no other include: the script binds every
.rl-newsletter-form on the page that is not bound yet. Success shows only
after the Worker answers 2xx; anything else shows the error line and keeps
the typed address. Messages are set with textContent, never innerHTML.
"""
from __future__ import annotations

import html
import re

LEAD_WORKER_URL = "https://fueling-lead-intake.gravelgodcoaching.workers.dev"
NEWSLETTER_SOURCE = "newsletter_subscribe"
NEWSLETTER_BRAND = "roadielabs"

NEWSLETTER_TITLE = "Get Roadie Labs by email"
NEWSLETTER_TEXT = "The first email asks which race you're training for. Reply, and I'll write back."
NEWSLETTER_FINE = "No spam. Unsubscribe anytime."
NEWSLETTER_BUTTON = "SUBSCRIBE"
NEWSLETTER_SUCCESS = "You're on the list."
NEWSLETTER_ERROR = "That didn't go through. Try again in a minute."
NEWSLETTER_INVALID = "Enter a valid email address."

_PLACEMENT_RE = re.compile(r"^[a-z0-9_]{1,32}$")

_SCRIPT = """<script>
(function(){
  var URL='__WORKER__';
  var forms=document.querySelectorAll('form.rl-newsletter-form:not([data-bound])');
  Array.prototype.forEach.call(forms,function(form){
    form.setAttribute('data-bound','1');
    var box=form.parentNode;
    var ok=box.querySelector('.rl-newsletter-success');
    var err=box.querySelector('.rl-newsletter-error');
    var btn=form.querySelector('button');
    form.addEventListener('submit',function(e){
      e.preventDefault();
      if(err){err.textContent='';err.hidden=true;}
      if(form.website&&form.website.value) return;
      var email=form.email.value.trim();
      if(!email||!/^[^\\s@]+@[^\\s@]+\\.[^\\s@]+$/.test(email)){
        if(err){err.textContent='__INVALID__';err.hidden=false;}
        return;
      }
      var placement=form.getAttribute('data-placement')||'';
      if(btn) btn.disabled=true;
      fetch(URL,{method:'POST',headers:{'Content-Type':'application/json'},
        body:JSON.stringify({email:email,brand:'__BRAND__',source:'__SOURCE__',website:form.website?form.website.value:''})})
        .then(function(r){
          if(!r.ok) throw new Error('status '+r.status);
          if(typeof gtag==='function'){
            gtag('event','email_capture',{source:'__SOURCE__',placement:placement});
          }
          form.hidden=true;
          if(ok){ok.textContent='__SUCCESS__';ok.hidden=false;}
        })
        .catch(function(){
          if(btn) btn.disabled=false;
          if(err){err.textContent='__ERROR__';err.hidden=false;}
        });
    });
  });
})();
</script>"""


def _js_str(text: str) -> str:
    """Escape text for a single-quoted JS string inside an HTML <script>."""
    return (text.replace("\\", "\\\\").replace("'", "\\'")
            .replace("<", "\\x3c").replace(">", "\\x3e"))


def newsletter_script() -> str:
    return (_SCRIPT
            .replace("__WORKER__", LEAD_WORKER_URL)
            .replace("__BRAND__", NEWSLETTER_BRAND)
            .replace("__SOURCE__", NEWSLETTER_SOURCE)
            .replace("__INVALID__", _js_str(NEWSLETTER_INVALID))
            .replace("__SUCCESS__", _js_str(NEWSLETTER_SUCCESS))
            .replace("__ERROR__", _js_str(NEWSLETTER_ERROR)))


def newsletter_form_html(placement: str, *, fine_print: bool = True, dark: bool = False) -> str:
    """The sign-up form plus its script. `placement` tags analytics only."""
    if not _PLACEMENT_RE.match(placement):
        raise ValueError(f"bad newsletter placement: {placement!r}")
    fine = f'\n  <p class="rl-newsletter-fine">{html.escape(NEWSLETTER_FINE)}</p>' if fine_print else ""
    variant = " rl-newsletter--dark" if dark else ""
    return f'''<div class="rl-newsletter{variant}">
  <form class="rl-newsletter-form" data-placement="{placement}" novalidate>
    <input type="text" name="website" value="" tabindex="-1" autocomplete="off" aria-hidden="true" class="rl-newsletter-hp">
    <label class="rl-newsletter-label" for="rl-newsletter-email-{placement}">Email address</label>
    <div class="rl-newsletter-row">
      <input type="email" name="email" id="rl-newsletter-email-{placement}" required placeholder="your@email.com" autocomplete="email" class="rl-newsletter-input">
      <button type="submit" class="rl-newsletter-btn" data-ga="subscribe_click" data-ga-label="{placement}">{NEWSLETTER_BUTTON}</button>
    </div>
  </form>
  <p class="rl-newsletter-success" role="status" hidden></p>
  <p class="rl-newsletter-error" role="alert" hidden></p>{fine}
</div>
{newsletter_script()}'''


def newsletter_css() -> str:
    """Form CSS on --rl-* tokens. Ink button: green is the training offer only."""
    return """
/* ── Newsletter sign-up (RL-16) ── */
.rl-newsletter { max-width: 480px; margin: 0 auto; }
.rl-newsletter-hp { position: absolute; left: -9999px; width: 1px; height: 1px; opacity: 0; }
.rl-newsletter-label { position: absolute; width: 1px; height: 1px; overflow: hidden; clip: rect(0 0 0 0); white-space: nowrap; }
.rl-newsletter-row { display: flex; gap: 8px; }
.rl-newsletter-input { flex: 1; min-width: 0; min-height: 44px; padding: 10px 12px; font-family: var(--rl-font-data); font-size: 14px; color: var(--rl-color-dark-navy); background: var(--rl-color-white); border: 2px solid var(--rl-color-dark-navy); }
.rl-newsletter-btn { min-height: 44px; padding: 10px 18px; font-family: var(--rl-font-data); font-size: 11px; font-weight: 700; letter-spacing: 2px; color: var(--rl-color-white); background: var(--rl-color-dark-navy); border: 2px solid var(--rl-color-dark-navy); cursor: pointer; transition: background-color 0.2s, color 0.2s; }
.rl-newsletter-btn:hover { background: var(--rl-color-white); color: var(--rl-color-dark-navy); }
.rl-newsletter-btn:disabled { opacity: 0.6; cursor: wait; }
.rl-newsletter-success { margin: 8px 0 0; font-family: var(--rl-font-data); font-size: 13px; font-weight: 700; color: var(--rl-color-dark-navy); }
.rl-newsletter-error { margin: 8px 0 0; font-family: var(--rl-font-data); font-size: 13px; color: var(--rl-color-error); }
.rl-newsletter-error::before { content: "\\26A0\\FE0E  "; }
.rl-newsletter-fine { margin: 8px 0 0; font-family: var(--rl-font-data); font-size: 11px; color: var(--rl-color-secondary-blue); }
.rl-newsletter--dark .rl-newsletter-fine,
.rl-newsletter--dark .rl-newsletter-success,
.rl-newsletter--dark .rl-newsletter-error { color: var(--rl-color-silver); }
.rl-newsletter--dark .rl-newsletter-input,
.rl-newsletter--dark .rl-newsletter-btn { border-color: var(--rl-color-silver); }
@media (max-width: 600px) {
  .rl-newsletter-row { flex-direction: column; }
}
"""
