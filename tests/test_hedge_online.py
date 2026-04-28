"""Onda 259: testa engine/hedge_online.py."""
import sys, csv
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from engine.hedge_online import HedgeAggregator, evaluate_hedge

ok = fail = 0
def check(cond, msg):
    global ok, fail
    if cond: ok += 1; print(f"  OK  {msg}")
    else: fail += 1; print(f"  FAIL {msg}")


print("=== test_hedge_online ===")

print("\n[1] HedgeAggregator init")
agg = HedgeAggregator(["a", "b", "c"], eta=0.5)
check(agg.k == 3, "k=3")
check(all(w == 1.0 for w in agg.weights.values()), "weights init 1")

p = agg.predict({"a": 0.7, "b": 0.3, "c": 0.5})
check(abs(p - 0.5) < 1e-9, f"equal weights → mean ({p:.3f})")

print("\n[2] Update — bad expert downweighted")
agg = HedgeAggregator(["good", "bad"], eta=1.0)
# 5 rounds: good predicts perfectly, bad predicts opposite
for y in [1, 1, 1, 0, 0]:
    preds = {"good": 0.9 if y == 1 else 0.1, "bad": 0.1 if y == 1 else 0.9}
    agg.update(preds, y, loss_fn="brier")

w = agg.normalized_weights()
print(f"  weights: {w}")
check(w["good"] > w["bad"], f"good > bad ({w['good']:.3f} > {w['bad']:.3f})")
check(w["good"] > 0.7, f"good dominant ({w['good']:.3f})")

print("\n[3] evaluate_hedge — synthetic")
events = [
    {"outcome_framing": "x", "contexto": "", "outcome_real": 1},
    {"outcome_framing": "y", "contexto": "", "outcome_real": 0},
    {"outcome_framing": "z", "contexto": "", "outcome_real": 1},
    {"outcome_framing": "w", "contexto": "", "outcome_real": 0},
] * 3

fns = {
    "perfect": lambda f, c: 0.9 if "x" in f or "z" in f else 0.1,
    "random": lambda f, c: 0.5,
    "wrong": lambda f, c: 0.1 if "x" in f or "z" in f else 0.9,
}
res = evaluate_hedge(events, fns, eta=1.0, loss_fn="brier")
print(f"  n={res['n']} acc={res['acc']:.1%} brier={res['brier']:.4f}")
print(f"  weights={res['weights']}")
print(f"  best_expert={res['best_expert']} regret={res['regret_vs_best']:.4f}")
check(res["best_expert"] == "perfect", "perfect identified as best")
check(res["weights"]["perfect"] > res["weights"]["wrong"], "perfect > wrong")

print("\n[4] Hedge on real classifier — combine multiple priors")
sys.path.insert(0, "/home/pedroafonso/vila-inteia")
from engine.post_cutoff_classifier import classify_and_predict

# Build several "experts" from variants
def base(f, c): return classify_and_predict(f, c)[0]
def shrunk(f, c):
    p = classify_and_predict(f, c)[0]
    return 0.4 + 0.4 * p  # shrink toward 0.6
def aggressive(f, c):
    p = classify_and_predict(f, c)[0]
    return min(1, max(0, 1.5 * p - 0.25))  # widen
def chance(f, c): return 0.5
def yes_bias(f, c): return 0.6

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

all_events = []
for fn in ["post_cutoff_q1_2026", "post_cutoff_q1_2026_v2",
           "brazil_votes_q1_2026", "sports_specific_q1_2026",
           "tech_releases_q1_2026", "elections_2026_q1",
           "space_science_q1_2026"]:
    all_events += load_csv(f"/home/pedroafonso/vila-inteia/data/backtest/{fn}.csv")

experts = {"base": base, "shrunk": shrunk, "aggressive": aggressive,
           "chance": chance, "yes_bias": yes_bias}

res = evaluate_hedge(all_events, experts, eta=2.0, loss_fn="brier")
print(f"  n={res['n']}")
print(f"  Hedge: acc={res['acc']:.1%} brier={res['brier']:.4f}")
print(f"  best_expert={res['best_expert']}")
print(f"  final weights:")
for n, w in sorted(res["weights"].items(), key=lambda x: -x[1]):
    print(f"    {n:<15} {w:.4f}")
check(res["n"] == 70, f"70 events (got {res['n']})")
check(res["best_expert"] in {"base", "aggressive", "shrunk"},
      f"non-trivial expert wins (got {res['best_expert']})")
check(res["weights"]["chance"] < 0.05, f"chance downweighted ({res['weights']['chance']:.4f})")

print(f"\n{ok} ok, {fail} fail")
sys.exit(0 if fail == 0 else 1)
