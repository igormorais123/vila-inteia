"""Test engine/time_decay.py — exponential time-decay shrinkage."""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from engine.time_decay import (
    apply_time_decay,
    event_age_days,
    time_decay_weight,
)
from engine.post_cutoff_classifier import classify_and_predict


ok = fail = 0


def check(cond, msg):
    global ok, fail
    if cond:
        ok += 1
        print(f"  OK  {msg}")
    else:
        fail += 1
        print(f"  FAIL {msg}")


print("=== test_time_decay ===")

print("\n[1] event_age_days basic arithmetic")
ref = "2026-04-28"
check(event_age_days("2026-04-28", ref) == 0, "same date age=0")
check(event_age_days("2026-04-21", ref) == 7, "7 days back")
check(event_age_days("2026-05-05", ref) == 7, "7 days forward (abs)")
check(event_age_days("2025-04-28", ref) == 365, "1 year back == 365")
# Default reference defaults to 2026-04-28.
check(event_age_days("2026-04-28") == 0, "default ref is 2026-04-28")
# Future event 6 months ahead.
check(event_age_days("2026-10-25", ref) == 180, "180 days forward")

print("\n[2] time_decay_weight curve properties")
w0 = time_decay_weight(0)
check(abs(w0 - 1.0) < 1e-9, f"age=0 -> 1.0 (got {w0})")
w_half = time_decay_weight(180, half_life=180)
check(abs(w_half - 0.5) < 1e-9, f"age=half_life -> 0.5 (got {w_half})")
w_double = time_decay_weight(360, half_life=180)
check(abs(w_double - 0.25) < 1e-9, f"age=2*half -> 0.25 (got {w_double})")
# Strictly in (0, 1] for any non-negative age.
for age in (0, 1, 7, 30, 90, 365, 1000, 5000):
    w = time_decay_weight(age)
    check(0.0 < w <= 1.0, f"age={age} weight in (0,1] (={w:.4f})")
# Negative age treated as |age|.
check(time_decay_weight(-180, half_life=180) == time_decay_weight(180, half_life=180),
      "negative age symmetric")
# Half-life monotonicity: longer half_life -> larger weight at fixed age.
check(time_decay_weight(180, half_life=360) > time_decay_weight(180, half_life=180),
      "longer half_life shrinks slower")
# Invalid half_life raises.
raised = False
try:
    time_decay_weight(10, half_life=0)
except ValueError:
    raised = True
check(raised, "half_life=0 raises ValueError")

print("\n[3] apply_time_decay shrinks toward prior")
# Fresh: w=1, output equals p.
out = apply_time_decay(0.9, 0, prior=0.5)
check(abs(out - 0.9) < 1e-9, f"age=0 keeps p=0.9 (got {out})")
# At half-life: midpoint between p and prior.
out = apply_time_decay(0.9, 180, prior=0.5, half_life=180)
check(abs(out - 0.7) < 1e-9, f"age=half_life midpoint=0.7 (got {out})")
# Distant: ~prior.
out = apply_time_decay(0.9, 10_000, prior=0.5)
check(abs(out - 0.5) < 1e-3, f"age huge collapses to prior (got {out})")
# Output always in [0,1].
for p, age in [(0.0, 0), (1.0, 0), (0.99, 720), (0.01, 720), (0.5, 100)]:
    o = apply_time_decay(p, age, prior=0.5)
    check(0.0 <= o <= 1.0, f"p={p} age={age} in [0,1] (={o:.4f})")
# When p == prior, no change regardless of age.
out = apply_time_decay(0.5, 9999, prior=0.5)
check(abs(out - 0.5) < 1e-9, f"p=prior unchanged (got {out})")
# Distant events shrink MORE than near events (toward prior=0.5).
near = apply_time_decay(0.95, 30, prior=0.5)
far = apply_time_decay(0.95, 365, prior=0.5)
check(far < near, f"distant shrinks more (near={near:.3f} far={far:.3f})")

print("\n[4] Custom half_life and prior")
out = apply_time_decay(0.9, 90, prior=0.5, half_life=90)
check(abs(out - 0.7) < 1e-9, f"half_life=90 (got {out})")
out = apply_time_decay(0.9, 0, prior=0.3)
check(abs(out - 0.9) < 1e-9, f"prior ignored when age=0 (got {out})")
# Decayed value is exactly prior at age=infinity (numerical proxy).
out = apply_time_decay(0.9, 100_000, prior=0.3)
check(abs(out - 0.3) < 1e-3, f"converges to prior=0.3 (got {out})")

print("\n[5] classify_and_predict integration with time-decay flag")
# Fresh event (age 0): apply_time_decay True/False match.
p_no, _ = classify_and_predict("Olympics 2026 held", "summit",
                               apply_time_decay=False)
p_yes, _ = classify_and_predict("Olympics 2026 held", "summit",
                                apply_time_decay=True,
                                event_date="2026-04-28")
check(abs(p_no - p_yes) < 1e-9,
      f"age=0 same (no={p_no:.4f} yes={p_yes:.4f})")
# Distant future event shrinks toward 0.5.
p_far, _ = classify_and_predict("Olympics 2026 held", "summit",
                                apply_time_decay=True,
                                event_date="2030-04-28",
                                half_life=180)
check(p_far < p_no,
      f"distant shrinks (no={p_no:.3f} far={p_far:.3f})")
check(abs(p_far - 0.5) < 0.05,
      f"very distant ~0.5 (got {p_far:.4f})")
# event_date None -> no decay applied even if flag True.
p_none, _ = classify_and_predict("Olympics 2026 held", "summit",
                                 apply_time_decay=True, event_date=None)
check(abs(p_none - p_no) < 1e-9,
      f"None event_date is no-op (got {p_none})")
# Custom decay_prior.
p_low, _ = classify_and_predict("Olympics 2026 held", "summit",
                                apply_time_decay=True,
                                event_date="2030-04-28",
                                half_life=180,
                                decay_prior=0.0)
check(p_low < p_far,
      f"prior=0 shrinks lower (default={p_far:.3f} prior0={p_low:.3f})")

print(f"\n{ok} ok, {fail} fail")
sys.exit(0 if fail == 0 else 1)
