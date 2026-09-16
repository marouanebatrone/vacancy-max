"""Every break worth considering, with what it costs and what it buys.

The enumeration rests on one observation. A break is a run of consecutive days
off, so the workdays inside it must *all* be taken as leave -- skip one and the
run splits in two. A candidate break is therefore exactly a consecutive slice of
the year's workdays, and the search space is slices, not arbitrary day subsets:
O(workdays x budget) of them, a few thousand for a year. Small enough to
enumerate exhaustively, which is why the solver can be exact.
"""

from __future__ import annotations

from dataclasses import dataclass

from .types import Calendar, DayType


@dataclass(frozen=True, slots=True)
class Candidate:
    """A possible break, addressed by the workdays it consumes.

    Indices are positions in the *workday* array, not the day array: they are
    what the solver reasons about. ``start``/``end`` are day-array indices for
    the resulting stretch off, already expanded over the adjacent free days.
    """

    first_workday: int
    last_workday: int
    start: int
    end: int

    @property
    def cost(self) -> int:
        """Leave days consumed."""
        return self.last_workday - self.first_workday + 1

    @property
    def value(self) -> int:
        """Calendar days off, including the free days at both edges."""
        return self.end - self.start + 1

    @property
    def gain(self) -> int:
        """Days bought beyond the leave spent. This is the whole point."""
        return self.value - self.cost


def workday_indices(calendar: Calendar) -> tuple[int, ...]:
    """Positions of every workday in the calendar, in order."""
    return tuple(i for i, day in enumerate(calendar.days) if day.is_workday)


def holiday_prefix(calendar: Calendar) -> tuple[int, ...]:
    """Running count of public holidays, for O(1) "does this span one?" checks."""
    counts = [0]
    for day in calendar.days:
        counts.append(counts[-1] + (1 if day.type is DayType.HOLIDAY else 0))
    return tuple(counts)


def enumerate_candidates(
    calendar: Calendar,
    budget: int,
    *,
    require_gain: bool = True,
    require_holiday: bool = True,
) -> tuple[Candidate, ...]:
    """All breaks costing at most ``budget`` leave days.

    Each candidate expands outward across the free days on either side, because
    taking the Friday before a weekend buys the weekend too.

    ``require_gain`` drops candidates that return exactly what they cost -- a
    lone Wednesday in a holiday-free week is a day off, but not a *vacation*.

    ``require_holiday`` keeps only breaks that actually contain a public
    holiday, and it is what makes the output a holiday plan rather than a list
    of long weekends. Without it the true optimum is degenerate: a lone Friday
    buys three days for one, the same ratio as most real bridges, and a year has
    far more Fridays than holidays -- so maximizing days off alone spends the
    whole budget on scattered three-day weekends and bridges nothing. Leave that
    buys no bridge is reported as ``leave_unused`` instead, and stays the user's
    to take whenever they like.
    """
    if budget <= 0:
        return ()

    holidays = holiday_prefix(calendar)
    workdays = workday_indices(calendar)
    total_workdays = len(workdays)
    last_day = len(calendar) - 1

    candidates: list[Candidate] = []
    for first in range(total_workdays):
        for last in range(first, min(total_workdays, first + budget)):
            # Expand over the free days flanking the slice: everything from the
            # day after the previous untaken workday to the day before the next.
            start = workdays[first - 1] + 1 if first > 0 else 0
            end = workdays[last + 1] - 1 if last + 1 < total_workdays else last_day

            candidate = Candidate(first_workday=first, last_workday=last, start=start, end=end)
            if require_gain and candidate.gain <= 0:
                continue
            if require_holiday and holidays[end + 1] == holidays[start]:
                continue
            candidates.append(candidate)

    return tuple(candidates)
