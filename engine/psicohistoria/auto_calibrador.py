"""
Auto-calibrador periódico (Onda 18).

A cada N steps, recalibra a matriz M do grafo psico-histórico global usando
a trajetória real observada até então. Substitui baseline estático por
adaptive learning.

Integração:
    engine.simulacao.SimulacaoVila a cada 50 steps chama
    AUTO_CALIBRADOR_GLOBAL.talvez_calibrar(step)
"""

from __future__ import annotations

from dataclasses import dataclass, field
import threading
import time
from typing import Callable

import numpy as np

from engine.psicohistoria.grafo_eventos import construir_grafo_vila, GrafoPsicohistoria
from engine.psicohistoria.calibracao_online import calibrar, perplexity


@dataclass
class RegistroCalibracao:
    step: int
    n_transicoes: int
    cobertura_pct: float
    divergencia_frobenius: float
    perplexity_antes: float
    perplexity_depois: float
    timestamp: float = field(default_factory=time.time)


class AutoCalibrador:
    """
    Gerencia matriz M "viva" que é atualizada periodicamente.
    Thread-safe.
    """

    def __init__(
        self,
        intervalo_steps: int = 50,
        metodo: str = "laplace",
        alpha: float = 0.1,
        min_transicoes: int = 20,
    ):
        self.intervalo_steps = intervalo_steps
        self.metodo = metodo
        self.alpha = alpha
        self.min_transicoes = min_transicoes
        self._grafo = construir_grafo_vila()
        self._historico: list[RegistroCalibracao] = []
        self._lock = threading.Lock()
        self._ultimo_step_calibrado = 0

    def grafo_atual(self) -> GrafoPsicohistoria:
        with self._lock:
            return self._grafo

    def matriz_atual(self) -> np.ndarray:
        with self._lock:
            return self._grafo.matriz.copy()

    def talvez_calibrar(self, step: int, trajetoria: list[str]) -> RegistroCalibracao | None:
        """
        Chama a cada step. Dispara recalibração se passou intervalo e dados suficientes.
        Retorna RegistroCalibracao se calibrou; None caso contrário.
        """
        with self._lock:
            if step - self._ultimo_step_calibrado < self.intervalo_steps:
                return None
            if len(trajetoria) < self.min_transicoes:
                return None
            return self._calibrar_locked(step, trajetoria)

    def _calibrar_locked(self, step: int, trajetoria: list[str]) -> RegistroCalibracao:
        pp_antes = perplexity(trajetoria, self._grafo.matriz, self._grafo)
        r = calibrar(trajetoria, metodo=self.metodo, alpha=self.alpha)
        pp_depois = perplexity(trajetoria, r.matriz_calibrada, self._grafo)
        # Atualiza matriz viva
        self._grafo.matriz = r.matriz_calibrada
        reg = RegistroCalibracao(
            step=step,
            n_transicoes=r.n_transicoes,
            cobertura_pct=r.cobertura_pct,
            divergencia_frobenius=r.divergencia_frobenius,
            perplexity_antes=pp_antes,
            perplexity_depois=pp_depois,
        )
        self._historico.append(reg)
        self._historico = self._historico[-50:]  # podagem
        self._ultimo_step_calibrado = step
        return reg

    def historico(self) -> list[RegistroCalibracao]:
        with self._lock:
            return list(self._historico)

    def stats(self) -> dict:
        with self._lock:
            ultimo = self._historico[-1] if self._historico else None
            return {
                "n_calibracoes": len(self._historico),
                "intervalo_steps": self.intervalo_steps,
                "metodo": self.metodo,
                "ultimo_step_calibrado": self._ultimo_step_calibrado,
                "ultima_calibracao": {
                    "step": ultimo.step,
                    "perplexity_antes": ultimo.perplexity_antes,
                    "perplexity_depois": ultimo.perplexity_depois,
                    "ganho_pct": (ultimo.perplexity_antes - ultimo.perplexity_depois) / ultimo.perplexity_antes * 100 if ultimo.perplexity_antes > 0 else 0,
                } if ultimo else None,
            }


AUTO_CALIBRADOR_GLOBAL = AutoCalibrador()
