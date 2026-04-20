"""
Bayesian belief updating para agentes.

Cada persona mantém prior + likelihood sobre tópicos e sobre outros agentes.
Posterior update após observar evidência (post, debate, síntese).
"""

from __future__ import annotations

import math


def atualizar_crenca_bayes(
    prior: float,
    likelihood_dado_h1: float,
    likelihood_dado_h0: float,
) -> float:
    """
    Posterior P(H1 | evidência) = P(E|H1) * P(H1) / P(E)

    prior: P(H1) em [0, 1]
    likelihood_dado_h1: P(evidência | H1)
    likelihood_dado_h0: P(evidência | H0)

    Retorna posterior em [0, 1].
    """
    if not (0 <= prior <= 1):
        raise ValueError("prior fora de [0, 1]")
    numerador = likelihood_dado_h1 * prior
    p_e = numerador + likelihood_dado_h0 * (1 - prior)
    if p_e == 0:
        return prior
    return numerador / p_e


def log_odds(prob: float) -> float:
    """Converte probabilidade em log-odds (útil para atualização sequencial)."""
    prob = min(1 - 1e-9, max(1e-9, prob))
    return math.log(prob / (1 - prob))


def logistica(log_odds_val: float) -> float:
    """Inversa de log_odds."""
    return 1 / (1 + math.exp(-log_odds_val))


def atualizar_log_odds(
    prior: float,
    log_bayes_factor: float,
) -> float:
    """
    Soma log Bayes factor no log-odds. Mais estável numericamente que Bayes direto
    quando há muitas evidências sequenciais.
    """
    return logistica(log_odds(prior) + log_bayes_factor)
