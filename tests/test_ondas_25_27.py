"""Testes Ondas 25-27: tuner + SSE stream + backtest comparativo."""

from __future__ import annotations
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.psicohistoria.tuner_classificador import (
    ThresholdsClassificador, classificar_com_thresholds,
    entropia_distribuicao, grid_search_thresholds,
)
from engine.psicohistoria.detector_estado_vila import MetricasStep

ok, fail = 0, 0


def teste(nome, cond, det=""):
    global ok, fail
    if cond: ok += 1; print(f"  OK  {nome}")
    else:    fail += 1; print(f"  FAIL {nome} {det}")


# ========== Onda 25 ==========

def t_classificar_com_thresholds_default():
    t = ThresholdsClassificador()
    m = MetricasStep(step=5, n_conversas=0, n_reflexoes=0,
                     n_agentes_ativos=20, n_agentes_latentes=0, total_agentes=100)
    teste("thresholds default → bootstrap",
          classificar_com_thresholds(m, t) == "bootstrap")


def t_classificar_com_thresholds_custom():
    # Thresholds que fazem contrib>5 já expansão
    t = ThresholdsClassificador(
        expansao_contribs_min=5, expansao_ativos_frac_min=0.5,
    )
    m = MetricasStep(step=50, n_conversas=30, n_reflexoes=5,
                     n_agentes_ativos=80, n_agentes_latentes=20, total_agentes=100,
                     contribuicoes_ao_desafio=10)
    teste("thresholds custom → expansao", classificar_com_thresholds(m, t) == "expansao")


def t_entropia_concentrado():
    teste("entropia concentrada = 0",
          entropia_distribuicao(["expansao"] * 10) < 0.01)


def t_entropia_balanceada():
    estados = ["bootstrap", "recrutamento", "expansao", "consenso_fragil",
               "polarizacao", "crise_economica", "renovacao_constituinte", "equilibrio"]
    e = entropia_distribuicao(estados)
    teste("entropia 8 estados únicos ~ 1", abs(e - 1.0) < 0.01, f"got {e}")


def t_grid_search_melhora_entropia():
    # Cria 30 métricas com variedade
    metricas = []
    for i in range(30):
        m = MetricasStep(
            step=i * 10, n_conversas=i * 2, n_reflexoes=i % 3,
            n_agentes_ativos=50 + i, n_agentes_latentes=50 - i,
            total_agentes=100,
            polarizacao_media=(i % 5) * 0.15,
            gini_economia=(i % 3) * 0.3,
            contribuicoes_ao_desafio=i * 3,
        )
        metricas.append(m)
    r = grid_search_thresholds(metricas, n_grid=3)
    teste("grid search: entropia ótima >= default",
          r.entropia_otima >= r.entropia_default - 1e-9,
          f"otima={r.entropia_otima} default={r.entropia_default}")
    teste("grid search: testa múltiplos", r.n_testados > 1)


def t_grid_search_preserva_thresholds_validos():
    metricas = [MetricasStep(step=i, n_conversas=5, n_reflexoes=1,
                               n_agentes_ativos=80, n_agentes_latentes=20,
                               total_agentes=100, polarizacao_media=0.25)
                for i in range(20)]
    r = grid_search_thresholds(metricas, n_grid=2)
    t = r.thresholds_otimos
    teste("thresholds válidos: cf_min < cf_max",
          t.consenso_fragil_min < t.consenso_fragil_max)


# ========== Onda 27 ==========

def t_backtest_comparativo_todos_datasets():
    from engine.backtest import rodar_backtest
    from pathlib import Path
    base = Path("data/backtest")
    datasets = sorted([p.stem for p in base.glob("*.csv")])
    teste("≥5 datasets presentes", len(datasets) >= 5, f"got {len(datasets)}")
    resultados = []
    for d in datasets:
        r = rodar_backtest(d, n_sims=1)
        resultados.append((d, r.brier, r.accuracy))
    for d, b, a in resultados:
        teste(f"{d}: brier válido", 0 <= b <= 1, f"brier={b}")
        teste(f"{d}: accuracy válida", 0 <= a <= 1, f"acc={a}")


def main():
    print("=== test_ondas_25_27 ===")
    for fn in [t_classificar_com_thresholds_default, t_classificar_com_thresholds_custom,
               t_entropia_concentrado, t_entropia_balanceada,
               t_grid_search_melhora_entropia, t_grid_search_preserva_thresholds_validos,
               t_backtest_comparativo_todos_datasets]:
        try: fn()
        except Exception as e:
            global fail; fail += 1
            print(f"  FAIL {fn.__name__}: {type(e).__name__}: {e}")
    print(f"\n{ok} ok, {fail} fail")
    sys.exit(0 if fail == 0 else 1)


if __name__ == "__main__":
    main()
