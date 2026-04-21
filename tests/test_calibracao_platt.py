"""Testes Onda 93: Platt calibração."""

from __future__ import annotations
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.calibracao_platt import (
    fit_platt, aplicar_platt, brier, log_loss, ece, avaliar_calibracao,
)

ok, fail = 0, 0


def teste(nome, cond, det=""):
    global ok, fail
    if cond: ok += 1; print(f"  OK  {nome}")
    else:    fail += 1; print(f"  FAIL {nome} {det}")


def t_brier_simples():
    teste("brier 0.8,1 = 0.04", abs(brier([0.8], [1]) - 0.04) < 1e-9)
    teste("brier 0.5,1 = 0.25", abs(brier([0.5], [1]) - 0.25) < 1e-9)


def t_log_loss_simples():
    teste("log_loss cert correto ≈ 0", log_loss([0.99], [1]) < 0.02)
    teste("log_loss cert errado alto", log_loss([0.01], [1]) > 3)


def t_ece_perfeita():
    # 10 previsões a 0.5, metade acerta → ece ≈ 0
    probs = [0.5] * 10
    y = [1, 1, 1, 1, 1, 0, 0, 0, 0, 0]
    teste("ece ~0 se prob = freq", ece(probs, y) < 0.01)


def t_ece_descalibrado():
    # Todos 0.9, mas só metade acerta → ece ≈ 0.4
    probs = [0.9] * 10
    y = [1]*5 + [0]*5
    teste("ece ~0.4 over-confident", abs(ece(probs, y) - 0.4) < 0.05)


def t_platt_fit_roda_sem_erro():
    probs = [0.8, 0.9, 0.7, 0.6, 0.85, 0.75]
    y = [1, 1, 0, 0, 1, 1]
    a, b = fit_platt(probs, y)
    teste("a float", isinstance(a, float))
    teste("b float", isinstance(b, float))


def t_platt_reduz_over_confidence():
    # Vila over-confident: sempre 0.9, real 50/50
    import random
    random.seed(42)
    probs = [0.9] * 40
    y = [1 if i % 2 == 0 else 0 for i in range(40)]
    a, b = fit_platt(probs, y)
    p_cal = aplicar_platt(probs, a, b)
    media_cal = sum(p_cal) / len(p_cal)
    teste(f"calibração baixa prob (média {media_cal:.2f} → ~0.5)",
           0.3 < media_cal < 0.7)


def t_avaliar_calibracao_melhora_ece():
    probs = [0.9] * 20
    y = [1]*10 + [0]*10
    r = avaliar_calibracao(probs, y)
    teste("ece_antes alto", r["ece_antes"] > 0.3)
    teste("ece_depois menor que antes",
           r["ece_depois"] <= r["ece_antes"])
    teste("brier_depois menor que antes",
           r["brier_depois"] <= r["brier_antes"])


def t_aplicar_platt_identidade_a1_b0():
    probs = [0.5, 0.7, 0.3]
    out = aplicar_platt(probs, 1.0, 0.0)
    # Com a=1, b=0: P_cal = sigmoid(logit(P_raw)) = P_raw
    for p_raw, p_cal in zip(probs, out):
        teste(f"a=1,b=0 preserva {p_raw:.1f}", abs(p_cal - p_raw) < 1e-6)


def t_dados_vazios():
    r = avaliar_calibracao([], [])
    teste("vazio: erro", "erro" in r)


def main():
    print("=== test_calibracao_platt ===")
    for fn in [t_brier_simples, t_log_loss_simples, t_ece_perfeita,
               t_ece_descalibrado, t_platt_fit_roda_sem_erro,
               t_platt_reduz_over_confidence, t_avaliar_calibracao_melhora_ece,
               t_aplicar_platt_identidade_a1_b0, t_dados_vazios]:
        try: fn()
        except Exception as e:
            global fail; fail += 1
            print(f"  FAIL {fn.__name__}: {type(e).__name__}: {e}")
            import traceback; traceback.print_exc()
    print(f"\n{ok} ok, {fail} fail")
    sys.exit(0 if fail == 0 else 1)


if __name__ == "__main__":
    main()
