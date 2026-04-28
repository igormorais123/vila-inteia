"""Tests engine/kalman_binary.py — Kalman filter for binary forecasts."""
import sys, csv, math
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from engine.kalman_binary import (
    KalmanBinaryFilter, run_kalman, evaluate_kalman,
)
from engine.post_cutoff_classifier import classify_and_predict

ok = fail = 0
def check(cond, msg):
    global ok, fail
    if cond: ok += 1; print(f"  OK  {msg}")
    else: fail += 1; print(f"  FAIL {msg}")


print("=== test_kalman_binary ===")

print("\n[1] KalmanBinaryFilter init + predict")
kf = KalmanBinaryFilter(initial_logit=0.0, Q=0.01, R=1.0)
check(abs(kf.prob() - 0.5) < 1e-9, "init prob 0.5")
p = kf.predict()
check(abs(p - 0.5) < 1e-9, f"predict pre-obs still ~0.5 ({p:.4f})")
check(kf.P > 1.0, f"P grew by Q ({kf.P:.4f})")

print("\n[2] update moves prob toward observation")
kf = KalmanBinaryFilter()
p_before = kf.prob()
for _ in range(10):
    kf.predict(); kf.update(1)
p_after = kf.prob()
print(f"  before={p_before:.4f} after10x_y=1: {p_after:.4f}")
check(p_after > 0.7, f"prob shifted up ({p_after:.4f})")

kf2 = KalmanBinaryFilter()
for _ in range(10):
    kf2.predict(); kf2.update(0)
p2 = kf2.prob()
print(f"  after10x_y=0: {p2:.4f}")
check(p2 < 0.3, f"prob shifted down ({p2:.4f})")

print("\n[3] run_kalman returns trajectory")
outs = [1, 1, 1, 0, 0, 0, 1, 1, 1, 1]
traj = run_kalman(outs, Q=0.05, R=1.0)
print(f"  trajectory: {[round(p, 3) for p in traj]}")
check(len(traj) == len(outs), "len matches")
check(all(0.0 <= p <= 1.0 for p in traj), "all probs in [0,1]")
check(traj[-1] > 0.5, f"final after y=1 streak >0.5 ({traj[-1]:.4f})")

print("\n[4] evaluate_kalman synthetic — biased coin")
import random
random.seed(7)
outs = [1 if random.random() < 0.7 else 0 for _ in range(80)]
res = evaluate_kalman(outs, Q=0.02, R=1.0)
print(f"  n={res['n']} acc={res['acc']:.1%} brier={res['brier']:.4f}")
print(f"  final_logit={res['final_logit']:.3f} final_prob={res['final_prob']:.4f}")
check(res["n"] == 80, "n=80")
check(res["final_prob"] > 0.5, f"learned bias toward 1 ({res['final_prob']:.4f})")
check(res["brier"] < 0.27, f"brier reasonable ({res['brier']:.4f})")

print("\n[5] Kalman on real Q2 holdout outcomes")
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

events = load_csv("/home/pedroafonso/vila-inteia/data/backtest/post_cutoff_q2_2026_holdout.csv")
events += load_csv("/home/pedroafonso/vila-inteia/data/backtest/post_cutoff_q2_2026_holdout_v2.csv")
outcomes = [e["outcome_real"] for e in events]
n_pos = sum(outcomes); n_tot = len(outcomes)
print(f"  n_total={n_tot} n_pos={n_pos} base_rate={n_pos/n_tot:.3f}")

# Kalman variants — different Q/R
for Q, R in [(0.01, 1.0), (0.05, 1.0), (0.1, 0.5)]:
    res = evaluate_kalman(outcomes, Q=Q, R=R)
    print(f"  Q={Q} R={R}: acc={res['acc']:.1%} brier={res['brier']:.4f} "
          f"final_p={res['final_prob']:.3f}")
    check(0.0 <= res["brier"] <= 1.0, f"brier in [0,1] (Q={Q})")

# combine with classifier: kalman tracks bias of classifier residuals
def base(f, c=""): return classify_and_predict(f, c)[0]
residuals = []
for e in events:
    p = base(e["outcome_framing"], e["contexto"])
    residuals.append(1 if e["outcome_real"] >= p else 0)
res_resid = evaluate_kalman(residuals, Q=0.05, R=1.0)
print(f"  classifier-residual kalman: final_p={res_resid['final_prob']:.4f}")
check(0.0 <= res_resid["final_prob"] <= 1.0, "residual prob valid")

print(f"\n{ok} ok, {fail} fail")
sys.exit(0 if fail == 0 else 1)
