"""Tests for engine/hierarchical_bayes.py — 2-level Beta-Binomial."""
import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from engine.hierarchical_bayes import (
    fit_hierarchical_bayes, hierarchical_predict, evaluate_hbe,
)
from engine.empirical_bayes import fit_beta_binomial
from engine.post_cutoff_classifier import classify_and_predict, KEYWORD_PRIORS

ok = fail = 0
def check(cond, msg):
    global ok, fail
    if cond: ok += 1; print(f"  OK  {msg}")
    else: fail += 1; print(f"  FAIL {msg}")


print("=== test_hierarchical_bayes ===")


def fake_clf(framing, contexto=""):
    f = framing.lower()
    if "sports_specific" in f: return 0.30, "sports_specific"
    if "sports_struct" in f: return 0.75, "sports_struct"
    if "war" in f: return 0.80, "war"
    if "elec" in f: return 0.50, "election"
    return 0.50, "default"


parent_map = {
    "sports_specific": "sports",
    "sports_struct": "sports",
    "war": "geopolitics",
    "election": "politics",
}


print("\n[1] basic shrinkage toward parent group")
# sports_specific scarce (1 event), sports_struct abundant. Borrow from sibling.
events = (
    [{"outcome_framing": "sports_struct A", "outcome_real": 1, "contexto": ""}] * 8 +
    [{"outcome_framing": "sports_struct B", "outcome_real": 1, "contexto": ""}] * 2 +
    [{"outcome_framing": "sports_specific Z", "outcome_real": 0, "contexto": ""}] * 1
)
post = fit_hierarchical_bayes(events, fake_clf, parent_map, prior_strength=3.0)
# group sports: k=10, n=11 -> p_g ≈ 0.909.
# sports_specific leaf: k=0, n=1 -> (0.909*3 + 0)/(3 + 1) = 2.727/4 ≈ 0.682
check("sports_specific" in post, "sports_specific present")
check(0.55 < post["sports_specific"] < 0.80,
      f"sports_specific shrunk toward group (got {post['sports_specific']:.3f})")

print("\n[2] standalone category (no parent in map) uses self prior")
events2 = [{"outcome_framing": "default thing", "outcome_real": 1, "contexto": ""}] * 4
post2 = fit_hierarchical_bayes(events2, fake_clf, parent_map={}, prior_strength=3.0)
# parent_map empty -> group=label, p_g = empirical (1.0)
# posterior = (1.0*3 + 4) / (3 + 4) = 7/7 = 1.0
check(post2["default"] > 0.90, f"self-only group near empirical ({post2['default']:.3f})")

print("\n[3] hierarchical_predict label + fallback")
p, lbl = hierarchical_predict("war event", "", fake_clf, post)
check(lbl == "war", f"label kept ({lbl})")
post_partial = {"war": 0.85}
p, lbl = hierarchical_predict("election thing", "", fake_clf, post_partial)
check(p == 0.50, f"unseen falls back to hardcode ({p})")

print("\n[4] HBE >= EB stability for scarce cats (no worse on balanced data)")
# Compare HBE vs flat EB on the same fake events (sports group all-1s).
post_eb = fit_beta_binomial(events, fake_clf, prior_strength=3.0)
# EB sports_specific: alpha=0.30*3=0.9, beta=2.1, k=0, n=1 -> 0.9/4 = 0.225
# HBE pulls it up via sports group mean ~0.91 -> ~0.68
check(post["sports_specific"] > post_eb["sports_specific"],
      f"HBE > EB for scarce cat (HBE={post['sports_specific']:.3f} EB={post_eb['sports_specific']:.3f})")

print("\n[5] empty events return empty posterior")
post3 = fit_hierarchical_bayes([], fake_clf, parent_map, prior_strength=3.0)
check(post3 == {}, "empty in -> empty out")


print("\n[6] real-data: post_cutoff_q2_2026_holdout (n=10)")
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
base = "/home/pedroafonso/vila-inteia/data/backtest"
cal = []
for f in cal_files:
    cal += load_csv(f"{base}/{f}")
test = []
for f in test_files:
    test += load_csv(f"{base}/{f}")

# Build parent_map for real categories.
real_parents = {
    "war_conflict": "geopolitics",
    "geopolitical_low": "geopolitics",
    "geopolitical_routine": "geopolitics",
    "regime_change": "geopolitics",
    "tariff_action": "geopolitics",
    "casualty_threshold": "geopolitics",
    "sports_specific_winner": "sports",
    "sports_event_structure": "sports",
    "negative_rank_claim": "sports",
    "scheduled_event": "events",
    "central_bank_meeting": "macro",
    "fed_action": "macro",
    "election": "politics",
    "polling": "politics",
    "br_legislative": "politics",
    "br_reform_complex": "politics",
    "regulatory_active": "regulatory",
    "regulatory_action": "regulatory",
    "corporate_action": "corporate",
    "corporate_negative": "corporate",
    "tech_release": "tech",
    "price_threshold": "markets",
    "price_target": "markets",
    "etf_approval": "markets",
    "crypto_product_launch": "markets",
    "extreme_quantity_claim": "markets",
}

post_real = fit_hierarchical_bayes(cal, classify_and_predict, real_parents, prior_strength=3.0)
res = evaluate_hbe(test, classify_and_predict, post_real)

# Baseline (raw classifier, no EB).
hits_b = 0
brier_b = 0.0
for e in test:
    p, _ = classify_and_predict(e["outcome_framing"], e["contexto"], use_eb_tuned=False)
    if (p >= 0.5) == bool(e["outcome_real"]):
        hits_b += 1
    brier_b += (p - e["outcome_real"]) ** 2

n_t = len(test)
print(f"  Baseline (raw): acc={hits_b/n_t:.1%} brier={brier_b/n_t:.4f}")
print(f"  HBE:            acc={res['acc']:.1%} brier={res['brier']:.4f}")
check(res["n"] == 10, f"n=10 (got {res['n']})")
check(res["brier"] <= brier_b / n_t + 0.10, "HBE brier within tolerance of baseline")

print(f"\n{ok} ok, {fail} fail")
sys.exit(0 if fail == 0 else 1)
