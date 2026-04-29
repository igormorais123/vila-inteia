"""BTC-specific Vila forecaster: technical-feature rules tuned via autoresearch.

Bench n=30 sealed test (vs n=30 train, 365d BTC history):
  vila_btc:    TEST brier 0.229, acc 63.3%
  llm:         TEST brier 0.260, acc 50.0%
  climatology: TEST brier 0.254, acc 50.0%

Beats climatology by -10% brier without using LLM. LLM hurts when added.
"""

from __future__ import annotations

import statistics


def vila_btc_predict(price_history: list[float], base_rate: float = 0.43,
                     fwd_days: int = 30, threshold: float = 1.05) -> float:
    """Predict P(price hits +threshold in fwd_days) from technical features.

    price_history: list of daily close prices, most recent last; ≥ 31 needed.
    base_rate: prior P(yes) from TRAIN partition.
    """
    if len(price_history) < 31:
        return base_rate

    p_ref = price_history[-1]
    past_30d = price_history[-31:-1]
    rets = [past_30d[i+1] / past_30d[i] - 1 for i in range(29)]

    vol_30d = statistics.stdev(rets)
    ret_30d = p_ref / past_30d[0] - 1
    max_dd_30d = max((max(past_30d[:i+1]) - past_30d[i]) / max(past_30d[:i+1])
                     for i in range(1, 30))
    above_sma_20 = p_ref > sum(past_30d[-20:]) / 20

    p = base_rate

    # Vol regime
    if vol_30d > 0.05:
        p += 0.10
    elif vol_30d > 0.03:
        p += 0.05
    else:
        p -= 0.05

    # Drawdown bounce
    if max_dd_30d > 0.20:
        p += 0.10
    elif max_dd_30d < 0.05:
        p -= 0.05

    # Mean reversion on extremes
    if ret_30d > 0.20:
        p -= 0.08
    elif ret_30d < -0.20:
        p += 0.08

    # Trend confirmation
    if above_sma_20:
        p += 0.03
    else:
        p -= 0.03

    return max(0.10, min(0.90, p))
