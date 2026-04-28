"""Tests for engine/wasserstein.py."""
import sys, csv, math
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from engine.wasserstein import wasserstein_1d, wasserstein_calibration
from engine.post_cutoff_classifier import classify_and_predict
from engine._pred_utils import pairs_from_events

ok = fail = 0
def check(cond, msg):
    global ok, fail
    if cond: ok += 1; print(f"  OK  {msg}")
    else: fail += 1; print(f"  FAIL {msg}")


print("=== test_wasserstein ===")

print("\n[1] Empty -> 0")
check(wasserstein_1d([], []) == 0.0, "empty 1d")
check(wasserstein_calibration([], []) == 0.0, "empty cal")

print("\n[2] Identical samples -> 0")
v = wasserstein_1d([0.1, 0.5, 0.9], [0.1, 0.5, 0.9])
check(abs(v) < 1e-9, f"identical -> 0 (got {v})")

print("\n[3] Shifted by constant c -> W1 = c (equal length)")
a = [0.0, 0.5, 1.0]
b = [0.2, 0.7, 1.2]
v = wasserstein_1d(a, b)
check(abs(v - 0.2) < 1e-9, f"shift 0.2 (got {v})")

print("\n[4] Symmetry W(a,b) == W(b,a)")
a = [0.1, 0.4, 0.7]
b = [0.2, 0.3, 0.9]
v1 = wasserstein_1d(a, b)
v2 = wasserstein_1d(b, a)
check(abs(v1 - v2) < 1e-9, f"symmetric (a={v1} b={v2})")

print("\n[5] Unequal length: dirac vs uniform")
# Single point at 0 vs three points at 1
v = wasserstein_1d([0.0], [1.0, 1.0, 1.0])
check(abs(v - 1.0) < 1e-9, f"dirac at 0 vs 1 -> 1.0 (got {v})")

print("\n[6] Real bench: classifier on holdout v2 (n=40)")
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
check(len(events) >= 40, f"n>=40 (got {len(events)})")

pairs = pairs_from_events(events, classify_and_predict)
preds = [p for p, _ in pairs]
reals = [y for _, y in pairs]

w = wasserstein_calibration(preds, reals)
print(f"  n={len(pairs)} W1(pred,obs)={w:.4f}")
check(w >= 0.0 and math.isfinite(w), f"finite >=0 (got {w})")
check(w <= 1.0, f"<= 1 since outcomes in [0,1] (got {w})")

print(f"\n{ok} ok, {fail} fail")
sys.exit(0 if fail == 0 else 1)
