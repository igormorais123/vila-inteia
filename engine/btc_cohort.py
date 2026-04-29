"""BTC cohort-based forecaster: empirical base rate per (fwd_days, threshold_pct).

Discovered via autoresearch on n=2400+ events (365d × 4 horizons × 4 thresholds).
Bench TEST brier 0.177 vs global climatology 0.244 (-27%).

No hardcoded rules; just per-cohort empirical proportions from TRAIN.
"""

from __future__ import annotations

from collections import defaultdict


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
