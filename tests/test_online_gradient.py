"""Tests engine/online_gradient.py — Online Gradient Descent (Zinkevich 2003)."""
import sys, csv, math
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from engine.online_gradient import (
    OGDAggregator, evaluate_ogd, _project_simplex,
)
from engine.post_cutoff_classifier import classify_and_predict

ok = fail = 0
def check(cond, msg):
    global ok, fail
    if cond: ok += 1; print(f"  OK  {msg}")
    else: fail += 1; print(f"  FAIL {msg}")


print("=== test_online_gradient ===")

print("\n[1] simplex projection")
v = [0.5, 0.5, 0.5]
proj = _project_simplex(v)
check(abs(sum(proj) - 1.0) < 1e-9, f"sum=1 ({sum(proj):.6f})")
check(all(p >= 0 for p in proj), "all non-negative")

# unbalanced
v2 = [3.0, -1.0, 0.0]
p2 = _project_simplex(v2)
check(abs(sum(p2) - 1.0) < 1e-9, "unbalanced sum=1")
check(all(x >= 0 for x in p2), "unbalanced non-negative")
check(p2[0] > p2[1] and p2[0] > p2[2], "largest stays largest")

print("\n[2] OGDAggregator init")
agg = OGDAggregator(K=3, lr_schedule="sqrt")
check(agg.K == 3, "K=3")
check(abs(sum(agg.w) - 1.0) < 1e-9, "weights sum to 1")
check(all(abs(w - 1/3) < 1e-9 for w in agg.w), "uniform init")

p = agg.predict([0.7, 0.3, 0.5])
check(abs(p - 0.5) < 1e-9, f"uniform prediction = mean ({p:.4f})")

print("\n[3] update — bad expert downweighted")
agg = OGDAggregator(K=2, lr_schedule="const", lr_const=0.5)
# good expert says 1 when y=1; bad inverts
for _ in range(40):
    for y in [1, 0]:
        probs = [0.95 if y == 1 else 0.05, 0.05 if y == 1 else 0.95]
        agg.update(probs, y)

print(f"  weights={agg.w}")
check(agg.w[0] > agg.w[1], f"good > bad ({agg.w[0]:.3f} > {agg.w[1]:.3f})")
check(agg.w[0] > 0.7, f"good dominant ({agg.w[0]:.3f})")

print("\n[4] evaluate_ogd — synthetic")
events = ([{"outcome_framing": "x", "outcome_real": 1}] +
          [{"outcome_framing": "y", "outcome_real": 0}]) * 10

fns = {
    "perfect": lambda f, c="": 0.92 if "x" in f else 0.08,
    "noisy":   lambda f, c="": 0.6 if "x" in f else 0.4,
    "wrong":   lambda f, c="": 0.1 if "x" in f else 0.9,
    "chance":  lambda f, c="": 0.5,
}
res = evaluate_ogd(events, fns, lr_schedule="sqrt")
print(f"  n={res['n']} acc={res['acc']:.1%} brier={res['brier']:.4f}")
print(f"  best_expert={res['best_expert']}")
print(f"  final_weights={res['final_weights']}")
check(res["best_expert"] == "perfect", "perfect identified")
check(res["final_weights"]["perfect"] >= res["final_weights"]["wrong"],
      "perfect >= wrong")

print("\n[5] OGD on real classifier — Q2 holdout, multi-variant")
def base(f, c=""): return classify_and_predict(f, c)[0]
def aggressive(f, c=""):
    p = classify_and_predict(f, c)[0]
    return min(1.0, max(0.0, 1.5 * p - 0.25))
def shrunk(f, c=""):
    p = classify_and_predict(f, c)[0]
    return 0.4 + 0.4 * p
def chance(f, c=""): return 0.5
def yes_bias(f, c=""): return 0.65

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

events = load_csv("/home/pedroafonso/vila-inteia/data/backtest/post_cutoff_q2_2026_holdout.csv")
events += load_csv("/home/pedroafonso/vila-inteia/data/backtest/post_cutoff_q2_2026_holdout_v2.csv")

experts = {
    "base": base, "aggressive": aggressive, "shrunk": shrunk,
    "chance": chance, "yes_bias": yes_bias,
}

res = evaluate_ogd(events, experts, lr_schedule="sqrt")
print(f"  n={res['n']} acc={res['acc']:.1%} brier={res['brier']:.4f}")
print(f"  best_expert={res['best_expert']} best_loss={res['best_loss']:.4f}")
print(f"  final_weights:")
for n, w in sorted(res["final_weights"].items(), key=lambda x: -x[1]):
    print(f"    {n:<12} {w:.4f}")

check(res["n"] >= 40, f"events loaded ({res['n']})")
check(abs(sum(res["final_weights"].values()) - 1.0) < 1e-6,
      "final weights still on simplex")
check(all(w >= 0 for w in res["final_weights"].values()),
      "all weights non-negative")
check(0.0 <= res["brier"] <= 1.0, f"brier in [0,1] ({res['brier']:.4f})")

print(f"\n{ok} ok, {fail} fail")
sys.exit(0 if fail == 0 else 1)
