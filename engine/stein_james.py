"""Stein-James shrinkage estimator (Stein & James 1961).

For d>=3 normal means, shrinking toward the grand mean strictly dominates
the MLE in total MSE. Useful for shrinking per-category empirical priors.
"""

from __future__ import annotations

from typing import Iterable


def stein_james_shrink(
    estimates: Iterable[float],
    variances: Iterable[float],
) -> list[float]:
    """James-Stein shrinkage toward grand mean.

    theta_i_shrunk = theta_grand
        + max(0, 1 - (d-2) * sigma2 / sum (theta_i - theta_grand)^2)
        * (theta_i - theta_grand)

    sigma2 is the average per-coordinate variance.
    Returns input unchanged when d<3 (no admissibility gain).
    """
    theta = [float(x) for x in estimates]
    var = [float(v) for v in variances]
    d = len(theta)
    if d == 0 or len(var) != d:
        return theta
    if d < 3:
        return theta

    grand = sum(theta) / d
    sigma2 = sum(var) / d
    ss = sum((t - grand) ** 2 for t in theta)
    if ss <= 0:
        return [grand] * d
    factor = 1.0 - (d - 2) * sigma2 / ss
    if factor < 0.0:
        factor = 0.0  # positive-part Stein
    return [grand + factor * (t - grand) for t in theta]


def apply_stein_to_eb_priors(
    eb_priors: dict[str, float],
    n_per_cat: dict[str, int],
) -> dict[str, float]:
    """Shrink empirical-Bayes priors toward weighted grand mean.

    Variance per coord uses Bernoulli p*(1-p)/n_cat.
    Grand mean is sample-size-weighted across categories.
    """
    if not eb_priors:
        return {}
    labels = list(eb_priors.keys())
    d = len(labels)
    if d < 3:
        return dict(eb_priors)

    total_n = sum(max(1, n_per_cat.get(lbl, 1)) for lbl in labels)
    grand = sum(
        eb_priors[lbl] * max(1, n_per_cat.get(lbl, 1)) for lbl in labels
    ) / total_n

    theta = [eb_priors[lbl] for lbl in labels]
    var = [
        max(eb_priors[lbl] * (1 - eb_priors[lbl]), 1e-6)
        / max(1, n_per_cat.get(lbl, 1))
        for lbl in labels
    ]
    sigma2 = sum(var) / d
    ss = sum((t - grand) ** 2 for t in theta)
    if ss <= 0:
        return {lbl: grand for lbl in labels}
    factor = 1.0 - (d - 2) * sigma2 / ss
    if factor < 0.0:
        factor = 0.0
    return {
        lbl: max(0.0, min(1.0, grand + factor * (eb_priors[lbl] - grand)))
        for lbl in labels
    }
