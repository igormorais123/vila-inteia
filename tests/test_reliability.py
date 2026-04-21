"""Testes Onda 101: reliability diagram."""

from __future__ import annotations
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.reliability_diagram import reliability, reliability_ascii

ok, fail = 0, 0


def teste(nome, cond, det=""):
    global ok, fail
    if cond: ok += 1; print(f"  OK  {nome}")
    else:    fail += 1; print(f"  FAIL {nome} {det}")


def t_vazio():
    r = reliability([], [])
    teste("vazio n=0", r["n"] == 0)
    teste("vazio bins=[]", r["bins"] == [])


def t_calibrado_perfeito():
    # 100 probs = 0.5, metade é 1
    probs = [0.5] * 100
    y = [1]*50 + [0]*50
    r = reliability(probs, y, n_bins=10)
    bin_pop = next(b for b in r["bins"] if b["n"] > 0)
    teste(f"bin populado acc~0.5 (got {bin_pop['accuracy']})",
           abs(bin_pop["accuracy"] - 0.5) < 0.01)


def t_over_confident():
    probs = [0.9] * 20
    y = [1]*10 + [0]*10
    r = reliability(probs, y, n_bins=10)
    bin_09 = next(b for b in r["bins"] if b["n"] > 0)
    teste("confidence = 0.9", abs(bin_09["confidence"] - 0.9) < 1e-6)
    teste("accuracy = 0.5", abs(bin_09["accuracy"] - 0.5) < 1e-6)
    teste("gap = 0.4 (over-confident)", abs(bin_09["gap"] - 0.4) < 1e-6)


def t_ascii_renderiza():
    probs = [0.2, 0.5, 0.8]
    y = [0, 1, 1]
    s = reliability_ascii(probs, y, n_bins=5)
    teste("ASCII contém 'Reliability'", "Reliability" in s)
    teste("ASCII multiline", "\n" in s)


def t_bins_estrutura():
    r = reliability([0.1, 0.9], [0, 1], n_bins=5)
    teste("5 bins", len(r["bins"]) == 5)
    teste("center presente", all("center" in b for b in r["bins"]))
    teste("n presente", all("n" in b for b in r["bins"]))


def main():
    print("=== test_reliability ===")
    for fn in [t_vazio, t_calibrado_perfeito, t_over_confident,
               t_ascii_renderiza, t_bins_estrutura]:
        try: fn()
        except Exception as e:
            global fail; fail += 1
            print(f"  FAIL {fn.__name__}: {type(e).__name__}: {e}")
            import traceback; traceback.print_exc()
    print(f"\n{ok} ok, {fail} fail")
    sys.exit(0 if fail == 0 else 1)


if __name__ == "__main__":
    main()
