"""Past-season power rankings are retired, not re-shipped (issue #164).

/race/power-rankings-2026/ was re-uploaded on 2026-11-15 after the rollover
because wordpress/output kept the old dir and sync_pages shipped every subdir.
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "wordpress"))


def _push():
    spec = importlib.util.spec_from_file_location(
        "push_wordpress_season", ROOT / "scripts" / "push_wordpress.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_past_seasons_301_to_current_season():
    block = _push().build_redirect_block(season=2028)
    assert "RewriteRule ^race/power-rankings-2026/?$ /race/power-rankings-2028/ [R=301,L]" in block
    assert "RewriteRule ^race/power-rankings-2027/?$ /race/power-rankings-2028/ [R=301,L]" in block
    assert "power-rankings-2028/?$" not in block
    assert "{season_rules}" not in block


def test_current_season_has_no_self_redirect():
    push = _push()
    season = push.current_season()
    block = push.build_redirect_block()
    assert f"^race/power-rankings-{season}/?$" not in block


def test_stale_dirs_are_only_other_season_power_rankings():
    stale = _push().stale_power_rankings_dirs(
        ["power-rankings-2026", "power-rankings-2027", "power-rankings-x",
         "calendar", "power-rankings-2026-old"],
        2027,
    )
    assert stale == ["power-rankings-2026"]


def test_sync_pages_refuses_past_season_before_touching_server(tmp_path, monkeypatch):
    push = _push()
    season = push.current_season()
    (tmp_path / f"power-rankings-{season - 1}").mkdir()
    (tmp_path / f"power-rankings-{season - 1}" / "index.html").write_text("old")
    monkeypatch.setattr(push, "get_ssh_credentials", lambda: ("h", "u", "1"))
    monkeypatch.setattr(push, "find_prep_kit_gaps", lambda *a, **k: [])

    def no_ssh(*args, **kwargs):
        raise AssertionError("server touched despite the season gate")

    monkeypatch.setattr(push.subprocess, "run", no_ssh)
    monkeypatch.setattr(push.subprocess, "Popen", no_ssh)
    assert push.sync_pages(str(tmp_path)) is None


def test_generator_prunes_past_seasons(tmp_path):
    from generate_power_rankings import prune_past_seasons

    for name in ("power-rankings-2026", "power-rankings-2027", "calendar"):
        (tmp_path / name).mkdir()
    removed = prune_past_seasons(tmp_path, 2027)
    assert [d.name for d in removed] == ["power-rankings-2026"]
    assert sorted(p.name for p in tmp_path.iterdir()) == ["calendar", "power-rankings-2027"]


HTACCESS = (
    "RewriteRule ^race/power-rankings-2026/?$ /race/power-rankings-2027/ [R=301,L]\n"
    "RewriteRule ^race/a-vs-b/?$ - [G,L]\n"
)


def test_retire_needs_live_rule_and_existing_target():
    push = _push()
    listing = ["power-rankings-2026", "power-rankings-2027", "a-vs-b", "c-vs-d"]
    safe, kept = push.retirable_dirs(["power-rankings-2026", "a-vs-b", "c-vs-d"], HTACCESS, listing)
    assert safe == ["a-vs-b", "power-rankings-2026"]
    assert kept == ["c-vs-d"]


def test_retire_keeps_old_season_when_current_page_is_missing():
    push = _push()
    safe, kept = push.retirable_dirs(["power-rankings-2026"], HTACCESS, ["power-rankings-2026"])
    assert safe == [] and kept == ["power-rankings-2026"]


def test_retire_keeps_old_season_when_redirect_not_deployed():
    push = _push()
    listing = ["power-rankings-2026", "power-rankings-2027"]
    safe, kept = push.retirable_dirs(["power-rankings-2026"], "", listing)
    assert safe == [] and kept == ["power-rankings-2026"]
