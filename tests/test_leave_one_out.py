"""Test LOO CV + per-event sensitivity on post-cutoff bench."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from engine.backtest_real import carregar_dataset
from engine.leave_one_out import loo_cv, loo_sensitivity
from engine.post_cutoff_classifier import classify_and_predict

REPO = Path(__file__).resolve().parent.parent

ok = fail = 0


def check(cond, msg):
    global ok, fail
    if cond:
        ok += 1
        print(f"  OK  {msg}")
    else:
        fail += 1
        print(f"  FAIL {msg}")


print("=== test_leave_one_out ===")

print("\n[1] loo_cv schema sintético")
events = [
    {"evento_id": "a", "outcome_framing": "Israel attack Iran", "contexto": "", "outcome_real": 1},
    {"evento_id": "b", "outcome_framing": "Apple lança product", "contexto": "", "outcome_real": 0},
    {"evento_id": "c", "outcome_framing": "Generic", "contexto": "", "outcome_real": 1},
]
res = loo_cv(events, classify_and_predict)
check(res["n"] == 3, f"n=3 (got {res['n']})")
for k in ["loo_acc", "loo_brier", "per_fold_acc", "per_fold_brier"]:
    check(k in res, f"{k} present")
check(0.0 <= res["loo_acc"] <= 1.0, f"loo_acc in [0,1] (got {res['loo_acc']:.3f})")

print("\n[2] loo_sensitivity per-event delta-Brier")
sens = loo_sensitivity(events, classify_and_predict)
check(len(sens) == 3, f"3 events scored (got {len(sens)})")
for d in sens:
    for k in ["evento_id", "delta_brier", "delta_acc", "per_event_brier"]:
        check(k in d, f"{k} key in entry")
abs_deltas = [abs(d["delta_brier"]) for d in sens]
check(abs_deltas == sorted(abs_deltas, reverse=True), "sorted desc by |delta_brier|")

print("\n[3] sensitivity reflete worst-Brier event como mais influente")
worst_id = max(sens, key=lambda d: d["per_event_brier"])["evento_id"]
top_id = sens[0]["evento_id"]
check(worst_id == top_id, f"top influence = worst-Brier (top={top_id}, worst={worst_id})")

print("\n[4] real bench post_cutoff Q1 2026 (n=20)")
ev1 = carregar_dataset(REPO / "data" / "backtest" / "post_cutoff_q1_2026.csv")
ev2 = carregar_dataset(REPO / "data" / "backtest" / "post_cutoff_q1_2026_v2.csv")
combined = ev1 + ev2
res_real = loo_cv(combined, classify_and_predict)
check(res_real["n"] == 20, f"n=20 (got {res_real['n']})")
print(f"     loo_acc={res_real['loo_acc']:.3f}  loo_brier={res_real['loo_brier']:.3f}")

sens_real = loo_sensitivity(combined, classify_and_predict)
check(len(sens_real) == 20, f"20 sensitivity entries (got {len(sens_real)})")
top5 = sens_real[:5]
print("     top-5 mais influentes:")
for d in top5:
    print(f"       {d['evento_id']:>8} y={d['outcome_real']} delta_brier={d['delta_brier']:+.4f} per_b={d['per_event_brier']:.3f}")
check(all(abs(d["delta_brier"]) >= abs(sens_real[-1]["delta_brier"]) for d in top5),
      "top-5 deltas dominate tail")

print("\n[5] degenerate cases")
res0 = loo_cv([], classify_and_predict)
check("error" in res0, "empty -> error")
res1 = loo_sensitivity([{"outcome_real": 1, "outcome_framing": "x"}], classify_and_predict)
check(res1 == [], "n=1 -> empty sensitivity")

print(f"\n{ok} ok, {fail} fail")
sys.exit(0 if fail == 0 else 1)
