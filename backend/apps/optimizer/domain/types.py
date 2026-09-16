"""The vocabulary of the domain.

Pure data. No Django, no I/O, no clock. Everything here is frozen: a Calendar
that could be mutated halfway through the solver is a bug waiting to happen.
"""

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass
from enum import StrEnum
from itertools import pairwise

#: ``date.weekday()`` values that are not working days in Morocco.
WEEKEND_SAT_SUN: frozenset[int] = frozenset({5, 6})


class DayType(StrEnum):
    """What a single calendar day costs.

    Only WORKDAY consumes leave; the other two are already free.
    """

    WORKDAY = "workday"
    WEEKEND = "weekend"
    HOLIDAY = "holiday"


@dataclass(frozen=True, slots=True)
class Day:
    """One day of the year, already classified."""

    date: dt.date
    type: DayType
    holiday_name: str | None = None
    #: True when this is a Hijri holiday whose date is not officially confirmed.
    is_estimated: bool = False

    @property
    def is_free(self) -> bool:
        """Free means 'off without spending leave'."""
        return self.type is not DayType.WORKDAY

    @property
    def is_workday(self) -> bool:
        return self.type is DayType.WORKDAY


@dataclass(frozen=True, slots=True)
class Calendar:
    """Every day of one year, in order, with no gaps.

    The contiguity guarantee is what lets the solver treat the year as an array
    and index into it by ordinal arithmetic instead of searching.
    """

    year: int
    days: tuple[Day, ...]

    def __post_init__(self) -> None:
        expected = (dt.date(self.year, 12, 31) - dt.date(self.year, 1, 1)).days + 1
        if len(self.days) != expected:
            raise ValueError(f"{self.year} needs {expected} days, got {len(self.days)}")
        if self.days[0].date != dt.date(self.year, 1, 1):
            raise ValueError("Calendar must start on January 1st")
        for previous, current in pairwise(self.days):
            if current.date - previous.date != dt.timedelta(days=1):
                raise ValueError(f"Gap in calendar between {previous.date} and {current.date}")

    def __len__(self) -> int:
        return len(self.days)

    def index_of(self, day: dt.date) -> int:
        """Position of ``day`` in :attr:`days`. O(1): no scanning."""
        if day.year != self.year:
            raise ValueError(f"{day} is outside calendar year {self.year}")
        return (day - dt.date(self.year, 1, 1)).days

    def day_at(self, day: dt.date) -> Day:
        return self.days[self.index_of(day)]

    @property
    def workdays(self) -> tuple[Day, ...]:
        return tuple(day for day in self.days if day.is_workday)

    @property
    def holidays(self) -> tuple[Day, ...]:
        return tuple(day for day in self.days if day.type is DayType.HOLIDAY)

    @property
    def has_estimated_holidays(self) -> bool:
        return any(day.is_estimated for day in self.days)
