"""HTTP contract for the calendar endpoints."""

import pytest
from django.core.management import call_command
from rest_framework.test import APIClient

pytestmark = pytest.mark.django_db


@pytest.fixture
def seeded() -> None:
    call_command("seed_holidays")


def test_supported_years(api_client: APIClient, seeded: None) -> None:
    response = api_client.get("/api/v1/calendars/years/")

    assert response.status_code == 200
    assert response.json()["years"] == [2026, 2027]
    assert response.json()["default_year"] in (2026, 2027)


def test_year_overview(api_client: APIClient, seeded: None) -> None:
    response = api_client.get("/api/v1/calendars/years/2026/")
    body = response.json()

    assert response.status_code == 200
    assert body["year"] == 2026
    assert body["weekend"] == ["saturday", "sunday"]
    assert len(body["holidays"]) == 17
    assert body["stats"]["total_days"] == 365
    assert body["stats"]["has_estimated_holidays"] is True


def test_year_overview_exposes_estimate_flags(api_client: APIClient, seeded: None) -> None:
    """A user must never be shown an estimated Eid as if it were certain."""
    body = api_client.get("/api/v1/calendars/years/2026/").json()
    eid = next(h for h in body["holidays"] if h["name"].startswith("Eid al-Fitr"))

    assert eid["is_confirmed"] is False
    assert eid["uncertainty_days"] == 1


def test_unsupported_year_returns_404_envelope(api_client: APIClient, seeded: None) -> None:
    response = api_client.get("/api/v1/calendars/years/2030/")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "unsupported_year"


def test_holidays_are_ordered_by_date(api_client: APIClient, seeded: None) -> None:
    dates = [h["date"] for h in api_client.get("/api/v1/calendars/years/2026/").json()["holidays"]]

    assert dates == sorted(dates)


def test_openapi_schema_is_generatable(api_client: APIClient) -> None:
    """If this breaks, the frontend's generated types break with it."""
    response = api_client.get("/api/schema/")

    assert response.status_code == 200
