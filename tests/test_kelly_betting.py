"""Tests for engine/kelly_betting.py (Kelly 1956)."""
import sys, csv
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from engine.kelly_betting import (
    kelly_fraction, expected_value, kelly_betting_simulation,
)
from engine.post_cutoff_classifier import classify_and_predict

ok = fail = 0
def check(cond, msg):
    global ok, fail
    if cond: ok += 1; print(f"  OK  {msg}")
    else: fail += 1; print(f"  FAIL {msg}")


print("=== test_kelly_betting ===")

print("\n[1] Closed-form: p=0.6, odds=2.0 -> b=1, q=0.4 -> f=0.2")
f = kelly_fraction(0.6, 2.0)
check(abs(f - 0.2) < 1e-9, f"f=0.2 (got {f})")

print("\n[2] No edge -> f=0")
# p=0.5 at fair 2.0 odds: ev = 0
f = kelly_fraction(0.5, 2.0)
check(f == 0.0, f"no-edge fraction (got {f})")
# Negative edge
f = kelly_fraction(0.4, 2.0)
check(f == 0.0, f"negative-edge clipped (got {f})")
# Bad inputs
check(kelly_fraction(0.7, 1.0) == 0.0, "odds<=1 -> 0")

print("\n[3] EV sign matches edge")
check(expected_value(0.6, 2.0) > 0, "ev positive when edge")
check(abs(expected_value(0.5, 2.0)) < 1e-9, "ev=0 at fair odds")
check(expected_value(0.3, 2.0) < 0, "ev negative")

print("\n[4] Half-Kelly halves stake")
full = kelly_fraction(0.7, 2.0)
half = kelly_fraction(0.7, 2.0, fractional=0.5)
check(abs(half - full * 0.5) < 1e-9, f"half-kelly (full={full}, half={half})")

print("\n[5] Tiny synthetic sim: deterministic outcomes")
# Two events, both winners at p=0.7 odds=2.0 -> f=0.4 each
fake = [
    {"outcome_framing": "guerra", "contexto": "", "outcome_real": 1, "decimal_odds": 2.0},
    {"outcome_framing": "guerra", "contexto": "", "outcome_real": 1, "decimal_odds": 2.0},
]
def fake_classify(framing, contexto):
    return 0.7
sim = kelly_betting_simulation(fake, fake_classify, initial_bankroll=1000.0)
# Stake1 = 400, win -> +400 -> 1400. Stake2 = 1400*0.4=560, win -> +560 -> 1960
check(abs(sim["final_bankroll"] - 1960.0) < 1e-6,
      f"compounded growth (got {sim['final_bankroll']})")
check(sim["bets"] == 2 and sim["wins"] == 2, "2 bets / 2 wins")

print("\n[6] Real bench: post_cutoff_q2_2026_holdout_v2 @ 1.91 odds")
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
                               initial_bankroll=1000.0,
                               fractional=0.5)  # half-Kelly
print(f"  N={len(events)} bets={sim['bets']} wins={sim['wins']}"
      f" win_rate={sim['win_rate']:.2%}")
print(f"  final_bankroll=${sim['final_bankroll']:.2f}"
      f" (return {sim['total_return']:+.2%})")
print(f"  sharpe={sim['sharpe']:.3f} max_dd={sim['max_drawdown']:.2%}")

check(len(events) >= 30, f"loaded enough events (got {len(events)})")
check(sim["initial_bankroll"] == 1000.0, "initial preserved")
check(sim["final_bankroll"] >= 0, "bankroll non-negative")
check(0 <= sim["max_drawdown"] <= 1.0, "max_dd in [0,1]")

print(f"\n{ok} ok, {fail} fail")
sys.exit(0 if fail == 0 else 1)
