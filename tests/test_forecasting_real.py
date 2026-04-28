"""Onda 231: testa engine/forecasting_real.py — strategies pra REAL forecasting."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from engine.forecasting_real import (
    shrink_toward, invert_tail, conservative_clip,
    base_rate_event_class, ensemble_strategies,
    apply_strategy, evaluate_strategy_on_events,
    autoresearch_loop_post_cutoff,
)

ok = fail = 0
def check(cond, msg):
    global ok, fail
    if cond: ok += 1; print(f"  OK  {msg}")
    else: fail += 1; print(f"  FAIL {msg}")


print("=== test_forecasting_real ===")

print("\n[1] shrink_toward pulls toward target")
check(shrink_toward(0.9, 0.5, 0.4) < 0.9, "0.9 → toward 0.5 (lower)")
check(shrink_toward(0.1, 0.5, 0.4) > 0.1, "0.1 → toward 0.5 (higher)")
check(shrink_toward(0.5, 0.5, 0.4) == 0.5, "0.5 stays 0.5")

print("\n[2] invert_tail flips extremes")
check(invert_tail(0.10) == 0.90, f"0.10 → 0.90 (got {invert_tail(0.10)})")
check(abs(invert_tail(0.95) - 0.05) < 1e-9, f"0.95 → 0.05 (got {invert_tail(0.95)})")
check(invert_tail(0.5) == 0.5, "0.5 unchanged")

print("\n[3] conservative_clip limits range")
check(conservative_clip(0.95) == 0.70, "0.95 → 0.70")
check(conservative_clip(0.05) == 0.30, "0.05 → 0.30")
check(conservative_clip(0.5) == 0.5, "0.5 unchanged")

print("\n[4] base_rate_event_class shrinks per category")
p = base_rate_event_class(0.9, "geopolitics_extreme")
check(0.5 < p < 0.9, f"geopolitics shrinks 0.9 → {p:.3f}")
p2 = base_rate_event_class(0.9, "tech_release")
check(p2 < p, "tech_release base 0.4 < geopolitics 0.5")

print("\n[5] ensemble_strategies combines defenses")
e = ensemble_strategies(0.95)
check(0.4 < e <= 0.75, f"0.95 → ensemble {e:.3f} (mid-range)")

print("\n[6] apply_strategy + evaluate end-to-end")
preds = [0.9, 0.1, 0.7, 0.3]
reals = [1, 0, 0, 1]
res = evaluate_strategy_on_events(preds, reals, "s1")
check(res["hits"] == 2, f"baseline 2 hits (got {res['hits']})")

res_s2 = evaluate_strategy_on_events(preds, reals, "s2")
check(res_s2["brier"] != res["brier"], "s2 different from baseline")

print("\n[7] autoresearch_loop returns trace + best")
loop = autoresearch_loop_post_cutoff(preds, reals)
check("trace" in loop and "best" in loop, "trace + best presentes")
check(len(loop["trace"]) >= 6, f"6+ strategies por default (got {len(loop['trace'])})")
check(loop["best"]["brier"] <= min(r["brier"] for r in loop["trace"]),
      "best tem menor brier")

print("\n[8] Bad strategy raises ValueError")
try:
    apply_strategy(0.5, "unknown")
    check(False, "raised ValueError")
except ValueError:
    check(True, "ValueError raised correctly")

print(f"\n{ok} ok, {fail} fail")
sys.exit(0 if fail == 0 else 1)
