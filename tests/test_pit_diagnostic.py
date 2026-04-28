"""Onda 257: testa engine/pit_diagnostic.py."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from engine.pit_diagnostic import randomized_pit, pit_histogram

ok = fail = 0
def check(cond, msg):
    global ok, fail
    if cond: ok += 1; print(f"  OK  {msg}")
    else: fail += 1; print(f"  FAIL {msg}")


print("=== test_pit_diagnostic ===")

print("\n[1] randomized_pit ranges")
# y=1, p=0.8 → u in [0.2, 1.0]
u = randomized_pit(0.8, 1, 0.5)
check(0.2 <= u <= 1.0, f"y=1 p=0.8 u={u:.3f} in [0.2,1]")
# y=0, p=0.8 → u in [0, 0.2]
u = randomized_pit(0.8, 0, 0.5)
check(0 <= u <= 0.2, f"y=0 p=0.8 u={u:.3f} in [0,0.2]")
# y=1, p=0.5, rng=0 → u=0.5
u = randomized_pit(0.5, 1, 0.0)
check(abs(u - 0.5) < 1e-9, f"y=1 p=0.5 rng=0 u={u}")

print("\n[2] pit_histogram — well-calibrated synthetic")
import random
rng = random.Random(0)
def perfect(framing, contexto=""):
    return float(framing.split("|")[0]), "synth"

events = []
for _ in range(200):
    p_true = rng.random()
    y = 1 if rng.random() < p_true else 0
    events.append({"outcome_framing": f"{p_true}|", "outcome_real": y})

res = pit_histogram(events, perfect, n_bins=10, seed=1)
print(f"  n={res['n']} chi²={res['chi_square']:.2f} diag={res['diagnosis']}")
check(res["n"] == 200, "n=200")
check(res["diagnosis"] == "well-calibrated", f"calibrated (got {res['diagnosis']})")

print("\n[3] pit_histogram — overconfident classifier")
def overconfident(framing, contexto=""):
    return 0.99 if "yes" in framing else 0.01, "oc"

events = (
    [{"outcome_framing": "yes A", "outcome_real": 1}] * 30 +
    [{"outcome_framing": "yes B", "outcome_real": 0}] * 20 +  # wrongly confident
    [{"outcome_framing": "no A", "outcome_real": 0}] * 30 +
    [{"outcome_framing": "no B", "outcome_real": 1}] * 20  # wrongly confident
)
res = pit_histogram(events, overconfident, n_bins=10, seed=2)
print(f"  diag={res['diagnosis']} u_score={res['u_score']:.2f}")
# Overconfident should produce U-shape (under-coverage) — counts piled at extremes
check(res["u_score"] > 0, f"underconfident-like (got u_score {res['u_score']:.2f})")

print("\n[4] pit_histogram — empty")
res = pit_histogram([], perfect)
check(res["n"] == 0, "empty handled")

print("\n[5] PIT on real classifier + holdout")
sys.path.insert(0, "/home/pedroafonso/vila-inteia")
from engine.post_cutoff_classifier import classify_and_predict
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

all_events = []
for fn in ["post_cutoff_q1_2026.csv", "post_cutoff_q1_2026_v2.csv",
           "post_cutoff_q2_2026_holdout.csv",
           "brazil_votes_q1_2026.csv", "sports_specific_q1_2026.csv",
           "tech_releases_q1_2026.csv", "elections_2026_q1.csv",
           "space_science_q1_2026.csv", "price_predictions_q1_2026.csv"]:
    fp = f"/home/pedroafonso/vila-inteia/data/backtest/{fn}"
    all_events += load_csv(fp)

res = pit_histogram(all_events, classify_and_predict, n_bins=10, seed=42)
print(f"  Real classifier on {res['n']} events:")
print(f"  bins counts: {res['counts']}")
print(f"  chi²={res['chi_square']:.2f} slope={res['slope']:.2f} u_score={res['u_score']:.2f}")
print(f"  Diagnosis: {res['diagnosis']}")
check(res["n"] == 110, f"110 events (got {res['n']})")

print(f"\n{ok} ok, {fail} fail")
sys.exit(0 if fail == 0 else 1)
