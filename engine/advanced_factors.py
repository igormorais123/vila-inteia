"""
Onda 245: Fórmulas avançadas pouco aplicadas em retail forecasting.

Implementa 4 técnicas de academic finance/physics raramente usadas
em prediction markets:

1. HURST EXPONENT (Mandelbrot 1971, Hurst 1951)
   - Detecta regime: H>0.5 trending, H=0.5 random walk, H<0.5 mean-reverting
   - Aplicação: switch entre momentum (H>0.6) e mean rev (H<0.4)

2. VOLATILITY-ADJUSTED MOMENTUM (Moskowitz et al 2012 "Time series momentum")
   - Risk-normalize: signal = return / volatility (Sharpe-like)
   - Mais robusto que momentum raw — penaliza moves de alta vol noise

3. KELLY FRACTIONAL (Kelly 1956)
   - Optimal bet sizing dado edge + odds
   - Aplicação: confidence em prediction proporcional a Kelly fraction

4. BAYESIAN MULTI-SIGNAL POSTERIOR (Cox 1946 / Jaynes 2003)
   - Combine multiple weak signals via Bayes update
   - Likelihood ratio cada signal × prior odds

Refs:
- Mandelbrot 1971 "When Can Price Be Arbitraged Efficiently?"
- Hurst 1951 "Long-term storage capacity of reservoirs"
- Moskowitz, Ooi, Pedersen 2012 "Time series momentum" (JFE)
- Kelly 1956 "A New Interpretation of Information Rate"
- Jaynes 2003 "Probability Theory: The Logic of Science"
"""

from __future__ import annotations

import math
from datetime import datetime, timedelta

from engine.factor_models import (
    get_price_series, momentum_predictor, mean_reversion_predictor,
)


# ============================================================================
# 1. HURST EXPONENT (R/S analysis)
# ============================================================================
def hurst_exponent(prices: list[float], min_lag: int = 2, max_lag: int = 20) -> float | None:
    """Computa Hurst H via R/S (rescaled range) analysis.

    H ∈ [0, 1]:
    - H > 0.5: trending (persistent, momentum trades)
    - H = 0.5: random walk (efficient market)
    - H < 0.5: mean-reverting (anti-persistent)

    Returns H ou None se data insuficiente.
    """
    if len(prices) < max_lag + 2:
        return None

    # Log returns
    returns = []
    for i in range(1, len(prices)):
        if prices[i - 1] > 0:
            returns.append(math.log(prices[i] / prices[i - 1]))
    if len(returns) < max_lag:
        return None

    log_lags = []
    log_rs = []
    for lag in range(min_lag, min(max_lag + 1, len(returns))):
        # Mean of returns in window
        mean = sum(returns[:lag]) / lag
        deviations = [r - mean for r in returns[:lag]]
        # Cumulative deviation
        cum = []
        s = 0
        for d in deviations:
            s += d
            cum.append(s)
        R = max(cum) - min(cum) if cum else 0
        # Std dev
        var = sum(d ** 2 for d in deviations) / lag
        S = math.sqrt(var) if var > 0 else 1e-9
        if R / S > 0:
            log_lags.append(math.log(lag))
            log_rs.append(math.log(R / S))

    if len(log_lags) < 2:
        return None

    # Linear regression slope = H
    n = len(log_lags)
    mean_x = sum(log_lags) / n
    mean_y = sum(log_rs) / n
    num = sum((log_lags[i] - mean_x) * (log_rs[i] - mean_y) for i in range(n))
    den = sum((log_lags[i] - mean_x) ** 2 for i in range(n))
    if den == 0:
        return None
    return num / den


def hurst_regime_predictor(symbol: str, date_iso: str) -> float:
    """Switch strategy by Hurst regime.

    H > 0.55: usa momentum
    H < 0.45: usa mean reversion
    Else: 0.50 (efficient regime)
    """
    series = get_price_series(symbol, date_iso, n_days=22)
    h = hurst_exponent(series)
    if h is None:
        return 0.50
    if h > 0.55:
        return momentum_predictor(symbol, date_iso)
    if h < 0.45:
        return mean_reversion_predictor(symbol, date_iso)
    return 0.50


