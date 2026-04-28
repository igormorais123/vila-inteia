"""Tests for engine/calibration_error.py."""
import sys, csv
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from engine.calibration_error import calibration_errors
from engine.post_cutoff_classifier import classify_and_predict
from engine._pred_utils import pairs_from_events

ok = fail = 0
def check(cond, msg):
    global ok, fail
    if cond: ok += 1; print(f"  OK  {msg}")
    else: fail += 1; print(f"  FAIL {msg}")


print("=== test_calibration_error ===")

print("\n[1] Empty -> ece/mce None")
r = calibration_errors([], [])
check(r["ece"] is None and r["mce"] is None, f"empty (got {r})")

print("\n[2] Perfect calibration -> ECE = 0, MCE = 0")
# 100 events at p=0.7 with 70% real
preds = [0.7] * 100
reals = [1] * 70 + [0] * 30
r = calibration_errors(preds, reals, n_bins=10)
check(abs(r["ece"]) < 1e-9, f"ECE=0 perfect (got {r['ece']})")
check(abs(r["mce"]) < 1e-9, f"MCE=0 perfect (got {r['mce']})")

print("\n[3] Maximally miscalibrated -> ECE high")
# All preds 0.9 but no positives
preds = [0.9] * 50
reals = [0] * 50
r = calibration_errors(preds, reals, n_bins=10)
check(abs(r["ece"] - 0.9) < 1e-9, f"ECE=0.9 (got {r['ece']})")
check(abs(r["mce"] - 0.9) < 1e-9, f"MCE=0.9 (got {r['mce']})")

print("\n[4] MCE >= ECE always")
preds = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 0.95]
reals = [0,    1,   0,   1,   0,   1,   0,   1,   0,   1]
r = calibration_errors(preds, reals, n_bins=5)
check(r["mce"] >= r["ece"] - 1e-12, f"MCE>=ECE (mce={r['mce']:.3f} ece={r['ece']:.3f})")

print("\n[5] Adaptive vs equal-width: both >= 0, both <= 1")
r_eq = calibration_errors(preds, reals, n_bins=5, adaptive=False)
r_ad = calibration_errors(preds, reals, n_bins=5, adaptive=True)
check(0 <= r_eq["ece"] <= 1 and 0 <= r_ad["ece"] <= 1, "ECE in [0,1]")
check(0 <= r_eq["mce"] <= 1 and 0 <= r_ad["mce"] <= 1, "MCE in [0,1]")

print("\n[6] n_bins parameter respected")
r = calibration_errors(preds, reals, n_bins=10)
check(r["n_bins"] == 10, f"n_bins=10 (got {r['n_bins']})")

print("\n[7] Real bench: classifier on holdout v2 (n=40)")
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

r = calibration_errors(preds, reals, n_bins=10, adaptive=False)
r_ad = calibration_errors(preds, reals, n_bins=10, adaptive=True)
print(f"  n={r['n']} ECE={r['ece']:.4f} MCE={r['mce']:.4f}")
print(f"  adaptive: ECE={r_ad['ece']:.4f} MCE={r_ad['mce']:.4f}")
check(0 <= r["ece"] <= 1, f"ECE in [0,1] (got {r['ece']})")
check(0 <= r["mce"] <= 1, f"MCE in [0,1] (got {r['mce']})")
check(r["mce"] >= r["ece"] - 1e-12, "MCE>=ECE on real")

print(f"\n{ok} ok, {fail} fail")
sys.exit(0 if fail == 0 else 1)
