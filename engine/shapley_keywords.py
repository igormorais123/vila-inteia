"""Shapley value attribution for keyword categories (Shapley 1953; Lundberg-Lee 2017).

For each category in KEYWORD_PRIORS, estimate marginal contribution to bench
accuracy via Monte Carlo: sample random subsets S not containing cat, compute
v(S ∪ {cat}) - v(S), average across samples. v(S) is accuracy of a classifier
restricted to categories in S (others fall through to the default prior).
"""

from __future__ import annotations

import random
from typing import Callable


def _classify_with_subset(
    framing: str, contexto: str,
    keyword_priors: list[tuple[list[str], float, str]],
    allowed: set[str],
    default_prior: float = 0.50,
) -> tuple[float, str]:
    """First match within allowed labels; else default."""
    text = (framing + " " + contexto).lower()
    for keywords, prior, label in keyword_priors:
        if label not in allowed:
            continue
        if any(kw in text for kw in keywords):
            return prior, label
    return default_prior, "default"


def _accuracy(
    events: list,
    keyword_priors: list[tuple[list[str], float, str]],
    allowed: set[str],
    default_prior: float = 0.50,
) -> float:
    n = 0
    hits = 0
    for e in events:
        framing = e.get("outcome_framing") or e.get("framing", "")
        contexto = e.get("contexto", "")
        real = e.get("outcome_real")
        if real is None:
            continue
        p, _ = _classify_with_subset(
            framing, contexto, keyword_priors, allowed, default_prior
        )
        n += 1
        if (p >= 0.5) == bool(real):
            hits += 1
    return hits / n if n else 0.0


def shapley_attribution(
    events: list,
    classify_fn: Callable[[str, str], tuple[float, str]],  # noqa: ARG001
    keyword_priors: list[tuple[list[str], float, str]],
    n_samples: int = 100,
    default_prior: float = 0.50,
    seed: int | None = 42,
) -> dict[str, float]:
    """Monte Carlo Shapley over keyword categories.

    For each category c, sample n_samples random subsets S of the OTHER
    categories, average accuracy(S ∪ {c}) - accuracy(S).
    classify_fn is unused (signature kept for parity with other modules).
    """
    rng = random.Random(seed)
    cats = [label for _, _, label in keyword_priors]
    shapley: dict[str, float] = {c: 0.0 for c in cats}
    for c in cats:
        others = [x for x in cats if x != c]
        total = 0.0
        for _ in range(n_samples):
            # Random subset size, then sample that many from others.
            k = rng.randint(0, len(others))
            S = set(rng.sample(others, k)) if k > 0 else set()
            v_without = _accuracy(events, keyword_priors, S, default_prior)
            v_with = _accuracy(events, keyword_priors, S | {c}, default_prior)
            total += v_with - v_without
        shapley[c] = total / n_samples if n_samples else 0.0
    return shapley
