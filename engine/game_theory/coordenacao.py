"""
Jogos de coordenação: stag hunt, Schelling focal points, battle of sexes.

Referências:
    Schelling (1960), The Strategy of Conflict.
    Skyrms (2004), The Stag Hunt.

Uso na Vila:
    - Escolha coletiva de tema (todos debaterem o mesmo ou se dispersarem)
    - Sincronização de timing em desafios
"""

from __future__ import annotations

import numpy as np


def stag_hunt(n_jogadores: int, caca_cervo: int) -> float:
    """
    Stag hunt payoff: cooperação arriscada (cervo) vs segurança (lebre).
    Retorna payoff de quem escolhe cervo quando `caca_cervo` cooperam.
    Cervo só compensa se TODOS cooperarem.
    """
    if caca_cervo == n_jogadores:
        return 4.0      # todos cooperam: cervo grande, dividido
    else:
        return 0.0      # alguém desertou: caçadores de cervo perdem


def focal_point_schelling(opcoes: list[str], saliencias: dict[str, float]) -> str:
    """
    Focal point de Schelling: dada ausência de comunicação, jogadores
    convergem para opção mais "saliente" (nome famoso, meio, primeira, etc.)

    saliencias[opcao] = quão saliente é aquela opção
    Retorna opção escolhida.
    """
    if not opcoes:
        raise ValueError("sem opções")
    return max(opcoes, key=lambda o: saliencias.get(o, 0.0))


def battle_of_sexes_nash(
    payoff_a_pref: float = 2.0,
    payoff_b_pref: float = 2.0,
    payoff_desacordo: float = 0.0,
) -> dict:
    """
    Battle of sexes 2x2.

    Payoff matrix (A preferia Opera O, B preferia Box X):
        O   X
      O (A,B) (0,0)
      X (0,0) (B,A)

    Tem 2 NE puros ((O,O), (X,X)) e 1 misto:
        p_A* = b/(a+b)   (A joga O com essa prob)
        p_B* = a/(a+b)   (B joga O com essa prob)
    """
    a = payoff_a_pref
    b = payoff_b_pref
    d = payoff_desacordo
    total = a + b
    if total <= 0:
        raise ValueError("a + b > 0 requerido")
    return {
        "ne_puros": [
            {"jogada": ("O", "O"), "payoff": (a, b)},
            {"jogada": ("X", "X"), "payoff": (b, a)},
        ],
        "ne_misto": {
            "p_a_toca_o": b / total,
            "p_b_toca_o": a / total,
            "payoff_esperado_a": (a * b) / total,
            "payoff_esperado_b": (a * b) / total,
        },
        "desacordo_payoff": d,
    }
