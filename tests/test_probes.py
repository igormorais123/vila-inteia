"""Testes Onda 108: livez + readyz probes."""

from __future__ import annotations
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

ok, fail = 0, 0


def teste(nome, cond, det=""):
    global ok, fail
    if cond: ok += 1; print(f"  OK  {nome}")
    else:    fail += 1; print(f"  FAIL {nome} {det}")


def t_livez_retorna_dict():
    from api.rotas_health import endpoint_livez
    r = endpoint_livez()
    teste("alive=True", r["alive"] is True)
    teste("ts int", isinstance(r["ts"], int))


def t_readyz_sim_none_503():
    from api import rotas_vila as rv
    from api.rotas_health import endpoint_readyz
    # Forçar sim None
    orig = rv.simulacao
    rv.simulacao = None
    try:
        r = endpoint_readyz()
        # FastAPI JSONResponse
        teste("readyz retorna algo", r is not None)
        # Status 503 indicado via status_code
        status = getattr(r, "status_code", 200)
        teste("sim None → 503", status == 503, f"got {status}")
    finally:
        rv.simulacao = orig


def t_readyz_structure():
    from api.rotas_health import endpoint_readyz
    import json
    r = endpoint_readyz()
    body_bytes = r.body if hasattr(r, "body") else b"{}"
    body = json.loads(body_bytes)
    teste("body tem ready", "ready" in body)
    teste("body tem checks", "checks" in body)
    teste("body tem ts", "ts" in body)


def main():
    print("=== test_probes ===")
    for fn in [t_livez_retorna_dict, t_readyz_sim_none_503, t_readyz_structure]:
        try: fn()
        except Exception as e:
            global fail; fail += 1
            print(f"  FAIL {fn.__name__}: {type(e).__name__}: {e}")
            import traceback; traceback.print_exc()
    print(f"\n{ok} ok, {fail} fail")
    sys.exit(0 if fail == 0 else 1)


if __name__ == "__main__":
    main()
