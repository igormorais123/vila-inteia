"""
Onda 238: Factor models pra alpha real (vs base rate 0.50).

Implementa 3 estratégias clássicas de fator models:
  1. MOMENTUM: pred up se 5d return > 0 (Jegadeesh & Titman 1993)
  2. MEAN REVERSION: pred up se 5d return < 0 (DeBondt & Thaler 1985)
  3. RSI(14): pred up se RSI < 30 (oversold), down se > 70 (overbought)

Cada strategy usa price history via market_data.fetch_close_price.
Fallback to base rate (0.50) se data insuficiente.

Validação: backtest sobre 197 events resolved Q1 2026.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Callable

from engine.market_data import CRYPTO_YAHOO, fetch_close_price


def get_price_series(symbol: str, end_date: str, n_days: int = 14) -> list[float]:
    """Get last n_days closing prices ending at end_date.

    Returns lista (mais recente último). Pode ter < n_days se fail.
    """
    try:
        end = datetime.fromisoformat(end_date)
    except ValueError:
        return []
    prices = []
    for i in range(n_days, 0, -1):
        d = (end - timedelta(days=i)).strftime("%Y-%m-%d")
        p = fetch_close_price(symbol, d)
        if p is not None:
            prices.append(p)
    return prices


def momentum_predictor(symbol: str, date_iso: str, lookback_days: int = 5) -> float:
    """Pred prob up baseado em momentum (return positivo recente).

    Returns 0.55 se up momentum, 0.45 se down. Falha → 0.50.
    """
    series = get_price_series(symbol, date_iso, lookback_days + 2)
    if len(series) < 2:
        return 0.50
    ret = (series[-1] - series[0]) / series[0] if series[0] != 0 else 0
    if ret > 0.02:
        return 0.55
    if ret < -0.02:
        return 0.45
    return 0.50


def momentum_multi_window(symbol: str, date_iso: str,
                          windows: tuple = (3, 5, 10, 20)) -> float:
    """Onda 243: ensemble momentum over multiple lookback windows.

    Average de 4 momentum signals (3d, 5d, 10d, 20d). Reduz noise + captura
    diferentes timeframes (Asness 1994 — momentum across horizons).

    Returns prob ∈ [0.40, 0.60].
    """
    preds = []
    for w in windows:
        preds.append(momentum_predictor(symbol, date_iso, lookback_days=w))
    return sum(preds) / len(preds)


def momentum_strong(symbol: str, date_iso: str, lookback_days: int = 5,
                    threshold: float = 0.05) -> float:
    """Onda 243: stronger threshold momentum.

    Só sinal se return > 5% (vs 2% default). Mais conservativo,
    menos signal noise.
    """
    series = get_price_series(symbol, date_iso, lookback_days + 2)
    if len(series) < 2:
        return 0.50
    ret = (series[-1] - series[0]) / series[0] if series[0] != 0 else 0
    if ret > threshold:
        return 0.60
    if ret < -threshold:
        return 0.40
    return 0.50


def mean_reversion_predictor(symbol: str, date_iso: str, lookback_days: int = 5) -> float:
    """Pred prob up baseado em mean reversion (return NEGATIVO → bounce up).

    Returns 0.55 se oversold (recent down), 0.45 se overbought.
    """
    series = get_price_series(symbol, date_iso, lookback_days + 2)
    if len(series) < 2:
        return 0.50
    ret = (series[-1] - series[0]) / series[0] if series[0] != 0 else 0
    if ret < -0.05:  # heavily down → bounce
        return 0.55
    if ret > 0.05:  # heavily up → revert
        return 0.45
    return 0.50


def rsi(prices: list[float], period: int = 14) -> float | None:
    """Compute RSI(period) sobre prices."""
    if len(prices) < period + 1:
        return None
    gains = []
    losses = []
    for i in range(1, len(prices)):
        diff = prices[i] - prices[i - 1]
        if diff > 0:
            gains.append(diff)
            losses.append(0)
        else:
            gains.append(0)
            losses.append(-diff)
    avg_gain = sum(gains[-period:]) / period
    avg_loss = sum(losses[-period:]) / period
    if avg_loss == 0:
        return 100.0
    rs = avg_gain / avg_loss
    return 100.0 - (100.0 / (1.0 + rs))


def rsi_predictor(symbol: str, date_iso: str) -> float:
    """RSI(14) signal: oversold (<30) → up, overbought (>70) → down."""
    series = get_price_series(symbol, date_iso, n_days=20)
    r = rsi(series)
    if r is None:
        return 0.50
    if r < 30:
        return 0.60
    if r > 70:
        return 0.40
    return 0.50


def ensemble_predictor(symbol: str, date_iso: str) -> float:
    """Mean of 3 strategies + base rate."""
    p1 = momentum_predictor(symbol, date_iso)
    p2 = mean_reversion_predictor(symbol, date_iso)
    p3 = rsi_predictor(symbol, date_iso)
    return (p1 + p2 + p3 + 0.50) / 4


def _resolve_symbol(category: str, raw_symbol: str) -> str:
    """Map raw to Yahoo symbol."""
    if category.startswith("crypto"):
        return CRYPTO_YAHOO.get(raw_symbol.upper(), f"{raw_symbol.upper()}-USD")
    return raw_symbol


def evaluate_strategy_on_events(events: list, strategy: str) -> dict:
    """Aplica strategy em events resolvidos. Retorna metrics.

    strategy: 'baseline' | 'momentum' | 'mean_reversion' | 'rsi' | 'ensemble'
    """
    funcs: dict[str, Callable] = {
        "baseline": lambda s, d: 0.50,
        "momentum": momentum_predictor,
        "momentum_multi": momentum_multi_window,
        "momentum_strong": momentum_strong,
        "mean_reversion": mean_reversion_predictor,
        "rsi": rsi_predictor,
        "ensemble": ensemble_predictor,
    }
    fn = funcs.get(strategy)
    if fn is None:
        raise ValueError(f"unknown strategy: {strategy}")

    resolved = [e for e in events if e.real_outcome is not None]
    hits = 0
    brier_sum = 0.0
    for e in resolved:
        # Extract symbol
        parts = e.event_id.split("_")
        if len(parts) < 2:
            continue
        symbol = _resolve_symbol(e.category, parts[1])
        p = fn(symbol, e.date)
        if (p >= 0.5) == bool(e.real_outcome):
            hits += 1
        brier_sum += (p - e.real_outcome) ** 2
    return {
        "strategy": strategy, "n": len(resolved), "hits": hits,
        "acc": hits / len(resolved) if resolved else 0,
        "brier": brier_sum / len(resolved) if resolved else 0,
    }
