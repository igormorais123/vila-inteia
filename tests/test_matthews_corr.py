"""Tests for engine/matthews_corr.py."""
import sys, csv
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from engine.matthews_corr import matthews_corr

ok = fail = 0
def check(cond, msg):
    global ok, fail
    if cond: ok += 1; print(f"  OK  {msg}")
    else: fail += 1; print(f"  FAIL {msg}")


print("=== test_matthews_corr ===")

print("\n[1] Empty -> mcc=None")
r = matthews_corr([], [])
check(r["mcc"] is None, "empty mcc=None")

print("\n[2] Perfect predictions -> MCC = 1")
r = matthews_corr([0.9, 0.9, 0.1, 0.1], [1, 1, 0, 0])
check(abs(r["mcc"] - 1.0) < 1e-9, f"perfect mcc=1 (got {r['mcc']})")

print("\n[3] Inverted predictions -> MCC = -1")
r = matthews_corr([0.1, 0.1, 0.9, 0.9], [1, 1, 0, 0])
check(abs(r["mcc"] - (-1.0)) < 1e-9, f"inverted mcc=-1 (got {r['mcc']})")

print("\n[4] All-positive predictions on imbalanced -> MCC = 0")
# All preds positive: TP+FP > 0 but TN+FN = 0 -> denominator zero
r = matthews_corr([0.9, 0.9, 0.9, 0.9], [1, 0, 1, 0])
check(r["mcc"] == 0.0, f"degenerate mcc=0 (got {r['mcc']})")

print("\n[5] Imbalanced manual check")
# TP=1, FP=1, FN=2, TN=1
# preds=[1,1,0,0,0], reals=[1,0,1,1,0]
# TP=p1=1,r1=1 -> 1; FP=p2=1,r0=0 -> 1; FN=p0,r1 (idx2,3) = 2; TN=p0,r0 (idx4) = 1
preds = [0.9, 0.9, 0.1, 0.1, 0.1]
reals = [1, 0, 1, 1, 0]
r = matthews_corr(preds, reals)
import math
expected = (1 * 1 - 1 * 2) / math.sqrt((1 + 1) * (1 + 2) * (1 + 1) * (1 + 2))
check(abs(r["mcc"] - expected) < 1e-9,
      f"manual computation matches (got {r['mcc']}, expected {expected})")

print("\n[6] Threshold parameter")
preds = [0.55, 0.45, 0.6, 0.4]
reals = [1, 0, 1, 0]
r = matthews_corr(preds, reals, threshold=0.5)
check(abs(r["mcc"] - 1.0) < 1e-9, f"thresh perfect (got {r['mcc']})")

print("\n[7] Real classifier on holdout")
sys.path.insert(0, "/home/pedroafonso/vila-inteia")
from engine.post_cutoff_classifier import classify_and_predict


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


events = []
for fn in ["post_cutoff_q2_2026_holdout", "post_cutoff_q1_2026",
           "brazil_votes_q1_2026"]:
    events += load_csv(f"/home/pedroafonso/vila-inteia/data/backtest/{fn}.csv")

preds = []
reals = []
for e in events:
    p, _ = classify_and_predict(e["outcome_framing"], e["contexto"])
    preds.append(p)
    reals.append(e["outcome_real"])

r = matthews_corr(preds, reals)
print(f"  N={r['n']} TP={r['tp']} FP={r['fp']} FN={r['fn']} TN={r['tn']} MCC={r['mcc']:.3f}")
check(-1.0 <= r["mcc"] <= 1.0, f"MCC in [-1,1] (got {r['mcc']})")
check(r["mcc"] > 0, f"MCC > 0 (got {r['mcc']})")

print(f"\n{ok} ok, {fail} fail")
sys.exit(0 if fail == 0 else 1)
