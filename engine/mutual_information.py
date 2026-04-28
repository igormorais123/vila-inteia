"""Mutual information between predictions and outcomes.

I(P; Y) = H(P) + H(Y) - H(P, Y), with predictions discretized into
n_bins. NMI normalizes by sqrt(H(P) * H(Y)) so output sits in [0, 1].
"""

from __future__ import annotations

import math
from typing import Iterable


def _entropy(probs: list[float]) -> float:
    """Shannon entropy in nats."""
    h = 0.0
    for p in probs:
        if p > 0.0:
            h -= p * math.log(p)
    return h


def _bin_index(p: float, n_bins: int) -> int:
    idx = int(p * n_bins)
    if idx >= n_bins:
        idx = n_bins - 1
    if idx < 0:
        idx = 0
    return idx


def mutual_information(
    preds: Iterable[float],
    reals: Iterable[int],
    n_bins: int = 10,
) -> float:
    """Mutual information I(P_bin; Y) in nats."""
    p_list = [float(p) for p in preds]
    y_list = [int(y) for y in reals]
    n = len(p_list)
    if n == 0 or n_bins <= 0:
        return 0.0
    joint: dict[tuple[int, int], int] = {}
    p_marg: dict[int, int] = {}
    y_marg: dict[int, int] = {}
    for p, y in zip(p_list, y_list):
        b = _bin_index(p, n_bins)
        joint[(b, y)] = joint.get((b, y), 0) + 1
        p_marg[b] = p_marg.get(b, 0) + 1
        y_marg[y] = y_marg.get(y, 0) + 1
    mi = 0.0
    for (b, y), c in joint.items():
        p_xy = c / n
        p_x = p_marg[b] / n
        p_y = y_marg[y] / n
        if p_xy > 0 and p_x > 0 and p_y > 0:
            mi += p_xy * math.log(p_xy / (p_x * p_y))
    return max(0.0, mi)


def normalized_mutual_information(
    preds: Iterable[float],
    reals: Iterable[int],
    n_bins: int = 10,
) -> float:
    """NMI = I(P;Y) / sqrt(H(P) * H(Y)) in [0, 1]."""
    p_list = [float(p) for p in preds]
    y_list = [int(y) for y in reals]
    n = len(p_list)
    if n == 0 or n_bins <= 0:
        return 0.0
    p_marg: dict[int, int] = {}
    y_marg: dict[int, int] = {}
    for p, y in zip(p_list, y_list):
        b = _bin_index(p, n_bins)
        p_marg[b] = p_marg.get(b, 0) + 1
        y_marg[y] = y_marg.get(y, 0) + 1
    h_p = _entropy([c / n for c in p_marg.values()])
    h_y = _entropy([c / n for c in y_marg.values()])
    if h_p <= 0.0 or h_y <= 0.0:
        return 0.0
    mi = mutual_information(p_list, y_list, n_bins)
    nmi = mi / math.sqrt(h_p * h_y)
    return max(0.0, min(1.0, nmi))
