"""Tests for engine/thompson_sampling.py."""
import sys, csv, random
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from engine.thompson_sampling import ThompsonSampler, evaluate_thompson_classifier_variants

ok = fail = 0
def check(cond, msg):
    global ok, fail
    if cond: ok += 1; print(f"  OK  {msg}")
    else: fail += 1; print(f"  FAIL {msg}")


print("=== test_thompson_sampling ===")

print("\n[1] init + invariants")
ts = ThompsonSampler(3)
check(ts.n_arms == 3, "n_arms=3")
check(all(a == 1.0 for a in ts.alpha), "alpha=1 init")
check(all(b == 1.0 for b in ts.beta), "beta=1 init")
try:
    ThompsonSampler(0)
    check(False, "expected ValueError on n_arms=0")
except ValueError:
    check(True, "raised on n_arms<1")

print("\n[2] update changes posterior")
ts = ThompsonSampler(2, rng=random.Random(42))
ts.update(0, 1.0)
ts.update(0, 1.0)
ts.update(1, 0.0)
check(ts.alpha[0] == 3.0, f"alpha[0]=3 ({ts.alpha[0]})")
check(ts.beta[0] == 1.0, f"beta[0]=1 ({ts.beta[0]})")
check(ts.beta[1] == 2.0, f"beta[1]=2 ({ts.beta[1]})")
check(ts.posterior_mean(0) > ts.posterior_mean(1),
      f"arm0 mean > arm1 ({ts.posterior_mean(0):.3f} vs {ts.posterior_mean(1):.3f})")

print("\n[3] selects good arm in synthetic 2-arm")
random.seed(7)
ts = ThompsonSampler(2, rng=random.Random(7))
# Arm 0 reward prob 0.9, arm 1 reward prob 0.1
rng = random.Random(11)
for _ in range(200):
    a = ts.select()
    if a == 0:
        r = 1.0 if rng.random() < 0.9 else 0.0
    else:
        r = 1.0 if rng.random() < 0.1 else 0.0
    ts.update(a, r)
check(ts.posterior_mean(0) > ts.posterior_mean(1),
      f"arm0 > arm1 ({ts.posterior_mean(0):.3f} vs {ts.posterior_mean(1):.3f})")
check(ts.posterior_mean(0) > 0.7, f"arm0 mean > 0.7 ({ts.posterior_mean(0):.3f})")

print("\n[4] evaluate_thompson_classifier_variants synthetic")
events = ([{"outcome_framing": "x", "outcome_real": 1}] +
          [{"outcome_framing": "y", "outcome_real": 0}]) * 10
fns = {
    "perfect": lambda f, c="": 0.95 if "x" in f else 0.05,
    "noisy":   lambda f, c="": 0.55 if "x" in f else 0.45,
    "wrong":   lambda f, c="": 0.05 if "x" in f else 0.95,
}
res = evaluate_thompson_classifier_variants(events, fns, seed=1)
print(f"  n={res['n']} acc={res['acc']:.1%} brier={res['brier']:.4f}")
print(f"  pulls={res['pulls']}")
print(f"  posterior_means={ {k: round(v,3) for k,v in res['posterior_means'].items()} }")
check(res["n"] == 20, f"n=20 ({res['n']})")
check(res["best_arm"] == "perfect", f"best=perfect ({res['best_arm']})")
check(res["pulls"]["perfect"] >= res["pulls"]["wrong"],
      "perfect pulled >= wrong")

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
res = evaluate_thompson_classifier_variants(
    events, {"base": base, "aggressive": aggressive, "shrunk": shrunk}, seed=3)
print(f"  acc={res['acc']:.1%} brier={res['brier']:.4f} best_arm={res['best_arm']}")
print(f"  pulls={res['pulls']}")
print(f"  posterior_means={ {k: round(v,3) for k,v in res['posterior_means'].items()} }")
check(res["n"] == 50, f"n=50 ({res['n']})")
check(sum(res["pulls"].values()) == 50, "pulls sum == n")
check(0.0 <= res["acc"] <= 1.0, "acc in [0,1]")
check(0.0 <= res["brier"] <= 1.0, "brier in [0,1]")

print(f"\n{ok} ok, {fail} fail")
sys.exit(0 if fail == 0 else 1)
