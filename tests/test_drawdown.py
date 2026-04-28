"""Tests for engine/drawdown.py."""
import sys, csv
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from engine.drawdown import max_drawdown, drawdown_metrics
from engine.kelly_betting import kelly_betting_simulation
from engine.post_cutoff_classifier import classify_and_predict

ok = fail = 0
def check(cond, msg):
    global ok, fail
    if cond: ok += 1; print(f"  OK  {msg}")
    else: fail += 1; print(f"  FAIL {msg}")


print("=== test_drawdown ===")

print("\n[1] Empty -> zeros")
r = max_drawdown([])
check(r["max_dd"] == 0.0 and r["peak_idx"] == -1, f"empty (got {r})")

print("\n[2] Monotone up -> dd=0")
r = max_drawdown([100, 110, 120, 130])
check(r["max_dd"] == 0.0, f"no drawdown (got {r['max_dd']})")

print("\n[3] V-shape: 100 -> 50 -> 100")
# Peak=100 at i=0, trough=50 at i=1, recovery at i=2.
r = max_drawdown([100, 50, 100])
check(abs(r["max_dd"] - 0.5) < 1e-9, f"50% dd (got {r['max_dd']})")
check(r["peak_idx"] == 0 and r["trough_idx"] == 1,
      f"peak/trough idx (got {r['peak_idx']},{r['trough_idx']})")
check(r["recovery_idx"] == 2, f"recovery idx (got {r['recovery_idx']})")

print("\n[4] Never recovered -> recovery_idx=-1")
r = max_drawdown([100, 80, 90, 85])
check(r["recovery_idx"] == -1, f"no recovery (got {r['recovery_idx']})")
check(abs(r["max_dd"] - 0.20) < 1e-9, f"20% dd (got {r['max_dd']})")

print("\n[5] drawdown_metrics chains returns to bankroll")
# Returns -10%, +10% -> 1000 -> 900 -> 990
r = drawdown_metrics([-0.10, 0.10], initial=1000.0)
check(abs(r["final_bankroll"] - 990.0) < 1e-6,
      f"chained final={r['final_bankroll']}")
check(abs(r["max_dd"] - 0.10) < 1e-9, f"10% dd (got {r['max_dd']})")

print("\n[6] DD duration is trough-from-peak (steps)")
# Peak at 0, trough at 3
r = max_drawdown([100, 95, 90, 70, 80])
check(r["dd_duration"] == 3, f"dd_duration=3 (got {r['dd_duration']})")

print("\n[7] Real bench: holdout Kelly bankroll series")
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
dd = max_drawdown(sim["bankroll_series"])
print(f"  N_series={len(sim['bankroll_series'])} max_dd={dd['max_dd']:.2%}"
      f" peak@{dd['peak_idx']} trough@{dd['trough_idx']}"
      f" recovery@{dd['recovery_idx']}")
check(0.0 <= dd["max_dd"] <= 1.0, f"max_dd valid (got {dd['max_dd']})")
check(dd["peak_idx"] <= dd["trough_idx"], "peak before trough")

print(f"\n{ok} ok, {fail} fail")
sys.exit(0 if fail == 0 else 1)
