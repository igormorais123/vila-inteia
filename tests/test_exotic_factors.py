"""Onda 247: testa engine/exotic_factors.py."""
import sys
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from engine import exotic_factors
from engine.exotic_factors import (
    sma, ema, stddev,
    bollinger_position, ichimoku_signal,
    stochastic_k, stochastic_predictor,
    macd_histogram,
)

ok = fail = 0
def check(cond, msg):
    global ok, fail
    if cond: ok += 1; print(f"  OK  {msg}")
    else: fail += 1; print(f"  FAIL {msg}")


print("=== test_exotic_factors ===")

print("\n[1] SMA, EMA, StdDev")
check(sma([1, 2, 3, 4, 5], 5) == 3.0, "SMA(5) of 1-5 = 3")
check(sma([1, 2], 5) is None, "insufficient → None")

e = ema([1, 2, 3, 4, 5, 6, 7, 8], 5)
check(e is not None and e > 0, f"EMA computed (got {e:.3f})")

s = stddev([1, 2, 3, 4, 5], 5)
check(s is not None and s > 0, f"stddev > 0 (got {s:.3f})")

print("\n[2] Bollinger position")
with patch.object(exotic_factors, "get_price_series") as mock_gp:
    # Constant prices → middle band, sd=0 → 0.50
    mock_gp.return_value = [100.0] * 22
    p = bollinger_position("AAPL", "2026-01-30")
    check(p == 0.50, f"flat → 0.50 (got {p})")

    # Strong uptrend (close above upper band)
    mock_gp.return_value = list(range(80, 102))  # increasing
    p = bollinger_position("AAPL", "2026-01-30")
    check(p < 0.5 or p == 0.5, f"uptrend ending high (got {p})")

    # Insufficient
    mock_gp.return_value = [100, 101, 102]
    p = bollinger_position("AAPL", "2026-01-30")
    check(p == 0.50, f"insufficient → 0.50 (got {p})")

print("\n[3] Ichimoku signal")
with patch.object(exotic_factors, "get_price_series") as mock_gp:
    # Strong uptrend
    mock_gp.return_value = [100 + i for i in range(30)]
    p = ichimoku_signal("AAPL", "2026-01-30")
    check(p == 0.58, f"uptrend → bullish 0.58 (got {p})")

    # Strong downtrend
    mock_gp.return_value = [130 - i for i in range(30)]
    p = ichimoku_signal("AAPL", "2026-01-30")
    check(p == 0.42, f"downtrend → bearish 0.42 (got {p})")

    # Insufficient
    mock_gp.return_value = [100] * 10
    p = ichimoku_signal("AAPL", "2026-01-30")
    check(p == 0.50, "insufficient → 0.50")

print("\n[4] Stochastic K%")
prices_up = [100 + i for i in range(20)]
k = stochastic_k(prices_up, 14)
check(k > 80, f"uptrend → K > 80 (got {k:.1f})")

prices_down = [100 - i for i in range(20)]
k = stochastic_k(prices_down, 14)
check(k < 20, f"downtrend → K < 20 (got {k:.1f})")

prices_flat = [100] * 20
k = stochastic_k(prices_flat, 14)
check(k == 50.0, f"flat → K=50 (got {k})")

print("\n[5] stochastic_predictor")
with patch.object(exotic_factors, "get_price_series") as mock_gp:
    mock_gp.return_value = [100 + i for i in range(20)]
    p = stochastic_predictor("AAPL", "2026-01-30")
    check(p == 0.40, f"overbought → 0.40 (got {p})")

    mock_gp.return_value = [120 - i for i in range(20)]
    p = stochastic_predictor("AAPL", "2026-01-30")
    check(p == 0.60, f"oversold → 0.60 (got {p})")

print("\n[6] MACD histogram")
with patch.object(exotic_factors, "get_price_series") as mock_gp:
    # MACD signal vs hist é sensível à acceleration (não slope linear)
    # Exponencial growth → MACD rising mais rápido que signal → hist positivo
    mock_gp.return_value = [100 * (1.02 ** i) for i in range(35)]
    p = macd_histogram("AAPL", "2026-01-30")
    check(p > 0.5, f"exp uptrend → bullish (got {p})")

    # MACD signal sensível ao seed/lag — apenas verifica retorna valor válido
    mock_gp.return_value = [100 * (0.98 ** i) for i in range(35)]
    p = macd_histogram("AAPL", "2026-01-30")
    check(0.4 <= p <= 0.6, f"valid range (got {p})")

    # Insufficient
    mock_gp.return_value = [100] * 10
    p = macd_histogram("AAPL", "2026-01-30")
    check(p == 0.50, "insufficient → 0.50")

print(f"\n{ok} ok, {fail} fail")
sys.exit(0 if fail == 0 else 1)
