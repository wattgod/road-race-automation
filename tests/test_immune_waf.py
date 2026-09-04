"""Regression tests for the SiteGround WAF-challenge handling in the immune
link checker (2026-07-22 incident: 18 false dead/money-path findings that
were all HTTP 202 bot-challenge responses).

Covers: challenge classification, retry budget, checker exit semantics, and
immune_check's parsing of the checker's output (including crash handling).
"""

from __future__ import annotations

import io
import subprocess
import sys
import urllib.error
from pathlib import Path
from types import SimpleNamespace

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

import check_links
import immune_check


class FakeResponse:
    def __init__(self, status: int, headers: dict[str, str] | None = None,
                 body: bytes = b"", content_type: str = "text/html"):
        self.status = status
        hdrs = {"Content-Type": content_type}
        hdrs.update(headers or {})
        # email.message-style case-insensitive membership is what the code
        # relies on; a plain dict with known-case keys is close enough here.
        self.headers = hdrs
        self._body = body

    def read(self, n: int = -1) -> bytes:
        return self._body

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


# ── Challenge classification ─────────────────────────────────────────────────
def test_202_is_challenged_not_dead(monkeypatch):
    monkeypatch.setattr(check_links.urllib.request, "urlopen",
                        lambda req, timeout=15: FakeResponse(202, {"sg-captcha": "challenge"}))
    status, _, challenged = check_links.fetch_once("https://roadielabs.com/x/")
    assert status == 202 and challenged


def test_404_with_sg_captcha_header_is_dead_not_challenged(monkeypatch):
    err = urllib.error.HTTPError(
        "https://roadielabs.com/x/", 404, "Not Found",
        {"sg-captcha": "challenge"}, io.BytesIO(b""))
    def raise_it(req, timeout=15):
        raise err
    monkeypatch.setattr(check_links.urllib.request, "urlopen", raise_it)
    status, _, challenged = check_links.fetch_once("https://roadielabs.com/x/")
    assert status == 404 and not challenged


def test_200_is_clean(monkeypatch):
    monkeypatch.setattr(check_links.urllib.request, "urlopen",
                        lambda req, timeout=15: FakeResponse(200, body=b"<html></html>"))
    status, _, challenged = check_links.fetch_once("https://roadielabs.com/")
    assert status == 200 and not challenged


# ── Retry budget ─────────────────────────────────────────────────────────────
def test_retry_backoff_consumes_budget(monkeypatch):
    sleeps: list[float] = []
    monkeypatch.setattr(check_links.time, "sleep", sleeps.append)
    monkeypatch.setattr(check_links, "fetch_once",
                        lambda url, timeout=15: (202, "", True))
    monkeypatch.setattr(check_links, "_challenge_budget",
                        check_links.CHALLENGE_RETRY_BUDGET)
    status, _, challenged = check_links.fetch("https://roadielabs.com/x/")
    assert challenged
    assert sleeps == list(check_links.CHALLENGE_BACKOFF)
    assert check_links._challenge_budget == \
        check_links.CHALLENGE_RETRY_BUDGET - sum(check_links.CHALLENGE_BACKOFF)


def test_exhausted_budget_skips_sleeping(monkeypatch):
    sleeps: list[float] = []
    monkeypatch.setattr(check_links.time, "sleep", sleeps.append)
    monkeypatch.setattr(check_links, "fetch_once",
                        lambda url, timeout=15: (202, "", True))
    monkeypatch.setattr(check_links, "_challenge_budget", 5)
    status, _, challenged = check_links.fetch("https://roadielabs.com/x/")
    assert challenged and sleeps == []


def test_incident_pattern_fits_subprocess_timeout():
    """18 persistently challenged URLs (the Jul 22 pattern) must not be able
    to sleep past immune_check's 900s subprocess timeout."""
    assert check_links.CHALLENGE_RETRY_BUDGET + 120 < 900


# ── immune_check parsing of checker output ───────────────────────────────────
def run_with(stdout: str, returncode: int, stderr: str = ""):
    fake = SimpleNamespace(stdout=stdout, stderr=stderr, returncode=returncode)
    return fake


def parse(monkeypatch, stdout, returncode, stderr=""):
    monkeypatch.setattr(immune_check.subprocess, "run",
                        lambda *a, **k: run_with(stdout, returncode, stderr))
    return immune_check.run_live_link_check()


