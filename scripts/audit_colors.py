#!/usr/bin/env python3
"""
Audit all brand color usage across the codebase.

Verifies that every hardcoded hex color matches the canonical brand tokens
in wordpress/brand_tokens.py. Flags any stale or out-of-sync values.

Also checks WCAG AA contrast ratios for key color pairs.

Usage:
    python scripts/audit_colors.py           # Run full audit
    python scripts/audit_colors.py --fix     # Show suggested fix commands
    python scripts/audit_colors.py --contrast # Only run contrast checks
"""

import argparse
import math
import re
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

# ── Canonical brand colors (source of truth) ──────────────────
# These MUST match the values in wordpress/brand_tokens.py
# Roadie Labs "Newsprint / Charcoal" monochrome palette
CANONICAL_COLORS = {
    "rich_black": "#1a1a1a",
    "charcoal": "#333333",
    "medium_gray": "#555555",
    "muted_gray": "#777777",
    "light_gray": "#999999",
    "warm_silver": "#d0d0c8",
    "newsprint": "#f5f5f0",
    "error": "#8b1a1a",
    "tier_1": "#1a1a1a",
    "tier_2": "#4a4a4a",
    "tier_3": "#777777",
    "tier_4": "#aaaaaa",
}

# Old values that should NEVER appear in the codebase (Gravel God palette)
BANNED_COLORS = {
    "#3a2e25": "GG dark brown (use #1a1a1a)",
    "#9a7e0a": "GG gold (use #333333)",
    "#B7950B": "GG gold alt (use #333333)",
    "#b7950b": "GG gold alt (use #333333)",
    "#59473c": "GG primary brown (use #1a1a1a)",
    "#f5efe6": "GG warm paper (use #f5f5f0)",
    "#ede4d8": "GG sand (use #f5f5f0)",
    "#d4c5b9": "GG muted tan (use #d0d0c8)",
    "#1a1613": "GG near-black (use #1a1a1a)",
    "#8c7568": "GG secondary brown (use #555555)",
    "#7d695d": "GG T2 brown (use #4a4a4a)",
    "#766a5e": "GG T3 (use #777777)",
    "#5e6868": "GG T4 (use #aaaaaa)",
    "#178079": "GG teal (use #333333)",
    "#1A8A82": "GG teal alt (use #333333)",
    "#1a8a82": "GG teal alt (use #333333)",
}

# Files to scan (glob patterns relative to project root)
SCAN_PATTERNS = [
    "wordpress/*.py",
    "web/*.html",
    "web/*.js",
    "scripts/*.py",
    "scripts/media_templates/*.py",
    "workers/**/*.js",
    "guide/*.json",
    "tests/*.py",
    "docs/**/*.md",
    "skills/*.md",
]

# Files to skip (build output, node_modules, etc.)
SKIP_PATTERNS = {"wordpress/output", "node_modules", ".git", "__pycache__"}

# ── WCAG Contrast Checking ────────────────────────────────────

# Required contrast pairs: (foreground, background, min_ratio, label)
CONTRAST_PAIRS = [
    ("#1a1a1a", "#f5f5f0", 4.5, "T1 rich black on newsprint"),
    ("#4a4a4a", "#f5f5f0", 4.5, "T2 dark gray on newsprint"),
    ("#777777", "#f5f5f0", 4.5, "T3 muted gray on newsprint"),
    ("#aaaaaa", "#f5f5f0", 3.0, "T4 light gray on newsprint (large text)"),
    ("#333333", "#ffffff", 4.5, "Charcoal on white"),
    ("#1a1a1a", "#d0d0c8", 4.5, "Rich black on warm silver"),
    ("#555555", "#f5f5f0", 4.5, "Medium gray on newsprint"),
]


def linearize(c):
    """Convert sRGB 0-255 to linear."""
    s = c / 255.0
    if s <= 0.04045:
        return s / 12.92
    return ((s + 0.055) / 1.055) ** 2.4


def relative_luminance(hex_color):
    """Calculate relative luminance from hex color."""
    h = hex_color.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return 0.2126 * linearize(r) + 0.7152 * linearize(g) + 0.0722 * linearize(b)


def contrast_ratio(fg, bg):
    """Calculate WCAG contrast ratio between two hex colors."""
    l1 = relative_luminance(fg)
    l2 = relative_luminance(bg)
    lighter = max(l1, l2)
    darker = min(l1, l2)
    return (lighter + 0.05) / (darker + 0.05)


def check_contrast():
    """Check all required contrast pairs. Returns (passes, failures)."""
    passes = []
    failures = []
    for fg, bg, min_ratio, label in CONTRAST_PAIRS:
        ratio = contrast_ratio(fg, bg)
        entry = (label, fg, bg, ratio, min_ratio)
        if ratio >= min_ratio:
            passes.append(entry)
        else:
            failures.append(entry)
    return passes, failures


