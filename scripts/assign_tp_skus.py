#!/usr/bin/env python3
"""Assign every race to a TrainingPeaks static-plan SKU family — northstar P3.1.

The TP marketplace bottleneck is that plans are built manually in TP's plan
builder, so we sell ~9 archetype FAMILIES (× 3 durations = 27 SKUs ecosystem-wide) instead
of per-race plans. Each race maps to the family whose demands it matches;
race pages deep-link to the family's TP plans once they exist.

Rule-based on the race-pack demand vectors (explainable, not a black box):
  distance      durability >= 7
  alpine-fondo  altitude >= 7 or climbing >= 7
  rolling-fast  vo2_power >= 7
  allrounder    everything else

Outputs data/tp-sku-map.json {slug: family}. Links live separately in
data/tp-sku-links.json {family: {"8": url, "12": url, "16": url}} — filled
as the TP plans get built (see athlete-custom-training-plan-pipeline/tp-skus/).

Usage: python3 scripts/assign_tp_skus.py
"""

import json
from pathlib import Path
from collections import Counter

PROJECT_ROOT = Path(__file__).resolve().parent.parent
PACKS_DIR = PROJECT_ROOT / "web" / "race-packs"
OUT_PATH = PROJECT_ROOT / "data" / "tp-sku-map.json"
LINKS_PATH = PROJECT_ROOT / "data" / "tp-sku-links.json"

FAMILIES = [
    "road-distance",
    "road-alpine-fondo",
    "road-rolling-fast",
    "road-allrounder",
]


def classify(demands: dict) -> str:
    if demands.get("durability", 0) >= 7:
        return "road-distance"
    if demands.get("altitude", 0) >= 7 or demands.get("climbing", 0) >= 7:
        return "road-alpine-fondo"
    if demands.get("vo2_power", 0) >= 7:
        return "road-rolling-fast"
    return "road-allrounder"


def main():
    mapping = {}
    for p in sorted(PACKS_DIR.glob("*.json")):
        demands = json.loads(p.read_text()).get("demands", {})
        if demands:
            mapping[p.stem] = classify(demands)

    OUT_PATH.parent.mkdir(exist_ok=True)
    OUT_PATH.write_text(json.dumps(mapping, indent=1, sort_keys=True))

    if not LINKS_PATH.exists():
        LINKS_PATH.write_text(json.dumps(
            {f: {"8": "", "12": "", "16": ""} for f in FAMILIES}, indent=1))

    counts = Counter(mapping.values())
    print(f"Assigned {len(mapping)} races → {OUT_PATH}")
    for fam, n in counts.most_common():
        print(f"  {fam}: {n}")


if __name__ == "__main__":
    main()
