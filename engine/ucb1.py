"""UCB1 (Auer, Cesa-Bianchi, Fischer 2002) for stochastic bandits.

Index: UCB_k(t) = mean_k + sqrt(2 log t / n_k). Optimism in face of
uncertainty. Sublinear regret O(sqrt(K T log T)).
"""

from __future__ import annotations

import math
from typing import Callable

from engine._pred_utils import unpack_pred


class UCB1:
    """UCB1 stochastic-bandit selector."""

    def __init__(self, n_arms: int):
        if n_arms < 1:
            raise ValueError("n_arms must be >= 1")
        self.n_arms = n_arms
        self.counts = [0] * n_arms
        self.sums = [0.0] * n_arms
        self.t = 0

    def select(self) -> int:
        """Pull each arm once first; then argmax of UCB index."""
        for k in range(self.n_arms):
            if self.counts[k] == 0:
                return k
        best = 0
        best_v = -float("inf")
        log_t = math.log(max(self.t, 1))
        for k in range(self.n_arms):
            mean = self.sums[k] / self.counts[k]
            bonus = math.sqrt(2.0 * log_t / self.counts[k])
            ucb = mean + bonus
            if ucb > best_v:
                best_v = ucb
                best = k
        return best

    def update(self, arm: int, reward: float):
        """Increment count, sum; advance t."""
        if not 0 <= arm < self.n_arms:
            raise ValueError(f"arm {arm} out of range")
        self.counts[arm] += 1
        self.sums[arm] += float(reward)
        self.t += 1

    def mean(self, arm: int) -> float:
        if self.counts[arm] == 0:
            return 0.0
        return self.sums[arm] / self.counts[arm]


def evaluate_ucb1_variants(
    events: list,
    classify_fns: dict[str, Callable[[str, str], float]],
) -> dict:
    """Run UCB1 over events with reward = 1 - brier loss."""
    names = list(classify_fns.keys())
    bandit = UCB1(len(names))

    n = hits = 0
    brier = 0.0
    pulls = {name: 0 for name in names}
    rewards = {name: 0.0 for name in names}

    for e in events:
        framing = e.get("outcome_framing") or e.get("framing", "")
        contexto = e.get("contexto", "")
        y = e.get("outcome_real")
        if y is None:
            continue
        arm = bandit.select()
        name = names[arm]
        p = unpack_pred(classify_fns[name](framing, contexto))
        loss = (p - y) ** 2
        reward = 1.0 - loss
        bandit.update(arm, reward)
        pulls[name] += 1
        rewards[name] += reward
        n += 1
        if (p >= 0.5) == bool(y):
            hits += 1
        brier += loss

    means = {names[k]: bandit.mean(k) for k in range(len(names))}
    best_arm = max(means.items(), key=lambda x: x[1])[0] if means else None

    return {
        "n": n,
        "hits": hits,
        "acc": hits / n if n else 0.0,
        "brier": brier / n if n else 0.0,
        "pulls": pulls,
        "rewards": rewards,
        "means": means,
        "best_arm": best_arm,
    }
