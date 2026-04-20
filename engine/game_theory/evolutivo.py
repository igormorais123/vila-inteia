"""
Evolutionary game theory: replicator dynamics, ESS.

Referências:
    Maynard Smith (1982), Evolution and the Theory of Games.
    Weibull (1995), Evolutionary Game Theory.
    Nowak (2006), Evolutionary Dynamics.

Uso na Vila:
    - Evolução do genoma populacional em engine/colmeia.py
    - Estratégias dominadas desaparecem; ESS emergem
"""

from __future__ import annotations

import numpy as np


def replicator_step(populacao: np.ndarray, payoffs: np.ndarray, dt: float = 0.1) -> np.ndarray:
    """
    Um passo discreto da equação replicadora.

    populacao: shape (n,) — frequência de cada estratégia (soma 1)
    payoffs: shape (n, n) — payoff[i, j] = payoff da estr i contra estr j
    dt: passo de integração

    Equação: x_i' = x_i * (f_i - f_bar)
        f_i = sum_j x_j * payoffs[i, j]       (fitness da estratégia i)
        f_bar = sum_i x_i * f_i               (fitness médio)

    Retorna nova distribuição (soma 1).
    """
    if populacao.ndim != 1 or payoffs.ndim != 2:
        raise ValueError("dims incorretas")
    fitness = payoffs @ populacao
    f_bar = populacao @ fitness
    delta = populacao * (fitness - f_bar)
    nova = populacao + dt * delta
    nova = np.clip(nova, 0, None)
    soma = nova.sum()
    return nova / soma if soma > 0 else populacao


def replicator_convergencia(
    populacao_inicial: np.ndarray,
    payoffs: np.ndarray,
    max_iter: int = 1000,
    tol: float = 1e-6,
) -> tuple[np.ndarray, int]:
    """
    Itera replicator dynamics até convergência.
    Retorna (distribuição_final, iteracoes).
    """
    pop = populacao_inicial.copy()
    for it in range(max_iter):
        nova = replicator_step(pop, payoffs)
        if np.abs(nova - pop).max() < tol:
            return nova, it
        pop = nova
    return pop, max_iter


def ess_candidatos(payoffs: np.ndarray) -> list[int]:
    """
    Encontra candidatos a ESS (Evolutionary Stable Strategy) em estratégias puras.

    Estratégia i é ESS se:
        1. (i, i) é NE: payoffs[i, i] >= payoffs[j, i] para todo j
        2. Se payoffs[j, i] == payoffs[i, i] para algum j != i,
           então payoffs[i, j] > payoffs[j, j]  (condição de estabilidade)

    Retorna índices das estratégias ESS.
    """
    if payoffs.ndim != 2 or payoffs.shape[0] != payoffs.shape[1]:
        raise ValueError("payoffs deve ser matriz simétrica")
    n = payoffs.shape[0]
    ess = []
    for i in range(n):
        # Condição 1: (i, i) é NE
        if not all(payoffs[i, i] >= payoffs[j, i] for j in range(n)):
            continue
        # Condição 2: estabilidade contra empates
        estavel = True
        for j in range(n):
            if j == i:
                continue
            if np.isclose(payoffs[j, i], payoffs[i, i]):
                if payoffs[i, j] <= payoffs[j, j]:
                    estavel = False
                    break
        if estavel:
            ess.append(i)
    return ess


def hawk_dove_ess(v: float = 2.0, c: float = 3.0) -> float:
    """
    Jogo hawk-dove clássico. v = valor do recurso, c = custo da luta.
    ESS mixed: p* = v / c (fração de hawks na população em equilíbrio).
    """
    if c == 0:
        return 1.0
    return min(v / c, 1.0)
