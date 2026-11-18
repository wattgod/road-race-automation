"""The vitals-card date moves the leading year to the end only for a bare date.

A status line such as '2026: May 16-17 (completed). 2027 dates not yet
announced.' used to come out as '... not yet announced., 2026'.
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "wordpress"))

from generate_neo_brutalist import _short_date


@pytest.mark.parametrize(
    "raw, expected",
    [
        ("2026: June 6", "June 6, 2026"),
        ("2026: September 12-13", "September 12-13, 2026"),
        ("2027: Sunday, April 4", "Sunday, April 4, 2027"),
        ("2026: October 4 (Sunday)", "October 4, 2026 (Sunday)"),
        ("2026: July 11 (confirmed).", "July 11, 2026 (confirmed)"),
        # Anything more than one date clause stays as written.
        (
            "2026: May 16-17 (completed; 33rd edition). 2027 dates not yet announced.",
            "2026: May 16-17 (completed; 33rd edition). 2027 dates not yet announced.",
        ),
        ("2026: June 13. 2027 date not yet announced.", "2026: June 13. 2027 date not yet announced."),
        ("2026: DISCONTINUED", "2026: DISCONTINUED"),
        ("Last held: May 26, 2024", "Last held: May 26, 2024"),
        ("", ""),
        (None, ""),
    ],
)
def test_short_date(raw, expected):
    assert _short_date(raw) == expected


def test_short_date_never_ends_in_a_dangling_year():
    assert not _short_date("2026: Cancelled. No 2027 date announced.").endswith(", 2026")
