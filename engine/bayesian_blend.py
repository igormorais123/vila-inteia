"""
Onda 125: Bayesian prior blending.

Combina Vila forecast com base rate do dataset via log-odds weighted mean.
log-odds(blend) = w_prior * log-odds(prior) + w_vila * log-odds(vila)

Rationale: base rate incorpora informação histórica do domínio.
Se Americanas dataset tem 100% outcomes=1, prior = 0.99 deve puxar Vila
pra cima mesmo que LLM duvide.

Weight balance:
- w_vila alto se Vila confiante E skill histórica alta
- w_prior alto se Vila incerta (prob ~0.5) ou dataset bem caracterizado
"""

from __future__ import annotations

import math
from typing import Iterable


_EPS = 1e-6


def _logit(p: float) -> float:
    p = max(_EPS, min(1 - _EPS, p))
    return math.log(p / (1 - p))


def _sigmoid(z: float) -> float:
    if z >= 0:
        e = math.exp(-z)
        return 1.0 / (1.0 + e)
    e = math.exp(z)
    return e / (1.0 + e)


def base_rate_dataset(y_history: Iterable[int], laplace: float = 1.0) -> float:
    """Laplace-smoothed base rate. Vazio → 0.5."""
    ys = list(y_history)
    n = len(ys)
    if n == 0:
        return 0.5
    k = sum(ys)
    return (k + laplace) / (n + 2 * laplace)


def bayesian_blend(
    prob_vila: float,
    prior_base_rate: float,
    peso_vila: float = 0.7,
) -> float:
    """
    Weighted log-odds blend.
    peso_vila=0.7 default (Vila domina, prior regula).
    peso_vila=1.0 → só Vila. peso_vila=0.0 → só prior.
    """
    w_vila = max(0.0, min(1.0, peso_vila))
    w_prior = 1.0 - w_vila
    lv = _logit(prob_vila)
    lp = _logit(prior_base_rate)
    z = w_vila * lv + w_prior * lp
    return _sigmoid(z)


def blend_vetor(
    probs_vila: Iterable[float],
    y_walk_forward: Iterable[int],
    peso_vila: float = 0.7,
    laplace: float = 1.0,
) -> list[float]:
    """
    Walk-forward blend: pra cada evento i, usa base_rate dos eventos 0..i-1.
    """
    probs = list(probs_vila)
    y = list(y_walk_forward)
    out = []
    for i, pv in enumerate(probs):
        br = base_rate_dataset(y[:i], laplace=laplace)
        out.append(bayesian_blend(pv, br, peso_vila=peso_vila))
    return out


def peso_adaptativo(
    prob_vila: float,
    skill_historico: float | None = None,
) -> float:
    """
    Retorna peso_vila adaptativo:
    - Vila muito confiante (|prob - 0.5| > 0.3) + skill > 0 → peso alto 0.8-0.9
    - Vila incerta (|prob - 0.5| < 0.1) → peso baixo 0.5-0.6 (prior ajuda)
    - Skill negativo → peso baixo (prior confia-se mais)
    """
    base = 0.7
    certeza = abs(prob_vila - 0.5) * 2  # 0 = max incerteza, 1 = certeza
    # Skill adjustment
    if skill_historico is not None:
        if skill_historico > 0.2:
            base += 0.1
        elif skill_historico < -0.2:
            base -= 0.15
    # Certainty modulation
    w = base + (certeza - 0.5) * 0.2  # range ~[-0.1, +0.1]
    return max(0.4, min(0.9, w))
