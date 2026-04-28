"""Wasserstein distance (Kantorovich-Rubinstein).

1D Earth Mover's Distance: integral of |F_a(x) - F_b(x)| dx, computed
via sorted samples — equal-length closed form is mean(|a_i - b_i|)
on sorted pairs; unequal-length uses the merged-CDF formula.
"""

from __future__ import annotations

from typing import Iterable


def wasserstein_1d(
    samples_a: Iterable[float],
    samples_b: Iterable[float],
) -> float:
    """1D Wasserstein-1 between two empirical samples."""
    a = sorted(float(x) for x in samples_a)
    b = sorted(float(x) for x in samples_b)
    if not a or not b:
        return 0.0
    if len(a) == len(b):
        return sum(abs(x - y) for x, y in zip(a, b)) / len(a)
    # General case: integrate |F_a - F_b| over the union of points.
    pts = sorted(set(a) | set(b))
    na, nb = len(a), len(b)
    ia = ib = 0
    total = 0.0
    for k in range(len(pts) - 1):
        x = pts[k]
        # CDF values strictly to the right of x include all <= x
        while ia < na and a[ia] <= x:
            ia += 1
        while ib < nb and b[ib] <= x:
            ib += 1
        fa = ia / na
        fb = ib / nb
        total += abs(fa - fb) * (pts[k + 1] - pts[k])
    return total


def wasserstein_calibration(
    preds: Iterable[float],
    reals: Iterable[int],
) -> float:
    """W1 between predicted prob distribution and observed outcome distribution."""
    p_list = [float(p) for p in preds]
    y_list = [float(y) for y in reals]
    if not p_list or not y_list:
        return 0.0
    return wasserstein_1d(p_list, y_list)
