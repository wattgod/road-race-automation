"""Tests for scripts/checkout_monitor.py — checkout flow health monitor.

Mocks the HTTP layer (_get / _post_json) so no live calls or Stripe sessions
are created. Verifies pass/fail detection, exit codes, and the synthetic
payload shape.
"""

import sys
from datetime import date
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import checkout_monitor as cm


# ── Health check ────────────────────────────────────────────


def test_health_ok(monkeypatch):
    monkeypatch.setattr(cm, "_get", lambda url: (200, {"status": "ok"}))
    r = cm.check_health()
    assert r["ok"] is True and r["check"] == "health"


def test_health_degraded_fails(monkeypatch):
    monkeypatch.setattr(cm, "_get", lambda url: (503, {"status": "degraded"}))
    r = cm.check_health()
    assert r["ok"] is False


def test_health_unreachable_fails(monkeypatch):
    # Railway trial expired / service down → connection failure (code 0).
    monkeypatch.setattr(cm, "_get", lambda url: (0, {"error": "connection failed"}))
    r = cm.check_health()
    assert r["ok"] is False and r["http"] == 0


# ── Checkout (deep) check ───────────────────────────────────


def test_checkout_ok_with_stripe_url(monkeypatch):
    monkeypatch.setattr(cm, "_post_json", lambda u, p, o: (
        200, {"checkout_url": "https://checkout.stripe.com/c/pay/cs_test_123"}))
    r = cm.check_checkout("road")
    assert r["ok"] is True


def test_checkout_200_but_no_stripe_url_fails(monkeypatch):
    # The exact "looks fine but broken" failure mode — 200 with no real URL.
    monkeypatch.setattr(cm, "_post_json", lambda u, p, o: (200, {"checkout_url": ""}))
    r = cm.check_checkout("road")
    assert r["ok"] is False


def test_checkout_stripe_error_fails(monkeypatch):
    # e.g. consent_collection ToS not accepted → 502 from the webhook.
    monkeypatch.setattr(cm, "_post_json", lambda u, p, o: (
        502, {"error": "Payment service error. Please try again."}))
    r = cm.check_checkout("gravel")
    assert r["ok"] is False and r["http"] == 502


def test_checkout_payload_is_valid_future_dated(monkeypatch):
    captured = {}

    def fake_post(url, payload, origin):
        captured["url"] = url
        captured["payload"] = payload
        captured["origin"] = origin
        return 200, {"checkout_url": "https://checkout.stripe.com/c/pay/x"}

    monkeypatch.setattr(cm, "_post_json", fake_post)
    cm.check_checkout("road")

    p = captured["payload"]
    assert "@" in p["email"] and p["name"]
    a_race = p["races"][0]
    assert a_race["priority"] == "A"
    # Date must be in the future (endpoint rejects >7 days past).
    assert date.fromisoformat(a_race["date"]) > date.today()
    assert captured["origin"] == cm.BRANDS["road"]["origin"]
    assert captured["url"].endswith("/api/create-checkout")


# ── Aggregate run + exit code ───────────────────────────────


def test_run_shallow_skips_checkout(monkeypatch):
    monkeypatch.setattr(cm, "_get", lambda url: (200, {"status": "ok"}))
    monkeypatch.setattr(cm, "_post_json", lambda *a: pytest.fail("should not POST"))
    results = cm.run(["road", "gravel"], shallow=True)
    assert len(results) == 1 and results[0]["check"] == "health"


def test_run_full_checks_both_brands(monkeypatch):
    monkeypatch.setattr(cm, "_get", lambda url: (200, {"status": "ok"}))
    monkeypatch.setattr(cm, "_post_json", lambda u, p, o: (
        200, {"checkout_url": "https://checkout.stripe.com/c/pay/x"}))
    results = cm.run(["road", "gravel"], shallow=False)
    assert len(results) == 3  # 1 health + 2 checkout
    assert all(r["ok"] for r in results)


def test_main_exit_zero_when_all_ok(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["checkout_monitor.py", "--shallow"])
    monkeypatch.setattr(cm, "_get", lambda url: (200, {"status": "ok"}))
    assert cm.main() == 0


def test_main_exit_nonzero_when_health_down(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["checkout_monitor.py", "--shallow"])
    monkeypatch.setattr(cm, "_get", lambda url: (0, {"error": "down"}))
    assert cm.main() == 1


def test_main_exit_nonzero_when_checkout_broken(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["checkout_monitor.py", "--brand", "road"])
    monkeypatch.setattr(cm, "_get", lambda url: (200, {"status": "ok"}))
    monkeypatch.setattr(cm, "_post_json", lambda u, p, o: (502, {"error": "stripe down"}))
    assert cm.main() == 1
