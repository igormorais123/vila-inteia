"""Testes Onda 97: runtime Platt calibration."""

from __future__ import annotations
import sys, os, tempfile, json as _json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.calibracao_runtime import (
    salvar_coefs, carregar_coefs, aplicar, aplicar_varios,
    calibracao_ativa, status, salvar_isotonic,
)

ok, fail = 0, 0


def teste(nome, cond, det=""):
    global ok, fail
    if cond: ok += 1; print(f"  OK  {nome}")
    else:    fail += 1; print(f"  FAIL {nome} {det}")


def _tmppath():
    import tempfile
    return tempfile.NamedTemporaryFile(suffix=".json", delete=False).name


def t_salvar_carregar_roundtrip():
    p = _tmppath()
    os.unlink(p)
    salvar_coefs(0.5, -0.3, 100, "teste", path=p)
    c = carregar_coefs(path=p, use_cache=False)
    teste("a preservado", abs(c["a"] - 0.5) < 1e-9)
    teste("b preservado", abs(c["b"] - (-0.3)) < 1e-9)
    teste("n preservado", c["n_amostras"] == 100)
    teste("fonte preservado", c["fonte"] == "teste")
    os.unlink(p)


def t_carregar_path_inexistente():
    teste("path inexistente → None",
          carregar_coefs(path="/tmp/nao_existe_xxx.json", use_cache=False) is None)


def t_calibracao_ativa():
    p = _tmppath()
    os.unlink(p)
    teste("antes: não ativa", not calibracao_ativa(path=p))
    salvar_coefs(1.0, 0.0, 10, path=p)
    teste("após salvar: ativa", calibracao_ativa(path=p))
    os.unlink(p)


def t_aplicar_sem_coefs_retorna_raw():
    # Path inexistente → retorna prob original
    out = aplicar(0.7, path="/tmp/naoexiste_xxxx.json")
    teste("sem coefs → preserva", abs(out - 0.7) < 1e-9)


def t_aplicar_identidade_a1_b0():
    p = _tmppath()
    os.unlink(p)
    salvar_coefs(1.0, 0.0, 10, path=p)
    # P(raw=0.5) → logit 0 → z=0 → sigmoid(0)=0.5
    teste("a=1,b=0 preserva 0.5", abs(aplicar(0.5, path=p) - 0.5) < 1e-9)
    teste("a=1,b=0 preserva 0.7", abs(aplicar(0.7, path=p) - 0.7) < 1e-6)
    os.unlink(p)


def t_aplicar_reduz_over_confidence():
    """a < 1 + b > 0 move probs para centro."""
    p = _tmppath()
    os.unlink(p)
    salvar_coefs(-0.337, 1.272, 15, path=p)  # coefs do backtest real
    # Raw 0.9 → com esses coefs → ~0.58
    cal = aplicar(0.9, path=p)
    teste(f"0.9 reduzido (got {cal:.3f})", 0.4 < cal < 0.8)
    cal_95 = aplicar(0.95, path=p)
    teste(f"0.95 reduzido (got {cal_95:.3f})", cal_95 < 0.95)
    os.unlink(p)


def t_aplicar_varios():
    p = _tmppath()
    os.unlink(p)
    salvar_coefs(1.0, 0.0, 10, path=p)
    out = aplicar_varios([0.3, 0.5, 0.7], path=p)
    teste("3 probs preservadas (a=1,b=0)",
          all(abs(a-b) < 1e-6 for a,b in zip(out, [0.3, 0.5, 0.7])))
    os.unlink(p)


def t_status():
    p = _tmppath()
    os.unlink(p)
    s1 = status(path=p)
    teste("não ativa: ativa=False", s1["ativa"] is False)
    salvar_coefs(1.5, -0.5, 50, "backtest", path=p)
    s2 = status(path=p)
    teste("ativa: ativa=True", s2["ativa"] is True)
    teste("a no status", s2["a"] == 1.5)
    teste("n_amostras no status", s2["n_amostras"] == 50)
    os.unlink(p)


def t_isotonic_roundtrip():
    p = _tmppath()
    os.unlink(p)
    mapping = [(0.1, 0.05), (0.3, 0.20), (0.5, 0.45), (0.7, 0.75), (0.9, 0.92)]
    salvar_isotonic(mapping, n_amostras=100, fonte="iso_test", path=p)
    c = carregar_coefs(path=p, use_cache=False)
    teste("tipo=isotonic", c["tipo"] == "isotonic")
    teste("mapping size=5", len(c["mapping"]) == 5)
    os.unlink(p)


def t_isotonic_aplicar_interpolacao():
    p = _tmppath()
    os.unlink(p)
    mapping = [(0.1, 0.05), (0.5, 0.45), (0.9, 0.92)]
    salvar_isotonic(mapping, n_amostras=100, path=p)
    # 0.5 → 0.45 (match exato)
    teste("iso 0.5 → 0.45", abs(aplicar(0.5, path=p) - 0.45) < 1e-6)
    # 0.3 interp entre 0.05 e 0.45 → 0.25
    v = aplicar(0.3, path=p)
    teste(f"iso 0.3 interp → ~0.25 (got {v:.3f})", abs(v - 0.25) < 0.01)
    # Fora de range: clampa
    teste("iso 0.0 → 0.05 (clamp lo)", abs(aplicar(0.0, path=p) - 0.05) < 1e-6)
    teste("iso 1.0 → 0.92 (clamp hi)", abs(aplicar(1.0, path=p) - 0.92) < 1e-6)
    os.unlink(p)


def t_status_isotonic_reporta_mapping_size():
    p = _tmppath()
    os.unlink(p)
    mapping = [(0.1, 0.1), (0.9, 0.9)]
    salvar_isotonic(mapping, n_amostras=50, path=p)
    s = status(p)
    teste("status tipo=isotonic", s["tipo"] == "isotonic")
    teste("status mapping_size=2", s["mapping_size"] == 2)
    os.unlink(p)


def main():
    print("=== test_calibracao_runtime ===")
    for fn in [t_salvar_carregar_roundtrip, t_carregar_path_inexistente,
               t_calibracao_ativa, t_aplicar_sem_coefs_retorna_raw,
               t_aplicar_identidade_a1_b0, t_aplicar_reduz_over_confidence,
               t_aplicar_varios, t_status,
               t_isotonic_roundtrip, t_isotonic_aplicar_interpolacao,
               t_status_isotonic_reporta_mapping_size]:
        try: fn()
        except Exception as e:
            global fail; fail += 1
            print(f"  FAIL {fn.__name__}: {type(e).__name__}: {e}")
            import traceback; traceback.print_exc()
    print(f"\n{ok} ok, {fail} fail")
    sys.exit(0 if fail == 0 else 1)


if __name__ == "__main__":
    main()
