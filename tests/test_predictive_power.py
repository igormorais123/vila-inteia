"""Testes Onda 82: predictive power scoring."""

from __future__ import annotations
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
from engine.predictive_power import (
    avaliar_predictive_power, brier_score, log_loss,
    accuracy_top1, skill_score,
)

ok, fail = 0, 0


def teste(nome, cond, det=""):
    global ok, fail
    if cond: ok += 1; print(f"  OK  {nome}")
    else:    fail += 1; print(f"  FAIL {nome} {det}")


def t_brier_perfeita_zero():
    p = np.array([0, 1, 0, 0])
    teste("brier perfeita = 0", brier_score(p, 1) == 0.0)


def t_brier_pior_max():
    p = np.array([1, 0, 0, 0])
    teste("brier péssima > 1", brier_score(p, 1) > 1.0)


def t_log_loss_perfeita_zero():
    p = np.array([0, 1, 0, 0])
    teste("log_loss perfeita ≈ 0", log_loss(p, 1) < 1e-9)


def t_log_loss_zero_clipped():
    p = np.array([1, 0, 0, 0])
    teste("log_loss prob 0 não inf", log_loss(p, 1) > 0 and log_loss(p, 1) < 100)


def t_accuracy_match():
    p = np.array([0.1, 0.7, 0.2])
    teste("accuracy top-1 acerta", accuracy_top1(p, 1) == 1)
    teste("accuracy top-1 erra", accuracy_top1(p, 0) == 0)


def t_skill_score_modelo_melhor():
    teste("skill > 0 quando modelo<baseline", skill_score(0.2, 0.5) > 0)


def t_skill_score_modelo_pior():
    teste("skill < 0 quando modelo>baseline", skill_score(0.5, 0.2) < 0)


def t_avaliar_estados_vazios():
    out = avaliar_predictive_power([])
    teste("vazio: n_predicoes=0", out["n_predicoes"] == 0)
    teste("vazio: aviso presente", "aviso" in out)


def t_avaliar_estados_validos():
    estados = ["bootstrap", "expansao", "expansao", "equilibrio", "expansao"]
    out = avaliar_predictive_power(estados)
    teste("n_predicoes=4", out["n_predicoes"] == 4)
    teste("markov dict completo", set(out["markov"].keys()) ==
          {"brier_avg", "log_loss_avg", "accuracy"})
    teste("random dict completo", set(out["random"].keys()) ==
          {"brier_avg", "log_loss_avg", "accuracy"})
    teste("skill_brier_vs_random presente", "skill_brier_vs_random" in out)
    teste("skill_logloss_vs_naive presente", "skill_logloss_vs_naive" in out)


def t_estados_invalidos_ignorados():
    estados = ["bootstrap", "expansao", "estado_inexistente", "equilibrio"]
    out = avaliar_predictive_power(estados)
    teste("invalidos filtrados (3 validos → 2 predicoes)",
          out["n_predicoes"] == 2)


def t_markov_supera_random_em_estados_estaveis():
    """Em estados onde transicao concentra prob, Markov bate random."""
    estados = ["expansao"] * 10 + ["equilibrio"] * 10
    out = avaliar_predictive_power(estados)
    teste("markov brier ≤ random brier",
          out["markov"]["brier_avg"] <= out["random"]["brier_avg"])


def t_naive_perfeito_em_estado_estavel():
    """Naive (último estado) acerta 100% se estado não muda."""
    estados = ["expansao"] * 10
    out = avaliar_predictive_power(estados)
    teste("naive accuracy = 1.0 em estado fixo",
          out["naive_last_state"]["accuracy"] == 1.0)


def main():
    print("=== test_predictive_power ===")
    for fn in [t_brier_perfeita_zero, t_brier_pior_max,
               t_log_loss_perfeita_zero, t_log_loss_zero_clipped,
               t_accuracy_match, t_skill_score_modelo_melhor,
               t_skill_score_modelo_pior, t_avaliar_estados_vazios,
               t_avaliar_estados_validos, t_estados_invalidos_ignorados,
               t_markov_supera_random_em_estados_estaveis,
               t_naive_perfeito_em_estado_estavel]:
        try: fn()
        except Exception as e:
            global fail; fail += 1
            print(f"  FAIL {fn.__name__}: {type(e).__name__}: {e}")
            import traceback; traceback.print_exc()
    print(f"\n{ok} ok, {fail} fail")
    sys.exit(0 if fail == 0 else 1)


if __name__ == "__main__":
    main()
