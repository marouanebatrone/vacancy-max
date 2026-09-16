"""The only bridge between the ORM and the solver.

Loads a year, runs the pure domain optimizer, and enriches the result with the
holiday names and confirmation flags the UI needs. Views call this and nothing
else; the domain package stays unaware that any of it exists.
"""

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass

from apps.calendars.services import get_year_calendar, next_planning_year
from apps.optimizer.domain.solver import solve
from apps.optimizer.domain.strategies import Strategy
from apps.optimizer.domain.types import Break, Calendar, DayType

#: Guard rail on the solver's O(workdays x budget^2) shape. Moroccan law grants
#: 18 working days a year, more with seniority; nobody has sixty, and refusing
#: the absurd keeps a stray request from pinning a worker thread.
MAX_BUDGET = 60


@dataclass(frozen=True, slots=True)
class HolidayRef:
    """A holiday a break is built around."""

    date: dt.date
    name: str
    is_confirmed: bool


@dataclass(frozen=True, slots=True)
class BreakView:
    """One break, ready to render."""

    start: dt.date
    end: dt.date
    total_days: int
    cost: int
    efficiency: float
    leave_days: tuple[dt.date, ...]
    holidays: tuple[HolidayRef, ...]
    has_estimated_holidays: bool


@dataclass(frozen=True, slots=True)
class PlanSummary:
    """The headline numbers, computed once so the UI never has to."""

    total_days_off: int
    leave_used: int
    leave_unused: int
    efficiency: float
    break_count: int
    longest_break: int
    has_estimated_holidays: bool


@dataclass(frozen=True, slots=True)
class PlanView:
    year: int
    budget: int
    strategy: str
    summary: PlanSummary
    breaks: tuple[BreakView, ...]


def build_plan(
    days: int,
    year: int | None = None,
    strategy: Strategy = Strategy.MAX_DAYS_OFF,
) -> PlanView:
    """Plan ``days`` of leave for ``year``.

    ``year`` defaults to the one the user most likely wants, because the product
    asks for a single number and derives everything else (see ADR 0002).
    """
    calendar = get_year_calendar(year if year is not None else next_planning_year())
    plan = solve(calendar, budget=days, strategy=strategy)

    breaks = tuple(_describe(calendar, brk) for brk in plan.breaks)
    return PlanView(
        year=plan.year,
        budget=plan.budget,
        strategy=str(plan.strategy),
        summary=PlanSummary(
            total_days_off=plan.total_days_off,
            leave_used=plan.leave_used,
            leave_unused=plan.leave_unused,
            efficiency=round(plan.efficiency, 2),
            break_count=len(breaks),
            longest_break=max((b.total_days for b in breaks), default=0),
            has_estimated_holidays=any(b.has_estimated_holidays for b in breaks),
        ),
        breaks=breaks,
    )


def _describe(calendar: Calendar, brk: Break) -> BreakView:
    """Attach the holidays a break covers, so the UI can name and caveat them."""
    span = calendar.days[calendar.index_of(brk.start) : calendar.index_of(brk.end) + 1]
    holidays = tuple(
        HolidayRef(date=day.date, name=day.holiday_name or "", is_confirmed=not day.is_estimated)
        for day in span
        if day.type is DayType.HOLIDAY
    )
    return BreakView(
        start=brk.start,
        end=brk.end,
        total_days=brk.total_days,
        cost=brk.cost,
        efficiency=round(brk.efficiency, 2),
        leave_days=brk.leave_days,
        holidays=holidays,
        has_estimated_holidays=any(not h.is_confirmed for h in holidays),
    )
