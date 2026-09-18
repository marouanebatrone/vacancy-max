"""Thin HTTP layer over the optimizer service."""

from django.http import HttpResponse
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.calendars.services import UnsupportedYearError
from apps.optimizer import services
from apps.optimizer.domain.strategies import Strategy
from apps.optimizer.ics import render_calendar

from .serializers import PlanRequestSerializer, PlanSerializer


class PlanView(APIView):
    """Turn a number of leave days into a year's worth of holidays."""

    @extend_schema(
        operation_id="createPlan",
        request=PlanRequestSerializer,
        responses=PlanSerializer,
        summary="Plan leave around the public holidays",
        tags=["optimizer"],
    )
    def post(self, request: Request) -> Response:
        form = PlanRequestSerializer(data=request.data)
        form.is_valid(raise_exception=True)
        data = form.validated_data

        try:
            plan = services.build_plan(
                days=data["days"],
                year=data.get("year"),
                strategy=Strategy(data["strategy"]),
            )
        except UnsupportedYearError as exc:
            return Response(
                {"error": {"code": "unsupported_year", "message": str(exc), "details": {}}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(PlanSerializer(plan).data)


class PlanCalendarView(APIView):
    """The same plan as a .ics file, ready to import into any calendar.

    A GET with query parameters rather than a POST, because a download has to
    be reachable from a plain link -- and because that link is itself the
    shareable, re-openable form of a plan.
    """

    @extend_schema(
        operation_id="downloadPlanCalendar",
        parameters=[
            OpenApiParameter("days", OpenApiTypes.INT, required=True),
            OpenApiParameter("year", OpenApiTypes.INT),
            OpenApiParameter("strategy", OpenApiTypes.STR),
        ],
        responses={(200, "text/calendar"): OpenApiTypes.BINARY},
        summary="Download the plan as a calendar file",
        tags=["optimizer"],
    )
    def get(self, request: Request) -> HttpResponse:
        form = PlanRequestSerializer(data=request.query_params)
        form.is_valid(raise_exception=True)
        data = form.validated_data

        try:
            plan = services.build_plan(
                days=data["days"],
                year=data.get("year"),
                strategy=Strategy(data["strategy"]),
            )
        except UnsupportedYearError as exc:
            return Response(
                {"error": {"code": "unsupported_year", "message": str(exc), "details": {}}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        response = HttpResponse(
            render_calendar(plan),
            content_type="text/calendar; charset=utf-8",
        )
        response["Content-Disposition"] = f'attachment; filename="vacancy-max-{plan.year}.ics"'
        return response
