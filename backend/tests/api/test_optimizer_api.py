"""HTTP contract for the plan endpoint -- the product's entire surface."""

from __future__ import annotations

from itertools import pairwise
from typing import Any

import pytest
from django.core.management import call_command
from rest_framework.test import APIClient

pytestmark = pytest.mark.django_db

URL = "/api/v1/optimizer/plan/"


@pytest.fixture
def seeded() -> None:
    call_command("seed_holidays")


def plan(api_client: APIClient, **payload: Any) -> dict[str, Any]:
    response = api_client.post(URL, payload, format="json")
    assert response.status_code == 200, response.json()
    body: dict[str, Any] = response.json()
    return body


class TestTheOneInput:
    def test_a_single_number_is_enough(self, api_client: APIClient, seeded: None) -> None:
        """The whole product: one field in, a year of holidays out."""
        body = plan(api_client, days=18)

        assert body["budget"] == 18
        assert body["year"] in (2026, 2027)
        assert body["summary"]["total_days_off"] > 40
        assert body["breaks"]

    def test_year_defaults_without_being_asked(self, api_client: APIClient, seeded: None) -> None:
        assert plan(api_client, days=10)["year"] == 2026

    def test_year_may_be_requested_explicitly(self, api_client: APIClient, seeded: None) -> None:
        assert plan(api_client, days=10, year=2027)["year"] == 2027


class TestPlanShape:
    def test_summary_is_internally_consistent(self, api_client: APIClient, seeded: None) -> None:
        body = plan(api_client, days=18)
        summary = body["summary"]

        assert summary["leave_used"] + summary["leave_unused"] == 18
        assert summary["break_count"] == len(body["breaks"])
        assert summary["total_days_off"] == sum(b["total_days"] for b in body["breaks"])
        assert summary["leave_used"] == sum(b["cost"] for b in body["breaks"])
        assert summary["longest_break"] == max(b["total_days"] for b in body["breaks"])

    def test_every_break_names_the_holidays_it_bridges(
        self, api_client: APIClient, seeded: None
    ) -> None:
        for brk in plan(api_client, days=18)["breaks"]:
            assert brk["holidays"], f"{brk['start']} bridges nothing"
            assert all(h["name"] for h in brk["holidays"])

    def test_leave_days_match_the_stated_cost(self, api_client: APIClient, seeded: None) -> None:
        for brk in plan(api_client, days=18)["breaks"]:
            assert len(brk["leave_days"]) == brk["cost"]
            assert brk["start"] <= min(brk["leave_days"])
            assert max(brk["leave_days"]) <= brk["end"]

    def test_estimated_holidays_are_flagged_on_the_break(
        self, api_client: APIClient, seeded: None
    ) -> None:
        """A break resting on an unconfirmed Eid must say so, or someone books
        a flight on the wrong week."""
        body = plan(api_client, days=18)
        estimated = [b for b in body["breaks"] if b["has_estimated_holidays"]]

        assert estimated, "2026 bridges several estimated lunar dates"
        assert body["summary"]["has_estimated_holidays"] is True
        for brk in estimated:
            assert any(not h["is_confirmed"] for h in brk["holidays"])

    def test_breaks_are_ordered_and_disjoint(self, api_client: APIClient, seeded: None) -> None:
        breaks = plan(api_client, days=18)["breaks"]

        for earlier, later in pairwise(breaks):
            assert earlier["end"] < later["start"]


class TestStrategies:
    def test_default_is_max_days_off(self, api_client: APIClient, seeded: None) -> None:
        assert plan(api_client, days=18)["strategy"] == "max_days_off"

    def test_longest_break_concentrates_leave(self, api_client: APIClient, seeded: None) -> None:
        spread = plan(api_client, days=18, strategy="max_days_off")
        concentrated = plan(api_client, days=18, strategy="longest_break")

        assert concentrated["summary"]["longest_break"] >= spread["summary"]["longest_break"]


class TestValidation:
    def test_days_is_required(self, api_client: APIClient, seeded: None) -> None:
        response = api_client.post(URL, {}, format="json")

        assert response.status_code == 400
        assert "days" in response.json()["error"]["details"]

    @pytest.mark.parametrize("days", [-1, 61, "many"])
    def test_absurd_budgets_are_refused(
        self, api_client: APIClient, seeded: None, days: object
    ) -> None:
        """The solver is O(workdays x budget^2); an unbounded budget is a way to
        pin a worker thread."""
        response = api_client.post(URL, {"days": days}, format="json")

        assert response.status_code == 400

    def test_zero_days_is_an_empty_plan_not_an_error(
        self, api_client: APIClient, seeded: None
    ) -> None:
        """Someone with no leave left deserves an answer, not a validation error."""
        body = plan(api_client, days=0)

        assert body["breaks"] == []
        assert body["summary"]["total_days_off"] == 0

    def test_unsupported_year_is_refused(self, api_client: APIClient, seeded: None) -> None:
        response = api_client.post(URL, {"days": 18, "year": 2030}, format="json")

        assert response.status_code == 400

    def test_unknown_strategy_is_refused(self, api_client: APIClient, seeded: None) -> None:
        response = api_client.post(URL, {"days": 18, "strategy": "vibes"}, format="json")

        assert response.status_code == 400

    def test_get_is_not_allowed(self, api_client: APIClient, seeded: None) -> None:
        assert api_client.get(URL).status_code == 405
