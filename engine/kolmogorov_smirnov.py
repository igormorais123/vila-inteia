"""Kolmogorov-Smirnov test for distribution comparison and PIT calibration."""

from __future__ import annotations

import math
from typing import Callable, Iterable


def _ks_pvalue(n: int, d: float) -> float:
    """Asymptotic two-sided KS p-value via Kolmogorov distribution."""
    if n <= 0 or d <= 0:
        return 1.0
    lam = (math.sqrt(n) + 0.12 + 0.11 / math.sqrt(n)) * d
    s = 0.0
    for k in range(1, 101):
        term = 2.0 * ((-1) ** (k - 1)) * math.exp(-2.0 * (k * lam) ** 2)
        s += term
        if abs(term) < 1e-12:
            break
    return max(0.0, min(1.0, s))


def _uniform_cdf(x: float) -> float:
    if x <= 0.0:
        return 0.0
    if x >= 1.0:
        return 1.0
    return x


def ks_test(samples: Iterable[float], reference: str | Callable = "uniform",
            alpha: float = 0.05) -> dict:
    """KS statistic = sup |F_emp(x) - F_ref(x)| vs reference CDF."""
    xs = sorted(float(x) for x in samples)
    n = len(xs)
    if n == 0:
        return {"n": 0, "ks": None, "p_value": None, "reject_h0": False}

    if reference == "uniform":
        cdf = _uniform_cdf
    elif callable(reference):
        cdf = reference
    else:
        return {"n": n, "ks": None, "p_value": None,
                "reject_h0": False, "erro": f"reference desconhecida: {reference}"}

    d = 0.0
    for i, x in enumerate(xs, start=1):
        f_ref = cdf(x)
        d_plus = i / n - f_ref
        d_minus = f_ref - (i - 1) / n
        d = max(d, d_plus, d_minus)

    p_value = _ks_pvalue(n, d)
    return {
        "n": n,
        "ks": d,
        "p_value": p_value,
        "reject_h0": p_value < alpha,
        "reference": reference if isinstance(reference, str) else "callable",
    }


def ks_pit_test(preds: Iterable[float], reals: Iterable[int],
                alpha: float = 0.05) -> dict:
    """KS test on PIT values (binary): u_i = p_i if y=1 else 1-p_i.

    Under perfect calibration, PITs ~ Uniform(0, 1).
    """
    p = [float(x) for x in preds]
    y = [int(x) for x in reals]
    n = len(p)
    if n == 0 or len(y) != n:
        return {"n": n, "ks": None, "p_value": None, "reject_h0": False}
    pit = [pi if yi == 1 else (1.0 - pi) for pi, yi in zip(p, y)]
    out = ks_test(pit, reference="uniform", alpha=alpha)
    out["pit_mean"] = sum(pit) / n
    return out
