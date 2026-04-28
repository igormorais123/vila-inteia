"""Permutation test: classifier vs random shuffling of predictions."""

from __future__ import annotations

import math
import random


def _brier(preds: list[float], reals: list[int]) -> float:
    n = len(reals)
    return sum((p - y) ** 2 for p, y in zip(preds, reals)) / n if n else 0.0


def _log_loss(preds: list[float], reals: list[int], eps: float = 1e-15) -> float:
    n = len(reals)
    if n == 0:
        return 0.0
    s = 0.0
    for p, y in zip(preds, reals):
        p = max(eps, min(1.0 - eps, p))
        s += -(y * math.log(p) + (1 - y) * math.log(1.0 - p))
    return s / n


def _acc(preds: list[float], reals: list[int]) -> float:
    n = len(reals)
    if n == 0:
        return 0.0
    return sum(1 for p, y in zip(preds, reals) if (p >= 0.5) == bool(y)) / n


_METRICS = {"brier": _brier, "log": _log_loss, "acc": _acc}
# lower-tail metrics: smaller observed = better (p = fraction permuted <= observed)
_LOWER = {"brier", "log"}


def permutation_test(
    preds: list[float],
    reals: list[int],
    n_perm: int = 1000,
    metric: str = "brier",
    seed: int = 42,
) -> dict:
    """Shuffle preds vs reals; p_value = fraction with metric at least as extreme.

    For brier/log (lower=better): p = fraction permuted <= observed.
    For acc (higher=better): p = fraction permuted >= observed.
    """
    if metric not in _METRICS:
        return {"erro": f"metric desconhecida: {metric}"}
    n = len(reals)
    if n < 2 or len(preds) != n:
        return {"erro": "tamanhos inconsistentes ou n<2"}

    fn = _METRICS[metric]
    observed = fn(list(preds), list(reals))

    rng = random.Random(seed)
    shuffled = list(preds)
    count = 0
    for _ in range(n_perm):
        rng.shuffle(shuffled)
        m = fn(shuffled, reals)
        if metric in _LOWER:
            if m <= observed:
                count += 1
        else:
            if m >= observed:
                count += 1

    # add-one smoothing to avoid p=0
    p_value = (count + 1) / (n_perm + 1)
    return {
        "observed_metric": observed,
        "p_value": p_value,
        "n_perm": n_perm,
        "n": n,
        "metric": metric,
        "reject_h0": p_value < 0.05,
    }
