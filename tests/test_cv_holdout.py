"""Testes Onda 114: CV holdout Platt."""

from __future__ import annotations
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.cv_holdout import split_train_test, cv_holdout_platt

ok, fail = 0, 0


def teste(nome, cond, det=""):
    global ok, fail
    if cond: ok += 1; print(f"  OK  {nome}")
    else:    fail += 1; print(f"  FAIL {nome} {det}")


def t_split_80_20():
    probs = list(range(10))
    y = [0]*5 + [1]*5
    pt, yt, pv, yv = split_train_test(probs, y, test_frac=0.2, seed=1)
    teste(f"test tem 2 (20%)", len(pv) == 2)
    teste(f"train tem 8", len(pt) == 8)


def t_split_determinístico():
    probs = list(range(20))
    y = list(range(20))
    _, _, pv1, yv1 = split_train_test(probs, y, seed=7)
    _, _, pv2, yv2 = split_train_test(probs, y, seed=7)
    teste("mesmo seed → mesmo split", pv1 == pv2)


def t_cv_n_insuficiente():
    r = cv_holdout_platt([0.5], [1])
    teste("n<5 erro", "erro" in r)


def t_cv_funcional():
    probs = [0.8, 0.7, 0.9, 0.3, 0.4, 0.2, 0.6, 0.75, 0.85, 0.5]
    y = [1, 1, 1, 0, 0, 0, 1, 1, 1, 0]
    r = cv_holdout_platt(probs, y, test_frac=0.3, n_repeats=5)
    teste("cv retorna brier_test_avg", "brier_test_avg" in r)
    teste("brier_test >= brier_train (overfit gap >= 0 esperado)",
          r["overfit_gap"] >= -0.1)  # tolerance
    teste("n_repeats <= 5", r["n_repeats"] <= 5)
    teste("platt_a_mean presente", "platt_a_mean" in r)
    teste("platt_a_std >= 0", r["platt_a_std"] >= 0)


def main():
    print("=== test_cv_holdout ===")
    for fn in [t_split_80_20, t_split_determinístico,
               t_cv_n_insuficiente, t_cv_funcional]:
        try: fn()
        except Exception as e:
            global fail; fail += 1
            print(f"  FAIL {fn.__name__}: {type(e).__name__}: {e}")
            import traceback; traceback.print_exc()
    print(f"\n{ok} ok, {fail} fail")
    sys.exit(0 if fail == 0 else 1)


if __name__ == "__main__":
    main()
