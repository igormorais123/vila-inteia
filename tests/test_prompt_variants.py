"""Testes Onda 165: prompt variant ensemble."""

from __future__ import annotations
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.prompt_variants import (
    gerar_variants, agregar_probs_variants,
)

ok, fail = 0, 0


def teste(nome, cond, det=""):
    global ok, fail
    if cond: ok += 1; print(f"  OK  {nome}")
    else:    fail += 1; print(f"  FAIL {nome} {det}")


def t_gerar_variants_inclui_original():
    v = gerar_variants("Dilma sofrerá impeachment?", n=3)
    teste("1ª é original", v[0] == "Dilma sofrerá impeachment?")


def t_gerar_variants_produz_n():
    v = gerar_variants("Dilma sofrerá impeachment?", n=3)
    teste(f"3 variants (got {len(v)})", len(v) == 3)


def t_gerar_variants_vazio():
    v = gerar_variants("", n=3)
    teste("vazio → []", v == [])


def t_variants_distintas():
    v = gerar_variants("Lula vencerá o 2º turno?", n=3)
    teste(f"3 variants distintas", len(set(v)) >= 2)


def t_agregar_median_3():
    teste("median 3 probs", agregar_probs_variants([0.3, 0.6, 0.9]) == 0.6)


def t_agregar_median_par():
    teste("median 4 probs = avg meio",
          abs(agregar_probs_variants([0.2, 0.4, 0.6, 0.8]) - 0.5) < 1e-9)


def t_agregar_ignora_none():
    teste("ignora None", agregar_probs_variants([None, 0.7, None]) == 0.7)


def t_agregar_todas_none():
    teste("todas None → None", agregar_probs_variants([None, None]) is None)


def main():
    print("=== test_prompt_variants ===")
    for fn in [t_gerar_variants_inclui_original, t_gerar_variants_produz_n,
               t_gerar_variants_vazio, t_variants_distintas,
               t_agregar_median_3, t_agregar_median_par,
               t_agregar_ignora_none, t_agregar_todas_none]:
        try: fn()
        except Exception as e:
            global fail; fail += 1
            print(f"  FAIL {fn.__name__}: {type(e).__name__}: {e}")
            import traceback; traceback.print_exc()
    print(f"\n{ok} ok, {fail} fail")
    sys.exit(0 if fail == 0 else 1)


if __name__ == "__main__":
    main()
