"""The solver against the real Moroccan calendar.

Assertions are deliberately structural rather than exact totals: the Hijri
dates are estimates, and correcting one when Morocco announces it must not
turn this suite red. What must hold is that every plan is a *holiday* plan,
stays inside budget, and is worth taking.
"""

from __future__ import annotations

import time

import pytest
from django.core.management import call_command

from apps.calendars.services import get_year_calendar, supported_years
from apps.optimizer.domain.solver import solve
from apps.optimizer.domain.types import DayType

pytestmark = pytest.mark.django_db


@pytest.fixture
def seeded() -> None:
    call_command("seed_holidays")


@pytest.mark.parametrize("year", supported_years())
def test_a_typical_budget_more_than_doubles_the_time_off(seeded: None, year: int) -> None:
    plan = solve(get_year_calendar(year), budget=18)

    assert plan.leave_used <= 18
    assert plan.total_days_off >= 40
    assert plan.efficiency >= 2.0


@pytest.mark.parametrize("year", supported_years())
def test_every_break_is_built_around_a_public_holiday(seeded: None, year: int) -> None:
    calendar = get_year_calendar(year)

    plan = solve(calendar, budget=18)

    assert plan.breaks
    for brk in plan.breaks:
        span = calendar.days[calendar.index_of(brk.start) : calendar.index_of(brk.end) + 1]
        assert any(day.type is DayType.HOLIDAY for day in span), f"{brk.start} bridges nothing"


def test_leave_days_are_never_weekends_or_holidays(seeded: None) -> None:
    """Requesting a day already free would waste it -- the one mistake a user
    would never forgive."""
    calendar = get_year_calendar(2026)

    plan = solve(calendar, budget=18)

    for day in plan.leave_days:
        assert calendar.day_at(day).type is DayType.WORKDAY


def test_small_budgets_buy_the_best_bridges_first(seeded: None) -> None:
    """With five days, every suggestion should be a high-efficiency bridge."""
    plan = solve(get_year_calendar(2026), budget=5)

    assert plan.leave_used <= 5
    assert plan.efficiency >= 3.0


def test_more_leave_never_reduces_time_off(seeded: None) -> None:
    calendar = get_year_calendar(2026)

    results = [solve(calendar, budget=n).total_days_off for n in range(0, 26)]

    assert results == sorted(results)
    assert results[0] == 0


def test_solves_a_full_year_fast(seeded: None) -> None:
    """A user waits on this synchronously; it must stay far below a second."""
    calendar = get_year_calendar(2026)

    start = time.perf_counter()
    solve(calendar, budget=30)
    elapsed = time.perf_counter() - start

    assert elapsed < 0.5, f"solver took {elapsed:.3f}s"


def test_plans_are_stable_across_runs(seeded: None) -> None:
    calendar = get_year_calendar(2026)

    assert solve(calendar, budget=18) == solve(calendar, budget=18)