# ============================================================================
# 2. VOLATILITY-ADJUSTED MOMENTUM (Moskowitz 2012)
# ============================================================================
def realized_volatility(prices: list[float]) -> float:
    """Annualized vol from daily returns."""
    if len(prices) < 2:
        return 0.0
    returns = []
    for i in range(1, len(prices)):
        if prices[i - 1] > 0:
            returns.append(math.log(prices[i] / prices[i - 1]))
    if not returns:
        return 0.0
    mean = sum(returns) / len(returns)
    var = sum((r - mean) ** 2 for r in returns) / len(returns)
    daily_vol = math.sqrt(var)
    return daily_vol * math.sqrt(252)  # annualize


def vol_adj_momentum(symbol: str, date_iso: str, lookback_days: int = 20) -> float:
    """Risk-normalized momentum (Sharpe-like).

    signal = recent_return / volatility
    Predict up se signal > threshold (mais robusto que raw return).
    """
    series = get_price_series(symbol, date_iso, lookback_days + 2)
    if len(series) < lookback_days // 2:
        return 0.50

    # Cumulative return over window
    if series[0] == 0:
        return 0.50
    ret = (series[-1] - series[0]) / series[0]

    # Realized vol over window
    vol = realized_volatility(series)
    if vol <= 0:
        return 0.50

    # Sharpe-like z-score (annualized)
    sharpe = ret / vol if vol > 0 else 0
    # Map to probability via sigmoid-like
    if sharpe > 0.3:
        return 0.62
    if sharpe < -0.3:
        return 0.38
    if sharpe > 0.1:
        return 0.55
    if sharpe < -0.1:
        return 0.45
    return 0.50


# ============================================================================
# 3. KELLY FRACTIONAL — bet sizing aware
# ============================================================================
def kelly_fraction(p_win: float, b_payoff: float = 1.0) -> float:
    """Kelly: f = (bp - q) / b, p+q=1.

    Returns fração in [0, 1]. Negative kelly → 0 (don't bet).
    """
    q = 1 - p_win
    if b_payoff <= 0:
        return 0.0
    f = (b_payoff * p_win - q) / b_payoff
    return max(0.0, min(1.0, f))


def kelly_calibrated_predictor(p_raw: float) -> float:
    """Adjust prediction by Kelly fraction (low edge → push toward 0.5).

    Edge = |p - 0.5|. Kelly f = 2*edge (binary even-money).
    Confidence-adjust: shrink toward 0.5 by (1 - kelly_f).
    """
    edge = abs(p_raw - 0.5)
    f = kelly_fraction(p_raw, 1.0) if p_raw > 0.5 else kelly_fraction(1 - p_raw, 1.0)
    # If kelly small (low edge), shrink hard
    return 0.5 + (p_raw - 0.5) * f


# ============================================================================
# 4. BAYESIAN MULTI-SIGNAL POSTERIOR
# ============================================================================
def bayes_update(prior: float, likelihood_ratio: float) -> float:
    """Update prior odds via Bayes.

    posterior_odds = prior_odds * LR
    """
    if prior <= 0 or prior >= 1:
        return prior
    prior_odds = prior / (1 - prior)
    posterior_odds = prior_odds * likelihood_ratio
    return posterior_odds / (1 + posterior_odds)


def signal_to_lr(p_signal: float, base_rate: float = 0.5) -> float:
    """Convert signal probability to likelihood ratio.

    LR = P(signal|H1) / P(signal|H0) ≈ p_signal / base_rate
    """
    if base_rate == 0:
        return 1.0
    return p_signal / base_rate


def bayesian_multi_signal_predictor(symbol: str, date_iso: str) -> float:
    """Combine 3 weak signals via Bayes update.

    prior = 0.50 (no info)
    Signals: momentum + vol_adj_momentum + hurst_regime
    """
    p_mom = momentum_predictor(symbol, date_iso)
    p_vol = vol_adj_momentum(symbol, date_iso)
    p_hurst = hurst_regime_predictor(symbol, date_iso)

    # Convert each to likelihood ratio
    posterior = 0.50
    for p_sig in (p_mom, p_vol, p_hurst):
        if abs(p_sig - 0.50) > 0.01:  # signal não-neutro
            lr = signal_to_lr(p_sig, 0.5)
            posterior = bayes_update(posterior, lr)
    return max(0.05, min(0.95, posterior))


# ============================================================================
# Strategy dispatch (extend factor_models.evaluate_strategy_on_events)
# ============================================================================
ADVANCED_STRATEGIES = {
    "hurst_regime": hurst_regime_predictor,
    "vol_adj_momentum": vol_adj_momentum,
    "kelly_calibrated": lambda s, d: kelly_calibrated_predictor(momentum_predictor(s, d)),
    "bayesian_multi": bayesian_multi_signal_predictor,
}
