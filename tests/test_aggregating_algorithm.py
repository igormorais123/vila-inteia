"""Tests for engine/aggregating_algorithm.py — Vovk AA log-loss."""
import csv
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from engine.aggregating_algorithm import aggregating_algorithm
from engine.post_cutoff_classifier import classify_and_predict
from engine.empirical_bayes import fit_beta_binomial, empirical_bayes_predict

ok = fail = 0
def check(cond, msg):
    global ok, fail
    if cond: ok += 1; print(f"  OK  {msg}")
    else: fail += 1; print(f"  FAIL {msg}")


print("=== test_aggregating_algorithm ===")


print("\n[1] empty inputs")
res = aggregating_algorithm([], [])
check(res["regret"] == 0.0, "empty -> regret 0")
check(res["aa_preds"] == [], "empty preds list")

print("\n[2] single expert -> AA matches that expert exactly")
preds = [{"e1": 0.7}, {"e1": 0.3}, {"e1": 0.9}]
ys = [1, 0, 1]
res = aggregating_algorithm(preds, ys)
expected_loss = -math.log(0.7) - math.log(0.7) - math.log(0.9)
check(abs(res["aa_loss"] - expected_loss) < 1e-9,
      f"AA loss matches single expert ({res['aa_loss']:.4f} vs {expected_loss:.4f})")
check(abs(res["regret"]) < 1e-9, f"regret~0 (got {res['regret']:.4e})")

print("\n[3] regret bounded by log(K) for log-loss (Vovk 1998 Thm)")
# Two experts, one always right, one always wrong.
preds = [{"good": 0.99, "bad": 0.01}] * 5 + [{"good": 0.99, "bad": 0.01}] * 5
ys = [1] * 10
res = aggregating_algorithm(preds, ys)
log_K = math.log(2)
# AA regret should be <= log(K) when log-loss mixable game holds.
print(f"  regret={res['regret']:.4f}  log(K)={log_K:.4f}")
check(res["regret"] <= log_K + 0.5,
      f"regret <= log(K) tolerance ({res['regret']:.3f})")

print("\n[4] weights concentrate on best expert")
preds = (
    [{"good": 0.9, "bad": 0.1}] * 10 +
    [{"good": 0.9, "bad": 0.1}] * 10
)
ys = [1] * 20
res = aggregating_algorithm(preds, ys)
check(res["weights"]["good"] > res["weights"]["bad"],
      f"good weight > bad ({res['weights']['good']:.3f} vs {res['weights']['bad']:.3f})")
check(res["weights"]["good"] > 0.99,
      f"good dominates ({res['weights']['good']:.4f})")

print("\n[5] mismatched lengths raises")
try:
    aggregating_algorithm([{"e": 0.5}], [1, 0])
    check(False, "expected ValueError")
except ValueError:
    check(True, "raised on length mismatch")


print("\n[6] real-data: 3 experts on post_cutoff_q2_2026_holdout (n=10)")
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


base = "/home/pedroafonso/vila-inteia/data/backtest"
cal = []
for f in ["post_cutoff_q1_2026.csv", "post_cutoff_q1_2026_v2.csv",
          "brazil_votes_q1_2026.csv", "sports_specific_q1_2026.csv"]:
    cal += load_csv(f"{base}/{f}")
test = load_csv(f"{base}/post_cutoff_q2_2026_holdout.csv")

eb_post = fit_beta_binomial(cal, classify_and_predict, prior_strength=3.0)

# 3 experts: raw classifier, EB-tuned classifier, fixed naive=0.6.
preds_per_round = []
ys = []
for e in test:
    fr, ctx = e["outcome_framing"], e["contexto"]
    p_raw, _ = classify_and_predict(fr, ctx, use_eb_tuned=False)
    p_eb, _ = empirical_bayes_predict(fr, ctx, classify_and_predict, eb_post)
    preds_per_round.append({"raw": p_raw, "eb": p_eb, "naive": 0.6})
    ys.append(e["outcome_real"])

res = aggregating_algorithm(preds_per_round, ys)
print(f"  T={res['T']}  K={res['K']}  AA loss={res['aa_loss']:.3f}  best={res['best_expert_loss']:.3f}  regret={res['regret']:.3f}")
print(f"  weights: " + ", ".join(f"{k}={v:.3f}" for k, v in res["weights"].items()))

check(res["T"] == 10, f"T=10 (got {res['T']})")
check(res["K"] == 3, f"K=3 (got {res['K']})")
check(res["regret"] >= -1e-9, f"regret >= 0 (got {res['regret']:.4f})")
check(res["regret"] <= math.log(res["K"]) + 1.0,
      f"regret <= log(K)+slack (got {res['regret']:.3f})")
total_w = sum(res["weights"].values())
check(abs(total_w - 1.0) < 1e-9, f"weights sum to 1 ({total_w:.6f})")


print(f"\n{ok} ok, {fail} fail")
sys.exit(0 if fail == 0 else 1)
