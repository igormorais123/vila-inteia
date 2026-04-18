"""
Scheduler de heartbeats da INTEIA dentro da Vila.

Não é cron do sistema — é gatilho por `step` da simulação. Dispara
`executar_heartbeat` quando `step % intervalo == 0`.

No modo live da Vila (`main.py live`), o simulacao.executar_step() chama
`scheduler.rodar_ciclo_se_devido(step=N)` a cada step. Em modo CLI/demo,
é também chamado; em modo serve puro (sem loop), não há step.
"""

from __future__ import annotations

import logging
from typing import Any

from .helena import HELENA
from .efesto import EFESTO

logger = logging.getLogger("vila-inteia.agentes_vivos.scheduler")


class HeartbeatScheduler:
    def __init__(self):
        self.agentes = [HELENA, EFESTO]
        self._ultimos_step: dict[str, int] = {}

    def rodar_ciclo_se_devido(self, step: int, sim: Any = None) -> list:
        """
        Varre os agentes, executa os que estão na cadência.
        Retorna lista de heartbeats executados neste step.
        """
        out = []
        for a in self.agentes:
            if step <= 0:
                continue
            intervalo = max(1, int(getattr(a, "intervalo_steps", 100)))
            ultimo = self._ultimos_step.get(a.id, -1)
            if step - ultimo >= intervalo or step == intervalo:
                try:
                    h = a.executar_heartbeat(step=step, sim=sim)
                    out.append(h)
                    self._ultimos_step[a.id] = step
                except Exception as exc:
                    logger.warning("heartbeat %s step %s falhou: %s", a.id, step, exc)
        return out

    def status(self) -> dict:
        return {
            "agentes": [
                {
                    "id": a.id,
                    "nome": a.nome,
                    "papel": a.papel,
                    "intervalo_steps": a.intervalo_steps,
                    "ultimo_step_executado": self._ultimos_step.get(a.id, None),
                }
                for a in self.agentes
            ]
        }


scheduler = HeartbeatScheduler()
