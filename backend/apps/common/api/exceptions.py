"""A single, predictable error envelope for the whole API.

Every failure the frontend sees has the same shape:

    {"error": {"code": "validation_error", "message": "...", "details": {...}}}
"""

from typing import Any

from rest_framework.response import Response
from rest_framework.views import exception_handler as drf_exception_handler


def exception_handler(exc: Exception, context: dict[str, Any]) -> Response | None:
    response = drf_exception_handler(exc, context)
    if response is None:
        return None

    code = getattr(exc, "default_code", "error")
    detail = response.data
    message = detail if isinstance(detail, str) else "The request could not be processed."

    response.data = {
        "error": {
            "code": code,
            "message": message,
            "details": detail if not isinstance(detail, str) else {},
        }
    }
    return response
