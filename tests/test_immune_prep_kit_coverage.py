"""Regression tests for run_prep_kit_coverage()'s transport handling.

2026-09-01: an uncaught http.client.RemoteDisconnected inside the thread pool
killed the whole `--live` run before report.json was written. 2026-09-02: the
sweep hung >10 min through a slow proxy with no scan-wide bound. Contract:
transport-level failures are *inconclusive* (prep-kit-check-blocked), never
"missing" (that is a real 404 only) and never a crash; the sweep is bounded
by PREP_KIT_SCAN_DEADLINE. Mirrors tests/test_immune_waf.py.
"""

from __future__ import annotations

import http.client
import io
import json
import socket
import ssl
import sys
import time
import urllib.error
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

import immune_check


class FakeResponse:
    def __init__(self, status: int):
        self.status = status

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


def _project_with_index(tmp_path: Path, slugs: list[str]) -> Path:
    web = tmp_path / "web"
    web.mkdir()
    (web / "race-index.json").write_text(
        json.dumps([{"slug": s, "has_profile": True} for s in slugs]), encoding="utf-8")
    return tmp_path


def _urlopen_for(behaviour: dict):
    """behaviour: slug -> int status | exception instance to raise."""
    def urlopen(req, timeout=12):
        slug = req.full_url.rstrip("/").split("/")[-2]
        outcome = behaviour[slug]
        if isinstance(outcome, BaseException):
            raise outcome
        return FakeResponse(outcome)
    return urlopen


def _http_404(url: str) -> urllib.error.HTTPError:
    return urllib.error.HTTPError(url, 404, "Not Found", {}, io.BytesIO(b""))


TRANSPORT_ERRORS = [
    http.client.RemoteDisconnected("Remote end closed connection without response"),
    ConnectionResetError(54, "Connection reset by peer"),
    TimeoutError("timed out"),
    socket.timeout("timed out"),
    ssl.SSLError(1, "TLS handshake failed"),
    OSError(101, "Network is unreachable"),
    urllib.error.URLError("DNS lookup failed"),
    http.client.BadStatusLine("garbage"),
]
_IDS = [type(e).__name__ for e in TRANSPORT_ERRORS]


# ── prep_kit_status(): the probe itself ──────────────────────────────────────
@pytest.mark.parametrize("exc", TRANSPORT_ERRORS, ids=_IDS)
def test_prep_kit_status_returns_none_on_transport_error(monkeypatch, exc):
    def raise_it(req, timeout=12):
        raise exc
    monkeypatch.setattr(immune_check.urllib.request, "urlopen", raise_it)
    assert immune_check.prep_kit_status("https://roadielabs.com/race/x/prep-kit/") is None


def test_prep_kit_status_never_raises_even_on_unexpected_error(monkeypatch):
    def raise_it(req, timeout=12):
        raise RuntimeError("something nobody anticipated")
    monkeypatch.setattr(immune_check.urllib.request, "urlopen", raise_it)
    assert immune_check.prep_kit_status("https://roadielabs.com/race/x/prep-kit/") is None


def test_prep_kit_status_404_is_a_real_status(monkeypatch):
    url = "https://roadielabs.com/race/x/prep-kit/"
    def raise_it(req, timeout=12):
        raise _http_404(url)
    monkeypatch.setattr(immune_check.urllib.request, "urlopen", raise_it)
    assert immune_check.prep_kit_status(url) == 404


# ── run_prep_kit_coverage(): classification ──────────────────────────────────
@pytest.mark.parametrize("exc", TRANSPORT_ERRORS, ids=_IDS)
def test_transport_error_is_blocked_not_missing_and_not_a_crash(tmp_path, monkeypatch, exc):
    monkeypatch.setattr(immune_check, "PROJECT_ROOT", _project_with_index(tmp_path, ["a-race"]))
    monkeypatch.setattr(immune_check.urllib.request, "urlopen", _urlopen_for({"a-race": exc}))

    findings = immune_check.run_prep_kit_coverage()   # must not raise

    assert [f.code for f in findings] == ["prep-kit-check-blocked"]
    assert findings[0].lane == immune_check.YELLOW
    assert "prep-kit-missing" not in [f.code for f in findings]
    # stable identity so the baseline can accept it once (issue #11 WO2)
    assert immune_check.fingerprint(findings[0]) == "prep-kit-check-blocked"


def test_404_is_missing_with_url_detail(tmp_path, monkeypatch):
    monkeypatch.setattr(immune_check, "PROJECT_ROOT", _project_with_index(tmp_path, ["letape-cunha"]))
    url = "https://roadielabs.com/race/letape-cunha/prep-kit/"
    monkeypatch.setattr(immune_check.urllib.request, "urlopen",
                        _urlopen_for({"letape-cunha": _http_404(url)}))

    findings = immune_check.run_prep_kit_coverage()

    assert [f.code for f in findings] == ["prep-kit-missing"]
    assert findings[0].detail == url
    assert immune_check.fingerprint(findings[0]) == f"prep-kit-missing::{url}"


def test_mixed_sweep_keeps_the_404_and_collapses_transport_noise(tmp_path, monkeypatch):
    slugs = ["ok-race", "gone-race", "reset-race", "timeout-race"]
    monkeypatch.setattr(immune_check, "PROJECT_ROOT", _project_with_index(tmp_path, slugs))
    monkeypatch.setattr(immune_check.urllib.request, "urlopen", _urlopen_for({
        "ok-race": 200,
        "gone-race": _http_404("https://roadielabs.com/race/gone-race/prep-kit/"),
        "reset-race": http.client.RemoteDisconnected("closed"),
        "timeout-race": TimeoutError("timed out"),
    }))

    findings = immune_check.run_prep_kit_coverage()
    codes = sorted(f.code for f in findings)

    assert codes == ["prep-kit-check-blocked", "prep-kit-missing"]
    missing = next(f for f in findings if f.code == "prep-kit-missing")
    assert "gone-race" in missing.detail
    blocked = next(f for f in findings if f.code == "prep-kit-check-blocked")
    assert "2 of 4" in blocked.detail


def test_clean_sweep_yields_nothing(tmp_path, monkeypatch):
    monkeypatch.setattr(immune_check, "PROJECT_ROOT", _project_with_index(tmp_path, ["a", "b"]))
    monkeypatch.setattr(immune_check.urllib.request, "urlopen", _urlopen_for({"a": 200, "b": 200}))
    assert immune_check.run_prep_kit_coverage() == []


# ── Scan deadline: a slow network can't hang the run ─────────────────────────
def test_scan_deadline_bounds_the_sweep_and_reports_blocked(tmp_path, monkeypatch):
    slugs = [f"slow-{i}" for i in range(4)]
    monkeypatch.setattr(immune_check, "PROJECT_ROOT", _project_with_index(tmp_path, slugs))
    monkeypatch.setattr(immune_check, "PREP_KIT_SCAN_DEADLINE", 0.2)

    def slow_urlopen(req, timeout=12):
        time.sleep(1.0)
        return FakeResponse(200)
    monkeypatch.setattr(immune_check.urllib.request, "urlopen", slow_urlopen)

    started = time.monotonic()
    findings = immune_check.run_prep_kit_coverage()
    elapsed = time.monotonic() - started

    assert elapsed < 3.0, f"sweep did not respect the deadline ({elapsed:.1f}s)"
    assert [f.code for f in findings] == ["prep-kit-check-blocked"]
    assert "deadline" in findings[0].detail
    assert "4 of 4" in findings[0].detail
