"""Thompson sampling (Thompson 1933) for binary-reward bandits.

Per-arm Beta(alpha, beta) posterior; each round sample theta_k ~ Beta_k
and select argmax. Bayesian-optimal exploration-exploitation balance.
"""

from __future__ import annotations

import random
from typing import Callable

from engine._pred_utils import unpack_pred


class ThompsonSampler:
    """Thompson sampler with Beta-Bernoulli posteriors per arm."""

    def __init__(self, n_arms: int, prior_alpha: float = 1.0,
                 prior_beta: float = 1.0, rng: random.Random | None = None):
        if n_arms < 1:
            raise ValueError("n_arms must be >= 1")
        self.n_arms = n_arms
        self.alpha = [float(prior_alpha)] * n_arms
        self.beta = [float(prior_beta)] * n_arms
        self.rng = rng or random.Random(0)
        self.t = 0

    def select(self) -> int:
        """Sample theta_k ~ Beta(alpha_k, beta_k); return argmax k."""
        samples = [self.rng.betavariate(self.alpha[k], self.beta[k])
                   for k in range(self.n_arms)]
        best = 0
        best_v = samples[0]
        for k in range(1, self.n_arms):
            if samples[k] > best_v:
                best_v = samples[k]
                best = k
        return best

    def update(self, arm: int, reward: float):
        """Bernoulli posterior update: alpha += r, beta += (1-r). Reward in [0,1]."""
        if not 0 <= arm < self.n_arms:
            raise ValueError(f"arm {arm} out of range")
        r = max(0.0, min(1.0, float(reward)))
        self.alpha[arm] += r
        self.beta[arm] += 1.0 - r
        self.t += 1

    def posterior_mean(self, arm: int) -> float:
        return self.alpha[arm] / (self.alpha[arm] + self.beta[arm])


def evaluate_thompson_classifier_variants(
    events: list,
    classify_fns: dict[str, Callable[[str, str], float]],
    seed: int = 0,
) -> dict:
    """Run Thompson sampling over events, picking one classifier per round.

    Reward = 1 - brier_loss = 1 - (p - y)^2 (in [0,1]).
    """
    names = list(classify_fns.keys())
    rng = random.Random(seed)
    sampler = ThompsonSampler(len(names), rng=rng)

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
        arm = sampler.select()
        name = names[arm]
        p = unpack_pred(classify_fns[name](framing, contexto))
        loss = (p - y) ** 2
        reward = 1.0 - loss
        sampler.update(arm, reward)
        pulls[name] += 1
        rewards[name] += reward
        n += 1
        if (p >= 0.5) == bool(y):
            hits += 1
        brier += loss

    posterior_means = {names[k]: sampler.posterior_mean(k)
                       for k in range(len(names))}
    best_arm = max(posterior_means.items(), key=lambda x: x[1])[0]

    return {
        "n": n,
        "hits": hits,
        "acc": hits / n if n else 0.0,
        "brier": brier / n if n else 0.0,
        "pulls": pulls,
        "rewards": rewards,
        "posterior_means": posterior_means,
        "best_arm": best_arm,
    }
