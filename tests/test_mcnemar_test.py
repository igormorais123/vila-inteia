"""Tests for engine/mcnemar_test.py."""

from __future__ import annotations
import sys, csv
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from engine.mcnemar_test import mcnemar_test
from engine.post_cutoff_classifier import classify_and_predict
from engine._pred_utils import pairs_from_events

ok = fail = 0
def check(cond, msg):
    global ok, fail
    if cond: ok += 1; print(f"  OK  {msg}")
    else: fail += 1; print(f"  FAIL {msg}")


print("=== test_mcnemar_test ===")

print("\n[1] Input validation")
r = mcnemar_test([], [], [])
check("erro" in r, "empty input → erro")
r = mcnemar_test([0.5, 0.6], [0.5], [1, 0])
check("erro" in r, "mismatched sizes → erro")

print("\n[2] Identical predictions → b=c=0, no rejection")
preds = [0.3, 0.6, 0.4, 0.7, 0.8]
reals = [0, 1, 0, 1, 1]
r = mcnemar_test(preds, preds, reals)
check(r["b"] == 0 and r["c"] == 0, f"b=c=0 (got b={r['b']},c={r['c']})")
check(r["chi_square"] == 0.0, "chi2=0")
check(not r["reject_h0"], "no reject")

print("\n[3] Counts: a=correct, b=wrong on simple case")
# preds_a all correct; preds_b all wrong
reals = [1, 1, 0, 0, 1, 0]
preds_a = [0.9, 0.9, 0.1, 0.1, 0.9, 0.1]  # all right
preds_b = [0.1, 0.1, 0.9, 0.9, 0.1, 0.9]  # all wrong
r = mcnemar_test(preds_a, preds_b, reals, continuity=False)
check(r["b"] == 6, f"b=6 (got {r['b']})")
check(r["c"] == 0, f"c=0 (got {r['c']})")
expected_chi = (6 - 0) ** 2 / (6 + 0)
check(abs(r["chi_square"] - expected_chi) < 1e-9, f"chi2={expected_chi} (got {r['chi_square']:.4f})")

print("\n[4] Continuity correction reduces chi2")
r1 = mcnemar_test(preds_a, preds_b, reals, continuity=False)
r2 = mcnemar_test(preds_a, preds_b, reals, continuity=True)
check(r2["chi_square"] < r1["chi_square"], f"cont {r2['chi_square']:.3f} < uncorr {r1['chi_square']:.3f}")
check(0.0 <= r2["p_value"] <= 1.0, "p in [0,1]")

print("\n[5] Symmetry: swap a,b → b/c swap, same chi2")
r1 = mcnemar_test(preds_a, preds_b, reals)
r2 = mcnemar_test(preds_b, preds_a, reals)
check(r1["b"] == r2["c"] and r1["c"] == r2["b"], "b/c swap")
check(abs(r1["chi_square"] - r2["chi_square"]) < 1e-9, "chi2 invariant on swap")
check(abs(r1["p_value"] - r2["p_value"]) < 1e-9, "p invariant on swap")

print("\n[6] Real bench: stretch=True vs stretch=False on holdout_v2")
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

def clf_stretch(framing, contexto=""):
    return classify_and_predict(framing, contexto, apply_stretch=True)
def clf_no_stretch(framing, contexto=""):
    return classify_and_predict(framing, contexto, apply_stretch=False)

pairs_a = pairs_from_events(events, clf_stretch)
pairs_b = pairs_from_events(events, clf_no_stretch)
preds_a = [p for p, _ in pairs_a]
preds_b = [p for p, _ in pairs_b]
reals = [y for _, y in pairs_a]

r = mcnemar_test(preds_a, preds_b, reals)
print(f"  n={r['n']} b={r['b']} c={r['c']} chi2={r['chi_square']:.3f} p={r['p_value']:.4f}")
check(r["n"] == 40, f"n=40 (got {r['n']})")
check(0.0 <= r["p_value"] <= 1.0, "p in [0,1]")
check(r["b"] >= 0 and r["c"] >= 0, "b,c non-negative")

print(f"\n{ok} ok, {fail} fail")
sys.exit(0 if fail == 0 else 1)
