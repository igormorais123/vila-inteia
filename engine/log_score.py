"""Logarithmic scoring rule (Good 1952).

Strictly proper: minimized in expectation iff p == true probability.
log_score = -1/n * sum [y log p + (1-y) log(1-p)]  (lower is better)
"""

from __future__ import annotations

import math
from typing import Iterable


def log_score(
    preds: Iterable[float],
    reals: Iterable[int],
    eps: float = 1e-9,
) -> float:
    """Mean negative log-likelihood. Returns 0.0 on empty input."""
    p = [float(x) for x in preds]
    y = [int(x) for x in reals]
    n = len(p)
    if n == 0 or len(y) != n:
        return 0.0
    s = 0.0
    for pi, yi in zip(p, y):
        pc = min(max(pi, eps), 1 - eps)
        s += -(yi * math.log(pc) + (1 - yi) * math.log(1 - pc))
    return s / n


def log_score_skill(
    preds: Iterable[float],
    reals: Iterable[int],
    baseline_rate: float | None = None,
    eps: float = 1e-9,
) -> float:
    """Skill score vs constant climatology forecast.

    skill = 1 - log_score(model) / log_score(baseline_rate)
    1 = perfect; 0 = climatology; negative = worse.
    """
    p = [float(x) for x in preds]
    y = [int(x) for x in reals]
    n = len(p)
    if n == 0 or len(y) != n:
        return 0.0
    base = sum(y) / n if baseline_rate is None else float(baseline_rate)
    base = min(max(base, eps), 1 - eps)
    ls_model = log_score(p, y, eps=eps)
    ls_clim = -(base * math.log(base) + (1 - base) * math.log(1 - base))
    if ls_clim <= 1e-12:
        return 0.0 if ls_model <= 1e-12 else float("-inf")
    return 1.0 - ls_model / ls_clim
