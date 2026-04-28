"""Tests for engine/spiegelhalter_z.py."""
import sys, csv
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from engine.spiegelhalter_z import spiegelhalter_z

ok = fail = 0
def check(cond, msg):
    global ok, fail
    if cond: ok += 1; print(f"  OK  {msg}")
    else: fail += 1; print(f"  FAIL {msg}")


print("=== test_spiegelhalter_z ===")

print("\n[1] Empty -> z=None")
r = spiegelhalter_z([], [])
check(r["z"] is None, "empty z=None")

print("\n[2] Perfect calibration on degenerate {0,1} -> denom=0 -> p=1")
r = spiegelhalter_z([0.0, 1.0, 0.0, 1.0], [0, 1, 0, 1])
check(abs(r["p_value"] - 1.0) < 1e-9, f"degenerate p=1 (got {r['p_value']})")
check(not r["reject_h0"], "no reject_h0 on perfect")

print("\n[3] Well-calibrated p=0.5 with balanced y -> z near 0, fail to reject")
preds = [0.5] * 100
reals = [1] * 50 + [0] * 50
r = spiegelhalter_z(preds, reals)
check(abs(r["z"]) < 1e-9, f"z ~ 0 (got {r['z']})")
check(r["p_value"] > 0.05, f"do not reject (p={r['p_value']})")

print("\n[4] Severe miscalibration -> reject H0")
# Predict 0.1 always, actual 80% positive -> grossly under-confident on 1s
preds = [0.1] * 50
reals = [1] * 40 + [0] * 10
r = spiegelhalter_z(preds, reals)
check(r["z"] > 3, f"z >> 0 (got {r['z']})")
check(r["reject_h0"], f"reject_h0 (p={r['p_value']})")

print("\n[5] Arithmetic check: numerator = sum(y - p)")
preds = [0.3, 0.7, 0.4, 0.6]
reals = [0, 1, 1, 0]
r = spiegelhalter_z(preds, reals)
expected_num = (0 - 0.3) + (1 - 0.7) + (1 - 0.4) + (0 - 0.6)
check(abs(r["numerator"] - expected_num) < 1e-12,
      f"numerator ok (got {r['numerator']} vs {expected_num})")

print("\n[6] Real classifier on holdout v2 (n=40)")
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


events = load_csv("/home/pedroafonso/vila-inteia/data/backtest/post_cutoff_q2_2026_holdout_v2.csv")
preds = []
reals = []
for e in events:
    p, _ = classify_and_predict(e["outcome_framing"], e["contexto"])
    preds.append(p)
    reals.append(e["outcome_real"])

r = spiegelhalter_z(preds, reals)
print(f"  N={r['n']} z={r['z']:.3f} p={r['p_value']:.4f} reject={r['reject_h0']}")
check(r["z"] is not None, "z finite")
check(r["n"] == 40, f"n=40 (got {r['n']})")

print(f"\n{ok} ok, {fail} fail")
sys.exit(0 if fail == 0 else 1)
