"""
engine.game_theory — fundamentos matemáticos de decisão estratégica.

Módulos:
    equilibrio      — Nash (puro+misto), best response, Stackelberg
    mecanismos      — VCG, Vickrey, second-price, allocation design
    jogos_repetidos — tit-for-tat, trigger strategies, folk theorem
    evolutivo       — replicator dynamics, ESS, hawk-dove
    coordenacao     — Schelling focal points, stag hunt
    bem_comum       — public goods, tragedy of commons, Ostrom

Convenção: matrizes de payoff como numpy arrays shape (n_strategies_i, n_strategies_j)
ou (n_players, n_strategies) para jogos n-player.
"""

from engine.game_theory.equilibrio import (
    nash_puro,
    nash_misto,
    best_response,
    stackelberg,
)
from engine.game_theory.mecanismos import (
    vcg_alocacao,
    vickrey_2nd_price,
)
from engine.game_theory.jogos_repetidos import (
    tit_for_tat,
    grim_trigger,
    rodada_iterada,
)
from engine.game_theory.evolutivo import (
    replicator_step,
    ess_candidatos,
)

__all__ = [
    "nash_puro",
    "nash_misto",
    "best_response",
    "stackelberg",
    "vcg_alocacao",
    "vickrey_2nd_price",
    "tit_for_tat",
    "grim_trigger",
    "rodada_iterada",
    "replicator_step",
    "ess_candidatos",
]
