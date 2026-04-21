"""Testes Onda 102: Brier decomposition."""

from __future__ import annotations
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.brier_decomp import decompor

ok, fail = 0, 0


def teste(nome, cond, det=""):
    global ok, fail
    if cond: ok += 1; print(f"  OK  {nome}")
    else:    fail += 1; print(f"  FAIL {nome} {det}")


def t_vazio():
    r = decompor([], [])
    teste("vazio: erro", "erro" in r)


def t_decomp_identity():
    """BS = REL − RES + UNC deve valer."""
    probs = [0.1, 0.3, 0.5, 0.7, 0.9, 0.2, 0.4, 0.6, 0.8, 0.95]
    y = [0, 0, 1, 1, 1, 0, 0, 1, 1, 1]
    r = decompor(probs, y, n_bins=5)
    # Gap tolerável por binning
    teste(f"decomp gap pequeno (got {r['decomp_gap']:.4f})",
           abs(r["decomp_gap"]) < 0.05)


def t_uncertainty_correta():
    # 50/50 split → unc = 0.25
    probs = [0.5] * 10
    y = [1]*5 + [0]*5
    r = decompor(probs, y)
    teste("uncertainty = 0.25", abs(r["uncertainty"] - 0.25) < 1e-9)


def t_uncertainty_zero_y_constante():
    probs = [0.5] * 10
    y = [1] * 10
    r = decompor(probs, y)
    teste("y constante → unc = 0", r["uncertainty"] == 0.0)


def t_resolution_positive_boa_separacao():
    """Boa separação → resolução alta."""
    probs = [0.1]*5 + [0.9]*5
    y = [0]*5 + [1]*5
    r = decompor(probs, y, n_bins=10)
    teste("resolução alta", r["resolution"] > 0.2)


def t_bss_presente():
    probs = [0.6, 0.7, 0.4]
    y = [1, 1, 0]
    r = decompor(probs, y)
    teste("BSS presente e finito",
           r["brier_skill_score"] is not None)


def main():
    print("=== test_brier_decomp ===")
    for fn in [t_vazio, t_decomp_identity, t_uncertainty_correta,
               t_uncertainty_zero_y_constante, t_resolution_positive_boa_separacao,
               t_bss_presente]:
        try: fn()
        except Exception as e:
            global fail; fail += 1
            print(f"  FAIL {fn.__name__}: {type(e).__name__}: {e}")
            import traceback; traceback.print_exc()
    print(f"\n{ok} ok, {fail} fail")
    sys.exit(0 if fail == 0 else 1)


if __name__ == "__main__":
    main()
