"""
Budget tracker USD (Onda 62).

Acumula custo total de chamadas LLM durante execução. Para simulação
quando atinge limite VILA_BUDGET_USD_MAX (default ilimitado).

Preços por modelo (USD / 1M tokens input+output) estimados abril/2026:
    gemini-2.5-flash-lite:  $0.10 in + $0.40 out
    gemini-2.5-flash:       $0.30 in + $2.50 out
    claude-haiku:           $1.00 in + $5.00 out
    claude-sonnet:          $3.00 in + $15.00 out
    omniroute/BestFREE:     $0.00 (grátis)
"""

from __future__ import annotations

import os
import threading
import time
from dataclasses import dataclass, field


# USD por 1M tokens (input, output). Atualizar conforme provider.
PRECOS_MODELO = {
    "gemini-2.5-flash-lite":  (0.10, 0.40),
    "gemini-2.5-flash":       (0.30, 2.50),
    "gemini-2.0-flash":       (0.10, 0.40),
    "gemini-flash-latest":    (0.30, 2.50),
    "claude-haiku-4-5-20251001":   (1.00, 5.00),
    "claude-sonnet-4-20250514":    (3.00, 15.00),
    "claude-opus-4-7":             (15.00, 75.00),
    "BestFREE":    (0.00, 0.00),
    "osa-elite":   (0.00, 0.00),
    "osa-specialist": (0.00, 0.00),
}


@dataclass
class RegistroChamada:
    modelo: str
    tokens_in: int
    tokens_out: int
    custo_usd: float
    timestamp: float = field(default_factory=time.time)


class BudgetTracker:
    def __init__(self, limite_usd: float = float("inf")):
        self.limite_usd = limite_usd
        self.total_usd = 0.0
        self.total_tokens_in = 0
        self.total_tokens_out = 0
        self._historico: list[RegistroChamada] = []
        self._lock = threading.Lock()

    def registrar(self, modelo: str, tokens_in: int, tokens_out: int) -> float:
        preco_in, preco_out = PRECOS_MODELO.get(modelo, (0.0, 0.0))
        custo = (tokens_in / 1_000_000) * preco_in + (tokens_out / 1_000_000) * preco_out
        with self._lock:
            self.total_usd += custo
            self.total_tokens_in += tokens_in
            self.total_tokens_out += tokens_out
            self._historico.append(RegistroChamada(
                modelo=modelo, tokens_in=tokens_in,
                tokens_out=tokens_out, custo_usd=custo,
            ))
            self._historico = self._historico[-1000:]
        return custo

    def pode_chamar(self) -> bool:
        """Retorna False se budget esgotou."""
        with self._lock:
            return self.total_usd < self.limite_usd

    def resetar(self) -> None:
        with self._lock:
            self.total_usd = 0.0
            self.total_tokens_in = 0
            self.total_tokens_out = 0
            self._historico.clear()

    def stats(self) -> dict:
        with self._lock:
            from collections import Counter
            por_modelo: dict[str, float] = {}
            for r in self._historico:
                por_modelo[r.modelo] = por_modelo.get(r.modelo, 0.0) + r.custo_usd
            return {
                "limite_usd": self.limite_usd if self.limite_usd != float("inf") else None,
                "total_usd": round(self.total_usd, 6),
                "total_tokens_in": self.total_tokens_in,
                "total_tokens_out": self.total_tokens_out,
                "n_chamadas": len(self._historico),
                "restante_usd": max(0, self.limite_usd - self.total_usd) if self.limite_usd != float("inf") else None,
                "exausto": self.total_usd >= self.limite_usd,
                "custo_por_modelo_usd": {k: round(v, 6) for k, v in por_modelo.items()},
            }


_limite = os.getenv("VILA_BUDGET_USD_MAX", "")
_BUDGET_LIMITE = float(_limite) if _limite else float("inf")
BUDGET_GLOBAL = BudgetTracker(limite_usd=_BUDGET_LIMITE)
