"""Diebold-Mariano test for forecast comparison (Diebold & Mariano 1995)."""

from __future__ import annotations

import math


def _brier_loss(p: float, y: int) -> float:
    return (p - y) ** 2


def _log_loss(p: float, y: int, eps: float = 1e-15) -> float:
    p = max(eps, min(1.0 - eps, p))
    return -(y * math.log(p) + (1 - y) * math.log(1.0 - p))


def _abs_loss(p: float, y: int) -> float:
    return abs(p - y)


_LOSSES = {"brier": _brier_loss, "log": _log_loss, "abs": _abs_loss}


def _normal_cdf(z: float) -> float:
    """Two-tailed via abramowitz erf approximation."""
    return 0.5 * (1.0 + math.erf(z / math.sqrt(2.0)))


def diebold_mariano(
    preds_a: list[float],
    preds_b: list[float],
    reals: list[int],
    loss: str = "brier",
) -> dict:
    """DM test: H0 mean(loss_a - loss_b) == 0.

    Returns dm_stat, p_value (two-sided), reject_h0 at alpha=0.05, n, mean_diff.
    """
    if loss not in _LOSSES:
        return {"erro": f"loss desconhecida: {loss}"}
    n = len(reals)
    if n < 2 or len(preds_a) != n or len(preds_b) != n:
        return {"erro": "tamanhos inconsistentes ou n<2"}

    L = _LOSSES[loss]
    d = [L(preds_a[i], reals[i]) - L(preds_b[i], reals[i]) for i in range(n)]
    mean_d = sum(d) / n
    var_d = sum((x - mean_d) ** 2 for x in d) / (n - 1) if n > 1 else 0.0

    if var_d <= 0:
        return {
            "dm_stat": 0.0,
            "p_value": 1.0,
            "reject_h0": False,
            "n": n,
            "mean_diff": mean_d,
            "var_diff": var_d,
            "loss": loss,
        }

    dm_stat = mean_d / math.sqrt(var_d / n)
    p_value = 2.0 * (1.0 - _normal_cdf(abs(dm_stat)))
    return {
        "dm_stat": dm_stat,
        "p_value": p_value,
        "reject_h0": p_value < 0.05,
        "n": n,
        "mean_diff": mean_d,
        "var_diff": var_d,
        "loss": loss,
    }
