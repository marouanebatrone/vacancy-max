"""The solver, checked three ways: by hand, by property, and against a
brute-force oracle that tries every possible combination.

The oracle is the one that matters. "Exact" is a strong claim, and the only
honest way to back it is to enumerate every subset of workdays on small
calendars and confirm the solver finds the true maximum every time.

Tests split along the anchoring rule. The `require_holiday=False` tests pin the
raw optimization: given a calendar, find the most days off. The anchored tests
pin the product: only propose breaks built around a public holiday.
"""

from __future__ import annotations

import datetime as dt
from itertools import combinations

from hypothesis import given, settings
from hypothesis import strategies as st

from apps.optimizer.domain.candidates import workday_indices
from apps.optimizer.domain.solver import solve
from apps.optimizer.domain.strategies import Strategy
from apps.optimizer.domain.types import Calendar, DayType, Plan

from .conftest import make_calendar


def solve_raw(pattern: str, budget: int) -> Plan:
    """Solve without holiday anchoring: the pure days-off optimum."""
    return solve(make_calendar(pattern), budget, require_holiday=False)


# --------------------------------------------------------------- brute force
def brute_force_best(calendar: Calendar, budget: int) -> int:
    """Maximum days off, found by trying every combination of leave days.

    Mirrors the solver's rule that a break must buy more than it costs: a
    configuration containing a zero-gain run is one the solver would never
    propose, so it is not eligible here either.
    """
    workdays = workday_indices(calendar)
    best = 0

    for size in range(budget + 1):
        for taken in combinations(workdays, size):
            total, eligible = _score_selection(calendar, set(taken))
            if eligible:
                best = max(best, total)

    return best


def _score_selection(calendar: Calendar, taken: set[int]) -> tuple[int, bool]:
    """Total days off for a set of leave days, and whether it is eligible."""
    if not taken:
        return 0, True

    free_or_taken = [day.is_free or i in taken for i, day in enumerate(calendar.days)]
    total = 0
    index = 0

    while index < len(free_or_taken):
        if not free_or_taken[index]:
            index += 1
            continue

        run_start = index
        while index < len(free_or_taken) and free_or_taken[index]:
            index += 1
        run = range(run_start, index)

        cost = sum(1 for i in run if i in taken)
        if cost:
            length = len(run)
            if length <= cost:  # a run that buys nothing: never proposed
                return 0, False
            total += length

    return total, True


# --------------------------------------------------------------- by hand
class TestHandChecked:
    def test_bridging_a_single_day(self) -> None:
        #  . . W . .  -- one day of leave, five days off
        plan = solve_raw("..W..", 1)

        assert plan.total_days_off == 5
        assert plan.leave_used == 1
        assert plan.efficiency == 5.0

    def test_prefers_the_bridge_over_a_plain_day(self) -> None:
        #  . W . W W W W  -- the lone W at index 1 bridges; the block does not
        plan = solve_raw(".W.WWWW", 1)

        assert plan.leave_days == (dt.date(2026, 1, 2),)
        assert plan.total_days_off == 3

    def test_spends_nothing_when_nothing_can_be_bought(self) -> None:
        plan = solve_raw("WWWWWWW", 5)

        assert plan.breaks == ()
        assert plan.leave_used == 0
        assert plan.leave_unused == 5

    def test_zero_budget_returns_an_empty_plan(self) -> None:
        plan = solve_raw("..W..", 0)

        assert plan.breaks == ()
        assert plan.total_days_off == 0

    def test_negative_budget_is_refused(self) -> None:
        import pytest

        with pytest.raises(ValueError, match="cannot be negative"):
            solve(make_calendar(".W."), -1)

    def test_two_separate_bridges_beat_one_long_break(self) -> None:
        #  . W . W W W W . W .  -- two 1-day bridges, 3 days off each
        plan = solve_raw(".W.WWWW.W.", 2)

        assert len(plan.breaks) == 2
        assert plan.total_days_off == 6

    def test_breaks_never_touch(self) -> None:
        """Two breaks that met would be one longer break, already a candidate."""
        plan = solve_raw(".W.W.W.W.", 4)

        for earlier, later in zip(plan.breaks, plan.breaks[1:], strict=False):
            assert earlier.end < later.start

    def test_longest_break_strategy_concentrates_leave(self) -> None:
        calendar = make_calendar(".HW..WH.")

        spread = solve(calendar, 2, strategy=Strategy.MAX_DAYS_OFF)
        concentrated = solve(calendar, 2, strategy=Strategy.LONGEST_BREAK)

        assert max(b.total_days for b in concentrated.breaks) >= max(
            b.total_days for b in spread.breaks
        )


