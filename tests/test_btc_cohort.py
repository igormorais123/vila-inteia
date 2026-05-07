"""Test engine/btc_cohort.py."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from engine.btc_cohort import fit_cohorts, predict_cohort, evaluate_cohort

ok = fail = 0
def check(c, m):
    global ok, fail
    if c: ok += 1; print(f"  OK  {m}")
    else: fail += 1; print(f"  FAIL {m}")

print("=== test_btc_cohort ===")

print("\n[1] fit_cohorts produces per-cohort rate")
events = [
    {"outcome": 1, "fwd_days": 30, "threshold_pct": 5},
    {"outcome": 1, "fwd_days": 30, "threshold_pct": 5},
    {"outcome": 0, "fwd_days": 30, "threshold_pct": 5},
    {"outcome": 0, "fwd_days": 30, "threshold_pct": 10},
    {"outcome": 0, "fwd_days": 30, "threshold_pct": 10},
]
rates = fit_cohorts(events)
check((30, 5) in rates, f"cohort (30,5) present (got {list(rates.keys())})")
check(abs(rates[(30, 5)] - 2/3) < 1e-9, f"(30,5) rate = 2/3 (got {rates[(30, 5)]})")
check(rates[(30, 10)] == 0.0, f"(30,10) rate = 0 (got {rates[(30, 10)]})")

print("\n[2] _global fallback")
check("_global" in rates, "_global key present")
check(abs(rates["_global"] - 2/5) < 1e-9, f"_global = 2/5 (got {rates['_global']})")

print("\n[3] predict_cohort")
p = predict_cohort(30, 5, rates)
check(abs(p - 2/3) < 1e-9, f"predict (30,5) = 2/3 (got {p})")

print("\n[4] predict unseen → fallback to global")
p = predict_cohort(99, 99, rates)
check(p == rates["_global"], f"unseen → global (got {p})")

print("\n[5] evaluate_cohort end-to-end")
test = [
    {"outcome": 1, "fwd_days": 30, "threshold_pct": 5},
    {"outcome": 0, "fwd_days": 30, "threshold_pct": 10},
]
res = evaluate_cohort(test, rates)
check(res["n"] == 2, f"n=2 (got {res['n']})")
check(0 <= res["brier"] <= 1, f"brier in [0,1] (got {res['brier']:.3f})")
check(res["acc"] >= 0.5, f"acc on simple test (got {res['acc']:.2%})")

print("\n[6] empty events handled")
res = evaluate_cohort([], rates)
check(res["n"] == 0 and res["brier"] == 0, "empty case")

print("\n[7] Empty train + edge cases")
rates_empty = fit_cohorts([])
check(rates_empty["_global"] == 0.5, "empty train _global = 0.5")

print(f"\n{ok} ok, {fail} fail")
sys.exit(0 if fail == 0 else 1)
