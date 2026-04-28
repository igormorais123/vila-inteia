"""Fisher (1932) combined p-value (a.k.a. Aitkin's combined test).

chi² = -2 * sum log(p_i),  df = 2k
Combined p = P(chi²(2k) > observed).
"""

from __future__ import annotations

import math
from typing import Iterable


def _chi2_sf(x: float, df: int) -> float:
    """P(X > x) for X ~ chi²(df). Wilson-Hilferty cubic-root approx."""
    if df <= 0 or x <= 0:
        return 1.0
    h = (x / df) ** (1.0 / 3.0)
    mu = 1.0 - 2.0 / (9.0 * df)
    sigma = math.sqrt(2.0 / (9.0 * df))
    if sigma <= 0:
        return 1.0 if x < df else 0.0
    z = (h - mu) / sigma
    # P(Z > z) using erfc
    return 0.5 * math.erfc(z / math.sqrt(2.0))


def aitkin_p(p_values: Iterable[float],
             clip_min: float = 1e-12) -> dict:
    """Combine k independent p-values via Fisher's method.

    p_values: iterable of p_i in (0, 1].
    clip_min: floor to avoid log(0).
    """
    ps = []
    for p in p_values:
        pf = float(p)
        if pf <= 0:
            pf = clip_min
        if pf > 1:
            pf = 1.0
        ps.append(pf)
    k = len(ps)
    if k == 0:
        return {"k": 0, "chi_square": 0.0, "df": 0, "p_combined": 1.0}
    chi2 = -2.0 * sum(math.log(p) for p in ps)
    df = 2 * k
    p_combined = _chi2_sf(chi2, df)
    return {
        "k": k,
        "chi_square": chi2,
        "df": df,
        "p_combined": p_combined,
    }
