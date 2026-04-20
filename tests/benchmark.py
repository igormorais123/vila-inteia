"""
Benchmark suite perf (Onda 41).

Mede latências dos subsistemas principais:
    - game_theory solvers
    - opinion_dynamics
    - psicohistoria (prever, plano_seldon, detector_estado)
    - calibracao_online
    - hmm_descobrir
    - auto_calibrador
    - grafo extração
    - meta-análise

Não é test unit — roda via: PYTHONPATH=. python tests/benchmark.py

Output: markdown table com latência por operação.
"""

from __future__ import annotations

import sys
import os
import time
from dataclasses import dataclass

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np


@dataclass
class Resultado:
    nome: str
    iteracoes: int
    tempo_total_ms: float
    latencia_media_ms: float
    ops_por_segundo: float


resultados: list[Resultado] = []


def bench(nome: str, iteracoes: int = 100):
    """Decorator que mede tempo."""
    def wrapper(fn):
        def executar():
            ini = time.perf_counter()
            for _ in range(iteracoes):
                fn()
            fim = time.perf_counter()
            total_ms = (fim - ini) * 1000
            avg_ms = total_ms / iteracoes
            ops = 1000 / avg_ms if avg_ms > 0 else float("inf")
            r = Resultado(nome, iteracoes, total_ms, avg_ms, ops)
            resultados.append(r)
            return r
        return executar
    return wrapper


# =================== Game theory ===================

@bench("game_theory.nash_puro (2×2)", 1000)
def b_nash_puro():
    from engine.game_theory.equilibrio import nash_puro
    A = np.array([[3, 0], [5, 1]])
    B = np.array([[3, 5], [0, 1]])
    nash_puro(A, B)


@bench("game_theory.replicator (10 iter)", 500)
def b_replicator():
    from engine.game_theory.evolutivo import replicator_convergencia
    pop = np.array([0.3, 0.3, 0.4])
    payoffs = np.array([[2, 1, 0], [1, 2, 1], [0, 1, 2]])
    replicator_convergencia(pop, payoffs, max_iter=10)


@bench("game_theory.torneio_axelrod (5×5, 50 rodadas)", 20)
def b_axelrod():
    from engine.game_theory.jogos_repetidos import (
        tit_for_tat, grim_trigger, sempre_cooperar, sempre_trair,
        tit_for_two_tats, torneio_axelrod,
    )
    estrats = {"tft": tit_for_tat, "grim": grim_trigger, "coop": sempre_cooperar,
                "trair": sempre_trair, "tft2": tit_for_two_tats}
    torneio_axelrod(estrats, rodadas=50)


# =================== Opinion dynamics ===================

@bench("opinion_dynamics.degroot_convergencia (5×5, 100 iter)", 500)
def b_degroot():
    from engine.opinion_dynamics.degroot import degroot_convergencia
    W = np.random.rand(5, 5)
    W = W / W.sum(axis=1, keepdims=True)
    x0 = np.random.rand(5)
    degroot_convergencia(x0, W, max_iter=100)


@bench("opinion_dynamics.deffuant (40 agentes, 1000 passos)", 20)
def b_deffuant():
    from engine.opinion_dynamics.bounded_confidence import deffuant_simular
    x0 = np.linspace(0, 1, 40)
    deffuant_simular(x0, epsilon=0.3, mu=0.5, passos=1000, seed=42)


# =================== Psico-história ===================

@bench("psicohistoria.prever_trajetoria (50 passos)", 500)
def b_prever():
    from engine.psicohistoria import construir_grafo_vila, prever_trajetoria
    g = construir_grafo_vila()
    prever_trajetoria(g, "bootstrap", passos=50)


@bench("psicohistoria.plano_seldon (horizonte 100)", 300)
def b_plano():
    from engine.psicohistoria import construir_grafo_vila, plano_seldon
    g = construir_grafo_vila()
    plano_seldon(g, "bootstrap", horizonte=100)


@bench("psicohistoria.classificar_estado", 10000)
def b_classificar():
    from engine.psicohistoria.detector_estado_vila import classificar_estado, MetricasStep
    m = MetricasStep(step=50, n_conversas=30, n_reflexoes=5,
                     n_agentes_ativos=80, n_agentes_latentes=20, total_agentes=100,
                     contribuicoes_ao_desafio=25)
    classificar_estado(m)


# =================== Calibração ===================

@bench("calibracao.mle_simples (200 estados)", 300)
def b_mle():
    from engine.psicohistoria.grafo_eventos import construir_grafo_vila
    from engine.psicohistoria.calibracao_online import mle_simples
    g = construir_grafo_vila()
    traj = ["expansao", "equilibrio"] * 100
    mle_simples(g, traj, alpha=0.1)


# =================== HMM ===================

@bench("hmm.descobrir_estados (20 steps, k=4)", 50)
def b_hmm():
    from engine.psicohistoria.hmm_estados import descobrir_estados
    metricas = [
        {"n_conversas": i, "n_reflexoes": i % 3, "n_agentes_ativos": 80,
         "n_agentes_latentes": 20, "polarizacao_media": 0.1,
         "gini_economia": 0.3, "propostas_constituintes_ativas": 0,
         "contribuicoes_ao_desafio": i}
        for i in range(20)
    ]
    descobrir_estados(metricas, k=4)


# =================== Grafo ===================

@bench("memoria.grafo.indexar_texto (1 sentença)", 500)
def b_grafo():
    from engine.memoria.grafo import GrafoConhecimento, indexar_texto
    g = GrafoConhecimento()
    indexar_texto(g, "Sun Tzu e Cleópatra conversaram com Alexandre.")


# =================== Causalidade ===================

@bench("causalidade.intervention_sweep (8 estados)", 200)
def b_sweep():
    from engine.causalidade import intervention_sweep
    from engine.psicohistoria import construir_grafo_vila
    g = construir_grafo_vila()
    intervention_sweep(g.matriz, estado_outcome_idx=0, horizonte=10)


# =================== Runner ===================

def main():
    benches = [
        b_nash_puro, b_replicator, b_axelrod,
        b_degroot, b_deffuant,
        b_prever, b_plano, b_classificar,
        b_mle, b_hmm, b_grafo, b_sweep,
    ]
    print("Running benchmarks...\n")
    for b in benches:
        b()
        r = resultados[-1]
        print(f"  {r.nome:<50} {r.latencia_media_ms:8.3f}ms  ({r.ops_por_segundo:>10.1f} ops/s)")

    print("\n| Operação | Iter | Latência (ms) | Ops/s |")
    print("|---|---:|---:|---:|")
    for r in resultados:
        print(f"| {r.nome} | {r.iteracoes} | {r.latencia_media_ms:.3f} | {r.ops_por_segundo:.1f} |")


if __name__ == "__main__":
    main()
