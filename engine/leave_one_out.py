"""Leave-one-out CV + per-event functional sensitivity (delta-Brier)."""

from __future__ import annotations

from typing import Callable

from engine._pred_utils import pairs_from_events


def loo_cv(events: list, classify_fn: Callable) -> dict:
    """LOO: classifier is stateless wrt events, so test = single held-out.

    Aggregates accuracy and Brier across the n single-event tests."""
    pairs = pairs_from_events(events, classify_fn)
    n = len(pairs)
    if n == 0:
        return {"error": "no labeled events", "n": 0}
    hits = sum(1 for p, y in pairs if (p >= 0.5) == bool(y))
    brier_sum = sum((p - y) ** 2 for p, y in pairs)
    return {
        "n": n,
        "loo_acc": hits / n,
        "loo_brier": brier_sum / n,
        "per_fold_acc": [1.0 if (p >= 0.5) == bool(y) else 0.0 for p, y in pairs],
        "per_fold_brier": [(p - y) ** 2 for p, y in pairs],
    }


def loo_sensitivity(events: list, classify_fn: Callable) -> list[dict]:
    """Delta-Brier when each event is removed. Sorted desc by |delta|.

    Higher |delta| = event has more influence on the overall metric."""
    labeled = [e for e in events if e.get("outcome_real") is not None]
    n = len(labeled)
    if n <= 1:
        return []

    base = loo_cv(labeled, classify_fn)
    base_brier = base["loo_brier"]
    base_acc = base["loo_acc"]
    base_brier_sum = base_brier * n
    base_hits = round(base_acc * n)

    out: list[dict] = []
    for i, ev in enumerate(labeled):
        per_b = base["per_fold_brier"][i]
        per_a = base["per_fold_acc"][i]
        new_n = n - 1
        new_brier = (base_brier_sum - per_b) / new_n
        new_acc = (base_hits - per_a) / new_n
        out.append({
            "evento_id": ev.get("evento_id"),
            "outcome_real": ev.get("outcome_real"),
            "delta_brier": new_brier - base_brier,
            "delta_acc": new_acc - base_acc,
            "per_event_brier": per_b,
        })

    out.sort(key=lambda d: abs(d["delta_brier"]), reverse=True)
    return out
