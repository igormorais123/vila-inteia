"""Testes cap LLM por step (Onda 68)."""

from __future__ import annotations
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import importlib
import engine.ia_client as ic

ok, fail = 0, 0


def teste(nome, cond, det=""):
    global ok, fail
    if cond: ok += 1; print(f"  OK  {nome}")
    else:    fail += 1; print(f"  FAIL {nome} {det}")


def _reset_module():
    importlib.reload(ic)


def t_inicial_zero():
    _reset_module()
    s = ic.stats_step_atual()
    teste("step_id inicial = -1", s["step_id"] == -1)
    teste("chamadas_no_step = 0", s["chamadas_no_step"] == 0)


def t_reset_atualiza_step_id():
    _reset_module()
    ic.reset_step_counter(42)
    s = ic.stats_step_atual()
    teste("step_id = 42", s["step_id"] == 42)
    teste("contador zerado", s["chamadas_no_step"] == 0)


def t_consumir_slot_incrementa():
    _reset_module()
    ic.reset_step_counter(0)
    ic._consumir_step_slot()
    ic._consumir_step_slot()
    teste("2 chamadas contadas",
          ic.stats_step_atual()["chamadas_no_step"] == 2)


def t_cap_bloqueia():
    _reset_module()
    ic.reset_step_counter(0)
    max_ = ic._VILA_LLM_MAX_POR_STEP
    for _ in range(max_):
        r = ic._consumir_step_slot()
        if not r:
            break
    r_excedente = ic._consumir_step_slot()
    teste(f"após {max_} chamadas: próxima bloqueia", not r_excedente)


def t_reset_libera_slots():
    _reset_module()
    ic.reset_step_counter(0)
    max_ = ic._VILA_LLM_MAX_POR_STEP
    for _ in range(max_):
        ic._consumir_step_slot()
    teste("esgotou step 0", not ic._consumir_step_slot())

    ic.reset_step_counter(1)  # novo step
    teste("step 1: slots livres", ic._consumir_step_slot())


def t_reset_mesmo_step_nao_zera():
    _reset_module()
    ic.reset_step_counter(5)
    ic._consumir_step_slot()
    ic._consumir_step_slot()
    ic.reset_step_counter(5)   # mesmo ID
    teste("reset mesmo step preserva contador",
          ic.stats_step_atual()["chamadas_no_step"] == 2)


def main():
    print("=== test_step_cap ===")
    for fn in [t_inicial_zero, t_reset_atualiza_step_id,
               t_consumir_slot_incrementa, t_cap_bloqueia,
               t_reset_libera_slots, t_reset_mesmo_step_nao_zera]:
        try: fn()
        except Exception as e:
            global fail; fail += 1
            print(f"  FAIL {fn.__name__}: {type(e).__name__}: {e}")
    print(f"\n{ok} ok, {fail} fail")
    sys.exit(0 if fail == 0 else 1)


if __name__ == "__main__":
    main()
