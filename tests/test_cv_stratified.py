"""Test stratified k-fold CV on post-cutoff bench."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from engine.backtest_real import carregar_dataset
from engine.cv_stratified import evaluate_stratified_cv, stratified_kfold
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


print("=== test_cv_stratified ===")

print("\n[1] stratified_kfold preserva balance")
events = (
    [{"evento_id": f"p{i}", "outcome_real": 1, "outcome_framing": "x", "contexto": ""} for i in range(10)]
    + [{"evento_id": f"n{i}", "outcome_real": 0, "outcome_framing": "y", "contexto": ""} for i in range(10)]
)
splits = stratified_kfold(events, n_folds=5, seed=1)
check(len(splits) == 5, f"5 folds (got {len(splits)})")
for i, (tr, te) in enumerate(splits):
    pos = sum(1 for e in te if e["outcome_real"] == 1)
    neg = sum(1 for e in te if e["outcome_real"] == 0)
    check(pos == 2 and neg == 2, f"fold {i}: 2 pos + 2 neg (got {pos}+{neg})")

print("\n[2] determinístico por seed")
s1 = stratified_kfold(events, n_folds=5, seed=7)
s2 = stratified_kfold(events, n_folds=5, seed=7)
ids1 = [[e["evento_id"] for e in te] for _, te in s1]
ids2 = [[e["evento_id"] for e in te] for _, te in s2]
check(ids1 == ids2, "same seed -> same split")

print("\n[3] evaluate_stratified_cv schema")
res = evaluate_stratified_cv(events, classify_and_predict, n_folds=5)
for k in ["mean_acc", "std_acc", "mean_brier", "std_brier", "n_folds", "fold_sizes"]:
    check(k in res, f"key {k} present")
check(0.0 <= res["mean_acc"] <= 1.0, f"mean_acc in [0,1] (got {res['mean_acc']:.3f})")
check(res["std_acc"] >= 0.0, f"std_acc >= 0 (got {res['std_acc']:.3f})")

print("\n[4] real bench post_cutoff Q1 2026 (n=20)")
ev1 = carregar_dataset(REPO / "data" / "backtest" / "post_cutoff_q1_2026.csv")
ev2 = carregar_dataset(REPO / "data" / "backtest" / "post_cutoff_q1_2026_v2.csv")
combined = ev1 + ev2
check(len(combined) == 20, f"n=20 combined (got {len(combined)})")
res_real = evaluate_stratified_cv(combined, classify_and_predict, n_folds=5)
check(res_real["n_folds"] == 5, f"5 folds on real (got {res_real['n_folds']})")
print(f"     mean_acc={res_real['mean_acc']:.3f} +/- {res_real['std_acc']:.3f}")
print(f"     mean_brier={res_real['mean_brier']:.3f} +/- {res_real['std_brier']:.3f}")
print(f"     fold_sizes={res_real['fold_sizes']}")
check(0.0 <= res_real["mean_acc"] <= 1.0, "real mean_acc in [0,1]")
check(res_real["mean_brier"] >= 0.0, "real mean_brier >= 0")

print("\n[5] insufficient -> error")
small = [{"evento_id": "a", "outcome_real": 1, "outcome_framing": "x", "contexto": ""}]
res_small = evaluate_stratified_cv(small, classify_and_predict, n_folds=5)
check("error" in res_small or res_small.get("n_folds", 0) <= 1, "small set handled")

print(f"\n{ok} ok, {fail} fail")
sys.exit(0 if fail == 0 else 1)
