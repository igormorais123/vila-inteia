"""Onda 253: testa engine/conformal.py."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from engine.conformal import (
    conformal_calibrate, conformal_interval, conformal_set, evaluate_conformal,
)

ok = fail = 0
def check(cond, msg):
    global ok, fail
    if cond: ok += 1; print(f"  OK  {msg}")
    else: fail += 1; print(f"  FAIL {msg}")


print("=== test_conformal ===")

print("\n[1] conformal_calibrate")
def fake_clf(framing, contexto=""):
    if "war" in framing.lower():
        return 0.8, "war"
    if "price" in framing.lower():
        return 0.5, "price"
    return 0.5, "default"

# war: 5 cal events all real=1, p=0.8 → nc=0.2 each
# price: 4 cal events 50/50, p=0.5 → nc=0.5 each
events = (
    [{"outcome_framing": "war event", "outcome_real": 1, "contexto": ""}] * 5 +
    [{"outcome_framing": "price btc", "outcome_real": 1, "contexto": ""}] * 2 +
    [{"outcome_framing": "price btc", "outcome_real": 0, "contexto": ""}] * 2
)
quants = conformal_calibrate(events, fake_clf, alpha=0.1)
check("war" in quants, f"war calibrated (got {list(quants.keys())})")
check("price" in quants, "price calibrated")
check(quants["war"] <= 0.21, f"war q low ({quants['war']:.2f})")
check(quants["price"] >= 0.4, f"price q high ({quants['price']:.2f})")

print("\n[2] conformal_interval")
lo, hi = conformal_interval(0.8, "war", quants)
check(0.5 < lo and hi <= 1.0, f"war interval [{lo:.2f}, {hi:.2f}] tight + bounded")

lo, hi = conformal_interval(0.5, "price", quants)
check(lo == 0 and hi == 1.0, f"price interval [{lo:.2f}, {hi:.2f}] wide")

# Unknown label
lo, hi = conformal_interval(0.7, "unknown", quants, default_q=0.3)
check(abs(lo - 0.4) < 1e-9 and hi == 1.0, f"unknown default ({lo:.2f}, {hi:.2f})")

print("\n[3] conformal_set")
# War with p=0.8, q=0.2 → [0.6, 1.0] → only {1}
s = conformal_set(0.8, "war", quants)
check(s == {1}, f"war confident YES (got {s})")

# Price with p=0.5, q=0.5 → [0,1] → {0,1} abstain
s = conformal_set(0.5, "price", quants)
check(s == {0, 1}, f"price abstain (got {s})")

# Synthetic: p=0.1, q=0.05 → [0.05, 0.15] → only {0}
qs = {"x": 0.05}
s = conformal_set(0.1, "x", qs)
check(s == {0}, f"low p confident NO (got {s})")

print("\n[4] evaluate_conformal")
# Calibrate then evaluate on different test set
test_events = [
    {"outcome_framing": "war event", "outcome_real": 1, "contexto": ""},
    {"outcome_framing": "price btc", "outcome_real": 0, "contexto": ""},
    {"outcome_framing": "price btc", "outcome_real": 1, "contexto": ""},
]
res = evaluate_conformal(test_events, fake_clf, quants, alpha=0.1)
check(res["n"] == 3, f"n=3 (got {res['n']})")
check(res["coverage"] >= 0.9, f"coverage ≥ 0.9 (got {res['coverage']:.2f})")
check(res["singletons"] >= 1, f"war is singleton (got {res['singletons']})")
check(res["abstain_rate"] >= 0.5, f"prices abstain (got {res['abstain_rate']:.2f})")

print("\n[5] coverage guarantee — empirical with classifier")
sys.path.insert(0, "/home/pedroafonso/vila-inteia")
from engine.post_cutoff_classifier import classify_and_predict

# Calibrate on q1, test on holdout q2
import csv
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

cal = load_csv("/home/pedroafonso/vila-inteia/data/backtest/post_cutoff_q1_2026.csv")
cal += load_csv("/home/pedroafonso/vila-inteia/data/backtest/post_cutoff_q1_2026_v2.csv")
test = load_csv("/home/pedroafonso/vila-inteia/data/backtest/post_cutoff_q2_2026_holdout.csv")

q = conformal_calibrate(cal, classify_and_predict, alpha=0.2)
res = evaluate_conformal(test, classify_and_predict, q, alpha=0.2)
print(f"  cal n={len(cal)} test n={res['n']}")
print(f"  coverage={res['coverage']:.2f} target={res['target_coverage']:.2f}")
print(f"  singletons={res['singletons']} singleton_acc={res['singleton_acc']:.2f}")
print(f"  abstain_rate={res['abstain_rate']:.2f}")
# Coverage não garantida em finite-sample mas próxima
check(res["coverage"] >= 0.6, f"coverage reasonable ({res['coverage']:.2f})")

print(f"\n{ok} ok, {fail} fail")
sys.exit(0 if fail == 0 else 1)
