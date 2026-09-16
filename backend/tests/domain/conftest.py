"""Helpers for building small, readable calendars.

A pattern string is far easier to reason about than 365 constructed days:

    "W.HW"  ->  workday, weekend, holiday, workday

The distinction between '.' and 'H' matters: both are free, but only 'H' anchors
a break, so a pattern with no 'H' has no eligible breaks at all under the
default holiday-anchored solve.

Calendar guarantees contiguity rather than a full year precisely so these can
exist, which is what makes brute-force verification of the solver possible.
"""

from __future__ import annotations

import datetime as dt

from apps.optimizer.domain.types import Calendar, Day, DayType

WORKDAY = "W"
WEEKEND = "."
HOLIDAY = "H"

_TYPES = {
    WORKDAY: DayType.WORKDAY,
    WEEKEND: DayType.WEEKEND,
    HOLIDAY: DayType.HOLIDAY,
}


def make_calendar(pattern: str, start: dt.date = dt.date(2026, 1, 1)) -> Calendar:
    """Build a calendar from 'W' (workday), '.' (weekend) and 'H' (holiday)."""
    days = tuple(
        Day(
            date=start + dt.timedelta(days=offset),
            type=_TYPES[symbol],
            holiday_name="Test Holiday" if symbol == HOLIDAY else None,
        )
        for offset, symbol in enumerate(pattern)
    )
    return Calendar(year=start.year, days=days)
