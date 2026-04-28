"""Tests for engine/ucb1.py."""
import sys, csv, random
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from engine.ucb1 import UCB1, evaluate_ucb1_variants

ok = fail = 0
def check(cond, msg):
    global ok, fail
    if cond: ok += 1; print(f"  OK  {msg}")
    else: fail += 1; print(f"  FAIL {msg}")


print("=== test_ucb1 ===")

print("\n[1] init + bad inputs")
b = UCB1(3)
check(b.n_arms == 3, "n_arms=3")
check(all(c == 0 for c in b.counts), "counts zero init")
try:
    UCB1(0)
    check(False, "expected ValueError")
except ValueError:
    check(True, "raised on n_arms<1")

print("\n[2] first K rounds explore each arm once")
b = UCB1(3)
seen = []
for _ in range(3):
    a = b.select()
    seen.append(a)
    b.update(a, 0.5)
check(set(seen) == {0, 1, 2}, f"all 3 arms in first 3 picks ({seen})")

print("\n[3] UCB picks best mean after exploration on 2-arm stochastic")
b = UCB1(2)
rng = random.Random(13)
for _ in range(300):
    a = b.select()
    if a == 0:
        r = 1.0 if rng.random() < 0.8 else 0.0
    else:
        r = 1.0 if rng.random() < 0.2 else 0.0
    b.update(a, r)
print(f"  counts={b.counts} means=({b.mean(0):.3f}, {b.mean(1):.3f})")
check(b.mean(0) > b.mean(1), "arm0 mean > arm1")
check(b.counts[0] > b.counts[1], "arm0 pulled more")

print("\n[4] evaluate_ucb1_variants synthetic")
events = ([{"outcome_framing": "x", "outcome_real": 1}] +
          [{"outcome_framing": "y", "outcome_real": 0}]) * 10
fns = {
    "perfect": lambda f, c="": 0.95 if "x" in f else 0.05,
    "noisy":   lambda f, c="": 0.55 if "x" in f else 0.45,
    "wrong":   lambda f, c="": 0.05 if "x" in f else 0.95,
}
res = evaluate_ucb1_variants(events, fns)
print(f"  n={res['n']} acc={res['acc']:.1%} brier={res['brier']:.4f}")
print(f"  pulls={res['pulls']} best={res['best_arm']}")
check(res["n"] == 20, f"n=20 ({res['n']})")
check(res["best_arm"] == "perfect", "perfect best")
check(res["pulls"]["perfect"] >= res["pulls"]["wrong"], "perfect pulled >= wrong")

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
res = evaluate_ucb1_variants(
    events, {"base": base, "aggressive": aggressive, "shrunk": shrunk})
print(f"  acc={res['acc']:.1%} brier={res['brier']:.4f} best_arm={res['best_arm']}")
print(f"  pulls={res['pulls']}")
print(f"  means={ {k: round(v,3) for k,v in res['means'].items()} }")
check(res["n"] == 50, f"n=50 ({res['n']})")
check(sum(res["pulls"].values()) == 50, "pulls sum == n")
check(all(v >= 1 for v in res["pulls"].values()), "all arms pulled >=1")

print(f"\n{ok} ok, {fail} fail")
sys.exit(0 if fail == 0 else 1)
