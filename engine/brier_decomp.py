"""
Onda 102: Brier Score decomposition.

Murphy (1973): BS = Reliability − Resolution + Uncertainty
  Reliability: mean squared gap entre confidence e accuracy por bin (lower=better)
  Resolution: spread de accuracy entre bins (higher=better)
  Uncertainty: variância intrínseca p(1-p) (depende só de y)

BS = BRIER score raw.
"""

from __future__ import annotations

from typing import Iterable
import numpy as np


def decompor(
    probs: Iterable[float],
    y: Iterable[int],
    n_bins: int = 10,
) -> dict:
    """Murphy decomposition. Retorna BS = REL - RES + UNC."""
    p = np.array(list(probs), dtype=float)
    yy = np.array(list(y), dtype=float)
    n = p.size
    if n == 0:
        return {"erro": "n=0"}

    y_bar = float(yy.mean())  # base rate

    bins = np.linspace(0, 1, n_bins + 1)
    reliability = 0.0
    resolution = 0.0
    for i in range(n_bins):
        lo, hi = bins[i], bins[i + 1]
        mask = (p >= lo) & (p < hi if i < n_bins - 1 else p <= hi)
        n_k = int(mask.sum())
        if n_k == 0:
            continue
        conf_k = float(p[mask].mean())
        acc_k = float(yy[mask].mean())
        reliability += (n_k / n) * (conf_k - acc_k) ** 2
        resolution += (n_k / n) * (acc_k - y_bar) ** 2

    uncertainty = y_bar * (1 - y_bar)
    bs = float(((p - yy) ** 2).mean())

    return {
        "n": n,
        "n_bins": n_bins,
        "brier_score": bs,
        "reliability": reliability,
        "resolution": resolution,
        "uncertainty": uncertainty,
        "decomp_check": reliability - resolution + uncertainty,
        "decomp_gap": bs - (reliability - resolution + uncertainty),
        "brier_skill_score": 1 - bs / uncertainty if uncertainty > 1e-12 else None,
    }
