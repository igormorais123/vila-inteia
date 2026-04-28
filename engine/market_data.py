"""
Onda 234: Market data resolver — yfinance integration pra resolver
real_outcome de stock/crypto micro events automaticamente.

Strategy:
  1. Try yfinance (pip install yfinance)
  2. Fallback: Yahoo Finance HTTP query direto (urllib, no deps)
  3. Cache results em data/market_cache.json

Resolve micro_events com category in {stock_price_up, stock_price_down,
crypto_price_up, crypto_price_down} preenchendo real_outcome.

Fail gracefully — se sem internet/yfinance, retorna events com
real_outcome=None (não-resolved).
"""

from __future__ import annotations

import json
import logging
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# Cache path
CACHE_PATH = Path(__file__).resolve().parent.parent / "data" / "market_cache.json"

# Crypto symbol mapping (Yahoo Finance format)
CRYPTO_YAHOO = {
    "BTC": "BTC-USD", "ETH": "ETH-USD", "SOL": "SOL-USD", "BNB": "BNB-USD",
    "XRP": "XRP-USD", "ADA": "ADA-USD", "DOGE": "DOGE-USD", "AVAX": "AVAX-USD",
    "MATIC": "MATIC-USD", "DOT": "DOT-USD", "LTC": "LTC-USD", "BCH": "BCH-USD",
    "LINK": "LINK-USD", "ATOM": "ATOM-USD", "UNI": "UNI7083-USD",
    "ICP": "ICP-USD", "FIL": "FIL-USD", "NEAR": "NEAR-USD", "APT": "APT-USD",
    "TRUMP": "TRUMP-USD",
}


def _load_cache() -> dict:
    if CACHE_PATH.exists():
        try:
            return json.loads(CACHE_PATH.read_text())
        except Exception:
            return {}
    return {}


def _save_cache(cache: dict) -> None:
    CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    CACHE_PATH.write_text(json.dumps(cache, indent=2))


def _yahoo_finance_http(symbol: str, date_iso: str) -> float | None:
    """Fetch close price for symbol on date via Yahoo Finance HTTP API.

    Returns close price or None se erro.
    """
    import time
    from datetime import datetime, timedelta

    try:
        dt = datetime.fromisoformat(date_iso)
    except ValueError:
        return None
    # Range: que dia +- 5 dias pra cobrir weekend/holidays
    period1 = int((dt - timedelta(days=5)).timestamp())
    period2 = int((dt + timedelta(days=5)).timestamp())

    url = (
        f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
        f"?period1={period1}&period2={period2}&interval=1d"
    )
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
    except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, OSError) as e:
        logger.debug(f"Yahoo HTTP fail {symbol} {date_iso}: {e}")
        return None

    try:
        result = data["chart"]["result"][0]
        timestamps = result["timestamp"]
        closes = result["indicators"]["quote"][0]["close"]
    except (KeyError, IndexError, TypeError):
        return None

    # Find closest timestamp to target date
    target = dt.timestamp()
    best_idx = None
    best_diff = float("inf")
    for i, ts in enumerate(timestamps):
        d = abs(ts - target)
        if d < best_diff and closes[i] is not None:
            best_diff = d
            best_idx = i
    if best_idx is None:
        return None
    return float(closes[best_idx])


def _try_yfinance(symbol: str, date_iso: str) -> float | None:
    """Try yfinance lib first."""
    try:
        import yfinance as yf
    except ImportError:
        return None
    try:
        from datetime import datetime, timedelta
        dt = datetime.fromisoformat(date_iso)
        start = (dt - timedelta(days=5)).strftime("%Y-%m-%d")
        end = (dt + timedelta(days=5)).strftime("%Y-%m-%d")
        ticker = yf.Ticker(symbol)
        hist = ticker.history(start=start, end=end)
        if hist.empty:
            return None
        # Find closest
        target = dt.date()
        for idx, row in hist.iterrows():
            if idx.date() <= target:
                last_close = float(row["Close"])
        return last_close if "last_close" in dir() else None
    except Exception as e:
        logger.debug(f"yfinance fail {symbol}: {e}")
        return None


def fetch_close_price(symbol: str, date_iso: str, use_cache: bool = True) -> float | None:
    """Fetch close price para symbol on date.

    Tries yfinance first, then HTTP. Cached.
    """
    cache = _load_cache() if use_cache else {}
    key = f"{symbol}:{date_iso}"
    if key in cache:
        return cache[key]

    price = _try_yfinance(symbol, date_iso)
    if price is None:
        price = _yahoo_finance_http(symbol, date_iso)

    if price is not None and use_cache:
        cache[key] = price
        _save_cache(cache)
    return price


def resolve_stock_event(symbol: str, date_iso: str) -> int | None:
    """Resolve stock_price_up event: 1 se close > open, else 0.

    Returns None se erro fetch.
    """
    # Get close on target date AND prior day
    from datetime import datetime, timedelta
    try:
        dt = datetime.fromisoformat(date_iso)
    except ValueError:
        return None
    prior = (dt - timedelta(days=7)).strftime("%Y-%m-%d")

    p_today = fetch_close_price(symbol, date_iso)
    p_prior = fetch_close_price(symbol, prior)
    if p_today is None or p_prior is None:
        return None
    return 1 if p_today > p_prior else 0


def resolve_crypto_event(coin: str, date_iso: str) -> int | None:
    """Resolve crypto_price_up: same logic with Yahoo crypto symbols."""
    symbol = CRYPTO_YAHOO.get(coin.upper(), f"{coin.upper()}-USD")
    return resolve_stock_event(symbol, date_iso)


def resolve_micro_events_market(events: list[Any]) -> dict:
    """Resolve all market-related events (stocks/criptos) preenchendo
    real_outcome inplace.

    events: list of MicroEvent objects.
    Returns: {n_resolved, n_failed, n_skipped, errors}.
    """
    n_resolved = 0
    n_failed = 0
    n_skipped = 0
    errors = []

    for e in events:
        cat = getattr(e, "category", "")
        if cat not in ("stock_price_up", "stock_price_down", "crypto_price_up", "crypto_price_down"):
            n_skipped += 1
            continue
        if e.real_outcome is not None:
            n_skipped += 1
            continue

        # Extract symbol and date from event_id
        eid = e.event_id
        # stk_AAPL_20260130 or crypto_BTC_20260115
        parts = eid.split("_")
        if len(parts) < 3:
            n_failed += 1
            continue
        symbol_raw = parts[1]
        # Use event date directly
        date_iso = getattr(e, "date", None)
        if date_iso is None:
            n_failed += 1
            continue

        try:
            if cat.startswith("stock"):
                outcome = resolve_stock_event(symbol_raw, date_iso)
            else:
                outcome = resolve_crypto_event(symbol_raw, date_iso)
        except Exception as ex:
            errors.append(f"{eid}: {ex}")
            n_failed += 1
            continue

        if outcome is None:
            n_failed += 1
        else:
            # If category is *_down, invert
            if cat.endswith("_down"):
                outcome = 1 - outcome
            e.real_outcome = outcome
            n_resolved += 1

    return {"n_resolved": n_resolved, "n_failed": n_failed,
            "n_skipped": n_skipped, "errors": errors}
