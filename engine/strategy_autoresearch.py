"""Autoresearch loop: discover best strategy combination per event category.

For each Vila category, sweep candidate weight combinations over
{vila, lindy, llm_direct, market_implied, tfidf} on Q1 train, pick
the combo with lowest brier. Hard-codes the winning per-category plan.

Replaces LLM coordinator with offline-discovered policy.
"""

from __future__ import annotations

import itertools
from collections import defaultdict
from typing import Callable

from engine.lindy import lindy_for_event
from engine.log_pool import log_pool
from engine.post_cutoff_classifier import classify_and_predict


def candidate_weight_combos(step: float = 0.5) -> list[dict[str, float]]:
    """Generate weight combos over 3 tools (vila, lindy, llm) summing to ~1."""
    combos = []
    for v, l, m in itertools.product(
        [0.0, step, 2*step, 1.0],
        [0.0, step, 2*step, 1.0],
        [0.0, step, 2*step, 1.0],
    ):
        s = v + l + m
        if s <= 0:
            continue
        combos.append({"vila": v/s, "lindy": l/s, "llm_direct": m/s})
    # Dedupe
    seen = set()
    unique = []
    for c in combos:
        key = (round(c["vila"], 2), round(c["lindy"], 2), round(c["llm_direct"], 2))
        if key not in seen:
            seen.add(key)
            unique.append(c)
    return unique


def evaluate_combo_per_event(events: list, weights: dict[str, float],
                             vila_predict_fn=classify_and_predict,
                             llm_predict_fn=None) -> float:
    """Compute brier for a fixed weight combo on events."""
    brier = 0.0
    n = 0
    for e in events:
        framing = e.get("outcome_framing") or e.get("framing", "")
        contexto = e.get("contexto", "")
        y = e.get("outcome_real")
        if y is None:
            continue
        probs = {}
        if weights.get("vila", 0) > 0:
            p, _ = vila_predict_fn(framing, contexto)
            probs["vila"] = p
        if weights.get("lindy", 0) > 0:
            p = lindy_for_event(framing, contexto)
            if p is not None:
                probs["lindy"] = p
        if weights.get("llm_direct", 0) > 0 and llm_predict_fn is not None:
            p = llm_predict_fn(framing, contexto)
            if p is not None:
                probs["llm_direct"] = p
        if not probs:
            continue
        active = {k: weights[k] for k in probs}
        p_pool = log_pool(probs, active)
        brier += (p_pool - y) ** 2
        n += 1
    return brier / n if n else 1.0


def discover_best_per_category(train_events: list,
                                vila_predict_fn=classify_and_predict,
                                llm_predict_fn=None,
                                step: float = 0.5) -> dict[str, dict[str, float]]:
    """For each Vila category in train, find best weight combo by brier."""
    by_cat: dict[str, list] = defaultdict(list)
    for e in train_events:
        framing = e.get("outcome_framing") or e.get("framing", "")
        _, label = vila_predict_fn(framing, e.get("contexto", ""))
        by_cat[label].append(e)

    combos = candidate_weight_combos(step=step)
    best_per_cat: dict[str, dict[str, float]] = {}
    for label, events in by_cat.items():
        if len(events) < 2:
            best_per_cat[label] = {"vila": 1.0}
            continue
        scores = []
        for combo in combos:
            b = evaluate_combo_per_event(events, combo,
                                         vila_predict_fn, llm_predict_fn)
            scores.append((b, combo))
        scores.sort(key=lambda x: x[0])
        best_per_cat[label] = scores[0][1]
    return best_per_cat


def autoresearch_predict(framing: str, contexto: str = "",
                         best_per_cat: dict[str, dict[str, float]] | None = None,
                         llm_predict_fn=None) -> float:
    """Use autoresearch-discovered weights for the event's category."""
    p_vila, label = classify_and_predict(framing, contexto)
    if not best_per_cat or label not in best_per_cat:
        return p_vila
    weights = best_per_cat[label]

    probs = {"vila": p_vila}
    if weights.get("lindy", 0) > 0:
        p = lindy_for_event(framing, contexto)
        if p is not None:
            probs["lindy"] = p
    if weights.get("llm_direct", 0) > 0 and llm_predict_fn is not None:
        p = llm_predict_fn(framing, contexto)
        if p is not None:
            probs["llm_direct"] = p

    active = {k: weights.get(k, 0) for k in probs if weights.get(k, 0) > 0}
    if not active:
        return p_vila
    return log_pool(probs, active)
