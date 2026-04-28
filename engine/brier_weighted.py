"""Weighted Brier score com importance weights.

WBS = Σ w_i (p_i - y_i)² / Σ w_i
Útil quando eventos têm stakes diferentes.
"""

from __future__ import annotations

import math


def brier_weighted(
    preds: list[float],
    reals: list,
    weights: list[float],
) -> float:
    """Importance-weighted Brier."""
    n = len(preds)
    if n == 0 or len(reals) != n or len(weights) != n:
        return 0.0
    num = 0.0
    den = 0.0
    for p, y, w in zip(preds, reals, weights):
        w = float(w)
        if w <= 0:
            continue
        num += w * (float(p) - float(y)) ** 2
        den += w
    return num / den if den > 0 else 0.0


def auto_weight_by_uncertainty(
    preds: list[float],
    reals: list | None = None,
    weight_fn: str = "entropy",
) -> list[float]:
    """Mais peso para preds incertas (perto de 0.5).

    weight_fn:
      - 'entropy': H(p) = -p log p - (1-p) log(1-p)
      - 'variance': p(1-p)
      - 'distance': 1 - 2|p - 0.5|
    """
    out = []
    for p in preds:
        p = min(1 - 1e-12, max(1e-12, float(p)))
        if weight_fn == "entropy":
            w = -(p * math.log(p) + (1 - p) * math.log(1 - p))
        elif weight_fn == "variance":
            w = p * (1 - p)
        elif weight_fn == "distance":
            w = 1.0 - 2.0 * abs(p - 0.5)
        else:
            raise ValueError(f"unknown weight_fn: {weight_fn}")
        out.append(w)
    return out
