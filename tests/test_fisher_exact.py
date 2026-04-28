"""Tests for engine/fisher_exact.py."""

from __future__ import annotations
import sys, csv
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from engine.fisher_exact import fisher_exact
from engine.post_cutoff_classifier import classify_and_predict
from engine._pred_utils import pairs_from_events

ok = fail = 0
def check(cond, msg):
    global ok, fail
    if cond: ok += 1; print(f"  OK  {msg}")
    else: fail += 1; print(f"  FAIL {msg}")


print("=== test_fisher_exact ===")

print("\n[1] Input validation")
r = fisher_exact(-1, 0, 0, 0)
check("erro" in r, "negative cell → erro")

print("\n[2] Empty margin → p=1")
r = fisher_exact(0, 0, 5, 5)  # row1 empty
check(r["p_value_two_sided"] == 1.0, "empty row → p=1")

print("\n[3] Classical 2x2: known p-value (Fisher's tea, 8x8 table)")
# Lady tasting tea: a=3, b=1, c=1, d=3 → p ≈ 0.486
r = fisher_exact(3, 1, 1, 3)
print(f"  3,1,1,3 → odds={r['odds_ratio']:.3f} p={r['p_value_two_sided']:.4f}")
check(abs(r["p_value_two_sided"] - 0.4857) < 0.01, f"p≈0.486 (got {r['p_value_two_sided']:.4f})")
check(abs(r["odds_ratio"] - 9.0) < 1e-9, f"odds=9 (got {r['odds_ratio']})")

print("\n[4] Strong association → small p")
# All success in row1, all failure in row2
r = fisher_exact(10, 0, 0, 10)
print(f"  10,0,0,10 → p={r['p_value_two_sided']:.6f}")
check(r["p_value_two_sided"] < 0.001, f"p<0.001 (got {r['p_value_two_sided']:.6f})")
check(r["reject_h0"], "reject H0")

print("\n[5] No association → large p")
# Equal proportions
r = fisher_exact(5, 5, 5, 5)
print(f"  5,5,5,5 → odds={r['odds_ratio']:.3f} p={r['p_value_two_sided']:.4f}")
check(abs(r["odds_ratio"] - 1.0) < 1e-9, "odds=1.0")
check(r["p_value_two_sided"] > 0.5, f"p>0.5 (got {r['p_value_two_sided']:.4f})")

print("\n[6] Real bench: 2x2 of correct/wrong stretch=True vs False on holdout_v2")
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

# 2x2 contingency: rows=stretch correct/wrong; cols=no-stretch correct/wrong
a = b = c = d = 0
for pa, pb, y in zip(preds_a, preds_b, reals):
    sa = (pa >= 0.5) == bool(y)
    sb = (pb >= 0.5) == bool(y)
    if sa and sb: a += 1
    elif sa and not sb: b += 1
    elif not sa and sb: c += 1
    else: d += 1

r = fisher_exact(a, b, c, d)
print(f"  a={a} b={b} c={c} d={d} odds={r['odds_ratio']:.3f} p={r['p_value_two_sided']:.4f}")
check(a + b + c + d == 40, f"n=40 (got {a+b+c+d})")
check(0.0 <= r["p_value_two_sided"] <= 1.0, "p in [0,1]")

print(f"\n{ok} ok, {fail} fail")
sys.exit(0 if fail == 0 else 1)
