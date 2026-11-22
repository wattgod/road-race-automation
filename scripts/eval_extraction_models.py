#!/usr/bin/env python3
"""
eval_extraction_models.py — Compare the cheap extractor against Claude on the same pages.

Runs both extractors on official-site HTML that is already in the scrape cache
(no fetching), then reports how often they agree per field. Claude is the
reference, not ground truth: read the disagreements before trusting either.

Usage:
  python scripts/eval_extraction_models.py --limit 30
  python scripts/eval_extraction_models.py --slug paris-brest-paris --verbose
  python scripts/eval_extraction_models.py --limit 30 --out reports/extraction-eval.json

  python scripts/eval_extraction_models.py --limit 30 --reference-model anthropic/claude-sonnet-5.5

Requires: OPENROUTER_API_KEY, plus ANTHROPIC_API_KEY unless --reference-model
routes the reference through OpenRouter. Writes nothing to race-data/.
"""

import argparse
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from scrape_utils import extract_race_facts, get_cached, load_official_sites

# Fields that feed fact_check_profiles.py and the race page.
COMPARED_FIELDS = (
    "date_2026",
    "distance_mi",
    "elevation_ft",
    "registration_status",
    "registration_cost",
    "location",
    "cutoff_time",
)

# Relative tolerance for numbers: the prompt asks for rounded values.
NUMERIC_TOLERANCE = 0.03


def _normalize(value):
    if value is None:
        return None
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return float(value)
    text = " ".join(str(value).lower().split())
    return text or None


def fields_agree(a, b) -> bool:
    """True when two extracted values are the same fact."""
    a, b = _normalize(a), _normalize(b)
    if a is None or b is None:
        return a is None and b is None
    if isinstance(a, float) and isinstance(b, float):
        if a == b:
            return True
        return abs(a - b) <= NUMERIC_TOLERANCE * max(abs(a), abs(b))
    return a == b


def compare_extracts(reference: dict, candidate: dict) -> dict:
    """Per-field verdict: agree, differ, candidate_missing or candidate_extra."""
    verdicts = {}
    for field in COMPARED_FIELDS:
        ref, cand = reference.get(field), candidate.get(field)
        if fields_agree(ref, cand):
            verdicts[field] = "agree"
        elif _normalize(cand) is None:
            verdicts[field] = "candidate_missing"
        elif _normalize(ref) is None:
            verdicts[field] = "candidate_extra"
        else:
            verdicts[field] = "differ"
    return verdicts


def summarize(cases: list[dict]) -> dict:
    """Agreement rate per field and overall, over cases where both arms returned facts."""
    scored = [c for c in cases if c.get("verdicts")]
    per_field = {}
    for field in COMPARED_FIELDS:
        counts = {"agree": 0, "differ": 0, "candidate_missing": 0, "candidate_extra": 0}
        for case in scored:
            counts[case["verdicts"][field]] += 1
        total = sum(counts.values())
        per_field[field] = {**counts, "agreement": round(counts["agree"] / total, 3) if total else None}

    all_verdicts = [v for c in scored for v in c["verdicts"].values()]
    costs = [c["candidate_cost_usd"] for c in cases if c.get("candidate_cost_usd") is not None]
    ref_costs = [c["reference_cost_usd"] for c in cases if c.get("reference_cost_usd") is not None]
    return {
        "cases": len(cases),
        "scored": len(scored),
        "reference_errors": sum(1 for c in cases if c.get("reference_error")),
        "candidate_errors": sum(1 for c in cases if c.get("candidate_error")),
        "overall_agreement": round(all_verdicts.count("agree") / len(all_verdicts), 3) if all_verdicts else None,
        "per_field": per_field,
        "candidate_cost_usd": round(sum(costs), 6) if costs else None,
        "reference_cost_usd": round(sum(ref_costs), 6) if ref_costs else None,
    }


def _extract_with_model(html: str, name: str, model: str) -> dict:
    """Run the OpenRouter extractor with one specific model, then restore the setting."""
    previous = os.environ.get("CHEAP_LLM_MODEL")
    os.environ["CHEAP_LLM_MODEL"] = model
    try:
        return extract_race_facts(html, name, {}, extractor="inkling")
    finally:
        if previous is None:
            del os.environ["CHEAP_LLM_MODEL"]
        else:
            os.environ["CHEAP_LLM_MODEL"] = previous


def run_case(slug: str, info: dict, verbose: bool = False,
             reference_model: str | None = None) -> dict | None:
    """Run both extractors on one cached page. Returns None when the page is not cached.

    reference_model, when given, is an OpenRouter model id used as the reference
    in place of the direct Anthropic call (for machines with no Anthropic key).
    """
    cached = get_cached(info["url"])
    if not cached or not cached.get("html"):
        return None
    html = cached["html"]

    if reference_model:
        reference = _extract_with_model(html, info["name"], reference_model)
    else:
        reference = extract_race_facts(html, info["name"], {}, extractor="claude")
    candidate = extract_race_facts(html, info["name"], {}, extractor="inkling")

    case = {"slug": slug, "url": info["url"]}
    if "error" in reference:
        case["reference_error"] = reference["error"]
    if "error" in candidate:
        case["candidate_error"] = candidate["error"]
    else:
        case["candidate_cost_usd"] = candidate.get("extraction_cost_usd")
    if "error" not in reference:
        case["reference_cost_usd"] = reference.get("extraction_cost_usd")
        case["reference_model"] = reference.get("extraction_model")
    if "error" not in reference and "error" not in candidate:
        case["verdicts"] = compare_extracts(reference, candidate)
        case["reference"] = {f: reference.get(f) for f in COMPARED_FIELDS}
        case["candidate"] = {f: candidate.get(f) for f in COMPARED_FIELDS}
        case["candidate_model"] = candidate.get("extraction_model")
    if verbose:
        print(json.dumps(case, indent=2, ensure_ascii=False))
    return case


def main():
    parser = argparse.ArgumentParser(description="Compare the cheap extractor against Claude")
    parser.add_argument("--limit", type=int, default=30, help="Number of cached pages to compare (default: 30)")
    parser.add_argument("--slug", help="Compare a single race")
    parser.add_argument("--reference-model",
                        help="OpenRouter model id to use as the reference instead of the "
                             "direct Anthropic call, e.g. anthropic/claude-sonnet-5.5")
    parser.add_argument("--out", help="Write the full JSON report here")
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    sites = load_official_sites(slug_filter=args.slug)
    cases = []
    for slug, info in sorted(sites.items()):
        if len(cases) >= args.limit:
            break
        case = run_case(slug, info, verbose=args.verbose, reference_model=args.reference_model)
        if case is None:
            continue
        cases.append(case)
        print(f"[{len(cases)}] {slug}")

    if not cases:
        print("No cached pages found. Run scrape_official_sites.py --no-claude first.")
        return 1

    summary = summarize(cases)
    print()
    print(f"Cases: {summary['cases']}  scored: {summary['scored']}  "
          f"claude errors: {summary['reference_errors']}  cheap-model errors: {summary['candidate_errors']}")
    print(f"Overall agreement with the reference: {summary['overall_agreement']}")
    print(f"Cost USD  reference: {summary['reference_cost_usd']}  cheap model: {summary['candidate_cost_usd']}")
    for field, row in summary["per_field"].items():
        print(f"  {field:22} agree={row['agree']:3} differ={row['differ']:3} "
              f"missing={row['candidate_missing']:3} extra={row['candidate_extra']:3}")

    if args.out:
        out = Path(args.out)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps({"summary": summary, "cases": cases}, indent=2, ensure_ascii=False) + "\n")
        print(f"\nReport: {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
