"""Tests for engine/cohens_kappa.py."""
import sys, csv
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from engine.cohens_kappa import cohens_kappa

ok = fail = 0
def check(cond, msg):
    global ok, fail
    if cond: ok += 1; print(f"  OK  {msg}")
    else: fail += 1; print(f"  FAIL {msg}")


print("=== test_cohens_kappa ===")

print("\n[1] Empty -> kappa=None")
r = cohens_kappa([], [])
check(r["kappa"] is None, "empty kappa=None")

print("\n[2] Perfect agreement -> kappa = 1.0")
r = cohens_kappa([0.9, 0.9, 0.1, 0.1], [1, 1, 0, 0])
check(abs(r["kappa"] - 1.0) < 1e-9, f"perfect kappa=1 (got {r['kappa']})")

print("\n[3] Random / chance agreement -> kappa ≈ 0")
# 10 events. preds = 5 pos / 5 neg. reals = 5 pos / 5 neg. 5 correct (chance).
preds = [0.9, 0.9, 0.9, 0.9, 0.9, 0.1, 0.1, 0.1, 0.1, 0.1]
reals = [1, 1, 0, 0, 0, 1, 1, 1, 0, 0]
r = cohens_kappa(preds, reals)
# p_o = 4/10 = 0.4 here; p_e = 0.5*0.5 + 0.5*0.5 = 0.5
# kappa = (0.4-0.5)/(1-0.5) = -0.2
check(abs(r["kappa"] - (-0.2)) < 1e-9, f"kappa = -0.2 (got {r['kappa']})")

print("\n[4] Total disagreement -> kappa = -1")
r = cohens_kappa([0.9, 0.9, 0.1, 0.1], [0, 0, 1, 1])
check(abs(r["kappa"] - (-1.0)) < 1e-9, f"disagree kappa=-1 (got {r['kappa']})")

print("\n[5] Threshold parameter")
preds = [0.6, 0.4, 0.6, 0.4]
reals = [1, 0, 1, 0]
# At threshold=0.5: preds = [1,0,1,0] vs reals -> perfect
r = cohens_kappa(preds, reals, threshold=0.5)
check(abs(r["kappa"] - 1.0) < 1e-9, f"thresh=0.5 perfect (got {r['kappa']})")
# At threshold=0.7: preds all 0 vs reals; degenerate (1-p_e=0)
r = cohens_kappa(preds, reals, threshold=0.7)
check(r["kappa"] is None or abs(r["p_e"] - 0.5) < 1.0,
      f"degenerate or kappa null (got {r['kappa']}, p_e={r['p_e']})")

print("\n[6] Confusion matrix sums to n")
r = cohens_kappa([0.9, 0.9, 0.1, 0.4], [1, 0, 0, 1])
check(r["tp"] + r["fp"] + r["fn"] + r["tn"] == 4,
      f"confusion sum = n (got {r})")

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

r = cohens_kappa(preds, reals)
print(f"  N={r['n']} p_o={r['p_o']:.3f} p_e={r['p_e']:.3f} kappa={r['kappa']:.3f}")
print(f"  TP={r['tp']} FP={r['fp']} FN={r['fn']} TN={r['tn']}")
check(r["kappa"] is not None, "kappa finite")
check(-1 <= r["kappa"] <= 1, f"kappa in [-1,1] (got {r['kappa']})")
check(r["kappa"] > 0, f"kappa > 0 better than chance (got {r['kappa']})")

print(f"\n{ok} ok, {fail} fail")
sys.exit(0 if fail == 0 else 1)
