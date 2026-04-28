"""McNemar test (1947) for paired binary classifiers."""

from __future__ import annotations

import math


def _normal_cdf(z: float) -> float:
    return 0.5 * (1.0 + math.erf(z / math.sqrt(2.0)))


def _chi2_1df_p(chi2: float) -> float:
    """Two-sided p-value for chi-square with 1 df via normal approx."""
    if chi2 <= 0:
        return 1.0
    z = math.sqrt(chi2)
    return 2.0 * (1.0 - _normal_cdf(z))


def mcnemar_test(
    preds_a: list[float],
    preds_b: list[float],
    reals: list[int],
    threshold: float = 0.5,
    continuity: bool = True,
) -> dict:
    """McNemar paired test on disagreements.

    b: clf_a right & clf_b wrong; c: clf_a wrong & clf_b right.
    chi2 = (|b-c| - 1)^2 / (b+c) with continuity, else (b-c)^2 / (b+c).
    """
    n = len(reals)
    if n < 1 or len(preds_a) != n or len(preds_b) != n:
        return {"erro": "tamanhos inconsistentes ou n<1"}

    b = c = 0
    a_correct = d_correct = 0
    for pa, pb, y in zip(preds_a, preds_b, reals):
        ya = (pa >= threshold) == bool(y)
        yb = (pb >= threshold) == bool(y)
        if ya and not yb:
            b += 1
        elif not ya and yb:
            c += 1
        elif ya and yb:
            a_correct += 1
            d_correct += 1

    disc = b + c
    if disc == 0:
        return {
            "chi_square": 0.0,
            "p_value": 1.0,
            "b": b,
            "c": c,
            "n": n,
            "reject_h0": False,
            "continuity": continuity,
        }

    if continuity:
        chi2 = (max(0, abs(b - c) - 1)) ** 2 / disc
    else:
        chi2 = (b - c) ** 2 / disc

    p_value = _chi2_1df_p(chi2)
    return {
        "chi_square": chi2,
        "p_value": p_value,
        "b": b,
        "c": c,
        "n": n,
        "reject_h0": p_value < 0.05,
        "continuity": continuity,
    }
