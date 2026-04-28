"""Bias-Variance decomposition para classifier binário.

MSE = Bias² + Variance + Irreducible noise
- bias² = (mean_p - true_rate)²
- variance via bootstrap resampling de eventos
- noise = y(1-y) intrínseco (estimado por base rate)
"""

from __future__ import annotations

import random


def bias_variance_decomp(
    preds: list[float],
    reals: list,
    n_bootstrap: int = 200,
    seed: int = 42,
) -> dict:
    """Bias² + Var + Noise decomposition via bootstrap."""
    n = len(preds)
    if n == 0 or len(reals) != n:
        return {"erro": "empty or mismatch"}

    rng = random.Random(seed)
    p_arr = [float(x) for x in preds]
    y_arr = [float(x) for x in reals]

    mean_p = sum(p_arr) / n
    true_rate = sum(y_arr) / n
    bias_sq = (mean_p - true_rate) ** 2

    # Bootstrap: resample (p, y) pairs, record bootstrap mean prediction
    boot_means = []
    boot_mse = []
    for _ in range(n_bootstrap):
        idx = [rng.randrange(n) for _ in range(n)]
        bp = [p_arr[i] for i in idx]
        by = [y_arr[i] for i in idx]
        boot_means.append(sum(bp) / n)
        boot_mse.append(sum((bp[i] - by[i]) ** 2 for i in range(n)) / n)

    if n_bootstrap > 0:
        m_b = sum(boot_means) / n_bootstrap
        variance = sum((b - m_b) ** 2 for b in boot_means) / n_bootstrap
    else:
        variance = 0.0

    mse = sum((p_arr[i] - y_arr[i]) ** 2 for i in range(n)) / n
    noise = true_rate * (1.0 - true_rate)

    return {
        "n": n,
        "n_bootstrap": n_bootstrap,
        "mean_pred": mean_p,
        "true_rate": true_rate,
        "bias_sq": bias_sq,
        "variance": variance,
        "noise": noise,
        "mse": mse,
        "decomp_check": bias_sq + variance + noise,
        "decomp_gap": mse - (bias_sq + variance + noise),
    }
