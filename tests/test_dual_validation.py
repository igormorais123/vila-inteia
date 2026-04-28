"""Test dual validation report on post-cutoff bench."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from engine.backtest_real import carregar_dataset
from engine.dual_validation import dual_validation_report
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


print("=== test_dual_validation ===")

print("\n[1] schema básico contém chaves esperadas")
events = (
    [{"evento_id": f"p{i}", "outcome_real": 1, "outcome_framing": "Israel attack", "contexto": ""} for i in range(8)]
    + [{"evento_id": f"n{i}", "outcome_real": 0, "outcome_framing": "Apple lança", "contexto": ""} for i in range(8)]
)
res = dual_validation_report(events, classify_and_predict, n_folds=4)
expected = [
    "train_test_acc", "train_test_brier",
    "loo_acc", "loo_brier",
    "stratified_acc_mean", "stratified_acc_std",
]
for k in expected:
    check(k in res, f"key {k} present")

print("\n[2] valores em ranges válidos")
check(0.0 <= res["train_test_acc"] <= 1.0, f"tt_acc in [0,1] (got {res['train_test_acc']:.3f})")
check(0.0 <= res["loo_acc"] <= 1.0, f"loo_acc in [0,1] (got {res['loo_acc']:.3f})")
check(res["loo_brier"] >= 0.0, f"loo_brier >= 0 (got {res['loo_brier']:.3f})")
check(res["stratified_acc_std"] >= 0.0, f"stratified std >= 0")

print("\n[3] insufficient -> error")
res_small = dual_validation_report([{"outcome_real": 1, "outcome_framing": "x"}], classify_and_predict, n_folds=5)
check("error" in res_small, "n<n_folds -> error")

print("\n[4] real bench post_cutoff Q1 2026 (n=20)")
ev1 = carregar_dataset(REPO / "data" / "backtest" / "post_cutoff_q1_2026.csv")
ev2 = carregar_dataset(REPO / "data" / "backtest" / "post_cutoff_q1_2026_v2.csv")
combined = ev1 + ev2
res_real = dual_validation_report(combined, classify_and_predict, n_folds=5)
check(res_real["n"] == 20, f"n=20 (got {res_real['n']})")
print(f"     train_test_acc  = {res_real['train_test_acc']:.3f}")
print(f"     train_test_brier= {res_real['train_test_brier']:.3f}")
print(f"     loo_acc         = {res_real['loo_acc']:.3f}")
print(f"     loo_brier       = {res_real['loo_brier']:.3f}")
print(f"     strat_acc       = {res_real['stratified_acc_mean']:.3f} +/- {res_real['stratified_acc_std']:.3f}")
print(f"     strat_brier     = {res_real['stratified_brier_mean']:.3f} +/- {res_real['stratified_brier_std']:.3f}")
check(0.0 <= res_real["loo_acc"] <= 1.0, "real loo_acc in [0,1]")
check(res_real["stratified_n_folds"] == 5, f"5 folds on real (got {res_real['stratified_n_folds']})")

print("\n[5] cross-method consistency: loo vs stratified mean próximos")
diff = abs(res_real["loo_acc"] - res_real["stratified_acc_mean"])
print(f"     |loo_acc - strat_acc_mean| = {diff:.3f}")
check(diff <= 0.25, f"acc methods agree within 0.25 (got {diff:.3f})")
brier_diff = abs(res_real["loo_brier"] - res_real["stratified_brier_mean"])
check(brier_diff <= 0.15, f"brier methods agree within 0.15 (got {brier_diff:.3f})")

print(f"\n{ok} ok, {fail} fail")
sys.exit(0 if fail == 0 else 1)
