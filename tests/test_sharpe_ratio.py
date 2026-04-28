"""Tests for engine/sharpe_ratio.py."""
import sys, csv, math
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from engine.sharpe_ratio import (
    sharpe_ratio, sortino_ratio, sharpe_breakdown,
)
from engine.kelly_betting import kelly_betting_simulation
from engine.post_cutoff_classifier import classify_and_predict

ok = fail = 0
def check(cond, msg):
    global ok, fail
    if cond: ok += 1; print(f"  OK  {msg}")
    else: fail += 1; print(f"  FAIL {msg}")


print("=== test_sharpe_ratio ===")

print("\n[1] Empty / singleton -> 0")
check(sharpe_ratio([]) == 0.0, "empty -> 0")
check(sharpe_ratio([0.05]) == 0.0, "n=1 -> 0")
check(sortino_ratio([]) == 0.0, "sortino empty -> 0")

print("\n[2] Constant returns -> std=0 -> 0")
check(sharpe_ratio([0.1, 0.1, 0.1, 0.1]) == 0.0, "constant -> 0")

print("\n[3] Closed form sanity")
# Returns 0.10, 0.20: mean=0.15, sample sd via n-1: sqrt((0.05^2+0.05^2)/1)
# = sqrt(0.005)=0.0707 -> sharpe = 0.15/0.0707 ~ 2.121
s = sharpe_ratio([0.10, 0.20])
expected = 0.15 / math.sqrt(0.005)
check(abs(s - expected) < 1e-6, f"closed-form sharpe (got {s})")

print("\n[4] Sortino > Sharpe when only some downside")
# Mixed returns with limited downside
rs = [0.05, 0.10, -0.02, 0.08, 0.06, -0.01]
sh = sharpe_ratio(rs)
so = sortino_ratio(rs)
check(so > sh, f"sortino={so:.3f} > sharpe={sh:.3f}")

print("\n[5] All-positive returns -> sortino=0 (no downside)")
so = sortino_ratio([0.01, 0.02, 0.03, 0.04])
check(so == 0.0, f"no downside -> 0 (got {so})")

print("\n[6] Risk-free shifts excess")
rs = [0.05, 0.06, 0.07, 0.08]
s0 = sharpe_ratio(rs, risk_free=0.0)
s1 = sharpe_ratio(rs, risk_free=0.05)
# Higher risk_free -> lower numerator -> lower sharpe
check(s1 < s0, f"rf shift (rf=0:{s0:.3f}, rf=0.05:{s1:.3f})")

print("\n[7] Real bench: per-bet returns from Kelly sim on holdout")
events = []
with open("/home/pedroafonso/vila-inteia/data/backtest/"
          "post_cutoff_q2_2026_holdout_v2.csv") as fh:
    for r in csv.DictReader(fh):
        try:
            events.append({
                "outcome_framing": r.get("outcome_framing")
                                    or r.get("framing", ""),
                "contexto": r.get("contexto", ""),
                "outcome_real": int(r["outcome_real"]),
                "decimal_odds": 1.91,
            })
        except (ValueError, KeyError):
            pass

sim = kelly_betting_simulation(events, classify_and_predict,
                               initial_bankroll=1000.0, fractional=0.5)
ret = [r for r in sim["returns"] if r != 0.0]  # only actual bets
br = sharpe_breakdown(ret)
print(f"  N={br['n']} mean={br['mean']:+.4f} std={br['std']:.4f}")
print(f"  sharpe={br['sharpe']:.3f} sortino={br['sortino']:.3f}")
check(br["n"] > 0, "had real bets")
check(math.isfinite(br["sharpe"]), "sharpe finite")
check(math.isfinite(br["sortino"]), "sortino finite")

print(f"\n{ok} ok, {fail} fail")
sys.exit(0 if fail == 0 else 1)
