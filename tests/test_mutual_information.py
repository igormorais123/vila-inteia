"""Tests for engine/mutual_information.py."""
import sys, csv, math
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from engine.mutual_information import mutual_information, normalized_mutual_information
from engine.post_cutoff_classifier import classify_and_predict
from engine._pred_utils import pairs_from_events

ok = fail = 0
def check(cond, msg):
    global ok, fail
    if cond: ok += 1; print(f"  OK  {msg}")
    else: fail += 1; print(f"  FAIL {msg}")


print("=== test_mutual_information ===")

print("\n[1] Empty -> 0")
check(mutual_information([], []) == 0.0, "empty mi")
check(normalized_mutual_information([], []) == 0.0, "empty nmi")

print("\n[2] Independent: constant pred and varying y -> MI ~ 0")
preds = [0.5] * 100
reals = [0, 1] * 50
mi = mutual_information(preds, reals, n_bins=10)
check(mi < 1e-9, f"constant pred -> MI~0 (got {mi})")

print("\n[3] Perfect dependence: pred=0.0 for y=0, pred=1.0 for y=1")
preds = [0.0] * 50 + [1.0] * 50
reals = [0] * 50 + [1] * 50
mi = mutual_information(preds, reals, n_bins=10)
nmi = normalized_mutual_information(preds, reals, n_bins=10)
# H(Y) = ln 2 ~ 0.693 with equal split
check(mi > 0.6, f"perfect dep MI>0.6 (got {mi})")
check(0.99 <= nmi <= 1.0001, f"perfect dep NMI~1 (got {nmi})")

print("\n[4] MI non-negative; NMI in [0,1]")
preds = [0.1, 0.3, 0.5, 0.7, 0.9, 0.2, 0.8, 0.6, 0.4, 0.5]
reals = [0, 0, 1, 1, 1, 0, 1, 0, 1, 0]
mi = mutual_information(preds, reals, n_bins=5)
nmi = normalized_mutual_information(preds, reals, n_bins=5)
check(mi >= 0.0, f"mi>=0 (got {mi})")
check(0.0 <= nmi <= 1.0, f"nmi in [0,1] (got {nmi})")

print("\n[5] More bins generally allows >= MI")
preds = [i / 50 for i in range(50)]
reals = [1 if i % 2 == 0 else 0 for i in range(50)]
mi_5 = mutual_information(preds, reals, n_bins=5)
mi_20 = mutual_information(preds, reals, n_bins=20)
check(mi_5 >= 0.0 and mi_20 >= 0.0, f"both >=0 (mi_5={mi_5}, mi_20={mi_20})")

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

mi = mutual_information(preds, reals, n_bins=10)
nmi = normalized_mutual_information(preds, reals, n_bins=10)
print(f"  n={len(pairs)} MI={mi:.4f} NMI={nmi:.4f}")
check(mi >= 0.0 and math.isfinite(mi), f"mi finite >=0 (got {mi})")
check(0.0 <= nmi <= 1.0, f"nmi in [0,1] (got {nmi})")

print(f"\n{ok} ok, {fail} fail")
sys.exit(0 if fail == 0 else 1)
