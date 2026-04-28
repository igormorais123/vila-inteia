"""Spherical scoring rule (Roby 1965). Strictly proper alternative to Brier/log."""

from __future__ import annotations

import math
from typing import Iterable


def _spherical_one(p: float, y: int) -> float:
    p = max(0.0, min(1.0, p))
    norm = math.sqrt(p * p + (1.0 - p) * (1.0 - p))
    if norm <= 1e-15:
        return 0.0
    py = p if y == 1 else (1.0 - p)
    return -py / norm


def spherical_score(preds: Iterable[float], reals: Iterable[int]) -> float:
    """Mean spherical score: SS = -p_y / sqrt(p^2 + (1-p)^2). Lower is better."""
    p = [float(x) for x in preds]
    y = [int(x) for x in reals]
    n = len(p)
    if n == 0 or len(y) != n:
        return 0.0
    return sum(_spherical_one(pi, yi) for pi, yi in zip(p, y)) / n
