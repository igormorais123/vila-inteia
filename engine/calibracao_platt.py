"""
Onda 93: calibração Platt scaling para probabilidades Vila.

Vila over-confident em backtest (Onda 92). Platt fit logistic:
    P_cal = 1 / (1 + exp(a * P_raw + b))

Onde (a, b) minimizam log-loss sobre holdout de (P_raw, y) reais.
Também suporta isotonic regression como baseline não-paramétrico.

Uso:
    a, b = fit_platt(probs_raw, y)
    p_cal = aplicar_platt(probs_raw, a, b)
"""

from __future__ import annotations

import math
from typing import Iterable

import numpy as np
from scipy.optimize import minimize_scalar


def _clip(p: float, eps: float = 1e-12) -> float:
    return max(eps, min(1 - eps, p))


def fit_platt(probs_raw: Iterable[float], y: Iterable[int]) -> tuple[float, float]:
    """
    Fit P_cal = sigmoid(a * logit(P_raw) + b) minimizando log-loss.

    Returns (a, b). Use aplicar_platt() pra obter prob calibrada.
    """
    probs = np.array([_clip(p) for p in probs_raw], dtype=float)
    labels = np.array(list(y), dtype=int)
    if probs.size == 0 or probs.size != labels.size:
        return 1.0, 0.0

    logits = np.log(probs / (1 - probs))  # logit(P_raw)

    def neg_log_loss(params):
        a, b = params
        z = a * logits + b
        p_cal = 1.0 / (1.0 + np.exp(-z))
        p_cal = np.clip(p_cal, 1e-12, 1 - 1e-12)
        return -np.mean(labels * np.log(p_cal) + (1 - labels) * np.log(1 - p_cal))

    # Busca simples (a,b)
    from scipy.optimize import minimize
    res = minimize(
        neg_log_loss,
        x0=[1.0, 0.0],
        method="Nelder-Mead",
        options={"xatol": 1e-4, "fatol": 1e-6, "maxiter": 500},
    )
    a, b = float(res.x[0]), float(res.x[1])
    return a, b


def aplicar_platt(probs_raw: Iterable[float], a: float, b: float) -> list[float]:
    probs = np.array([_clip(p) for p in probs_raw], dtype=float)
    logits = np.log(probs / (1 - probs))
    z = a * logits + b
    p_cal = 1.0 / (1.0 + np.exp(-z))
    return [float(p) for p in p_cal]


def brier(probs: Iterable[float], y: Iterable[int]) -> float:
    p = np.array(list(probs), dtype=float)
    y = np.array(list(y), dtype=int)
    return float(np.mean((p - y) ** 2))


def log_loss(probs: Iterable[float], y: Iterable[int]) -> float:
    p = np.array([_clip(x) for x in probs], dtype=float)
    y = np.array(list(y), dtype=int)
    return float(-np.mean(y * np.log(p) + (1 - y) * np.log(1 - p)))


def ece(probs: Iterable[float], y: Iterable[int], n_bins: int = 10) -> float:
    """
    Expected Calibration Error.
    Divide em n_bins, mede |prob_média - freq_real| por bin, pondera.
    Lower=better. 0 = perfect calibration.
    """
    p = np.array(list(probs), dtype=float)
    y = np.array(list(y), dtype=float)
    if p.size == 0:
        return 0.0
    bins = np.linspace(0, 1, n_bins + 1)
    total = 0.0
    for i in range(n_bins):
        lo, hi = bins[i], bins[i + 1]
        mask = (p >= lo) & (p < hi if i < n_bins - 1 else p <= hi)
        if mask.sum() == 0:
            continue
        conf = p[mask].mean()
        acc = y[mask].mean()
        w = mask.sum() / p.size
        total += w * abs(conf - acc)
    return float(total)


def avaliar_calibracao(
    probs_raw: Iterable[float],
    y: Iterable[int],
    n_bins: int = 10,
) -> dict:
    """
    Fit Platt + avalia antes/depois.
    Returns dict com brier_antes/depois, log_loss_antes/depois, ece_antes/depois, (a,b).
    """
    probs_raw = list(probs_raw)
    y = list(y)
    if not probs_raw:
        return {"erro": "dados vazios"}

    a, b = fit_platt(probs_raw, y)
    p_cal = aplicar_platt(probs_raw, a, b)
    return {
        "n": len(probs_raw),
        "platt_a": a,
        "platt_b": b,
        "brier_antes": brier(probs_raw, y),
        "brier_depois": brier(p_cal, y),
        "log_loss_antes": log_loss(probs_raw, y),
        "log_loss_depois": log_loss(p_cal, y),
        "ece_antes": ece(probs_raw, y, n_bins),
        "ece_depois": ece(p_cal, y, n_bins),
        "probs_calibradas": p_cal,
    }
