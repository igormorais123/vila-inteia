"""Tests for engine/reliability_diagram.py — reliability_diagram with Wilson CI."""

from __future__ import annotations
import sys, csv
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from engine.reliability_diagram import reliability_diagram
from engine.post_cutoff_classifier import classify_and_predict
from engine._pred_utils import pairs_from_events

ok = fail = 0
def check(cond, msg):
    global ok, fail
    if cond: ok += 1; print(f"  OK  {msg}")
    else: fail += 1; print(f"  FAIL {msg}")


print("=== test_reliability_diagram ===")

print("\n[1] Edge cases")
check(reliability_diagram([], [], n_bins=10) == [], "empty → []")
check(reliability_diagram([0.5], [0, 1], n_bins=10) == [], "size mismatch → []")
check(reliability_diagram([0.5], [1], n_bins=0) == [], "n_bins=0 → []")

print("\n[2] Perfect calibration: all p=0.5, half outcomes positive")
preds = [0.55] * 10
reals = [1, 0, 1, 0, 1, 0, 1, 0, 1, 0]
out = reliability_diagram(preds, reals, n_bins=10)
print(f"  {len(out)} bin(s); first: {out[0] if out else None}")
check(len(out) == 1, "single bin populated")
b = out[0]
check(abs(b["mean_p"] - 0.55) < 1e-9, f"mean_p=0.55 (got {b['mean_p']})")
check(abs(b["observed_rate"] - 0.5) < 1e-9, f"observed=0.5 (got {b['observed_rate']})")
check(b["n"] == 10, f"n=10")
check(0.0 <= b["ci_lo"] <= b["observed_rate"] <= b["ci_hi"] <= 1.0, "CI brackets observed")

print("\n[3] CI shrinks with n")
preds_small = [0.3, 0.31, 0.32]
reals_small = [1, 0, 0]
out_small = reliability_diagram(preds_small, reals_small, n_bins=10)
preds_big = [0.3 + 0.001 * i for i in range(100)]
reals_big = [1 if i % 3 == 0 else 0 for i in range(100)]
out_big = reliability_diagram(preds_big, reals_big, n_bins=10)
w_small = out_small[0]["ci_hi"] - out_small[0]["ci_lo"]
# big has many bins; pick one with most n
best_big = max(out_big, key=lambda b: b["n"])
w_big = best_big["ci_hi"] - best_big["ci_lo"]
print(f"  CI width: small_n={out_small[0]['n']} → {w_small:.3f} ; big_n={best_big['n']} → {w_big:.3f}")
check(w_big < w_small, f"CI narrows with n ({w_big:.3f} < {w_small:.3f})")

print("\n[4] Multiple bins populated with diverse predictions")
preds_div = [0.05, 0.15, 0.25, 0.35, 0.45, 0.55, 0.65, 0.75, 0.85, 0.95]
reals_div = [0, 0, 0, 0, 1, 0, 1, 1, 1, 1]
out = reliability_diagram(preds_div, reals_div, n_bins=10)
print(f"  bins populated: {len(out)}")
check(len(out) == 10, f"10 distinct bins (got {len(out)})")
for b in out:
    check(b["bin_lo"] <= b["mean_p"] <= b["bin_hi"], f"bin {b['bin']} mean_p in range")
    check(0.0 <= b["ci_lo"] <= b["ci_hi"] <= 1.0, f"bin {b['bin']} CI valid")

print("\n[5] Boundary p=1.0 lands in last bin")
out = reliability_diagram([1.0, 0.99], [1, 1], n_bins=10)
check(len(out) >= 1, "p=1.0 placed somewhere")
last = [b for b in out if b["bin"] == 9]
check(len(last) == 1, "p=1.0 lands in last bin")


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

out = reliability_diagram(preds_real, reals_real, n_bins=10)
total = sum(b["n"] for b in out)
print(f"  n_total={total}; populated bins={len(out)}")
for b in out:
    print(f"    bin {b['bin']} [{b['bin_lo']:.1f},{b['bin_hi']:.1f}): "
          f"n={b['n']} mean_p={b['mean_p']:.3f} obs={b['observed_rate']:.3f} "
          f"CI=[{b['ci_lo']:.3f},{b['ci_hi']:.3f}]")
check(total == len(reals_real) and total >= 40, f"sum n={total} matches and >=40")
check(all(b["ci_lo"] <= b["observed_rate"] <= b["ci_hi"] for b in out),
      "all bins: CI brackets observed_rate")

print(f"\n{ok} ok, {fail} fail")
sys.exit(0 if fail == 0 else 1)
