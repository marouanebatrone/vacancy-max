"""Candidate enumeration: the search space the solver is exact over.

Most tests here disable holiday anchoring to exercise the raw geometry of
break-finding; the anchoring rule gets its own section at the end.
"""

from apps.optimizer.domain.candidates import (
    Candidate,
    enumerate_candidates,
    workday_indices,
)

from .conftest import make_calendar


def unanchored(pattern: str, budget: int, **kwargs: bool) -> tuple[Candidate, ...]:
    return enumerate_candidates(make_calendar(pattern), budget, require_holiday=False, **kwargs)


class TestGeometry:
    def test_a_single_workday_between_free_days_buys_the_lot(self) -> None:
        #  . . W . .   -- one leave day, five days off
        candidates = unanchored("..W..", 5)

        assert len(candidates) == 1
        assert (candidates[0].cost, candidates[0].value, candidates[0].gain) == (1, 5, 4)

    def test_expands_across_free_days_on_both_sides(self) -> None:
        """`.WW.` offers three breaks: either workday alone (2 days off each, by
        absorbing the free day on its side) or both together (all four days)."""
        candidates = unanchored(".WW.", 2)

        assert sorted((c.cost, c.value) for c in candidates) == [(1, 2), (1, 2), (2, 4)]

    def test_budget_caps_candidate_cost(self) -> None:
        candidates = unanchored(".WWWW.", 2)

        assert candidates
        assert max(c.cost for c in candidates) == 2

    def test_zero_gain_candidates_are_dropped_by_default(self) -> None:
        """A lone workday in a workday-only stretch is a day off, but not a
        vacation: it returns exactly what it costs."""
        assert unanchored("WWWWW", 3) == ()

    def test_zero_gain_candidates_can_be_kept_explicitly(self) -> None:
        candidates = unanchored("WWWWW", 1, require_gain=False)

        assert len(candidates) == 5
        assert all(c.gain == 0 for c in candidates)

    def test_zero_budget_yields_nothing(self) -> None:
        assert unanchored(".W.", 0) == ()

    def test_candidates_are_consecutive_workday_slices(self) -> None:
        """Skipping a workday inside a break would split it in two, so every
        candidate must cover a contiguous run of workdays."""
        calendar = make_calendar(".W.WW.W.")
        workdays = workday_indices(calendar)

        for candidate in enumerate_candidates(calendar, budget=4, require_holiday=False):
            covered = workdays[candidate.first_workday : candidate.last_workday + 1]
            assert len(covered) == candidate.cost
            assert candidate.start <= covered[0] <= covered[-1] <= candidate.end


class TestHolidayAnchoring:
    def test_a_break_must_contain_a_holiday(self) -> None:
        #  . W H W .  -- both workdays bridge the holiday
        candidates = enumerate_candidates(make_calendar(".WHW."), budget=2)

        assert candidates
        assert all(c.start <= 2 <= c.end for c in candidates)

    def test_weekend_only_bridges_are_rejected(self) -> None:
        """A lone Friday buys a three-day weekend, but bridges no holiday, so it
        is not a plan this product should propose."""
        assert enumerate_candidates(make_calendar(".W."), budget=1) == ()
        assert enumerate_candidates(make_calendar(".W."), budget=1, require_holiday=False)

    def test_far_from_a_holiday_is_rejected_but_near_is_kept(self) -> None:
        #  H W W W W W W .  -- only slices reaching back to the holiday qualify
        candidates = enumerate_candidates(make_calendar("HWWWWWW."), budget=3)

        assert candidates
        assert all(c.start == 0 for c in candidates)
