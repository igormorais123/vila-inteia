"""Testes combinados Ondas 13-16."""

from __future__ import annotations
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np

from engine.psicohistoria.calibracao_online import (
    mle_simples, ewma_online, calibrar, perplexity,
)
from engine.psicohistoria.grafo_eventos import construir_grafo_vila
from engine.psicohistoria.persistencia import (
    PersistenciaPsico, RegistroPsico,
)
from engine.psicohistoria.hmm_estados import descobrir_estados, kmeans_simples
from engine.psicohistoria.decision_helper import recomendar_acao, relatorio_estrategico_helena
from engine.psicohistoria.detector_estado_vila import RASTREADOR_GLOBAL, MetricasStep

ok, fail = 0, 0


def teste(nome, cond, det=""):
    global ok, fail
    if cond: ok += 1; print(f"  OK  {nome}")
    else:    fail += 1; print(f"  FAIL {nome} {det}")


# ========== Onda 13 ==========

def t_mle_simples_conta_transicoes():
    g = construir_grafo_vila()
    traj = ["bootstrap", "recrutamento", "expansao", "expansao", "consenso_fragil"]
    M = mle_simples(g, traj, alpha=0.0)
    # Linha bootstrap: 1 transição pra recrutamento
    i_boot = g.estado_para_index("bootstrap")
    j_recr = g.estado_para_index("recrutamento")
    teste("MLE: bootstrap→recrutamento prob 1.0",
          abs(M[i_boot, j_recr] - 1.0) < 1e-9)


def t_ewma_preserva_estocastica():
    g = construir_grafo_vila()
    M = g.matriz.copy()
    M2 = ewma_online(M, ("bootstrap", "expansao"), g, peso_novo=0.1)
    for i in range(M2.shape[0]):
        teste(f"EWMA linha {i} soma 1",
              abs(M2[i].sum() - 1.0) < 1e-6, f"sum={M2[i].sum()}")
        if i >= 1: break  # só 1-2 linhas pra evitar spam


def t_calibrar_retorna_resultado():
    traj = ["bootstrap", "recrutamento", "expansao", "consenso_fragil",
            "equilibrio", "polarizacao", "equilibrio"]
    r = calibrar(traj, metodo="laplace", alpha=0.5)
    teste("calibrar 6 transições", r.n_transicoes == 6)
    teste("cobertura > 60%", r.cobertura_pct > 60, f"cob={r.cobertura_pct}")
    teste("divergência frobenius > 0", r.divergencia_frobenius > 0)


def t_perplexity_decresce_com_calibracao():
    g = construir_grafo_vila()
    # Trajetória que segue fortemente o padrão baseline
    traj = ["bootstrap", "recrutamento", "expansao", "equilibrio",
            "equilibrio", "equilibrio"]
    pp_original = perplexity(traj, g.matriz, g)
    M_calibrada = mle_simples(g, traj, alpha=0.1)
    pp_calibrada = perplexity(traj, M_calibrada, g)
    teste("perplexity cai após calibração",
          pp_calibrada < pp_original, f"orig={pp_original} cal={pp_calibrada}")


# ========== Onda 14 ==========

def t_persistencia_buffer():
    p = PersistenciaPsico(vila_id="test", batch_size=3)
    p.adicionar(RegistroPsico(vila_id="test", step=1, estado="bootstrap"))
    p.adicionar(RegistroPsico(vila_id="test", step=2, estado="recrutamento"))
    s = p.stats()
    teste("buffer tem 2 registros", s["buffer_atual"] == 2)


def t_persistencia_flush_auto():
    p = PersistenciaPsico(vila_id="test", batch_size=2)
    p.adicionar(RegistroPsico(vila_id="test", step=1, estado="a"))
    p.adicionar(RegistroPsico(vila_id="test", step=2, estado="b"))
    # Atingiu batch_size, flush interno
    s = p.stats()
    teste("buffer limpou após batch atingido",
          s["buffer_atual"] == 0, f"buf={s['buffer_atual']}")


