"""Persistence for holiday knowledge.

The YAML file is the source of truth; these rows are its queryable projection.
Re-seeding is therefore always safe and always wins.
"""

from __future__ import annotations

from typing import Any

from django.db import models

from apps.common.models import TimeStampedModel


class HolidayKind(models.TextChoices):
    FIXED = "fixed", "Fixed Gregorian"
    HIJRI = "hijri", "Hijri (lunar)"


class Holiday(TimeStampedModel):
    """One public holiday on one concrete date.

    A multi-day celebration is stored as one row per day (``eid-al-fitr-1``,
    ``eid-al-fitr-2``) so that the optimizer never has to expand anything: every
    row is exactly one day off.
    """

    #: Stable identity within a year. Survives a date correction, which is the
    #: whole point: re-seeding a corrected Hijri date updates the row in place
    #: instead of leaving the stale date behind.
    slug = models.SlugField(max_length=64)
    year = models.PositiveSmallIntegerField(
        editable=False,
        db_index=True,
        help_text="Derived from date on save. Denormalized so lookups stay trivial.",
    )
    date = models.DateField(db_index=True)

    name = models.CharField(max_length=120)
    name_fr = models.CharField(max_length=120, blank=True)
    name_ar = models.CharField(max_length=120, blank=True)

    kind = models.CharField(max_length=8, choices=HolidayKind)

    is_confirmed = models.BooleanField(
        default=True,
        help_text="False while a lunar date is only an astronomical estimate.",
    )
    uncertainty_days = models.PositiveSmallIntegerField(
        default=0,
        help_text="How far the real date may fall from this one, in days.",
    )

    class Meta:
        ordering = ["date"]
        constraints = [
            models.UniqueConstraint(fields=["year", "slug"], name="unique_holiday_per_year"),
        ]
        indexes = [models.Index(fields=["year", "date"])]

    def __str__(self) -> str:
        return f"{self.date.isoformat()} — {self.name}"

    def save(self, *args: Any, **kwargs: Any) -> None:
        self.year = self.date.year
        super().save(*args, **kwargs)

    @property
    def is_estimated(self) -> bool:
        return not self.is_confirmed
