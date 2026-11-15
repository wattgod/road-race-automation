"""RL-16: Roadie's newsletter is its own list, not Gravel God's Substack.

Every Roadie sign-up posts to the lead-intake Worker with
source=newsletter_subscribe and brand=roadielabs. Success shows only after a
2xx; the ARTICLES nav item and the Substack ticker/carousel are gone.
"""
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "wordpress"))

import newsletter_signup as ns  # noqa: E402
from generate_about import generate_about_page  # noqa: E402
from generate_calendar import (  # noqa: E402
    SEASON_YEAR, build_calendar_page, load_edition_dates, races_for_year,
)
from generate_homepage import generate_homepage, load_race_index  # noqa: E402
from generate_legal_pages import get_privacy_content  # noqa: E402
from generate_power_rankings import build_power_rankings_page  # noqa: E402
from shared_footer import get_mega_footer_html  # noqa: E402
from shared_header import get_site_header_html  # noqa: E402

GG_SUBSTACK = "gravelgodcycling.substack.com"


def _forms(html: str) -> list[str]:
    return re.findall(r'<form class="rl-newsletter-form" data-placement="([a-z0-9_]+)"', html)


@pytest.fixture(scope="module")
def pages():
    index = load_race_index()
    races = [r for r in index if isinstance(r, dict)][:20]
    return {
        "homepage": generate_homepage(index),
        "about": generate_about_page(),
        "calendar": build_calendar_page(
            races_for_year(index, load_edition_dates(), SEASON_YEAR), SEASON_YEAR),
        "power_rankings": build_power_rankings_page(races),
        "header": get_site_header_html(),
        "footer": get_mega_footer_html(),
    }


def test_no_generator_source_names_the_gravel_god_substack():
    hits = []
    for path in sorted((ROOT / "wordpress").rglob("*")):
        if "output" in path.parts or path.suffix not in (".py", ".php", ".js", ".html"):
            continue
        if GG_SUBSTACK in path.read_text(encoding="utf-8", errors="ignore"):
            hits.append(str(path.relative_to(ROOT)))
    assert hits == []


@pytest.mark.parametrize("name", ["homepage", "about", "calendar", "power_rankings", "header", "footer"])
def test_rendered_page_has_no_substack_signup_or_nav(pages, name):
    html = pages[name]
    assert "substack" not in html.lower()
    assert "ARTICLES" not in html


@pytest.mark.parametrize("name,placements", [
    ("homepage", ["homepage", "mega_footer"]),
    ("about", ["about", "mega_footer"]),
    ("calendar", ["calendar"]),
    ("power_rankings", ["power_rankings"]),
    ("footer", ["mega_footer"]),
])
def test_signup_surfaces_carry_the_roadie_form(pages, name, placements):
    html = pages[name]
    assert _forms(html) == placements
    assert "brand:'roadielabs'" in html
    assert "source:'newsletter_subscribe'" in html
    assert "fetch(URL," in html
    assert f"var URL='{ns.LEAD_WORKER_URL}'" in html


def test_homepage_has_no_newsletter_ticker_or_article_carousel(pages):
    html = pages["homepage"]
    assert "rl-ticker-tag--brown" not in html
    assert "rl-hp-article-carousel" not in html
    assert "rl-hp-article-card" not in html


def test_form_markup_has_honeypot_label_and_status_regions():
    html = ns.newsletter_form_html("homepage")
    assert 'name="website"' in html
    assert '<label class="rl-newsletter-label" for="rl-newsletter-email-homepage">' in html
    assert 'class="rl-newsletter-success" role="status" hidden' in html
    assert 'class="rl-newsletter-error" role="alert" hidden' in html


def test_bad_placement_is_refused():
    with pytest.raises(ValueError):
        ns.newsletter_form_html('x" onmouseover="alert(1)')


