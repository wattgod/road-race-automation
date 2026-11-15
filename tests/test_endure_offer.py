"""The Endure footer offer must state Endure's real trial length.

endurelabs src/lib/billing/trial-policy.ts sets STANDARD_TRIAL_DAYS = 14
(since 2026-10-23); Gravel God's footer already says 14.
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "wordpress"))

from endure_offer import get_endure_offer_html

ENDURE_TRIAL_DAYS = 14


def test_endure_offer_states_14_day_trial():
    html = get_endure_offer_html()
    assert f"Try Endure for {ENDURE_TRIAL_DAYS} days" in html
    assert f"{ENDURE_TRIAL_DAYS} days free." in html
    other = {int(n) for n in re.findall(r"\b(\d+)[- ]days?\b", html)} - {ENDURE_TRIAL_DAYS}
    assert not other, f"Endure offer states another trial length: {sorted(other)}"
