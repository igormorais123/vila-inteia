"""Tests for engine/stein_james.py."""
import sys, csv
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from engine.stein_james import stein_james_shrink, apply_stein_to_eb_priors
from engine.post_cutoff_classifier import classify_and_predict

ok = fail = 0
def check(cond, msg):
    global ok, fail
    if cond: ok += 1; print(f"  OK  {msg}")
    else: fail += 1; print(f"  FAIL {msg}")


print("=== test_stein_james ===")

print("\n[1] Empty / d<3 passthrough")
check(stein_james_shrink([], []) == [], "empty -> []")
check(stein_james_shrink([0.4, 0.6], [0.01, 0.01]) == [0.4, 0.6],
      "d=2 -> unchanged")

print("\n[2] Shrinks toward grand mean (d>=3)")
ests = [0.10, 0.50, 0.90]
vars_ = [0.01, 0.01, 0.01]
out = stein_james_shrink(ests, vars_)
grand = sum(ests) / 3
# Each shrunk value should be closer to grand than original
for orig, shrunk in zip(ests, out):
    check(abs(shrunk - grand) <= abs(orig - grand) + 1e-9,
          f"|{shrunk:.3f}-grand| <= |{orig:.3f}-grand|")

print("\n[3] Zero spread -> all equal grand mean")
out = stein_james_shrink([0.5, 0.5, 0.5, 0.5], [0.01] * 4)
check(all(abs(x - 0.5) < 1e-9 for x in out), f"all 0.5 -> 0.5 (got {out})")

print("\n[4] High variance, tight spread -> heavy shrinkage")
out = stein_james_shrink([0.49, 0.50, 0.51], [0.5, 0.5, 0.5])
# Factor likely <= 0 -> clamped to 0 -> all = grand
grand = 0.50
check(all(abs(x - grand) < 1e-6 for x in out),
      f"strong shrink (got {out})")

print("\n[5] Low variance, wide spread -> mild shrinkage")
ests = [0.1, 0.3, 0.5, 0.7, 0.9]
out = stein_james_shrink(ests, [1e-5] * 5)
# Should be close to original
diffs = [abs(o - e) for o, e in zip(out, ests)]
check(max(diffs) < 0.05, f"mild shrink, max diff={max(diffs):.4f}")

print("\n[6] apply_stein_to_eb_priors basics")
eb = {"a": 0.2, "b": 0.5, "c": 0.8, "d": 0.6}
n = {"a": 10, "b": 20, "c": 5, "d": 15}
out = apply_stein_to_eb_priors(eb, n)
check(set(out.keys()) == set(eb.keys()), "keys preserved")
check(all(0 <= v <= 1 for v in out.values()), "values in [0,1]")

# Empty + d<3
check(apply_stein_to_eb_priors({}, {}) == {}, "empty dict -> empty")
check(apply_stein_to_eb_priors({"a": 0.3, "b": 0.7}, {"a": 10, "b": 5})
      == {"a": 0.3, "b": 0.7}, "d=2 -> unchanged")

print("\n[7] Real bench: shrink per-category empirical rates on holdout")
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

events = load_csv("/home/pedroafonso/vila-inteia/data/backtest/post_cutoff_q2_2026_holdout_v2.csv")
check(len(events) >= 40, f"holdout n>=40 (got {len(events)})")

# Build per-cat empirical rates
agg = defaultdict(lambda: {"k": 0, "n": 0})
for e in events:
    _, label = classify_and_predict(e["outcome_framing"], e["contexto"])
    agg[label]["n"] += 1
    agg[label]["k"] += e["outcome_real"]

eb_priors = {lbl: s["k"] / s["n"] for lbl, s in agg.items() if s["n"] > 0}
n_per_cat = {lbl: s["n"] for lbl, s in agg.items() if s["n"] > 0}
shrunk = apply_stein_to_eb_priors(eb_priors, n_per_cat)

print(f"  d={len(eb_priors)} categories")
print(f"  raw mean={sum(eb_priors.values())/len(eb_priors):.3f} "
      f"shrunk mean={sum(shrunk.values())/len(shrunk):.3f}")
# Spread should not grow
raw_spread = max(eb_priors.values()) - min(eb_priors.values())
shrunk_spread = max(shrunk.values()) - min(shrunk.values())
check(shrunk_spread <= raw_spread + 1e-9,
      f"shrunk spread {shrunk_spread:.3f} <= raw {raw_spread:.3f}")
check(all(0 <= v <= 1 for v in shrunk.values()), "all shrunk in [0,1]")

print(f"\n{ok} ok, {fail} fail")
sys.exit(0 if fail == 0 else 1)
