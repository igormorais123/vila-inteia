"""Max drawdown analysis.

Tracks peak-to-trough decline of a bankroll/equity series.
"""

from __future__ import annotations


def max_drawdown(bankroll_series: list[float]) -> dict:
    """Peak-to-trough decline.

    Returns dict with max_dd (fraction), dd_duration (steps trough-from-peak),
    peak_idx, trough_idx, recovery_idx (-1 if never recovered).
    Empty series -> zeros.
    """
    s = [float(x) for x in bankroll_series]
    n = len(s)
    if n == 0:
        return {"max_dd": 0.0, "dd_duration": 0,
                "peak_idx": -1, "trough_idx": -1, "recovery_idx": -1}

    peak = s[0]
    peak_i = 0
    best_peak_i = 0
    best_trough_i = 0
    max_dd = 0.0
    for i, v in enumerate(s):
        if v > peak:
            peak = v
            peak_i = i
        dd = (peak - v) / peak if peak > 0 else 0.0
        if dd > max_dd:
            max_dd = dd
            best_peak_i = peak_i
            best_trough_i = i

    # Recovery: first index after trough where value >= peak value.
    peak_val = s[best_peak_i]
    recovery_i = -1
    for j in range(best_trough_i + 1, n):
        if s[j] >= peak_val:
            recovery_i = j
            break

    return {
        "max_dd": max_dd,
        "dd_duration": best_trough_i - best_peak_i,
        "peak_idx": best_peak_i,
        "trough_idx": best_trough_i,
        "recovery_idx": recovery_i,
        "peak_value": peak_val,
        "trough_value": s[best_trough_i],
    }


def drawdown_metrics(returns: list[float], initial: float = 1000.0) -> dict:
    """Chain returns into a bankroll series, then compute DD.

    returns are simple per-period returns (e.g. 0.05 = +5%).
    """
    bankroll = float(initial)
    series = [bankroll]
    for r in returns:
        bankroll *= (1.0 + float(r))
        series.append(bankroll)
    dd = max_drawdown(series)
    dd["bankroll_series"] = series
    dd["final_bankroll"] = bankroll
    return dd
