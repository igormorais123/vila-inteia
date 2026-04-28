"""Testes Bayesian Model Averaging (Hoeting et al. 1999)."""

from __future__ import annotations
import sys, os, csv
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.bayesian_model_averaging import bma_predict, _log_likelihood
from engine.post_cutoff_classifier import classify_and_predict

ok, fail = 0, 0


def teste(nome, cond, det=""):
    global ok, fail
    if cond: ok += 1; print(f"  OK  {nome}")
    else:    fail += 1; print(f"  FAIL {nome} {det}")


def t_vazio():
    r = bma_predict({}, [])
    teste("vazio: erro", "erro" in r)


def t_posterior_soma_1():
    preds = {
        "A": [0.8, 0.7, 0.9, 0.2],
        "B": [0.5, 0.5, 0.5, 0.5],
    }
    y = [1, 1, 1, 0]
    r = bma_predict(preds, y)
    s = sum(r["posterior_weights"].values())
    teste(f"posterior soma 1 (got {s:.6f})", abs(s - 1.0) < 1e-9)


def t_modelo_melhor_pesa_mais():
    """Modelo bom domina posterior."""
    preds = {
        "good": [0.9, 0.9, 0.9, 0.1],
        "bad":  [0.1, 0.1, 0.1, 0.9],
    }
    y = [1, 1, 1, 0]
    r = bma_predict(preds, y)
    pw = r["posterior_weights"]
    teste(f"good > bad (good={pw['good']:.3f})", pw["good"] > pw["bad"])
    teste("good > 0.9", pw["good"] > 0.9)


def t_avg_em_range():
    preds = {"A": [0.8] * 4, "B": [0.4] * 4}
    y = [1, 0, 1, 0]
    r = bma_predict(preds, y)
    for p in r["predictions"]:
        teste(f"avg in [0.4, 0.8] got {p:.3f}", 0.4 - 1e-9 <= p <= 0.8 + 1e-9)


def t_prior_uniforme_default():
    preds = {"A": [0.5]*3, "B": [0.5]*3, "C": [0.5]*3}
    y = [1, 0, 1]
    r = bma_predict(preds, y)
    # Likelihoods iguais (preds idênticos) → posterior = prior uniforme = 1/3
    for k, w in r["posterior_weights"].items():
        teste(f"posterior uniforme {k} (got {w:.3f})", abs(w - 1/3) < 1e-9)


def t_prior_custom():
    preds = {"A": [0.5]*3, "B": [0.5]*3}
    y = [1, 0, 1]
    r = bma_predict(preds, y, prior_weights={"A": 0.9, "B": 0.1})
    teste(f"prior A>B (A={r['posterior_weights']['A']:.3f})",
          r["posterior_weights"]["A"] > r["posterior_weights"]["B"])


def t_log_likelihood_perfect():
    """Pred = real → log_lik ~ 0 (ignorando clip)."""
    ll = _log_likelihood([1.0, 0.0, 1.0], [1, 0, 1])
    teste(f"perfect log_lik ~ 0 (got {ll:.3f})", ll > -1e-3)


def t_real_bench_post_cutoff():
    """Bench em CSV n=40: BMA bate single model."""
    csv_path = "/home/pedroafonso/vila-inteia/data/backtest/post_cutoff_q2_2026_holdout_v2.csv"
    if not os.path.exists(csv_path):
        teste("CSV exists", False, csv_path)
        return
    preds_classifier = []
    preds_const = []
    preds_prior = []
    reals = []
    with open(csv_path) as f:
        r = csv.DictReader(f)
        for row in r:
            framing = row.get("outcome_framing", "")
            ctx = row.get("contexto", "")
            p, _ = classify_and_predict(framing, ctx)
            preds_classifier.append(p)
            preds_const.append(0.5)
            preds_prior.append(float(row["probabilidade_prior"]))
            reals.append(int(row["outcome_real"]))
    n = len(reals)
    teste(f"n=40 (got {n})", n == 40)

    out = bma_predict(
        {"classifier": preds_classifier, "constant": preds_const, "prior": preds_prior},
        reals,
    )
    bma_preds = out["predictions"]
    bma_brier = sum((bma_preds[i] - reals[i]) ** 2 for i in range(n)) / n
    const_brier = sum((0.5 - reals[i]) ** 2 for i in range(n)) / n
    teste(f"BMA brier {bma_brier:.4f} < constant {const_brier:.4f}",
          bma_brier < const_brier)
    teste(f"posterior weights soma 1 ({sum(out['posterior_weights'].values()):.4f})",
          abs(sum(out["posterior_weights"].values()) - 1.0) < 1e-9)


def main():
    print("=== test_bayesian_model_averaging ===")
    for fn in [t_vazio, t_posterior_soma_1, t_modelo_melhor_pesa_mais,
               t_avg_em_range, t_prior_uniforme_default, t_prior_custom,
               t_log_likelihood_perfect, t_real_bench_post_cutoff]:
        try: fn()
        except Exception as e:
            global fail; fail += 1
            print(f"  FAIL {fn.__name__}: {type(e).__name__}: {e}")
            import traceback; traceback.print_exc()
    print(f"\n{ok} ok, {fail} fail")
    sys.exit(0 if fail == 0 else 1)


if __name__ == "__main__":
    main()
