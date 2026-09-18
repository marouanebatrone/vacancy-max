"""What people tell us about the product.

The table is defined outside this project (Neon), so the model matches that
DDL exactly -- same table name, same four nullable columns, nothing added:

    CREATE TABLE "vacancy_feedbacks" (
      "id" uuid PRIMARY KEY,
      "thumbs_up" boolean,
      "thumbs_down" boolean,
      "comment" text,
      "created_at" timestamptz DEFAULT now()
    );
"""

from __future__ import annotations

import uuid

from django.db import models


class Feedback(models.Model):
    """One person's verdict, and optionally what they'd change.

    `thumbs_up` and `thumbs_down` are two columns describing one choice, so
    only (True, False) and (False, True) are meaningful. The API takes a single
    required rating and derives the pair, which keeps the other two
    combinations unreachable rather than merely discouraged.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    thumbs_up = models.BooleanField(null=True)
    thumbs_down = models.BooleanField(null=True)
    # null=True on a text field is usually a smell -- two empty states. Here it
    # matches the column as defined in Neon, and the schema is the authority.
    comment = models.TextField(null=True, blank=True)  # noqa: DJ001
    # Django supplies this on insert; the column's own DEFAULT now() stays as a
    # safety net for any row written outside the app.
    created_at = models.DateTimeField(auto_now_add=True, editable=False)

    class Meta:
        db_table = "vacancy_feedbacks"
        verbose_name_plural = "feedback"
        ordering = ["-created_at"]  # newest first: what people just said matters most

    def __str__(self) -> str:
        verdict = "👍" if self.thumbs_up else "👎"
        return f"{verdict} {(self.comment or '')[:40]}".strip()

    @property
    def is_positive(self) -> bool:
        return bool(self.thumbs_up)
