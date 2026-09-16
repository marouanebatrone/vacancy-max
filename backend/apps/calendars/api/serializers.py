"""Read-only serializers over the service layer's dataclasses.

They describe the API contract and nothing else -- no queries, no logic. That
lives in services.py.
"""

from rest_framework import serializers


class HolidaySerializer(serializers.Serializer[object]):
    date = serializers.DateField(read_only=True)
    name = serializers.CharField(read_only=True)
    name_fr = serializers.CharField(read_only=True)
    name_ar = serializers.CharField(read_only=True)
    kind = serializers.CharField(read_only=True)
    weekday = serializers.CharField(read_only=True)
    is_confirmed = serializers.BooleanField(read_only=True)
    uncertainty_days = serializers.IntegerField(read_only=True)
    is_observed = serializers.BooleanField(read_only=True)


class YearStatsSerializer(serializers.Serializer[object]):
    total_days = serializers.IntegerField(read_only=True)
    workdays = serializers.IntegerField(read_only=True)
    weekend_days = serializers.IntegerField(read_only=True)
    holidays_observed = serializers.IntegerField(read_only=True)
    holidays_lost_to_weekend = serializers.IntegerField(read_only=True)
    has_estimated_holidays = serializers.BooleanField(read_only=True)


class YearOverviewSerializer(serializers.Serializer[object]):
    year = serializers.IntegerField(read_only=True)
    weekend = serializers.ListField(child=serializers.CharField(), read_only=True)
    stats = YearStatsSerializer(read_only=True)
    holidays = HolidaySerializer(many=True, read_only=True)


class SupportedYearsSerializer(serializers.Serializer[object]):
    years = serializers.ListField(child=serializers.IntegerField(), read_only=True)
    default_year = serializers.IntegerField(read_only=True)
