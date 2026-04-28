"""Tests for engine/regret_analysis.py."""
import sys, csv
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from engine.regret_analysis import compute_regret, compare_regrets

ok = fail = 0
def check(cond, msg):
    global ok, fail
    if cond: ok += 1; print(f"  OK  {msg}")
    else: fail += 1; print(f"  FAIL {msg}")


print("=== test_regret_analysis ===")

print("\n[1] empty -> empty curve")
out = compute_regret([], "a")
check(out == [], "empty list")

print("\n[2] compute_regret monotone non-decreasing on known losses")
rounds = [
    {"a": 0.1, "b": 0.5, "_alg_loss": 0.5},
    {"a": 0.2, "b": 0.6, "_alg_loss": 0.6},
    {"a": 0.0, "b": 0.4, "_alg_loss": 0.4},
]
curve = compute_regret(rounds, best_arm="a")
print(f"  curve={curve}")
# expected diffs: (0.5-0.1, 0.6-0.2, 0.4-0.0) cumsum = 0.4, 0.8, 1.2
check(abs(curve[0] - 0.4) < 1e-9, f"r1=0.4 ({curve[0]:.3f})")
check(abs(curve[-1] - 1.2) < 1e-9, f"r3=1.2 ({curve[-1]:.3f})")
check(all(curve[i] <= curve[i+1] + 1e-9 for i in range(len(curve)-1)),
      "non-decreasing")

print("\n[3] regret zero when alg matches best")
rounds = [
    {"a": 0.1, "b": 0.5, "_alg_loss": 0.1},
    {"a": 0.2, "b": 0.6, "_alg_loss": 0.2},
]
curve = compute_regret(rounds, "a")
check(all(abs(c) < 1e-9 for c in curve), "zero regret when always picking best")

print("\n[4] compare_regrets synthetic 3-classifier")
events = ([{"outcome_framing": "x", "outcome_real": 1}] +
          [{"outcome_framing": "y", "outcome_real": 0}]) * 20
fns = {
    "perfect": lambda f, c="": 0.95 if "x" in f else 0.05,
    "noisy":   lambda f, c="": 0.55 if "x" in f else 0.45,
    "wrong":   lambda f, c="": 0.05 if "x" in f else 0.95,
}
res = compare_regrets(events, fns, methods=["thompson", "ucb1", "exp3"], seed=1)
meta = res["_meta"]
print(f"  best_arm_global={meta['best_arm_global']} (n={meta['n_rounds']})")
for m in ["thompson", "ucb1", "exp3"]:
    r = res[m]
    print(f"  {m:<10}  final_regret={r['final_regret']:.4f}  alg_loss={r['alg_total_loss']:.3f}  best={r['best_total_loss']:.3f}")
check(meta["best_arm_global"] == "perfect", "perfect = best in hindsight")
for m in ["thompson", "ucb1", "exp3"]:
    check(res[m]["final_regret"] >= -1e-9, f"{m} regret >= 0")
    check(len(res[m]["regret_curve"]) == 40, f"{m} curve len 40")

print("\n[5] real bench: post_cutoff_q2_2026 holdout (n=50)")
from engine.post_cutoff_classifier import classify_and_predict

def base(f, c=""): return classify_and_predict(f, c)[0]
def aggressive(f, c=""):
    p = classify_and_predict(f, c)[0]
    return min(1, max(0, 1.5 * p - 0.25))
def shrunk(f, c=""):
    p = classify_and_predict(f, c)[0]
    return 0.4 + 0.4 * p

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

base_dir = "/home/pedroafonso/vila-inteia/data/backtest"
events = (load_csv(f"{base_dir}/post_cutoff_q2_2026_holdout.csv") +
          load_csv(f"{base_dir}/post_cutoff_q2_2026_holdout_v2.csv"))
print(f"  loaded n={len(events)}")

res = compare_regrets(
    events,
    {"base": base, "aggressive": aggressive, "shrunk": shrunk},
    methods=["thompson", "ucb1", "exp3"],
    seed=11,
)
meta = res["_meta"]
print(f"  best_arm_global={meta['best_arm_global']}")
print(f"  arm_total_loss={ {k: round(v,3) for k,v in meta['arm_total_loss'].items()} }")
for m in ["thompson", "ucb1", "exp3"]:
    r = res[m]
    print(f"  {m:<10}  final_regret={r['final_regret']:.4f}  alg_loss={r['alg_total_loss']:.3f}")
check(meta["n_rounds"] == 50, f"n=50 ({meta['n_rounds']})")
# Switching algorithms can occasionally beat best-fixed-arm in hindsight on a
# given realization (regret can be slightly negative). Bound is loose.
for m in ["thompson", "ucb1", "exp3"]:
    check(res[m]["final_regret"] >= -2.0, f"{m} regret >= -2 ({res[m]['final_regret']:.3f})")
    check(len(res[m]["regret_curve"]) == 50, f"{m} curve len 50")

print(f"\n{ok} ok, {fail} fail")
sys.exit(0 if fail == 0 else 1)
