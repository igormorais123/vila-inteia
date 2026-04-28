"""Bayes factor for binary forecasters (Jeffreys 1961; Kass & Raftery 1995).

K = P(D | M_a) / P(D | M_b). Returns log_bf for stability.
Evidence categories follow Kass & Raftery 1995 thresholds.
"""

from __future__ import annotations

import math
from typing import Iterable


def _evidence_label(bf: float) -> str:
    if bf <= 0:
        return "negative"
    if bf < 1:
        return "negative"
    if bf < 3:
        return "weak"
    if bf < 10:
        return "substantial"
    if bf < 30:
        return "strong"
    if bf < 100:
        return "very_strong"
    return "decisive"


def bayes_factor(
    preds_a: Iterable[float],
    preds_b: Iterable[float],
    reals: Iterable[int],
    eps: float = 1e-12,
) -> dict:
    """K = L_a / L_b for binary forecasts.

    log_bf = sum_i [y log(p_a) + (1-y) log(1-p_a)
                    - y log(p_b) - (1-y) log(1-p_b)]
    """
    pa = [float(x) for x in preds_a]
    pb = [float(x) for x in preds_b]
    y = [int(x) for x in reals]
    n = len(y)
    if n == 0 or len(pa) != n or len(pb) != n:
        return {
            "n": n, "log_bf": None, "bf": None,
            "evidence_strength": "n/a",
            "favors": None,
        }

    log_bf = 0.0
    for i in range(n):
        a = min(max(pa[i], eps), 1 - eps)
        b = min(max(pb[i], eps), 1 - eps)
        log_la = y[i] * math.log(a) + (1 - y[i]) * math.log(1 - a)
        log_lb = y[i] * math.log(b) + (1 - y[i]) * math.log(1 - b)
        log_bf += log_la - log_lb

    # bf may overflow for large |log_bf|; protect
    try:
        bf = math.exp(log_bf)
    except OverflowError:
        bf = float("inf") if log_bf > 0 else 0.0

    favors = "a" if log_bf > 0 else ("b" if log_bf < 0 else "tie")
    return {
        "n": n,
        "log_bf": log_bf,
        "bf": bf,
        "evidence_strength": _evidence_label(bf),
        "favors": favors,
    }
