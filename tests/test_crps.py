"""Tests for engine/crps.py."""
import sys, csv
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from engine.crps import crps_binary, crps_decomposition

ok = fail = 0
def check(cond, msg):
    global ok, fail
    if cond: ok += 1; print(f"  OK  {msg}")
    else: fail += 1; print(f"  FAIL {msg}")


print("=== test_crps ===")

print("\n[1] Empty input -> 0.0")
check(crps_binary([], []) == 0.0, "empty -> 0")

print("\n[2] Perfect forecasts (p=y) -> CRPS = 0")
crps = crps_binary([0.0, 1.0, 0.0, 1.0], [0, 1, 0, 1])
check(abs(crps) < 1e-12, f"perfect -> 0 (got {crps})")

print("\n[3] Worst forecasts (p=1-y) -> CRPS = 1")
crps = crps_binary([1.0, 0.0, 1.0, 0.0], [0, 1, 0, 1])
check(abs(crps - 1.0) < 1e-12, f"worst -> 1 (got {crps})")

print("\n[4] CRPS == Brier for binary case")
preds = [0.1, 0.9, 0.4, 0.7, 0.5]
reals = [0, 1, 0, 1, 1]
brier = sum((p - y) ** 2 for p, y in zip(preds, reals)) / len(preds)
crps = crps_binary(preds, reals)
check(abs(crps - brier) < 1e-12, f"CRPS=Brier (crps={crps}, brier={brier})")

print("\n[5] Decomposition: Brier ≈ REL - RES + UNC")
preds = [0.1, 0.3, 0.5, 0.7, 0.9, 0.2, 0.4, 0.6, 0.8, 0.95]
reals = [0, 0, 1, 1, 1, 0, 0, 1, 1, 1]
d = crps_decomposition(preds, reals, n_bins=5)
check(abs(d["decomp_gap"]) < 0.05, f"decomp_gap small (got {d['decomp_gap']})")
check(d["uncertainty"] > 0, f"unc > 0 (got {d['uncertainty']})")

print("\n[6] Length mismatch raises")
try:
    crps_binary([0.1, 0.2], [1])
    check(False, "should raise on mismatch")
except ValueError:
    check(True, "raises ValueError on length mismatch")

print("\n[7] Real classifier on holdout + multiple CSVs")
sys.path.insert(0, "/home/pedroafonso/vila-inteia")
from engine.post_cutoff_classifier import classify_and_predict


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


events = []
for fn in ["post_cutoff_q2_2026_holdout", "post_cutoff_q1_2026",
           "brazil_votes_q1_2026"]:
    events += load_csv(f"/home/pedroafonso/vila-inteia/data/backtest/{fn}.csv")

preds = []
reals = []
for e in events:
    p, _ = classify_and_predict(e["outcome_framing"], e["contexto"])
    preds.append(p)
    reals.append(e["outcome_real"])

crps = crps_binary(preds, reals)
print(f"  N={len(preds)} CRPS={crps:.4f}")
check(0.0 <= crps <= 1.0, f"CRPS in [0,1] (got {crps})")
check(crps < 0.30, f"CRPS < 0.30 on real classifier (got {crps})")

print(f"\n{ok} ok, {fail} fail")
sys.exit(0 if fail == 0 else 1)
