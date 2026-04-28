"""Shared utilities for forecasting modules."""

from __future__ import annotations

import math
from typing import Any, Callable


def unpack_pred(out: Any) -> float:
    """Normalize classify_fn output to bare prob."""
    return out[0] if isinstance(out, tuple) else out


def pairs_from_events(
    events: list, classify_fn: Callable
) -> list[tuple[float, int]]:
    """Extract (prob, outcome) pairs, skipping events without outcome_real."""
    pairs = []
    for e in events:
        framing = e.get("outcome_framing") or e.get("framing", "")
        contexto = e.get("contexto", "")
        y = e.get("outcome_real")
        if y is None:
            continue
        pairs.append((unpack_pred(classify_fn(framing, contexto)), int(y)))
    return pairs


def softmax_weights(scores: dict[str, float]) -> dict[str, float]:
    """Numerically-stable softmax over scores dict."""
    if not scores:
        return {}
    m = max(scores.values())
    exps = {n: math.exp(s - m) for n, s in scores.items()}
    total = sum(exps.values())
    if total <= 0:
        k = len(scores)
        return {n: 1.0 / k for n in scores}
    return {n: e / total for n, e in exps.items()}
