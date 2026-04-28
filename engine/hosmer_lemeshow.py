"""Hosmer-Lemeshow goodness-of-fit chi-square test (1980).

Group by decile of p, compare observed vs expected.
HL = sum (O - E)^2 / (E * (1 - E/n_g)) ~ chi^2(G-2).
"""

from __future__ import annotations

import math
from typing import Callable


def hosmer_lemeshow(
    events: list,
    classify_fn: Callable[[str, str], tuple[float, str]] | Callable,
    n_groups: int = 10,
) -> dict:
    """Compute HL statistic + chi-square approximation.

    Returns dict:
      - chi_square: HL test statistic
      - df: degrees of freedom (n_groups - 2)
      - groups: per-decile observed/expected
      - reject_h0: bool — reject calibration hypothesis at 0.05 level
    """
    pairs = []
    for e in events:
        framing = e.get("outcome_framing") or e.get("framing", "")
        contexto = e.get("contexto", "")
        y = e.get("outcome_real")
        if y is None:
            continue
        out = classify_fn(framing, contexto)
        p = out[0] if isinstance(out, tuple) else out
        pairs.append((p, int(y)))

    if not pairs:
        return {"n": 0, "chi_square": 0.0, "df": 0, "groups": [], "reject_h0": False}

    # Sort by p, split into n_groups roughly-equal-size deciles
    pairs.sort()
    n = len(pairs)
    bin_size = max(1, n // n_groups)

    groups = []
    chi_sq = 0.0

    for g in range(n_groups):
        start = g * bin_size
        end = (g + 1) * bin_size if g < n_groups - 1 else n
        group = pairs[start:end]
        if not group:
            continue
        n_g = len(group)
        observed = sum(y for _, y in group)
        expected = sum(p for p, _ in group)
        # HL component: (O - E)² / (E * (1 - E/n_g))
        denom = expected * (1 - expected / n_g)
        if denom <= 1e-9:
            comp = 0.0
        else:
            comp = (observed - expected) ** 2 / denom
        chi_sq += comp
        groups.append({
            "g": g, "n": n_g,
            "observed": observed,
            "expected": round(expected, 3),
            "mean_p": round(expected / n_g, 3),
            "obs_rate": round(observed / n_g, 3),
            "component": round(comp, 3),
        })

    df = max(1, len(groups) - 2)
    # Wilson-Hilferty chi-square upper-tail approximation:
    # If X² ~ chi²(df), then ((X²/df)^(1/3) - (1 - 2/(9df))) / sqrt(2/(9df)) ~ N(0,1)
    # P(X² > χ²) = P(Z > z) = 1 - Φ(z) = 0.5 * erfc(z/sqrt(2))
    if df > 0 and chi_sq > 0:
        h = (chi_sq / df) ** (1 / 3)
        mu = 1 - 2 / (9 * df)
        sigma = math.sqrt(2 / (9 * df))
        z = (h - mu) / sigma
        p_value = 0.5 * math.erfc(z / math.sqrt(2))
    else:
        p_value = 1.0

    return {
        "n": n,
        "chi_square": round(chi_sq, 3),
        "df": df,
        "p_value_approx": round(p_value, 4),
        "reject_h0": p_value < 0.05,
        "groups": groups,
    }
