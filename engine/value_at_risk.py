"""Value-at-Risk (VaR) + Conditional VaR (Expected Shortfall).

VaR_alpha: alpha-quantile of returns (worst-case loss at confidence 1-alpha).
CVaR_alpha: mean of returns at-or-below VaR_alpha.
Convention: returns are losses-negative (e.g. -0.05 = -5% loss).
"""

from __future__ import annotations


def _quantile(sorted_xs: list[float], q: float) -> float:
    """Linear-interpolation quantile, q in [0,1]."""
    n = len(sorted_xs)
    if n == 0:
        return 0.0
    if n == 1:
        return sorted_xs[0]
    q = max(0.0, min(1.0, q))
    pos = q * (n - 1)
    lo = int(pos)
    hi = min(lo + 1, n - 1)
    frac = pos - lo
    return sorted_xs[lo] * (1 - frac) + sorted_xs[hi] * frac


def var_cvar(returns: list, alpha: float = 0.05) -> dict:
    """Historical VaR + CVaR at confidence level alpha.

    alpha=0.05 -> 5% VaR (95% confidence). VaR/CVaR signs follow returns
    (typically negative for losses).
    """
    rs = sorted(float(r) for r in returns)
    n = len(rs)
    if n == 0:
        return {"n": 0, "alpha": alpha, "var": 0.0, "cvar": 0.0}

    var = _quantile(rs, alpha)
    tail = [r for r in rs if r <= var]
    if not tail:
        tail = [rs[0]]
    cvar = sum(tail) / len(tail)
    return {
        "n": n,
        "alpha": alpha,
        "var": var,
        "cvar": cvar,
        "tail_size": len(tail),
        "worst": rs[0],
        "best": rs[-1],
    }


def historical_simulation_var(returns_history: list,
                              alpha: float = 0.05) -> float:
    """Plain historical-simulation VaR (alpha-quantile)."""
    return var_cvar(returns_history, alpha=alpha)["var"]
