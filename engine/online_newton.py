"""Online Newton Step (Hazan, Agarwal, Kale 2007).

Second-order online learning. Regret O(log T) for exp-concave losses.
Update: A_t = A_{t-1} + g g^T, w_t = w_{t-1} - eta * A_t^{-1} g.
1D scalar-prob aggregation: A becomes scalar Hessian accumulator.
"""

from __future__ import annotations

import math
from typing import Callable

from engine._pred_utils import pairs_from_events


def _sigmoid(z: float) -> float:
    if z >= 0:
        ez = math.exp(-z)
        return 1.0 / (1.0 + ez)
    ez = math.exp(z)
    return ez / (1.0 + ez)


class OnlineNewton:
    """ONS over scalar logit param via Hessian-accumulator update."""

    def __init__(self, d: int = 1, eta: float = 1.0, eps: float = 1.0):
        self.d = d
        self.eta = eta
        self.w = [0.0] * d
        # diagonal Hessian approx (scalar per dim)
        self.A = [eps] * d

    def predict(self, x: list[float] | float) -> float:
        """Sigmoid(w . x). Scalar x allowed when d=1."""
        if isinstance(x, (int, float)):
            x = [float(x)] * self.d
        z = sum(self.w[i] * x[i] for i in range(self.d))
        return _sigmoid(z)

    def update(self, x: list[float] | float, y: int,
               gradient: list[float] | float | None = None) -> None:
        """Update Hessian + weights. gradient optional (else log-loss grad)."""
        if isinstance(x, (int, float)):
            x = [float(x)] * self.d
        if gradient is None:
            p = self.predict(x)
            g = [(p - y) * x[i] for i in range(self.d)]
        elif isinstance(gradient, (int, float)):
            g = [float(gradient)] * self.d
        else:
            g = list(gradient)
        for i in range(self.d):
            self.A[i] += g[i] * g[i]
            self.w[i] -= self.eta * g[i] / self.A[i]


def online_newton_aggregator(
    predictions: list[float], outcomes: list[int], eta: float = 1.0
) -> dict:
    """Run ONS over scalar prob stream. Returns metrics + final logit."""
    if len(predictions) != len(outcomes):
        raise ValueError("predictions/outcomes length mismatch")
    ons = OnlineNewton(d=1, eta=eta)
    n = hits = 0
    brier = 0.0
    for p_in, y in zip(predictions, outcomes):
        # logit of input prediction as feature
        p_in = max(1e-6, min(1 - 1e-6, p_in))
        x = math.log(p_in / (1 - p_in))
        p_hat = ons.predict(x)
        n += 1
        if (p_hat >= 0.5) == bool(y):
            hits += 1
        brier += (p_hat - y) ** 2
        ons.update(x, int(y))
    return {
        "n": n, "hits": hits,
        "acc": hits / n if n else 0.0,
        "brier": brier / n if n else 0.0,
        "final_w": list(ons.w),
        "final_A": list(ons.A),
    }


def evaluate_ons(
    events: list,
    classify_fn: Callable[[str, str], float] | Callable[[str, str], tuple],
    eta: float = 1.0,
) -> dict:
    """Run ONS over events using classify_fn output as scalar feature."""
    pairs = pairs_from_events(events, classify_fn)
    preds = [p for p, _ in pairs]
    outs = [y for _, y in pairs]
    return online_newton_aggregator(preds, outs, eta=eta)
