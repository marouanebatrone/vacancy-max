"""Thin HTTP layer. Every view here does three things and no more:
parse, delegate to services, serialize.
"""

from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.calendars import services

from .serializers import SupportedYearsSerializer, YearOverviewSerializer


class SupportedYearsView(APIView):
    """Which years can be planned, and which one to show by default."""

    @extend_schema(
        operation_id="listSupportedYears",
        responses=SupportedYearsSerializer,
        summary="List plannable years",
        tags=["calendars"],
    )
    def get(self, request: Request) -> Response:
        payload = {
            "years": services.supported_years(),
            "default_year": services.next_planning_year(),
        }
        return Response(SupportedYearsSerializer(payload).data)


class YearOverviewView(APIView):
    """Holidays and headline stats for one year."""

    @extend_schema(
        operation_id="getYearOverview",
        responses=YearOverviewSerializer,
        summary="Get a year's holiday calendar",
        tags=["calendars"],
    )
    def get(self, request: Request, year: int) -> Response:
        try:
            overview = services.get_year_overview(year)
        except services.UnsupportedYearError as exc:
            return Response(
                {"error": {"code": "unsupported_year", "message": str(exc), "details": {}}},
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response(YearOverviewSerializer(overview).data)
