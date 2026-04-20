"""
Gate LLM por tier (Onda 59).

Decide dinamicamente se chamada LLM é permitida para dado agente:
    - Hot tier (top N%): chama LLM real
    - Cold tier (restante): retorna None → fallback heurístico

Integra com engine/distribuido/tiers.py (Onda 9).
Override global via VILA_LLM_TIER=off pra desativar.
"""

from __future__ import annotations

import os
import threading


VILA_LLM_TIER = os.getenv("VILA_LLM_TIER", "on").lower()
VILA_HOT_FRACTION = float(os.getenv("VILA_HOT_FRACTION", "0.05"))
VILA_HOT_ROTATE_STEPS = int(os.getenv("VILA_HOT_ROTATE_STEPS", "20"))


class LLMTierGate:
    """
    Mantém conjunto de agentes 'hot' rotacionando a cada N steps.
    Hot = chama LLM. Cold = heurístico.
    """

    def __init__(self, fracao_hot: float = 0.05, rotate_steps: int = 20):
        self.fracao_hot = fracao_hot
        self.rotate_steps = rotate_steps
        self._hot: set[str] = set()
        self._todos: list[str] = []
        self._lock = threading.Lock()
        self._step_ultima_rotacao = 0
        self._cursor = 0

    def inicializar(self, agentes: list[str]) -> None:
        with self._lock:
            self._todos = list(agentes)
            n_hot = max(1, int(len(agentes) * self.fracao_hot))
            self._hot = set(agentes[:n_hot])

    def pode_chamar_llm(self, agente_id: str) -> bool:
        if VILA_LLM_TIER == "off":
            return True
        with self._lock:
            if not self._hot:
                return True  # Não inicializado = permite tudo
            return agente_id in self._hot

    def talvez_rotacionar(self, step: int) -> bool:
        """Chamar a cada step. Rotaciona hot tier se atingiu rotate_steps."""
        with self._lock:
            if step - self._step_ultima_rotacao < self.rotate_steps:
                return False
            if not self._todos:
                return False
            n_hot = len(self._hot)
            if n_hot == 0:
                return False
            # Avança cursor: hot = self._todos[cursor : cursor+n_hot]
            self._cursor = (self._cursor + n_hot) % len(self._todos)
            fim = self._cursor + n_hot
            if fim <= len(self._todos):
                self._hot = set(self._todos[self._cursor:fim])
            else:
                # wrap
                self._hot = set(self._todos[self._cursor:] +
                                 self._todos[:fim - len(self._todos)])
            self._step_ultima_rotacao = step
            return True

    def stats(self) -> dict:
        with self._lock:
            return {
                "ativo": VILA_LLM_TIER != "off",
                "fracao_hot": self.fracao_hot,
                "rotate_steps": self.rotate_steps,
                "n_hot": len(self._hot),
                "n_total": len(self._todos),
                "step_ultima_rotacao": self._step_ultima_rotacao,
                "amostra_hot": sorted(self._hot)[:5],
            }


TIER_GATE_GLOBAL = LLMTierGate(
    fracao_hot=VILA_HOT_FRACTION,
    rotate_steps=VILA_HOT_ROTATE_STEPS,
)
