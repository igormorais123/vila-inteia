"""Tests engine/online_newton.py — Online Newton Step."""
import sys, csv, math
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from engine.online_newton import (
    OnlineNewton, online_newton_aggregator, evaluate_ons,
)
from engine.post_cutoff_classifier import classify_and_predict

ok = fail = 0
def check(cond, msg):
    global ok, fail
    if cond: ok += 1; print(f"  OK  {msg}")
    else: fail += 1; print(f"  FAIL {msg}")


print("=== test_online_newton ===")

print("\n[1] OnlineNewton init")
ons = OnlineNewton(d=1, eta=1.0)
check(ons.d == 1, "d=1")
check(ons.w == [0.0], "w init zero")
check(ons.A[0] > 0, "A init positive (eps)")
p0 = ons.predict(0.0)
check(abs(p0 - 0.5) < 1e-9, f"predict at 0 → 0.5 ({p0:.4f})")

print("\n[2] Hessian + weights move with updates")
ons = OnlineNewton(d=1, eta=1.0)
A0 = ons.A[0]
# feed strong positive signal
for _ in range(20):
    ons.update(2.0, 1)
check(ons.A[0] > A0, f"A grew ({ons.A[0]:.3f} > {A0:.3f})")
check(ons.w[0] > 0, f"w positive after y=1 stream ({ons.w[0]:.3f})")
p_pos = ons.predict(2.0)
check(p_pos > 0.5, f"predict pos x → > 0.5 ({p_pos:.4f})")

print("\n[3] online_newton_aggregator — synthetic monotone stream")
preds = [0.7] * 30
outs = [1] * 30
res = online_newton_aggregator(preds, outs, eta=1.0)
print(f"  n={res['n']} acc={res['acc']:.1%} brier={res['brier']:.4f}")
print(f"  final_w={res['final_w']} final_A={res['final_A']}")
check(res["n"] == 30, "n=30")
check(res["acc"] > 0.5, f"learns to predict 1 ({res['acc']:.1%})")
check(res["final_w"][0] > 0, "w drifted positive")

print("\n[4] online_newton_aggregator — opposite outcomes")
preds = [0.7] * 20
outs = [0] * 20  # classifier wrong, but ONS adapts logit
res2 = online_newton_aggregator(preds, outs, eta=1.0)
print(f"  acc={res2['acc']:.1%} brier={res2['brier']:.4f}")
print(f"  final_w={res2['final_w']}")
check(res2["final_w"][0] < 0, f"w turns negative when feature anti-correlates ({res2['final_w'][0]:.3f})")

print("\n[5] ONS on real classifier — Q2 holdout")
def classify_only(f, c=""): return classify_and_predict(f, c)[0]

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

# variant aggregators on top of base classifier
def base(f, c=""): return classify_and_predict(f, c)[0]
def stretched(f, c=""):
    p = classify_and_predict(f, c)[0]
    return min(1.0, max(0.0, 1.5 * p - 0.25))

print("  -- variant: base --")
res_base = evaluate_ons(events, base, eta=1.0)
print(f"  n={res_base['n']} acc={res_base['acc']:.1%} brier={res_base['brier']:.4f}")
print(f"  final_w={res_base['final_w']} final_A={res_base['final_A']}")

print("  -- variant: stretched --")
res_str = evaluate_ons(events, stretched, eta=1.0)
print(f"  n={res_str['n']} acc={res_str['acc']:.1%} brier={res_str['brier']:.4f}")
print(f"  final_w={res_str['final_w']}")

check(res_base["n"] >= 40, f"events loaded ({res_base['n']})")
check(0.0 <= res_base["brier"] <= 1.0, f"brier in [0,1] ({res_base['brier']:.4f})")
check(res_base["final_A"][0] > 1.0, "Hessian accumulated (>eps)")

print(f"\n{ok} ok, {fail} fail")
sys.exit(0 if fail == 0 else 1)
