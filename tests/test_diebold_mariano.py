"""Tests for engine/diebold_mariano.py."""

from __future__ import annotations
import sys, csv
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from engine.diebold_mariano import diebold_mariano
from engine.post_cutoff_classifier import classify_and_predict
from engine._pred_utils import pairs_from_events

ok = fail = 0
def check(cond, msg):
    global ok, fail
    if cond: ok += 1; print(f"  OK  {msg}")
    else: fail += 1; print(f"  FAIL {msg}")


print("=== test_diebold_mariano ===")

print("\n[1] Input validation")
r = diebold_mariano([], [], [], loss="brier")
check("erro" in r, "empty input → erro")

r = diebold_mariano([0.5, 0.6], [0.5], [1, 0], loss="brier")
check("erro" in r, "mismatched sizes → erro")

r = diebold_mariano([0.5], [0.6], [1], loss="brier")
check("erro" in r, "n=1 → erro")

r = diebold_mariano([0.5, 0.6], [0.5, 0.6], [1, 0], loss="banana")
check("erro" in r, "unknown loss → erro")

print("\n[2] Identical forecasts → DM stat 0, no rejection")
preds = [0.3, 0.6, 0.4, 0.7, 0.5, 0.2, 0.8, 0.55]
reals = [0, 1, 0, 1, 1, 0, 1, 1]
r = diebold_mariano(preds, preds, reals, loss="brier")
check(abs(r["dm_stat"]) < 1e-9, f"identical → dm_stat≈0 (got {r['dm_stat']:.6f})")
check(not r["reject_h0"], "identical → no reject")

print("\n[3] B clearly better → DM stat positive (loss_a > loss_b)")
reals = [1, 1, 1, 1, 0, 0, 0, 0, 1, 0]
preds_a = [0.5] * 10  # constant
preds_b = [0.9, 0.9, 0.9, 0.9, 0.1, 0.1, 0.1, 0.1, 0.9, 0.1]  # near-perfect
r = diebold_mariano(preds_a, preds_b, reals, loss="brier")
print(f"  dm_stat={r['dm_stat']:.3f} p={r['p_value']:.4f} mean_diff={r['mean_diff']:.4f}")
check(r["dm_stat"] > 0, f"a worse → dm_stat>0")
check(r["mean_diff"] > 0, "mean(loss_a - loss_b) > 0")
check(r["reject_h0"], "reject H0")

print("\n[4] Loss types")
for loss in ["brier", "log", "abs"]:
    r = diebold_mariano(preds_a, preds_b, reals, loss=loss)
    check("dm_stat" in r and "p_value" in r, f"loss={loss} keys present")
    check(0.0 <= r["p_value"] <= 1.0, f"loss={loss} p in [0,1]")

print("\n[5] p-value symmetry: swap a,b → same p, opposite stat")
r1 = diebold_mariano(preds_a, preds_b, reals, loss="brier")
r2 = diebold_mariano(preds_b, preds_a, reals, loss="brier")
check(abs(r1["dm_stat"] + r2["dm_stat"]) < 1e-9, "stat sign-flip on swap")
check(abs(r1["p_value"] - r2["p_value"]) < 1e-9, "two-sided p invariant on swap")


print("\n[6] Real bench: stretch=True vs stretch=False on holdout v1+v2")
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

def clf_stretch(framing, contexto=""):
    return classify_and_predict(framing, contexto, apply_stretch=True)

def clf_no_stretch(framing, contexto=""):
    return classify_and_predict(framing, contexto, apply_stretch=False)

pairs_a = pairs_from_events(events, clf_stretch)
pairs_b = pairs_from_events(events, clf_no_stretch)
preds_a = [p for p, _ in pairs_a]
preds_b = [p for p, _ in pairs_b]
reals = [y for _, y in pairs_a]

r = diebold_mariano(preds_a, preds_b, reals, loss="brier")
print(f"  n={r['n']} dm_stat={r['dm_stat']:.3f} p={r['p_value']:.4f} mean_diff={r['mean_diff']:+.5f}")
check(r["n"] == len(reals) and r["n"] >= 40, f"n>=40 (got {r['n']})")
check(0.0 <= r["p_value"] <= 1.0, "p in [0,1]")

print(f"\n{ok} ok, {fail} fail")
sys.exit(0 if fail == 0 else 1)
