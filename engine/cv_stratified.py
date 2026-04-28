"""Stratified k-fold CV: preserves outcome class balance per fold."""

from __future__ import annotations

import math
import random
from typing import Callable

from engine._pred_utils import pairs_from_events


def stratified_kfold(
    events: list, n_folds: int = 5, seed: int = 42
) -> list[tuple[list, list]]:
    """Partition events stratifying by outcome_real. Returns [(train, test), ...]."""
    pos = [e for e in events if e.get("outcome_real") == 1]
    neg = [e for e in events if e.get("outcome_real") == 0]
    rng = random.Random(seed)
    rng.shuffle(pos)
    rng.shuffle(neg)

    def _fold_assign(items: list) -> list[list]:
        folds: list[list] = [[] for _ in range(n_folds)]
        for i, ev in enumerate(items):
            folds[i % n_folds].append(ev)
        return folds

    pos_folds = _fold_assign(pos)
    neg_folds = _fold_assign(neg)
    splits: list[tuple[list, list]] = []
    for k in range(n_folds):
        test = pos_folds[k] + neg_folds[k]
        train = []
        for j in range(n_folds):
            if j == k:
                continue
            train.extend(pos_folds[j])
            train.extend(neg_folds[j])
        if test:
            splits.append((train, test))
    return splits


def evaluate_stratified_cv(
    events: list, classify_fn: Callable, n_folds: int = 5
) -> dict:
    """Mean+std accuracy and Brier across stratified folds."""
    splits = stratified_kfold(events, n_folds=n_folds)
    if not splits:
        return {"error": "no folds", "n": len(events)}

    accs: list[float] = []
    briers: list[float] = []
    fold_sizes: list[int] = []
    for _train, test in splits:
        pairs = pairs_from_events(test, classify_fn)
        if not pairs:
            continue
        hits = sum(1 for p, y in pairs if (p >= 0.5) == bool(y))
        brier = sum((p - y) ** 2 for p, y in pairs)
        accs.append(hits / len(pairs))
        briers.append(brier / len(pairs))
        fold_sizes.append(len(pairs))

    if not accs:
        return {"error": "no scored folds"}

    mean_a = sum(accs) / len(accs)
    mean_b = sum(briers) / len(briers)
    return {
        "n": len(events),
        "n_folds": len(accs),
        "fold_sizes": fold_sizes,
        "mean_acc": mean_a,
        "std_acc": math.sqrt(sum((a - mean_a) ** 2 for a in accs) / len(accs)),
        "mean_brier": mean_b,
        "std_brier": math.sqrt(sum((b - mean_b) ** 2 for b in briers) / len(briers)),
    }
