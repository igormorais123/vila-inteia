"""Onda 234: testa engine/market_data.py — yfinance + HTTP fallback + cache."""
import sys
import json
import tempfile
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from engine import market_data
from engine.market_data import (
    CRYPTO_YAHOO, fetch_close_price, resolve_stock_event,
    resolve_crypto_event, resolve_micro_events_market,
)
from engine.micro_events import MicroEvent

ok = fail = 0
def check(cond, msg):
    global ok, fail
    if cond: ok += 1; print(f"  OK  {msg}")
    else: fail += 1; print(f"  FAIL {msg}")


print("=== test_market_data ===")

print("\n[1] CRYPTO_YAHOO mapping correto")
check(CRYPTO_YAHOO["BTC"] == "BTC-USD", "BTC mapeado")
check(CRYPTO_YAHOO["ETH"] == "ETH-USD", "ETH mapeado")
check(CRYPTO_YAHOO["TRUMP"] == "TRUMP-USD", "TRUMP mapeado")
check(len(CRYPTO_YAHOO) >= 20, f"20+ cryptos (got {len(CRYPTO_YAHOO)})")

print("\n[2] fetch_close_price com cache temp")
with tempfile.TemporaryDirectory() as tmp:
    cache_path = Path(tmp) / "cache.json"
    cache_path.write_text(json.dumps({"AAPL:2026-01-30": 250.5}))
    with patch.object(market_data, "CACHE_PATH", cache_path):
        # Cached hit — não deve fazer HTTP
        with patch.object(market_data, "_yahoo_finance_http") as mock_http:
            with patch.object(market_data, "_try_yfinance") as mock_yf:
                price = fetch_close_price("AAPL", "2026-01-30")
                check(price == 250.5, f"cached hit (got {price})")
                check(not mock_http.called, "HTTP não chamado em cache hit")

print("\n[3] resolve_stock_event com prices mockados")
with patch.object(market_data, "fetch_close_price") as mock_fetch:
    # close hoje > close prior → 1 (up)
    mock_fetch.side_effect = [105.0, 100.0]
    out = resolve_stock_event("AAPL", "2026-01-30")
    check(out == 1, f"close 105 > prior 100 → up=1 (got {out})")

with patch.object(market_data, "fetch_close_price") as mock_fetch:
    mock_fetch.side_effect = [95.0, 100.0]
    out = resolve_stock_event("AAPL", "2026-01-30")
    check(out == 0, f"close 95 < prior 100 → down=0 (got {out})")

with patch.object(market_data, "fetch_close_price") as mock_fetch:
    mock_fetch.return_value = None
    out = resolve_stock_event("INVALID", "2026-01-30")
    check(out is None, "fetch fail → None")

print("\n[4] resolve_crypto_event usa CRYPTO_YAHOO mapping")
with patch.object(market_data, "fetch_close_price") as mock_fetch:
    mock_fetch.side_effect = [120000, 100000]  # BTC up
    out = resolve_crypto_event("BTC", "2026-01-15")
    check(out == 1, "BTC up resolved")
    # Verifica que foi chamado com BTC-USD
    args = mock_fetch.call_args_list[0][0]
    check(args[0] == "BTC-USD", f"chamou com BTC-USD (got {args[0]})")

print("\n[5] resolve_micro_events_market preenche real_outcome inplace")
events = [
    MicroEvent(event_id="stk_AAPL_20260130", category="stock_price_up",
               framing="?", date="2026-01-30"),
    MicroEvent(event_id="stk_MSFT_20260130", category="stock_price_down",
               framing="?", date="2026-01-30"),
    MicroEvent(event_id="sport_001", category="sports_favorite_wins",
               framing="?", date="2026-01-15"),
    MicroEvent(event_id="stk_AAPL_20260130", category="stock_price_up",
               framing="?", date="2026-01-30", real_outcome=1),  # já resolved
]
with patch.object(market_data, "resolve_stock_event") as mock_res:
    mock_res.side_effect = [1, 0]  # AAPL up, MSFT up (mas category=down → invert → 0)
    summary = resolve_micro_events_market(events)
    check(summary["n_resolved"] == 2, f"2 resolved (got {summary['n_resolved']})")
    check(summary["n_skipped"] == 2, f"2 skipped (sport + already resolved) (got {summary['n_skipped']})")
    check(events[0].real_outcome == 1, "AAPL up = 1")
    check(events[1].real_outcome == 1, f"MSFT down inverted: 0 (raw up) → 1 (down=NOT up) (got {events[1].real_outcome})")

print(f"\n{ok} ok, {fail} fail")
sys.exit(0 if fail == 0 else 1)
