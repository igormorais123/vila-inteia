"""Online Gradient Descent (Zinkevich 2003).

Convex online learning, regret O(sqrt(T)).
Update: w_{t+1} = proj_simplex(w_t - eta_t * grad), eta_t = 1/sqrt(t).
For prob aggregation: w on simplex over K experts, brier loss gradient.
"""

from __future__ import annotations

import math
from typing import Callable


def _project_simplex(v: list[float]) -> list[float]:
    """Euclidean projection onto probability simplex (Wang & Carreira-Perpinan 2013)."""
    n = len(v)
    if n == 0:
        return []
    u = sorted(v, reverse=True)
    cssv = 0.0
    rho = 0
    theta = 0.0
    for i, ui in enumerate(u, start=1):
        cssv += ui
        cand = (cssv - 1.0) / i
        if ui - cand > 0:
            rho = i
            theta = cand
    return [max(0.0, x - theta) for x in v]


class OGDAggregator:
    """OGD over simplex of K experts, brier loss."""

    def __init__(self, K: int, lr_schedule: str = "sqrt", lr_const: float = 0.5):
        if K <= 0:
            raise ValueError("K must be > 0")
        self.K = K
        self.lr_schedule = lr_schedule
        self.lr_const = lr_const
        self.w = [1.0 / K] * K
        self.t = 0

    def _eta(self) -> float:
        if self.lr_schedule == "sqrt":
            return 1.0 / math.sqrt(self.t)
        if self.lr_schedule == "const":
            return self.lr_const
        if self.lr_schedule == "log":
            return 1.0 / math.log(self.t + 1.0)
        raise ValueError(f"unknown lr_schedule: {self.lr_schedule}")

    def predict(self, expert_probs: list[float]) -> float:
        """Weighted combination of expert probs."""
        if len(expert_probs) != self.K:
            raise ValueError(f"expected {self.K} expert probs, got {len(expert_probs)}")
        return sum(self.w[i] * expert_probs[i] for i in range(self.K))

    def update(self, expert_probs: list[float], y: int) -> None:
        """Brier-loss gradient step + simplex projection."""
        if len(expert_probs) != self.K:
            raise ValueError(f"expected {self.K} expert probs, got {len(expert_probs)}")
        self.t += 1
        eta = self._eta()
        p_hat = self.predict(expert_probs)
        # d/dw_i (p_hat - y)^2 = 2*(p_hat - y)*expert_probs[i]
        diff = p_hat - y
        grad = [2.0 * diff * expert_probs[i] for i in range(self.K)]
        new_w = [self.w[i] - eta * grad[i] for i in range(self.K)]
        self.w = _project_simplex(new_w)


def evaluate_ogd(
    events: list,
    expert_fns: dict[str, Callable[[str, str], float]],
    lr_schedule: str = "sqrt",
) -> dict:
    """Run OGD online over events. Cumulative brier + final weights."""
    names = list(expert_fns.keys())
    K = len(names)
    agg = OGDAggregator(K=K, lr_schedule=lr_schedule)
    n = hits = 0
    brier = 0.0
    cum_loss = {name: 0.0 for name in names}

    for e in events:
        framing = e.get("outcome_framing") or e.get("framing", "")
        contexto = e.get("contexto", "")
        y = e.get("outcome_real")
        if y is None:
            continue
        probs = [expert_fns[name](framing, contexto) for name in names]
        # unpack tuple outputs
        probs = [pi[0] if isinstance(pi, tuple) else pi for pi in probs]
        p = agg.predict(probs)
        n += 1
        if (p >= 0.5) == bool(y):
            hits += 1
        brier += (p - y) ** 2
        for name, pi in zip(names, probs):
            cum_loss[name] += (pi - y) ** 2
        agg.update(probs, int(y))

    best_name = min(cum_loss.items(), key=lambda kv: kv[1])[0] if cum_loss else None
    final_weights = {names[i]: agg.w[i] for i in range(K)}
    return {
        "n": n, "hits": hits,
        "acc": hits / n if n else 0.0,
        "brier": brier / n if n else 0.0,
        "final_weights": final_weights,
        "best_expert": best_name,
        "best_loss": cum_loss[best_name] / n if (n and best_name) else 0.0,
    }
