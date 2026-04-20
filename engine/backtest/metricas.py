"""
Métricas preditivas: Brier, log-loss, accuracy, calibration.
"""

from __future__ import annotations

import math
from typing import Iterable


def brier_score(probs: Iterable[float], outcomes: Iterable[int]) -> float:
    """
    Brier = mean((p - y)²). 0 = perfeito, 0.25 = random coin, 1 = maximally wrong.
    """
    probs = list(probs)
    outcomes = list(outcomes)
    if not probs or len(probs) != len(outcomes):
        return float("nan")
    return sum((p - y) ** 2 for p, y in zip(probs, outcomes)) / len(probs)


def log_loss(probs: Iterable[float], outcomes: Iterable[int], eps: float = 1e-12) -> float:
    """
    Binary log-loss: -mean(y*log(p) + (1-y)*log(1-p))
    """
    probs = list(probs)
    outcomes = list(outcomes)
    if not probs:
        return float("nan")
    total = 0.0
    for p, y in zip(probs, outcomes):
        p = min(1 - eps, max(eps, p))
        total += -(y * math.log(p) + (1 - y) * math.log(1 - p))
    return total / len(probs)


def accuracy_binaria(probs: Iterable[float], outcomes: Iterable[int], threshold: float = 0.5) -> float:
    """Fração de predições corretas acima do threshold."""
    probs = list(probs)
    outcomes = list(outcomes)
    if not probs:
        return float("nan")
    corretos = sum(1 for p, y in zip(probs, outcomes) if (p >= threshold) == bool(y))
    return corretos / len(probs)


def calibration_curve(probs: Iterable[float], outcomes: Iterable[int], bins: int = 10) -> list[dict]:
    """
    Reliability diagram: divide probs em `bins` e calcula outcome médio em cada.
    Predição perfeita: curva diagonal.
    """
    probs = list(probs)
    outcomes = list(outcomes)
    if not probs:
        return []
    buckets = [[] for _ in range(bins)]
    buckets_y = [[] for _ in range(bins)]
    for p, y in zip(probs, outcomes):
        idx = min(bins - 1, int(p * bins))
        buckets[idx].append(p)
        buckets_y[idx].append(y)
    curve = []
    for i in range(bins):
        if not buckets[i]:
            continue
        curve.append({
            "bin": i,
            "prob_media": sum(buckets[i]) / len(buckets[i]),
            "outcome_medio": sum(buckets_y[i]) / len(buckets_y[i]),
            "n": len(buckets[i]),
        })
    return curve
