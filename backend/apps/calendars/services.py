"""The bridge between stored holidays and the pure domain.

This is the only module allowed to hold both an ORM import and a domain import.
"""

from __future__ import annotations

import datetime as dt
from collections.abc import Iterable
from dataclasses import dataclass

from apps.optimizer.domain.calendar import build_calendar
from apps.optimizer.domain.types import Calendar, DayType

from .models import Holiday

#: Years we hold curated Hijri data for. Asking for anything else would silently
#: produce a calendar missing Eid, which is worse than an honest error.
FIRST_SUPPORTED_YEAR = 2026
LAST_SUPPORTED_YEAR = 2027


class UnsupportedYearError(ValueError):
    """Raised when no curated holiday data exists for the requested year."""


@dataclass(frozen=True, slots=True)
class YearStats:
    """Headline numbers about a year, before any optimization happens."""

    total_days: int
    workdays: int
    weekend_days: int
    #: Days -- not holiday records -- that are genuinely off work.
    holidays_observed: int
    #: Days carrying a holiday that Morocco does not give back, because they
    #: fall on a weekend. Two holidays on one such date count once.
    holidays_lost_to_weekend: int
    has_estimated_holidays: bool


def supported_years() -> list[int]:
    return list(range(FIRST_SUPPORTED_YEAR, LAST_SUPPORTED_YEAR + 1))


def get_year_calendar(year: int) -> Calendar:
    """Load ``year``'s holidays and classify every day of it."""
    if year not in supported_years():
        raise UnsupportedYearError(
            f"No holiday data for {year}. Supported years: {supported_years()}."
        )

    holidays = _holidays_by_date(Holiday.objects.filter(year=year))
    if not holidays:
        raise UnsupportedYearError(
            f"{year} has no holidays in the database. Run `manage.py seed_holidays`."
        )
    return build_calendar(year, holidays)


def _holidays_by_date(rows: Iterable[Holiday]) -> dict[dt.date, tuple[str, bool]]:
    """Collapse holiday rows onto the days they fall on.

    Two holidays can share one date -- in 2027 Oued Ed-Dahab and Aid Al Mawlid
    both land on August 14th. That is one day off, not two, so the calendar gets
    a single entry; the names are joined rather than one silently overwriting
    the other, and the day counts as estimated if either source is.
    """
    merged: dict[dt.date, tuple[str, bool]] = {}
    for row in rows:
        existing_name, existing_estimated = merged.get(row.date, ("", False))
        name = f"{existing_name} / {row.name}" if existing_name else row.name
        merged[row.date] = (name, existing_estimated or row.is_estimated)
    return merged


def summarize(calendar: Calendar) -> YearStats:
    """Count what the year looks like before any leave is spent."""
    observed = len(calendar.holidays)
    # A holiday on a Saturday or Sunday is classified WEEKEND but keeps its
    # name, so this counts exactly the days Morocco does not give back.
    lost = sum(1 for day in calendar.days if day.holiday_name and day.type is not DayType.HOLIDAY)
    return YearStats(
        total_days=len(calendar),
        workdays=len(calendar.workdays),
        weekend_days=sum(1 for day in calendar.days if day.type is DayType.WEEKEND),
        holidays_observed=observed,
        holidays_lost_to_weekend=lost,
        has_estimated_holidays=calendar.has_estimated_holidays,
    )


@dataclass(frozen=True, slots=True)
class HolidayView:
    """One holiday as the API presents it."""

    date: dt.date
    name: str
    name_fr: str
    name_ar: str
    kind: str
    is_confirmed: bool
    uncertainty_days: int
    weekday: str
    #: False when the holiday lands on a weekend and Morocco gives nothing back.
    is_observed: bool


@dataclass(frozen=True, slots=True)
class YearOverview:
    """Everything the frontend needs to render a year, before optimizing."""

    year: int
    weekend: tuple[str, ...]
    stats: YearStats
    holidays: tuple[HolidayView, ...]


def get_year_overview(year: int) -> YearOverview:
    """Holidays and headline stats for ``year``.

    Deliberately does not return all 365 days: weekends are derivable from the
    year alone, so shipping them would triple the payload to say nothing.
    """
    calendar = get_year_calendar(year)
    rows = Holiday.objects.filter(year=year)

    holidays = tuple(
        HolidayView(
            date=row.date,
            name=row.name,
            name_fr=row.name_fr,
            name_ar=row.name_ar,
            kind=row.kind,
            is_confirmed=row.is_confirmed,
            uncertainty_days=row.uncertainty_days,
            weekday=row.date.strftime("%A"),
            is_observed=calendar.day_at(row.date).type is DayType.HOLIDAY,
        )
        for row in rows
    )
    return YearOverview(
        year=year,
        weekend=("saturday", "sunday"),
        stats=summarize(calendar),
        holidays=holidays,
    )


def next_planning_year(today: dt.date | None = None) -> int:
    """The year a user most likely wants to plan.

    The current one until it runs out of usable runway, then the next.
    """
    today = today or dt.date.today()
    if today.year < FIRST_SUPPORTED_YEAR:
        return FIRST_SUPPORTED_YEAR
    if today.year in supported_years():
        return today.year
    return LAST_SUPPORTED_YEAR
