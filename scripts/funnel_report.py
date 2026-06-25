#!/usr/bin/env python3
"""
Conversion funnel analysis (Roadie Labs) — GA4 Data API stage-by-stage drop-off.

Reports two funnels:
  1. Training Plan funnel: race page_view → cta_click → tp_form_start →
     tp_form_submit → begin_checkout → purchase
  2. Coaching funnel: coaching page_view → coaching_cta_click →
     coaching_scroll_depth

Roadie Labs GA4 property is 540984732 (G-WQ7W8XN11N). The service-account JSON
used for the gravel property works here too IF it has been granted access to the
road property in GA4 Admin → Property Access Management.

Prerequisites:
  - Google Analytics Data API credentials (service account JSON)
  - pip install google-analytics-data

Usage:
    GA4_PROPERTY_ID=540984732 python scripts/funnel_report.py        # last 30 days
    python scripts/funnel_report.py --days 7                          # last 7 days
    python scripts/funnel_report.py --json                            # machine-readable
    python scripts/funnel_report.py --mock                            # sample data, no creds

Environment:
    GA4_PROPERTY_ID     — GA4 property ID (numeric; Roadie Labs = 540984732)
    GA4_CREDENTIALS     — path to service account JSON (default: ga4-credentials.json)
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import date, timedelta
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Roadie Labs GA4 property (G-WQ7W8XN11N). Used as the default when
# GA4_PROPERTY_ID is unset so the report "just works" for the road site.
ROADIE_GA4_PROPERTY_ID = "540984732"

# ── Funnel definitions ──────────────────────────────────────────────────
# Road fires the same GA4 event names as gravel (verified in the road
# generators). The road site has no /articles/ section, so there is no
# article funnel here.

TRAINING_PLAN_FUNNEL = [
    {"stage": "page_view",       "event": "page_view",      "label": "Race page views",
     "filter_field": "pagePath", "filter_prefix": "/race/"},
    {"stage": "cta_click",       "event": "cta_click",      "label": "CTA clicks"},
    {"stage": "tp_form_start",   "event": "tp_form_start",  "label": "Form started"},
    {"stage": "tp_form_submit",  "event": "tp_form_submit", "label": "Form submitted"},
    {"stage": "begin_checkout",  "event": "begin_checkout",  "label": "Checkout initiated"},
    {"stage": "purchase",        "event": "purchase",        "label": "Purchase completed"},
]

COACHING_FUNNEL = [
    {"stage": "page_view",              "event": "page_view",              "label": "Coaching page views",
     "filter_field": "pagePath", "filter_prefix": "/coaching/"},
    {"stage": "coaching_cta_click",     "event": "coaching_cta_click",     "label": "CTA clicks"},
    {"stage": "coaching_scroll_depth",  "event": "coaching_scroll_depth",  "label": "Deep scroll (FAQ/final CTA)"},
]


def get_funnel_data(property_id: str, credentials_path: str, days: int,
                    funnel: list[dict]) -> list[dict]:
    """Query GA4 Data API for event counts at each funnel stage."""
    try:
        from google.analytics.data_v1beta import BetaAnalyticsDataClient
        from google.analytics.data_v1beta.types import (
            DateRange,
            Dimension,
            Filter,
            FilterExpression,
            FilterExpressionList,
            Metric,
            RunReportRequest,
        )
    except ImportError:
        print("ERROR: google-analytics-data package not installed.")
        print("  pip install google-analytics-data")
        sys.exit(1)

    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = credentials_path
    client = BetaAnalyticsDataClient()

    start_date = (date.today() - timedelta(days=days)).isoformat()
    end_date = date.today().isoformat()

    stages = []
    for stage_def in funnel:
        event_filter = Filter(
            field_name="eventName",
            string_filter=Filter.StringFilter(value=stage_def["event"]),
        )

        # If the stage has a page path filter, combine with AND
        if "filter_field" in stage_def:
            path_filter = Filter(
                field_name=stage_def["filter_field"],
                string_filter=Filter.StringFilter(
                    value=stage_def["filter_prefix"],
                    match_type=Filter.StringFilter.MatchType.BEGINS_WITH,
                ),
            )
            dimension_filter = FilterExpression(
                and_group=FilterExpressionList(
                    expressions=[
                        FilterExpression(filter=event_filter),
                        FilterExpression(filter=path_filter),
                    ]
                )
            )
        else:
            dimension_filter = FilterExpression(filter=event_filter)

        request = RunReportRequest(
            property=f"properties/{property_id}",
            dimensions=[Dimension(name="eventName")],
            metrics=[Metric(name="eventCount")],
            date_ranges=[DateRange(start_date=start_date, end_date=end_date)],
            dimension_filter=dimension_filter,
        )

        response = client.run_report(request)

        count = 0
        for row in response.rows:
            count += int(row.metric_values[0].value)

        stages.append({
            "stage": stage_def["stage"],
            "label": stage_def["label"],
            "count": count,
        })

    return stages


def compute_funnel_metrics(stages: list[dict]) -> list[dict]:
    """Add drop-off and cumulative conversion percentages to stage data."""
    if not stages or stages[0]["count"] == 0:
        for s in stages:
            s["dropoff_pct"] = None
            s["cumulative_pct"] = None
        return stages

    top_count = stages[0]["count"]

    for i, s in enumerate(stages):
        # Cumulative conversion from top of funnel
        s["cumulative_pct"] = round(s["count"] / top_count * 100, 2)

        # Drop-off from previous stage
        if i == 0:
            s["dropoff_pct"] = None
        else:
            prev = stages[i - 1]["count"]
            if prev > 0:
                s["dropoff_pct"] = round((1 - s["count"] / prev) * 100, 2)
            else:
                s["dropoff_pct"] = None

    return stages


def print_funnel(title: str, stages: list[dict]):
    """Print a single funnel as a formatted table."""
    print(f"\n{'─' * 70}")
    print(f"  {title}")
    print(f"{'─' * 70}")

    # Header
    print(f"  {'Stage':<28} {'Count':>8}  {'Drop-off':>9}  {'Cumulative':>11}")
    print(f"  {'─' * 28} {'─' * 8}  {'─' * 9}  {'─' * 11}")

    for s in stages:
        dropoff = f"{s['dropoff_pct']:>8.1f}%" if s["dropoff_pct"] is not None else f"{'—':>9}"
        cumul = f"{s['cumulative_pct']:>10.1f}%" if s["cumulative_pct"] is not None else f"{'—':>11}"
        print(f"  {s['label']:<28} {s['count']:>8,}  {dropoff}  {cumul}")

    # Overall conversion
    if len(stages) >= 2 and stages[0]["count"] > 0:
        overall = stages[-1]["count"] / stages[0]["count"] * 100
        print(f"\n  Overall conversion: {overall:.2f}% "
              f"({stages[-1]['count']:,} / {stages[0]['count']:,})")


def print_report(tp_stages: list[dict], coaching_stages: list[dict], days: int):
    """Print human-readable funnel report to stdout."""
    print("=" * 70)
    print(f"ROADIE LABS CONVERSION FUNNEL REPORT — last {days} days")
    print("=" * 70)

    print_funnel("TRAINING PLAN FUNNEL", tp_stages)
    print_funnel("COACHING FUNNEL", coaching_stages)

    print(f"\n{'=' * 70}")


def get_mock_data() -> tuple[list[dict], list[dict]]:
    """Return hardcoded sample data for testing without credentials."""
    tp_stages = [
        {"stage": "page_view",       "label": "Race page views",     "count": 8200},
        {"stage": "cta_click",       "label": "CTA clicks",          "count": 1110},
        {"stage": "tp_form_start",   "label": "Form started",        "count": 360},
        {"stage": "tp_form_submit",  "label": "Form submitted",      "count": 158},
        {"stage": "begin_checkout",  "label": "Checkout initiated",   "count": 74},
        {"stage": "purchase",        "label": "Purchase completed",   "count": 27},
    ]
    coaching_stages = [
        {"stage": "page_view",              "label": "Coaching page views",          "count": 1850},
        {"stage": "coaching_cta_click",     "label": "CTA clicks",                   "count": 240},
        {"stage": "coaching_scroll_depth",  "label": "Deep scroll (FAQ/final CTA)",  "count": 610},
    ]
    return tp_stages, coaching_stages


def main():
    parser = argparse.ArgumentParser(
        description="Roadie Labs conversion funnel — stage-by-stage drop-off report"
    )
    parser.add_argument("--days", type=int, default=30,
                        help="Lookback days (default: 30)")
    parser.add_argument("--json", action="store_true",
                        help="JSON output")
    parser.add_argument("--mock", action="store_true",
                        help="Use mock data (for testing without GA4)")
    args = parser.parse_args()

    if args.mock:
        tp_stages, coaching_stages = get_mock_data()
    else:
        property_id = os.environ.get("GA4_PROPERTY_ID", ROADIE_GA4_PROPERTY_ID)

        credentials_path = os.environ.get(
            "GA4_CREDENTIALS",
            str(PROJECT_ROOT / "ga4-credentials.json")
        )
        if not Path(credentials_path).exists():
            print(f"ERROR: Credentials file not found: {credentials_path}")
            print("  Set GA4_CREDENTIALS to the service account JSON (the gravel")
            print("  ga4-credentials.json works if it has access to property")
            print(f"  {ROADIE_GA4_PROPERTY_ID}), or run with --mock.")
            sys.exit(1)

        tp_stages = get_funnel_data(
            property_id, credentials_path, args.days, TRAINING_PLAN_FUNNEL
        )
        coaching_stages = get_funnel_data(
            property_id, credentials_path, args.days, COACHING_FUNNEL
        )

    tp_stages = compute_funnel_metrics(tp_stages)
    coaching_stages = compute_funnel_metrics(coaching_stages)

    if args.json:
        output = {
            "days": args.days,
            "training_plan_funnel": tp_stages,
            "coaching_funnel": coaching_stages,
        }
        print(json.dumps(output, indent=2))
    else:
        print_report(tp_stages, coaching_stages, args.days)


if __name__ == "__main__":
    main()
