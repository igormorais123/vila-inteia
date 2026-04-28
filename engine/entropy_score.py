"""Entropy-based scoring for binary forecasts.

Predictive entropy: H(p) = -p log p - (1-p) log(1-p), in nats.
Conditional entropy and information gain quantify residual uncertainty
after observing outcomes.
"""

from __future__ import annotations

import math
from typing import Iterable


def _h_bin(p: float) -> float:
    """Binary entropy of a single prob, in nats."""
    if p <= 0.0 or p >= 1.0:
        return 0.0
    return -p * math.log(p) - (1.0 - p) * math.log(1.0 - p)


def predictive_entropy(preds: Iterable[float]) -> float:
    """Mean predictive entropy across forecasts."""
    p_list = [float(p) for p in preds]
    if not p_list:
        return 0.0
    return sum(_h_bin(p) for p in p_list) / len(p_list)


def conditional_entropy(
    preds: Iterable[float],
    reals: Iterable[int],
) -> float:
    """H(Y|P): mean cross-entropy of observed Y given predicted p."""
    p_list = [float(p) for p in preds]
    y_list = [int(y) for y in reals]
    if len(p_list) != len(y_list):
        raise ValueError("preds and reals length mismatch")
    n = len(p_list)
    if n == 0:
        return 0.0
    eps = 1e-12
    total = 0.0
    for p, y in zip(p_list, y_list):
        q = min(1.0 - eps, max(eps, p))
        total += -math.log(q) if y == 1 else -math.log(1.0 - q)
    return total / n


def information_gain(
    preds: Iterable[float],
    reals: Iterable[int],
) -> float:
    """H(Y) - H(Y|P): how much predictions reduce outcome uncertainty."""
    y_list = [int(y) for y in reals]
    n = len(y_list)
    if n == 0:
        return 0.0
    base_rate = sum(y_list) / n
    h_y = _h_bin(base_rate)
    h_y_given_p = conditional_entropy(preds, y_list)
    return h_y - h_y_given_p
