"""Onda 229: testa engine/validation_rigorous.py."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from engine.validation_rigorous import (
    murphy_decomposition, bootstrap_ci, diebold_mariano,
    roc_auc, reliability_diagram, knowledge_leak_warning,
    _normal_cdf,
)

ok = fail = 0
def check(cond, msg):
    global ok, fail
    if cond: ok += 1; print(f"  OK  {msg}")
    else: fail += 1; print(f"  FAIL {msg}")


print("=== test_validation_rigorous ===")

print("\n[1] Murphy decomposition: brier = REL - RES + UNC")
preds = [0.9, 0.8, 0.7, 0.6, 0.4, 0.3, 0.2, 0.1, 0.5, 0.5]
reals = [1, 1, 1, 0, 1, 0, 0, 0, 1, 0]
m = murphy_decomposition(preds, reals)
# Identidade sempre vale: brier = REL - RES + UNC
ident = m["reliability"] - m["resolution"] + m["uncertainty"]
check(abs(m["brier"] - ident) < 1e-9, f"identidade Murphy: {m['brier']:.4f} = REL-RES+UNC")
check(m["uncertainty"] > 0, f"UNC = {m['uncertainty']:.4f}")
check(m["reliability"] >= 0, "REL >= 0")
check(m["resolution"] >= 0, "RES >= 0")

print("\n[2] Bootstrap CI brier")
ci = bootstrap_ci(preds, reals, metric="brier", n_resamples=200, seed=42)
check(ci["lower"] <= ci["mean"] <= ci["upper"], "lower ≤ mean ≤ upper")
check(ci["upper"] - ci["lower"] > 0, "CI tem largura positiva")

ci_acc = bootstrap_ci(preds, reals, metric="acc", n_resamples=200)
check(0 <= ci_acc["mean"] <= 1, f"acc in [0, 1] (got {ci_acc['mean']:.3f})")

print("\n[3] Diebold-Mariano test detecta diferença")
# A perfeito vs B random
preds_a = [0.99, 0.99, 0.01, 0.01]
preds_b = [0.5, 0.5, 0.5, 0.5]
reals_dm = [1, 1, 0, 0]
dm = diebold_mariano(preds_a, preds_b, reals_dm)
check(dm["mean_diff"] < 0, f"A loss < B loss (mean_diff={dm['mean_diff']:.4f})")

# Mesmo forecaster: dm_stat ~0, p~1
dm_same = diebold_mariano(preds_a, preds_a, reals_dm)
check(abs(dm_same["mean_diff"]) < 1e-9, "same forecaster = mean_diff 0")

print("\n[4] ROC AUC: perfeito vs random")
auc_perfect = roc_auc([0.9, 0.8, 0.1, 0.2], [1, 1, 0, 0])
check(auc_perfect["auc"] == 1.0, f"perfect AUC=1.0 (got {auc_perfect['auc']})")

auc_inverse = roc_auc([0.1, 0.2, 0.9, 0.8], [1, 1, 0, 0])
check(auc_inverse["auc"] == 0.0, f"inverse AUC=0.0 (got {auc_inverse['auc']})")

auc_tied = roc_auc([0.5, 0.5, 0.5, 0.5], [1, 1, 0, 0])
check(auc_tied["auc"] == 0.5, f"tied AUC=0.5 (got {auc_tied['auc']})")

print("\n[5] Reliability diagram bins")
rd = reliability_diagram(preds, reals, n_bins=5)
check(len(rd) == 5, "5 bins")
total_count = sum(b["count"] for b in rd)
check(total_count == len(preds), f"counts somam ao N (got {total_count})")

print("\n[6] Knowledge leak warning")
# 100% pre-cutoff
warn1 = knowledge_leak_warning(["2024-01-01", "2023-05-15"], llm_cutoff="2026-01-01")
check(warn1["leak_ratio"] == 1.0, f"all pre-cutoff (got {warn1['leak_ratio']})")
check(warn1["warning"] is not None, "warning shown")

# Mix
warn2 = knowledge_leak_warning(["2024-01-01", "2027-05-15"], llm_cutoff="2026-01-01")
check(warn2["n_pre_cutoff"] == 1 and warn2["n_post_cutoff"] == 1, "split correto")

# All post-cutoff
warn3 = knowledge_leak_warning(["2027-01-01"], llm_cutoff="2026-01-01")
check(warn3["warning"] is None, "no warning (all post-cutoff)")

print("\n[7] _normal_cdf approximation")
check(abs(_normal_cdf(0) - 0.5) < 1e-6, "CDF(0) = 0.5")
check(_normal_cdf(2) > 0.97, f"CDF(2) > 0.97 (got {_normal_cdf(2):.4f})")
check(_normal_cdf(-2) < 0.03, f"CDF(-2) < 0.03 (got {_normal_cdf(-2):.4f})")

print(f"\n{ok} ok, {fail} fail")
sys.exit(0 if fail == 0 else 1)
