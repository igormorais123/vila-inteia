"""
Onda 247: Fórmulas exóticas pra forecasting honest.

Técnicas raramente usadas em retail prediction markets:

1. BOLLINGER BAND POSITION (Bollinger 1980s)
   - Z-score do preço relativo a SMA(20) ± 2σ
   - Mean reversion sinal nas bordas

2. ICHIMOKU KINKO HYO (Hosoda 1969)
   - Cloud trend confirmation
   - 5 lines pra regime + signal multi-timeframe

3. STOCHASTIC OSCILLATOR K%D (Lane 1950s)
   - %K = (close - low_n) / (high_n - low_n)
   - Crossover momentum signal

4. MACD HISTOGRAM DIVERGENCE (Appel 1979)
   - EMA12 - EMA26 vs signal EMA9
   - Histogram momentum + divergence detection

Refs:
- Bollinger 2002 "Bollinger on Bollinger Bands"
- Hosoda 1969 (originally Sanjin Ichimoku)
- Lane 1984 "Lane's Stochastics" Technical Analysis Stocks Commodities
- Appel 2005 "Technical Analysis: Power Tools for Active Investors"
"""

from __future__ import annotations

import math

from engine.factor_models import get_price_series


def sma(prices: list[float], period: int) -> float | None:
    """Simple moving average."""
    if len(prices) < period:
        return None
    return sum(prices[-period:]) / period


def ema(prices: list[float], period: int) -> float | None:
    """Exponential moving average."""
    if len(prices) < period:
        return None
    k = 2 / (period + 1)
    e = sum(prices[:period]) / period  # SMA seed
    for p in prices[period:]:
        e = p * k + e * (1 - k)
    return e


def stddev(prices: list[float], period: int) -> float | None:
    """Standard deviation over period."""
    if len(prices) < period:
        return None
    window = prices[-period:]
    mean = sum(window) / period
    var = sum((p - mean) ** 2 for p in window) / period
    return math.sqrt(var)


# ============================================================================
# 1. BOLLINGER BAND POSITION
# ============================================================================
def bollinger_position(symbol: str, date_iso: str, period: int = 20, k: float = 2.0) -> float:
    """%B = (close - lower_band) / (upper_band - lower_band).

    %B > 1: above upper band (overbought) → predict down (0.40)
    %B < 0: below lower band (oversold) → predict up (0.60)
    Else: 0.50
    """
    series = get_price_series(symbol, date_iso, n_days=period + 2)
    if len(series) < period:
        return 0.50

    middle = sma(series, period)
    sd = stddev(series, period)
    if middle is None or sd is None or sd == 0:
        return 0.50

    upper = middle + k * sd
    lower = middle - k * sd
    close = series[-1]

    if upper == lower:
        return 0.50
    pct_b = (close - lower) / (upper - lower)
    if pct_b > 1.0:
        return 0.40  # overbought, expect mean revert
    if pct_b < 0.0:
        return 0.60  # oversold, expect bounce
    if pct_b > 0.8:
        return 0.45
    if pct_b < 0.2:
        return 0.55
    return 0.50


# ============================================================================
# 2. ICHIMOKU CLOUD signal
# ============================================================================
def ichimoku_signal(symbol: str, date_iso: str) -> float:
    """Tenkan-sen + Kijun-sen cross signal.

    Tenkan = (9-period high + low) / 2
    Kijun = (26-period high + low) / 2

    Tenkan > Kijun + close > both: bullish (0.58)
    Tenkan < Kijun + close < both: bearish (0.42)
    """
    series = get_price_series(symbol, date_iso, n_days=30)
    if len(series) < 26:
        return 0.50

    # Tenkan (9 period)
    win9 = series[-9:]
    tenkan = (max(win9) + min(win9)) / 2

    # Kijun (26 period)
    win26 = series[-26:]
    kijun = (max(win26) + min(win26)) / 2

    close = series[-1]

    if tenkan > kijun and close > tenkan and close > kijun:
        return 0.58
    if tenkan < kijun and close < tenkan and close < kijun:
        return 0.42
    return 0.50


# ============================================================================
# 3. STOCHASTIC K%D
# ============================================================================
def stochastic_k(prices: list[float], period: int = 14) -> float | None:
    """%K = (close - low_n) / (high_n - low_n) * 100."""
    if len(prices) < period:
        return None
    window = prices[-period:]
    high = max(window)
    low = min(window)
    if high == low:
        return 50.0
    return (prices[-1] - low) / (high - low) * 100


def stochastic_predictor(symbol: str, date_iso: str) -> float:
    """%K based signal.

    %K > 80: overbought → 0.40
    %K < 20: oversold → 0.60
    Crossover momentum 50: trend signal
    """
    series = get_price_series(symbol, date_iso, n_days=20)
    k = stochastic_k(series)
    if k is None:
        return 0.50
    if k > 80:
        return 0.40
    if k < 20:
        return 0.60
    if k > 60:
        return 0.45
    if k < 40:
        return 0.55
    return 0.50


# ============================================================================
# 4. MACD histogram
# ============================================================================
def macd_histogram(symbol: str, date_iso: str) -> float:
    """MACD = EMA(12) - EMA(26). Signal = EMA(9) of MACD.
    Histogram = MACD - Signal.

    Histogram > 0 + crescendo: bullish (0.58)
    Histogram < 0 + decrescendo: bearish (0.42)
    """
    series = get_price_series(symbol, date_iso, n_days=35)
    if len(series) < 30:
        return 0.50

    e12 = ema(series, 12)
    e26 = ema(series, 26)
    if e12 is None or e26 is None:
        return 0.50
    macd_now = e12 - e26

    # Compute MACD series for signal (last few values)
    macd_series = []
    for i in range(20, len(series) + 1):
        sub = series[:i]
        e12_i = ema(sub, 12)
        e26_i = ema(sub, 26)
        if e12_i is None or e26_i is None:
            continue
        macd_series.append(e12_i - e26_i)

    if len(macd_series) < 9:
        return 0.50
    signal = ema(macd_series, 9)
    if signal is None:
        return 0.50

    hist = macd_now - signal
    if hist > 0:
        # Trend strength
        if len(macd_series) >= 2 and macd_series[-1] > macd_series[-2]:
            return 0.58
        return 0.53
    if hist < 0:
        if len(macd_series) >= 2 and macd_series[-1] < macd_series[-2]:
            return 0.42
        return 0.47
    return 0.50


EXOTIC_STRATEGIES = {
    "bollinger": bollinger_position,
    "ichimoku": ichimoku_signal,
    "stochastic": stochastic_predictor,
    "macd": macd_histogram,
}
