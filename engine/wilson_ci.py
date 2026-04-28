"""Wilson (1927) score interval for a binomial proportion.

Better than normal approx for small n / extreme p.
  center = (p_hat + z²/(2n)) / (1 + z²/n)
  half   = z*sqrt(p_hat*(1-p_hat)/n + z²/(4n²)) / (1 + z²/n)
"""

from __future__ import annotations

import math


def _z_from_alpha(alpha: float) -> float:
    """Two-sided normal quantile: returns z s.t. P(|Z| < z) = 1 - alpha."""
    # Solve erf(x/sqrt(2)) = 1 - alpha via Newton.
    target = 1.0 - alpha
    x = 1.0
    for _ in range(80):
        f = math.erf(x / math.sqrt(2)) - target
        # d/dx erf(x/sqrt2) = sqrt(2/pi) * exp(-x²/2)
        fp = math.sqrt(2.0 / math.pi) * math.exp(-(x * x) / 2.0)
        if fp <= 1e-300:
            break
        x_new = x - f / fp
        if abs(x_new - x) < 1e-12:
            x = x_new
            break
        x = x_new
    return x


def wilson_ci(p_hat: float, n: int, alpha: float = 0.05) -> dict:
    """Two-sided Wilson score CI for a Binomial proportion.

    p_hat: observed proportion
    n: sample size
    alpha: significance (default 0.05 -> 95% CI)
    """
    if n <= 0:
        return {"n": n, "p_hat": p_hat, "lo": 0.0, "hi": 1.0,
                "alpha": alpha, "z": 0.0}
    p_hat = max(0.0, min(1.0, float(p_hat)))
    z = _z_from_alpha(alpha)
    z2 = z * z
    denom = 1.0 + z2 / n
    center = (p_hat + z2 / (2 * n)) / denom
    half = z * math.sqrt(p_hat * (1 - p_hat) / n + z2 / (4 * n * n)) / denom
    lo = max(0.0, center - half)
    hi = min(1.0, center + half)
    # Snap floating-point near-boundary endpoints to {0,1} when p_hat is at boundary.
    if p_hat == 0.0:
        lo = 0.0
    if p_hat == 1.0:
        hi = 1.0
    return {
        "n": n,
        "p_hat": p_hat,
        "lo": lo,
        "hi": hi,
        "alpha": alpha,
        "z": z,
    }
