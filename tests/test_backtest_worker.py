"""Testes Onda 110: backtest worker daemon."""

from __future__ import annotations
import sys, os, importlib
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

ok, fail = 0, 0


def teste(nome, cond, det=""):
    global ok, fail
    if cond: ok += 1; print(f"  OK  {nome}")
    else:    fail += 1; print(f"  FAIL {nome} {det}")


def t_importa_sem_erro():
    # Importar script como módulo
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "backtest_worker",
        os.path.join(os.path.dirname(__file__), "..", "scripts", "backtest_worker.py"),
    )
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    teste("import OK", hasattr(m, "rodar_um_ciclo"))
    teste("main function", hasattr(m, "main"))
    teste("signal handler", hasattr(m, "_handle_sig"))
    return m


def t_sim_minima_carrega():
    m = t_importa_sem_erro()
    # ok+3 do import, +1 do assert aqui
    sim = m._SimMinima(["CL001", "CL002"])
    teste("SimMinima carrega personas válidas", len(sim.personas) >= 1)


def t_persona_inexistente_ignorada():
    m = t_importa_sem_erro()
    # Já counted x7 total de novo, continua
    sim = m._SimMinima(["CL999"])
    teste("CL999 inexistente: 0 personas", len(sim.personas) == 0)


def main():
    print("=== test_backtest_worker ===")
    for fn in [t_importa_sem_erro, t_sim_minima_carrega, t_persona_inexistente_ignorada]:
        try: fn()
        except Exception as e:
            global fail; fail += 1
            print(f"  FAIL {fn.__name__}: {type(e).__name__}: {e}")
            import traceback; traceback.print_exc()
    print(f"\n{ok} ok, {fail} fail")
    sys.exit(0 if fail == 0 else 1)


if __name__ == "__main__":
    main()
