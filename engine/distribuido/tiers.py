"""
Classificação hot/cold de agentes para roteamento de LLM.

Hot tier: 5 % dos agentes "ativos" no último ciclo usam LLM real.
Cold tier: 95 % usam apenas heurísticas (sem custo LLM).

A rotação é por turno, garantindo que todos os agentes vejam LLM
ao longo de muitos steps.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from collections import deque

HOT = "hot"
COLD = "cold"


@dataclass
class TierClassifier:
    total_agentes: int = 0
    fracao_hot: float = 0.05
    rotacao_turnos: int = 20
    _contador: int = 0
    _queue_hot: deque = field(default_factory=deque)

    def inicializar(self, ids_agentes: list[str]) -> None:
        self.total_agentes = len(ids_agentes)
        n_hot = max(1, int(self.total_agentes * self.fracao_hot))
        # Seed inicial: top-N (pode ser randomizado em produção)
        self._queue_hot = deque(ids_agentes[:n_hot])

    def tier_para(self, agente_id: str) -> str:
        return HOT if agente_id in self._queue_hot else COLD

    def passo_rotacao(self, todos_ids: list[str]) -> None:
        """Chama a cada step; rotaciona hot tier após N turnos."""
        self._contador += 1
        if self._contador < self.rotacao_turnos:
            return
        self._contador = 0
        # Descarta os primeiros, adiciona próximos
        n_hot = len(self._queue_hot)
        if not self._queue_hot or n_hot == 0:
            return
        fora = self._queue_hot.popleft()
        # Próximo na lista global que não está em hot
        nao_hot = [i for i in todos_ids if i not in self._queue_hot]
        if nao_hot:
            self._queue_hot.append(nao_hot[self._contador % len(nao_hot)])


def classificar_tier(agente_id: str, classifier: TierClassifier) -> str:
    return classifier.tier_para(agente_id)
