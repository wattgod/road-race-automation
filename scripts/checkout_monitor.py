#!/usr/bin/env python3
"""Checkout health monitor — full-flow synthetic check of the shared Railway
webhook + Stripe, for Roadie Labs (and Gravel God).

WHY THIS EXISTS (cross-brand lessons #7, #9, #10, #14):
  - Railway trials expire silently — the whole service goes 503 with no warning.
  - Railway shows "Online" even while route handlers crash.
  - The API can look fine while the REAL checkout is broken — Stripe can reject
    every session (expired key, or consent_collection ToS not accepted → 400 on
    every Session.create) while /health still returns 200.
  - Gravel God's training-plan checkout was broken for MONTHS, undetected,
    because only the API (not the full flow) was ever exercised.

So this monitor does TWO checks per brand:
  1. health   — GET /health → 200 and status == "ok".
  2. checkout — POST /api/create-checkout with a synthetic-but-valid payload
                (brand set via the Origin header) → 200 and a real Stripe
                checkout_url. This is the only way to catch a broken
                Session.create (the exact failure mode the lessons warn about).

SIDE EFFECTS (safe): the checkout probe creates an INCOMPLETE Stripe Checkout
Session under a clearly-labeled monitor email. It is never paid, so it auto-
expires and NO charge, NO plan generation, and NO customer email occur — the
pipeline only runs on the post-payment /webhook/stripe event, which never fires.
It does leave one stored intake record + one incomplete session per run (filter
by the monitor email). Use --shallow to skip the Stripe session entirely.

EXIT CODE: non-zero if any check fails, so a GitHub Action / cron surfaces it.

Usage:
  python scripts/checkout_monitor.py                 # both brands, health + checkout
  python scripts/checkout_monitor.py --brand road    # road only
  python scripts/checkout_monitor.py --shallow       # health only (no Stripe session)
  python scripts/checkout_monitor.py --json
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from datetime import date, timedelta

# Shared Railway webhook (both brands route through it; brand via Origin header).
DEFAULT_WEBHOOK = "https://athlete-custom-training-plan-pipeline-production.up.railway.app"
# `or DEFAULT` (not get's default) so an unset secret arriving as "" still works.
WEBHOOK_URL = (os.environ.get("CHECKOUT_WEBHOOK_URL") or DEFAULT_WEBHOOK).rstrip("/")

BRANDS = {
    "road": {
        "label": "Roadie Labs",
        "origin": "https://roadielabs.com",
        "monitor_email": "checkout-monitor@roadielabs.com",
    },
    "gravel": {
        "label": "Gravel God",
        "origin": "https://gravelgodcycling.com",
        "monitor_email": "checkout-monitor@gravelgodcycling.com",
    },
}

HTTP_TIMEOUT = 20  # seconds


def _post_json(url: str, payload: dict, origin: str) -> tuple[int, dict]:
    """POST JSON, return (status_code, parsed_body). Body {} if unparseable."""
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=body, method="POST")
    req.add_header("Content-Type", "application/json")
    req.add_header("Origin", origin)
    try:
        with urllib.request.urlopen(req, timeout=HTTP_TIMEOUT) as resp:
            raw = resp.read().decode("utf-8", "replace")
            return resp.status, _parse(raw)
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8", "replace") if e.fp else ""
        return e.code, _parse(raw)
    except (urllib.error.URLError, TimeoutError, OSError) as e:
        return 0, {"error": f"connection failed: {e}"}


def _get(url: str) -> tuple[int, dict]:
    req = urllib.request.Request(url, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=HTTP_TIMEOUT) as resp:
            return resp.status, _parse(resp.read().decode("utf-8", "replace"))
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8", "replace") if e.fp else ""
        return e.code, _parse(raw)
    except (urllib.error.URLError, TimeoutError, OSError) as e:
        return 0, {"error": f"connection failed: {e}"}


def _parse(raw: str) -> dict:
    try:
        out = json.loads(raw)
        return out if isinstance(out, dict) else {"_raw": raw[:300]}
    except (ValueError, TypeError):
        return {"_raw": raw[:300]}


def check_health() -> dict:
    """GET /health. Pass = 200 and status 'ok'."""
    code, body = _get(f"{WEBHOOK_URL}/health")
    ok = code == 200 and body.get("status") == "ok"
    detail = f"status={body.get('status', body.get('error', '?'))}"
    if code != 200:
        detail = f"HTTP {code} — {body.get('error', body.get('status', 'unreachable'))}"
    return {"check": "health", "ok": ok, "http": code, "detail": detail}


def check_checkout(brand_key: str) -> dict:
    """POST /api/create-checkout. Pass = 200 and a real Stripe checkout_url."""
    brand = BRANDS[brand_key]
    # Valid synthetic payload: an A-race ~12 weeks out (endpoint rejects past dates).
    race_date = (date.today() + timedelta(weeks=12)).isoformat()
    payload = {
        "email": brand["monitor_email"],
        "name": "Checkout Monitor",
        "races": [{
            "priority": "A",
            "name": "Synthetic Monitor Race",
            "date": race_date,
        }],
    }
    code, body = _post_json(
        f"{WEBHOOK_URL}/api/create-checkout", payload, brand["origin"]
    )
    url = body.get("checkout_url", "")
    is_stripe = isinstance(url, str) and "checkout.stripe.com" in url
    ok = code == 200 and is_stripe
    if code != 200:
        detail = f"HTTP {code} — {body.get('error', body.get('_raw', 'no body'))}"
    elif not is_stripe:
        detail = f"200 but no Stripe checkout_url (got: {url[:60] or body})"
    else:
        detail = "200 + Stripe checkout_url ✓"
    return {"check": "checkout", "ok": ok, "http": code, "detail": detail}


def run(brands: list[str], shallow: bool) -> list[dict]:
    results = []
    # Health is brand-independent (one shared service) — check once.
    health = check_health()
    results.append({**health, "brand": "shared"})
    for bk in brands:
        if shallow:
            continue
        res = check_checkout(bk)
        results.append({**res, "brand": bk, "brand_label": BRANDS[bk]["label"]})
    return results


def main() -> int:
    ap = argparse.ArgumentParser(description="Checkout flow health monitor")
    ap.add_argument("--brand", choices=["road", "gravel", "both"], default="both",
                    help="Which brand's checkout to probe (default: both)")
    ap.add_argument("--shallow", action="store_true",
                    help="Health check only — skip the Stripe session probe")
    ap.add_argument("--json", action="store_true", help="JSON output")
    args = ap.parse_args()

    brands = ["road", "gravel"] if args.brand == "both" else [args.brand]
    results = run(brands, args.shallow)
    failures = [r for r in results if not r["ok"]]

    if args.json:
        print(json.dumps({
            "webhook": WEBHOOK_URL,
            "ok": not failures,
            "results": results,
        }, indent=2))
    else:
        print(f"CHECKOUT HEALTH — {WEBHOOK_URL}")
        print("=" * 64)
        for r in results:
            mark = "✓" if r["ok"] else "✗"
            label = r.get("brand_label", r["brand"])
            print(f"  [{mark}] {r['check']:<9} {label:<12} {r['detail']}")
        print("=" * 64)
        print("ALL OK" if not failures else f"{len(failures)} CHECK(S) FAILED")

    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
