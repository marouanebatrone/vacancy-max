"""The feedback contract.

The table stores the verdict as two booleans; the API takes one required
choice. Mapping at the boundary means (True, True) and (False, False) are
simply unrepresentable rather than merely discouraged.
"""

from rest_framework import serializers

from apps.feedback.services import DOWN, UP

MAX_COMMENT = 2000


class FeedbackRequestSerializer(serializers.Serializer[object]):
    rating = serializers.ChoiceField(
        choices=[UP, DOWN],
        help_text="Thumbs up or down. The only required answer.",
    )
    comment = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=MAX_COMMENT,
        help_text="Optional: what would you change, or what's missing?",
    )


class FeedbackSerializer(serializers.Serializer[object]):
    id = serializers.UUIDField(read_only=True)
