"""
Onda 100: bootstrap confidence intervals + isotonic regression.

- bootstrap_ci(fn, data, n_boot=1000, alpha=0.05) — CI qualquer métrica
- isotonic_fit(probs, y) — non-parametric calibration alternative
- comparacao_platt_vs_isotonic — lado-a-lado
"""

from __future__ import annotations

import random
from typing import Callable, Iterable

import numpy as np


def bootstrap_ci(
    metric_fn: Callable[[list, list], float],
    probs: Iterable[float],
    y: Iterable[int],
    n_boot: int = 1000,
    alpha: float = 0.05,
    seed: int = 42,
) -> dict:
    """
    Percentile bootstrap 95% CI para qualquer métrica fn(probs, y) -> float.
    """
    probs = list(probs)
    y = list(y)
    n = len(probs)
    if n < 2:
        return {"point": None, "lo": None, "hi": None, "n_boot": 0, "erro": "n<2"}

    rng = random.Random(seed)
    samples = []
    for _ in range(n_boot):
        idx = [rng.randrange(n) for _ in range(n)]
        p_s = [probs[i] for i in idx]
        y_s = [y[i] for i in idx]
        try:
            samples.append(metric_fn(p_s, y_s))
        except Exception:
            pass

    if not samples:
        return {"point": None, "lo": None, "hi": None, "n_boot": 0, "erro": "todas boots falharam"}

    arr = np.array(samples)
    lo = float(np.percentile(arr, alpha / 2 * 100))
    hi = float(np.percentile(arr, (1 - alpha / 2) * 100))
    point = float(metric_fn(probs, y))
    return {
        "point": point,
        "lo": lo,
        "hi": hi,
        "n_boot": len(samples),
        "alpha": alpha,
    }


def isotonic_fit(probs: Iterable[float], y: Iterable[int]) -> list[tuple[float, float]]:
    """
    Pool adjacent violators (PAV) algorithm.
    Retorna lista ordenada [(prob_raw, prob_cal), ...] pra interpolação.
    """
    pares = sorted(zip(probs, y))
    if not pares:
        return []

    # Initialize
    groups = [[p, float(yy), 1] for p, yy in pares]  # [prob, y_mean, weight]

    # Pool
    changed = True
    while changed:
        changed = False
        for i in range(len(groups) - 1):
            if groups[i][1] > groups[i + 1][1]:
                total_w = groups[i][2] + groups[i + 1][2]
                new_mean = (groups[i][1] * groups[i][2] + groups[i + 1][1] * groups[i + 1][2]) / total_w
                new_p = (groups[i][0] * groups[i][2] + groups[i + 1][0] * groups[i + 1][2]) / total_w
                groups[i] = [new_p, new_mean, total_w]
                del groups[i + 1]
                changed = True
                break

    # Map each original prob → cal
    out = []
    gi = 0
    for p, _ in pares:
        while gi + 1 < len(groups) and p > groups[gi + 1][0]:
            gi += 1
        out.append((p, groups[gi][1]))
    return out


def isotonic_aplicar(prob_raw: float, mapping: list[tuple[float, float]]) -> float:
    """
    Interpolação linear em mapping isotônico.
    """
    if not mapping:
        return prob_raw
    xs = [m[0] for m in mapping]
    ys = [m[1] for m in mapping]
    if prob_raw <= xs[0]:
        return ys[0]
    if prob_raw >= xs[-1]:
        return ys[-1]
    # Linear interp
    for i in range(len(xs) - 1):
        if xs[i] <= prob_raw <= xs[i + 1]:
            t = (prob_raw - xs[i]) / max(xs[i + 1] - xs[i], 1e-12)
            return ys[i] * (1 - t) + ys[i + 1] * t
    return prob_raw


def comparacao_platt_vs_isotonic(probs: Iterable[float], y: Iterable[int]) -> dict:
    """
    Fita ambos, compara Brier/log-loss/ECE.
    """
    from engine.calibracao_platt import fit_platt, aplicar_platt, brier, log_loss, ece
    probs = list(probs); y = list(y)
    if len(probs) < 5:
        return {"erro": "n<5 insuficiente"}

    a, b = fit_platt(probs, y)
    p_platt = aplicar_platt(probs, a, b)

    mapping = isotonic_fit(probs, y)
    p_iso = [isotonic_aplicar(p, mapping) for p in probs]

    return {
        "n": len(probs),
        "raw": {
            "brier": brier(probs, y),
            "log_loss": log_loss(probs, y),
            "ece": ece(probs, y),
        },
        "platt": {
            "a": a, "b": b,
            "brier": brier(p_platt, y),
            "log_loss": log_loss(p_platt, y),
            "ece": ece(p_platt, y),
        },
        "isotonic": {
            "mapping_size": len(mapping),
            "brier": brier(p_iso, y),
            "log_loss": log_loss(p_iso, y),
            "ece": ece(p_iso, y),
        },
    }
