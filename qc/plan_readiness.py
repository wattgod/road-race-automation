#!/usr/bin/env python3
"""
Per-race TrainingPeaks plan-catalog readiness for road-race-automation.

Reads every race-data/*.json profile and scores it for readiness:
    validator-clean AND editorial-present AND course-character-present
    AND active/registerable (web-verified eligibility) AND future-parsed-date.

Emits data/plan-readiness.json:
    - per-race record: {slug, tier, score, checks{}, eligibility_status, ready,
      runway_weeks, race_date, blockers[]}
    - ranked_queue: content-present races (editorial + course_character), sorted
      runway x rating (races with a known future date and higher rating first)
    - pilot_candidates: ready races, Tier 1 or 2, runway_weeks >= 8
    - summary: corpus-wide counts

Read-only on race-data/ — this script never writes race profiles.

Usage:
    python3 qc/plan_readiness.py            # write data/plan-readiness.json
    python3 qc/plan_readiness.py --check    # exit 1 if output would change
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date, datetime
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parent.parent
RACE_DATA_DIR = PROJECT_ROOT / "race-data"
OUTPUT_PATH = PROJECT_ROOT / "data" / "plan-readiness.json"

sys.path.insert(0, str(PROJECT_ROOT / "scripts"))
from validate_profile import validate_profile  # noqa: E402
from generate_race_dates import parse_date_specific  # noqa: E402

PILOT_TIERS = (1, 2)
PILOT_MIN_RUNWAY_WEEKS = 8


def _load_race(path: Path) -> dict[str, Any] | None:
    try:
        data = json.loads(path.read_text())
    except json.JSONDecodeError:
        return None
    race = data.get("race")
    if not isinstance(race, dict):
        return None
    return race


def _truthy_str(value: Any) -> bool:
    return isinstance(value, str) and value.strip() != ""


def _as_dict(value: Any) -> dict[str, Any]:
    """Defensive coercion — malformed profiles sometimes have a scalar where a
    section dict is expected (e.g. eligibility: "active" instead of a dict).
    Never let that crash the sweep; treat it as absent."""
    return value if isinstance(value, dict) else {}


def score_race(path: Path, today: date) -> dict[str, Any]:
    """Compute the readiness record for a single race profile."""
    slug = path.stem
    race = _load_race(path)

    if race is None:
        checks = {
            "validator_clean": False,
            "editorial": False,
            "course_character": False,
            "future_date": False,
            "active_registerable": False,
        }
        return {
            "slug": slug,
            "tier": None,
            "score": None,
            "checks": checks,
            "eligibility_status": "unknown",
            "ready": False,
            "runway_weeks": None,
            "race_date": None,
            "blockers": ["profile unreadable (invalid JSON or missing 'race' key)"],
        }

    blockers: list[str] = []

    # --- validator-clean ---
    errors = validate_profile(path)
    validator_clean = len(errors) == 0
    if not validator_clean:
        blockers.append(f"validator: {len(errors)} error(s) — {'; '.join(errors)}")

    # --- editorial ---
    biased_opinion = _as_dict(race.get("biased_opinion"))
    editorial = _truthy_str(biased_opinion.get("summary"))
    if not editorial:
        blockers.append("no editorial (biased_opinion.summary)")

    # --- course character ---
    course_description = _as_dict(race.get("course_description"))
    course_character = _truthy_str(course_description.get("character"))
    if not course_character:
        blockers.append("no course_character (course_description.character)")

    # --- future parsed date / runway ---
    vitals = _as_dict(race.get("vitals"))
    parsed_iso = parse_date_specific(vitals.get("date_specific"))
    race_date: date | None = None
    if parsed_iso:
        try:
            race_date = date.fromisoformat(parsed_iso)
        except ValueError:
            race_date = None

    future_date = race_date is not None and race_date >= today
    runway_weeks: int | None = None
    if future_date:
        runway_weeks = (race_date - today).days // 7
    if not future_date:
        blockers.append("no parsed future date")

    # --- eligibility / active-registerable ---
    eligibility = _as_dict(race.get("eligibility"))
    eligibility_status = eligibility.get("status") or "unknown"
    if eligibility_status not in ("active", "defunct", "cancelled", "unknown"):
        eligibility_status = "unknown"
    has_provenance = _truthy_str(eligibility.get("verified")) and _truthy_str(eligibility.get("source"))
    active_registerable = eligibility_status == "active" and has_provenance
    if not active_registerable:
        if eligibility_status == "unknown":
            blockers.append("eligibility unverified (unknown)")
        elif eligibility_status == "active" and not has_provenance:
            blockers.append("eligibility marked active but missing verified/source provenance")
        else:
            blockers.append(f"eligibility: {eligibility_status}")

    checks = {
        "validator_clean": validator_clean,
        "editorial": editorial,
        "course_character": course_character,
        "future_date": future_date,
        "active_registerable": active_registerable,
    }
    ready = all(checks.values())

    rating = _as_dict(race.get("fondo_rating"))
    tier = rating.get("tier")
    if tier not in (1, 2, 3, 4):
        tier = None
    score = rating.get("overall_score")
    if not isinstance(score, (int, float)):
        score = None

    return {
        "slug": slug,
        "tier": tier,
        "score": score,
        "checks": checks,
        "eligibility_status": eligibility_status,
        "ready": ready,
        "runway_weeks": runway_weeks,
        "race_date": race_date.isoformat() if race_date else None,
        "blockers": blockers,
    }


def _priority_key(record: dict[str, Any]) -> tuple:
    """Sort key for ranked_queue / pilot_candidates: runway*score desc, then
    score desc, then slug asc — for determinism."""
    runway = record["runway_weeks"]
    score = record["score"] or 0
    priority = runway * score if runway and runway > 0 else 0
    # Negate for descending sort on priority/score, slug stays ascending.
    return (-priority, -score, record["slug"])


def build(race_data_dir: Path = RACE_DATA_DIR, today: date | None = None) -> dict[str, Any]:
    """Build the full readiness payload for every profile in race_data_dir."""
    if today is None:
        today = date.today()

    records: dict[str, Any] = {}
    for path in sorted(race_data_dir.glob("*.json")):
        record = score_race(path, today)
        records[record["slug"]] = record

    content_present_slugs = [
        slug
        for slug, r in records.items()
        if r["checks"]["editorial"] and r["checks"]["course_character"]
    ]
    ranked_queue = sorted(content_present_slugs, key=lambda s: _priority_key(records[s]))

    pilot_candidates = sorted(
        (
            slug
            for slug, r in records.items()
            if r["ready"] and r["tier"] in PILOT_TIERS and (r["runway_weeks"] or 0) >= PILOT_MIN_RUNWAY_WEEKS
        ),
        key=lambda s: _priority_key(records[s]),
    )

    by_tier_ready = {"1": 0, "2": 0, "3": 0, "4": 0}
    for r in records.values():
        if r["ready"] and r["tier"] in (1, 2, 3, 4):
            by_tier_ready[str(r["tier"])] += 1

    summary = {
        "total": len(records),
        "ready": sum(1 for r in records.values() if r["ready"]),
        "content_present": len(content_present_slugs),
        "validator_clean": sum(1 for r in records.values() if r["checks"]["validator_clean"]),
        "pilot_candidates": len(pilot_candidates),
        "by_tier_ready": by_tier_ready,
    }

    return {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "races": dict(sorted(records.items())),
        "ranked_queue": ranked_queue,
        "pilot_candidates": pilot_candidates,
        "summary": summary,
    }


def _serialize(payload: dict[str, Any]) -> str:
    return json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=False) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Compute per-race TP plan readiness")
    parser.add_argument("--check", action="store_true", help="Exit 1 if output would change; don't write")
    args = parser.parse_args()

    payload = build()
    # generated_at is intentionally excluded from the --check diff (always changes).
    serialized = _serialize(payload)

    if args.check:
        current = OUTPUT_PATH.read_text() if OUTPUT_PATH.exists() else ""

        def _strip_ts(text: str) -> str:
            try:
                obj = json.loads(text) if text else {}
            except json.JSONDecodeError:
                obj = {}
            obj.pop("generated_at", None)
            return json.dumps(obj, indent=2, ensure_ascii=False, sort_keys=False)

        payload_no_ts = dict(payload)
        payload_no_ts.pop("generated_at", None)
        if _strip_ts(current) != json.dumps(payload_no_ts, indent=2, ensure_ascii=False, sort_keys=False):
            print("data/plan-readiness.json is stale — rerun qc/plan_readiness.py")
            return 1
        print("data/plan-readiness.json is up to date")
        return 0

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(serialized)

    s = payload["summary"]
    print(f"Wrote {OUTPUT_PATH} ({len(serialized):,} bytes)")
    print(
        f"total={s['total']} content_present={s['content_present']} "
        f"validator_clean={s['validator_clean']} ready={s['ready']} "
        f"pilot_candidates={s['pilot_candidates']} by_tier_ready={s['by_tier_ready']}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
