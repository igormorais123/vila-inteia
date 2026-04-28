"""Combined diagnostic pipeline: Brier+CI, selective, conformal, Murphy, time-series CV."""

from __future__ import annotations

import math
import random
from typing import Callable

from engine._pred_utils import pairs_from_events, unpack_pred
from engine.conformal import conformal_calibrate, evaluate_conformal
from engine.post_cutoff_classifier import classify_and_predict
from engine.selective_forecast import evaluate_selective
from engine.validation_rigorous import (
    bootstrap_ci as _bootstrap_ci,
    murphy_decomposition as _murphy_core,
)


def bootstrap_brier_ci(
    events: list, classify_fn: Callable, n_resamples: int = 1000, seed: int = 42,
) -> tuple[float, float, float]:
    pairs = pairs_from_events(events, classify_fn)
    if not pairs:
        return 0.0, 0.0, 0.0
    preds = [p for p, _ in pairs]
    reals = [y for _, y in pairs]
    res = _bootstrap_ci(preds, reals, metric="brier", n_resamples=n_resamples, seed=seed)
    return res["mean"], res["lower"], res["upper"]


def time_series_cv(
    events: list, classify_fn: Callable, n_folds: int = 5,
) -> dict:
    """Walk-forward CV: train on prefix, test on next fold."""
    n = len(events)
    if n < n_folds * 2:
        return {"error": "insufficient data", "n": n}

    fold_size = n // n_folds
    accs: list[float] = []
    briers: list[float] = []
    for fold in range(1, n_folds):
        test = events[fold * fold_size: (fold + 1) * fold_size]
        if not test:
            continue
        pairs = pairs_from_events(test, classify_fn)
        if not pairs:
            continue
        hits = sum(1 for p, y in pairs if (p >= 0.5) == bool(y))
        brier = sum((p - y) ** 2 for p, y in pairs)
        accs.append(hits / len(pairs))
        briers.append(brier / len(pairs))

    if not accs:
        return {"error": "no folds"}
    mean_a = sum(accs) / len(accs)
    mean_b = sum(briers) / len(briers)
    return {
        "n_folds": len(accs),
        "mean_acc": mean_a,
        "std_acc": math.sqrt(sum((a - mean_a) ** 2 for a in accs) / len(accs)),
        "mean_brier": mean_b,
        "std_brier": math.sqrt(sum((b - mean_b) ** 2 for b in briers) / len(briers)),
    }


def murphy_decomposition(events: list, classify_fn: Callable, n_bins: int = 10) -> dict:
    """Brier = REL + UNC - RES (delegates to validation_rigorous)."""
    pairs = pairs_from_events(events, classify_fn)
    preds = [p for p, _ in pairs]
    reals = [y for _, y in pairs]
    out = _murphy_core(preds, reals, n_bins=n_bins)
    base_rate = sum(reals) / len(reals) if reals else 0
    out["base_rate"] = round(base_rate, 3)
    out["brier"] = round(out["brier"], 4)
    out["reliability"] = round(out["reliability"], 4)
    out["resolution"] = round(out["resolution"], 4)
    out["uncertainty"] = round(out["uncertainty"], 4)
    return out


def combined_report(events: list, classify_fn: Callable = classify_and_predict) -> dict:
    pairs = pairs_from_events(events, classify_fn)
    n = len(pairs)
    hits = sum(1 for p, y in pairs if (p >= 0.5) == bool(y))
    brier = sum((p - y) ** 2 for p, y in pairs)
    base_acc = hits / n if n else 0
    base_brier = brier / n if n else 0

    pt, lo, hi = bootstrap_brier_ci(events, classify_fn)

    selective = {tau: evaluate_selective(events, classify_fn, tau=tau)
                 for tau in (0.0, 0.15, 0.30, 0.40)}

    quants = conformal_calibrate(events, classify_fn, alpha=0.2)
    conformal = evaluate_conformal(events, classify_fn, quants, alpha=0.2)
    murphy = murphy_decomposition(events, classify_fn)
    cv = time_series_cv(events, classify_fn, n_folds=5)

    return {
        "n": n,
        "base_acc": round(base_acc, 3),
        "base_brier": round(base_brier, 4),
        "bootstrap_brier_ci": (round(lo, 4), round(hi, 4)),
        "selective": selective,
        "conformal": conformal,
        "murphy": murphy,
        "time_series_cv": cv,
    }
