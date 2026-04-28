"""
Onda 265: AdaHedge (de Rooij, van Erven, Grünwald, Koolen 2014).

Hedge requires tuning learning rate eta — wrong eta hurts regret bound.
AdaHedge adapts eta automatically using mix loss vs algorithm loss.

Key idea:
  delta_t = mixloss_t - alg_loss_t  (>= 0 always)
  eta_{t+1} = ln(K) / sum delta_t

Mixloss = -log(sum_k w_k * exp(-L_k_t)) (full-information softmin)
Alg loss = sum_k (w_k_t / sum_j w_j) * loss_k_t (linear combo)

Regret bounded O(sqrt(L* log K)) onde L* = best expert cumulative loss.
Adapts to "easy" instances (low L*) tightening regret.

Sem memorization: agg loss state apenas.
"""

from __future__ import annotations

import math
from typing import Callable


class AdaHedge:
    """Adaptive Hedge with auto-tuned learning rate."""

    def __init__(self, expert_names: list[str]):
        self.experts = expert_names
        self.k = len(expert_names)
        self.cum_loss = {name: 0.0 for name in expert_names}
        self.delta_sum = 1e-9  # avoid div by 0
        self.t = 0

    def _eta(self) -> float:
        if self.delta_sum <= 1e-9 or self.k <= 1:
            return 1.0
        return math.log(self.k) / self.delta_sum

    def _weights(self) -> dict[str, float]:
        eta = self._eta()
        scores = {n: -eta * L for n, L in self.cum_loss.items()}
        m = max(scores.values()) if scores else 0
        exps = {n: math.exp(s - m) for n, s in scores.items()}
        total = sum(exps.values())
        return {n: e / total for n, e in exps.items()} if total else {n: 1.0/self.k for n in self.experts}

    def predict(self, expert_preds: dict[str, float]) -> float:
        w = self._weights()
        total_w = sum(w.get(n, 0) for n in expert_preds)
        if total_w == 0:
            return 0.5
        return sum(w[n] * p / total_w for n, p in expert_preds.items() if n in w)

    def update(self, expert_preds: dict[str, float], y: int):
        """Update with brier loss + adapt eta."""
        self.t += 1
        w = self._weights()
        eta = self._eta()

        # Per-expert losses
        losses = {n: (p - y) ** 2 for n, p in expert_preds.items() if n in w}

        # Algorithm loss (weighted prediction loss)
        p_alg = sum(w[n] * p for n, p in expert_preds.items() if n in w)
        alg_loss = (p_alg - y) ** 2

        # Mix loss = -ln(sum_k w_k * exp(-eta * loss_k)) / eta
        if eta > 1e-9:
            inner = sum(w[n] * math.exp(-eta * L) for n, L in losses.items())
            mix_loss = -math.log(max(inner, 1e-30)) / eta
        else:
            mix_loss = alg_loss  # degenerate

        delta = max(0.0, alg_loss - mix_loss)
        self.delta_sum += delta

        for n, L in losses.items():
            self.cum_loss[n] += L


def evaluate_adahedge(
    events: list,
    expert_fns: dict[str, Callable[[str, str], float]],
) -> dict:
    """Run AdaHedge online over events."""
    agg = AdaHedge(list(expert_fns.keys()))
    n = hits = 0
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
        agg.update(preds, int(y))

    best_name = min(agg.cum_loss.items(), key=lambda x: x[1])[0]
    return {
        "n": n, "hits": hits,
        "acc": hits / n if n else 0,
        "brier": brier / n if n else 0,
        "final_eta": agg._eta(),
        "final_weights": agg._weights(),
        "best_expert": best_name,
        "best_loss": agg.cum_loss[best_name] / n if n else 0,
    }