def t_persistencia_flush_manual():
    p = PersistenciaPsico(batch_size=100)
    p.adicionar(RegistroPsico(vila_id="x", step=1, estado="a"))
    n = p.flush()
    # Sem Supabase OK, flush retorna 0
    teste("flush manual retorna contagem", n >= 0)


# ========== Onda 15 ==========

def t_kmeans_converge():
    X = np.array([[0, 0], [1, 1], [10, 10], [11, 11]], dtype=float)
    labels, cents, inercia, its = kmeans_simples(X, k=2, seed=1)
    teste("kmeans 2 clusters claros",
          len(set(labels)) == 2, f"labels={labels}")
    teste("kmeans inércia baixa", inercia < 5, f"inercia={inercia}")


def t_descobrir_estados():
    # 20 steps de métricas diversificadas
    metricas = [
        {"n_conversas": i * 2, "n_reflexoes": i % 3,
         "n_agentes_ativos": 50 + i,
         "n_agentes_latentes": 50 - i,
         "polarizacao_media": (i % 10) / 10,
         "gini_economia": 0.3,
         "propostas_constituintes_ativas": 0,
         "contribuicoes_ao_desafio": i}
        for i in range(20)
    ]
    r = descobrir_estados(metricas, k=4, seed=42)
    teste("HMM: 4 estados latentes", r.k == 4)
    teste("HMM: labels por step", len(r.labels_por_step) == 20)
    teste("HMM: 4 centroides", len(r.estados_latentes) == 4)
    teste("HMM: rótulos auto não vazios",
          all(e.rotulo_auto for e in r.estados_latentes))


# ========== Onda 16 ==========

def t_recomendar_sem_dados():
    # Limpa rastreador
    RASTREADOR_GLOBAL.trajetoria.estados = []
    r = recomendar_acao()
    teste("recomendar sem dados retorna aguardar",
          "aguardar" in r.acao_recomendada.lower())
    teste("urgência baixa", r.urgencia == "baixa")


def t_recomendar_com_trajetoria():
    RASTREADOR_GLOBAL.trajetoria.estados = []
    for i in range(10):
        m = MetricasStep(step=i, n_conversas=5, n_reflexoes=1,
                         n_agentes_ativos=80, n_agentes_latentes=20, total_agentes=100,
                         polarizacao_media=0.05)
        RASTREADOR_GLOBAL.registrar_step(m)
    r = recomendar_acao()
    teste("recomendar com trajetória: estado definido",
          r.estado_atual in ("equilibrio", "expansao", "consenso_fragil"))
    teste("recomendar: destino preenchido", r.destino_previsto != "—")
    teste("recomendar: justificativa não vazia", len(r.justificativa) > 20)


def t_relatorio_helena():
    rel = relatorio_estrategico_helena()
    teste("relatório Helena: tipo correto",
          rel["tipo"] == "parecer_psicohistorico")
    teste("relatório Helena: campos essenciais",
          all(k in rel for k in ("estado", "destino", "urgencia",
                                  "recomendacao", "justificativa")))


def main():
    print("=== test_ondas_13_a_16 ===")
    for fn in [t_mle_simples_conta_transicoes, t_ewma_preserva_estocastica,
               t_calibrar_retorna_resultado, t_perplexity_decresce_com_calibracao,
               t_persistencia_buffer, t_persistencia_flush_auto, t_persistencia_flush_manual,
               t_kmeans_converge, t_descobrir_estados,
               t_recomendar_sem_dados, t_recomendar_com_trajetoria, t_relatorio_helena]:
        try: fn()
        except Exception as e:
            global fail; fail += 1
            print(f"  FAIL {fn.__name__}: {type(e).__name__}: {e}")
    print(f"\n{ok} ok, {fail} fail")
    sys.exit(0 if fail == 0 else 1)


if __name__ == "__main__":
    main()
