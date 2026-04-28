"""Combine train-test split + LOO + stratified CV for robust validation."""

from __future__ import annotations

import random
from typing import Callable

from engine._pred_utils import pairs_from_events
from engine.cv_stratified import evaluate_stratified_cv
from engine.leave_one_out import loo_cv


def _train_test_split(
    events: list, test_frac: float = 0.3, seed: int = 42
) -> tuple[list, list]:
    """Random shuffled split into (train, test)."""
    items = list(events)
    rng = random.Random(seed)
    rng.shuffle(items)
    n_test = max(1, int(len(items) * test_frac))
    return items[n_test:], items[:n_test]


def dual_validation_report(
    events: list,
    classify_fn: Callable,
    test_frac: float = 0.3,
    seed: int = 42,
    n_folds: int = 5,
) -> dict:
    """Aggregate train-test, LOO and stratified-CV metrics in a single dict."""
    labeled = [e for e in events if e.get("outcome_real") is not None]
    n = len(labeled)
    if n < n_folds:
        return {"error": f"need >= {n_folds} labeled events", "n": n}

    _train, test = _train_test_split(labeled, test_frac=test_frac, seed=seed)
    pairs = pairs_from_events(test, classify_fn)
    if pairs:
        hits = sum(1 for p, y in pairs if (p >= 0.5) == bool(y))
        tt_acc = hits / len(pairs)
        tt_brier = sum((p - y) ** 2 for p, y in pairs) / len(pairs)
    else:
        tt_acc = 0.0
        tt_brier = 0.0

    loo = loo_cv(labeled, classify_fn)
    strat = evaluate_stratified_cv(labeled, classify_fn, n_folds=n_folds)

    return {
        "n": n,
        "train_test_acc": tt_acc,
        "train_test_brier": tt_brier,
        "train_test_n": len(pairs),
        "loo_acc": loo.get("loo_acc", 0.0),
        "loo_brier": loo.get("loo_brier", 0.0),
        "stratified_acc_mean": strat.get("mean_acc", 0.0),
        "stratified_acc_std": strat.get("std_acc", 0.0),
        "stratified_brier_mean": strat.get("mean_brier", 0.0),
        "stratified_brier_std": strat.get("std_brier", 0.0),
        "stratified_n_folds": strat.get("n_folds", 0),
    }
