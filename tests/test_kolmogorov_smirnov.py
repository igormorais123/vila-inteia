"""Tests for engine/kolmogorov_smirnov.py."""
import sys, csv, random
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from engine.kolmogorov_smirnov import ks_test, ks_pit_test

ok = fail = 0
def check(cond, msg):
    global ok, fail
    if cond: ok += 1; print(f"  OK  {msg}")
    else: fail += 1; print(f"  FAIL {msg}")


print("=== test_kolmogorov_smirnov ===")

print("\n[1] Empty -> ks=None")
r = ks_test([])
check(r["ks"] is None, "empty ks=None")

print("\n[2] Uniform sample -> small KS, p > 0.05")
random.seed(42)
samples = [random.random() for _ in range(500)]
r = ks_test(samples, reference="uniform")
check(r["ks"] < 0.1, f"KS small for uniform (got {r['ks']:.3f})")
check(r["p_value"] > 0.05, f"do not reject (p={r['p_value']:.3f})")

print("\n[3] Heavily-skewed sample -> large KS, p < 0.05")
samples = [random.random() ** 4 for _ in range(500)]  # skewed toward 0
r = ks_test(samples, reference="uniform")
check(r["ks"] > 0.2, f"KS large (got {r['ks']:.3f})")
check(r["reject_h0"], f"reject_h0 (p={r['p_value']:.4f})")

print("\n[4] PIT under perfect calibration -> ~uniform, do not reject")
# y_i ~ Bernoulli(p_i) with p_i fixed; PIT u_i = p if y=1 else 1-p.
# For p=0.5 uniform y, PITs all 0.5 -> not uniform but degenerate.
# Use varied p with matching realizations.
random.seed(7)
preds, reals = [], []
for _ in range(300):
    p = random.uniform(0.1, 0.9)
    preds.append(p)
    reals.append(1 if random.random() < p else 0)
r = ks_pit_test(preds, reals)
print(f"  PIT KS={r['ks']:.3f} p={r['p_value']:.3f} mean={r['pit_mean']:.3f}")
check(r["ks"] is not None, "PIT ks finite")

print("\n[5] PIT under severe miscalibration -> reject")
# Predict 0.5 but realizations always 1 -> all PITs = 0.5 (degenerate spike)
preds = [0.9] * 100
reals = [0] * 100  # always wrong; PITs = 1-0.9 = 0.1 each (degenerate)
r = ks_pit_test(preds, reals)
print(f"  miscal KS={r['ks']:.3f} p={r['p_value']:.4f}")
check(r["ks"] > 0.3, f"KS large for spike (got {r['ks']:.3f})")
check(r["reject_h0"], f"reject_h0 miscalibrated (p={r['p_value']})")

print("\n[6] Custom callable reference (linear cdf shift)")
samples = [0.6, 0.7, 0.8, 0.9, 0.95]
def cdf_shifted(x):
    return max(0.0, min(1.0, (x - 0.5) / 0.5))
r = ks_test(samples, reference=cdf_shifted)
check(r["ks"] is not None, f"callable ref ok (ks={r['ks']:.3f})")

print("\n[7] Real classifier on holdout v2 (n=40)")
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


events = load_csv("/home/pedroafonso/vila-inteia/data/backtest/post_cutoff_q2_2026_holdout_v2.csv")
preds = []
reals = []
for e in events:
    p, _ = classify_and_predict(e["outcome_framing"], e["contexto"])
    preds.append(p)
    reals.append(e["outcome_real"])

r = ks_pit_test(preds, reals)
print(f"  N={r['n']} PIT KS={r['ks']:.3f} p={r['p_value']:.4f} mean={r['pit_mean']:.3f}")
check(r["ks"] is not None, "PIT ks finite")
check(r["n"] == 40, f"n=40 (got {r['n']})")

print(f"\n{ok} ok, {fail} fail")
sys.exit(0 if fail == 0 else 1)
