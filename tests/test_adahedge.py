"""Onda 265: testa engine/adahedge.py."""
import sys, csv
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from engine.adahedge import AdaHedge, evaluate_adahedge

ok = fail = 0
def check(cond, msg):
    global ok, fail
    if cond: ok += 1; print(f"  OK  {msg}")
    else: fail += 1; print(f"  FAIL {msg}")


print("=== test_adahedge ===")

print("\n[1] AdaHedge init")
ah = AdaHedge(["a", "b", "c"])
check(ah.k == 3, "k=3")
w = ah._weights()
check(abs(sum(w.values()) - 1.0) < 1e-9, "weights sum to 1")
# Initially uniform
check(all(abs(w[n] - 1/3) < 0.05 for n in w), f"uniform init ({w})")

print("\n[2] Bad expert downweighted online")
ah = AdaHedge(["good", "bad"])
for y in [1, 1, 1, 0, 0]:
    preds = {"good": 0.95 if y == 1 else 0.05, "bad": 0.05 if y == 1 else 0.95}
    p = ah.predict(preds)
    ah.update(preds, y)

w = ah._weights()
print(f"  weights={w}")
print(f"  eta={ah._eta():.3f}")
check(w["good"] > w["bad"], f"good > bad ({w['good']:.3f} > {w['bad']:.3f})")
check(w["good"] > 0.7, f"good dominant ({w['good']:.3f})")

print("\n[3] evaluate_adahedge — synthetic")
events = ([{"outcome_framing": "x", "outcome_real": 1}] +
          [{"outcome_framing": "y", "outcome_real": 0}]) * 6

fns = {
    "perfect": lambda f, c="": 0.9 if "x" in f else 0.1,
    "noisy": lambda f, c="": 0.6 if "x" in f else 0.4,
    "wrong": lambda f, c="": 0.1 if "x" in f else 0.9,
}
res = evaluate_adahedge(events, fns)
print(f"  n={res['n']} acc={res['acc']:.1%} brier={res['brier']:.4f}")
print(f"  best_expert={res['best_expert']} eta={res['final_eta']:.2f}")
print(f"  weights={res['final_weights']}")
check(res["best_expert"] == "perfect", "perfect identified")

print("\n[4] AdaHedge on real classifier — multi variant")
sys.path.insert(0, "/home/pedroafonso/vila-inteia")
from engine.post_cutoff_classifier import classify_and_predict

def base(f, c=""): return classify_and_predict(f, c)[0]
def aggressive(f, c=""):
    p = classify_and_predict(f, c)[0]
    return min(1, max(0, 1.5 * p - 0.25))
def shrunk(f, c=""):
    p = classify_and_predict(f, c)[0]
    return 0.4 + 0.4 * p
def chance(f, c=""): return 0.5

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
           "space_science_q1_2026", "macro_central_banks_q1_2026",
           "corporate_ma_q1_2026", "regulatory_legal_q1_2026",
           "geopolitics_q1_2026"]:
    all_events += load_csv(f"/home/pedroafonso/vila-inteia/data/backtest/{fn}.csv")

experts = {"base": base, "aggressive": aggressive, "shrunk": shrunk, "chance": chance}
res = evaluate_adahedge(all_events, experts)
print(f"  n={res['n']}")
print(f"  acc={res['acc']:.1%} brier={res['brier']:.4f}")
print(f"  best={res['best_expert']} eta_final={res['final_eta']:.2f}")
print(f"  weights:")
for n, w in sorted(res["final_weights"].items(), key=lambda x: -x[1]):
    print(f"    {n:<12} {w:.4f}")
check(res["n"] == 110, f"110 events (got {res['n']})")
check(res["final_weights"]["chance"] < 0.1, "chance downweighted")

print(f"\n{ok} ok, {fail} fail")
sys.exit(0 if fail == 0 else 1)
