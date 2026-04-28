"""Spiegelhalter's Z-test for binary forecast calibration (Spiegelhalter 1986)."""

from __future__ import annotations

import math
from typing import Iterable


def _normal_cdf(z: float) -> float:
    return 0.5 * (1.0 + math.erf(z / math.sqrt(2.0)))


def spiegelhalter_z(preds: Iterable[float], reals: Iterable[int],
                    alpha: float = 0.05) -> dict:
    """Z = sum (y_i - p_i) / sqrt(sum p_i (1 - p_i)).

    Under H0 (well-calibrated), Z ~ N(0, 1). Two-sided p-value.
    """
    p = [float(x) for x in preds]
    y = [int(x) for x in reals]
    n = len(p)
    if n == 0 or len(y) != n:
        return {"n": n, "z": None, "p_value": None,
                "reject_h0": False, "numerator": 0.0, "denominator": 0.0}

    num = sum(yi - pi for pi, yi in zip(p, y))
    var = sum(pi * (1.0 - pi) for pi in p)
    if var <= 1e-15:
        return {"n": n, "z": 0.0, "p_value": 1.0, "reject_h0": False,
                "numerator": num, "denominator": 0.0}

    z = num / math.sqrt(var)
    p_value = 2.0 * (1.0 - _normal_cdf(abs(z)))
    return {
        "n": n,
        "z": z,
        "p_value": p_value,
        "reject_h0": p_value < alpha,
        "numerator": num,
        "denominator": math.sqrt(var),
    }
