"""
Tracker de crenças numéricas por agente e por tópico.

Módulo opcional (não quebra nada se não usado). Mantém um dict
    crencas[agente_id][topico] = valor em [0, 1]
atualizado via Deffuant-Weisbuch (bounded confidence) após cada conversa.

Persistência é em memória por default; pode ser conectado ao Supabase
(tabela vila_crencas_historico) em camada superior.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from collections import defaultdict
import threading

from engine.cognitivo.integracoes_onda10 import atualizar_crenca_pos_conversa
from engine.opinion_dynamics.bounded_confidence import polarization_index
import numpy as np


@dataclass
class CrencaSnapshot:
    step: int
    topico: str
    valor_medio: float
    polarizacao: float
    n_agentes: int


class TrackerCrencas:
    """
    Estrutura thread-safe. Use ao longo da simulação.
    """

    def __init__(self) -> None:
        # agente_id → topico → float em [0, 1]
        self._crencas: dict[str, dict[str, float]] = defaultdict(dict)
        self._historico: list[CrencaSnapshot] = []
        self._lock = threading.Lock()

    def inicializar_agente(self, agente_id: str, topico: str, valor: float = 0.5) -> None:
        with self._lock:
            self._crencas[agente_id][topico] = max(0.0, min(1.0, valor))

    def obter(self, agente_id: str, topico: str, default: float = 0.5) -> float:
        return self._crencas.get(agente_id, {}).get(topico, default)

    def atualizar_apos_conversa(
        self,
        agente_id: str,
        parceiro_id: str,
        topico: str,
        influencia: float = 0.3,
        epsilon: float = 0.5,
    ) -> tuple[float, float]:
        """
        Chamar após cognitivo.conversar. Deffuant simétrico.
        Retorna (crenca_nova_agente, crenca_nova_parceiro).
        """
        with self._lock:
            ca = self._crencas[agente_id].get(topico, 0.5)
            cp = self._crencas[parceiro_id].get(topico, 0.5)
            nova_a = atualizar_crenca_pos_conversa(ca, cp, influencia, epsilon)
            nova_p = atualizar_crenca_pos_conversa(cp, ca, influencia, epsilon)
            self._crencas[agente_id][topico] = nova_a
            self._crencas[parceiro_id][topico] = nova_p
            return nova_a, nova_p

    def snapshot(self, step: int, topico: str) -> CrencaSnapshot:
        with self._lock:
            valores = [
                d[topico] for d in self._crencas.values() if topico in d
            ]
            if not valores:
                snap = CrencaSnapshot(step=step, topico=topico, valor_medio=0.5,
                                       polarizacao=0.0, n_agentes=0)
            else:
                arr = np.array(valores)
                snap = CrencaSnapshot(
                    step=step,
                    topico=topico,
                    valor_medio=float(arr.mean()),
                    polarizacao=float(polarization_index(arr)),
                    n_agentes=len(valores),
                )
            self._historico.append(snap)
            return snap

    def distribuicao(self, topico: str) -> dict[str, float]:
        """Retorna crença atual por agente no tópico."""
        with self._lock:
            return {
                aid: self._crencas[aid][topico]
                for aid in self._crencas
                if topico in self._crencas[aid]
            }

    def historico(self, topico: str | None = None) -> list[CrencaSnapshot]:
        with self._lock:
            if topico is None:
                return list(self._historico)
            return [s for s in self._historico if s.topico == topico]

    def topicos_rastreados(self) -> set[str]:
        with self._lock:
            tops: set[str] = set()
            for d in self._crencas.values():
                tops.update(d.keys())
            return tops


# Instância singleton opcional — simulação pode usar diretamente
TRACKER_GLOBAL = TrackerCrencas()
