"""EXP3 (Auer et al. 2002) for adversarial bandits.

Hedge-style probabilistic arm selection with importance-weighted reward
estimates. Recommended eta = sqrt(log(K) / (T * K)) for horizon T.
"""

from __future__ import annotations

import math
import random
from typing import Callable

from engine._pred_utils import unpack_pred


class EXP3:
    """EXP3 adversarial-bandit selector."""

    def __init__(self, n_arms: int, eta: float,
                 rng: random.Random | None = None):
        if n_arms < 1:
            raise ValueError("n_arms must be >= 1")
        if eta <= 0:
            raise ValueError("eta must be > 0")
        self.n_arms = n_arms
        self.eta = float(eta)
        self.weights = [1.0] * n_arms
        self.last_probs: list[float] = [1.0 / n_arms] * n_arms
        self.rng = rng or random.Random(0)
        self.t = 0

    def _probs(self) -> list[float]:
        total = sum(self.weights)
        if total <= 0:
            return [1.0 / self.n_arms] * self.n_arms
        return [w / total for w in self.weights]

    def select(self) -> int:
        """Sample arm proportional to current weight distribution."""
        probs = self._probs()
        self.last_probs = probs
        u = self.rng.random()
        acc = 0.0
        for k, p in enumerate(probs):
            acc += p
            if u <= acc:
                return k
        return self.n_arms - 1

    def update(self, arm: int, reward: float):
        """Importance-weighted exponential update on selected arm."""
        if not 0 <= arm < self.n_arms:
            raise ValueError(f"arm {arm} out of range")
        r = max(0.0, min(1.0, float(reward)))
        prob = max(self.last_probs[arm], 1e-12)
        est = r / prob
        # Stabilize against overflow.
        exponent = self.eta * est
        if exponent > 50.0:
            exponent = 50.0
        self.weights[arm] *= math.exp(exponent)
        # Renormalize to prevent drift.
        m = max(self.weights)
        if m > 1e150:
            self.weights = [w / m for w in self.weights]
        self.t += 1

    @staticmethod
    def suggested_eta(n_arms: int, horizon: int) -> float:
        if horizon < 1:
            horizon = 1
        if n_arms < 2:
            n_arms = 2
        return math.sqrt(math.log(n_arms) / (horizon * n_arms))


def evaluate_exp3_variants(
    events: list,
    classify_fns: dict[str, Callable[[str, str], float]],
    seed: int = 0,
    eta: float | None = None,
) -> dict:
    """Run EXP3 over events with reward = 1 - brier loss."""
    names = list(classify_fns.keys())
    horizon = sum(1 for e in events if e.get("outcome_real") is not None)
    if eta is None:
        eta = EXP3.suggested_eta(len(names), horizon)
    rng = random.Random(seed)
    bandit = EXP3(len(names), eta, rng=rng)

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

    final_probs = bandit._probs()
    probs = {names[k]: final_probs[k] for k in range(len(names))}
    best_arm = max(probs.items(), key=lambda x: x[1])[0] if probs else None

    return {
        "n": n,
        "hits": hits,
        "acc": hits / n if n else 0.0,
        "brier": brier / n if n else 0.0,
        "pulls": pulls,
        "rewards": rewards,
        "probs": probs,
        "best_arm": best_arm,
        "eta": eta,
    }
