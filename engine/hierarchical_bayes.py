"""Hierarchical Empirical Bayes (Gelman BDA ch.5): 2-level Beta-Binomial.

Level 1: per-category posterior (Beta-Binomial, see engine/empirical_bayes.py).
Level 2: hyperprior across categories sharing the same parent group.
Posterior for cat in group g combines empirical (k_g, n_g) at the group level
with the hyperprior (alpha_g, beta_g) derived from group-level mean.
Borrows strength from siblings to stabilize scarce categories.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Callable


def fit_hierarchical_bayes(
    events: list,
    classify_fn: Callable[[str, str], tuple[float, str]],
    parent_map: dict[str, str],
    prior_strength: float = 3.0,
) -> dict[str, float]:
    """Compute per-category posterior with parent-group shrinkage.

    parent_map: {category_label: parent_group}. Categories without an entry are
    treated as their own parent (no group sharing).
    prior_strength: pseudo-count weighting hardcoded prior at the leaf level.
    """
    leaf: dict[str, dict] = defaultdict(lambda: {"k": 0, "n": 0, "p_hc": 0.5})
    for e in events:
        framing = e.get("outcome_framing") or e.get("framing", "")
        contexto = e.get("contexto", "")
        real = e.get("outcome_real")
        if real is None:
            continue
        out = classify_fn(framing, contexto)
        p, label = out if isinstance(out, tuple) else (out, "default")
        leaf[label]["k"] += int(real)
        leaf[label]["n"] += 1
        leaf[label]["p_hc"] = p

    # Aggregate group-level stats: sum k, sum n across cats sharing the parent.
    group_k: dict[str, int] = defaultdict(int)
    group_n: dict[str, int] = defaultdict(int)
    for label, s in leaf.items():
        g = parent_map.get(label, label)
        group_k[g] += s["k"]
        group_n[g] += s["n"]

    posterior: dict[str, float] = {}
    for label, s in leaf.items():
        g = parent_map.get(label, label)
        # Hyperprior from group-level empirical mean (Gelman BDA 5.3).
        if group_n[g] > 0:
            p_g = group_k[g] / group_n[g]
        else:
            p_g = s["p_hc"]
        # Combine leaf hardcoded prior with group prior for hyper-mean.
        # Use group mean as the hyper-mean; pseudo-count = prior_strength.
        alpha_h = p_g * prior_strength
        beta_h = (1 - p_g) * prior_strength
        # Leaf posterior: hyper + leaf data (BDA ch.5: pool toward group mean).
        posterior[label] = (alpha_h + s["k"]) / (alpha_h + beta_h + s["n"])
    return posterior


def hierarchical_predict(
    framing: str, contexto: str,
    classify_fn: Callable[[str, str], tuple[float, str]],
    posterior: dict[str, float],
) -> tuple[float, str]:
    """Predict using HBE posterior; falls back to hardcoded prior if unseen."""
    out = classify_fn(framing, contexto)
    p_hc, label = out if isinstance(out, tuple) else (out, "default")
    return posterior.get(label, p_hc), label


def evaluate_hbe(
    test_events: list,
    classify_fn: Callable[[str, str], tuple[float, str]],
    posterior: dict[str, float],
) -> dict:
    """Eval HBE classifier on test events."""
    n = 0
    hits = 0
    brier = 0.0
    for e in test_events:
        framing = e.get("outcome_framing") or e.get("framing", "")
        contexto = e.get("contexto", "")
        real = e.get("outcome_real")
        if real is None:
            continue
        p, _ = hierarchical_predict(framing, contexto, classify_fn, posterior)
        n += 1
        if (p >= 0.5) == bool(real):
            hits += 1
        brier += (p - real) ** 2
    return {
        "n": n, "hits": hits,
        "acc": hits / n if n else 0.0,
        "brier": brier / n if n else 0.0,
    }
