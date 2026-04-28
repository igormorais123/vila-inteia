"""Wilcoxon signed-rank test (1945) for paired non-parametric comparison."""

from __future__ import annotations

import math


def _brier_loss(p: float, y: int) -> float:
    return (p - y) ** 2


def _normal_cdf(z: float) -> float:
    return 0.5 * (1.0 + math.erf(z / math.sqrt(2.0)))


def _ranks_with_ties(values: list[float]) -> list[float]:
    """Average ranks with tie correction."""
    n = len(values)
    indexed = sorted(range(n), key=lambda i: values[i])
    ranks = [0.0] * n
    i = 0
    while i < n:
        j = i
        while j + 1 < n and values[indexed[j + 1]] == values[indexed[i]]:
            j += 1
        avg = (i + j) / 2.0 + 1.0
        for k in range(i, j + 1):
            ranks[indexed[k]] = avg
        i = j + 1
    return ranks


def wilcoxon_signed_rank(
    losses_a: list[float],
    losses_b: list[float],
) -> dict:
    """H0: median(loss_a - loss_b) == 0.

    W = sum of ranks with positive sign. Z-approx p (two-sided) for n_nz>20.
    """
    if len(losses_a) != len(losses_b) or len(losses_a) < 1:
        return {"erro": "tamanhos inconsistentes ou n<1"}

    diffs = [a - b for a, b in zip(losses_a, losses_b)]
    nonzero = [d for d in diffs if d != 0.0]
    n_nz = len(nonzero)
    if n_nz == 0:
        return {
            "W": 0.0,
            "p_value": 1.0,
            "n_nonzero": 0,
            "reject_h0": False,
        }

    abs_vals = [abs(d) for d in nonzero]
    ranks = _ranks_with_ties(abs_vals)
    W_pos = sum(r for r, d in zip(ranks, nonzero) if d > 0)
    W_neg = sum(r for r, d in zip(ranks, nonzero) if d < 0)
    W = min(W_pos, W_neg)

    mean_W = n_nz * (n_nz + 1) / 4.0
    # tie correction for variance
    tie_term = 0.0
    sorted_abs = sorted(abs_vals)
    i = 0
    while i < n_nz:
        j = i
        while j + 1 < n_nz and sorted_abs[j + 1] == sorted_abs[i]:
            j += 1
        t = j - i + 1
        if t > 1:
            tie_term += (t ** 3 - t)
        i = j + 1
    var_W = n_nz * (n_nz + 1) * (2 * n_nz + 1) / 24.0 - tie_term / 48.0
    if var_W <= 0:
        return {
            "W": W,
            "p_value": 1.0,
            "n_nonzero": n_nz,
            "reject_h0": False,
        }

    # continuity correction
    z = (W_pos - mean_W)
    if z > 0:
        z -= 0.5
    elif z < 0:
        z += 0.5
    z /= math.sqrt(var_W)
    p_value = 2.0 * (1.0 - _normal_cdf(abs(z)))

    return {
        "W": W,
        "W_pos": W_pos,
        "W_neg": W_neg,
        "z": z,
        "p_value": p_value,
        "n_nonzero": n_nz,
        "reject_h0": p_value < 0.05,
    }


def per_event_brier(preds: list[float], reals: list[int]) -> list[float]:
    """Helper: per-event Brier loss list."""
    return [_brier_loss(p, y) for p, y in zip(preds, reals)]
