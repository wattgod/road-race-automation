"""Prep-kit gate on race-page deploys (issue #11, 2026-09-04).

Every race page links to /race/{slug}/prep-kit/ (the email-capture CTA), but
kits only ever shipped through the separate opt-in --sync-prep-kits, so new
races went live with a 404 kit page (15+ slugs in the backlog). These tests
guard: the pure gate decision, that sync_pages refuses BEFORE any ssh when a
staged page's kit is missing, and that a present kit ships in the same tar
as its page.
"""

from __future__ import annotations

import io
import sys
from pathlib import Path
from unittest.mock import Mock

import pytest

SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

import push_wordpress  # noqa: E402

PAGE = '<html><body><a href="/race/{slug}/prep-kit/">Open Your Prep Kit</a></body></html>'


# ── Pure gate decision ───────────────────────────────────────────────────────
class TestPrepKitGaps:
    def test_gated_page_without_kit_is_a_gap(self):
        pages = {"letape-cunha": PAGE.format(slug="letape-cunha")}
        assert push_wordpress.prep_kit_gaps(pages, set()) == ["letape-cunha"]

    def test_gated_page_with_kit_passes(self):
        pages = {"letape-cunha": PAGE.format(slug="letape-cunha")}
        assert push_wordpress.prep_kit_gaps(pages, {"letape-cunha"}) == []

    def test_page_without_kit_link_is_not_gated(self):
        pages = {"methodology": "<html><body>no kit CTA here</body></html>"}
        assert push_wordpress.prep_kit_gaps(pages, set()) == []

    def test_link_to_another_slugs_kit_does_not_gate_this_page(self):
        pages = {"vs-page": PAGE.format(slug="some-other-race")}
        assert push_wordpress.prep_kit_gaps(pages, set()) == []

    def test_reports_every_gap_sorted(self):
        backlog = ["letape-san-bernardino", "chasing-cancellara-bern-zermatt",
                   "gran-fondo-mendoza", "letape-leshan"]
        pages = {s: PAGE.format(slug=s) for s in backlog}
        pages["paris-brest-paris"] = PAGE.format(slug="paris-brest-paris")
        gaps = push_wordpress.prep_kit_gaps(pages, {"paris-brest-paris"})
        assert gaps == sorted(backlog)

    def test_empty_html_is_not_gated(self):
        assert push_wordpress.prep_kit_gaps({"blank": ""}, set()) == []


# ── I/O wrapper ──────────────────────────────────────────────────────────────
def test_find_prep_kit_gaps_reads_pages_and_lists_kits(tmp_path):
    pages = tmp_path / "pages"
    pages.mkdir()
    (pages / "a-race.html").write_text(PAGE.format(slug="a-race"), encoding="utf-8")
    (pages / "b-race.html").write_text(PAGE.format(slug="b-race"), encoding="utf-8")
    kits = tmp_path / "kits"
    kits.mkdir()
    (kits / "b-race.html").write_text("<html>kit</html>", encoding="utf-8")
    (kits / "index.html").write_text("<html>kit index</html>", encoding="utf-8")

    gaps = push_wordpress.find_prep_kit_gaps(sorted(pages.glob("*.html")), kits)
    assert gaps == ["a-race"]


def test_find_prep_kit_gaps_with_missing_kit_dir_flags_every_gated_page(tmp_path):
    pages = tmp_path / "pages"
    pages.mkdir()
    (pages / "a-race.html").write_text(PAGE.format(slug="a-race"), encoding="utf-8")
    gaps = push_wordpress.find_prep_kit_gaps(sorted(pages.glob("*.html")), tmp_path / "nope")
    assert gaps == ["a-race"]


# ── sync_pages behaviour ─────────────────────────────────────────────────────
@pytest.fixture
def ssh_creds(monkeypatch):
    monkeypatch.setattr(push_wordpress, "get_ssh_credentials", lambda: ("host", "user", "18765"))


def _stage(tmp_path: Path, page_slugs: list[str], kit_slugs: list[str]) -> tuple[Path, Path]:
    pages = tmp_path / "pages"
    pages.mkdir()
    for slug in page_slugs:
        (pages / f"{slug}.html").write_text(PAGE.format(slug=slug), encoding="utf-8")
    kits = tmp_path / "kits"
    kits.mkdir()
    for slug in kit_slugs:
        (kits / f"{slug}.html").write_text(f"<html>{slug} kit</html>", encoding="utf-8")
    return pages, kits


def test_sync_pages_refuses_before_any_ssh_when_a_kit_is_missing(tmp_path, monkeypatch, ssh_creds, capsys):
    pages, kits = _stage(tmp_path, ["gran-fondo-mendoza", "letape-cunha"], ["gran-fondo-mendoza"])
    run = Mock()
    popen = Mock()
    monkeypatch.setattr(push_wordpress.subprocess, "run", run)
    monkeypatch.setattr(push_wordpress.subprocess, "Popen", popen)

    assert push_wordpress.sync_pages(str(pages), prep_kit_dir=str(kits)) is None

    assert run.call_count == 0, "gate must fire before the remote mkdir"
    assert popen.call_count == 0, "gate must fire before the tar+ssh push"
    out = capsys.readouterr().out
    assert "Prep-kit gate" in out
    gap_block = out.split("Prep-kit gate", 1)[1]
    assert "letape-cunha" in gap_block
    assert "gran-fondo-mendoza" not in gap_block


class FakeProc:
    """Stand-in for subprocess.Popen that snapshots the tar staging dir."""
    snapshots: list[list[str]] = []

    def __init__(self, cmd, **kwargs):
        if cmd[0] == "tar":
            root = Path(cmd[cmd.index("-C") + 1])
            FakeProc.snapshots.append(sorted(
                str(p.relative_to(root)) for p in root.rglob("*") if p.is_file()))
        self.stdout = io.BytesIO(b"")
        self.returncode = 0

    def communicate(self, timeout=None):
        return b"", b""

    def kill(self):
        pass


def test_sync_pages_ships_each_kit_in_the_same_tar_as_its_page(tmp_path, monkeypatch, ssh_creds, capsys):
    pages, kits = _stage(tmp_path, ["letape-cunha"], ["letape-cunha"])
    FakeProc.snapshots = []
    monkeypatch.setattr(push_wordpress.subprocess, "Popen", FakeProc)
    monkeypatch.setattr(push_wordpress.subprocess, "run",
                        Mock(return_value=Mock(returncode=0, stdout="", stderr="")))

    result = push_wordpress.sync_pages(str(pages), prep_kit_dir=str(kits))

    assert result is not None
    assert FakeProc.snapshots, "tar was never invoked"
    staged = FakeProc.snapshots[0]
    assert "letape-cunha/index.html" in staged
    assert "letape-cunha/prep-kit/index.html" in staged
    assert "Including 1 prep kits" in capsys.readouterr().out


def test_sync_pages_without_gated_pages_needs_no_kits(tmp_path, monkeypatch, ssh_creds):
    pages = tmp_path / "pages"
    pages.mkdir()
    (pages / "methodology.html").write_text("<html>no kit link</html>", encoding="utf-8")
    FakeProc.snapshots = []
    monkeypatch.setattr(push_wordpress.subprocess, "Popen", FakeProc)
    monkeypatch.setattr(push_wordpress.subprocess, "run",
                        Mock(return_value=Mock(returncode=0, stdout="", stderr="")))

    assert push_wordpress.sync_pages(str(pages), prep_kit_dir=str(tmp_path / "no-kits")) is not None
    assert FakeProc.snapshots[0] == ["methodology/index.html"]
