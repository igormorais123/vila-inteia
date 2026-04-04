"""
Memória Espacial - Consciência de localização do agente.

Mantém um modelo mental do campus: onde estão as coisas,
quem foi visto onde, e rotas conhecidas.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class RegistroPresenca:
    """Registro de quem foi visto em determinado local."""

    agente_id: str
    agente_nome: str
    local_id: str
    visto_em: datetime = field(default_factory=datetime.now)
    acao_observada: str = ""


class MemoriaEspacial:
    """
    Modelo mental do espaço que o agente mantém.

    Sabe:
    - Onde cada local fica e como chegar
    - Quem foi visto onde recentemente
    - Seus locais favoritos
    - Locais que evita
    """

    def __init__(self):
        # Mapa mental: local_id -> info conhecida
        self.locais_conhecidos: set[str] = set()

        # Presenças observadas: agente_id -> último registro
        self.presencas: dict[str, RegistroPresenca] = {}

        # Histórico de locais visitados: lista de (local_id, timestamp)
        self.historico: list[tuple[str, datetime]] = []

        # Locais favoritos (mais visitados)
        self._contagem_visitas: dict[str, int] = {}

        # Locais a evitar (experiências negativas)
        self.locais_evitar: set[str] = set()

    def registrar_visita(self, local_id: str, quando: datetime | None = None):
        """Registra que o agente visitou um local."""
        quando = quando or datetime.now()
        self.locais_conhecidos.add(local_id)
        self.historico.append((local_id, quando))
        self._contagem_visitas[local_id] = (
            self._contagem_visitas.get(local_id, 0) + 1
        )

    def registrar_presenca(
        self,
        agente_id: str,
        agente_nome: str,
        local_id: str,
        acao: str = "",
        quando: datetime | None = None,
    ):
        """Registra que viu outro agente em um local."""
        self.presencas[agente_id] = RegistroPresenca(
            agente_id=agente_id,
            agente_nome=agente_nome,
            local_id=local_id,
            visto_em=quando or datetime.now(),
            acao_observada=acao,
        )

    def onde_esta(self, agente_id: str) -> Optional[str]:
        """Retorna o último local conhecido de outro agente."""
        registro = self.presencas.get(agente_id)
        return registro.local_id if registro else None

    def quem_esta_em(self, local_id: str) -> list[RegistroPresenca]:
        """Retorna quem foi visto em um local (pode estar desatualizado)."""
        return [
            r for r in self.presencas.values()
            if r.local_id == local_id
        ]

    def locais_favoritos(self, n: int = 5) -> list[str]:
        """Retorna os N locais mais visitados."""
        ordenados = sorted(
            self._contagem_visitas.items(),
            key=lambda x: x[1],
            reverse=True,
        )
        return [local_id for local_id, _ in ordenados[:n]]

    def local_atual(self) -> Optional[str]:
        """Retorna o local mais recente no histórico."""
        if self.historico:
            return self.historico[-1][0]
        return None

    def tempo_no_local_atual(self, agora: datetime | None = None) -> float:
        """Retorna horas no local atual."""
        if not self.historico:
            return 0
        agora = agora or datetime.now()
        _, entrada = self.historico[-1]
        return (agora - entrada).total_seconds() / 3600

    def to_dict(self) -> dict:
        return {
            "locais_conhecidos": list(self.locais_conhecidos),
            "presencas": {
                k: {
                    "agente_id": v.agente_id,
                    "agente_nome": v.agente_nome,
                    "local_id": v.local_id,
                    "visto_em": v.visto_em.isoformat(),
                    "acao_observada": v.acao_observada,
                }
                for k, v in self.presencas.items()
            },
            "contagem_visitas": self._contagem_visitas,
            "locais_evitar": list(self.locais_evitar),
        }
