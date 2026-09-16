"""The plan endpoint's contract.

The request is one field. Everything else the optimizer needs -- the year, the
weekend rule, the Moroccan holiday set -- is the backend's knowledge, and
`year` is accepted only so tooling can ask for a specific one. The UI must not
put it on screen (ADR 0002).
"""

from rest_framework import serializers

from apps.calendars.services import supported_years
from apps.optimizer.domain.strategies import Strategy
from apps.optimizer.services import MAX_BUDGET


class PlanRequestSerializer(serializers.Serializer[object]):
    days = serializers.IntegerField(
        min_value=0,
        max_value=MAX_BUDGET,
        help_text="Paid leave days the company grants. The only thing the user is asked.",
    )
    year = serializers.ChoiceField(
        choices=supported_years(),
        required=False,
        help_text="Optional. Defaults to the year the user most likely wants to plan.",
    )
    strategy = serializers.ChoiceField(
        choices=[strategy.value for strategy in Strategy],
        required=False,
        default=Strategy.MAX_DAYS_OFF.value,
        help_text="What 'best' means: most total days off, or one longest break.",
    )


class HolidayRefSerializer(serializers.Serializer[object]):
    date = serializers.DateField(read_only=True)
    name = serializers.CharField(read_only=True)
    is_confirmed = serializers.BooleanField(read_only=True)


class BreakSerializer(serializers.Serializer[object]):
    start = serializers.DateField(read_only=True)
    end = serializers.DateField(read_only=True)
    total_days = serializers.IntegerField(read_only=True)
    cost = serializers.IntegerField(read_only=True)
    efficiency = serializers.FloatField(read_only=True)
    leave_days = serializers.ListField(child=serializers.DateField(), read_only=True)
    holidays = HolidayRefSerializer(many=True, read_only=True)
    has_estimated_holidays = serializers.BooleanField(read_only=True)


class PlanSummarySerializer(serializers.Serializer[object]):
    total_days_off = serializers.IntegerField(read_only=True)
    leave_used = serializers.IntegerField(read_only=True)
    leave_unused = serializers.IntegerField(read_only=True)
    efficiency = serializers.FloatField(read_only=True)
    break_count = serializers.IntegerField(read_only=True)
    longest_break = serializers.IntegerField(read_only=True)
    has_estimated_holidays = serializers.BooleanField(read_only=True)


class PlanSerializer(serializers.Serializer[object]):
    year = serializers.IntegerField(read_only=True)
    budget = serializers.IntegerField(read_only=True)
    strategy = serializers.CharField(read_only=True)
    summary = PlanSummarySerializer(read_only=True)
    breaks = BreakSerializer(many=True, read_only=True)
