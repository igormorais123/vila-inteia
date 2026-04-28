"""Kelly criterion (Kelly 1956) bet sizing.

Binary bet at decimal odds o with prob p:
  b = o - 1
  q = 1 - p
  f* = (b*p - q) / b
EV per unit: ev = p*(o-1) - (1-p)
"""

from __future__ import annotations

import math
from typing import Callable

from engine._pred_utils import unpack_pred


def kelly_fraction(p: float, decimal_odds: float,
                   fractional: float = 1.0) -> float:
    """Optimal fraction of bankroll to wager.

    fractional<1.0 implements fractional Kelly (e.g. 0.5 = half-Kelly).
    Returns 0.0 when no edge (or bad inputs).
    """
    if decimal_odds <= 1.0:
        return 0.0
    p = max(0.0, min(1.0, float(p)))
    b = decimal_odds - 1.0
    q = 1.0 - p
    f = (b * p - q) / b
    if f <= 0 or not math.isfinite(f):
        return 0.0
    return max(0.0, min(1.0, f * fractional))


def expected_value(p: float, decimal_odds: float) -> float:
    """EV per 1 unit staked. Positive => +edge."""
    return p * (decimal_odds - 1.0) - (1.0 - p)


def kelly_betting_simulation(events_with_odds: list,
                             classify_fn: Callable,
                             initial_bankroll: float = 1000.0,
                             fractional: float = 1.0,
                             min_edge: float = 0.0) -> dict:
    """Sequentially bet Kelly fraction on each event.

    events_with_odds: list of dicts with framing/contexto/outcome_real and
      optional 'decimal_odds' (defaults to 1.91, typical Polymarket/Kalshi).
    classify_fn(framing, contexto) -> p (or (p, label)).
    Returns final_bankroll, sharpe, max_drawdown, and per-bet trace.
    """
    bankroll = float(initial_bankroll)
    series: list[float] = [bankroll]
    returns: list[float] = []
    bets = 0
    wins = 0

    for e in events_with_odds:
        framing = e.get("outcome_framing") or e.get("framing", "")
        contexto = e.get("contexto", "")
        y = e.get("outcome_real")
        if y is None:
            continue
        odds = float(e.get("decimal_odds", 1.91))
        p = unpack_pred(classify_fn(framing, contexto))
        ev = expected_value(p, odds)
        if ev <= min_edge:
            series.append(bankroll)
            returns.append(0.0)
            continue
        f = kelly_fraction(p, odds, fractional=fractional)
        stake = bankroll * f
        if stake <= 0:
            series.append(bankroll)
            returns.append(0.0)
            continue
        if int(y) == 1:
            pnl = stake * (odds - 1.0)
            wins += 1
        else:
            pnl = -stake
        prev = bankroll
        bankroll += pnl
        bets += 1
        series.append(bankroll)
        returns.append(pnl / prev if prev > 0 else 0.0)

    # Sharpe (unannualized, risk_free=0).
    sharpe = 0.0
    if returns:
        mean_r = sum(returns) / len(returns)
        var_r = sum((r - mean_r) ** 2 for r in returns) / len(returns)
        sd = math.sqrt(var_r)
        sharpe = mean_r / sd if sd > 0 else 0.0

    # Max drawdown.
    peak = series[0]
    max_dd = 0.0
    for v in series:
        if v > peak:
            peak = v
        dd = (peak - v) / peak if peak > 0 else 0.0
        if dd > max_dd:
            max_dd = dd

    return {
        "final_bankroll": bankroll,
        "initial_bankroll": initial_bankroll,
        "total_return": (bankroll - initial_bankroll) / initial_bankroll
                         if initial_bankroll else 0.0,
        "bets": bets,
        "wins": wins,
        "win_rate": wins / bets if bets else 0.0,
        "sharpe": sharpe,
        "max_drawdown": max_dd,
        "bankroll_series": series,
        "returns": returns,
    }
