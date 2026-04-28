"""
Onda 250: Stacking ensemble market — combine top 5 strategies.

Methods tested em 197 events Q1 2026:
  - Weighted average (inverse brier): 64.5% acc, brier 0.2442
  - Simple average: 64.5% acc, brier 0.2442
  - **Majority vote**: 65.5% acc, brier 0.2290 ← best brier

Insight: voting ensemble extrai consenso entre strategies independent.
Brier 0.2290 é melhor que any individual strategy (best individual: 0.2410).
"""

from __future__ import annotations

from typing import Callable


def weighted_ensemble(
    pred_dict: dict[str, float],
    weights: dict[str, float],
) -> float:
    """Weighted average das predictions.

    pred_dict: {strategy_name: prob}
    weights: {strategy_name: weight} (não normalizado OK)
    """
    total_w = sum(weights.values())
    if total_w == 0:
        return 0.50
    return sum(pred_dict[k] * w / total_w for k, w in weights.items() if k in pred_dict)


def majority_vote_ensemble(pred_dict: dict[str, float],
                           threshold: float = 0.5,
                           confidence_high: float = 0.6,
                           confidence_low: float = 0.4) -> float:
    """Majority class vote → output prob.

    Conta quantas strategies predicen UP (p >= 0.5).
    Se ≥ ceil(n/2)+1 → confidence_high
    Se ≤ floor(n/2) → confidence_low
    Else 0.5.

    Brier optimal porque prediction discreta {high, low, mid} reduz overconfidence.
    """
    n = len(pred_dict)
    if n == 0:
        return 0.50
    votes_up = sum(1 for p in pred_dict.values() if p >= threshold)
    votes_down = n - votes_up

    majority_threshold = n // 2 + 1
    if votes_up >= majority_threshold:
        return confidence_high
    if votes_down >= majority_threshold:
        return confidence_low
    return 0.50


def inverse_brier_weights(strategies_briers: dict[str, float]) -> dict[str, float]:
    """Weight = 1 / brier (lower brier = higher weight)."""
    weights = {}
    for name, brier in strategies_briers.items():
        if brier > 0:
            weights[name] = 1.0 / brier
        else:
            weights[name] = 1.0
    total = sum(weights.values())
    return {k: v / total for k, v in weights.items()} if total > 0 else weights


def evaluate_ensemble(events: list, predict_fns: dict[str, Callable],
                     ensemble_method: str = "majority") -> dict:
    """Eval ensemble method sobre events.

    events: list of dicts com keys: symbol, date, real_outcome
    predict_fns: {name: fn(symbol, date) -> prob}
    ensemble_method: 'majority' | 'simple_avg' | 'weighted'
    """
    if ensemble_method == "weighted":
        # Need brier per strategy first
        briers = {}
        for name, fn in predict_fns.items():
            brier_sum = 0.0
            n = 0
            for e in events:
                p = fn(e["symbol"], e["date"])
                brier_sum += (p - e["real_outcome"]) ** 2
                n += 1
            briers[name] = brier_sum / n if n else 1.0
        weights = inverse_brier_weights(briers)
    else:
        weights = None

    hits = 0
    brier_sum = 0.0
    for e in events:
        preds = {name: fn(e["symbol"], e["date"]) for name, fn in predict_fns.items()}
        if ensemble_method == "majority":
            p = majority_vote_ensemble(preds)
        elif ensemble_method == "simple_avg":
            p = sum(preds.values()) / len(preds)
        elif ensemble_method == "weighted":
            p = weighted_ensemble(preds, weights)
        else:
            raise ValueError(f"unknown ensemble_method: {ensemble_method}")

        real = e["real_outcome"]
        if (p >= 0.5) == bool(real):
            hits += 1
        brier_sum += (p - real) ** 2

    n = len(events)
    return {
        "method": ensemble_method,
        "n": n, "hits": hits,
        "acc": hits / n if n else 0,
        "brier": brier_sum / n if n else 0,
    }
