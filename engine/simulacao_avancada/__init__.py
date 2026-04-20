"""
engine.simulacao_avancada — física, coalizões, topologias, segregação.

Módulos:
    campus_fisica         — A* pathfinding, congestion, queueing
    coalizoes             — Shapley, core, Banzhaf
    schelling             — Schelling segregation 2D
    voter_espacial        — Hotelling/Downs spatial voter
    redes                 — small-world, preferential attachment, community
    informacao_imperfeita — signaling, cheap talk, reputation
"""

from engine.simulacao_avancada.campus_fisica import rota_otima, congestao
from engine.simulacao_avancada.coalizoes import shapley_value, core_membership
from engine.simulacao_avancada.schelling import schelling_step, tipping_point
from engine.simulacao_avancada.voter_espacial import median_voter, hotelling_equilibrio
from engine.simulacao_avancada.redes import small_world, preferential_attachment, detectar_comunidades

__all__ = [
    "rota_otima",
    "congestao",
    "shapley_value",
    "core_membership",
    "schelling_step",
    "tipping_point",
    "median_voter",
    "hotelling_equilibrio",
    "small_world",
    "preferential_attachment",
    "detectar_comunidades",
]
