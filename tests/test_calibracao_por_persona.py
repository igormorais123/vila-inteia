"""Testes Onda 156: per-persona Platt/isotonic calibration."""

from __future__ import annotations
import sys, os, tempfile
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.calibracao_por_persona import (
    aplicar_persona, fitar_persona, fitar_todas_personas, status, _carregar,
)

ok, fail = 0, 0


def teste(nome, cond, det=""):
    global ok, fail
    if cond: ok += 1; print(f"  OK  {nome}")
    else:    fail += 1; print(f"  FAIL {nome} {det}")


def _tmppath():
    p = tempfile.NamedTemporaryFile(suffix=".json", delete=False).name
    os.unlink(p)
    return p


def t_sem_calibrador_retorna_raw():
    p = _tmppath()
    teste("CL_unknown raw preservado",
          aplicar_persona("CL999", 0.7, path=p) == 0.7)


def t_fit_persona_salva_isolado():
    p = _tmppath()
    probs = [0.9, 0.85, 0.95, 0.80, 0.75, 0.70, 0.88, 0.92, 0.78, 0.65]
    ys = [1, 0, 1, 0, 1, 0, 1, 0, 0, 1]
    r = fitar_persona("CL001", probs, ys, path=p)
    teste("CL001 salvo", r["salvo"] is True)
    # adicionar outra
    fitar_persona("CL002", probs, ys, path=p)
    data = _carregar(p)
    teste("dois registros isolados", "CL001" in data and "CL002" in data)
    os.unlink(p)


def t_fit_aplicar_roundtrip():
    p = _tmppath()
    probs = [0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]
    ys =    [0,   0,   0,   1,   0,   1,   1,   1]
    fitar_persona("CL007", probs, ys, path=p)
    p_cal = aplicar_persona("CL007", 0.5, path=p)
    teste(f"CL007 calib(0.5) ≠ 0.5 (got {p_cal:.3f})", abs(p_cal - 0.5) > 0.001)
    os.unlink(p)


def t_poucos_amostras_nao_salva():
    p = _tmppath()
    r = fitar_persona("CL003", [0.5, 0.5], [0, 1], path=p)
    teste("n<5 não salva", r["salvo"] is False)


def t_fitar_todas_respeita_min_amostras():
    p = _tmppath()
    datasets = [
        {"eventos": [
            {"outcome_real": 1, "per_persona": [
                {"persona_id": "CL001", "prob_extraida": 0.8},
                {"persona_id": "CL002", "prob_extraida": 0.3},
            ]},
            {"outcome_real": 0, "per_persona": [
                {"persona_id": "CL001", "prob_extraida": 0.7},
                {"persona_id": "CL002", "prob_extraida": 0.4},
            ]},
        ]}
    ]
    r = fitar_todas_personas(datasets, min_amostras=5, path=p)
    teste("CL001 2ev <5 min: não fit",
          r.get("CL001", {}).get("salvo") is False)


def t_status_reporta_personas():
    p = _tmppath()
    probs = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]
    ys = [0, 0, 0, 1, 0, 1, 1, 0, 1]
    fitar_persona("CL001", probs, ys, path=p)
    fitar_persona("CL007", probs, ys, path=p)
    st = status(p)
    teste("2 personas no status",
          st["n_personas_calibradas"] == 2)
    teste("CL001 no status", "CL001" in st["personas"])
    os.unlink(p)


def main():
    print("=== test_calibracao_por_persona ===")
    for fn in [t_sem_calibrador_retorna_raw,
               t_fit_persona_salva_isolado,
               t_fit_aplicar_roundtrip,
               t_poucos_amostras_nao_salva,
               t_fitar_todas_respeita_min_amostras,
               t_status_reporta_personas]:
        try: fn()
        except Exception as e:
            global fail; fail += 1
            print(f"  FAIL {fn.__name__}: {type(e).__name__}: {e}")
            import traceback; traceback.print_exc()
    print(f"\n{ok} ok, {fail} fail")
    sys.exit(0 if fail == 0 else 1)


if __name__ == "__main__":
    main()
