"""Tests for engine/wilcoxon_signed_rank.py."""

from __future__ import annotations
import sys, csv
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from engine.wilcoxon_signed_rank import wilcoxon_signed_rank, per_event_brier
from engine.post_cutoff_classifier import classify_and_predict
from engine._pred_utils import pairs_from_events

ok = fail = 0
def check(cond, msg):
    global ok, fail
    if cond: ok += 1; print(f"  OK  {msg}")
    else: fail += 1; print(f"  FAIL {msg}")


print("=== test_wilcoxon_signed_rank ===")

print("\n[1] Input validation")
r = wilcoxon_signed_rank([], [])
check("erro" in r, "empty → erro")
r = wilcoxon_signed_rank([1.0, 2.0], [1.0])
check("erro" in r, "mismatched sizes → erro")

print("\n[2] Identical losses → all diffs zero, n_nonzero=0")
losses = [0.1, 0.2, 0.05, 0.3, 0.15]
r = wilcoxon_signed_rank(losses, losses)
check(r["n_nonzero"] == 0, "n_nonzero=0")
check(not r["reject_h0"], "no reject")
check(r["p_value"] == 1.0, "p=1.0")

print("\n[3] B clearly better → W_pos large, W_neg small")
losses_a = [0.5, 0.6, 0.55, 0.7, 0.4, 0.65, 0.5, 0.6, 0.55, 0.7,
            0.5, 0.6, 0.55, 0.7, 0.4, 0.65, 0.5, 0.6, 0.55, 0.7,
            0.5, 0.6, 0.55, 0.7, 0.4]
losses_b = [0.1, 0.05, 0.15, 0.2, 0.08, 0.12, 0.1, 0.05, 0.15, 0.2,
            0.1, 0.05, 0.15, 0.2, 0.08, 0.12, 0.1, 0.05, 0.15, 0.2,
            0.1, 0.05, 0.15, 0.2, 0.08]
r = wilcoxon_signed_rank(losses_a, losses_b)
print(f"  W={r['W']:.1f} W_pos={r['W_pos']:.1f} z={r['z']:.3f} p={r['p_value']:.4f} n_nz={r['n_nonzero']}")
check(r["W_pos"] > r["W_neg"], "W_pos > W_neg (a worse)")
check(r["reject_h0"], "reject H0")

print("\n[4] Symmetry: swap → W_pos/W_neg swap, same |z|")
r1 = wilcoxon_signed_rank(losses_a, losses_b)
r2 = wilcoxon_signed_rank(losses_b, losses_a)
check(abs(r1["W_pos"] - r2["W_neg"]) < 1e-9, "W_pos/W_neg swap")
check(abs(abs(r1["z"]) - abs(r2["z"])) < 1e-9, "|z| invariant")
check(abs(r1["p_value"] - r2["p_value"]) < 1e-9, "p invariant on swap")

print("\n[5] Tie handling: zero diffs excluded, ties get average rank")
a = [0.1, 0.2, 0.3, 0.3, 0.4]
b = [0.2, 0.1, 0.3, 0.3, 0.5]  # diffs: -0.1, 0.1, 0, 0, -0.1
r = wilcoxon_signed_rank(a, b)
check(r["n_nonzero"] == 3, f"n_nonzero=3 (got {r['n_nonzero']})")
check(0.0 <= r["p_value"] <= 1.0, "p in [0,1]")

print("\n[6] Real bench: per-event Brier stretch=True vs False on holdout_v2")
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

losses_a = per_event_brier(preds_a, reals)
losses_b = per_event_brier(preds_b, reals)

r = wilcoxon_signed_rank(losses_a, losses_b)
print(f"  n={len(reals)} n_nz={r['n_nonzero']} W={r['W']:.1f} z={r.get('z',0):.3f} p={r['p_value']:.4f}")
check(len(reals) == 40, f"n=40 (got {len(reals)})")
check(0.0 <= r["p_value"] <= 1.0, "p in [0,1]")
check(r["n_nonzero"] >= 0, "n_nonzero defined")

print(f"\n{ok} ok, {fail} fail")
sys.exit(0 if fail == 0 else 1)
