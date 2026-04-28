"""Pairwise comparative ranking of forecasters across metrics."""

from __future__ import annotations

import math
from typing import Iterable


def _brier(p: list[float], y: list[int]) -> float:
    return sum((pi - yi) ** 2 for pi, yi in zip(p, y)) / len(p)


def _log_loss(p: list[float], y: list[int], eps: float = 1e-15) -> float:
    s = 0.0
    for pi, yi in zip(p, y):
        pi = max(eps, min(1.0 - eps, pi))
        s += -(yi * math.log(pi) + (1 - yi) * math.log(1.0 - pi))
    return s / len(p)


def _abs_loss(p: list[float], y: list[int]) -> float:
    return sum(abs(pi - yi) for pi, yi in zip(p, y)) / len(p)


def _spherical(p: list[float], y: list[int]) -> float:
    s = 0.0
    for pi, yi in zip(p, y):
        norm = math.sqrt(pi * pi + (1.0 - pi) * (1.0 - pi))
        if norm <= 1e-15:
            continue
        py = pi if yi == 1 else (1.0 - pi)
        s += -py / norm
    return s / len(p)


def _accuracy(p: list[float], y: list[int]) -> float:
    """Negated so lower is better (consistent with loss-style metrics)."""
    correct = sum(1 for pi, yi in zip(p, y) if (pi >= 0.5) == bool(yi))
    return -correct / len(p)


_METRICS = {
    "brier": _brier,
    "log": _log_loss,
    "abs": _abs_loss,
    "spherical": _spherical,
    "accuracy": _accuracy,
}


def rank_forecasters(predictors_dict: dict[str, Iterable[float]],
                     reals: Iterable[int],
                     metric: str = "brier") -> list[tuple[str, float, int]]:
    """Rank forecasters by metric (lower = better). Returns [(name, score, rank)]."""
    if metric not in _METRICS:
        return []
    y = [int(x) for x in reals]
    n = len(y)
    if n == 0:
        return []

    fn = _METRICS[metric]
    scored: list[tuple[str, float]] = []
    for name, preds in predictors_dict.items():
        p = [float(x) for x in preds]
        if len(p) != n:
            continue
        scored.append((name, fn(p, y)))

    scored.sort(key=lambda t: t[1])
    return [(name, score, rank + 1) for rank, (name, score) in enumerate(scored)]


def pairwise_dm(predictors_dict: dict[str, Iterable[float]],
                reals: Iterable[int],
                loss: str = "brier") -> list[dict]:
    """Pairwise Diebold-Mariano comparisons. Empty if dm module unavailable."""
    try:
        from engine.diebold_mariano import diebold_mariano
    except ImportError:
        return []

    y = [int(x) for x in reals]
    names = list(predictors_dict.keys())
    out = []
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            res = diebold_mariano(
                list(predictors_dict[a]),
                list(predictors_dict[b]),
                y,
                loss=loss,
            )
            res["a"] = a
            res["b"] = b
            out.append(res)
    return out