def test_script_uses_text_content_and_waits_for_a_2xx():
    js = ns.newsletter_script()
    assert "innerHTML" not in js
    assert js.index("if(!r.ok) throw") < js.index("ok.hidden=false")
    assert js.index("if(!r.ok) throw") < js.index("gtag('event','email_capture'")


def test_privacy_names_the_real_processors_not_substack():
    text = get_privacy_content()
    assert "Substack" not in text
    assert "Supabase" in text and "Resend" in text


def test_copy_has_no_banned_terms():
    copy = " ".join([ns.NEWSLETTER_TITLE, ns.NEWSLETTER_TEXT, ns.NEWSLETTER_FINE,
                     ns.NEWSLETTER_SUCCESS, ns.NEWSLETTER_ERROR, ns.NEWSLETTER_INVALID])
    for word in ("Matt", "coach", "Claude", "Codex", "GPT", "AI", "Substack", "Gravel God"):
        assert not re.search(rf"\b{word}\b", copy), word


# ── Behaviour: run the form script in node against a stub DOM ──

_NODE_HARNESS = r"""
const [script, statusArg] = process.argv.slice(-2);
const status = Number(statusArg);
function el() { return { hidden: true, textContent: '', disabled: false }; }
const ok = el(), err = el(), btn = el();
const listeners = {};
const attrs = { 'data-placement': 'homepage' };
const form = {
  hidden: false,
  email: { value: ' rider@example.com ' },
  website: { value: '' },
  setAttribute(k, v) { attrs[k] = v; },
  getAttribute(k) { return attrs[k]; },
  querySelector() { return btn; },
  addEventListener(type, fn) { listeners[type] = fn; },
  parentNode: { querySelector(sel) { return sel.includes('success') ? ok : err; } },
};
globalThis.document = { querySelectorAll() { return [form]; } };
const calls = [];
const events = [];
globalThis.gtag = (...a) => events.push(a);
globalThis.fetch = (url, opts) => {
  calls.push({ url, body: JSON.parse(opts.body) });
  if (status === 0) return Promise.reject(new TypeError('network'));
  return Promise.resolve({ ok: status >= 200 && status < 300, status });
};
eval(script);
listeners.submit({ preventDefault() {} });
setTimeout(() => {
  console.log(JSON.stringify({ calls, events, formHidden: form.hidden,
    ok: { hidden: ok.hidden, text: ok.textContent },
    err: { hidden: err.hidden, text: err.textContent }, btnDisabled: btn.disabled }));
}, 20);
"""


def _run(status: int) -> dict:
    js = ns.newsletter_script()
    body = js[js.index("<script>") + len("<script>"):js.rindex("</script>")]
    out = subprocess.run(["node", "-e", _NODE_HARNESS, body, str(status)],
                         capture_output=True, text=True, timeout=30)
    assert out.returncode == 0, out.stderr
    return json.loads(out.stdout)


needs_node = pytest.mark.skipif(shutil.which("node") is None, reason="node not installed")


@needs_node
def test_2xx_posts_roadie_payload_then_shows_success():
    r = _run(200)
    assert r["calls"] == [{"url": ns.LEAD_WORKER_URL, "body": {
        "email": "rider@example.com", "brand": "roadielabs",
        "source": "newsletter_subscribe", "website": ""}}]
    assert r["formHidden"] is True
    assert r["ok"] == {"hidden": False, "text": ns.NEWSLETTER_SUCCESS}
    assert r["err"]["hidden"] is True
    assert r["events"] == [["event", "email_capture",
                            {"source": "newsletter_subscribe", "placement": "homepage"}]]


@needs_node
@pytest.mark.parametrize("status", [400, 503, 0])
def test_failure_shows_error_and_never_success(status):
    r = _run(status)
    assert r["formHidden"] is False
    assert r["ok"]["hidden"] is True
    assert r["err"] == {"hidden": False, "text": ns.NEWSLETTER_ERROR}
    assert r["btnDisabled"] is False
    assert r["events"] == []
