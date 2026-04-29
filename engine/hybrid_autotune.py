"""Per-dataset autotune of (gate, w_llm) for vila_llm_hybrid.

Two-regime issue (Onda 282 bench): optimal hybrid params depend on
holdout difficulty. Easy holdouts favor gate=0.15 w_llm=0.7; hard
holdouts favor gate=0.50 w_llm=1.0. This module fits both per
TRAIN partition.

Usage:
  best = autotune_hybrid(train_events)
  p = autotune_predict(framing, contexto, best)
"""

from __future__ import annotations

import math
import statistics
from typing import Optional

from engine.llm_forecaster import llm_predict
from engine.log_pool import log_pool_predict
from engine.post_cutoff_classifier import classify_and_predict


GATE_GRID = (0.0, 0.10, 0.15, 0.20, 0.30, 0.40, 0.50)
W_LLM_GRID = (0.0, 0.30, 0.50, 0.70, 0.85, 0.95, 1.0)


def _hybrid_with_params(p_vila: float, p_llm: float,
                        gate: float, w_llm: float) -> float:
    """Apply gate-then-pool combine."""
    if abs(p_vila - 0.5) >= gate and gate > 0:
        return p_vila
    return log_pool_predict(p_llm, p_vila, w_a=w_llm)


def autotune_hybrid(train_events: list,
                    metric: str = "brier") -> dict:
    """Sweep (gate, w_llm) on TRAIN events; return best combo + brier.

    metric: 'brier' | 'acc'
    Returns: {'gate': τ, 'w_llm': w, 'brier': b, 'acc': a, 'n': n}
    """
    pairs = []
    for e in train_events:
        framing = e.get("outcome_framing") or e.get("framing", "")
        contexto = e.get("contexto", "")
        y = e.get("outcome_real")
        if y is None:
            continue
        p_v, _ = classify_and_predict(framing, contexto)
        p_l = llm_predict(framing, contexto)
        if p_l is None:
            continue
        pairs.append((p_v, p_l, int(y)))

    if not pairs:
        return {"gate": 0.20, "w_llm": 0.85, "brier": 1.0, "acc": 0, "n": 0}

    best = {"gate": 0.20, "w_llm": 0.85, "brier": 1.0, "acc": 0, "n": len(pairs)}
    for g in GATE_GRID:
        for w in W_LLM_GRID:
            preds = [(_hybrid_with_params(pv, pl, g, w), y)
                     for pv, pl, y in pairs]
            n = len(preds)
            b = sum((p - y) ** 2 for p, y in preds) / n
            a = sum(1 for p, y in preds if (p >= 0.5) == bool(y)) / n
            if metric == "brier" and b < best["brier"]:
                best = {"gate": g, "w_llm": w, "brier": b, "acc": a, "n": n}
            elif metric == "acc" and a > best["acc"]:
                best = {"gate": g, "w_llm": w, "brier": b, "acc": a, "n": n}
    return best


def autotune_predict(framing: str, contexto: str, params: dict) -> float:
    """Predict using autotuned (gate, w_llm) params from autotune_hybrid."""
    p_v, _ = classify_and_predict(framing, contexto)
    if abs(p_v - 0.5) >= params.get("gate", 0.20) and params.get("gate", 0.20) > 0:
        return p_v
    p_l = llm_predict(framing, contexto)
    if p_l is None:
        return p_v
    return log_pool_predict(p_l, p_v, w_a=params.get("w_llm", 0.85))


def evaluate_autotuned(train_events: list, test_events: list) -> dict:
    """Fit on train, evaluate on test (no peek)."""
    params = autotune_hybrid(train_events)
    n = hits = 0
    brier = 0.0
    for e in test_events:
        framing = e.get("outcome_framing") or e.get("framing", "")
        contexto = e.get("contexto", "")
        y = e.get("outcome_real")
        if y is None:
            continue
        p = autotune_predict(framing, contexto, params)
        n += 1
        if (p >= 0.5) == bool(y):
            hits += 1
        brier += (p - y) ** 2
    return {
        "params": params,
        "test_n": n,
        "test_acc": hits / n if n else 0,
        "test_brier": brier / n if n else 0,
    }
