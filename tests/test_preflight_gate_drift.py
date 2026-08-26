"""Regression coverage for static-site preflight ownership and JS wiring."""

import json
import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "wordpress"))

from generate_insights import generate_insights_page  # noqa: E402
from generate_neo_brutalist import build_inline_js, get_page_css  # noqa: E402


def _assert_valid_js(js: str) -> None:
    result = subprocess.run(
        [
            "node", "-e",
            f"try {{ new Function({json.dumps(js)}); }}"
            f" catch(e) {{ console.error(e.message); process.exit(1); }}",
        ],
        capture_output=True,
        text=True,
        timeout=10,
    )
    assert result.returncode == 0, result.stderr


def test_race_runtime_is_valid_javascript_and_status_css_is_not_embedded():
    js = build_inline_js().replace("<script>", "").replace("</script>", "")
    _assert_valid_js(js)
    assert ".rl-status-notice {" not in js
    assert ".rl-status-notice" in get_page_css()


def test_insights_page_renders_the_canonical_race_runtime():
    page = generate_insights_page()
    assert "var section = this.closest('.rl-section, .rl-sticky-cta');" in page
    assert "gtag('event', 'cta_click'" in page


def test_static_site_does_not_require_a_wordpress_ab_plugin():
    assert not (PROJECT_ROOT / "wordpress" / "mu-plugins" / "rl-ab.php").exists()
    assert (PROJECT_ROOT / "web" / "rl-ab-tests.js").exists()
    assert (PROJECT_ROOT / "web" / "ab" / "experiments.json").exists()
