"""Onda 255: testa engine/calibration.py."""
import sys, csv
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from engine.calibration import (
    fit_platt, platt_predict,
    fit_isotonic, isotonic_predict,
    evaluate_calibration,
)

ok = fail = 0
def check(cond, msg):
    global ok, fail
    if cond: ok += 1; print(f"  OK  {msg}")
    else: fail += 1; print(f"  FAIL {msg}")


print("=== test_calibration ===")

print("\n[1] fit_platt — overconfident classifier")
def overconfident(framing, contexto=""):
    if "yes" in framing.lower():
        return 0.95, "yes"
    return 0.05, "no"

# Reality: only 70% of yes are true; 30% of no are true (overconfidence)
events = (
    [{"outcome_framing": "yes case", "outcome_real": 1, "contexto": ""}] * 7 +
    [{"outcome_framing": "yes case", "outcome_real": 0, "contexto": ""}] * 3 +
    [{"outcome_framing": "no case", "outcome_real": 1, "contexto": ""}] * 3 +
    [{"outcome_framing": "no case", "outcome_real": 0, "contexto": ""}] * 7
)
A, B = fit_platt(events, overconfident, max_iter=500, lr=0.1)
p_yes = platt_predict(0.95, A, B)
p_no = platt_predict(0.05, A, B)
print(f"  A={A:.3f} B={B:.3f}")
print(f"  raw 0.95 → calibrated {p_yes:.3f}")
print(f"  raw 0.05 → calibrated {p_no:.3f}")
check(p_yes < 0.95, f"yes shrunk ({p_yes:.2f})")
check(p_no > 0.05, f"no relaxed ({p_no:.2f})")

print("\n[2] fit_isotonic — non-monotonic ground truth")
def varied(framing, contexto=""):
    if "high" in framing: return 0.9, "high"
    if "mid" in framing: return 0.6, "mid"
    if "low" in framing: return 0.3, "low"
    return 0.5, "default"

events = (
    [{"outcome_framing": "high A", "outcome_real": 1, "contexto": ""}] * 4 +
    [{"outcome_framing": "high B", "outcome_real": 0, "contexto": ""}] * 1 +
    [{"outcome_framing": "mid A", "outcome_real": 1, "contexto": ""}] * 3 +
    [{"outcome_framing": "mid B", "outcome_real": 0, "contexto": ""}] * 2 +
    [{"outcome_framing": "low A", "outcome_real": 1, "contexto": ""}] * 1 +
    [{"outcome_framing": "low B", "outcome_real": 0, "contexto": ""}] * 4
)
knots = fit_isotonic(events, varied)
print(f"  knots: {knots}")
check(len(knots) >= 2, f"≥ 2 knots (got {len(knots)})")
# Monotonic non-decreasing
vals = [v for _, v in knots]
check(all(vals[i] <= vals[i+1] for i in range(len(vals)-1)), "monotonic")

p_low = isotonic_predict(0.3, knots)
p_high = isotonic_predict(0.9, knots)
check(p_low <= p_high, f"order preserved ({p_low:.2f} ≤ {p_high:.2f})")

print("\n[3] evaluate_calibration end-to-end")
from engine.post_cutoff_classifier import classify_and_predict

def load_csv(fp):
    out = []
    with open(fp, encoding="utf-8") as f:
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

cal_files = [
    "post_cutoff_q1_2026.csv", "post_cutoff_q1_2026_v2.csv",
    "brazil_votes_q1_2026.csv", "sports_specific_q1_2026.csv",
    "tech_releases_q1_2026.csv", "elections_2026_q1.csv",
    "space_science_q1_2026.csv", "price_predictions_q1_2026.csv",
]
cal = []
for f in cal_files:
    cal += load_csv(ROOT / "data" / "backtest" / f)
test = load_csv(ROOT / "data" / "backtest" / "post_cutoff_q2_2026_holdout.csv")

# Baseline
res_base = evaluate_calibration(test, classify_and_predict, method="raw", params=None)

# Platt
A, B = fit_platt(cal, classify_and_predict, max_iter=500, lr=0.05)
res_platt = evaluate_calibration(test, classify_and_predict, method="platt", params=(A, B))

# Isotonic
knots = fit_isotonic(cal, classify_and_predict)
res_iso = evaluate_calibration(test, classify_and_predict, method="isotonic", params=knots)

print(f"  Baseline: acc={res_base['acc']:.1%} brier={res_base['brier']:.4f}")
print(f"  Platt:    acc={res_platt['acc']:.1%} brier={res_platt['brier']:.4f} (A={A:.2f} B={B:.2f})")
print(f"  Isotonic: acc={res_iso['acc']:.1%} brier={res_iso['brier']:.4f} ({len(knots)} knots)")
check(res_platt["n"] == 10, "platt n=10")
check(res_iso["n"] == 10, "iso n=10")

print(f"\n{ok} ok, {fail} fail")
sys.exit(0 if fail == 0 else 1)
