"""Sharpe ratio + Sortino ratio for forecaster returns.

Sharpe = (mean(returns) - risk_free) / std(returns)
Sortino = (mean(returns) - target) / downside_deviation
where downside_deviation = sqrt(mean(min(0, r - target)^2))
"""

from __future__ import annotations

import math


def _mean(xs: list[float]) -> float:
    return sum(xs) / len(xs) if xs else 0.0


def sharpe_ratio(returns: list[float], risk_free: float = 0.0) -> float:
    """Per-period Sharpe (unannualized).

    Returns 0.0 when n<2 or std=0.
    """
    rs = [float(r) for r in returns]
    n = len(rs)
    if n < 2:
        return 0.0
    excess = [r - risk_free for r in rs]
    mu = _mean(excess)
    var = sum((e - mu) ** 2 for e in excess) / (n - 1)
    sd = math.sqrt(var)
    if sd <= 0:
        return 0.0
    return mu / sd


def sortino_ratio(returns: list[float], target: float = 0.0) -> float:
    """Per-period Sortino. Penalizes only downside vs target.

    Returns 0.0 when n<2 or no downside.
    """
    rs = [float(r) for r in returns]
    n = len(rs)
    if n < 2:
        return 0.0
    mu = _mean(rs) - target
    downside_sq = [min(0.0, r - target) ** 2 for r in rs]
    dd_var = sum(downside_sq) / n
    dd = math.sqrt(dd_var)
    if dd <= 0:
        return 0.0
    return mu / dd


def sharpe_breakdown(returns: list[float], risk_free: float = 0.0,
                     target: float = 0.0) -> dict:
    """Joint Sharpe + Sortino + supporting stats."""
    rs = [float(r) for r in returns]
    n = len(rs)
    if not rs:
        return {"n": 0, "mean": 0.0, "std": 0.0,
                "sharpe": 0.0, "sortino": 0.0}
    mu = _mean(rs)
    var = (sum((r - mu) ** 2 for r in rs) / (n - 1)) if n >= 2 else 0.0
    return {
        "n": n,
        "mean": mu,
        "std": math.sqrt(var),
        "sharpe": sharpe_ratio(rs, risk_free=risk_free),
        "sortino": sortino_ratio(rs, target=target),
    }
