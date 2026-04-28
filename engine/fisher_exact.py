"""Fisher's exact test (1922) for 2x2 contingency tables."""

from __future__ import annotations

import math


def _log_factorial(n: int) -> float:
    return math.lgamma(n + 1)


def _hypergeom_log_pmf(a: int, b: int, c: int, d: int) -> float:
    """log P(X=a) under hypergeometric with row/col margins fixed."""
    n = a + b + c + d
    return (
        _log_factorial(a + b)
        + _log_factorial(c + d)
        + _log_factorial(a + c)
        + _log_factorial(b + d)
        - _log_factorial(n)
        - _log_factorial(a)
        - _log_factorial(b)
        - _log_factorial(c)
        - _log_factorial(d)
    )


def fisher_exact(a: int, b: int, c: int, d: int) -> dict:
    """Two-sided p via summing all tables with margins fixed and prob <= observed.

    Table:
        | a | b |   row1 = a+b
        | c | d |   row2 = c+d
        col1=a+c  col2=b+d
    Odds ratio: (a*d)/(b*c) with 0.5 continuity if any zero.
    """
    if min(a, b, c, d) < 0:
        return {"erro": "células negativas"}
    if a + b == 0 or c + d == 0 or a + c == 0 or b + d == 0:
        return {
            "odds_ratio": float("nan"),
            "p_value_two_sided": 1.0,
            "n": a + b + c + d,
        }

    if a == 0 or b == 0 or c == 0 or d == 0:
        odds_ratio = ((a + 0.5) * (d + 0.5)) / ((b + 0.5) * (c + 0.5))
    else:
        odds_ratio = (a * d) / (b * c)

    row1 = a + b
    col1 = a + c
    n = a + b + c + d
    a_min = max(0, col1 - (n - row1))
    a_max = min(row1, col1)

    log_p_obs = _hypergeom_log_pmf(a, b, c, d)

    # numerical tolerance for "as extreme as observed"
    tol = 1e-10
    log_total = None
    log_extreme = None
    for ai in range(a_min, a_max + 1):
        bi = row1 - ai
        ci = col1 - ai
        di = (n - row1) - ci
        if bi < 0 or ci < 0 or di < 0:
            continue
        lp = _hypergeom_log_pmf(ai, bi, ci, di)
        log_total = lp if log_total is None else _logaddexp(log_total, lp)
        if lp <= log_p_obs + tol:
            log_extreme = lp if log_extreme is None else _logaddexp(log_extreme, lp)

    if log_extreme is None or log_total is None:
        p_two = 1.0
    else:
        p_two = math.exp(log_extreme - log_total)
        p_two = max(0.0, min(1.0, p_two))

    return {
        "odds_ratio": odds_ratio,
        "p_value_two_sided": p_two,
        "n": n,
        "reject_h0": p_two < 0.05,
    }


def _logaddexp(la: float, lb: float) -> float:
    if la == lb == float("-inf"):
        return float("-inf")
    m = max(la, lb)
    return m + math.log(math.exp(la - m) + math.exp(lb - m))
