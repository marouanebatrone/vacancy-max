"""Receiving feedback. One POST, open to anyone, rate-limited."""

from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView

from apps.feedback import services

from .serializers import FeedbackRequestSerializer, FeedbackSerializer


class FeedbackView(APIView):
    """Record one person's verdict on the product.

    Unauthenticated by design -- asking someone to sign in before they can say
    "this was useful" would collect nothing. That makes it a public write, so
    it is throttled per client.
    """

    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "feedback"

    @extend_schema(
        operation_id="submitFeedback",
        request=FeedbackRequestSerializer,
        responses={201: FeedbackSerializer},
        summary="Send feedback about the planner",
        tags=["feedback"],
    )
    def post(self, request: Request) -> Response:
        form = FeedbackRequestSerializer(data=request.data)
        form.is_valid(raise_exception=True)

        feedback = services.record(
            rating=form.validated_data["rating"],
            comment=form.validated_data.get("comment", ""),
        )
        return Response(
            FeedbackSerializer(feedback).data,
            status=status.HTTP_201_CREATED,
        )
