"""Onda 254: testa engine/empirical_bayes.py."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from engine.empirical_bayes import (
    fit_beta_binomial, empirical_bayes_predict, evaluate_eb,
)

ok = fail = 0
def check(cond, msg):
    global ok, fail
    if cond: ok += 1; print(f"  OK  {msg}")
    else: fail += 1; print(f"  FAIL {msg}")


print("=== test_empirical_bayes ===")

print("\n[1] fit_beta_binomial — empirical dominates with large n")
def fake_clf(framing, contexto=""):
    if "war" in framing.lower():
        return 0.8, "war"
    if "regime" in framing.lower():
        return 0.30, "regime"  # hardcode wrong; reality is 0.8
    return 0.5, "default"

# Regime: hardcode 0.30 but 8 of 10 cal events are real=1
events = (
    [{"outcome_framing": "regime change X", "outcome_real": 1, "contexto": ""}] * 8 +
    [{"outcome_framing": "regime change Y", "outcome_real": 0, "contexto": ""}] * 2
)
post = fit_beta_binomial(events, fake_clf, prior_strength=5.0)
# alpha = 0.30 * 5 = 1.5, beta = 3.5
# posterior = (1.5 + 8) / (5 + 10) = 9.5/15 ≈ 0.633
check("regime" in post, f"regime cat (got {list(post.keys())})")
check(0.55 < post["regime"] < 0.70, f"regime corrected up ({post['regime']:.2f})")

print("\n[2] prior dominates with small n")
events_small = [{"outcome_framing": "war event", "outcome_real": 1, "contexto": ""}]
post_small = fit_beta_binomial(events_small, fake_clf, prior_strength=10.0)
# alpha = 0.8 * 10 = 8, beta = 2, k=1, n=1
# posterior = (8 + 1) / (10 + 1) = 9/11 ≈ 0.818
check(0.78 < post_small["war"] < 0.85, f"war stays near hardcode ({post_small['war']:.2f})")

print("\n[3] empirical_bayes_predict")
p, lbl = empirical_bayes_predict("regime change Z", "", fake_clf, post)
check(lbl == "regime", f"label preserved (got {lbl})")
check(abs(p - post["regime"]) < 1e-9, f"uses posterior (got {p:.3f})")

# Unseen category falls back
post_partial = {"war": 0.85}
p, lbl = empirical_bayes_predict("default thing", "", fake_clf, post_partial)
check(p == 0.5, f"unseen fallback ({p})")

print("\n[4] evaluate_eb end-to-end on real classifier")
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

cal_files = [
    "post_cutoff_q1_2026.csv", "post_cutoff_q1_2026_v2.csv",
    "brazil_votes_q1_2026.csv", "sports_specific_q1_2026.csv",
    "tech_releases_q1_2026.csv", "elections_2026_q1.csv",
    "space_science_q1_2026.csv", "price_predictions_q1_2026.csv",
]
test_files = ["post_cutoff_q2_2026_holdout.csv"]

cal = []
for f in cal_files:
    cal += load_csv(f"/home/pedroafonso/vila-inteia/data/backtest/{f}")
test = []
for f in test_files:
    test += load_csv(f"/home/pedroafonso/vila-inteia/data/backtest/{f}")

post = fit_beta_binomial(cal, classify_and_predict, prior_strength=3.0)
res_eb = evaluate_eb(test, classify_and_predict, post)

# Baseline (no EB)
hits = 0
brier = 0.0
for e in test:
    p, _ = classify_and_predict(e["outcome_framing"], e["contexto"])
    if (p >= 0.5) == bool(e["outcome_real"]):
        hits += 1
    brier += (p - e["outcome_real"]) ** 2
n = len(test)
res_base = {"acc": hits / n, "brier": brier / n}

print(f"  Baseline: acc={res_base['acc']:.1%} brier={res_base['brier']:.4f}")
print(f"  EB:       acc={res_eb['acc']:.1%} brier={res_eb['brier']:.4f}")
check(res_eb["n"] == 10, f"n=10 (got {res_eb['n']})")
check(res_eb["brier"] <= res_base["brier"] + 0.05, "EB doesn't hurt much")

print(f"\n{ok} ok, {fail} fail")
sys.exit(0 if fail == 0 else 1)
