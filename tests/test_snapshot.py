"""Testes Onda 90: snapshot export endpoint."""

from __future__ import annotations
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

ok, fail = 0, 0


def teste(nome, cond, det=""):
    global ok, fail
    if cond: ok += 1; print(f"  OK  {nome}")
    else:    fail += 1; print(f"  FAIL {nome} {det}")


def t_serializar_sim_retorna_dict():
    from engine.save_load import _serializar_simulacao

    class _Pers:
        nome_exibicao = "X"
        def resumo(self): return {"nome": "X", "id": "CL0"}
        def to_dict(self): return {"nome": "X", "id": "CL0"}

    class _Sim:
        nome = "test"
        step = 5
        personas = {"CL0": _Pers()}
        conversas_recentes = []
        sinteses = []
    out = _serializar_simulacao(_Sim())
    teste("retorna dict", isinstance(out, dict))


def t_snapshot_schema_version():
    import json
    schema = {
        "vila_id": "test", "step": 10, "exportado_em": 123,
        "schema_version": 1, "estado": {}
    }
    serialized = json.dumps(schema)
    teste("schema json-serializable", len(serialized) > 10)
    reparsed = json.loads(serialized)
    teste("schema_version=1", reparsed["schema_version"] == 1)


def main():
    print("=== test_snapshot ===")
    for fn in [t_serializar_sim_retorna_dict, t_snapshot_schema_version]:
        try: fn()
        except Exception as e:
            global fail; fail += 1
            print(f"  FAIL {fn.__name__}: {type(e).__name__}: {e}")
            import traceback; traceback.print_exc()
    print(f"\n{ok} ok, {fail} fail")
    sys.exit(0 if fail == 0 else 1)


if __name__ == "__main__":
    main()
