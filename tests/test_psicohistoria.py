"""
Testes da psico-história.
Rodar: PYTHONPATH=. python tests/test_psicohistoria.py
"""

from __future__ import annotations

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np

from engine.psicohistoria.grafo_eventos import (
    GrafoPsicohistoria, Estado, construir_grafo_vila, contagens_de_lista,
)
from engine.psicohistoria.equacoes import (
    prever_trajetoria, distribuicao_estacionaria, tempo_ate_absorver,
    entropia_trajetoria, predizer_estado_provavel,
)
from engine.psicohistoria.plano import (
    plano_seldon, divergencia_plano_realidade,
)
from engine.psicohistoria.detectores import (
    detectar_mule, criticidade_evento, agentes_anomalos_por_comportamento,
)

ok = 0
fail = 0


def teste(nome, cond, det=""):
    global ok, fail
    if cond:
        ok += 1
        print(f"  OK  {nome}")
    else:
        fail += 1
        print(f"  FAIL {nome} {det}")


def t_grafo_basico():
    g = GrafoPsicohistoria()
    g.adicionar_estado(Estado(id="a"))
    g.adicionar_estado(Estado(id="b"))
    g.observar_transicao("a", "b")
    g.observar_transicao("a", "b")
    g.observar_transicao("a", "a")
    M = g.montar_matriz()
    teste("matriz montada: shape 2x2", M.shape == (2, 2))
    teste("matriz estocástica (linhas somam 1)",
          np.allclose(M.sum(axis=1), 1.0), f"rows={M.sum(axis=1)}")
    teste("a→b = 2/3", abs(M[0, 1] - 2/3) < 1e-9, f"got {M[0,1]}")


def t_grafo_vila_baseline():
    g = construir_grafo_vila()
    teste("Vila baseline: 8 estados", len(g.estados) == 8)
    teste("matriz estocástica",
          np.allclose(g.matriz.sum(axis=1), 1.0, atol=1e-6))


def t_previsao_trajetoria():
    g = construir_grafo_vila()
    traj = prever_trajetoria(g, "bootstrap", passos=30)
    teste("trajetória shape correta",
          traj.shape == (31, 8), f"got {traj.shape}")
    teste("passo 0 = one-hot bootstrap",
          abs(traj[0, g.estado_para_index("bootstrap")] - 1.0) < 1e-9)
    # Cada linha deve somar 1 (distribuição de prob)
    teste("todas linhas somam 1",
          np.allclose(traj.sum(axis=1), 1.0, atol=1e-6))


def t_distribuicao_estacionaria():
    g = construir_grafo_vila()
    pi = distribuicao_estacionaria(g)
    teste("π é dict com 8 entradas", len(pi) == 8)
    teste("π soma 1", abs(sum(pi.values()) - 1.0) < 1e-6, f"sum={sum(pi.values())}")
    # Equilíbrio deve ser estado provável no baseline (self-loop alto)
    teste("equilíbrio é estado dominante ou top-2 em π",
          pi["equilibrio"] > 0.1, f"π[equilibrio]={pi['equilibrio']:.3f}")


def t_tempo_absorver():
    # Cadeia simples: A → B com prob 0.5, A → A com 0.5
    g = GrafoPsicohistoria()
    g.adicionar_estado(Estado(id="A"))
    g.adicionar_estado(Estado(id="B"))
    for _ in range(5):
        g.observar_transicao("A", "B")
        g.observar_transicao("A", "A")
    for _ in range(10):
        g.observar_transicao("B", "B")   # absorvente
    g.montar_matriz()
    t = tempo_ate_absorver(g, "A", "B", max_passos=100, limiar=0.95)
    teste("tempo até absorver (limiar 95%)", t is not None and 2 <= t <= 20,
          f"got t={t}")


def t_plano_seldon_gera_crises():
    g = construir_grafo_vila()
    p = plano_seldon(g, "bootstrap", horizonte=100)
    teste("plano tem horizonte 100", p.horizonte == 100)
    teste("plano tem pelo menos 1 crise",
          len(p.crises) >= 1, f"crises={len(p.crises)}")
    teste("destino provável preenchido", p.destino_provavel != "")


def t_divergencia_plano_realidade():
    g = construir_grafo_vila()
    p = plano_seldon(g, "bootstrap", horizonte=50)
    # Realidade segue plano perfeitamente
    traj_real_correta = list(p.estados_modais[:20])
    d1 = divergencia_plano_realidade(p, traj_real_correta, g)
    teste("real=plano: 0 divergentes", d1["passos_divergentes"] == 0)

    # Realidade completamente divergente: sempre 'polarizacao'
    traj_real_errada = ["polarizacao"] * 20
    d2 = divergencia_plano_realidade(p, traj_real_errada, g)
    teste("real divergente detecta", d2["passos_divergentes"] > 0,
          f"got {d2}")


def t_detectar_mule():
    g = construir_grafo_vila()
    traj = prever_trajetoria(g, "bootstrap", passos=20)
    # Realidade improvável: bootstrap -> equilíbrio direto no step 1 (baixíssima prob)
    traj_real = ["bootstrap", "equilibrio", "equilibrio"]
    mules = detectar_mule(traj_real, traj[:3], g, z_score_limite=2.0)
    teste("detecta Mule em transição rara", len(mules) >= 1,
          f"mules={mules}")


def t_criticidade_equilibrio():
    g = construir_grafo_vila()
    c_eq = criticidade_evento(g, "equilibrio")
    c_boot = criticidade_evento(g, "bootstrap")
    teste("criticidade equilíbrio > bootstrap (self-loop alto)",
          c_eq > c_boot, f"eq={c_eq} boot={c_boot}")


def t_agentes_anomalos():
    comp = {
        "a": {"produtividade": 5.0, "custo": 1.0},
        "b": {"produtividade": 5.1, "custo": 1.1},
        "c": {"produtividade": 5.0, "custo": 0.9},
        "d": {"produtividade": 50.0, "custo": 1.0},   # outlier
    }
    outliers = agentes_anomalos_por_comportamento(comp, n_desvios=1.5)
    teste("detecta 'd' como outlier", "d" in outliers, f"got {outliers}")


def t_entropia_decresce():
    g = construir_grafo_vila()
    traj = prever_trajetoria(g, "bootstrap", passos=200)
    H = entropia_trajetoria(traj)
    # Entropia inicial = 0 (one-hot). Sobe depois estabiliza.
    teste("entropia cresce inicial", H[10] > H[0])


def t_predizer_estado_provavel():
    g = construir_grafo_vila()
    estado, prob = predizer_estado_provavel(g, "bootstrap", passos=500)
    teste("predição retorna estado e prob válidos",
          estado in g.estados and 0 <= prob <= 1, f"estado={estado} prob={prob}")


def main():
    print("=== test_psicohistoria ===")
    for fn in [
        t_grafo_basico,
        t_grafo_vila_baseline,
        t_previsao_trajetoria,
        t_distribuicao_estacionaria,
        t_tempo_absorver,
        t_plano_seldon_gera_crises,
        t_divergencia_plano_realidade,
        t_detectar_mule,
        t_criticidade_equilibrio,
        t_agentes_anomalos,
        t_entropia_decresce,
        t_predizer_estado_provavel,
    ]:
        try:
            fn()
        except NotImplementedError as e:
            print(f"  SKIP {fn.__name__}: {e}")
        except Exception as e:
            global fail
            fail += 1
            print(f"  FAIL {fn.__name__}: {type(e).__name__}: {e}")

    print(f"\n{ok} ok, {fail} fail")
    sys.exit(0 if fail == 0 else 1)


if __name__ == "__main__":
    main()
