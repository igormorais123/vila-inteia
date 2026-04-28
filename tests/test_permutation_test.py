"""Tests for engine/permutation_test.py."""

from __future__ import annotations
import sys, csv
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from engine.permutation_test import permutation_test
from engine.post_cutoff_classifier import classify_and_predict
from engine._pred_utils import pairs_from_events

ok = fail = 0
def check(cond, msg):
    global ok, fail
    if cond: ok += 1; print(f"  OK  {msg}")
    else: fail += 1; print(f"  FAIL {msg}")


print("=== test_permutation_test ===")

print("\n[1] Input validation")
r = permutation_test([], [], n_perm=10, metric="brier")
check("erro" in r, "empty → erro")

r = permutation_test([0.5], [0], n_perm=10, metric="brier")
check("erro" in r, "n=1 → erro")

r = permutation_test([0.5, 0.6], [0, 1], n_perm=10, metric="banana")
check("erro" in r, "unknown metric → erro")

r = permutation_test([0.5, 0.6], [0], n_perm=10, metric="brier")
check("erro" in r, "size mismatch → erro")

print("\n[2] Perfect classifier vs random — should reject H0 (low p)")
preds = [0.05, 0.05, 0.05, 0.05, 0.05, 0.95, 0.95, 0.95, 0.95, 0.95]
reals = [0, 0, 0, 0, 0, 1, 1, 1, 1, 1]
r = permutation_test(preds, reals, n_perm=500, metric="brier")
print(f"  observed_brier={r['observed_metric']:.4f} p={r['p_value']:.4f}")
check(r["p_value"] < 0.05, f"perfect → reject H0 (p={r['p_value']:.4f})")
check(r["reject_h0"], "reject_h0=True")

print("\n[3] Random preds — should NOT reject (high p)")
import random as _r
rng = _r.Random(7)
reals_r = [rng.randint(0, 1) for _ in range(20)]
preds_r = [rng.random() for _ in range(20)]
r = permutation_test(preds_r, reals_r, n_perm=500, metric="brier", seed=11)
print(f"  random brier={r['observed_metric']:.4f} p={r['p_value']:.4f}")
check(r["p_value"] > 0.05, f"random → no reject (p={r['p_value']:.4f})")

print("\n[4] Determinism with seed")
r1 = permutation_test(preds, reals, n_perm=300, metric="brier", seed=99)
r2 = permutation_test(preds, reals, n_perm=300, metric="brier", seed=99)
check(r1["p_value"] == r2["p_value"], "same seed → same p")

print("\n[5] Metrics — acc upper-tail; brier/log lower-tail")
for m in ["brier", "log", "acc"]:
    r = permutation_test(preds, reals, n_perm=200, metric=m)
    check(0.0 <= r["p_value"] <= 1.0, f"{m} p in [0,1]")
    check("observed_metric" in r, f"{m} returns observed")


print("\n[6] Real bench: classifier on holdout v1+v2")
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

events = (
    load_csv("/home/pedroafonso/vila-inteia/data/backtest/post_cutoff_q2_2026_holdout.csv")
    + load_csv("/home/pedroafonso/vila-inteia/data/backtest/post_cutoff_q2_2026_holdout_v2.csv")
)
pairs = pairs_from_events(events, classify_and_predict)
preds_real = [p for p, _ in pairs]
reals_real = [y for _, y in pairs]

r = permutation_test(preds_real, reals_real, n_perm=1000, metric="brier")
print(f"  n={r['n']} observed_brier={r['observed_metric']:.4f} p={r['p_value']:.4f} reject={r['reject_h0']}")
check(r["n"] >= 40, f"n>=40 (got {r['n']})")
check(0.0 <= r["p_value"] <= 1.0, "p in [0,1]")
check(r["n_perm"] == 1000, "n_perm=1000")

print(f"\n{ok} ok, {fail} fail")
sys.exit(0 if fail == 0 else 1)
