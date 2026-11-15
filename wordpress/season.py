"""Season year shared by Roadie Labs generators (RL-14).

Riders plan, search and register for next year's races from autumn, so from
``ROLLOVER_MONTH`` (September, same rule as Gravel God's ``season.py``) the
season a rider reads as "this season" is next year. Use ``season_year()`` for
page titles, hero copy and calendar URLs that mean the coming season.
Copyright lines and dates stamped on reports keep ``date.today().year``.

This module only names the season. It never projects a race's next edition
date: a race without a published date for a season has no date for it.
"""

from __future__ import annotations

from datetime import date

ROLLOVER_MONTH = 9


def season_year(today: date | None = None) -> int:
    """The rider-facing season for ``today`` (defaults to the build date)."""
    today = today or date.today()
    return today.year + 1 if today.month >= ROLLOVER_MONTH else today.year
