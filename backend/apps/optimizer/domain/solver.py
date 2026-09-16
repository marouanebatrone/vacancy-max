"""The optimizer. Exact, deterministic, and framework-free.

Given a year and a leave budget, choose which workdays to request so the total
time off is maximal. This is solved exactly -- no greedy pass, no heuristic.

The shape of the problem is weighted interval scheduling crossed with a
knapsack. Candidates are consecutive slices of the workday array (see
candidates.py); two chosen slices must be separated by at least one *untaken*
workday, because two slices that touch are a single longer slice already in the
candidate set. So the state is:

    dp[a][k] = the best achievable from workday a onward with k leave days left

with two moves from each state: leave workday ``a`` untaken and move to
``a + 1``, or take a candidate starting at ``a`` and jump past its end plus the
one workday that must separate it from whatever comes next.

Complexity is O(workdays x budget x budget) -- roughly 80k operations for a year
and a typical budget, i.e. under a millisecond.
"""

from __future__ import annotations

import datetime as dt
from collections import defaultdict

from .candidates import Candidate, enumerate_candidates, workday_indices
from .strategies import Strategy, score
from .types import Break, Calendar, Plan

#: dp cells hold (total score, leave days left over). Comparing the tuple gives
#: the tie-break for free: among equally good plans, prefer the one that spends
#: less leave. Getting 44 days off for 16 days beats getting them for 18.
type Cell = tuple[float, int]


def solve(
    calendar: Calendar,
    budget: int,
    strategy: Strategy = Strategy.MAX_DAYS_OFF,
    *,
    require_holiday: bool = True,
) -> Plan:
    """Build the optimal leave plan for ``calendar`` under ``budget``.

    ``require_holiday`` (the default) restricts the plan to breaks built around
    public holidays, which is the product: bridging. Turning it off maximizes
    raw days off and degenerates into scattered long weekends -- a useful
    baseline in tests, not advice to give anyone.
    """
    if budget < 0:
        raise ValueError(f"Leave budget cannot be negative: {budget}")

    workdays = workday_indices(calendar)
    total = len(workdays)
    candidates = enumerate_candidates(calendar, budget, require_holiday=require_holiday)

    by_start: defaultdict[int, list[Candidate]] = defaultdict(list)
    for candidate in candidates:
        by_start[candidate.first_workday].append(candidate)

    # dp[a][k], with two rows of padding so that jumping past the final
    # candidate never needs a bounds check.
    dp: list[list[Cell]] = [[(0.0, k) for k in range(budget + 1)] for _ in range(total + 2)]
    chosen: list[list[Candidate | None]] = [[None] * (budget + 1) for _ in range(total + 2)]

    for a in range(total - 1, -1, -1):
        for k in range(budget + 1):
            best = dp[a + 1][k]  # move: do not take workday a
            pick: Candidate | None = None

            for candidate in by_start[a]:
                if candidate.cost > k:
                    continue
                # +2: skip the break's own workdays and the one that must
                # separate it from the next break.
                resume = min(candidate.last_workday + 2, total)
                after = dp[resume][k - candidate.cost]
                value = (after[0] + score(candidate, strategy), after[1])
                if value > best:
                    best, pick = value, candidate

            dp[a][k] = best
            chosen[a][k] = pick

    return Plan(
        year=calendar.year,
        budget=budget,
        breaks=_reconstruct(calendar, workdays, chosen, budget, total),
        strategy=strategy,
    )


def _reconstruct(
    calendar: Calendar,
    workdays: tuple[int, ...],
    chosen: list[list[Candidate | None]],
    budget: int,
    total: int,
) -> tuple[Break, ...]:
    """Walk the decision table back into the breaks it represents."""
    breaks: list[Break] = []
    a, k = 0, budget

    while a < total:
        candidate = chosen[a][k]
        if candidate is None:
            a += 1
            continue

        breaks.append(_to_break(calendar, workdays, candidate))
        k -= candidate.cost
        a = candidate.last_workday + 2

    return tuple(breaks)


def _to_break(calendar: Calendar, workdays: tuple[int, ...], candidate: Candidate) -> Break:
    """Translate workday indices back into the dates a human will request."""
    leave_days: tuple[dt.date, ...] = tuple(
        calendar.days[workdays[i]].date
        for i in range(candidate.first_workday, candidate.last_workday + 1)
    )
    return Break(
        start=calendar.days[candidate.start].date,
        end=calendar.days[candidate.end].date,
        leave_days=leave_days,
    )
