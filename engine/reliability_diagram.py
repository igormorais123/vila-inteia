"""
Onda 101: reliability diagram (calibration curve).

Retorna bin_center, bin_confidence, bin_accuracy, bin_count.
Frontend renderiza como scatter/line pra diagnosticar calibração.
"""

from __future__ import annotations

import math
from typing import Iterable
import numpy as np


def _wilson_ci(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    """Wilson score interval for binomial proportion."""
    if n == 0:
        return (0.0, 1.0)
    p_hat = k / n
    denom = 1.0 + z * z / n
    center = (p_hat + z * z / (2 * n)) / denom
    margin = (z * math.sqrt(p_hat * (1 - p_hat) / n + z * z / (4 * n * n))) / denom
    lo = max(0.0, center - margin)
    hi = min(1.0, center + margin)
    return (lo, hi)


def reliability_diagram(
    preds: list[float],
    reals: list[int],
    n_bins: int = 10,
) -> list[dict]:
    """Bins preds; returns list of dicts per non-empty bin with Wilson 95% CI."""
    n = len(reals)
    if n == 0 or len(preds) != n or n_bins < 1:
        return []

    bins: list[list[tuple[float, int]]] = [[] for _ in range(n_bins)]
    for p, y in zip(preds, reals):
        idx = min(n_bins - 1, max(0, int(p * n_bins)))
        bins[idx].append((p, int(y)))

    out = []
    for i, items in enumerate(bins):
        if not items:
            continue
        ni = len(items)
        mean_p = sum(p for p, _ in items) / ni
        k = sum(y for _, y in items)
        observed = k / ni
        lo, hi = _wilson_ci(k, ni)
        out.append({
            "bin": i,
            "bin_lo": i / n_bins,
            "bin_hi": (i + 1) / n_bins,
            "mean_p": mean_p,
            "observed_rate": observed,
            "n": ni,
            "ci_lo": lo,
            "ci_hi": hi,
        })
    return out


def reliability(
    probs: Iterable[float],
    y: Iterable[int],
    n_bins: int = 10,
) -> dict:
    """
    Para cada bin [lo, hi): confidence média = mean(probs in bin),
    accuracy = mean(y in bin). Diagonal perfeita y=x → calibrado.
    """
    p = np.array(list(probs), dtype=float)
    y = np.array(list(y), dtype=float)
    if p.size == 0:
        return {"bins": [], "n": 0}

    bins = np.linspace(0, 1, n_bins + 1)
    out = []
    for i in range(n_bins):
        lo, hi = bins[i], bins[i + 1]
        mask = (p >= lo) & (p < hi if i < n_bins - 1 else p <= hi)
        n = int(mask.sum())
        if n == 0:
            out.append({
                "bin_idx": i, "lo": float(lo), "hi": float(hi),
                "center": float((lo + hi) / 2),
                "n": 0, "confidence": None, "accuracy": None,
            })
            continue
        out.append({
            "bin_idx": i,
            "lo": float(lo), "hi": float(hi),
            "center": float((lo + hi) / 2),
            "n": n,
            "confidence": float(p[mask].mean()),
            "accuracy": float(y[mask].mean()),
            "gap": float(p[mask].mean() - y[mask].mean()),
        })
    return {"n": int(p.size), "n_bins": n_bins, "bins": out}


def reliability_ascii(
    probs: Iterable[float],
    y: Iterable[int],
    n_bins: int = 10,
    width: int = 40,
) -> str:
    """Rendering ASCII do reliability diagram pra log/terminal."""
    d = reliability(probs, y, n_bins)
    lines = [f"Reliability (n={d['n']}, {d['n_bins']} bins):",
             "  conf  acc   n    bar"]
    for b in d["bins"]:
        if b["n"] == 0:
            lines.append(f"  {b['center']:.2f}  —    0")
            continue
        c = b["confidence"] or 0
        a = b["accuracy"] or 0
        gap = c - a
        bar_c = int(c * width)
        bar_a = int(a * width)
        vis = "".join("█" if i < bar_a else ("▁" if i < bar_c else " ")
                       for i in range(width))
        mark = "✓" if abs(gap) < 0.05 else ("↑" if gap > 0 else "↓")
        lines.append(f"  {c:.2f}  {a:.2f}  {b['n']:3d}  {vis}{mark}")
    return "\n".join(lines)
