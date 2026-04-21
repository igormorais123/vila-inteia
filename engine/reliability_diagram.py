"""
Onda 101: reliability diagram (calibration curve).

Retorna bin_center, bin_confidence, bin_accuracy, bin_count.
Frontend renderiza como scatter/line pra diagnosticar calibração.
"""

from __future__ import annotations

from typing import Iterable
import numpy as np


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
