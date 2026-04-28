"""Onda 267: testa engine/combined_pipeline.py."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from engine.combined_pipeline import (
    bootstrap_brier_ci, time_series_cv, murphy_decomposition, combined_report,
)
from engine.post_cutoff_classifier import classify_and_predict

ok = fail = 0
def check(cond, msg):
    global ok, fail
    if cond: ok += 1; print(f"  OK  {msg}")
    else: fail += 1; print(f"  FAIL {msg}")


print("=== test_combined_pipeline ===")

events = [
    {"outcome_framing": "war event", "outcome_real": 1, "contexto": ""},
    {"outcome_framing": "Olympics held", "outcome_real": 1, "contexto": ""},
    {"outcome_framing": "tech launches", "outcome_real": 0, "contexto": ""},
    {"outcome_framing": "Generic random", "outcome_real": 1, "contexto": ""},
    {"outcome_framing": "Bitcoin > $200k", "outcome_real": 0, "contexto": ""},
    {"outcome_framing": "FOMC reunião realizada", "outcome_real": 1, "contexto": ""},
    {"outcome_framing": "Brazil PEC reforma", "outcome_real": 0, "contexto": ""},
    {"outcome_framing": "war attack Iran", "outcome_real": 1, "contexto": ""},
    {"outcome_framing": "Apple lança iPad", "outcome_real": 1, "contexto": ""},
    {"outcome_framing": "election candidate wins", "outcome_real": 1, "contexto": ""},
] * 3  # 30 events

print("\n[1] bootstrap_brier_ci")
pt, lo, hi = bootstrap_brier_ci(events, classify_and_predict, n_resamples=200)
print(f"  point={pt:.3f} CI=[{lo:.3f}, {hi:.3f}]")
check(0 <= lo <= pt <= hi <= 1, "CI ordered")
check(hi - lo > 0, "non-zero CI width")

print("\n[2] time_series_cv")
res = time_series_cv(events, classify_and_predict, n_folds=5)
print(f"  folds={res['n_folds']} mean_acc={res['mean_acc']:.2%} std_acc={res['std_acc']:.2%}")
check(res["n_folds"] >= 2, "≥2 folds")
check(0 <= res["mean_acc"] <= 1, "acc in [0,1]")

print("\n[3] murphy_decomposition")
res = murphy_decomposition(events, classify_and_predict)
print(f"  brier={res['brier']} REL={res['reliability']} RES={res['resolution']} UNC={res['uncertainty']}")
# Brier ≈ REL + UNC - RES (with binning approximation)
expected = res["reliability"] + res["uncertainty"] - res["resolution"]
check(abs(res["brier"] - expected) < 0.05, f"brier ≈ REL+UNC-RES ({res['brier']:.3f} vs {expected:.3f})")

print("\n[4] combined_report end-to-end")
res = combined_report(events, classify_and_predict)
print(f"  n={res['n']} acc={res['base_acc']} brier={res['base_brier']}")
print(f"  CI={res['bootstrap_brier_ci']}")
print(f"  selective tau=0.3: cov={res['selective'][0.3]['coverage']:.2f} acc={res['selective'][0.3]['selective_acc']:.2%}")
print(f"  conformal singleton acc={res['conformal']['singleton_acc']:.2%}")
print(f"  murphy REL={res['murphy']['reliability']}")
check(res["n"] == 30, f"n=30 (got {res['n']})")
check("base_acc" in res and "selective" in res and "conformal" in res, "all components present")

print("\n[5] Real holdout n=50")
import csv
def load(fp):
    out = []
    with open(fp) as f:
        for r in csv.DictReader(f):
            try: out.append({'outcome_framing': r.get('outcome_framing',''), 'contexto': r.get('contexto',''), 'outcome_real': int(r['outcome_real'])})
            except: pass
    return out

holdout = []
for fn in ["post_cutoff_q2_2026_holdout", "post_cutoff_q2_2026_holdout_v2"]:
    holdout += load(f"/home/pedroafonso/vila-inteia/data/backtest/{fn}.csv")

res = combined_report(holdout, classify_and_predict)
print(f"  Holdout Q2 n={res['n']}")
print(f"  acc={res['base_acc']:.1%} brier={res['base_brier']:.4f} CI={res['bootstrap_brier_ci']}")
print(f"  Selective tau=0.30: acc={res['selective'][0.3]['selective_acc']:.2%} cov={res['selective'][0.3]['coverage']:.2f}")
print(f"  Murphy: REL={res['murphy']['reliability']:.3f} RES={res['murphy']['resolution']:.3f} UNC={res['murphy']['uncertainty']:.3f}")
print(f"  Time-series CV: acc={res['time_series_cv']['mean_acc']:.1%} ± {res['time_series_cv']['std_acc']:.1%}")
check(res["n"] == 50, f"holdout n=50 (got {res['n']})")
check(res["selective"][0.3]["selective_acc"] > 0.85,
      f"selective tau=0.30 acc > 85% (got {res['selective'][0.3]['selective_acc']:.2%})")

print(f"\n{ok} ok, {fail} fail")
sys.exit(0 if fail == 0 else 1)
