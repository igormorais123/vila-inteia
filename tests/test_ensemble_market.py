"""Onda 250: testa engine/ensemble_market.py."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from engine.ensemble_market import (
    weighted_ensemble, majority_vote_ensemble,
    inverse_brier_weights, evaluate_ensemble,
)

ok = fail = 0
def check(cond, msg):
    global ok, fail
    if cond: ok += 1; print(f"  OK  {msg}")
    else: fail += 1; print(f"  FAIL {msg}")


print("=== test_ensemble_market ===")

print("\n[1] weighted_ensemble")
preds = {"a": 0.7, "b": 0.3}
weights = {"a": 1, "b": 1}
p = weighted_ensemble(preds, weights)
check(p == 0.5, f"equal weights → mean (got {p})")

# Skewed weights
weights = {"a": 3, "b": 1}
p = weighted_ensemble(preds, weights)
expected = (0.7*3 + 0.3*1) / 4
check(abs(p - expected) < 1e-9, f"weighted (got {p:.3f}, expected {expected:.3f})")

print("\n[2] majority_vote_ensemble")
# 3 up, 0 down → high confidence
p = majority_vote_ensemble({"a": 0.6, "b": 0.55, "c": 0.7})
check(p == 0.6, f"3 up → 0.6 (got {p})")

# 0 up, 3 down → low confidence
p = majority_vote_ensemble({"a": 0.3, "b": 0.45, "c": 0.4})
check(p == 0.4, f"3 down → 0.4 (got {p})")

# Tie (1 vs 1) → 0.5
p = majority_vote_ensemble({"a": 0.6, "b": 0.4})
check(p == 0.5, f"tie → 0.5 (got {p})")

# Empty
p = majority_vote_ensemble({})
check(p == 0.5, f"empty → 0.5 (got {p})")

print("\n[3] inverse_brier_weights")
briers = {"a": 0.20, "b": 0.40}
weights = inverse_brier_weights(briers)
# a should have higher weight (lower brier)
check(weights["a"] > weights["b"], "lower brier → higher weight")
check(abs(sum(weights.values()) - 1.0) < 1e-9, "sums to 1")

# Edge: brier=0 → weight=1 fallback
briers = {"a": 0, "b": 0.5}
weights = inverse_brier_weights(briers)
check(sum(weights.values()) > 0, "non-zero total")

print("\n[4] evaluate_ensemble end-to-end")
events = [
    {"symbol": "AAPL", "date": "2026-01-30", "real_outcome": 1},
    {"symbol": "MSFT", "date": "2026-01-30", "real_outcome": 0},
]
fns = {
    "s1": lambda s, d: 0.7 if s == "AAPL" else 0.3,
    "s2": lambda s, d: 0.6 if s == "AAPL" else 0.4,
}
res = evaluate_ensemble(events, fns, "majority")
# AAPL: both predict up → 0.6, real 1 → hit
# MSFT: both predict down → 0.4, real 0 → hit
check(res["hits"] == 2, f"majority 2 hits (got {res['hits']})")
check(res["method"] == "majority", "method recorded")

res_avg = evaluate_ensemble(events, fns, "simple_avg")
# AAPL avg = 0.65, real 1 hit. MSFT avg = 0.35, real 0 hit
check(res_avg["hits"] == 2, f"simple_avg 2 hits (got {res_avg['hits']})")

print("\n[5] Bad method raises")
try:
    evaluate_ensemble(events, fns, "unknown")
    check(False, "should raise")
except ValueError:
    check(True, "ValueError raised")

print(f"\n{ok} ok, {fail} fail")
sys.exit(0 if fail == 0 else 1)
