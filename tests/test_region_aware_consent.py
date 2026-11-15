"""Region-aware consent wiring outside the shared consent module.

Matti's ruling (2026-11-14): Roadie Labs uses Gravel God's consent model.
- The plan form reports the *effective* analytics consent (a stored choice,
  else the region default from the head script) so the checkout backend can
  record the server-side GA4 purchase for visitors outside opt-in regions.
- The verified Stripe webhook is the sole GA4 ``purchase`` source: no Roadie
  page fires ``gtag('event','purchase'`` from the browser.
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "wordpress"))

FORM_JS = ROOT / "web" / "training-plans-form.js"
PURCHASE_EVENT = re.compile(r"""gtag\(\s*['"]event['"]\s*,\s*['"]purchase['"]""")


def _extract_function(source: str, name: str) -> str:
    start = source.index(f"function {name}(")
    depth = 0
    for i in range(source.index("{", start), len(source)):
        if source[i] == "{":
            depth += 1
        elif source[i] == "}":
            depth -= 1
            if depth == 0:
                return source[start:i + 1]
    raise AssertionError(f"unterminated function {name}")


class TestPlanFormConsent:
    @pytest.mark.parametrize(
        ("cookie", "requires_opt_in", "expected"),
        [
            ("", False, "granted"),       # outside EEA/UK/CH, no choice
            ("", True, "denied"),         # EEA/UK/CH or unknown timezone
            ("", None, "denied"),         # head script missing: fail closed
            ("rl_consent=accepted", True, "granted"),
            ("rl_consent=declined", False, "denied"),
            ("other=1; rl_consent=declined", False, "denied"),
        ],
    )
    def test_effective_consent_matches_head_default(self, cookie, requires_opt_in, expected):
        source = FORM_JS.read_text(encoding="utf-8")
        fn = _extract_function(source, "analyticsConsentGranted")
        flag = "" if requires_opt_in is None else (
            f"window.rlConsentRequiresOptIn={json.dumps(requires_opt_in)};")
        script = (
            f"global.window={{}};{flag}"
            f"global.document={{cookie:{json.dumps(cookie)}}};"
            f"{fn}\nprocess.stdout.write(analyticsConsentGranted()?'granted':'denied');"
        )
        result = subprocess.run(["node", "-e", script], capture_output=True, text=True, timeout=10)
        assert result.returncode == 0, result.stderr
        assert result.stdout == expected

    def test_checkout_payload_uses_effective_consent(self):
        source = FORM_JS.read_text(encoding="utf-8")
        fn = _extract_function(source, "ga4Attribution")
        assert "!analyticsConsentGranted()" in fn
        assert "rl_consent=accepted/.test(document.cookie) ||" not in fn
        assert "workerData.analytics_consent = attribution.analytics_consent || 'denied';" in source


class TestNoBrowserPurchaseEvent:
    def test_no_source_fires_purchase(self):
        offenders = []
        for pattern in ("wordpress/*.py", "wordpress/mu-plugins/*.php", "scripts/*.py",
                        "web/*.js", "web/*.html"):
            for f in sorted(ROOT.glob(pattern)):
                if PURCHASE_EVENT.search(f.read_text(encoding="utf-8", errors="ignore")):
                    offenders.append(str(f.relative_to(ROOT)))
        assert not offenders, f"Browser-side purchase events: {offenders}"

    def test_generated_success_pages_do_not_fire_purchase(self):
        from generate_success_pages import PAGES, generate_success_page

        for key in PAGES:
            html = generate_success_page(key)
            assert not PURCHASE_EVENT.search(html), key
            assert "success_page_view" in html, key
