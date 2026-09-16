"""The ORM-to-domain bridge."""

import datetime as dt

import pytest
from django.core.management import call_command

from apps.calendars import services
from apps.calendars.models import Holiday
from apps.optimizer.domain.types import DayType

pytestmark = pytest.mark.django_db


@pytest.fixture
def seeded() -> None:
    call_command("seed_holidays")


def test_builds_a_full_year(seeded: None) -> None:
    calendar = services.get_year_calendar(2026)

    assert len(calendar) == 365
    assert calendar.year == 2026


def test_labour_day_2026_is_observed(seeded: None) -> None:
    """2026-05-01 is a Friday: a real day off, and a bridge candidate."""
    calendar = services.get_year_calendar(2026)
    day = calendar.day_at(dt.date(2026, 5, 1))

    assert day.type is DayType.HOLIDAY
    assert day.holiday_name == "Labour Day"


def test_unsupported_year_is_refused(seeded: None) -> None:
    with pytest.raises(services.UnsupportedYearError, match="No holiday data for 2030"):
        services.get_year_calendar(2030)


def test_unseeded_year_is_refused_rather_than_silently_empty() -> None:
    """An empty holiday table must not yield a plausible-looking holiday-free year."""
    with pytest.raises(services.UnsupportedYearError, match="seed_holidays"):
        services.get_year_calendar(2026)


def test_stats_account_for_every_day(seeded: None) -> None:
    stats = services.summarize(services.get_year_calendar(2026))

    assert stats.total_days == 365
    assert stats.workdays + stats.weekend_days + stats.holidays_observed == 365
    assert stats.has_estimated_holidays is True


def test_holidays_lost_to_weekend_are_counted(seeded: None) -> None:
    """Stats count DAYS, so they must reconcile against distinct holiday dates,
    not holiday records: 2027 has two holidays sharing August 14th."""
    for year in (2026, 2027):
        stats = services.summarize(services.get_year_calendar(year))
        distinct_dates = Holiday.objects.filter(year=year).values("date").distinct().count()

        assert stats.holidays_observed + stats.holidays_lost_to_weekend == distinct_dates
        assert stats.holidays_lost_to_weekend > 0


def test_two_holidays_on_one_date_count_as_one_day(seeded: None) -> None:
    """2027-08-14 is both Oued Ed-Dahab and Aid Al Mawlid. One day, both names."""
    calendar = services.get_year_calendar(2027)
    day = calendar.day_at(dt.date(2027, 8, 14))

    assert day.holiday_name is not None
    assert " / " in day.holiday_name
    assert "Oued Ed-Dahab" in day.holiday_name
    assert "Mawlid" in day.holiday_name


def test_overview_marks_lost_holidays_as_not_observed(seeded: None) -> None:
    overview = services.get_year_overview(2026)
    lost = [h for h in overview.holidays if not h.is_observed]

    assert lost, "2026 should lose at least one holiday to the weekend"
    for holiday in lost:
        assert holiday.weekday in {"Saturday", "Sunday"}


def test_next_planning_year_stays_in_supported_range() -> None:
    assert services.next_planning_year(dt.date(2025, 6, 1)) == 2026
    assert services.next_planning_year(dt.date(2026, 6, 1)) == 2026
    assert services.next_planning_year(dt.date(2027, 6, 1)) == 2027
    assert services.next_planning_year(dt.date(2030, 6, 1)) == 2027