def test_mixed_waf_and_dead(monkeypatch):
    stdout = (
        "  WAF challenge on https://roadielabs.com/a/ — retrying in 20s\n"
        "Checked 11 of 12 seed pages + 300 discovered URLs\n"
        "\nWAF-CHALLENGED (2): still behind SiteGround's bot challenge after retries\n"
        "   202  https://roadielabs.com/a/\n"
        "   202  https://roadielabs.com/a/\n"
        "\nDEAD LINKS (2):\n"
        "   404  https://roadielabs.com/coaching/\n"
        "   500  https://roadielabs.com/some-page/\n")
    findings = parse(monkeypatch, stdout, 1)
    codes = [f.code for f in findings]
    assert codes.count("live-check-challenged") == 1
    assert "money-path-404" in codes and "dead-link" in codes
    assert "live-check-failed" not in codes
    challenged = next(f for f in findings if f.code == "live-check-challenged")
    assert "https://roadielabs.com/a/" in challenged.detail
    assert challenged.lane == immune_check.YELLOW
    money = next(f for f in findings if f.code == "money-path-404")
    assert money.lane == immune_check.RED


def test_challenged_only_rc2(monkeypatch):
    stdout = (
        "Checked 12 of 12 seed pages + 300 discovered URLs\n"
        "\nWAF-CHALLENGED (1): still behind SiteGround's bot challenge after retries\n"
        "   202  https://roadielabs.com/questionnaire/\n"
        "No dead links found, but the scan is INCONCLUSIVE (WAF challenges).\n")
    findings = parse(monkeypatch, stdout, 2)
    assert [f.code for f in findings] == ["live-check-challenged"]
    assert "questionnaire" in findings[0].detail


def test_crash_is_a_finding_not_silence(monkeypatch):
    findings = parse(monkeypatch, "", 3, stderr="Traceback (most recent call last): ...")
    assert [f.code for f in findings] == ["live-check-failed"]
    assert "Traceback" in findings[0].detail


def test_rc1_without_parsable_dead_lines_flags_drift(monkeypatch):
    findings = parse(monkeypatch, "SOMETHING UNEXPECTED\n", 1)
    assert [f.code for f in findings] == ["live-check-failed"]


def test_clean_run_yields_nothing(monkeypatch):
    findings = parse(monkeypatch, "Checked 12 of 12 seed pages + 300 discovered URLs\nAll links alive.\n", 0)
    assert findings == []


# ── Fingerprint stability for volatile findings ──────────────────────────────
def test_live_check_challenged_fingerprint_is_stable():
    """Regression test for the volatile-detail bug: live-check-challenged findings
    with different URL lists must produce the same fingerprint so they don't
    re-alert every run (26+ days of noise across three race DBs)."""
    finding_a = immune_check.Finding(
        code="live-check-challenged",
        lane=immune_check.YELLOW,
        severity="low",
        title="Live Check Challenged by WAF",
        detail="2 URLs unverifiable behind SiteGround's bot challenge: https://roadielabs.com/a/ https://roadielabs.com/b/",
        remedy="Transport noise, re-run later",
        source="check_links",
    )
    finding_b = immune_check.Finding(
        code="live-check-challenged",
        lane=immune_check.YELLOW,
        severity="low",
        title="Live Check Challenged by WAF",
        detail="3 URLs unverifiable behind SiteGround's bot challenge: https://roadielabs.com/c/ https://roadielabs.com/d/ https://roadielabs.com/e/",
        remedy="Transport noise, re-run later",
        source="check_links",
    )
    # Different details → same fingerprint (code alone)
    assert immune_check.fingerprint(finding_a) == immune_check.fingerprint(finding_b) == "live-check-challenged"


def test_prep_kit_check_blocked_fingerprint_is_stable():
    """prep-kit-check-blocked is also volatile (non-404 transport noise)."""
    finding_a = immune_check.Finding(
        code="prep-kit-check-blocked",
        lane=immune_check.YELLOW,
        severity="low",
        title="Prep-Kit Coverage Partially Blocked",
        detail="some kit URLs returned non-404 errors (WAF challenge / timeout) — coverage unverified for those",
        remedy="Transport noise",
        source="prep_kit_coverage",
    )
    finding_b = immune_check.Finding(
        code="prep-kit-check-blocked",
        lane=immune_check.YELLOW,
        severity="low",
        title="Prep-Kit Coverage Partially Blocked",
        detail="different detail text that changes run to run",
        remedy="Transport noise",
        source="prep_kit_coverage",
    )
    assert immune_check.fingerprint(finding_a) == immune_check.fingerprint(finding_b) == "prep-kit-check-blocked"