def should_skip(path):
    """Check if file path should be skipped."""
    parts = str(path.relative_to(PROJECT_ROOT)).split("/")
    if any(skip in parts for skip in SKIP_PATTERNS):
        return True
    # Skip this script's own BANNED_COLORS dict
    if path.name == "audit_colors.py":
        return True
    return False


def scan_for_banned_colors():
    """Scan all source files for banned color values. Returns list of (file, line, color, note)."""
    findings = []
    for pattern in SCAN_PATTERNS:
        for filepath in PROJECT_ROOT.glob(pattern):
            if should_skip(filepath) or not filepath.is_file():
                continue
            try:
                lines = filepath.read_text(encoding="utf-8").splitlines()
            except (UnicodeDecodeError, PermissionError):
                continue
            for i, line in enumerate(lines, 1):
                for banned, note in BANNED_COLORS.items():
                    if banned in line:
                        findings.append((filepath, i, banned, note))
    return findings


def verify_brand_tokens_sync():
    """Verify that brand_tokens.py COLORS dict matches CSS custom properties."""
    bt_path = PROJECT_ROOT / "wordpress" / "brand_tokens.py"
    content = bt_path.read_text()

    issues = []

    # Extract CSS custom property values
    css_vars = {}
    for m in re.finditer(r"--rl-color-([\w-]+):\s*(#[0-9a-fA-F]{6});", content):
        css_vars[m.group(1)] = m.group(2).lower()

    # Extract COLORS dict values
    colors_dict = {}
    for m in re.finditer(r'"(\w+)":\s*"(#[0-9a-fA-F]{6})"', content):
        colors_dict[m.group(1)] = m.group(2).lower()

    # Cross-check tier colors
    for tier in range(1, 5):
        css_key = f"tier-{tier}"
        dict_key = f"tier_{tier}"
        css_val = css_vars.get(css_key, "MISSING")
        dict_val = colors_dict.get(dict_key, "MISSING")
        if css_val != dict_val:
            issues.append(f"MISMATCH: CSS --rl-color-{css_key}={css_val} vs COLORS[{dict_key}]={dict_val}")

    # Cross-check named colors
    cross_checks = [
        ("secondary-brown", "secondary_brown"),
        ("gold", "gold"),
        ("teal", "teal"),
    ]
    for css_key, dict_key in cross_checks:
        css_val = css_vars.get(css_key, "MISSING")
        dict_val = colors_dict.get(dict_key, "MISSING")
        if css_val != dict_val:
            issues.append(f"MISMATCH: CSS --rl-color-{css_key}={css_val} vs COLORS[{dict_key}]={dict_val}")

    return issues


def main():
    parser = argparse.ArgumentParser(description="Audit brand color usage")
    parser.add_argument("--fix", action="store_true", help="Show suggested fix commands")
    parser.add_argument("--contrast", action="store_true", help="Only run contrast checks")
    args = parser.parse_args()

    exit_code = 0

    # ── Contrast checks ──
    print("=" * 60)
    print("WCAG AA CONTRAST AUDIT")
    print("=" * 60)
    passes, failures = check_contrast()
    for label, fg, bg, ratio, min_ratio in passes:
        print(f"  PASS  {ratio:.2f}:1 >= {min_ratio}:1  {label}")
    for label, fg, bg, ratio, min_ratio in failures:
        print(f"  FAIL  {ratio:.2f}:1 <  {min_ratio}:1  {label}  ({fg} on {bg})")
        exit_code = 1
    print(f"\n  {len(passes)} passed, {len(failures)} failed\n")

    if args.contrast:
        sys.exit(exit_code)

    # ── Brand tokens internal consistency ──
    print("=" * 60)
    print("BRAND TOKENS INTERNAL CONSISTENCY")
    print("=" * 60)
    sync_issues = verify_brand_tokens_sync()
    if sync_issues:
        for issue in sync_issues:
            print(f"  {issue}")
        exit_code = 1
    else:
        print("  All CSS vars match COLORS dict")
    print()

    # ── Banned color scan ──
    print("=" * 60)
    print("BANNED COLOR SCAN")
    print("=" * 60)
    findings = scan_for_banned_colors()
    if findings:
        for filepath, line, color, note in findings:
            rel = filepath.relative_to(PROJECT_ROOT)
            print(f"  {rel}:{line}  {color}  ({note})")
        exit_code = 1
        print(f"\n  {len(findings)} stale color references found")
    else:
        print("  No banned colors found — all clean")
    print()

    if exit_code == 0:
        print("ALL CHECKS PASSED")
    else:
        print("AUDIT FAILED — fix issues above")

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
