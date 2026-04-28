"""Tests for engine/kl_divergence.py."""
import sys, csv, math
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from engine.kl_divergence import kl_divergence_binary, kl_calibration
from engine.post_cutoff_classifier import classify_and_predict
from engine._pred_utils import pairs_from_events

ok = fail = 0
def check(cond, msg):
    global ok, fail
    if cond: ok += 1; print(f"  OK  {msg}")
    else: fail += 1; print(f"  FAIL {msg}")


print("=== test_kl_divergence ===")

print("\n[1] Empty -> 0.0")
check(kl_divergence_binary([], []) == 0.0, "empty kl_div")
check(kl_calibration([], []) == 0.0, "empty kl_cal")

print("\n[2] Perfect predictions -> KL ~ 0")
preds = [0.999999] * 50
reals = [1] * 50
v = kl_divergence_binary(preds, reals)
check(v < 1e-3, f"perfect preds kl small (got {v})")

print("\n[3] Bad preds (p=0.001 but y=1) -> high KL")
v = kl_divergence_binary([0.001] * 10, [1] * 10)
check(v > 5.0, f"bad pred high kl (got {v})")

print("\n[4] KL non-negative")
preds = [0.1, 0.3, 0.5, 0.7, 0.9]
reals = [0, 1, 0, 1, 1]
v = kl_divergence_binary(preds, reals)
check(v >= 0.0, f"kl >=0 (got {v})")
v2 = kl_calibration(preds, reals, n_bins=5)
check(v2 >= 0.0, f"kl_cal >=0 (got {v2})")

print("\n[5] Length mismatch raises")
try:
    kl_divergence_binary([0.5, 0.6], [1])
    check(False, "should raise")
except ValueError:
    check(True, "raises ValueError")

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

kl = kl_divergence_binary(preds, reals)
kl_cal = kl_calibration(preds, reals, n_bins=10)
print(f"  n={len(pairs)} KL_binary={kl:.4f} KL_cal={kl_cal:.4f}")
check(kl >= 0.0 and math.isfinite(kl), f"kl finite >=0 (got {kl})")
check(kl_cal >= 0.0 and math.isfinite(kl_cal), f"kl_cal finite >=0 (got {kl_cal})")

print(f"\n{ok} ok, {fail} fail")
sys.exit(0 if fail == 0 else 1)
