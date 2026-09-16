"""What "best" means.

The solver maximizes a sum of per-break scores. Changing the objective is
changing this function -- the dynamic program itself never changes, and stays
exact for whichever scoring is chosen.
"""

from __future__ import annotations

from enum import StrEnum

from .candidates import Candidate


class Strategy(StrEnum):
    #: Maximize total calendar days off across the year. The default, and what
    #: most people mean by "get the most out of my leave".
    MAX_DAYS_OFF = "max_days_off"

    #: Favour one long holiday over several short ones. Scoring by the square of
    #: the length is convex, so concentrating days always beats spreading them:
    #: a single 10-day break scores 100 where two 5-day breaks score 50.
    LONGEST_BREAK = "longest_break"


def score(candidate: Candidate, strategy: Strategy) -> float:
    match strategy:
        case Strategy.MAX_DAYS_OFF:
            return float(candidate.value)
        case Strategy.LONGEST_BREAK:
            return float(candidate.value) ** 2
