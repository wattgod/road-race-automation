#!/usr/bin/env python3
"""Flag Roadie Labs rating-block mismatches without inventing a rubric."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

try:
    from scripts import jev_client
except ImportError:  # pragma: no cover - direct script execution
    import jev_client


ROOT = Path(__file__).resolve().parent.parent
RACE_DATA = ROOT / "race-data"
DEFAULT_OUT = ROOT / "data" / "jev" / "rating-audit-report.json"


def parse_rubric() -> dict[str, list[str]]:
    """Return no rubric: Road has no written per-level rubric in its docs."""
    return {}


def _profiles(args: argparse.Namespace) -> list[tuple[str, dict[str, Any]]]:
    paths = sorted(RACE_DATA.glob("*.json"))
    profiles = [(path.stem, json.loads(path.read_text(encoding="utf-8"))) for path in paths]
    if args.slug:
        profiles = [item for item in profiles if item[0] == args.slug]
    if args.tier is not None:
        profiles = [
            item for item in profiles
            if item[1].get("race", {}).get("fondo_rating", {}).get("tier") == args.tier
        ]
    if args.limit is not None:
        profiles = profiles[: args.limit]
    return profiles


def audit_profile(slug: str, data: dict[str, Any]) -> list[dict[str, Any]]:
    race = data.get("race", {})
    opinions = race.get("biased_opinion_ratings")
    if not isinstance(opinions, dict):
        return []
    rating = race.get("fondo_rating") or {}
    rows = []
    for dimension, opinion in opinions.items():
        if not isinstance(opinion, dict):
            continue
        assigned = rating.get(dimension)
        mismatch = opinion.get("score") != assigned
        rows.append({
            "slug": slug,
            "dimension": dimension,
            "assigned": assigned,
            "jev_level": None,
            "confidence": None,
            "probabilities": {},
            "severity": None,
            "explanation_mismatch": mismatch,
            "model": None,
            "response_available": False,
        })
    return rows


def run(args: argparse.Namespace) -> dict[str, Any]:
    profiles = _profiles(args)
    rows = [
        row
        for slug, data in profiles
        for row in audit_profile(slug, data)
    ]
    report = jev_client.base_report(None, available=False)
    report.update({
        "rubric_available": False,
        "rubric_note": (
            "No written Road per-level rubric was found in docs, CLAUDE.md, "
            "or the schema-and-data skill; only deterministic block mismatch checks run."
        ),
        "rows": rows,
        "summary": {
            "profiles_considered": len(profiles),
            "profiles_skipped_no_opinions": sum(
                not isinstance(data.get("race", {}).get("biased_opinion_ratings"), dict)
                for _, data in profiles
            ),
            "explanation_mismatch": sum(row["explanation_mismatch"] for row in rows),
            "high": 0,
            "low": 0,
        },
    })
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--slug")
    parser.add_argument("--tier", type=int)
    parser.add_argument("--limit", type=int)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args(argv)
    report = run(args)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
