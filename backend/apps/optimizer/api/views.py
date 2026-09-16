"""Thin HTTP layer over the optimizer service."""

from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.calendars.services import UnsupportedYearError
from apps.optimizer import services
from apps.optimizer.domain.strategies import Strategy

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
