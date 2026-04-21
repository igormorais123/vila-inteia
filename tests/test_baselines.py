"""Testes Onda 118: simple baselines."""

from __future__ import annotations
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.baselines import (
    base_rate, last_value, markov_1_order, exp_smoothing,
    comparar_baselines,
)

ok, fail = 0, 0


def teste(nome, cond, det=""):
    global ok, fail
    if cond: ok += 1; print(f"  OK  {nome}")
    else:    fail += 1; print(f"  FAIL {nome} {det}")


def t_base_rate_vazio():
    teste("vazio retorna default", base_rate([]) == 0.5)


def t_base_rate_metade():
    teste("[1,0,1,0] = 0.5", base_rate([1,0,1,0]) == 0.5)
    teste("[1,1,1] = 1.0", base_rate([1,1,1]) == 1.0)


def t_last_value():
    teste("último é 0", last_value([1,1,0]) == 0.0)
    teste("vazio default", last_value([]) == 0.5)


def t_markov_1_curto():
    teste("len<2 = 0.5", markov_1_order([1]) == 0.5)


def t_markov_1_basico():
    # 1→1 duas vezes, nunca 1→0 → com Laplace 1.0: (2+1)/(2+2) = 0.75
    out = markov_1_order([1,1,1], laplace=1.0)
    teste("P(1|1) alto com persistência", out > 0.5)


def t_exp_smoothing_convergencia():
    out = exp_smoothing([1,1,1,1,1], alpha=0.5)
    teste("y=1 const → ≈1", out > 0.9)


def t_comparar_baselines_chaves():
    probs = [0.8, 0.7, 0.9, 0.3, 0.4]
    y = [1, 1, 1, 0, 0]
    r = comparar_baselines(probs, y)
    teste("tem metodos dict", "metodos" in r)
    teste("vila presente", "vila" in r["metodos"])
    teste("base_rate presente", "base_rate" in r["metodos"])
    teste("ranking ordenado", r["ranking_brier_asc"][0]["brier"] <=
          r["ranking_brier_asc"][-1]["brier"])


def t_comparar_com_priors():
    probs = [0.8, 0.7]
    y = [1, 1]
    priors = [0.6, 0.65]
    r = comparar_baselines(probs, y, priors=priors)
    teste("prior_humano presente", "prior_humano" in r["metodos"])
    teste("skill vs prior humano", "skill_vila_vs_prior_humano" in r)


def t_n_insuficiente():
    r = comparar_baselines([0.5], [1])
    teste("n<2: erro", "erro" in r)


def main():
    print("=== test_baselines ===")
    for fn in [t_base_rate_vazio, t_base_rate_metade, t_last_value,
               t_markov_1_curto, t_markov_1_basico,
               t_exp_smoothing_convergencia,
               t_comparar_baselines_chaves, t_comparar_com_priors,
               t_n_insuficiente]:
        try: fn()
        except Exception as e:
            global fail; fail += 1
            print(f"  FAIL {fn.__name__}: {type(e).__name__}: {e}")
            import traceback; traceback.print_exc()
    print(f"\n{ok} ok, {fail} fail")
    sys.exit(0 if fail == 0 else 1)


if __name__ == "__main__":
    main()
