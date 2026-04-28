"""
Onda 259: Hedge algorithm (Freund & Schapire 1997) — online expert combination.

Setting: K experts predict each round; observe outcome; pay loss; update.
Goal: regret vs best expert in hindsight bounded by O(sqrt(T log K)).

Update rule (multiplicative weights):
  w_k(t+1) = w_k(t) * exp(-eta * loss_k(t))

Prediction: p_t = sum_k (w_k(t) / sum_j w_j(t)) * p_k(t)

Loss: |p_k - y| (linear) ou (p_k - y)² (quadratic / Brier).

Aplicação: combine 5+ classifiers/predictors online sem hyperparam tuning;
adapta automaticamente ao expert melhor.

Sem memorization: usa só agg loss history, não eventos individuais.
"""

from __future__ import annotations

import math
from typing import Callable


class HedgeAggregator:
    """Online aggregator over K experts via multiplicative weights."""

    def __init__(self, expert_names: list[str], eta: float = 0.5):
        self.experts = expert_names
        self.k = len(expert_names)
        self.eta = eta
        self.weights = {name: 1.0 for name in expert_names}
        self.cumulative_loss = {name: 0.0 for name in expert_names}
        self.history: list[dict] = []

    def predict(self, expert_preds: dict[str, float]) -> float:
        """Weighted average of expert predictions."""
        total_w = sum(self.weights[n] for n in expert_preds if n in self.weights)
        if total_w == 0:
            return 0.5
        return sum(
            self.weights[n] * p / total_w
            for n, p in expert_preds.items() if n in self.weights
        )

    def update(self, expert_preds: dict[str, float], y: int, loss_fn: str = "brier"):
        """Update weights given true outcome y."""
        for name, p in expert_preds.items():
            if name not in self.weights:
                continue
            if loss_fn == "brier":
                loss = (p - y) ** 2
            elif loss_fn == "linear":
                loss = abs(p - y)
            else:
                raise ValueError(f"unknown loss_fn: {loss_fn}")
            self.weights[name] *= math.exp(-self.eta * loss)
            self.cumulative_loss[name] += loss
        self.history.append({"y": y, "preds": dict(expert_preds)})

    def normalized_weights(self) -> dict[str, float]:
        total = sum(self.weights.values())
        return {n: w / total for n, w in self.weights.items()} if total else {}


def evaluate_hedge(
    events: list,
    expert_fns: dict[str, Callable[[str, str], float]],
    eta: float = 0.5,
    loss_fn: str = "brier",
) -> dict:
    """Run hedge online over events. Return cumulative metrics."""
    agg = HedgeAggregator(list(expert_fns.keys()), eta=eta)
    n = 0
    hits = 0
    brier = 0.0

    for e in events:
        framing = e.get("outcome_framing") or e.get("framing", "")
        contexto = e.get("contexto", "")
        y = e.get("outcome_real")
        if y is None:
            continue
        preds = {name: fn(framing, contexto) for name, fn in expert_fns.items()}
        p = agg.predict(preds)
        n += 1
        if (p >= 0.5) == bool(y):
            hits += 1
        brier += (p - y) ** 2
        agg.update(preds, int(y), loss_fn=loss_fn)

    best_expert = min(agg.cumulative_loss.items(), key=lambda x: x[1])
    return {
        "n": n, "hits": hits,
        "acc": hits / n if n else 0,
        "brier": brier / n if n else 0,
        "weights": agg.normalized_weights(),
        "best_expert": best_expert[0],
        "best_loss": best_expert[1] / n if n else 0,
        "regret_vs_best": (brier / n - best_expert[1] / n) if n else 0,
    }
