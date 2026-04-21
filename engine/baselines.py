"""
Onda 118: simple time-series baselines para comparar vs Vila.

Pra cada evento no backtest, prediz prob via:
- base_rate: média de outcome dos eventos anteriores
- markov_1: p(y=1 | y_anterior) via contagem
- exp_smooth: exponential smoothing com alpha
- last_value: y_anterior ou 0.5 inicial
- random_uniform: 0.5 sempre
- prior_humano: usa prob_prior do CSV (já existe)

Evalua Brier + accuracy de cada + compara com Vila.
"""

from __future__ import annotations

import logging
from typing import Iterable

import numpy as np

logger = logging.getLogger(__name__)


def base_rate(y_history: list[int], default: float = 0.5) -> float:
    """Média de outcomes passados (ou default se vazio)."""
    if not y_history:
        return default
    return sum(y_history) / len(y_history)


def last_value(y_history: list[int], default: float = 0.5) -> float:
    if not y_history:
        return default
    return float(y_history[-1])


def markov_1_order(y_history: list[int], laplace: float = 1.0) -> float:
    """Laplace-smoothed P(y=1 | ultima obs). Só faz sentido com >=2 obs."""
    if len(y_history) < 2:
        return 0.5
    last = y_history[-1]
    # Count transitions from 'last' to {0,1}
    trans_1 = sum(1 for i in range(len(y_history) - 1)
                  if y_history[i] == last and y_history[i+1] == 1)
    trans_tot = sum(1 for i in range(len(y_history) - 1)
                    if y_history[i] == last)
    # Laplace smoothing
    return (trans_1 + laplace) / (trans_tot + 2 * laplace)


def exp_smoothing(y_history: list[int], alpha: float = 0.3,
                  default: float = 0.5) -> float:
    """Simple exponential smoothing. Recent obs peso mais."""
    if not y_history:
        return default
    s = default
    for y in y_history:
        s = alpha * y + (1 - alpha) * s
    return s


def random_uniform(*_) -> float:
    return 0.5


def comparar_baselines(
    probs_vila: Iterable[float],
    y: Iterable[int],
    priors: Iterable[float] | None = None,
) -> dict:
    """
    Walk-forward compare todos baselines.

    Returns dict com {method: {brier_avg, accuracy, n}} pra cada método +
    skill_vs_base_rate, skill_vs_markov, skill_vs_prior.
    """
    probs_vila = list(probs_vila)
    y = list(y)
    priors = list(priors) if priors else None
    n = len(y)
    if n < 2:
        return {"erro": "n<2", "n": n}

    methods = {
        "vila": probs_vila,
        "base_rate": [],
        "last_value": [],
        "markov_1": [],
        "exp_smooth_0.3": [],
        "random": [0.5] * n,
    }
    if priors:
        methods["prior_humano"] = priors

    # Walk-forward compute baselines
    for i in range(n):
        hist = y[:i]
        methods["base_rate"].append(base_rate(hist))
        methods["last_value"].append(last_value(hist))
        methods["markov_1"].append(markov_1_order(hist))
        methods["exp_smooth_0.3"].append(exp_smoothing(hist, alpha=0.3))

    def _score(preds):
        brier = sum((p - yi)**2 for p, yi in zip(preds, y)) / n
        acc = sum(int((p >= 0.5) == (yi == 1)) for p, yi in zip(preds, y)) / n
        return brier, acc

    out = {"n": n, "metodos": {}}
    briers = {}
    for name, preds in methods.items():
        if len(preds) != n: continue
        br, ac = _score(preds)
        out["metodos"][name] = {"brier_avg": br, "accuracy": ac}
        briers[name] = br

    # Skill scores vs cada baseline
    if "vila" in briers:
        bv = briers["vila"]
        for base in ["base_rate", "last_value", "markov_1", "exp_smooth_0.3", "random"]:
            if base in briers and briers[base] > 0:
                out[f"skill_vila_vs_{base}"] = 1 - bv / briers[base]
        if "prior_humano" in briers and briers["prior_humano"] > 0:
            out["skill_vila_vs_prior_humano"] = 1 - bv / briers["prior_humano"]

    # Ranking
    ranking = sorted(
        [(name, d["brier_avg"]) for name, d in out["metodos"].items()],
        key=lambda x: x[1],
    )
    out["ranking_brier_asc"] = [{"metodo": n, "brier": b} for n, b in ranking]

    return out
