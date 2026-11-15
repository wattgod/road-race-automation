"""Race tier names: one mapping, Gravel God's names (Matti ruling 2026-11-14).

Tier 1 Elite, Tier 2 Contender, Tier 3 Solid, Tier 4 Roster
(gravel-race-automation scripts/generate_llms_txt.py TIER_LABELS).
`wordpress/brand_tokens.py` TIER_NAMES is the only definition; every
generator imports it and web/road-labs-search.js must equal it.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "wordpress"))
sys.path.insert(0, str(ROOT / "scripts"))

from brand_tokens import TIER_NAMES  # noqa: E402

EXPECTED = {1: "Elite", 2: "Contender", 3: "Solid", 4: "Roster"}
RETIRED = ("Rising", "Local", "Grassroots")


def test_canonical_mapping_is_gravel_gods():
    assert TIER_NAMES == EXPECTED


def test_search_js_matches_the_mapping():
    js = (ROOT / "web" / "road-labs-search.js").read_text(encoding="utf-8")
    m = re.search(r"const TIER_NAMES = \{([^}]*)\}", js)
    assert m, "TIER_NAMES map missing from road-labs-search.js"
    pairs = dict(re.findall(r"(\d+):\s*'([^']*)'", m.group(1)))
    assert {int(k): v for k, v in pairs.items()} == EXPECTED


def _code_files():
    for sub, pattern in (("wordpress", "*.py"), ("scripts", "*.py"), ("web", "*.js")):
        yield from sorted((ROOT / sub).glob(pattern))


def _py_files():
    return [p for p in _code_files() if p.suffix == ".py"]


def test_no_other_tier_name_mapping():
    """No Python file may define its own tier-number -> name dict (the JS
    copy is pinned by test_search_js_matches_the_mapping)."""
    tier_dict = re.compile(r"""\{\s*1\s*:\s*['"](?:Elite|The Icons)['"]""")
    offenders = [
        str(p.relative_to(ROOT)) for p in _py_files()
        if p.name != "brand_tokens.py" and tier_dict.search(p.read_text(encoding="utf-8"))
    ]
    assert not offenders, f"redefine TIER_NAMES instead of importing it: {offenders}"


@pytest.mark.parametrize("name", RETIRED)
def test_retired_tier_names_not_used_as_labels(name):
    """'Rising'/'Local'/... must not appear as a quoted tier label."""
    label = re.compile(rf"""['"]{re.escape(name)}['"]|\({re.escape(name)}\)|>{re.escape(name)}<""")
    offenders = [
        str(p.relative_to(ROOT)) for p in _code_files()
        if label.search(p.read_text(encoding="utf-8"))
    ]
    assert not offenders, f"retired tier name {name!r} in {offenders}"


def test_llms_txt_labels_follow_the_mapping():
    import generate_llms_txt
    assert generate_llms_txt.TIER_LABELS == {
        1: "Tier 1 (Elite)", 2: "Tier 2 (Contender)",
        3: "Tier 3 (Solid)", 4: "Tier 4 (Roster)",
    }


def test_methodology_table_uses_the_mapping():
    from generate_methodology import generate_methodology_page
    html = generate_methodology_page()
    for name in EXPECTED.values():
        assert f'<td style="font-weight:700">{name}</td>' in html
    for name in ("Rising", "Local"):
        assert f'<td style="font-weight:700">{name}</td>' not in html


# ── Tier hubs: counts come from the index, never typed in ──────────


def _races(tier, n):
    return [{"slug": f"r{tier}-{i}", "name": f"Race {i}", "tier": tier,
             "overall_score": 50} for i in range(n)]


def test_hub_titles_use_index_counts():
    import generate_tier_hubs as th
    all_races = _races(1, 3) + _races(2, 1) + _races(3, 2) + _races(4, 1)
    t1 = th.build_hub_page(1, _races(1, 3), all_races)
    assert "<title>The 3 Best Road Races in the World | Roadie Labs</title>" in t1
    assert "Tier 1 holds 3 races." in t1
    assert "25" not in th.TIER_META[1]["title"] + th.TIER_META[1]["description"]
    t2 = th.build_hub_page(2, _races(2, 1), all_races)
    assert "<title>1 Must-Do Road Race | Contender Tier | Roadie Labs</title>" in t2
    assert "73" not in th.TIER_META[2]["title"]


def test_hub_pluralises_one_race():
    import generate_tier_hubs as th
    all_races = _races(1, 2) + _races(2, 2) + _races(3, 2) + _races(4, 1)
    html = th.build_hub_page(4, _races(4, 1), all_races)
    assert "1 races" not in html
    assert '<div class="rl-hub-hero-count">1 race &middot;' in html
    assert "<title>Grassroots Road Events | Roster Tier | Roadie Labs</title>" in html


def test_hub_meta_description_not_double_escaped():
    import generate_tier_hubs as th
    all_races = _races(1, 2) + _races(2, 2) + _races(3, 2) + _races(4, 2)
    html = th.build_hub_page(1, _races(1, 2), all_races)
    assert "&amp;mdash;" not in html
    assert '<meta name="description" content="The definitive road events — the deepest' in html


def test_hub_refuses_a_tier_with_no_races():
    import generate_tier_hubs as th
    with pytest.raises(ValueError):
        th.build_hub_page(1, [], _races(2, 1))


def test_hub_names_follow_the_mapping():
    import generate_tier_hubs as th
    for tier, name in EXPECTED.items():
        assert th.TIER_META[tier]["name"] == name


def test_tier_hub_headings_use_the_mapping():
    from generate_tier_hubs import TIER_META
    for tier, cfg in TIER_META.items():
        assert cfg["h1"] == f"Tier {tier} — {TIER_NAMES[tier]}"


@pytest.mark.parametrize("rating", [{}, {"tier": None, "overall_score": 70},
                                    {"tier": 5, "overall_score": 70}, {"tier": 2}])
def test_blog_preview_refuses_a_missing_tier_or_score(monkeypatch, rating):
    import generate_blog_preview as gbp
    monkeypatch.setattr(gbp, "load_race", lambda slug: {"name": "Test Fondo", "vitals": {},
                                                        "fondo_rating": rating})
    with pytest.raises(ValueError):
        gbp.generate_preview_html("test-fondo")
