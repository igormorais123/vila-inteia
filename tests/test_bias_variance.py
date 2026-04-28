"""Testes Bias-Variance decomposition."""

from __future__ import annotations
import sys, os, csv
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.bias_variance import bias_variance_decomp
from engine.post_cutoff_classifier import classify_and_predict

ok, fail = 0, 0


def teste(nome, cond, det=""):
    global ok, fail
    if cond: ok += 1; print(f"  OK  {nome}")
    else:    fail += 1; print(f"  FAIL {nome} {det}")


def t_vazio():
    r = bias_variance_decomp([], [])
    teste("vazio: erro", "erro" in r)


def t_bias_zero_quando_calibrado():
    """mean_p == true_rate → bias² = 0."""
    preds = [0.5] * 10
    reals = [1, 0, 1, 0, 1, 0, 1, 0, 1, 0]
    r = bias_variance_decomp(preds, reals, n_bootstrap=50, seed=1)
    teste(f"bias² ~ 0 (got {r['bias_sq']:.6f})", r["bias_sq"] < 1e-9)


def t_bias_alto_quando_descalibrado():
    """preds 0.9 mas true rate 0.1 → bias² alto."""
    preds = [0.9] * 10
    reals = [1, 0, 0, 0, 0, 0, 0, 0, 0, 0]  # rate 0.1
    r = bias_variance_decomp(preds, reals, n_bootstrap=50, seed=1)
    teste(f"bias² > 0.5 (got {r['bias_sq']:.4f})", r["bias_sq"] > 0.5)


def t_variance_zero_pred_constante():
    """Pred constante → variance bootstrap = 0 (mean idêntica em todo resample)."""
    preds = [0.5] * 20
    reals = [1, 0] * 10
    r = bias_variance_decomp(preds, reals, n_bootstrap=100, seed=42)
    teste(f"variance ~ 0 pred const (got {r['variance']:.6f})", r["variance"] < 1e-9)


def t_variance_positiva_preds_dispersos():
    """Preds variados → bootstrap mean tem variância."""
    preds = [0.1, 0.9] * 10
    reals = [1, 0] * 10
    r = bias_variance_decomp(preds, reals, n_bootstrap=200, seed=42)
    teste(f"variance > 0 preds dispersos (got {r['variance']:.6f})",
          r["variance"] > 0)


def t_decomp_keys_presentes():
    preds = [0.6, 0.4, 0.7, 0.3]
    reals = [1, 0, 1, 0]
    r = bias_variance_decomp(preds, reals, n_bootstrap=50, seed=1)
    for k in ("bias_sq", "variance", "mse", "n", "noise"):
        teste(f"key {k} presente", k in r)
    teste("mse > 0", r["mse"] >= 0)


def t_real_bench_post_cutoff():
    """CSV n=40: decomp do classifier."""
    csv_path = "/home/pedroafonso/vila-inteia/data/backtest/post_cutoff_q2_2026_holdout_v2.csv"
    if not os.path.exists(csv_path):
        teste("CSV exists", False, csv_path)
        return
    preds, reals = [], []
    with open(csv_path) as f:
        r = csv.DictReader(f)
        for row in r:
            p, _ = classify_and_predict(row.get("outcome_framing", ""), row.get("contexto", ""))
            preds.append(p)
            reals.append(int(row["outcome_real"]))
    n = len(reals)
    teste(f"n=40 (got {n})", n == 40)
    out = bias_variance_decomp(preds, reals, n_bootstrap=200, seed=42)
    teste(f"bias_sq finito (got {out['bias_sq']:.4f})", out["bias_sq"] >= 0)
    teste(f"variance finita (got {out['variance']:.4f})", out["variance"] >= 0)
    teste(f"mse > 0 (got {out['mse']:.4f})", out["mse"] > 0)
    teste(f"decomp_gap pequeno (|gap|={abs(out['decomp_gap']):.4f})",
          abs(out["decomp_gap"]) < 0.5)


def main():
    print("=== test_bias_variance ===")
    for fn in [t_vazio, t_bias_zero_quando_calibrado, t_bias_alto_quando_descalibrado,
               t_variance_zero_pred_constante, t_variance_positiva_preds_dispersos,
               t_decomp_keys_presentes, t_real_bench_post_cutoff]:
        try: fn()
        except Exception as e:
            global fail; fail += 1
            print(f"  FAIL {fn.__name__}: {type(e).__name__}: {e}")
            import traceback; traceback.print_exc()
    print(f"\n{ok} ok, {fail} fail")
    sys.exit(0 if fail == 0 else 1)


if __name__ == "__main__":
    main()
