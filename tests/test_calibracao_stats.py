"""Testes Onda 100: bootstrap CI + isotonic."""

from __future__ import annotations
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.calibracao_stats import (
    bootstrap_ci, isotonic_fit, isotonic_aplicar, comparacao_platt_vs_isotonic,
)
from engine.calibracao_platt import brier

ok, fail = 0, 0


def teste(nome, cond, det=""):
    global ok, fail
    if cond: ok += 1; print(f"  OK  {nome}")
    else:    fail += 1; print(f"  FAIL {nome} {det}")


def t_bootstrap_simples():
    probs = [0.7, 0.8, 0.9, 0.3, 0.4]
    y = [1, 1, 1, 0, 0]
    r = bootstrap_ci(brier, probs, y, n_boot=200)
    teste("point retornado", r["point"] is not None)
    teste("lo ≤ point ≤ hi", r["lo"] <= r["point"] <= r["hi"])
    teste("n_boot=200", r["n_boot"] == 200)


def t_bootstrap_n_insuficiente():
    r = bootstrap_ci(brier, [0.5], [1], n_boot=10)
    teste("n<2 retorna erro", "erro" in r)


def t_isotonic_monotonico():
    # Y crescente com prob → mapping deve ser identidade-like
    probs = [0.1, 0.3, 0.5, 0.7, 0.9]
    y = [0, 0, 1, 1, 1]
    m = isotonic_fit(probs, y)
    # Valores cal devem ser não-decrescentes
    cals = [c for _, c in m]
    teste("isotonic monotônico", all(cals[i] <= cals[i+1] for i in range(len(cals)-1)))


def t_isotonic_inversao():
    # Y decresce — PAV deve poolar tudo na média
    probs = [0.2, 0.4, 0.6, 0.8]
    y = [1, 1, 0, 0]
    m = isotonic_fit(probs, y)
    cals = [c for _, c in m]
    # Todos iguais (média = 0.5)
    teste("PAV pool inversão", all(abs(c - 0.5) < 1e-9 for c in cals))


def t_isotonic_aplicar_boundary():
    mapping = [(0.1, 0.05), (0.5, 0.5), (0.9, 0.95)]
    teste("antes range", isotonic_aplicar(0.0, mapping) == 0.05)
    teste("após range", isotonic_aplicar(1.0, mapping) == 0.95)
    teste("mid interp", abs(isotonic_aplicar(0.3, mapping) - 0.275) < 0.05)


def t_comparacao():
    import random
    random.seed(1)
    # Varied data: probs correlacionam com outcome com ruído
    probs = [0.1, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 0.2, 0.85]
    y     = [  0,   0,   1,   0,   1,   1,   1,   1,   0,    1]
    r = comparacao_platt_vs_isotonic(probs, y)
    teste("n=10", r["n"] == 10)
    teste("raw, platt, isotonic chaves", all(k in r for k in ["raw","platt","isotonic"]))
    # Platt não sempre reduz Brier (Nelder-Mead subotimo); deve reduzir ECE
    teste("isotonic reduz ECE", r["isotonic"]["ece"] <= r["raw"]["ece"] + 0.01)


def main():
    print("=== test_calibracao_stats ===")
    for fn in [t_bootstrap_simples, t_bootstrap_n_insuficiente,
               t_isotonic_monotonico, t_isotonic_inversao,
               t_isotonic_aplicar_boundary, t_comparacao]:
        try: fn()
        except Exception as e:
            global fail; fail += 1
            print(f"  FAIL {fn.__name__}: {type(e).__name__}: {e}")
            import traceback; traceback.print_exc()
    print(f"\n{ok} ok, {fail} fail")
    sys.exit(0 if fail == 0 else 1)


if __name__ == "__main__":
    main()