# --------------------------------------------------------------- anchoring
class TestHolidayAnchoring:
    def test_only_proposes_breaks_around_holidays(self) -> None:
        """`. H W . . W .` with one day to spend: bridging off the holiday is
        eligible, the lone workday at the far end is not."""
        plan = solve(make_calendar(".HW..W."), 1)

        assert len(plan.breaks) == 1
        assert plan.breaks[0].leave_days == (dt.date(2026, 1, 3),)
        assert plan.breaks[0].start == dt.date(2026, 1, 1)

    def test_a_distant_workday_qualifies_once_the_break_reaches_the_holiday(self) -> None:
        """Anchoring is a property of the *break*, not of each day: with two
        days to spend, both workdays join one stretch that contains the
        holiday, so taking them is a real holiday, not a stray day off."""
        plan = solve(make_calendar(".HW..W."), 2)

        assert len(plan.breaks) == 1
        assert plan.breaks[0].total_days == 7
        assert plan.breaks[0].leave_days == (dt.date(2026, 1, 3), dt.date(2026, 1, 6))

    def test_a_year_without_holidays_yields_nothing(self) -> None:
        """We would rather return an empty plan than spend leave on nothing."""
        plan = solve(make_calendar(".WWWWW." * 4), 10)

        assert plan.breaks == ()
        assert plan.leave_unused == 10

    def test_unanchored_would_have_spent_that_budget(self) -> None:
        """The same calendar, unanchored, does find long weekends -- which is
        exactly the degenerate advice anchoring exists to prevent."""
        plan = solve(make_calendar(".WWWWW." * 4), 10, require_holiday=False)

        assert plan.breaks


@given(
    pattern=st.text(alphabet=".WH", min_size=1, max_size=40),
    budget=st.integers(min_value=0, max_value=10),
)
def test_anchored_breaks_always_contain_a_holiday(pattern: str, budget: int) -> None:
    calendar = make_calendar(pattern)

    plan = solve(calendar, budget)

    for brk in plan.breaks:
        span = calendar.days[calendar.index_of(brk.start) : calendar.index_of(brk.end) + 1]
        assert any(day.type is DayType.HOLIDAY for day in span)


# --------------------------------------------------------------- oracle
@settings(max_examples=250, deadline=None)
@given(
    pattern=st.text(alphabet=".W", min_size=1, max_size=14),
    budget=st.integers(min_value=0, max_value=4),
)
def test_matches_brute_force(pattern: str, budget: int) -> None:
    """The solver must find the true optimum, not merely a good answer."""
    calendar = make_calendar(pattern)

    plan = solve(calendar, budget, require_holiday=False)

    assert plan.total_days_off == brute_force_best(calendar, budget)


# --------------------------------------------------------------- invariants
PATTERNS = st.text(alphabet=".WH", min_size=1, max_size=40)
BUDGETS = st.integers(min_value=0, max_value=10)


@given(pattern=PATTERNS, budget=BUDGETS)
def test_never_exceeds_the_budget(pattern: str, budget: int) -> None:
    plan = solve(make_calendar(pattern), budget)

    assert plan.leave_used <= budget
    assert plan.leave_unused >= 0


@given(pattern=PATTERNS, budget=BUDGETS)
def test_every_leave_day_is_a_workday(pattern: str, budget: int) -> None:
    """Requesting leave on a Sunday would be absurd -- and would silently
    inflate the day count."""
    calendar = make_calendar(pattern)

    plan = solve(calendar, budget)

    for day in plan.leave_days:
        assert calendar.day_at(day).is_workday


@given(pattern=PATTERNS, budget=BUDGETS)
def test_breaks_are_ordered_and_disjoint(pattern: str, budget: int) -> None:
    plan = solve(make_calendar(pattern), budget)

    for earlier, later in zip(plan.breaks, plan.breaks[1:], strict=False):
        assert earlier.end < later.start


@given(pattern=PATTERNS, budget=BUDGETS)
def test_every_break_is_worth_taking(pattern: str, budget: int) -> None:
    plan = solve(make_calendar(pattern), budget)

    for brk in plan.breaks:
        assert brk.efficiency > 1.0


@settings(max_examples=100, deadline=None)
@given(
    pattern=st.text(alphabet=".WH", min_size=1, max_size=30),
    budget=st.integers(min_value=0, max_value=8),
)
def test_more_leave_is_never_worse(pattern: str, budget: int) -> None:
    """Monotonicity: an extra day of leave can never reduce the time off."""
    calendar = make_calendar(pattern)

    assert solve(calendar, budget + 1).total_days_off >= solve(calendar, budget).total_days_off


@given(pattern=PATTERNS, budget=BUDGETS)
def test_plan_is_deterministic(pattern: str, budget: int) -> None:
    calendar = make_calendar(pattern)

    assert solve(calendar, budget) == solve(calendar, budget)
