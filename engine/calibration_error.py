"""Expected and Maximum Calibration Error (Naeini, Cooper & Hauskrecht 2015).

ECE = sum_b (n_b / n) * |obs_b - mean_p_b|
MCE = max_b |obs_b - mean_p_b|

Adaptive ECE uses equal-frequency bins (each ~n/B samples) instead of
equal-width, reducing bias on skewed forecast distributions.
"""

from __future__ import annotations

from typing import Iterable


def _bin_stats(pairs: list[tuple[float, int]],
               edges: list[float]) -> list[dict]:
    """Group (p, y) into bins using sorted edges; returns per-bin stats."""
    bins: list[list[tuple[float, int]]] = [[] for _ in range(len(edges) - 1)]
    for p, y in pairs:
        # Find bin: lower-inclusive, upper-inclusive only for last
        idx = 0
        for j in range(len(edges) - 1):
            lo, hi = edges[j], edges[j + 1]
            if (lo <= p < hi) or (j == len(edges) - 2 and p == hi):
                idx = j
                break
        bins[idx].append((p, y))

    out = []
    for b in bins:
        if not b:
            out.append({"n": 0, "mean_p": 0.0, "obs": 0.0, "gap": 0.0})
            continue
        n = len(b)
        mean_p = sum(p for p, _ in b) / n
        obs = sum(y for _, y in b) / n
        out.append({
            "n": n,
            "mean_p": mean_p,
            "obs": obs,
            "gap": abs(obs - mean_p),
        })
    return out


def calibration_errors(
    preds: Iterable[float],
    reals: Iterable[int],
    n_bins: int = 10,
    adaptive: bool = False,
) -> dict:
    """Compute ECE and MCE.

    adaptive=True: equal-frequency bins; else equal-width on [0, 1].
    """
    pairs = [(float(p), int(y)) for p, y in zip(preds, reals)]
    n = len(pairs)
    if n == 0:
        return {"n": 0, "ece": None, "mce": None,
                "n_bins": n_bins, "bins": [], "adaptive": adaptive}

    n_bins = max(1, int(n_bins))

    if adaptive:
        sorted_pairs = sorted(pairs)
        # Quantile edges
        edges = [0.0]
        for b in range(1, n_bins):
            idx = min(n - 1, int(round(b * n / n_bins)))
            edges.append(sorted_pairs[idx][0])
        edges.append(1.0)
        # Dedup monotonically
        cleaned = [edges[0]]
        for e in edges[1:]:
            if e > cleaned[-1] + 1e-12:
                cleaned.append(e)
            elif e == 1.0 and cleaned[-1] < 1.0:
                cleaned.append(1.0)
        if cleaned[-1] < 1.0:
            cleaned.append(1.0)
        edges = cleaned
    else:
        edges = [i / n_bins for i in range(n_bins + 1)]

    stats = _bin_stats(pairs, edges)
    ece = sum((b["n"] / n) * b["gap"] for b in stats)
    mce = max((b["gap"] for b in stats if b["n"] > 0), default=0.0)

    return {
        "n": n,
        "ece": ece,
        "mce": mce,
        "n_bins": len(stats),
        "bins": stats,
        "adaptive": adaptive,
    }
