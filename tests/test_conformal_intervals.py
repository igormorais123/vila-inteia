"""Testes Onda 162: conformal prediction intervals."""

from __future__ import annotations
import sys, os, random
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.conformal_intervals import (
    residuais_absolutos, quantil_empirico,
    intervalo_conformal, cobertura_empirica, fitar_intervalos,
)

ok, fail = 0, 0


def teste(nome, cond, det=""):
    global ok, fail
    if cond: ok += 1; print(f"  OK  {nome}")
    else:    fail += 1; print(f"  FAIL {nome} {det}")


def t_residuais_basico():
    probs = [0.9, 0.3, 0.7, 0.1]
    y = [1, 0, 0, 1]
    r = residuais_absolutos(probs, y)
    teste("residual 0.9-1=0.1", abs(r[0] - 0.1) < 1e-9)
    teste("residual 0.3-0=0.3", abs(r[1] - 0.3) < 1e-9)
    teste("residual 0.7-0=0.7", abs(r[2] - 0.7) < 1e-9)


def t_quantil_mediano():
    teste("mediana 5 elems", abs(quantil_empirico([1, 2, 3, 4, 5], 0.5) - 3) < 1e-9)


def t_quantil_vazio():
    teste("vazio retorna 0", quantil_empirico([], 0.5) == 0.0)


def t_intervalo_clamp_range():
    lo, hi = intervalo_conformal(0.95, [0.5], alpha=0.2)
    teste(f"hi clampa 1.0 (got {hi})", hi <= 1.0)
    lo, hi = intervalo_conformal(0.05, [0.5], alpha=0.2)
    teste(f"lo clampa 0.0 (got {lo})", lo >= 0.0)


def t_intervalo_vazio_hist_default():
    lo, hi = intervalo_conformal(0.5, [], alpha=0.2)
    teste("sem histórico: default ±0.5", lo == 0.0 and hi == 1.0)


def t_cobertura_acima_1_menos_alpha():
    # Simulate: probs calibradas mal, mas teste na própria distribuição
    random.seed(42)
    n = 200
    probs = [random.random() for _ in range(n)]
    y = [1 if random.random() < p else 0 for p in probs]

    # Split 60/40
    mid = int(n * 0.6)
    probs_calib = probs[:mid]
    y_calib = y[:mid]
    probs_test = probs[mid:]
    y_test = y[mid:]

    residuais_calib = residuais_absolutos(probs_calib, y_calib)
    r = cobertura_empirica(probs_test, y_test, residuais_calib, alpha=0.2)
    teste(f"cobertura >= 70% (got {r['cobertura_observada']:.2f})",
          r['cobertura_observada'] >= 0.70)  # allow small finite-sample gap


def t_fitar_retorna_q_valido():
    probs = [0.8, 0.2, 0.6, 0.4, 0.9, 0.1, 0.7, 0.3, 0.5, 0.5]
    y = [1, 0, 1, 0, 1, 0, 1, 0, 1, 0]
    r = fitar_intervalos(probs, y, alpha=0.2)
    teste("q é float", isinstance(r["q"], float))
    teste("q >= 0", r["q"] >= 0)
    teste("n=10", r["n"] == 10)


def t_alpha_menor_intervalo_maior():
    """Menor alpha (mais cobertura) → intervalo maior."""
    random.seed(1)
    residuais = [random.random() * 0.3 for _ in range(50)]
    lo1, hi1 = intervalo_conformal(0.5, residuais, alpha=0.2)  # 80% CI
    lo2, hi2 = intervalo_conformal(0.5, residuais, alpha=0.05)  # 95% CI
    teste(f"alpha menor → largura maior (0.8={hi1-lo1:.3f}, 0.95={hi2-lo2:.3f})",
          (hi2 - lo2) >= (hi1 - lo1))


def main():
    print("=== test_conformal_intervals ===")
    for fn in [t_residuais_basico, t_quantil_mediano, t_quantil_vazio,
               t_intervalo_clamp_range, t_intervalo_vazio_hist_default,
               t_cobertura_acima_1_menos_alpha, t_fitar_retorna_q_valido,
               t_alpha_menor_intervalo_maior]:
        try: fn()
        except Exception as e:
            global fail; fail += 1
            print(f"  FAIL {fn.__name__}: {type(e).__name__}: {e}")
            import traceback; traceback.print_exc()
    print(f"\n{ok} ok, {fail} fail")
    sys.exit(0 if fail == 0 else 1)


if __name__ == "__main__":
    main()
