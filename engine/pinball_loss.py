"""Pinball loss for quantile forecasts (Koenker & Bassett 1978).

pinball(y, q, alpha) = max(alpha*(y-q), (alpha-1)*(y-q))
                     = (alpha - I(y < q)) * (y - q)
Asymmetric — penalizes under/over predictions differently.
"""

from __future__ import annotations


def _pinball_one(y: float, q: float, alpha: float) -> float:
    diff = y - q
    return alpha * diff if diff >= 0 else (alpha - 1.0) * diff


def pinball_loss(
    quantile_preds: list[float],
    reals: list,
    alpha: float = 0.5,
) -> float:
    """Mean pinball loss para quantil alpha."""
    if not quantile_preds:
        return 0.0
    if not (0.0 < alpha < 1.0):
        raise ValueError("alpha must be in (0,1)")
    s = 0.0
    n = 0
    for q, y in zip(quantile_preds, reals):
        s += _pinball_one(float(y), float(q), alpha)
        n += 1
    return s / n if n else 0.0


def quantile_calibration(
    preds: list[float],
    reals: list,
    alpha: float = 0.5,
) -> dict:
    """Empirical coverage P(y <= q_alpha) vs nominal alpha."""
    if not preds:
        return {"erro": "empty"}
    n = len(preds)
    below = sum(1 for q, y in zip(preds, reals) if float(y) <= float(q))
    coverage = below / n
    loss = pinball_loss(preds, reals, alpha=alpha)
    return {
        "n": n,
        "alpha": alpha,
        "coverage": coverage,
        "miscoverage": coverage - alpha,
        "pinball_loss": loss,
    }
