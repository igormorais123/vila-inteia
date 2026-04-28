"""Onda 245: testa engine/advanced_factors.py."""
import sys
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from engine import advanced_factors
from engine.advanced_factors import (
    hurst_exponent, hurst_regime_predictor,
    realized_volatility, vol_adj_momentum,
    kelly_fraction, kelly_calibrated_predictor,
    bayes_update, signal_to_lr, bayesian_multi_signal_predictor,
)

ok = fail = 0
def check(cond, msg):
    global ok, fail
    if cond: ok += 1; print(f"  OK  {msg}")
    else: fail += 1; print(f"  FAIL {msg}")


print("=== test_advanced_factors ===")

print("\n[1] Hurst exponent")
# Trending series (cumulative random walk with drift)
trending = [100 + i for i in range(30)]
h = hurst_exponent(trending)
check(h is not None and h > 0.5, f"linear trend H>0.5 (got {h})")

# Insufficient data
check(hurst_exponent([100, 101, 102]) is None, "insufficient → None")

# Random walk approximate
import random
rng = random.Random(42)
walk = [100]
for _ in range(50):
    walk.append(walk[-1] * (1 + rng.gauss(0, 0.01)))
h_rw = hurst_exponent(walk)
check(h_rw is not None and 0.2 < h_rw < 0.8, f"random walk H ~ 0.5 (got {h_rw:.3f})")

print("\n[2] hurst_regime_predictor")
with patch.object(advanced_factors, "get_price_series") as mock_gp:
    mock_gp.return_value = []
    p = hurst_regime_predictor("AAPL", "2026-01-30")
    check(p == 0.50, f"no data → 0.50 (got {p})")

print("\n[3] realized_volatility")
flat = [100] * 20
vol = realized_volatility(flat)
check(vol == 0.0, f"flat → 0 vol (got {vol})")

vol_series = [100, 105, 95, 102, 98]
v = realized_volatility(vol_series)
check(v > 0, f"volatile → vol > 0 (got {v:.4f})")

print("\n[4] vol_adj_momentum")
with patch.object(advanced_factors, "get_price_series") as mock_gp:
    # Strong up trend, low vol
    mock_gp.return_value = [100 + i*0.5 for i in range(22)]
    p = vol_adj_momentum("AAPL", "2026-01-30")
    check(p > 0.5, f"strong up momentum → p > 0.5 (got {p})")

print("\n[5] kelly_fraction")
# 60/40 even-money: f = 2p - 1 = 0.2
f = kelly_fraction(0.6, 1.0)
check(abs(f - 0.2) < 1e-9, f"p=0.6 → f=0.2 (got {f})")

# 50/50: f=0
f = kelly_fraction(0.5, 1.0)
check(f == 0.0, f"p=0.5 → f=0 (got {f})")

# Negative edge: f=0
f = kelly_fraction(0.3, 1.0)
check(f == 0.0, f"p=0.3 → f=0 (got {f})")

print("\n[6] kelly_calibrated_predictor")
# High prob: shrink toward 0.5 by Kelly fraction
p = kelly_calibrated_predictor(0.7)
check(0.5 < p < 0.7, f"0.7 shrunk by Kelly (got {p:.3f})")

p = kelly_calibrated_predictor(0.5)
check(p == 0.5, f"0.5 stays 0.5 (got {p})")

print("\n[7] bayes_update")
# Prior 0.5, LR=2 → posterior 2/3
p = bayes_update(0.5, 2.0)
check(abs(p - 2/3) < 1e-9, f"0.5 * LR=2 → 2/3 (got {p})")

# Prior 0.5, LR=1 → 0.5
p = bayes_update(0.5, 1.0)
check(p == 0.5, f"LR=1 → unchanged (got {p})")

# Edge cases
check(bayes_update(0, 2) == 0, "prior=0 → 0")
check(bayes_update(1, 2) == 1, "prior=1 → 1")

print("\n[8] signal_to_lr")
check(signal_to_lr(0.6, 0.5) > 1, "signal > base → LR > 1")
check(signal_to_lr(0.4, 0.5) < 1, "signal < base → LR < 1")

print("\n[9] bayesian_multi_signal_predictor")
with patch.object(advanced_factors, "momentum_predictor", return_value=0.55), \
     patch.object(advanced_factors, "vol_adj_momentum", return_value=0.55), \
     patch.object(advanced_factors, "hurst_regime_predictor", return_value=0.55):
    p = bayesian_multi_signal_predictor("AAPL", "2026-01-30")
    # 3 LRs each = 0.55/0.5 = 1.1 → posterior odds = 1 * 1.1^3 = 1.33 → p ≈ 0.57
    check(p > 0.55, f"all signals up → posterior > 0.55 (got {p:.3f})")

print(f"\n{ok} ok, {fail} fail")
sys.exit(0 if fail == 0 else 1)
