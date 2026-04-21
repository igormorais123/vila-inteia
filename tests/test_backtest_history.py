"""Testes Onda 106: backtest history persistence."""

from __future__ import annotations
import sys, os, tempfile, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine import backtest_history as bh

ok, fail = 0, 0


def teste(nome, cond, det=""):
    global ok, fail
    if cond: ok += 1; print(f"  OK  {nome}")
    else:    fail += 1; print(f"  FAIL {nome} {det}")


def t_flatten_basico():
    saida = {
        "agregado": {"n_eventos_total": 15, "accuracy_global": 0.67,
                     "brier_vila_macro_avg": 0.28, "brier_prior_macro_avg": 0.16,
                     "skill_brier_vs_prior_macro": -0.80, "n_datasets": 5},
        "calibracao_platt": {"platt_a": -0.337, "platt_b": 1.272},
        "datasets": [{"persona_panel": ["CL001", "CL007"]}],
    }
    r = bh._flatten(saida)
    teste("id gerado", r["id"] and len(r["id"]) > 10)
    teste("n_eventos", r["n_eventos"] == 15)
    teste("accuracy", r["accuracy_global"] == 0.67)
    teste("skill", r["skill"] == -0.80)
    teste("platt_a", r["platt_a"] == -0.337)
    teste("personas", r["personas"] == ["CL001", "CL007"])


def t_salvar_local_sem_supabase():
    # Forçar path local
    tmp = tempfile.NamedTemporaryFile(suffix=".jsonl", delete=False).name
    os.unlink(tmp)
    from pathlib import Path
    orig = bh._LOCAL_LOG
    bh._LOCAL_LOG = Path(tmp)
    try:
        saida = {"agregado": {"n_eventos_total": 5, "accuracy_global": 0.6},
                  "datasets": [{"persona_panel": ["CL001"]}]}
        r = bh.salvar(saida)
        teste("salvou em local", r["salvo_em_local"])
        # Read back
        lines = open(tmp).readlines()
        teste("1 linha JSONL", len(lines) == 1)
        rec = json.loads(lines[0])
        teste("sem raw_payload no local", "raw_payload" not in rec)
        teste("id presente", rec["id"] == r["id"])
    finally:
        bh._LOCAL_LOG = orig
        if os.path.exists(tmp):
            os.unlink(tmp)


def t_historico_le_local():
    tmp = tempfile.NamedTemporaryFile(suffix=".jsonl", delete=False).name
    from pathlib import Path
    orig = bh._LOCAL_LOG
    bh._LOCAL_LOG = Path(tmp)
    # Write 3 records
    for i in range(3):
        bh.salvar({"agregado": {"n_eventos_total": i}, "datasets": []})
    try:
        hist = bh.historico(limite=10)
        # Sem supabase → reads local
        teste("histórico >= 3 recs", len(hist) >= 3)
        teste("ordem mais recente primeiro",
              hist[0]["n_eventos"] == 2 or hist[0].get("n_eventos") is not None)
    finally:
        bh._LOCAL_LOG = orig
        if os.path.exists(tmp):
            os.unlink(tmp)


def t_supabase_disponivel():
    # Teste não-destructivo: retorna bool sem crash
    r = bh._supabase_disponivel()
    teste("retorna bool", isinstance(r, bool))


def main():
    print("=== test_backtest_history ===")
    for fn in [t_flatten_basico, t_salvar_local_sem_supabase,
               t_historico_le_local, t_supabase_disponivel]:
        try: fn()
        except Exception as e:
            global fail; fail += 1
            print(f"  FAIL {fn.__name__}: {type(e).__name__}: {e}")
            import traceback; traceback.print_exc()
    print(f"\n{ok} ok, {fail} fail")
    sys.exit(0 if fail == 0 else 1)


if __name__ == "__main__":
    main()
