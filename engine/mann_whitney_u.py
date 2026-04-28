"""Mann-Whitney U test (1947) for unpaired two-sample location."""

from __future__ import annotations

import math


def _normal_cdf(z: float) -> float:
    return 0.5 * (1.0 + math.erf(z / math.sqrt(2.0)))


def _ranks_with_ties(values: list[float]) -> tuple[list[float], float]:
    """Average ranks; return ranks list + tie-correction sum sum(t^3 - t)."""
    n = len(values)
    indexed = sorted(range(n), key=lambda i: values[i])
    ranks = [0.0] * n
    tie_sum = 0.0
    i = 0
    while i < n:
        j = i
        while j + 1 < n and values[indexed[j + 1]] == values[indexed[i]]:
            j += 1
        avg = (i + j) / 2.0 + 1.0
        for k in range(i, j + 1):
            ranks[indexed[k]] = avg
        t = j - i + 1
        if t > 1:
            tie_sum += (t ** 3 - t)
        i = j + 1
    return ranks, tie_sum


def mann_whitney_u(
    samples_a: list[float],
    samples_b: list[float],
) -> dict:
    """H0: distributions identical. Returns U (smaller of U_a, U_b), z-approx p two-sided."""
    n_a, n_b = len(samples_a), len(samples_b)
    if n_a < 1 or n_b < 1:
        return {"erro": "amostras vazias"}

    combined = list(samples_a) + list(samples_b)
    ranks, tie_sum = _ranks_with_ties(combined)
    R_a = sum(ranks[:n_a])
    R_b = sum(ranks[n_a:])

    U_a = R_a - n_a * (n_a + 1) / 2.0
    U_b = R_b - n_b * (n_b + 1) / 2.0
    U = min(U_a, U_b)

    N = n_a + n_b
    mean_U = n_a * n_b / 2.0
    if N <= 1:
        return {"U": U, "p_value": 1.0, "n_a": n_a, "n_b": n_b, "reject_h0": False}

    tie_correction = tie_sum / (N * (N - 1)) if N > 1 else 0.0
    var_U = n_a * n_b / 12.0 * ((N + 1) - tie_correction)
    if var_U <= 0:
        return {"U": U, "p_value": 1.0, "n_a": n_a, "n_b": n_b, "reject_h0": False}

    # continuity correction
    diff = U_a - mean_U
    if diff > 0:
        diff -= 0.5
    elif diff < 0:
        diff += 0.5
    z = diff / math.sqrt(var_U)
    p_value = 2.0 * (1.0 - _normal_cdf(abs(z)))

    return {
        "U": U,
        "U_a": U_a,
        "U_b": U_b,
        "z": z,
        "p_value": p_value,
        "n_a": n_a,
        "n_b": n_b,
        "reject_h0": p_value < 0.05,
    }
