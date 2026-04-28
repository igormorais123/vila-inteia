"""Brier Skill Score: BSS = 1 - BS_model / BS_climatology.

BS_climatology uses the empirical base rate y_bar as constant forecast,
so BS_clim = y_bar * (1 - y_bar). BSS in (-inf, 1]; 0 = climatology.
"""

from __future__ import annotations

from typing import Iterable


def brier(preds: Iterable[float], reals: Iterable[int]) -> float:
    p = [float(x) for x in preds]
    y = [int(x) for x in reals]
    if not p:
        return 0.0
    return sum((pi - yi) ** 2 for pi, yi in zip(p, y)) / len(p)


def brier_skill_score(preds: Iterable[float], reals: Iterable[int],
                      base_rate: float | None = None) -> dict:
    """BSS = 1 - BS_model / BS_clim.

    base_rate: optional climatology forecast. If None, uses empirical mean(y).
    """
    p = [float(x) for x in preds]
    y = [int(x) for x in reals]
    n = len(p)
    if n == 0 or len(y) != n:
        return {"n": n, "bss": None, "bs_model": 0.0,
                "bs_clim": 0.0, "base_rate": None}
    y_bar = sum(y) / n if base_rate is None else float(base_rate)
    bs_model = sum((pi - yi) ** 2 for pi, yi in zip(p, y)) / n
    bs_clim = sum((y_bar - yi) ** 2 for yi in y) / n
    if bs_clim <= 1e-12:
        bss = None
    else:
        bss = 1.0 - bs_model / bs_clim
    return {
        "n": n,
        "bss": bss,
        "bs_model": bs_model,
        "bs_clim": bs_clim,
        "base_rate": y_bar,
    }
