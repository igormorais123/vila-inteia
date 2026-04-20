"""
Persistência da trajetória psico-histórica em Supabase (Onda 14).

Flush batched: acumula N estados na memória, escreve em lote quando atinge
limiar. Falha silenciosa: se Supabase não configurado, apenas no-op.
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
import time
import threading

try:
    from engine.supabase_db import inserir
    SUPABASE_OK = True
except Exception:
    SUPABASE_OK = False


@dataclass
class RegistroPsico:
    vila_id: str
    step: int
    estado: str
    polarizacao: float = 0.0
    gini: float = 0.0
    n_ativos: int = 0
    n_latentes: int = 0
    timestamp: float = field(default_factory=time.time)


class PersistenciaPsico:
    """Buffer thread-safe com flush auto a cada N registros."""

    def __init__(self, vila_id: str = "default", batch_size: int = 50,
                 tabela: str = "vila_trajetoria_psico"):
        self.vila_id = vila_id
        self.batch_size = batch_size
        self.tabela = tabela
        self._buffer: list[RegistroPsico] = []
        self._lock = threading.Lock()
        self._total_flushed = 0

    def adicionar(self, reg: RegistroPsico) -> bool:
        """Adiciona ao buffer. Flush automático se atingir batch_size."""
        with self._lock:
            self._buffer.append(reg)
            if len(self._buffer) >= self.batch_size:
                self._flush_locked()
        return True

    def _flush_locked(self) -> int:
        """Internal — chama com _lock já adquirido."""
        if not self._buffer:
            return 0
        if not SUPABASE_OK:
            self._buffer.clear()
            return 0
        n = len(self._buffer)
        try:
            for reg in self._buffer:
                inserir(self.tabela, {
                    "vila_id": reg.vila_id,
                    "step": reg.step,
                    "estado": reg.estado,
                    "polarizacao": reg.polarizacao,
                    "gini": reg.gini,
                    "n_ativos": reg.n_ativos,
                    "n_latentes": reg.n_latentes,
                })
            self._total_flushed += n
        except Exception:
            # Não derrubar simulação por falha de persistência
            pass
        self._buffer.clear()
        return n

    def flush(self) -> int:
        """Força flush manual. Retorna número de registros enviados."""
        with self._lock:
            return self._flush_locked()

    def stats(self) -> dict:
        with self._lock:
            return {
                "buffer_atual": len(self._buffer),
                "total_flushed": self._total_flushed,
                "supabase_ativo": SUPABASE_OK,
                "tabela": self.tabela,
            }


PERSISTENCIA_GLOBAL = PersistenciaPsico()
