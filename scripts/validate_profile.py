#!/usr/bin/env python3
"""
Validate a road race event profile against the schema and scoring rules.

Usage:
    python validate_profile.py race-data/maratona-dles-dolomites.json
    python validate_profile.py --all          # Validate all profiles
"""

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
RACE_DATA = PROJECT_ROOT / "race-data"
CONFIG = PROJECT_ROOT / "config" / "dimensions.json"

_config = json.loads(CONFIG.read_text())
SCORE_FIELDS = [d["key"] for d in _config["dimensions"]]
VALID_DISCIPLINES = set(_config["disciplines"])
RATING_KEY = "fondo_rating"


def validate_profile(path: Path) -> list[str]:
    """Validate a single profile. Returns list of errors (empty = valid)."""
    errors = []
    slug = path.stem

    try:
        data = json.loads(path.read_text())
    except json.JSONDecodeError as e:
        return [f"{slug}: Invalid JSON — {e}"]

    race = data.get("race")
    if not race:
        return [f"{slug}: Missing 'race' key"]

    # Required top-level fields
    for field in ("name", "slug", "vitals", RATING_KEY, "final_verdict", "citations"):
        if field not in race:
            errors.append(f"{slug}: Missing race.{field}")

    # Vitals
    vitals = race.get("vitals", {})
    for field in ("distance_km", "location", "date"):
        if not vitals.get(field):
            errors.append(f"{slug}: Missing vitals.{field}")

    # Dual units check
    if vitals.get("distance_km") and not vitals.get("distance_mi"):
        errors.append(f"{slug}: Has distance_km but missing distance_mi (dual units required)")
    if vitals.get("elevation_m") and not vitals.get("elevation_ft"):
        errors.append(f"{slug}: Has elevation_m but missing elevation_ft (dual units required)")

    # Rating
    rating = race.get(RATING_KEY, {})
    for dim in SCORE_FIELDS:
        score = rating.get(dim)
        if score is None:
            errors.append(f"{slug}: Missing {RATING_KEY}.{dim}")
        elif not isinstance(score, (int, float)) or score < 1 or score > 5:
            errors.append(f"{slug}: {RATING_KEY}.{dim} = {score} (must be 1-5)")

    # Overall score math
    if all(rating.get(f) for f in SCORE_FIELDS):
        base_sum = sum(rating.get(f, 0) for f in SCORE_FIELDS)
        ci = rating.get("cultural_impact", 0)
        expected = round((base_sum + ci) / 70 * 100)
        actual = rating.get("overall_score", 0)
        if expected != actual:
            errors.append(f"{slug}: overall_score={actual} but dimensions sum to {expected}")

    # Tier
    tier = rating.get("tier")
    if tier not in (1, 2, 3, 4):
        errors.append(f"{slug}: Invalid tier={tier}")

    # Discipline
    disc = rating.get("discipline")
    if disc and disc not in VALID_DISCIPLINES:
        errors.append(f"{slug}: Unknown discipline '{disc}' (valid: {VALID_DISCIPLINES})")

    # Citations
    citations = race.get("citations", [])
    if len(citations) < 3:
        errors.append(f"{slug}: Only {len(citations)} citations (minimum 3)")
    for i, c in enumerate(citations):
        if not c.get("url"):
            errors.append(f"{slug}: Citation {i} missing URL")

    # Final verdict
    verdict = race.get("final_verdict", {})
    if not verdict.get("one_liner"):
        errors.append(f"{slug}: Missing final_verdict.one_liner")

    # Climb profile check (required if climbing >= 3)
    climbing_score = rating.get("climbing", 0)
    if climbing_score >= 3 and "climb_profile" not in race:
        errors.append(f"{slug}: climbing={climbing_score} but no climb_profile section")

    return errors


def main():
    parser = argparse.ArgumentParser(description="Validate road race profiles")
    parser.add_argument("files", nargs="*", help="Profile JSON files to validate")
    parser.add_argument("--all", action="store_true", help="Validate all profiles in race-data/")
    args = parser.parse_args()

    if args.all:
        files = sorted(RACE_DATA.glob("*.json"))
    elif args.files:
        files = [Path(f) for f in args.files]
    else:
        parser.print_help()
        sys.exit(1)

    total_errors = 0
    for path in files:
        errors = validate_profile(path)
        if errors:
            for e in errors:
                print(f"  ERROR: {e}")
            total_errors += len(errors)
        else:
            print(f"  OK: {path.stem}")

    print(f"\n{len(files)} profiles checked, {total_errors} errors")
    sys.exit(1 if total_errors > 0 else 0)


if __name__ == "__main__":
    main()
