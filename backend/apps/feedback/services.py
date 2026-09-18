"""Recording feedback. Thin, but it keeps the rating-to-columns mapping in one
place rather than spread between a serializer and a view."""

from __future__ import annotations

from .models import Feedback

UP = "up"
DOWN = "down"


def record(rating: str, comment: str = "") -> Feedback:
    """Store one verdict. `rating` is 'up' or 'down'; comment may be empty."""
    if rating not in {UP, DOWN}:
        raise ValueError(f"Unknown rating: {rating!r}")

    return Feedback.objects.create(
        thumbs_up=rating == UP,
        thumbs_down=rating == DOWN,
        comment=comment.strip() or None,
    )