def test_non_volatile_findings_still_fingerprint_with_detail():
    """Findings that aren't volatile (e.g. 404s) must still include detail in
    their fingerprint so distinct errors don't collapse."""
    finding_a = immune_check.Finding(
        code="prep-kit-missing",
        lane=immune_check.YELLOW,
        severity="high",
        title="Prep kit missing: unbound-gravel",
        detail="https://roadielabs.com/race/unbound-gravel/prep-kit/",
        remedy="Generate and deploy the kit page",
        source="prep_kit_coverage",
    )
    finding_b = immune_check.Finding(
        code="prep-kit-missing",
        lane=immune_check.YELLOW,
        severity="high",
        title="Prep kit missing: dirty-kanza",
        detail="https://roadielabs.com/race/dirty-kanza/prep-kit/",
        remedy="Generate and deploy the kit page",
        source="prep_kit_coverage",
    )
    # Different details → different fingerprints (include detail)
    fp_a = immune_check.fingerprint(finding_a)
    fp_b = immune_check.fingerprint(finding_b)
    assert fp_a != fp_b
    assert "https://roadielabs.com/race/unbound-gravel/prep-kit/" in fp_a
    assert "https://roadielabs.com/race/dirty-kanza/prep-kit/" in fp_b


# ── Transport failures are inconclusive, never dead (issue #11, 2026-09-04) ──
# Before this fix fetch_once() returned (0, "", False) for any non-HTTP
# exception, so a connection reset / timeout printed under DEAD LINKS as
# "ERR" and immune_check turned it into a dead-link — or a RED money-path-404
# when the URL happened to be /questionnaire/ or /coaching/.
import http.client
import socket
import ssl

TRANSPORT_ERRORS = [
    http.client.RemoteDisconnected("Remote end closed connection without response"),
    ConnectionResetError(54, "Connection reset by peer"),
    TimeoutError("timed out"),
    socket.timeout("timed out"),
    ssl.SSLError(1, "TLS handshake failed"),
    OSError(101, "Network is unreachable"),
    urllib.error.URLError("DNS lookup failed"),
]


@pytest.mark.parametrize("exc", TRANSPORT_ERRORS, ids=[type(e).__name__ for e in TRANSPORT_ERRORS])
def test_transport_failure_is_inconclusive_not_dead(monkeypatch, exc):
    def raise_it(req, timeout=15):
        raise exc
    monkeypatch.setattr(check_links.urllib.request, "urlopen", raise_it)
    status, body, challenged = check_links.fetch_once("https://roadielabs.com/questionnaire/")
    assert (status, body, challenged) == (0, "", True)


def test_http_404_is_still_dead_after_transport_fix(monkeypatch):
    err = urllib.error.HTTPError("https://roadielabs.com/x/", 404, "Not Found", {}, io.BytesIO(b""))
    def raise_it(req, timeout=15):
        raise err
    monkeypatch.setattr(check_links.urllib.request, "urlopen", raise_it)
    status, _, challenged = check_links.fetch_once("https://roadielabs.com/x/")
    assert status == 404 and not challenged


def test_transport_failure_lands_under_waf_challenged_not_dead_links(monkeypatch, capsys):
    """End to end through main(): a reset URL prints as an ERR row under the
    WAF-CHALLENGED header (which immune_check maps to live-check-challenged),
    never under DEAD LINKS, and the exit code is 2 (inconclusive), not 1."""
    monkeypatch.setattr(check_links, "SEED_PATHS", ["/"])
    monkeypatch.setattr(check_links, "EXTRA_URLS", ["https://roadielabs.com/questionnaire/"])
    monkeypatch.setattr(check_links.time, "sleep", lambda s: None)
    monkeypatch.setattr(check_links, "_challenge_budget", 0)  # no retries: record immediately

    def fake_fetch_once(url, timeout=15):
        if url.endswith("/questionnaire/"):
            return 0, "", True          # what fetch_once now returns on a reset
        return 200, "<html><body>home</body></html>", False
    monkeypatch.setattr(check_links, "fetch_once", fake_fetch_once)
    monkeypatch.setattr(sys, "argv", ["check_links.py"])

    rc = check_links.main()
    out = capsys.readouterr().out

    assert rc == 2
    assert "WAF-CHALLENGED (1)" in out
    assert "   ERR  https://roadielabs.com/questionnaire/" in out
    assert "DEAD LINKS" not in out


def test_immune_parses_err_row_under_waf_header_as_challenged_not_money_path(monkeypatch):
    """The checker's ERR row for a money-path URL must classify as
    live-check-challenged (YELLOW), never money-path-404 (RED)."""
    stdout = (
        "Checked 1 of 1 seed pages + 1 discovered URLs\n"
        "\nWAF-CHALLENGED (1): still behind SiteGround's bot challenge (202) or "
        "unreachable at the transport level (ERR) after retries — scan inconclusive, NOT dead links\n"
        "   ERR  https://roadielabs.com/questionnaire/\n"
        "No dead links found, but the scan is INCONCLUSIVE (WAF challenges).\n")
    findings = parse(monkeypatch, stdout, 2)
    assert [f.code for f in findings] == ["live-check-challenged"]
    assert findings[0].lane == immune_check.YELLOW
    assert "questionnaire" in findings[0].detail
