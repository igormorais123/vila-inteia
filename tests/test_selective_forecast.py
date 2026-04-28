"""Onda 264: testa engine/selective_forecast.py."""
import sys, csv
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from engine.selective_forecast import (
    selective_predict, evaluate_selective, risk_coverage_curve,
)

ok = fail = 0
def check(cond, msg):
    global ok, fail
    if cond: ok += 1; print(f"  OK  {msg}")
    else: fail += 1; print(f"  FAIL {msg}")


print("=== test_selective_forecast ===")

print("\n[1] selective_predict")
check(selective_predict(0.95, tau=0.10) == 1, "high p → 1")
check(selective_predict(0.05, tau=0.10) == 0, "low p → 0")
check(selective_predict(0.55, tau=0.10) is None, "borderline → abstain")
check(selective_predict(0.50, tau=0.05) is None, "exactly 0.5 → abstain")
check(selective_predict(0.65, tau=0.10) == 1, "0.65 with tau=0.10 → 1")

print("\n[2] evaluate_selective on classifier")
sys.path.insert(0, "/home/pedroafonso/vila-inteia")
from engine.post_cutoff_classifier import classify_and_predict

def load_csv(fp):
    out = []
    with open(fp) as f:
        for r in csv.DictReader(f):
            try:
                out.append({
                    "outcome_framing": r.get("outcome_framing") or r.get("framing", ""),
                    "contexto": r.get("contexto", ""),
                    "outcome_real": int(r["outcome_real"]),
                })
            except (ValueError, KeyError):
                pass
    return out

all_events = []
for fn in ["post_cutoff_q1_2026", "post_cutoff_q1_2026_v2",
           "post_cutoff_q2_2026_holdout", "brazil_votes_q1_2026",
           "sports_specific_q1_2026", "tech_releases_q1_2026",
           "elections_2026_q1", "space_science_q1_2026",
           "price_predictions_q1_2026", "macro_central_banks_q1_2026",
           "corporate_ma_q1_2026", "regulatory_legal_q1_2026",
           "geopolitics_q1_2026"]:
    all_events += load_csv(f"/home/pedroafonso/vila-inteia/data/backtest/{fn}.csv")

# Default tau
res = evaluate_selective(all_events, classify_and_predict, tau=0.0)
print(f"  tau=0 (no abstain): n={res['n_total']} cov={res['coverage']:.2f} acc={res['selective_acc']:.2%} brier={res['selective_brier']:.4f}")
check(res["coverage"] == 1.0, "tau=0 covers all")

res = evaluate_selective(all_events, classify_and_predict, tau=0.15)
print(f"  tau=0.15: cov={res['coverage']:.2f} acc={res['selective_acc']:.2%} brier={res['selective_brier']:.4f}")
check(res["coverage"] < 1.0, "tau>0 abstains some")
check(res["selective_acc"] >= 0.7, f"selective acc ≥ 0.70 (got {res['selective_acc']:.2%})")

res = evaluate_selective(all_events, classify_and_predict, tau=0.30)
print(f"  tau=0.30: cov={res['coverage']:.2f} acc={res['selective_acc']:.2%} brier={res['selective_brier']:.4f}")
check(res["selective_acc"] >= 0.75, f"high tau → high acc (got {res['selective_acc']:.2%})")

print("\n[3] risk-coverage curve")
curve = risk_coverage_curve(all_events, classify_and_predict)
print(f"  {'tau':>5} {'cov':>6} {'acc':>6} {'brier':>7}")
for r in curve:
    print(f"  {r['tau']:>5.2f} {r['coverage']:>6.2%} {r['selective_acc']:>6.2%} {r['selective_brier']:>7.4f}")
# Acc should be monotonic non-decreasing in tau (mostly)
accs = [r["selective_acc"] for r in curve]
check(accs[-1] >= accs[0] - 0.05, f"high tau ≥ low tau acc ({accs[-1]:.2%} vs {accs[0]:.2%})")

print(f"\n{ok} ok, {fail} fail")
sys.exit(0 if fail == 0 else 1)
