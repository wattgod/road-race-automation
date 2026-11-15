"""Every var(--rl-*) a generator or web asset uses must be defined (RL-11).

An undefined custom property fails silently: the declaration becomes invalid
at computed-value time, so colours and borders inherit or vanish and the
page stops rendering as designed. A token counts as defined when
brand_tokens.get_tokens_css() declares it, or when the same file declares it
locally (`--rl-foo: ...`).
"""

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "wordpress"))

from brand_tokens import get_tokens_css  # noqa: E402

_DEF_RE = re.compile(r"(--rl-[\w-]+)\s*:")
_USE_RE = re.compile(r"var\(\s*(--rl-[\w-]+)")


def _scanned_files():
    files = set(ROOT.glob("wordpress/**/*.py"))
    files |= set(ROOT.glob("web/*.css"))
    files |= set(ROOT.glob("web/*.js"))
    return sorted(f for f in files if "output" not in f.relative_to(ROOT).parts)


def _undefined_uses():
    defined = set(_DEF_RE.findall(get_tokens_css()))
    problems = []
    for path in _scanned_files():
        text = path.read_text(encoding="utf-8", errors="replace")
        local = set(_DEF_RE.findall(text))
        for lineno, line in enumerate(text.splitlines(), 1):
            for token in _USE_RE.findall(line):
                if token not in defined and token not in local:
                    problems.append(f"{path.relative_to(ROOT)}:{lineno} {token}")
    return problems


def test_tokens_css_defines_core_palette():
    defined = set(_DEF_RE.findall(get_tokens_css()))
    for token in ("--rl-color-ink", "--rl-color-paper", "--rl-color-graphite"):
        assert token in defined


def test_scan_covers_generators():
    names = {p.name for p in _scanned_files()}
    assert "generate_neo_brutalist.py" in names
    assert "shared_footer.py" in names


def test_no_undefined_rl_tokens():
    problems = _undefined_uses()
    assert not problems, (
        "var(--rl-*) used but never defined in get_tokens_css() or locally:\n  "
        + "\n  ".join(problems)
    )
