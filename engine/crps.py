"""CRPS (Continuous Ranked Probability Score).

For binary outcomes, CRPS = (p - y)^2, equal to per-event Brier.
crps_binary returns the mean CRPS over a sequence.
crps_decomposition returns reliability/resolution/uncertainty
under the Brier-equivalent form for binary forecasts.
"""

from __future__ import annotations

from typing import Iterable


def crps_binary(preds: Iterable[float], reals: Iterable[int]) -> float:
    """Mean CRPS for binary forecasts. Degenerates to Brier."""
    p_list = [float(p) for p in preds]
    y_list = [int(y) for y in reals]
    if len(p_list) != len(y_list):
        raise ValueError("preds and reals length mismatch")
    n = len(p_list)
    if n == 0:
        return 0.0
    return sum((p - y) ** 2 for p, y in zip(p_list, y_list)) / n


def crps_decomposition(preds: Iterable[float], reals: Iterable[int],
                       n_bins: int = 10) -> dict:
    """Murphy-style decomposition for binary CRPS (= Brier)."""
    p = [float(x) for x in preds]
    y = [int(x) for x in reals]
    n = len(p)
    if n == 0:
        return {"n": 0, "crps": 0.0, "reliability": 0.0,
                "resolution": 0.0, "uncertainty": 0.0}
    y_bar = sum(y) / n
    rel = 0.0
    res = 0.0
    edges = [i / n_bins for i in range(n_bins + 1)]
    for i in range(n_bins):
        lo, hi = edges[i], edges[i + 1]
        if i < n_bins - 1:
            idx = [j for j in range(n) if lo <= p[j] < hi]
        else:
            idx = [j for j in range(n) if lo <= p[j] <= hi]
        n_k = len(idx)
        if n_k == 0:
            continue
        conf_k = sum(p[j] for j in idx) / n_k
        acc_k = sum(y[j] for j in idx) / n_k
        rel += (n_k / n) * (conf_k - acc_k) ** 2
        res += (n_k / n) * (acc_k - y_bar) ** 2
    unc = y_bar * (1 - y_bar)
    crps = sum((p[j] - y[j]) ** 2 for j in range(n)) / n
    return {
        "n": n,
        "crps": crps,
        "reliability": rel,
        "resolution": res,
        "uncertainty": unc,
        "decomp_gap": crps - (rel - res + unc),
    }
