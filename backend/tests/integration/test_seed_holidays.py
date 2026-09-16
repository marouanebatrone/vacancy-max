"""The seeder must be safe to run on every deploy, forever."""

import datetime as dt

import pytest
from django.core.management import call_command

from apps.calendars.models import Holiday, HolidayKind

pytestmark = pytest.mark.django_db


def test_seeds_both_supported_years() -> None:
    call_command("seed_holidays")

    assert Holiday.objects.filter(year=2026).count() == 17
    assert Holiday.objects.filter(year=2027).count() == 17


def test_is_idempotent() -> None:
    call_command("seed_holidays")
    first = set(Holiday.objects.values_list("year", "slug", "date"))

    call_command("seed_holidays")

    assert Holiday.objects.count() == 34
    assert set(Holiday.objects.values_list("year", "slug", "date")) == first


def test_corrected_lunar_date_updates_in_place() -> None:
    """When Morocco announces the real Eid date, re-seeding must move the row,
    not leave a duplicate on the stale date."""
    call_command("seed_holidays")
    eid = Holiday.objects.get(year=2026, slug="eid-al-fitr-1")

    eid.date = eid.date + dt.timedelta(days=1)  # simulate a drifted local edit
    eid.is_confirmed = True
    eid.save()

    call_command("seed_holidays", "--years", "2026")

    refreshed = Holiday.objects.get(year=2026, slug="eid-al-fitr-1")
    assert refreshed.date == dt.date(2026, 3, 20)  # back to the YAML value
    assert refreshed.is_confirmed is False
    assert Holiday.objects.filter(year=2026, slug="eid-al-fitr-1").count() == 1


def test_lunar_holidays_are_marked_unconfirmed() -> None:
    call_command("seed_holidays")

    hijri = Holiday.objects.filter(kind=HolidayKind.HIJRI)
    assert hijri.count() == 14
    assert not hijri.filter(is_confirmed=True).exists()
    assert not hijri.filter(uncertainty_days=0).exists()


def test_fixed_holidays_are_confirmed_and_exact() -> None:
    call_command("seed_holidays")

    fixed = Holiday.objects.filter(kind=HolidayKind.FIXED)
    assert fixed.count() == 20  # 10 per year
    assert not fixed.filter(is_confirmed=False).exists()
    assert not fixed.filter(uncertainty_days__gt=0).exists()


def test_year_is_derived_from_date() -> None:
    call_command("seed_holidays")

    for holiday in Holiday.objects.all():
        assert holiday.year == holiday.date.year
