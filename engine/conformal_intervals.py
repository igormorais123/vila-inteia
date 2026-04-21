"""
Onda 162: conformal prediction intervals.

Quantifica incerteza: output [lo, hi] com coverage guarantee empírica.
Método: split conformal regression.

Pra cada prediction prob_p, calcular:
  residual_i = |prob_i - y_i|  em histórico
  quantile alpha = (1 - coverage) / 2
  q = quantil(residuals, 1 - alpha)
  interval = [max(0, p - q), min(1, p + q)]

Coverage guarantee: P(y in [lo, hi]) >= 1 - alpha (distribution-free).
Refs:
  - Vovk, Gammerman, Shafer (2005) Algorithmic Learning in a Random World.
  - Angelopoulos, Bates (2022) A Gentle Introduction to Conformal Prediction.
"""

from __future__ import annotations

import logging
from typing import Iterable, Sequence

logger = logging.getLogger(__name__)


def residuais_absolutos(
    probs: Iterable[float],
    y: Iterable[int],
) -> list[float]:
    """|prob - y| para cada par."""
    return [abs(float(p) - int(yy)) for p, yy in zip(probs, y)]


def quantil_empirico(valores: Sequence[float], q: float) -> float:
    """
    Quantile q (0..1) de valores. Linear interp entre samples ordenados.
    Retorna 0 se vazio.
    """
    if not valores:
        return 0.0
    vs = sorted(valores)
    n = len(vs)
    if n == 1:
        return vs[0]
    # Conformal: use ceil((n+1) * (1-alpha)) / n pra finite sample correção
    idx = q * (n - 1)
    lo = int(idx)
    hi = min(lo + 1, n - 1)
    frac = idx - lo
    return vs[lo] * (1 - frac) + vs[hi] * frac


def intervalo_conformal(
    prob: float,
    residuais_historico: Sequence[float],
    alpha: float = 0.2,
) -> tuple[float, float]:
    """
    Retorna (lo, hi) com cobertura empírica >= 1-alpha.
    alpha=0.2 → 80% CI. alpha=0.1 → 90% CI.
    """
    if not residuais_historico:
        return (max(0.0, prob - 0.5), min(1.0, prob + 0.5))
    # finite sample correction Conformal: quantile at (n+1)(1-alpha)/n clamped
    n = len(residuais_historico)
    q_level = min(1.0, (1 - alpha) * (n + 1) / n)
    q = quantil_empirico(list(residuais_historico), q_level)
    lo = max(0.0, prob - q)
    hi = min(1.0, prob + q)
    return lo, hi


def cobertura_empirica(
    probs_test: Iterable[float],
    y_test: Iterable[int],
    residuais_calib: Sequence[float],
    alpha: float = 0.2,
) -> dict:
    """
    Avalia quantas predictions test tiveram y dentro do [lo, hi].
    Retorna {cobertura_observada, n_test, alpha, cobertura_esperada_min}.
    """
    probs_test = list(probs_test)
    y_test = list(y_test)
    if not probs_test:
        return {"erro": "test vazio"}

    hits = 0
    for p, y in zip(probs_test, y_test):
        lo, hi = intervalo_conformal(p, residuais_calib, alpha=alpha)
        if lo <= y <= hi:
            hits += 1
    n = len(probs_test)
    return {
        "cobertura_observada": hits / n,
        "n_test": n,
        "alpha": alpha,
        "cobertura_esperada_min": 1 - alpha,
        "valida": (hits / n) >= (1 - alpha) - 0.1,  # tolerância 10 pts
    }


def fitar_intervalos(
    probs: Iterable[float],
    y: Iterable[int],
    alpha: float = 0.2,
) -> dict:
    """
    Fita conformal de calibração. Retorna {residuais, q, alpha, n}.
    Uso: aplicar `intervalo_conformal(prob, residuais, alpha)` em predição futura.
    """
    residuais = residuais_absolutos(probs, y)
    n = len(residuais)
    if n == 0:
        return {"erro": "dados vazios"}
    q_level = min(1.0, (1 - alpha) * (n + 1) / n)
    q = quantil_empirico(residuais, q_level)
    return {
        "residuais": residuais,
        "q": q,
        "alpha": alpha,
        "n": n,
        "half_width": q,  # intervalo típico = [p-q, p+q]
    }
