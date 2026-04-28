"""Tests for engine/mann_whitney_u.py."""

from __future__ import annotations
import sys, csv
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from engine.mann_whitney_u import mann_whitney_u
from engine.post_cutoff_classifier import classify_and_predict
from engine._pred_utils import pairs_from_events
from engine.wilcoxon_signed_rank import per_event_brier

ok = fail = 0
def check(cond, msg):
    global ok, fail
    if cond: ok += 1; print(f"  OK  {msg}")
    else: fail += 1; print(f"  FAIL {msg}")


print("=== test_mann_whitney_u ===")

print("\n[1] Input validation")
r = mann_whitney_u([], [1.0, 2.0])
check("erro" in r, "empty a → erro")
r = mann_whitney_u([1.0], [])
check("erro" in r, "empty b → erro")

print("\n[2] Identical samples → U near n_a*n_b/2, no rejection")
a = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8]
b = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8]
r = mann_whitney_u(a, b)
expected = len(a) * len(b) / 2.0
check(abs(r["U_a"] - expected) < 1e-9, f"U_a≈{expected} (got {r['U_a']})")
check(not r["reject_h0"], "no reject")

print("\n[3] Strict separation a < b → U_a small (a ranks low)")
a = [0.1, 0.2, 0.3, 0.15, 0.25, 0.18, 0.22, 0.28, 0.12, 0.16,
     0.1, 0.2, 0.3, 0.15, 0.25]
b = [0.7, 0.8, 0.9, 0.75, 0.85, 0.78, 0.82, 0.88, 0.72, 0.76,
     0.7, 0.8, 0.9, 0.75, 0.85]
r = mann_whitney_u(a, b)
print(f"  U={r['U']:.1f} U_a={r['U_a']:.1f} U_b={r['U_b']:.1f} z={r['z']:.3f} p={r['p_value']:.4f}")
check(r["U_a"] == 0.0, f"U_a=0 (got {r['U_a']})")
check(r["reject_h0"], "reject H0")

print("\n[4] Symmetry: swap → U_a/U_b swap, same p")
r1 = mann_whitney_u(a, b)
r2 = mann_whitney_u(b, a)
check(abs(r1["U_a"] - r2["U_b"]) < 1e-9, "U swap")
check(abs(r1["p_value"] - r2["p_value"]) < 1e-9, "p invariant")

print("\n[5] Ties: U_a + U_b = n_a*n_b always")
a = [1, 1, 2, 2, 3]
b = [1, 2, 2, 3, 3]
r = mann_whitney_u(a, b)
check(abs((r["U_a"] + r["U_b"]) - len(a) * len(b)) < 1e-9, "U_a+U_b=n_a*n_b")
check(0.0 <= r["p_value"] <= 1.0, "p in [0,1]")

print("\n[6] Real bench: per-event Brier stretch=True vs False (unpaired) on holdout_v2")
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

r = mann_whitney_u(losses_a, losses_b)
print(f"  n_a={r['n_a']} n_b={r['n_b']} U={r['U']:.1f} z={r['z']:.3f} p={r['p_value']:.4f}")
check(r["n_a"] == 40 and r["n_b"] == 40, f"n_a=n_b=40")
check(0.0 <= r["p_value"] <= 1.0, "p in [0,1]")
check(abs((r["U_a"] + r["U_b"]) - r["n_a"] * r["n_b"]) < 1e-9, "U_a+U_b=n_a*n_b")

print(f"\n{ok} ok, {fail} fail")
sys.exit(0 if fail == 0 else 1)
