"""Kullback-Leibler divergence (Kullback & Leibler 1951).

Binary forecasts: D_KL(P||Q) = p log(p/q) + (1-p) log((1-p)/(1-q)).
kl_calibration sums KL between observed and predicted rates per bin.
"""

from __future__ import annotations

import math
from typing import Iterable


def _clip(x: float, eps: float) -> float:
    """Keep x in [eps, 1-eps]."""
    return min(1.0 - eps, max(eps, x))


def kl_divergence_binary(
    preds: Iterable[float],
    reals: Iterable[int],
    eps: float = 1e-9,
) -> float:
    """Mean per-event D_KL(real || pred) for binary outcomes."""
    p_list = [float(p) for p in preds]
    y_list = [int(y) for y in reals]
    if len(p_list) != len(y_list):
        raise ValueError("preds and reals length mismatch")
    n = len(p_list)
    if n == 0:
        return 0.0
    total = 0.0
    for p, y in zip(p_list, y_list):
        q = _clip(p, eps)
        # P = real (point mass at y); D_KL(P||Q) = -log q if y=1 else -log(1-q)
        if y == 1:
            total += -math.log(q)
        else:
            total += -math.log(1.0 - q)
    return total / n


def kl_calibration(
    preds: Iterable[float],
    reals: Iterable[int],
    n_bins: int = 10,
    eps: float = 1e-9,
) -> float:
    """Weighted KL between observed and mean-predicted rate per bin.

    For each bin: D_KL(obs || mean_p) = obs log(obs/mean_p) +
                                          (1-obs) log((1-obs)/(1-mean_p)).
    Weighted by bin frequency.
    """
    p_list = [float(p) for p in preds]
    y_list = [int(y) for y in reals]
    n = len(p_list)
    if n == 0:
        return 0.0
    n_bins = max(1, int(n_bins))
    edges = [i / n_bins for i in range(n_bins + 1)]
    total = 0.0
    for i in range(n_bins):
        lo, hi = edges[i], edges[i + 1]
        if i < n_bins - 1:
            idx = [j for j in range(n) if lo <= p_list[j] < hi]
        else:
            idx = [j for j in range(n) if lo <= p_list[j] <= hi]
        n_k = len(idx)
        if n_k == 0:
            continue
        mean_p = _clip(sum(p_list[j] for j in idx) / n_k, eps)
        obs = _clip(sum(y_list[j] for j in idx) / n_k, eps)
        kl = obs * math.log(obs / mean_p) + (1 - obs) * math.log(
            (1 - obs) / (1 - mean_p)
        )
        total += (n_k / n) * kl
    return total
