"""
Event sourcing JSONL (Onda 31).

Escreve cada step da simulação como linha JSON em um arquivo. Permite:
- Replay determinístico post-mortem
- Auditoria completa (cada evento preservado)
- Compressão fácil (gzip do .jsonl reduz 10x)
- Análise offline com jq / pandas
"""

from __future__ import annotations

from dataclasses import dataclass, asdict, field
from pathlib import Path
import json
import threading
import time


@dataclass
class Evento:
    tipo: str                    # "step", "mule", "calibracao", "mudanca_estado", "desafio_concluido"
    step: int
    timestamp: float = field(default_factory=time.time)
    payload: dict = field(default_factory=dict)


class EventLog:
    """Escreve eventos thread-safe em JSONL (append-only)."""

    def __init__(self, arquivo: str | Path, vila_id: str = "default"):
        self.arquivo = Path(arquivo)
        self.vila_id = vila_id
        self._lock = threading.Lock()
        self._contador_por_tipo: dict[str, int] = {}
        self.arquivo.parent.mkdir(parents=True, exist_ok=True)

    def escrever(self, evento: Evento) -> None:
        with self._lock:
            d = asdict(evento)
            d["vila_id"] = self.vila_id
            linha = json.dumps(d, ensure_ascii=False) + "\n"
            with self.arquivo.open("a", encoding="utf-8") as fh:
                fh.write(linha)
            self._contador_por_tipo[evento.tipo] = self._contador_por_tipo.get(evento.tipo, 0) + 1

    def stats(self) -> dict:
        with self._lock:
            size_bytes = self.arquivo.stat().st_size if self.arquivo.exists() else 0
            return {
                "arquivo": str(self.arquivo),
                "vila_id": self.vila_id,
                "contador_por_tipo": dict(self._contador_por_tipo),
                "total_eventos": sum(self._contador_por_tipo.values()),
                "tamanho_bytes": size_bytes,
            }


def ler_eventos(arquivo: str | Path) -> list[Evento]:
    """Lê JSONL → lista de Evento."""
    path = Path(arquivo)
    if not path.exists():
        raise FileNotFoundError(f"arquivo não existe: {path}")
    eventos = []
    with path.open(encoding="utf-8") as fh:
        for linha in fh:
            linha = linha.strip()
            if not linha:
                continue
            d = json.loads(linha)
            d.pop("vila_id", None)
            eventos.append(Evento(**d))
    return eventos


def filtrar_por_tipo(eventos: list[Evento], tipo: str) -> list[Evento]:
    return [e for e in eventos if e.tipo == tipo]


def resumo_eventos(eventos: list[Evento]) -> dict:
    """Contagem + range temporal."""
    if not eventos:
        return {"total": 0}
    from collections import Counter
    tipos = Counter(e.tipo for e in eventos)
    steps = [e.step for e in eventos]
    ts = [e.timestamp for e in eventos]
    return {
        "total": len(eventos),
        "por_tipo": dict(tipos),
        "step_min": min(steps),
        "step_max": max(steps),
        "timestamp_min": min(ts),
        "timestamp_max": max(ts),
        "duracao_segundos": max(ts) - min(ts),
    }


def reconstituir_trajetoria(eventos: list[Evento]) -> list[str]:
    """Extrai trajetória de estados dos eventos 'step' ou 'mudanca_estado'."""
    traj = []
    for e in eventos:
        if e.tipo in ("step", "mudanca_estado"):
            estado = e.payload.get("estado")
            if estado:
                traj.append(estado)
    return traj


# Singleton opcional — pode ser reconfigurado
EVENT_LOG_GLOBAL = EventLog(arquivo="data/events/vila_events.jsonl")
