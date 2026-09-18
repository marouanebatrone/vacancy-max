"""The .ics export.

Calendar clients are unforgiving about this format, so the tests check the
mechanics -- CRLF, exclusive DTEND, octet-safe folding, TEXT escaping -- not
just that a file comes back.
"""

from __future__ import annotations

import datetime as dt

import pytest
from django.core.management import call_command
from rest_framework.test import APIClient

pytestmark = pytest.mark.django_db

URL = "/api/v1/optimizer/plan.ics"


def _without_timestamps(body: bytes) -> list[str]:
    """Two renders of the same plan differ only in DTSTAMP."""
    return [line for line in body.decode("utf-8").splitlines() if not line.startswith("DTSTAMP")]


@pytest.fixture
def seeded() -> None:
    call_command("seed_holidays")


@pytest.fixture
def ics(api_client: APIClient, seeded: None) -> str:
    response = api_client.get(URL, {"days": 18})
    assert response.status_code == 200
    body: bytes = response.content
    return body.decode("utf-8")


class TestDelivery:
    def test_served_as_a_calendar_download(self, api_client: APIClient, seeded: None) -> None:
        response = api_client.get(URL, {"days": 18})

        assert response.status_code == 200
        assert response["Content-Type"] == "text/calendar; charset=utf-8"
        assert response["Content-Disposition"] == 'attachment; filename="vacancy-max-2026.ics"'

    def test_the_link_alone_reproduces_a_plan(self, api_client: APIClient, seeded: None) -> None:
        """A plan is a pure function of its query string: that is what makes the
        URL shareable without any storage behind it."""
        first = api_client.get(URL, {"days": 12, "year": 2027}).content
        second = api_client.get(URL, {"days": 12, "year": 2027}).content

        assert _without_timestamps(first) == _without_timestamps(second)

    def test_validation_matches_the_json_endpoint(
        self, api_client: APIClient, seeded: None
    ) -> None:
        assert api_client.get(URL).status_code == 400
        assert api_client.get(URL, {"days": 900}).status_code == 400
        assert api_client.get(URL, {"days": 18, "year": 2030}).status_code == 400


class TestFormat:
    def test_is_a_well_formed_calendar(self, ics: str) -> None:
        assert ics.startswith("BEGIN:VCALENDAR\r\n")
        assert ics.endswith("END:VCALENDAR\r\n")
        assert "VERSION:2.0" in ics
        assert "PRODID:-//Vacancy Max//Moroccan leave planner//EN" in ics

    def test_uses_crlf_everywhere(self, ics: str) -> None:
        """A lone LF makes strict clients reject the whole file."""
        assert "\n" in ics
        assert ics.replace("\r\n", "").count("\n") == 0

    def test_no_line_exceeds_75_octets(self, ics: str) -> None:
        for line in ics.split("\r\n"):
            assert len(line.encode("utf-8")) <= 75, line

    def test_one_event_per_break(self, api_client: APIClient, ics: str) -> None:
        plan = api_client.post("/api/v1/optimizer/plan/", {"days": 18}, format="json").json()

        assert ics.count("BEGIN:VEVENT") == len(plan["breaks"])
        assert ics.count("END:VEVENT") == len(plan["breaks"])

    def test_all_day_events_end_the_day_after(self, api_client: APIClient, ics: str) -> None:
        """DTEND is exclusive for DATE values. Off by one here and every
        holiday shows up a day short."""
        plan = api_client.post("/api/v1/optimizer/plan/", {"days": 18}, format="json").json()
        first = plan["breaks"][0]
        expected_end = dt.date.fromisoformat(first["end"]) + dt.timedelta(days=1)

        assert f"DTSTART;VALUE=DATE:{first['start'].replace('-', '')}" in ics
        assert f"DTEND;VALUE=DATE:{expected_end.strftime('%Y%m%d')}" in ics

    def test_every_event_carries_a_stable_unique_id(self, ics: str) -> None:
        uids = [line for line in ics.split("\r\n") if line.startswith("UID:")]

        assert uids
        assert len(set(uids)) == len(uids)

    def test_commas_in_holiday_names_are_escaped(self, ics: str) -> None:
        """An unescaped comma silently splits a TEXT value in two."""
        for line in ics.split("\r\n"):
            if line.startswith(("SUMMARY:", "DESCRIPTION:")):
                bare_commas = [
                    index
                    for index, char in enumerate(line)
                    if char == "," and (index == 0 or line[index - 1] != "\\")
                ]
                assert bare_commas == [], line


class TestContent:
    def test_tells_you_which_days_to_request(self, ics: str, api_client: APIClient) -> None:
        plan = api_client.post("/api/v1/optimizer/plan/", {"days": 18}, format="json").json()
        unfolded = ics.replace("\r\n ", "")

        for day in plan["breaks"][0]["leave_days"]:
            pretty = dt.date.fromisoformat(day).strftime("%a %d %b %Y")
            assert pretty in unfolded

    def test_warns_when_a_break_rests_on_an_unconfirmed_date(self, ics: str) -> None:
        assert "moon sighting" in ics.replace("\r\n ", "")

    def test_names_the_holidays_in_the_summary(self, ics: str) -> None:
        assert "days off" in ics.replace("\r\n ", "")
        assert "Throne Day" in ics.replace("\r\n ", "")

    def test_empty_plan_is_still_a_valid_calendar(
        self, api_client: APIClient, seeded: None
    ) -> None:
        body = api_client.get(URL, {"days": 0}).content.decode()

        assert body.startswith("BEGIN:VCALENDAR\r\n")
        assert body.endswith("END:VCALENDAR\r\n")
        assert "BEGIN:VEVENT" not in body
