"""
engine/agentes_vivos — Agentes da INTEIA que vivem na Vila e executam
ciclos reais (não apenas personas passivas).

Hoje: Helena (cientista-chefe, estratégia) e Efesto (CTO, infraestrutura).
Cada um tem heartbeat com cadência própria, acessa endpoints reais do
harness, grava relatórios em data/ e Supabase, e emite alertas quando
detectar anomalia.

Usar:
    from engine.agentes_vivos import HELENA, EFESTO, scheduler
    scheduler.rodar_ciclo_se_devido(step=N, sim=sim)
"""

from .helena import HelenaStrategos, HELENA
from .efesto import EfestoTekhton, EFESTO
from .scheduler import HeartbeatScheduler, scheduler

__all__ = [
    "HelenaStrategos", "HELENA",
    "EfestoTekhton", "EFESTO",
    "HeartbeatScheduler", "scheduler",
]
