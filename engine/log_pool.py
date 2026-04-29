"""Log-linear pooling (geometric-mean) of probabilistic forecasts.

For K forecasters with probs p_k and weights w_k (sum=1):
  p_pool ∝ ∏ p_k^w_k     /     [∏ p_k^w_k + ∏ (1-p_k)^w_k]

Equivalent to weighted average of logits:
  logit(p_pool) = sum w_k · logit(p_k)

References: Genest & Zidek 1986, Allard et al. 2012.
"""

from __future__ import annotations

import math


def _logit(p: float, eps: float = 1e-9) -> float:
    p = max(eps, min(1 - eps, p))
    return math.log(p / (1 - p))


def _sigmoid(x: float) -> float:
    if x >= 0:
        z = math.exp(-x)
        return 1.0 / (1.0 + z)
    z = math.exp(x)
    return z / (1.0 + z)


def log_pool(probs: dict[str, float], weights: dict[str, float] | None = None) -> float:
    """Log-linear pool of binary probabilities."""
    if not probs:
        return 0.5
    if weights is None:
        weights = {k: 1.0 for k in probs}
    total_w = sum(weights.get(k, 0) for k in probs)
    if total_w <= 0:
        return 0.5
    pooled_logit = sum(weights.get(k, 0) / total_w * _logit(p)
                       for k, p in probs.items())
    return _sigmoid(pooled_logit)


def log_pool_predict(p_a: float, p_b: float, w_a: float = 0.5) -> float:
    """Two-forecaster shortcut. w_a = weight on first, 1-w_a on second."""
    return _sigmoid(w_a * _logit(p_a) + (1 - w_a) * _logit(p_b))
