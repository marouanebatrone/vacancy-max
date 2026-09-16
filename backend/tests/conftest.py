"""Shared fixtures.

Tests under tests/domain/ must not touch the database; that is the point of the
pure domain layer. Only integration/ and api/ use the `db` fixture.
"""

import pytest
from rest_framework.test import APIClient


@pytest.fixture
def api_client() -> APIClient:
    return APIClient()
