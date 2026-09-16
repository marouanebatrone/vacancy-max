"""The pure calendar layer. No database, no Django -- these run in milliseconds."""

import datetime as dt

import pytest
from hypothesis import given
from hypothesis import strategies as st

from apps.optimizer.domain.calendar import build_calendar, iter_year
from apps.optimizer.domain.types import Calendar, Day, DayType


class TestBuildCalendar:
    def test_classifies_weekday_as_workday(self) -> None:
        calendar = build_calendar(2026, holidays={})
        # 2026-01-02 is a Friday.
        assert calendar.day_at(dt.date(2026, 1, 2)).type is DayType.WORKDAY

    def test_classifies_saturday_and_sunday_as_weekend(self) -> None:
        calendar = build_calendar(2026, holidays={})
        assert calendar.day_at(dt.date(2026, 1, 3)).type is DayType.WEEKEND  # Saturday
        assert calendar.day_at(dt.date(2026, 1, 4)).type is DayType.WEEKEND  # Sunday

    def test_holiday_on_a_weekday_is_a_holiday(self) -> None:
        # 2026-05-01 (Labour Day) is a Friday.
        calendar = build_calendar(2026, {dt.date(2026, 5, 1): ("Labour Day", False)})
        day = calendar.day_at(dt.date(2026, 5, 1))
        assert day.type is DayType.HOLIDAY
        assert day.holiday_name == "Labour Day"
        assert day.is_free

    def test_holiday_on_a_weekend_stays_a_weekend_but_keeps_its_name(self) -> None:
        """Morocco grants no day in lieu. The optimizer must not pretend otherwise."""
        # 2026-08-14 is a Friday; 2026-08-15 is a Saturday.
        calendar = build_calendar(2026, {dt.date(2026, 8, 15): ("Some Holiday", False)})
        day = calendar.day_at(dt.date(2026, 8, 15))
        assert day.type is DayType.WEEKEND
        assert day.holiday_name == "Some Holiday"  # so the UI can show what was lost

    def test_estimated_flag_survives_only_for_observed_holidays(self) -> None:
        calendar = build_calendar(
            2026,
            {
                dt.date(2026, 3, 20): ("Eid al-Fitr", True),  # Friday, observed
                dt.date(2026, 3, 21): ("Eid al-Fitr", True),  # Saturday, lost
            },
        )
        assert calendar.day_at(dt.date(2026, 3, 20)).is_estimated is True
        assert calendar.day_at(dt.date(2026, 3, 21)).is_estimated is False
        assert calendar.has_estimated_holidays is True


class TestCalendarInvariants:
    def test_build_calendar_always_covers_the_whole_year(self) -> None:
        """Covering the year is build_calendar's promise. Calendar itself only
        guarantees contiguity, so the solver can run on short spans in tests."""
        assert build_calendar(2026, holidays={}).is_full_year is True

    def test_rejects_empty(self) -> None:
        with pytest.raises(ValueError, match="no days"):
            Calendar(year=2026, days=())

    def test_rejects_days_from_another_year(self) -> None:
        with pytest.raises(ValueError, match="must all fall in 2026"):
            Calendar(year=2026, days=(Day(dt.date(2025, 1, 1), DayType.WORKDAY),))

    def test_rejects_gaps(self) -> None:
        days = tuple(Day(d, DayType.WORKDAY) for d in iter_year(2026) if d != dt.date(2026, 6, 15))
        with pytest.raises(ValueError, match="Gap in calendar"):
            Calendar(year=2026, days=days)

    def test_index_of_rejects_foreign_year(self) -> None:
        calendar = build_calendar(2026, holidays={})
        with pytest.raises(ValueError, match="outside calendar year"):
            calendar.index_of(dt.date(2027, 1, 1))


@given(year=st.integers(min_value=1950, max_value=2100))
def test_calendar_covers_exactly_the_year(year: int) -> None:
    calendar = build_calendar(year, holidays={})
    expected = (dt.date(year, 12, 31) - dt.date(year, 1, 1)).days + 1

    assert len(calendar) == expected
    assert calendar.days[0].date == dt.date(year, 1, 1)
    assert calendar.days[-1].date == dt.date(year, 12, 31)


@given(year=st.integers(min_value=1950, max_value=2100))
def test_every_day_has_exactly_one_type(year: int) -> None:
    calendar = build_calendar(year, holidays={})
    by_type = dict.fromkeys(DayType, 0)
    for day in calendar.days:
        by_type[day.type] += 1

    assert sum(by_type.values()) == len(calendar)
    # A year always has 52 or 53 of each weekend day.
    assert 104 <= by_type[DayType.WEEKEND] <= 106


@given(
    year=st.integers(min_value=2000, max_value=2100),
    offset=st.integers(min_value=0, max_value=364),
)
def test_index_of_and_day_at_round_trip(year: int, offset: int) -> None:
    calendar = build_calendar(year, holidays={})
    day = dt.date(year, 1, 1) + dt.timedelta(days=offset)

    assert calendar.index_of(day) == offset
    assert calendar.day_at(day).date == day
