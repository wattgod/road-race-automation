"""Folded duplicate slugs 301 to their canonical race (issue #177).

They were served as July meta-refresh stubs instead of real redirects.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent

FOLDED = {
    "gran-fondo-stelvio": "la-stelvio-santini",
    "granfondo-nove-colli": "nove-colli",
    "granfondo-strade-bianche": "strade-bianche-gran-fondo",
    "oetztaler-radmarathon": "otztaler-radmarathon",
}


def _block() -> str:
    spec = importlib.util.spec_from_file_location(
        "push_wordpress_folded", ROOT / "scripts" / "push_wordpress.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.build_redirect_block()


@pytest.mark.parametrize("old,new", sorted(FOLDED.items()))
def test_folded_slug_301s_to_canonical(old, new):
    block = _block()
    assert f"RewriteRule ^race/{old}/?$ /race/{new}/ [R=301,L]" in block
    assert f"RewriteRule ^race/{old}/(.*)$ /race/{new}/$1 [R=301,L]" in block
    assert f"RewriteRule ^race/{old}\\.md$ /race/{new}.md [R=301,L]" in block
    deployed = (ROOT / "web" / "htaccess-root").read_text(encoding="utf-8")
    assert f"RewriteRule ^race/{old}/?$ /race/{new}/ [R=301,L]" in deployed
    assert f"RewriteRule ^race/{old}/(.*)$ /race/{new}/$1 [R=301,L]" in deployed
    assert f"RewriteRule ^race/{old}\\.md$ /race/{new}.md [R=301,L]" in deployed
    assert not (ROOT / "race-data" / f"{old}.json").exists()
    assert (ROOT / "race-data" / f"{new}.json").exists()


def test_subpath_rule_does_not_swallow_vs_pages():
    block = _block()
    # "^race/oetztaler-radmarathon/(.*)$" needs the slash, so the vs page
    # "oetztaler-radmarathon-vs-paris-brest-paris" keeps its own 301.
    assert ("RewriteRule ^race/oetztaler-radmarathon-vs-paris-brest-paris/?$ "
            "/race/otztaler-radmarathon-vs-paris-brest-paris/ [R=301,L]") in block
