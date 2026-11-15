"""Power rankings filter row wraps instead of overflowing a 375px phone.

Measured live 2026-11-15: the fourth .rl-pr-filter-btn ended at 402px on a
375px viewport (document scrollWidth 402), same pattern as RL-18's sort row.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "wordpress"))


def test_filter_row_wraps():
    src = (ROOT / "wordpress" / "generate_power_rankings.py").read_text(encoding="utf-8")
    m = re.search(r"\.rl-pr-filters \{\{(.*?)\}\}", src, re.S)
    assert m, ".rl-pr-filters rule missing"
    assert "flex-wrap: wrap" in m.group(1)
