"""Tests for engine/entropy_score.py."""
import sys, csv, math
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from engine.entropy_score import (
    predictive_entropy, conditional_entropy, information_gain,
)
from engine.post_cutoff_classifier import classify_and_predict
from engine._pred_utils import pairs_from_events

ok = fail = 0
def check(cond, msg):
    global ok, fail
    if cond: ok += 1; print(f"  OK  {msg}")
    else: fail += 1; print(f"  FAIL {msg}")


print("=== test_entropy_score ===")

print("\n[1] Empty -> 0")
check(predictive_entropy([]) == 0.0, "empty pred_h")
check(conditional_entropy([], []) == 0.0, "empty cond_h")
check(information_gain([], []) == 0.0, "empty info_gain")

print("\n[2] Confident preds (p=0 or 1) -> H = 0")
v = predictive_entropy([0.0, 1.0, 0.0, 1.0])
check(abs(v) < 1e-9, f"confident H=0 (got {v})")

print("\n[3] Maximum uncertainty p=0.5 -> H = ln(2)")
v = predictive_entropy([0.5] * 10)
check(abs(v - math.log(2)) < 1e-9, f"max H=ln2 (got {v})")

print("\n[4] Conditional entropy: perfect preds -> ~0")
preds = [0.999, 0.001, 0.999, 0.001]
reals = [1, 0, 1, 0]
v = conditional_entropy(preds, reals)
check(v < 1e-2, f"perfect cond_h~0 (got {v})")

print("\n[5] Information gain: perfect preds on balanced -> ~ ln(2)")
preds = [0.999] * 50 + [0.001] * 50
reals = [1] * 50 + [0] * 50
ig = information_gain(preds, reals)
check(ig > 0.5, f"perfect IG large (got {ig})")
# IG <= H(Y)
check(ig <= math.log(2) + 1e-6, f"IG <= H(Y) (got {ig})")

print("\n[6] Information gain: useless preds -> ~0")
preds = [0.5] * 100
reals = [1] * 50 + [0] * 50
ig = information_gain(preds, reals)
# H(Y|P=0.5) = -0.5 log 0.5 - 0.5 log 0.5 = ln 2 = H(Y), so IG ~ 0
check(abs(ig) < 1e-3, f"useless IG~0 (got {ig})")

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

h = predictive_entropy(preds)
hc = conditional_entropy(preds, reals)
ig = information_gain(preds, reals)
print(f"  n={len(pairs)} pred_H={h:.4f} cond_H={hc:.4f} IG={ig:.4f}")
check(h >= 0.0 and math.isfinite(h), f"pred_h finite >=0 (got {h})")
check(hc >= 0.0 and math.isfinite(hc), f"cond_h finite >=0 (got {hc})")
check(math.isfinite(ig), f"ig finite (got {ig})")

print(f"\n{ok} ok, {fail} fail")
sys.exit(0 if fail == 0 else 1)
