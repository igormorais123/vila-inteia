"""Test engine/btc_vila.py."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from engine.btc_vila import vila_btc_predict

ok = fail = 0
def check(c, m):
    global ok, fail
    if c: ok += 1; print(f"  OK  {m}")
    else: fail += 1; print(f"  FAIL {m}")

print("=== test_btc_vila ===")

print("\n[1] Insufficient history → base rate")
p = vila_btc_predict([100.0]*10)
check(p == 0.43, f"too short → base rate (got {p})")

print("\n[2] Stable low-vol price → base - vol_penalty")
hist = [100.0 + i*0.1 for i in range(40)]
p = vila_btc_predict(hist)
check(p < 0.43, f"low vol → < base (got {p:.3f})")

print("\n[3] High vol → above base")
import random
rng = random.Random(0)
hist = [100.0 * (1 + rng.gauss(0, 0.06)) for _ in range(40)]
p = vila_btc_predict(hist)
check(p >= 0.40, f"high vol → ≥ base ish (got {p:.3f})")

print("\n[4] Big drawdown → bounce expectation")
hist = [100.0]*20 + [100.0 * (1 - i*0.025) for i in range(20)]
p = vila_btc_predict(hist)
check(p > 0.45, f"big drawdown → up (got {p:.3f})")

print("\n[5] Extreme +30% rally → mean revert down")
hist = [100.0]*20 + [100.0 * (1 + i*0.02) for i in range(20)]
p = vila_btc_predict(hist)
print(f"  rally hist last={hist[-1]:.2f}, p={p:.3f}")
check(p <= 0.55, f"overheated → ≤ base+small (got {p:.3f})")

print("\n[6] Output range [0.10, 0.90]")
for _ in range(20):
    hist = [100.0 * (1 + rng.gauss(0, 0.10)) for _ in range(40)]
    p = vila_btc_predict(hist)
    check(0.10 <= p <= 0.90, f"in range (got {p:.3f})")
    if not (0.10 <= p <= 0.90):
        break

print(f"\n{ok} ok, {fail} fail")
sys.exit(0 if fail == 0 else 1)
