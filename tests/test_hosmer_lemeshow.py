"""Onda 261: testa engine/hosmer_lemeshow.py."""
import sys, csv
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from engine.hosmer_lemeshow import hosmer_lemeshow

ok = fail = 0
def check(cond, msg):
    global ok, fail
    if cond: ok += 1; print(f"  OK  {msg}")
    else: fail += 1; print(f"  FAIL {msg}")


print("=== test_hosmer_lemeshow ===")

print("\n[1] Well-calibrated synthetic — chi² close to df")
import random
rng = random.Random(42)
def perfect(framing, contexto=""):
    return float(framing.split("|")[0]), "synth"

events = []
for _ in range(1000):
    p_true = rng.uniform(0.1, 0.9)
    y = 1 if rng.random() < p_true else 0
    events.append({"outcome_framing": f"{p_true}|", "outcome_real": y})

res = hosmer_lemeshow(events, perfect, n_groups=10)
print(f"  n={res['n']} chi²={res['chi_square']} df={res['df']} p={res['p_value_approx']}")
check(res["n"] == 1000, "n=1000")
# E[chi²] ≈ df under H0; allow up to 3*df for finite-sample variance
check(res["chi_square"] < 3 * res["df"],
      f"chi² ({res['chi_square']}) < 3*df ({3*res['df']})")

print("\n[2] Mis-calibrated synthetic — large chi²")
def overconfident(framing, contexto=""):
    return float(framing.split("|")[0]), "synth"

# Predictions all 0.9, but only 30% are actually 1
events_bad = []
for _ in range(100):
    y = 1 if rng.random() < 0.3 else 0
    events_bad.append({"outcome_framing": "0.9|", "outcome_real": y})

res_bad = hosmer_lemeshow(events_bad, overconfident, n_groups=5)
print(f"  chi²={res_bad['chi_square']} reject={res_bad['reject_h0']}")
check(res_bad["chi_square"] > 5, f"chi² large ({res_bad['chi_square']})")
check(res_bad["reject_h0"], f"reject H0 (got {res_bad['reject_h0']})")

print("\n[3] Empty handled")
res = hosmer_lemeshow([], perfect)
check(res["n"] == 0, "empty n=0")
check(not res["reject_h0"], "no reject empty")

print("\n[4] Real classifier on holdout + train")
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

all_events = []
for fn in ["post_cutoff_q1_2026", "post_cutoff_q1_2026_v2",
           "post_cutoff_q2_2026_holdout", "brazil_votes_q1_2026",
           "sports_specific_q1_2026", "tech_releases_q1_2026",
           "elections_2026_q1", "space_science_q1_2026",
           "price_predictions_q1_2026"]:
    all_events += load_csv(f"/home/pedroafonso/vila-inteia/data/backtest/{fn}.csv")

res = hosmer_lemeshow(all_events, classify_and_predict, n_groups=10)
print(f"  Real classifier on {res['n']} events:")
print(f"  chi²={res['chi_square']} df={res['df']} p≈{res['p_value_approx']}")
print(f"  reject_h0={res['reject_h0']}")
print("  Per-group:")
for g in res["groups"]:
    print(f"    g={g['g']} n={g['n']:>2} mean_p={g['mean_p']:.2f} obs_rate={g['obs_rate']:.2f} comp={g['component']:.2f}")
check(res["n"] == 110, "110 events")
check(res["df"] >= 1, f"df ≥ 1 (got {res['df']})")

print(f"\n{ok} ok, {fail} fail")
sys.exit(0 if fail == 0 else 1)
