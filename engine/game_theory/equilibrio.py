"""
Solvers de equilíbrio: Nash (puro+misto), best response, Stackelberg.

Referências:
    Nash (1950), Equilibrium points in n-person games.
    Fudenberg & Tirole (1991), Game Theory.
"""

from __future__ import annotations

import numpy as np
from dataclasses import dataclass


@dataclass
class EquilibrioNash:
    tipo: str                      # "puro" ou "misto"
    estrategias: list[np.ndarray]  # uma distribuição por jogador
    payoffs: list[float]           # payoff esperado de cada jogador
    unico: bool = False            # True se é o único equilíbrio


def nash_puro(payoff_a: np.ndarray, payoff_b: np.ndarray) -> list[EquilibrioNash]:
    """
    Encontra todos os equilíbrios de Nash em estratégias puras para jogo 2-jogador.

    payoff_a: shape (m, n) — payoffs do jogador A para cada combinação (i, j)
    payoff_b: shape (m, n) — payoffs do jogador B

    Retorna lista de equilíbrios (pode ser vazia, 1, ou múltiplos).

    Algoritmo: para cada célula (i, j), checa se i é melhor resposta à j
    (argmax de payoff_a[:, j]) E j é melhor resposta à i (argmax de payoff_b[i, :]).
    """
    if payoff_a.shape != payoff_b.shape:
        raise ValueError("matrizes devem ter mesma shape")
    m, n = payoff_a.shape
    eqs: list[EquilibrioNash] = []
    # Para cada coluna j, maior payoff_a é best-response de A
    best_a_por_col = [np.flatnonzero(payoff_a[:, j] == payoff_a[:, j].max()) for j in range(n)]
    # Para cada linha i, maior payoff_b é best-response de B
    best_b_por_lin = [np.flatnonzero(payoff_b[i, :] == payoff_b[i, :].max()) for i in range(m)]
    for i in range(m):
        for j in range(n):
            if i in best_a_por_col[j] and j in best_b_por_lin[i]:
                estr_a = np.zeros(m); estr_a[i] = 1
                estr_b = np.zeros(n); estr_b[j] = 1
                eqs.append(EquilibrioNash(
                    tipo="puro",
                    estrategias=[estr_a, estr_b],
                    payoffs=[float(payoff_a[i, j]), float(payoff_b[i, j])],
                    unico=False,
                ))
    if len(eqs) == 1:
        eqs[0].unico = True
    return eqs


def nash_misto(payoff_a: np.ndarray, payoff_b: np.ndarray) -> EquilibrioNash | None:
    """
    Equilíbrio de Nash em estratégias mistas para jogo 2-jogador.

    Usa nashpy (lemke-howson / support enumeration). Retorna o primeiro equilíbrio
    completamente misto encontrado (support > 1 em pelo menos um jogador).
    Se apenas puros existem, retorna None.
    """
    try:
        import nashpy as nash
    except ImportError:
        raise RuntimeError("nashpy não instalado; rodar: pip install nashpy")
    jogo = nash.Game(payoff_a, payoff_b)
    for sa, sb in jogo.support_enumeration():
        support_a = int(np.sum(sa > 1e-9))
        support_b = int(np.sum(sb > 1e-9))
        if support_a > 1 or support_b > 1:
            pa = float(sa @ payoff_a @ sb)
            pb = float(sa @ payoff_b @ sb)
            return EquilibrioNash(
                tipo="misto",
                estrategias=[np.array(sa), np.array(sb)],
                payoffs=[pa, pb],
                unico=False,
            )
    return None


def best_response(payoff_proprio: np.ndarray, estrategia_oponente: np.ndarray) -> int:
    """
    Melhor resposta pura a uma estratégia (possivelmente mista) do oponente.

    payoff_proprio: shape (m, n) — payoff do jogador para cada (minha_estr, estr_oponente)
    estrategia_oponente: shape (n,) — distribuição de prob do oponente

    Retorna índice da estratégia pura que maximiza payoff esperado.
    """
    if payoff_proprio.ndim != 2:
        raise ValueError("payoff_proprio deve ser 2D")
    if estrategia_oponente.shape[0] != payoff_proprio.shape[1]:
        raise ValueError("shape mismatch")
    valores = payoff_proprio @ estrategia_oponente
    return int(np.argmax(valores))


def stackelberg(
    payoff_leader: np.ndarray,
    payoff_follower: np.ndarray,
) -> EquilibrioNash:
    """
    Equilíbrio de Stackelberg — leader move primeiro, follower responde ótimo.

    Backward induction: para cada estratégia i do leader, calcula best response j(i)
    do follower, depois leader escolhe i que maximiza payoff_leader[i, j(i)].
    """
    if payoff_leader.shape != payoff_follower.shape:
        raise ValueError("shapes divergem")
    m, n = payoff_leader.shape
    melhor_i = 0
    melhor_j = 0
    melhor_payoff = -np.inf
    for i in range(m):
        j = int(np.argmax(payoff_follower[i, :]))
        pl = payoff_leader[i, j]
        if pl > melhor_payoff:
            melhor_payoff = pl
            melhor_i = i
            melhor_j = j
    estr_a = np.zeros(m); estr_a[melhor_i] = 1
    estr_b = np.zeros(n); estr_b[melhor_j] = 1
    return EquilibrioNash(
        tipo="puro",
        estrategias=[estr_a, estr_b],
        payoffs=[float(melhor_payoff), float(payoff_follower[melhor_i, melhor_j])],
        unico=True,
    )
