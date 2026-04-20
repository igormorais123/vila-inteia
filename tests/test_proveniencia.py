"""
Testes proveniência + backtest (Onda 5).
Rodar: PYTHONPATH=. python tests/test_proveniencia.py
"""

from __future__ import annotations

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.proveniencia import construir_proveniencia, hash_trace, hash_materia
from engine.backtest import brier_score, log_loss, accuracy_binaria, rodar_backtest

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


def t_proveniencia_basica():
    traces = [
        {"trace_id": "t1", "fase": "perceber", "agente_id": "sun_tzu",
         "duracao_ms": 120, "tokens_consumidos": 50, "custo_usd": 0.001,
         "resultado": "sucesso", "causal_parent": None},
        {"trace_id": "t2", "fase": "planejar", "agente_id": "sun_tzu",
         "duracao_ms": 200, "tokens_consumidos": 120, "custo_usd": 0.004,
         "resultado": "sucesso", "causal_parent": "t1"},
    ]
    p = construir_proveniencia("materia_01", traces)
    teste("2 traces, raiz = t1", p.raiz and p.raiz.trace_id == "t1")
    teste("t1 tem t2 como filho",
          len(p.raiz.filhos) == 1 and p.raiz.filhos[0].trace_id == "t2")
    teste("tokens totais 170", p.tokens_totais == 170)
    teste("custo agregado ≈ 0.005", abs(p.custo_usd_total - 0.005) < 1e-9)
    teste("fases cobertas 2", set(p.fases_cobertas) == {"perceber", "planejar"})


def t_hash_determinista():
    traces = [{"trace_id": "t1", "fase": "sintetizar", "agente_id": "a",
               "tokens_consumidos": 100, "custo_usd": 0.01, "resultado": "sucesso"}]
    p1 = construir_proveniencia("m1", traces)
    h1 = hash_trace(p1)
    p2 = construir_proveniencia("m1", traces)
    h2 = hash_trace(p2)
    teste("hash determinístico", h1 == h2)
    teste("hash tem 64 chars (SHA-256 hex)", len(h1) == 64)


def t_hash_materia_combina():
    h = hash_materia("conteúdo da matéria", "abc123")
    teste("hash_materia 64 chars", len(h) == 64)


def t_influencias():
    traces = [{"trace_id": "t1", "fase": "conversar", "agente_id": "a",
               "tokens_consumidos": 1, "custo_usd": 0.0, "resultado": "sucesso"}]
    citacoes = [("a", "b"), ("a", "b"), ("b", "c")]
    p = construir_proveniencia("m", traces, ["a", "b", "c"], citacoes)
    teste("3 citações → 2 arestas únicas", len(p.grafo_influencia) == 2)
    pesos = {(i.agente_origem, i.agente_destino): i.peso for i in p.grafo_influencia}
    teste("a→b peso maior", pesos.get(("a", "b"), 0) > pesos.get(("b", "c"), 0))


def t_brier_perfeito():
    # Prob=1 quando y=1, prob=0 quando y=0 → Brier=0
    teste("Brier perfeito = 0",
          abs(brier_score([1.0, 0.0, 1.0, 0.0], [1, 0, 1, 0])) < 1e-9)


def t_brier_random():
    # Prob=0.5 para tudo → Brier=0.25
    teste("Brier random = 0.25",
          abs(brier_score([0.5] * 4, [0, 1, 0, 1]) - 0.25) < 1e-9)


def t_log_loss_range():
    ll = log_loss([0.9, 0.1, 0.9, 0.1], [1, 0, 1, 0])
    teste("log_loss confiante correto é baixo", ll < 0.2, f"ll={ll}")


def t_accuracy_binaria():
    acc = accuracy_binaria([0.9, 0.1, 0.6, 0.4], [1, 0, 1, 0])
    teste("accuracy binária", abs(acc - 1.0) < 1e-9)


def t_backtest_seed_dataset():
    try:
        r = rodar_backtest("seed_eleicao_municipal_sp_2024", n_sims=1,
                           base_dir="data/backtest")
        teste(f"backtest dataset seed (n={r.n_eventos})", r.n_eventos == 10)
        teste("brier em [0, 1]", 0 <= r.brier <= 1, f"brier={r.brier}")
        teste("accuracy em [0, 1]", 0 <= r.accuracy <= 1)
        teste("10 predições", len(r.predicoes) == 10)
    except FileNotFoundError as e:
        print(f"  SKIP {e}")


def main():
    print("=== test_proveniencia ===")
    for fn in [
        t_proveniencia_basica,
        t_hash_determinista,
        t_hash_materia_combina,
        t_influencias,
        t_brier_perfeito,
        t_brier_random,
        t_log_loss_range,
        t_accuracy_binaria,
        t_backtest_seed_dataset,
    ]:
        try:
            fn()
        except Exception as e:
            global fail
            fail += 1
            print(f"  FAIL {fn.__name__}: {type(e).__name__}: {e}")

    print(f"\n{ok} ok, {fail} fail")
    sys.exit(0 if fail == 0 else 1)


if __name__ == "__main__":
    main()
