"""Collecting feedback.

The table keeps the verdict in two boolean columns; the API accepts one
choice. These tests pin that mapping, because the contradictory states the
columns allow must never actually be written.
"""

from __future__ import annotations

import datetime as dt
import uuid

import pytest
from rest_framework.test import APIClient

from apps.feedback.models import Feedback

pytestmark = pytest.mark.django_db

URL = "/api/v1/feedback/"


class TestSubmitting:
    def test_a_thumbs_up_is_enough(self, api_client: APIClient) -> None:
        """The comment is optional -- requiring it would cost us most replies."""
        response = api_client.post(URL, {"rating": "up"}, format="json")

        assert response.status_code == 201
        assert uuid.UUID(response.json()["id"])

        feedback = Feedback.objects.get()
        assert feedback.thumbs_up is True
        assert feedback.thumbs_down is False
        assert feedback.comment is None

    def test_a_thumbs_down_sets_the_other_column(self, api_client: APIClient) -> None:
        api_client.post(URL, {"rating": "down"}, format="json")

        feedback = Feedback.objects.get()
        assert feedback.thumbs_up is False
        assert feedback.thumbs_down is True

    def test_a_comment_is_kept(self, api_client: APIClient) -> None:
        api_client.post(
            URL,
            {"rating": "down", "comment": "Add 2028, and French please"},
            format="json",
        )

        assert Feedback.objects.get().comment == "Add 2028, and French please"

    def test_a_blank_comment_is_stored_as_null_not_empty_string(
        self, api_client: APIClient
    ) -> None:
        """Two empty states would make 'did they write anything?' ambiguous."""
        api_client.post(URL, {"rating": "up", "comment": "   "}, format="json")

        assert Feedback.objects.get().comment is None

    def test_each_row_is_timestamped(self, api_client: APIClient) -> None:
        """Without a time there is no way to see whether sentiment is moving."""
        before = dt.datetime.now(dt.UTC)

        api_client.post(URL, {"rating": "up"}, format="json")

        created = Feedback.objects.get().created_at
        assert before <= created <= dt.datetime.now(dt.UTC)

    def test_newest_feedback_comes_first(self, api_client: APIClient) -> None:
        api_client.post(URL, {"rating": "up", "comment": "first"}, format="json")
        api_client.post(URL, {"rating": "down", "comment": "second"}, format="json")

        assert [row.comment for row in Feedback.objects.all()] == ["second", "first"]

    def test_every_submission_is_its_own_row(self, api_client: APIClient) -> None:
        api_client.post(URL, {"rating": "up"}, format="json")
        api_client.post(URL, {"rating": "down"}, format="json")

        assert Feedback.objects.count() == 2
        assert len({str(row.id) for row in Feedback.objects.all()}) == 2

    def test_the_contradictory_states_are_never_written(self, api_client: APIClient) -> None:
        """The columns allow (True, True) and (False, False); the API cannot
        produce either, whatever it is sent."""
        for payload in [
            {"rating": "up"},
            {"rating": "down"},
            {"rating": "up", "comment": "x"},
        ]:
            api_client.post(URL, payload, format="json")

        for feedback in Feedback.objects.all():
            assert feedback.thumbs_up != feedback.thumbs_down


class TestValidation:
    def test_rating_is_required(self, api_client: APIClient) -> None:
        response = api_client.post(URL, {"comment": "nice"}, format="json")

        assert response.status_code == 400
        assert "rating" in response.json()["error"]["details"]
        assert not Feedback.objects.exists()

    @pytest.mark.parametrize("rating", ["maybe", "", "UP", True, 1])
    def test_only_up_or_down_is_accepted(self, api_client: APIClient, rating: object) -> None:
        response = api_client.post(URL, {"rating": rating}, format="json")

        assert response.status_code == 400
        assert not Feedback.objects.exists()

    def test_an_overlong_comment_is_refused(self, api_client: APIClient) -> None:
        response = api_client.post(URL, {"rating": "up", "comment": "x" * 2001}, format="json")

        assert response.status_code == 400
        assert not Feedback.objects.exists()

    def test_a_long_but_reasonable_comment_is_fine(self, api_client: APIClient) -> None:
        response = api_client.post(URL, {"rating": "up", "comment": "x" * 2000}, format="json")

        assert response.status_code == 201

    def test_reading_feedback_back_is_not_a_public_endpoint(self, api_client: APIClient) -> None:
        """People send this expecting it to be private, so there is no GET."""
        assert api_client.get(URL).status_code == 405
