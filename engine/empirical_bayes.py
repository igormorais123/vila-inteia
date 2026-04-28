"""Beta-Binomial Empirical Bayes per-category prior tuning (Robbins 1956).

Posterior = Beta(alpha + k, beta + n - k) where alpha+beta = prior_strength.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Callable


def fit_beta_binomial(
    cal_events: list,
    classify_fn: Callable[[str, str], tuple[float, str]],
    prior_strength: float = 5.0,
) -> dict[str, float]:
    """Compute posterior mean per category.

    prior_strength = pseudo-count weighting hardcoded prior.
    Higher = more shrinkage toward hardcoded.
    Default 5 = ~5 fictional observations of hardcode prior.
    """
    by_cat: dict[str, dict] = defaultdict(lambda: {"k": 0, "n": 0, "p_hc": 0.5})
    for e in cal_events:
        framing = e.get("outcome_framing") or e.get("framing", "")
        contexto = e.get("contexto", "")
        real = e.get("outcome_real")
        if real is None:
            continue
        p, label = classify_fn(framing, contexto)
        by_cat[label]["k"] += int(real)
        by_cat[label]["n"] += 1
        by_cat[label]["p_hc"] = p  # last-seen hardcode prior; same per cat

    posterior: dict[str, float] = {}
    for label, s in by_cat.items():
        alpha = s["p_hc"] * prior_strength
        beta = (1 - s["p_hc"]) * prior_strength
        posterior[label] = (alpha + s["k"]) / (alpha + beta + s["n"])
    return posterior


def empirical_bayes_predict(
    framing: str, contexto: str,
    classify_fn: Callable[[str, str], tuple[float, str]],
    posterior: dict[str, float],
) -> tuple[float, str]:
    """Predict using EB-tuned prior. Falls back to hardcode if cat unseen."""
    p_hc, label = classify_fn(framing, contexto)
    return posterior.get(label, p_hc), label


def evaluate_eb(
    test_events: list,
    classify_fn: Callable[[str, str], tuple[float, str]],
    posterior: dict[str, float],
) -> dict:
    """Eval EB classifier on test events."""
    n = 0
    hits = 0
    brier = 0.0
    for e in test_events:
        framing = e.get("outcome_framing") or e.get("framing", "")
        contexto = e.get("contexto", "")
        real = e.get("outcome_real")
        if real is None:
            continue
        p, _ = empirical_bayes_predict(framing, contexto, classify_fn, posterior)
        n += 1
        if (p >= 0.5) == bool(real):
            hits += 1
        brier += (p - real) ** 2
    return {
        "n": n, "hits": hits,
        "acc": hits / n if n else 0,
        "brier": brier / n if n else 0,
    }
