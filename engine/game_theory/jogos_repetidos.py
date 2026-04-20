"""
Jogos repetidos: estratégias de cooperação/traição iteradas.

Referências:
    Axelrod (1984), The Evolution of Cooperation.
    Fudenberg & Maskin (1986), folk theorem.

Uso na Vila:
    - Interação entre rivais lendários ao longo de steps (mentor vs discípulo, etc.)
    - Confiança/traição modelada formalmente além do LLM heurístico
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable


COOPERAR = 1
TRAIR = 0


@dataclass
class Historico:
    minhas_acoes: list[int] = field(default_factory=list)
    acoes_oponente: list[int] = field(default_factory=list)


EstrategiaFn = Callable[[Historico], int]


def tit_for_tat(hist: Historico) -> int:
    """
    Tit-for-tat: coopera na primeira, depois copia última jogada do oponente.
    Campeão do torneio de Axelrod 1980.
    """
    if not hist.acoes_oponente:
        return COOPERAR
    return hist.acoes_oponente[-1]


def grim_trigger(hist: Historico) -> int:
    """
    Trigger strategy: coopera até oponente trair uma vez, depois trai para sempre.
    """
    if TRAIR in hist.acoes_oponente:
        return TRAIR
    return COOPERAR


def tit_for_two_tats(hist: Historico) -> int:
    """
    Mais tolerante: só trai após 2 traições consecutivas.
    """
    if len(hist.acoes_oponente) >= 2 and hist.acoes_oponente[-1] == TRAIR and hist.acoes_oponente[-2] == TRAIR:
        return TRAIR
    return COOPERAR


def sempre_cooperar(hist: Historico) -> int:
    return COOPERAR


def sempre_trair(hist: Historico) -> int:
    return TRAIR


@dataclass
class ResultadoRodada:
    rodadas: int
    payoff_a: float
    payoff_b: float
    historico_a: list[int]
    historico_b: list[int]


def rodada_iterada(
    estrat_a: EstrategiaFn,
    estrat_b: EstrategiaFn,
    rodadas: int = 100,
    matriz_payoff: tuple[tuple[int, int], tuple[int, int], tuple[int, int], tuple[int, int]] = (
        (3, 3),  # CC
        (0, 5),  # CT
        (5, 0),  # TC
        (1, 1),  # TT
    ),
) -> ResultadoRodada:
    """
    Prisoner's dilemma iterado padrão.
    matriz_payoff = (CC, CT, TC, TT) onde cada tupla é (payoff_a, payoff_b)
    """
    hist_a = Historico()
    hist_b = Historico()
    total_a = 0.0
    total_b = 0.0

    cc, ct, tc, tt = matriz_payoff

    for _ in range(rodadas):
        a = estrat_a(hist_a)
        b = estrat_b(hist_b)
        if a == COOPERAR and b == COOPERAR:
            pa, pb = cc
        elif a == COOPERAR and b == TRAIR:
            pa, pb = ct
        elif a == TRAIR and b == COOPERAR:
            pa, pb = tc
        else:
            pa, pb = tt
        total_a += pa
        total_b += pb
        hist_a.minhas_acoes.append(a)
        hist_a.acoes_oponente.append(b)
        hist_b.minhas_acoes.append(b)
        hist_b.acoes_oponente.append(a)

    return ResultadoRodada(
        rodadas=rodadas,
        payoff_a=total_a,
        payoff_b=total_b,
        historico_a=hist_a.minhas_acoes,
        historico_b=hist_b.minhas_acoes,
    )


def torneio_axelrod(estrategias: dict[str, EstrategiaFn], rodadas: int = 200) -> dict[str, float]:
    """
    Round-robin tournament: cada estratégia joga contra todas (inclusive cópia dela).
    Retorna payoff médio por estratégia (ordenado: chave mais alta = vencedor).
    """
    nomes = list(estrategias.keys())
    totais = {n: 0.0 for n in nomes}
    n_jogos = {n: 0 for n in nomes}
    for i, a in enumerate(nomes):
        for b in nomes[i:]:
            r = rodada_iterada(estrategias[a], estrategias[b], rodadas=rodadas)
            totais[a] += r.payoff_a
            totais[b] += r.payoff_b
            n_jogos[a] += 1
            n_jogos[b] += 1
    return {n: totais[n] / max(1, n_jogos[n]) for n in nomes}
