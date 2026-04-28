"""Bayesian Model Averaging (Hoeting et al. 1999).

Average predictions weighted by posterior model probabilities P(M_k | D).
P(M_k | D) ∝ P(D | M_k) * P(M_k)
P(D | M_k) = Π_i p_ki^y_i * (1-p_ki)^(1-y_i)
"""

from __future__ import annotations

import math


def _log_likelihood(preds: list[float], reals: list[int]) -> float:
    """Log P(D | M) = Σ y log p + (1-y) log(1-p) com clip."""
    eps = 1e-12
    s = 0.0
    for p, y in zip(preds, reals):
        p = min(1 - eps, max(eps, float(p)))
        s += y * math.log(p) + (1 - y) * math.log(1 - p)
    return s


def bma_predict(
    model_predictions: dict[str, list],
    reals: list,
    prior_weights: dict | None = None,
) -> dict:
    """Posterior model probs + weighted average preds."""
    if not model_predictions:
        return {"erro": "empty"}
    n = len(reals)
    if any(len(v) != n for v in model_predictions.values()):
        return {"erro": "shape mismatch"}

    names = list(model_predictions.keys())
    if prior_weights is None:
        prior_weights = {k: 1.0 / len(names) for k in names}
    else:
        s = sum(prior_weights.get(k, 0.0) for k in names)
        if s <= 0:
            prior_weights = {k: 1.0 / len(names) for k in names}
        else:
            prior_weights = {k: prior_weights.get(k, 0.0) / s for k in names}

    log_lik = {k: _log_likelihood(model_predictions[k], reals) for k in names}
    log_post = {k: log_lik[k] + math.log(max(prior_weights[k], 1e-300)) for k in names}

    m = max(log_post.values())
    exps = {k: math.exp(log_post[k] - m) for k in names}
    z = sum(exps.values())
    posterior = {k: exps[k] / z for k in names}

    avg_preds = []
    for i in range(n):
        avg_preds.append(sum(posterior[k] * model_predictions[k][i] for k in names))

    return {
        "predictions": avg_preds,
        "posterior_weights": posterior,
        "log_likelihood": log_lik,
        "prior_weights": prior_weights,
        "n": n,
    }
