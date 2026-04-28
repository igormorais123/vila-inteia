"""Onda 238: testa engine/factor_models.py."""
import sys
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from engine import factor_models
from engine.factor_models import (
    momentum_predictor, mean_reversion_predictor, rsi_predictor,
    rsi, ensemble_predictor, evaluate_strategy_on_events, _resolve_symbol,
)
from engine.micro_events import MicroEvent

ok = fail = 0
def check(cond, msg):
    global ok, fail
    if cond: ok += 1; print(f"  OK  {msg}")
    else: fail += 1; print(f"  FAIL {msg}")


print("=== test_factor_models ===")

print("\n[1] momentum_predictor: up momentum → 0.55, down → 0.45")
with patch.object(factor_models, "get_price_series") as mock_gp:
    # Up momentum (5% gain)
    mock_gp.return_value = [100.0, 105.0]
    p = momentum_predictor("AAPL", "2026-01-30")
    check(p == 0.55, f"up momentum → 0.55 (got {p})")

    # Down momentum (5% loss)
    mock_gp.return_value = [100.0, 95.0]
    p = momentum_predictor("AAPL", "2026-01-30")
    check(p == 0.45, f"down momentum → 0.45 (got {p})")

    # Flat (within 2% threshold)
    mock_gp.return_value = [100.0, 101.0]
    p = momentum_predictor("AAPL", "2026-01-30")
    check(p == 0.50, f"flat → 0.50 (got {p})")

    # Insufficient data
    mock_gp.return_value = []
    p = momentum_predictor("AAPL", "2026-01-30")
    check(p == 0.50, f"no data → 0.50 (got {p})")

print("\n[2] mean_reversion_predictor: down → bounce up (0.55)")
with patch.object(factor_models, "get_price_series") as mock_gp:
    mock_gp.return_value = [100.0, 90.0]  # 10% down
    p = mean_reversion_predictor("AAPL", "2026-01-30")
    check(p == 0.55, f"oversold → bounce 0.55 (got {p})")

    mock_gp.return_value = [100.0, 110.0]  # 10% up
    p = mean_reversion_predictor("AAPL", "2026-01-30")
    check(p == 0.45, f"overbought → revert 0.45 (got {p})")

print("\n[3] RSI computation")
# Constant prices → RSI = 100 (no losses)
prices_flat = [100] * 20
r = rsi(prices_flat, 14)
check(r == 100.0, f"flat prices RSI=100 (got {r})")

# Strict downtrend → RSI = 0
prices_down = [100 - i for i in range(20)]
r = rsi(prices_down, 14)
check(r == 0.0, f"all down RSI=0 (got {r})")

# Insufficient data
r = rsi([100, 101], 14)
check(r is None, f"insufficient → None (got {r})")

print("\n[4] rsi_predictor signal")
with patch.object(factor_models, "get_price_series") as mock_gp:
    # Oversold (RSI < 30) — strong downtrend
    mock_gp.return_value = [100 - i*2 for i in range(20)]
    p = rsi_predictor("AAPL", "2026-01-30")
    check(p == 0.60, f"oversold → 0.60 (got {p})")

    # Overbought (RSI > 70) — strong uptrend
    mock_gp.return_value = [100 + i*2 for i in range(20)]
    p = rsi_predictor("AAPL", "2026-01-30")
    check(p == 0.40, f"overbought → 0.40 (got {p})")

print("\n[5] ensemble combina 3 strategies + base rate")
with patch.object(factor_models, "momentum_predictor", return_value=0.55), \
     patch.object(factor_models, "mean_reversion_predictor", return_value=0.55), \
     patch.object(factor_models, "rsi_predictor", return_value=0.60):
    e = ensemble_predictor("AAPL", "2026-01-30")
    expected = (0.55 + 0.55 + 0.60 + 0.50) / 4
    check(abs(e - expected) < 1e-9, f"ensemble = mean (got {e:.4f}, expected {expected:.4f})")

print("\n[6] _resolve_symbol mapping")
check(_resolve_symbol("crypto_price_up", "BTC") == "BTC-USD", "crypto BTC → BTC-USD")
check(_resolve_symbol("stock_price_up", "AAPL") == "AAPL", "stock AAPL → AAPL")

print("\n[7] evaluate_strategy_on_events end-to-end")
events = [
    MicroEvent(event_id="stk_AAPL_20260130", category="stock_price_up",
               framing="?", date="2026-01-30", real_outcome=1),
    MicroEvent(event_id="stk_MSFT_20260130", category="stock_price_up",
               framing="?", date="2026-01-30", real_outcome=0),
]
with patch.object(factor_models, "get_price_series") as mock_gp:
    mock_gp.side_effect = [[100, 105], [100, 95]]  # AAPL up, MSFT down
    res = evaluate_strategy_on_events(events, "momentum")
    # AAPL: pred 0.55 → cls 1, real 1, hit
    # MSFT: pred 0.45 → cls 0, real 0, hit
    check(res["hits"] == 2, f"momentum 2 hits (got {res['hits']})")
    check(res["acc"] == 1.0, "100% acc")

print("\n[8] Bad strategy raises")
try:
    evaluate_strategy_on_events([], "unknown")
    check(False, "should raise")
except ValueError:
    check(True, "ValueError raised")

print(f"\n{ok} ok, {fail} fail")
sys.exit(0 if fail == 0 else 1)
