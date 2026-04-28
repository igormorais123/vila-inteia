"""Time-decay feature for forecasting.

Events further in the future are harder to predict.
Weight predictions toward a prior based on recency.

Formula:
    weight = exp(-age_days / half_life * ln(2))
    p_decayed = weight * p + (1 - weight) * prior

So a fresh event (age=0) keeps p verbatim; an event at age=half_life
gets shrunk halfway toward the prior; very old/distant events collapse
to the prior.
"""

from __future__ import annotations

import math
from datetime import date, datetime


DEFAULT_REFERENCE_DATE = "2026-04-28"
DEFAULT_HALF_LIFE = 180
DEFAULT_PRIOR = 0.5


def _parse_date(s: str) -> date:
    """Parse YYYY-MM-DD into a date object."""
    return datetime.strptime(s.strip(), "%Y-%m-%d").date()


def event_age_days(event_date: str,
                   reference_date: str = DEFAULT_REFERENCE_DATE) -> int:
    """Absolute distance in days between event_date and reference_date.

    Returns absolute value: future events and past events are equally
    "far" from the reference for the purpose of decaying confidence.
    """
    ed = _parse_date(event_date)
    rd = _parse_date(reference_date)
    return abs((ed - rd).days)


def time_decay_weight(age_days: int, half_life: int = DEFAULT_HALF_LIFE) -> float:
    """exp(-age_days / half_life * ln(2)). Returns weight in (0, 1].

    age=0     -> 1.0
    age=half  -> 0.5
    age=2*half -> 0.25
    """
    if half_life <= 0:
        raise ValueError("half_life must be positive")
    if age_days < 0:
        age_days = -age_days
    return math.exp(-age_days / half_life * math.log(2.0))


def apply_time_decay(p: float, age_days: int,
                     prior: float = DEFAULT_PRIOR,
                     half_life: int = DEFAULT_HALF_LIFE) -> float:
    """Shrink p toward prior with weight = 1 - time_decay_weight.

    Distant events shrink more. Returns value in [0, 1].

    p_out = w * p + (1 - w) * prior
        where w = time_decay_weight(age_days, half_life)
    """
    w = time_decay_weight(age_days, half_life=half_life)
    out = w * p + (1.0 - w) * prior
    if out < 0.0:
        return 0.0
    if out > 1.0:
        return 1.0
    return out
