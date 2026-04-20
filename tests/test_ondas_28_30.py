"""Testes Ondas 28-30: causalidade + comparativo + CLI."""

from __future__ import annotations
import sys, os, subprocess
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np

from engine.causalidade import intervir, counterfactual, ate, intervention_sweep
from engine.comparativo import (
    ConfigSimComparativa, rodar_comparativo, comparar_trajetorias, diferenca_convergencia,
)
from engine.psicohistoria.replay import ExportRun

ok, fail = 0, 0


def teste(nome, cond, det=""):
    global ok, fail
    if cond: ok += 1; print(f"  OK  {nome}")
    else:    fail += 1; print(f"  FAIL {nome} {det}")


# ========== Onda 28: Causalidade ==========

def t_intervir_cria_self_loop():
    M = np.array([[0.5, 0.5], [0.3, 0.7]])
    M_int = intervir(M, 0, 2)
    teste("do(X=0): linha 0 é [1, 0]",
          abs(M_int[0, 0] - 1.0) < 1e-9 and abs(M_int[0, 1]) < 1e-9)
    teste("do(X=0): linha 1 intacta",
          abs(M_int[1, 0] - 0.3) < 1e-9 and abs(M_int[1, 1] - 0.7) < 1e-9)


def t_counterfactual_divergencia():
    # Matriz simples: A → B com alta prob, B → B absorvente
    M = np.array([[0.1, 0.9], [0.0, 1.0]])
    r = counterfactual(M, [0, 1], ponto_intervencao=0, valor_alternativo=1, passos_depois=5)
    teste("counterfactual retorna trajetórias",
          len(r["trajetoria_factual"]) == 6 and len(r["trajetoria_counterfactual"]) == 6)
    teste("estado_original preservado", r["estado_original"] == 0)
    teste("estado_alternativo preservado", r["estado_alternativo"] == 1)


def t_ate_direcao_correta():
    # Treatment = estado 0 (converge rápido para outcome); Control = estado 1 (fica preso)
    # Outcome = estado 0
    M = np.array([[0.9, 0.1], [0.1, 0.9]])
    eff = ate(M, estado_tratamento_idx=0, estado_controle_idx=1,
              estado_outcome_idx=0, horizonte=5)
    # Tratamento inicia em 0 (o outcome), controle em 1; efeito positivo
    teste("ATE positivo quando tratamento=outcome", eff > 0, f"eff={eff}")


def t_intervention_sweep():
    M = np.array([[0.5, 0.5], [0.2, 0.8]])
    r = intervention_sweep(M, estado_outcome_idx=1, horizonte=10)
    teste("sweep retorna 2 resultados", len(r) == 2)
    teste("resultados ordenados por prob outcome",
          r[0].probabilidades_finais[1] >= r[1].probabilidades_finais[1])


# ========== Onda 29: Comparativo ==========

def t_comparar_trajetorias_iguais():
    m = comparar_trajetorias(["a", "b", "a"], ["a", "b", "a"])
    teste("trajetórias iguais: KL ≈ 0", m["kl_divergence"] < 0.01)
    teste("TV ≈ 0", m["total_variation"] < 0.01)


def t_comparar_trajetorias_totalmente_diferentes():
    m = comparar_trajetorias(["a"] * 10, ["b"] * 10)
    teste("trajetórias divergem: TV = 1", abs(m["total_variation"] - 1.0) < 0.01)
    teste("estados totais = 2", m["estados_totais"] == 2)
    teste("estados_comuns = 0", m["estados_comuns"] == 0)


def t_diferenca_convergencia():
    a = {"p1": 0.3, "p2": 0.8}
    b = {"p1": 0.4, "p2": 0.8}
    d = diferenca_convergencia(a, b)
    teste("diferença: média de 0.1 e 0.0 = 0.05", abs(d - 0.05) < 1e-9)


def t_rodar_comparativo_identico():
    run = ExportRun(
        vila_id="a", timestamp_export=0, n_steps=3,
        estados=["x", "y", "z"], steps=[1, 2, 3],
        metricas=[], mules=[], meta={},
    )
    r = rodar_comparativo(run, run)
    teste("rodar comparativo: runs idênticas → conclusão idêntica",
          any("idênticas" in c for c in r.conclusoes),
          f"conclusoes={r.conclusoes}")


# ========== Onda 30: CLI ==========

def t_cli_help():
    r = subprocess.run(
        ["python", "scripts/vila_cli.py", "--help"],
        capture_output=True, text=True, timeout=5,
    )
    teste("CLI --help funciona", r.returncode == 0)
    teste("CLI menciona trajetoria", "trajetoria" in r.stdout)
    teste("CLI menciona calibrar", "calibrar" in r.stdout)


def t_cli_backend_offline():
    # URL fake deve retornar erro graciosamente
    r = subprocess.run(
        ["python", "scripts/vila_cli.py",
         "--url", "http://localhost:9999", "stats"],
        capture_output=True, text=True, timeout=10,
    )
    # Não deve crashar
    teste("CLI backend offline não crasha", r.returncode == 0)


def main():
    print("=== test_ondas_28_30 ===")
    for fn in [t_intervir_cria_self_loop, t_counterfactual_divergencia,
               t_ate_direcao_correta, t_intervention_sweep,
               t_comparar_trajetorias_iguais, t_comparar_trajetorias_totalmente_diferentes,
               t_diferenca_convergencia, t_rodar_comparativo_identico,
               t_cli_help, t_cli_backend_offline]:
        try: fn()
        except Exception as e:
            global fail; fail += 1
            print(f"  FAIL {fn.__name__}: {type(e).__name__}: {e}")
    print(f"\n{ok} ok, {fail} fail")
    sys.exit(0 if fail == 0 else 1)


if __name__ == "__main__":
    main()
