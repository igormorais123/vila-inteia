"""BTC cohort-based forecaster: empirical base rate per (fwd_days, threshold_pct, vol_bin5).

Autoresearch on n=1472 events (365d × 4 horizons × 4 thresholds × every 3 days):
  - Round 1 (fwd, thr):                   brier 0.1772
  - Round 2 + vol_bin3:                   brier 0.1693
  - Round 7 + vol_bin5:                   brier 0.1649
  - Round 9 + Stein shrink 0.1 → global:  brier 0.1641 (FINAL)
  Climatology baseline:                    brier 0.2441

Improvement -33% vs climatology, no hardcoded rules.
"""

from __future__ import annotations

import statistics
from collections import defaultdict


def vol_bin5(vol_30d: float) -> str:
    """5-bin volatility classification."""
    if vol_30d < 0.015: return "v1"
    if vol_30d < 0.025: return "v2"
    if vol_30d < 0.035: return "v3"
    if vol_30d < 0.05: return "v4"
    return "v5"


def make_event(idx: int, prices: list, fwd_days: int, threshold_pct: float) -> dict | None:
    """Build a BTC event dict for autoresearch / bench."""
    if idx < 30 or idx + fwd_days >= len(prices):
        return None
    p_ref = prices[idx]
    forward = prices[idx + 1: idx + 1 + fwd_days]
    past = prices[idx - 30: idx]
    rets = [past[i + 1] / past[i] - 1 for i in range(29)]
    return {
        "outcome": 1 if max(forward) > p_ref * (1 + threshold_pct / 100) else 0,
        "fwd_days": fwd_days,
        "threshold_pct": threshold_pct,
        "vol_bin5": vol_bin5(statistics.stdev(rets)),
    }


def fit_cohorts_v5(train_events: list, stein_shrink: float = 0.1) -> dict:
    """Fit cohort base rates per (fwd_days, threshold_pct, vol_bin5).

    Returns dict with cohort tuples + special keys:
      ('_basic', fwd, thr): 2D fallback
      '_global': global TRAIN base rate
      '_shrink': Stein shrink amount (for predict_v5 to apply)
    """
    by_5 = defaultdict(list)
    by_basic = defaultdict(list)
    for e in train_events:
        by_5[(e["fwd_days"], e["threshold_pct"], e["vol_bin5"])].append(e["outcome"])
        by_basic[(e["fwd_days"], e["threshold_pct"])].append(e["outcome"])

    rates = {k: sum(v) / len(v) for k, v in by_5.items()}
    for k, v in by_basic.items():
        rates[("_basic",) + k] = sum(v) / len(v)
    n = sum(1 for _ in train_events)
    rates["_global"] = sum(e["outcome"] for e in train_events) / n if n else 0.5
    rates["_shrink"] = stein_shrink
    return rates


def predict_cohort_v5(fwd_days: int, threshold_pct: float, vol_30d: float,
                      cohort_rates: dict) -> float:
    """Predict via cohort v5 → basic fallback → global, with Stein shrink to global."""
    vbin = vol_bin5(vol_30d)
    p = cohort_rates.get((fwd_days, threshold_pct, vbin),
                         cohort_rates.get(("_basic", fwd_days, threshold_pct),
                                          cohort_rates.get("_global", 0.5)))
    s = cohort_rates.get("_shrink", 0.1)
    g = cohort_rates.get("_global", 0.5)
    return (1 - s) * p + s * g


def fit_cohorts(train_events: list) -> dict:
    """Fit cohort base rates from TRAIN events.

    Each event must have keys: outcome, fwd_days, threshold_pct.
    Returns: {(fwd_days, threshold_pct): base_rate, "_global": global_rate}
    """
    cohorts = defaultdict(list)
    for e in train_events:
        cohorts[(e["fwd_days"], e["threshold_pct"])].append(e["outcome"])
    rates = {k: sum(v) / len(v) for k, v in cohorts.items()}
    n_total = sum(len(v) for v in cohorts.values())
    rates["_global"] = sum(e["outcome"] for e in train_events) / n_total if n_total else 0.5
    return rates


def predict_cohort(fwd_days: int, threshold_pct: float, cohort_rates: dict) -> float:
    """Predict P(yes) for given (fwd_days, threshold_pct) cohort."""
    return cohort_rates.get((fwd_days, threshold_pct), cohort_rates.get("_global", 0.5))


def evaluate_cohort(test_events: list, cohort_rates: dict) -> dict:
    """Eval cohort predictor on TEST events."""
    n = len(test_events)
    if n == 0:
        return {"n": 0, "brier": 0, "acc": 0}
    brier = 0.0
    hits = 0
    for e in test_events:
        p = predict_cohort(e["fwd_days"], e["threshold_pct"], cohort_rates)
        brier += (p - e["outcome"]) ** 2
        if (p >= 0.5) == bool(e["outcome"]):
            hits += 1
    return {"n": n, "brier": brier / n, "acc": hits / n}
