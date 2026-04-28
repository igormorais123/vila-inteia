"""Kalman filter for binary forecasts (Kalman 1960).

Track latent logit state with Gaussian process+observation noise.
Observation: 0/1 mapped to logit space via pseudo-obs (Gaussian approx
of Bernoulli around current sigmoid mean).
"""

from __future__ import annotations

import math


def _sigmoid(z: float) -> float:
    if z >= 0:
        ez = math.exp(-z)
        return 1.0 / (1.0 + ez)
    ez = math.exp(z)
    return ez / (1.0 + ez)


def _logit(p: float) -> float:
    p = max(1e-6, min(1 - 1e-6, p))
    return math.log(p / (1 - p))


class KalmanBinaryFilter:
    """1-D Kalman over logit of binary outcome probability."""

    def __init__(self, initial_logit: float = 0.0,
                 Q: float = 0.01, R: float = 1.0,
                 initial_var: float = 1.0):
        self.x = float(initial_logit)
        self.P = float(initial_var)
        self.Q = float(Q)
        self.R = float(R)

    def predict(self) -> float:
        """Time update: x stays (random walk), P grows by Q. Returns prob."""
        self.P += self.Q
        return _sigmoid(self.x)

    def update(self, y: int) -> float:
        """Measurement update with pseudo-observation in logit space.

        Maps 0/1 to bounded logit (+/- 6) and applies linear Kalman gain.
        """
        z = 6.0 if int(y) == 1 else -6.0
        K = self.P / (self.P + self.R)
        self.x = self.x + K * (z - self.x)
        self.P = (1.0 - K) * self.P
        return _sigmoid(self.x)

    def prob(self) -> float:
        return _sigmoid(self.x)


def run_kalman(outcomes: list[int],
               initial_logit: float = 0.0,
               Q: float = 0.01, R: float = 1.0) -> list[float]:
    """Returns posterior prob after each observation."""
    kf = KalmanBinaryFilter(initial_logit=initial_logit, Q=Q, R=R)
    out = []
    for y in outcomes:
        kf.predict()
        out.append(kf.update(int(y)))
    return out


def evaluate_kalman(outcomes: list[int],
                    Q: float = 0.01, R: float = 1.0) -> dict:
    """Run kalman, score predict-then-update brier (one-step-ahead)."""
    kf = KalmanBinaryFilter(Q=Q, R=R)
    n = hits = 0
    brier = 0.0
    for y in outcomes:
        p = kf.predict()
        n += 1
        if (p >= 0.5) == bool(y):
            hits += 1
        brier += (p - y) ** 2
        kf.update(int(y))
    return {
        "n": n, "hits": hits,
        "acc": hits / n if n else 0.0,
        "brier": brier / n if n else 0.0,
        "final_logit": kf.x,
        "final_prob": kf.prob(),
        "final_var": kf.P,
    }
