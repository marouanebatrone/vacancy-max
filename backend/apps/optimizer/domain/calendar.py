"""Turn a set of holidays into a fully classified year.

Pure function of its arguments -- the same inputs always produce the same
Calendar, which is what makes the optimizer reproducible and testable.
"""

from __future__ import annotations

import datetime as dt
from collections.abc import Iterable, Mapping

from .types import WEEKEND_SAT_SUN, Calendar, Day, DayType


def iter_year(year: int) -> Iterable[dt.date]:
    """Every date in ``year``, January 1st through December 31st."""
    day = dt.date(year, 1, 1)
    end = dt.date(year, 12, 31)
    while day <= end:
        yield day
        day += dt.timedelta(days=1)


def build_calendar(
    year: int,
    holidays: Mapping[dt.date, tuple[str, bool]],
    weekend: frozenset[int] = WEEKEND_SAT_SUN,
) -> Calendar:
    """Classify every day of ``year``.

    Args:
        year: the Gregorian year to build.
        holidays: date -> (display name, is_estimated).
        weekend: ``date.weekday()`` values that are not working days.

    Weekend wins over holiday on purpose. Morocco grants no day in lieu when a
    public holiday falls on a Saturday or Sunday, so counting such a day as a
    HOLIDAY would let the optimizer believe it had bought a free day it never
    got. The holiday's name is still attached, so the UI can show the user
    exactly which holidays their year lost to the weekend.
    """
    days: list[Day] = []
    for day in iter_year(year):
        holiday = holidays.get(day)
        if day.weekday() in weekend:
            day_type = DayType.WEEKEND
        elif holiday is not None:
            day_type = DayType.HOLIDAY
        else:
            day_type = DayType.WORKDAY

        name, is_estimated = holiday if holiday is not None else (None, False)
        days.append(
            Day(
                date=day,
                type=day_type,
                holiday_name=name,
                is_estimated=is_estimated and day_type is DayType.HOLIDAY,
            )
        )
    return Calendar(year=year, days=tuple(days))
