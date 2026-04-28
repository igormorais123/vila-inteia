"""Randomized PIT histogram diagnostic (Czado et al. 2009).

Bin u = randomized_pit(p, y) into n_bins, test uniformity via chi-square.
U-shape = underconfident, inverted-U = overconfident, skew = biased.
"""

from __future__ import annotations

import math
from typing import Callable


def randomized_pit(p: float, y: int, rng_value: float) -> float:
    """Randomized PIT for binary outcome.

    rng_value: pre-sampled uniform [0,1] for reproducibility.
    Returns u in [0, 1].

    Definition (Czado et al. 2009):
    F_lower = P(Y < y) ; F_upper = P(Y ≤ y)
    u = F_lower + rng_value * (F_upper - F_lower)
    """
    if y == 1:
        # F_lower = 1-p (P(Y<1) = P(Y=0) = 1-p), F_upper = 1
        return (1 - p) + rng_value * p
    # y == 0: F_lower = 0, F_upper = 1-p
    return rng_value * (1 - p)


def pit_histogram(
    events: list,
    classify_fn: Callable[[str, str], tuple[float, float]] | Callable,
    n_bins: int = 10,
    seed: int = 42,
) -> dict:
    """Compute PIT histogram + uniformity test.

    classify_fn: returns (prob, label) OR just prob (handled).
    Returns dict with bins, counts, chi_square, p_value (chi2 approx),
    diagnosis string.
    """
    import random
    rng = random.Random(seed)

    pits = []
    for e in events:
        framing = e.get("outcome_framing") or e.get("framing", "")
        contexto = e.get("contexto", "")
        y = e.get("outcome_real")
        if y is None:
            continue
        out = classify_fn(framing, contexto)
        p = out[0] if isinstance(out, tuple) else out
        u = randomized_pit(p, int(y), rng.random())
        pits.append(u)

    if not pits:
        return {"n": 0, "bins": [], "counts": [], "chi_square": 0,
                "diagnosis": "no data"}

    # Histogram
    counts = [0] * n_bins
    for u in pits:
        idx = min(n_bins - 1, int(u * n_bins))
        counts[idx] += 1

    expected = len(pits) / n_bins
    chi_sq = sum((c - expected) ** 2 / expected for c in counts) if expected else 0.0

    # Diagnose shape
    n_per_bin = [c / len(pits) for c in counts]
    edges = [(i + 0.5) / n_bins for i in range(n_bins)]  # centers
    # Linear regression slope (skew test)
    mean_x = sum(edges) / n_bins
    mean_y = sum(n_per_bin) / n_bins
    num = sum((edges[i] - mean_x) * (n_per_bin[i] - mean_y) for i in range(n_bins))
    den = sum((edges[i] - mean_x) ** 2 for i in range(n_bins))
    slope = num / den if den else 0.0

    # U vs inv-U: compare ends vs middle
    ends = (counts[0] + counts[-1]) / 2
    middle = sum(counts[n_bins // 2 - 1: n_bins // 2 + 1]) / 2
    u_score = (ends - middle) / max(expected, 1)

    if abs(slope) > 0.3:
        diag = "skewed"
    elif u_score > 0.3:
        diag = "underconfident (U-shape)"
    elif u_score < -0.3:
        diag = "overconfident (inverted-U)"
    else:
        diag = "well-calibrated"

    return {
        "n": len(pits),
        "n_bins": n_bins,
        "counts": counts,
        "expected_per_bin": expected,
        "chi_square": chi_sq,
        "slope": slope,
        "u_score": u_score,
        "diagnosis": diag,
    }
