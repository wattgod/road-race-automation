"""Vs pages the generator no longer plans are retired, not left live (issue #165).

The server held 205 /race/*-vs-*/ dirs against 150 generated: 56 orphans
showing old numbers, shipped because the stage was copied from an output dir
that never dropped a pair.
"""
from __future__ import annotations

import importlib.util
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "wordpress"))

import generate_vs_pages as vs  # noqa: E402


def _push():
    spec = importlib.util.spec_from_file_location(
        "push_wordpress_vs", ROOT / "scripts" / "push_wordpress.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _vs_rules(block: str):
    return re.findall(r"^RewriteRule \^race/(\S+-vs-\S+)/\?\$ (\S+) \[(\S+)\]$", block, re.M)


PLANNED = vs.planned_vs_slugs(vs.load_index())


def test_retired_vs_rules_cover_the_56_orphans():
    rules = _vs_rules(_push().build_redirect_block())
    assert len(rules) == 56
    assert sum(1 for _, _, flags in rules if flags == "R=301,L") == 18
    assert sum(1 for _, target, flags in rules if target == "-" and flags == "G,L") == 38


def test_retired_sources_are_not_planned_and_targets_are():
    for source, target, flags in _vs_rules(_push().build_redirect_block()):
        assert source not in PLANNED, f"{source} is still generated; its rule would hide it"
        if flags == "R=301,L":
            assert target.strip("/").removeprefix("race/") in PLANNED, target


def test_planned_pairs_skip_races_without_scores():
    good = {"slug": "a", "tier": 1, "region": "X", "overall_score": 80,
            "scores": {k: 3 for k, _ in vs.ALL_DIMS}}
    bad = dict(good, slug="b", scores={})
    assert vs.planned_pairs([good, bad]) == []
    assert vs.planned_pairs([good, dict(good, slug="c")]) == [("a", "c")]


def test_generator_prunes_unplanned_vs_dirs(tmp_path):
    for name in ("a-vs-b", "c-vs-d", "calendar", "paris-roubaix-challenge"):
        (tmp_path / name).mkdir()
    removed = vs.prune_unplanned(tmp_path, {"a-vs-b"})
    assert [d.name for d in removed] == ["c-vs-d"]
    assert sorted(p.name for p in tmp_path.iterdir()) == ["a-vs-b", "calendar", "paris-roubaix-challenge"]


def test_sync_pages_refuses_unplanned_vs_before_touching_server(tmp_path, monkeypatch):
    push = _push()
    (tmp_path / "gran-fondo-stelvio-vs-la-marmotte").mkdir()
    (tmp_path / "gran-fondo-stelvio-vs-la-marmotte" / "index.html").write_text("old")
    monkeypatch.setattr(push, "get_ssh_credentials", lambda: ("h", "u", "1"))
    monkeypatch.setattr(push, "find_prep_kit_gaps", lambda *a, **k: [])

    def no_ssh(*args, **kwargs):
        raise AssertionError("server touched despite the vs gate")

    monkeypatch.setattr(push.subprocess, "run", no_ssh)
    monkeypatch.setattr(push.subprocess, "Popen", no_ssh)
    assert push.sync_pages(str(tmp_path)) is None
