"""Tests for engine/aitkin_p.py (Fisher 1932 combined p-value)."""
import sys, math, csv
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from engine.aitkin_p import aitkin_p, _chi2_sf

ok = fail = 0
def check(cond, msg):
    global ok, fail
    if cond: ok += 1; print(f"  OK  {msg}")
    else: fail += 1; print(f"  FAIL {msg}")


print("=== test_aitkin_p ===")

print("\n[1] Empty -> p_combined=1.0, k=0")
r = aitkin_p([])
check(r["k"] == 0 and r["p_combined"] == 1.0, f"empty (got {r})")

print("\n[2] Single p-value: chi² = -2*ln(p), df=2")
r = aitkin_p([0.5])
expected_chi2 = -2 * math.log(0.5)
check(abs(r["chi_square"] - expected_chi2) < 1e-9,
      f"chi2 = -2 ln(p) (got {r['chi_square']}, expected {expected_chi2})")
check(r["df"] == 2, f"df=2 (got {r['df']})")

print("\n[3] All p=1.0 -> chi²=0 -> p_combined=1.0")
r = aitkin_p([1.0, 1.0, 1.0])
check(r["chi_square"] == 0.0, f"chi²=0 (got {r['chi_square']})")
check(abs(r["p_combined"] - 1.0) < 1e-3, f"p=1 (got {r['p_combined']})")

print("\n[4] All very small p -> combined p very small")
r = aitkin_p([0.001, 0.001, 0.001, 0.001])
check(r["p_combined"] < 1e-6, f"combined small (got {r['p_combined']})")
check(r["df"] == 8, f"df=8 (got {r['df']})")

print("\n[5] Independent Uniform(0,1) p-values: combined ≈ uniform")
# Sanity: for k uniform p, mean of combined p approx 0.5
import random
rng = random.Random(7)
combined_ps = []
for _ in range(200):
    ps = [rng.random() for _ in range(5)]
    combined_ps.append(aitkin_p(ps)["p_combined"])
mean_p = sum(combined_ps) / len(combined_ps)
check(0.4 < mean_p < 0.6, f"uniform p-values give mean ≈ 0.5 (got {mean_p:.3f})")

print("\n[6] Clip min: p=0 floored, no -inf chi²")
r = aitkin_p([0.0, 0.5])
check(math.isfinite(r["chi_square"]), f"chi² finite with p=0 (got {r['chi_square']})")

print("\n[7] _chi2_sf sanity: P(X > 0) ≈ 1, P(X > df) ≈ 0.5-ish")
sf0 = _chi2_sf(0.0, 4)
sf_inf = _chi2_sf(1e6, 4)
check(sf0 == 1.0, f"sf(0)=1 (got {sf0})")
check(sf_inf < 1e-6, f"sf(1e6) ≈ 0 (got {sf_inf})")

print("\n[8] Real classifier: per-event p-values combined")
# Use Brier score per event as a "surprise" -> derive p via mid-point heuristic.
# Honest test: check combination machinery against real classifier outputs
# treated as predicted probabilities -> map (1-p) when y=1, p when y=0 as
# approximate one-sided "surprise p" for sanity, then combine.
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

# "p-value" of being wrong: if y=1 use (1 - p_hat), if y=0 use p_hat.
# Higher = more surprised. For a calibrated classifier, these should NOT all
# be tiny; they should look like ~Uniform(0, 1) in expectation.
surprise_ps = []
for e in events:
    p, _ = classify_and_predict(e["outcome_framing"], e["contexto"])
    sp = 1 - p if e["outcome_real"] == 1 else p
    surprise_ps.append(max(sp, 1e-6))

r = aitkin_p(surprise_ps)
print(f"  N={len(surprise_ps)} k={r['k']} chi²={r['chi_square']:.2f} df={r['df']} p_combined={r['p_combined']:.4g}")
check(r["k"] == len(events), f"k=N (got {r['k']})")
check(r["df"] == 2 * len(events), f"df=2k (got {r['df']})")
check(0.0 <= r["p_combined"] <= 1.0, f"p in [0,1] (got {r['p_combined']})")

print(f"\n{ok} ok, {fail} fail")
sys.exit(0 if fail == 0 else 1)
