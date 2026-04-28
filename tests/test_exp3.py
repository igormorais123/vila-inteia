"""Tests for engine/exp3.py."""
import sys, csv, random
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from engine.exp3 import EXP3, evaluate_exp3_variants

ok = fail = 0
def check(cond, msg):
    global ok, fail
    if cond: ok += 1; print(f"  OK  {msg}")
    else: fail += 1; print(f"  FAIL {msg}")


print("=== test_exp3 ===")

print("\n[1] init + bad inputs")
e = EXP3(3, 0.1)
check(e.n_arms == 3, "n_arms=3")
check(abs(sum(e._probs()) - 1.0) < 1e-9, "probs sum to 1")
check(all(abs(p - 1/3) < 1e-9 for p in e._probs()), "uniform init")
try:
    EXP3(3, 0)
    check(False, "expected ValueError eta=0")
except ValueError:
    check(True, "raised on eta<=0")

print("\n[2] suggested_eta sane")
eta = EXP3.suggested_eta(3, 100)
print(f"  eta(K=3, T=100)={eta:.4f}")
check(eta > 0, "eta > 0")
check(eta < 1, "eta < 1")

print("\n[3] arms with high reward gain weight")
rng = random.Random(5)
e = EXP3(2, eta=0.3, rng=rng)
rwd = random.Random(9)
for _ in range(500):
    a = e.select()
    r = (1.0 if rwd.random() < 0.85 else 0.0) if a == 0 else (1.0 if rwd.random() < 0.15 else 0.0)
    e.update(a, r)
probs = e._probs()
print(f"  final probs={probs}")
check(probs[0] > probs[1], f"arm0 prob > arm1 ({probs[0]:.3f} vs {probs[1]:.3f})")

print("\n[4] evaluate_exp3_variants synthetic")
events = ([{"outcome_framing": "x", "outcome_real": 1}] +
          [{"outcome_framing": "y", "outcome_real": 0}]) * 30
fns = {
    "perfect": lambda f, c="": 0.95 if "x" in f else 0.05,
    "noisy":   lambda f, c="": 0.55 if "x" in f else 0.45,
    "wrong":   lambda f, c="": 0.05 if "x" in f else 0.95,
}
res = evaluate_exp3_variants(events, fns, seed=2)
print(f"  n={res['n']} acc={res['acc']:.1%} brier={res['brier']:.4f}")
print(f"  pulls={res['pulls']}")
print(f"  probs={ {k: round(v,3) for k,v in res['probs'].items()} } eta={res['eta']:.4f}")
check(res["n"] == 60, f"n=60 ({res['n']})")
check(abs(sum(res["probs"].values()) - 1.0) < 1e-6, "probs sum to 1")
check(res["probs"]["perfect"] >= res["probs"]["wrong"], "perfect prob >= wrong")

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
res = evaluate_exp3_variants(
    events, {"base": base, "aggressive": aggressive, "shrunk": shrunk}, seed=4)
print(f"  acc={res['acc']:.1%} brier={res['brier']:.4f} best_arm={res['best_arm']}")
print(f"  pulls={res['pulls']}")
print(f"  probs={ {k: round(v,3) for k,v in res['probs'].items()} } eta={res['eta']:.4f}")
check(res["n"] == 50, f"n=50 ({res['n']})")
check(sum(res["pulls"].values()) == 50, "pulls sum == n")
check(abs(sum(res["probs"].values()) - 1.0) < 1e-6, "probs sum to 1")

print(f"\n{ok} ok, {fail} fail")
sys.exit(0 if fail == 0 else 1)
