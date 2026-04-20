"""
Bounded confidence models: só atualiza crença se opinião alheia é "próxima o bastante".

Captura polarização: threshold baixo → cluster em ilhas isoladas;
threshold alto → consenso global.

Referências:
    Deffuant, Neau, Amblard, Weisbuch (2000).
    Hegselmann & Krause (2002).
"""

from __future__ import annotations

import numpy as np
import random


def deffuant_step(
    crencas: np.ndarray,
    epsilon: float = 0.3,
    mu: float = 0.5,
    rng: random.Random | None = None,
) -> np.ndarray:
    """
    Deffuant-Weisbuch: selciona 2 agentes aleatórios. Se |x_i - x_j| < epsilon,
    aproximam-se por fator mu.

    epsilon: threshold de confiança (0.1 = muito fragmentado; 0.5 = consenso)
    mu: velocidade de convergência em [0, 0.5]
    """
    if rng is None:
        rng = random.Random()
    cr = crencas.copy()
    n = len(cr)
    if n < 2:
        return cr
    i, j = rng.sample(range(n), 2)
    if abs(cr[i] - cr[j]) < epsilon:
        media_shift = mu * (cr[j] - cr[i])
        cr[i] += media_shift
        cr[j] -= media_shift
    return cr


def deffuant_simular(
    crencas_inicial: np.ndarray,
    epsilon: float = 0.3,
    mu: float = 0.5,
    passos: int = 10000,
    seed: int = 42,
) -> np.ndarray:
    """Roda Deffuant por N interações."""
    rng = random.Random(seed)
    cr = crencas_inicial.copy()
    for _ in range(passos):
        cr = deffuant_step(cr, epsilon, mu, rng)
    return cr


def hk_step(crencas: np.ndarray, epsilon: float = 0.2) -> np.ndarray:
    """
    Hegselmann-Krause: cada agente vira a média dos vizinhos dentro do raio epsilon.
    Atualização síncrona (todos ao mesmo tempo).
    """
    n = len(crencas)
    nova = np.zeros_like(crencas)
    for i in range(n):
        vizinhos = np.abs(crencas - crencas[i]) < epsilon
        nova[i] = crencas[vizinhos].mean()
    return nova


def polarization_index(crencas: np.ndarray) -> float:
    """
    Índice de polarização: variância bimodal normalizada.
    0 = consenso total, 1 = polarização máxima (metade em 0, metade em 1).
    """
    if len(crencas) < 2:
        return 0.0
    var = float(np.var(crencas))
    return min(1.0, var * 4)  # 0.25 = var de Bernoulli(0.5) → 1
