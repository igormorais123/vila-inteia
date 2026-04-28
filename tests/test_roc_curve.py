"""Tests for engine/roc_curve.py."""

from __future__ import annotations
import sys, csv
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from engine.roc_curve import roc_curve_points, roc_auc
from engine.post_cutoff_classifier import classify_and_predict
from engine._pred_utils import pairs_from_events

ok = fail = 0
def check(cond, msg):
    global ok, fail
    if cond: ok += 1; print(f"  OK  {msg}")
    else: fail += 1; print(f"  FAIL {msg}")


print("=== test_roc_curve ===")

print("\n[1] Edge cases")
check(roc_curve_points([], []) == [], "empty → []")
check(roc_auc([], []) == 0.5, "empty AUC → 0.5")
check(roc_auc([0.1, 0.5], [1, 1]) == 0.5, "all positive → AUC 0.5")
check(roc_auc([0.1, 0.5], [0, 0]) == 0.5, "all negative → AUC 0.5")

print("\n[2] Perfect classifier → AUC=1.0")
preds = [0.1, 0.2, 0.3, 0.7, 0.8, 0.9]
reals = [0, 0, 0, 1, 1, 1]
auc = roc_auc(preds, reals)
print(f"  AUC={auc:.4f}")
check(abs(auc - 1.0) < 1e-9, f"perfect AUC=1.0 (got {auc})")

print("\n[3] Inverted classifier → AUC=0.0")
preds_inv = [0.9, 0.8, 0.7, 0.3, 0.2, 0.1]
reals = [0, 0, 0, 1, 1, 1]
auc = roc_auc(preds_inv, reals)
check(abs(auc - 0.0) < 1e-9, f"inverted AUC=0.0 (got {auc})")

print("\n[4] Random/tied → AUC=0.5")
preds_t = [0.5, 0.5, 0.5, 0.5]
reals_t = [0, 1, 0, 1]
auc = roc_auc(preds_t, reals_t)
check(abs(auc - 0.5) < 1e-9, f"all tied AUC=0.5 (got {auc})")

print("\n[5] AUC bounded in [0,1]; curve starts (0,0) ends (1,1)")
preds = [0.1, 0.4, 0.6, 0.35, 0.8]
reals = [0, 0, 1, 1, 1]
auc = roc_auc(preds, reals)
pts = roc_curve_points(preds, reals)
print(f"  AUC={auc:.4f}, points={len(pts)}")
check(0.0 <= auc <= 1.0, f"AUC in [0,1]")
check(pts[0] == (0.0, 0.0), f"starts (0,0): {pts[0]}")
check(pts[-1] == (1.0, 1.0), f"ends (1,1): {pts[-1]}")
# monotonic non-decreasing in fpr
fprs = [x for x, _ in pts]
check(all(fprs[i] <= fprs[i+1] for i in range(len(fprs)-1)), "fpr non-decreasing")


print("\n[6] Real bench on holdout v1+v2")
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

events = (
    load_csv("/home/pedroafonso/vila-inteia/data/backtest/post_cutoff_q2_2026_holdout.csv")
    + load_csv("/home/pedroafonso/vila-inteia/data/backtest/post_cutoff_q2_2026_holdout_v2.csv")
)
pairs = pairs_from_events(events, classify_and_predict)
preds_real = [p for p, _ in pairs]
reals_real = [y for _, y in pairs]

auc = roc_auc(preds_real, reals_real)
pts = roc_curve_points(preds_real, reals_real)
print(f"  n={len(reals_real)} AUC={auc:.4f} curve_points={len(pts)}")
check(len(reals_real) >= 40, f"n>=40 (got {len(reals_real)})")
check(0.0 <= auc <= 1.0, f"AUC in [0,1] (got {auc:.4f})")
check(len(pts) >= 2, f"curve has points")

print(f"\n{ok} ok, {fail} fail")
sys.exit(0 if fail == 0 else 1)
