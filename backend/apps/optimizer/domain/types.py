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
        # Contiguity is the load-bearing invariant: it is what lets the solver
        # index by ordinal arithmetic instead of searching. Covering a whole
        # year is a guarantee of build_calendar, not of this type, so that the
        # solver can also be exercised on small spans.
        if not self.days:
            raise ValueError("Calendar has no days")
        if self.days[0].date.year != self.year or self.days[-1].date.year != self.year:
            raise ValueError(f"Calendar days must all fall in {self.year}")
        for previous, current in pairwise(self.days):
            if current.date - previous.date != dt.timedelta(days=1):
                raise ValueError(f"Gap in calendar between {previous.date} and {current.date}")

    @property
    def is_full_year(self) -> bool:
        return self.days[0].date == dt.date(self.year, 1, 1) and self.days[-1].date == dt.date(
            self.year, 12, 31
        )

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


@dataclass(frozen=True, slots=True)
class Break:
    """One continuous stretch away from work.

    ``start``/``end`` bound the whole stretch including the weekends and
    holidays at its edges; ``leave_days`` are only the workdays the employee
    actually has to request. That gap between the two is the product.
    """

    start: dt.date
    end: dt.date
    leave_days: tuple[dt.date, ...]

    def __post_init__(self) -> None:
        if self.end < self.start:
            raise ValueError(f"Break ends ({self.end}) before it starts ({self.start})")
        if not self.leave_days:
            raise ValueError("A break with no leave days is just a weekend")
        for day in self.leave_days:
            if not self.start <= day <= self.end:
                raise ValueError(f"Leave day {day} lies outside its break")

    @property
    def total_days(self) -> int:
        """Calendar days off, end to end."""
        return (self.end - self.start).days + 1

    @property
    def cost(self) -> int:
        """Leave days this break consumes."""
        return len(self.leave_days)

    @property
    def efficiency(self) -> float:
        """Days off bought per leave day spent. The number that sells the app."""
        return self.total_days / self.cost


@dataclass(frozen=True, slots=True)
class Plan:
    """The answer: which days to request, and what they buy."""

    year: int
    budget: int
    breaks: tuple[Break, ...]
    strategy: str

    def __post_init__(self) -> None:
        if self.leave_used > self.budget:
            raise ValueError(f"Plan spends {self.leave_used} days of a {self.budget} day budget")
        for earlier, later in pairwise(self.breaks):
            if earlier.end >= later.start:
                raise ValueError(f"Breaks overlap: {earlier.end} then {later.start}")

    @property
    def leave_used(self) -> int:
        return sum(brk.cost for brk in self.breaks)

    @property
    def leave_unused(self) -> int:
        """Days we deliberately did not spend, because nothing bought a gain."""
        return self.budget - self.leave_used

    @property
    def total_days_off(self) -> int:
        """Calendar days inside the breaks. Weekends already free elsewhere in
        the year are not counted -- this is the holiday, not the year."""
        return sum(brk.total_days for brk in self.breaks)

    @property
    def efficiency(self) -> float:
        if not self.leave_used:
            return 0.0
        return self.total_days_off / self.leave_used

    @property
    def leave_days(self) -> tuple[dt.date, ...]:
        """Every day to request, in order. The literal to-do list."""
        return tuple(day for brk in self.breaks for day in brk.leave_days)
