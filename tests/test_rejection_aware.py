"""Testes Onda 134: rejection-aware CoT prompt."""

from __future__ import annotations
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.backtest_real import _build_cot_prefix

ok, fail = 0, 0


def teste(nome, cond, det=""):
    global ok, fail
    if cond: ok += 1; print(f"  OK  {nome}")
    else:    fail += 1; print(f"  FAIL {nome} {det}")


def t_default_rejection_aware_on():
    cot = _build_cot_prefix()
    teste("default tem step 5 REJEIÇÃO", "REJEIÇÃO" in cot)
    teste("tem bloqueio/fracasso menção",
          "bloqueio" in cot.lower() or "fracasso" in cot.lower())


def t_rejection_aware_off():
    cot = _build_cot_prefix(rejection_aware=False)
    teste("off: sem REJEIÇÃO", "REJEIÇÃO" not in cot)
    teste("off: mantém steps 1-4",
           "drivers" in cot and "over-confident" in cot)


def t_format_intact():
    cot = _build_cot_prefix()
    teste("tem RACIOCÍNIO", "RACIOCÍNIO" in cot)
    teste("tem PROBABILIDADE FINAL", "PROBABILIDADE FINAL" in cot)


def t_anti_bias_msg():
    cot = _build_cot_prefix()
    # Deve ter prompt explícito contra bias de otimismo
    teste("prompt pede considerar NEGATIVO ou INVERSO",
          "NEGATIVO" in cot or "INVERSO" in cot)


def main():
    print("=== test_rejection_aware ===")
    for fn in [t_default_rejection_aware_on, t_rejection_aware_off,
               t_format_intact, t_anti_bias_msg]:
        try: fn()
        except Exception as e:
            global fail; fail += 1
            print(f"  FAIL {fn.__name__}: {type(e).__name__}: {e}")
            import traceback; traceback.print_exc()
    print(f"\n{ok} ok, {fail} fail")
    sys.exit(0 if fail == 0 else 1)


if __name__ == "__main__":
    main()
