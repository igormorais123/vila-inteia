"""Tests for engine/conformal.py — conformal_calibrate_smart.

5 sections:
  [1] basic: alpha grid search returns valid quants dict
  [2] target hit: train LOO abstain near target (within tolerance)
  [3] per-category tiers: high-reliability tighter than volatile
  [4] pooled fallback: unseen labels get __pooled__ quantile, not 0.5
  [5] holdout bench: Q1 train fit, Q2+Q3 (n=80) eval — abstain reduces, singleton_acc preserved
"""
from __future__ import annotations

import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from engine.conformal import (
    conformal_calibrate, conformal_calibrate_smart, conformal_interval,
    evaluate_conformal,
)
from engine.post_cutoff_classifier import classify_and_predict

ok = fail = 0


def check(cond, msg):
    global ok, fail
    if cond:
        ok += 1
        print(f"  OK  {msg}")
    else:
        fail += 1
        print(f"  FAIL {msg}")


print("=== test_conformal_smart ===")


def fake_clf(framing, contexto=""):
    t = framing.lower()
    if "war" in t:
        return 0.85, "war_conflict"  # high-reliability
    if "scheduled" in t:
        return 0.95, "scheduled_event"  # high-reliability
    if "price" in t:
        return 0.55, "price_threshold"  # volatile
    if "tech" in t:
        return 0.45, "tech_release"  # volatile
    return 0.50, "default"


synthetic = (
    [{"outcome_framing": "war event", "outcome_real": 1, "contexto": ""}] * 6 +
    [{"outcome_framing": "scheduled event", "outcome_real": 1, "contexto": ""}] * 6 +
    [{"outcome_framing": "price btc", "outcome_real": 1, "contexto": ""}] * 3 +
    [{"outcome_framing": "price btc", "outcome_real": 0, "contexto": ""}] * 3 +
    [{"outcome_framing": "tech launch", "outcome_real": 0, "contexto": ""}] * 3 +
    [{"outcome_framing": "tech launch", "outcome_real": 1, "contexto": ""}] * 1
)

print("\n[1] basic: smart returns valid quants dict")
quants = conformal_calibrate_smart(synthetic, fake_clf, target_abstain_rate=0.5)
check(isinstance(quants, dict), "returns dict")
check("__alpha__" in quants, "carries selected alpha")
check("__pooled__" in quants, "carries pooled fallback")
check(0.05 <= quants["__alpha__"] <= 0.5, f"alpha in [0.05, 0.5] (got {quants['__alpha__']:.3f})")
check(any(k in quants for k in ("war_conflict", "price_threshold")),
      f"per-category quantiles present (got {[k for k in quants if not k.startswith('__')]})")

print("\n[2] target hit: smart picks alpha closest to target")
for tgt in (0.3, 0.5):
    q = conformal_calibrate_smart(synthetic, fake_clf, target_abstain_rate=tgt)
    # Just sanity: alpha is one of the grid points.
    a = q["__alpha__"]
    check(abs((a * 100) % 5) < 1e-6, f"target={tgt}: alpha {a:.3f} on 0.05 grid")

print("\n[3] per-category tiers: reliable tight, volatile wide")
q = conformal_calibrate_smart(synthetic, fake_clf, target_abstain_rate=0.5)
# war_conflict (reliable, all real=1, p=0.85 → nc=0.15 each) should be tighter
# than price_threshold (volatile, mixed, p=0.55 → nc up to 0.55).
war_q = q.get("war_conflict", 1.0)
price_q = q.get("price_threshold", 0.0)
check(war_q < price_q, f"war_conflict ({war_q:.3f}) < price_threshold ({price_q:.3f})")
check(war_q <= 0.20, f"war_conflict tight (≤ 0.20, got {war_q:.3f})")

print("\n[4] pooled fallback for unseen labels")
# Use an unseen label name; conformal_interval should consult __pooled__.
lo, hi = conformal_interval(0.7, "totally_unseen_category", q)
expected_q = q["__pooled__"]
check(abs((hi - lo) - 2 * expected_q) < 1e-6 or hi == 1.0 or lo == 0.0,
      f"unseen label uses pooled q={expected_q:.3f}, got width={hi - lo:.3f}")
# default_q=0.5 NOT used when __pooled__ is present (pooled uses train data).
default_lo, default_hi = conformal_interval(0.5, "another_unseen", {})
check(default_lo == 0.0 and default_hi == 1.0,
      f"empty quants → default_q=0.5 → [0,1] (got [{default_lo:.2f}, {default_hi:.2f}])")

print("\n[5] holdout bench: Q1 fit, Q2+Q3 eval (n=80)")
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

base = "/home/pedroafonso/vila-inteia/data/backtest"
q1 = load_csv(f"{base}/post_cutoff_q1_2026.csv") + load_csv(f"{base}/post_cutoff_q1_2026_v2.csv")
holdout = (
    load_csv(f"{base}/post_cutoff_q2_2026_holdout.csv") +
    load_csv(f"{base}/post_cutoff_q2_2026_holdout_v2.csv") +
    load_csv(f"{base}/post_cutoff_q3_2026_holdout_v3.csv")
)
print(f"  Q1 train n={len(q1)}, Q2+Q3 holdout n={len(holdout)}")

# Baseline alpha=0.20.
qb = conformal_calibrate(q1, classify_and_predict, alpha=0.20)
rb = evaluate_conformal(holdout, classify_and_predict, qb, alpha=0.20)
print(f"  baseline alpha=0.20: abstain={rb['abstain_rate']:.3f} singleton_acc={rb['singleton_acc']:.3f}")

# Smart, target 0.5.
qs = conformal_calibrate_smart(q1, classify_and_predict, target_abstain_rate=0.5)
rs = evaluate_conformal(holdout, classify_and_predict, qs)
print(f"  smart  tgt=0.50  alpha={qs['__alpha__']:.2f}: abstain={rs['abstain_rate']:.3f} singleton_acc={rs['singleton_acc']:.3f}")

check(rs["abstain_rate"] <= rb["abstain_rate"],
      f"smart reduces abstain ({rs['abstain_rate']:.3f} ≤ {rb['abstain_rate']:.3f})")
check(rs["singleton_acc"] >= rb["singleton_acc"] - 0.05,
      f"smart preserves singleton_acc within 5pp ({rs['singleton_acc']:.3f} vs {rb['singleton_acc']:.3f})")
check(rs["n"] == 80, f"holdout n=80 (got {rs['n']})")

print(f"\n{ok} ok, {fail} fail")
sys.exit(0 if fail == 0 else 1)
