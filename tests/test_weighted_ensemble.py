"""Testes Onda 122: weighted ensemble por persona skill."""

from __future__ import annotations
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.backtest_real import (
    _agregar_ponderado, pesos_desde_ranking_skill,
)

ok, fail = 0, 0


def teste(nome, cond, det=""):
    global ok, fail
    if cond: ok += 1; print(f"  OK  {nome}")
    else:    fail += 1; print(f"  FAIL {nome} {det}")


def t_agregar_sem_pesos_media_simples():
    pp = [
        {"persona_id": "A", "prob_extraida": 0.8},
        {"persona_id": "B", "prob_extraida": 0.4},
    ]
    teste("sem pesos: média = 0.6", abs(_agregar_ponderado(pp, None) - 0.6) < 1e-9)


def t_agregar_com_pesos_dominante():
    pp = [
        {"persona_id": "A", "prob_extraida": 0.9},
        {"persona_id": "B", "prob_extraida": 0.1},
    ]
    # A tem peso 10x → resultado perto de 0.9
    pesos = {"A": 10.0, "B": 1.0}
    out = _agregar_ponderado(pp, pesos)
    teste(f"peso 10x A → ~0.83 (got {out:.3f})", abs(out - 0.8273) < 0.01)


def t_agregar_vazio():
    teste("vazio → None", _agregar_ponderado([], {"A":1}) is None)
    pp = [{"persona_id":"A", "prob_extraida": None}]
    teste("só None → None", _agregar_ponderado(pp, None) is None)


def t_agregar_ignora_none_extraido():
    pp = [
        {"persona_id": "A", "prob_extraida": 0.8},
        {"persona_id": "B", "prob_extraida": None},
        {"persona_id": "C", "prob_extraida": 0.2},
    ]
    teste("ignora extraida None: média = 0.5",
          abs(_agregar_ponderado(pp, None) - 0.5) < 1e-9)


def t_pesos_inverso_brier():
    ranking = [
        {"persona_id": "A", "brier_avg": 0.01},   # melhor
        {"persona_id": "B", "brier_avg": 0.25},   # mediano
        {"persona_id": "C", "brier_avg": 0.49},   # pior
    ]
    pesos = pesos_desde_ranking_skill(ranking)
    teste("A peso > B peso", pesos["A"] > pesos["B"])
    teste("B peso > C peso", pesos["B"] > pesos["C"])
    # 1/(0.01+0.01) = 50
    teste("A peso ≈ 50", abs(pesos["A"] - 50.0) < 0.1)


def t_pesos_missing_brier_default_1():
    ranking = [
        {"persona_id": "X", "brier_avg": None},
        {"persona_id": "Y"},
    ]
    pesos = pesos_desde_ranking_skill(ranking)
    teste("X peso = 1.0 (None)", pesos["X"] == 1.0)
    teste("Y peso = 1.0 (missing)", pesos["Y"] == 1.0)


def t_weighted_reduces_bad_predictor_impact():
    """Simula cenário real: Bezos muito peso, Icahn muito pouco."""
    # Evento onde Bezos acerta (0.9, real=1), Icahn erra (0.95, real=0)
    pp_correct = [
        {"persona_id": "BEZ", "prob_extraida": 0.9},
        {"persona_id": "ICA", "prob_extraida": 0.95},
    ]
    # Média simples = 0.925 (ambos > 0.5 preveriam 1). Se y=0, ambos erram.
    # Mas se BEZ tinha brier histórico 0.01 e ICA 0.24:
    pesos = {"BEZ": 100.0, "ICA": 1/0.25}  # 100 vs 4
    ag = _agregar_ponderado(pp_correct, pesos)
    # Muito mais próximo de Bezos (0.9)
    teste(f"weighted ~Bezos (got {ag:.3f})", abs(ag - 0.902) < 0.005)


def main():
    print("=== test_weighted_ensemble ===")
    for fn in [t_agregar_sem_pesos_media_simples,
               t_agregar_com_pesos_dominante,
               t_agregar_vazio, t_agregar_ignora_none_extraido,
               t_pesos_inverso_brier, t_pesos_missing_brier_default_1,
               t_weighted_reduces_bad_predictor_impact]:
        try: fn()
        except Exception as e:
            global fail; fail += 1
            print(f"  FAIL {fn.__name__}: {type(e).__name__}: {e}")
            import traceback; traceback.print_exc()
    print(f"\n{ok} ok, {fail} fail")
    sys.exit(0 if fail == 0 else 1)


if __name__ == "__main__":
    main()
