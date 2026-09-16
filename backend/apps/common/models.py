"""Abstract bases shared across apps."""

from django.db import models


class TimeStampedModel(models.Model):
    """Adds self-updating created/modified fields."""

    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    updated_at = models.DateTimeField(auto_now=True, editable=False)

    class Meta:
        abstract = True
