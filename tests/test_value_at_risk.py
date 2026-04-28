"""Tests for engine/value_at_risk.py."""
import sys, csv
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from engine.value_at_risk import var_cvar, historical_simulation_var
from engine.kelly_betting import kelly_betting_simulation
from engine.post_cutoff_classifier import classify_and_predict

ok = fail = 0
def check(cond, msg):
    global ok, fail
    if cond: ok += 1; print(f"  OK  {msg}")
    else: fail += 1; print(f"  FAIL {msg}")


print("=== test_value_at_risk ===")

print("\n[1] Empty -> zeros")
r = var_cvar([])
check(r["n"] == 0 and r["var"] == 0.0 and r["cvar"] == 0.0,
      f"empty (got {r})")

print("\n[2] Closed form: 0..99, alpha=0.05 -> VaR ≈ 4.95")
rs = list(range(100))
r = var_cvar(rs, alpha=0.05)
check(abs(r["var"] - 4.95) < 1e-6, f"VaR p5 (got {r['var']})")
# CVaR is mean of returns <= 4.95 -> {0..4} mean=2.0
check(abs(r["cvar"] - 2.0) < 1e-9, f"CVaR (got {r['cvar']})")

print("\n[3] CVaR <= VaR for losses (returns sorted asc)")
losses = [-0.10, -0.08, -0.05, -0.02, 0.0, 0.02, 0.05, 0.08, 0.10, 0.12]
r = var_cvar(losses, alpha=0.10)
check(r["cvar"] <= r["var"], f"cvar={r['cvar']} <= var={r['var']}")

print("\n[4] historical_simulation_var convenience matches var_cvar")
v1 = historical_simulation_var(losses, alpha=0.05)
v2 = var_cvar(losses, alpha=0.05)["var"]
check(abs(v1 - v2) < 1e-12, f"helper matches ({v1} vs {v2})")

print("\n[5] Higher alpha -> less extreme VaR (closer to median)")
r1 = var_cvar(rs, alpha=0.05)["var"]
r2 = var_cvar(rs, alpha=0.50)["var"]
check(r2 > r1, f"alpha sensitivity ({r1} < {r2})")

print("\n[6] Worst/best populated")
r = var_cvar(losses, alpha=0.05)
check(r["worst"] == min(losses), f"worst (got {r['worst']})")
check(r["best"] == max(losses), f"best (got {r['best']})")

print("\n[7] Real bench: VaR/CVaR on holdout Kelly returns")
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
non_zero = [r for r in sim["returns"] if r != 0.0]
res = var_cvar(non_zero, alpha=0.05)
print(f"  N_returns={res['n']} VaR(5%)={res['var']:+.4f}"
      f" CVaR(5%)={res['cvar']:+.4f}")
print(f"  worst={res['worst']:+.4f} best={res['best']:+.4f}")
check(res["n"] > 0, "had returns")
check(res["cvar"] <= res["var"], "cvar <= var (left-tail)")

print(f"\n{ok} ok, {fail} fail")
sys.exit(0 if fail == 0 else 1)
