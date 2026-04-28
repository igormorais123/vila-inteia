"""Cumulative regret analysis for online bandit / hedge methods.

regret_t = sum_{s<=t} loss_alg_s - sum_{s<=t} loss_best_arm_s.
Sublinear regret_t / t -> 0 indicates no-regret learning.
"""

from __future__ import annotations

from typing import Callable

from engine._pred_utils import unpack_pred
from engine.exp3 import EXP3
from engine.thompson_sampling import ThompsonSampler
from engine.ucb1 import UCB1


def compute_regret(losses_per_round: list[dict], best_arm: str) -> list[float]:
    """Per-round cumulative regret of best_arm vs each round's chosen arm.

    losses_per_round: list of dicts {arm_name: loss} for that round.
                      Must include the 'chosen' arm under key '_chosen' or
                      pass arm losses explicitly per round; here we assume
                      each round dict has a '_alg_loss' key giving the loss
                      incurred by the algorithm in that round.
    """
    if not losses_per_round:
        return []
    cum_alg = 0.0
    cum_best = 0.0
    out: list[float] = []
    for r in losses_per_round:
        alg_loss = r.get("_alg_loss", 0.0)
        best_loss = r.get(best_arm, 0.0)
        cum_alg += alg_loss
        cum_best += best_loss
        out.append(cum_alg - cum_best)
    return out


def _run_method(method: str, names: list, events: list,
                classify_fns: dict, seed: int = 0):
    """Run one method, return (per-round dicts, chosen names, total losses per arm)."""
    rounds: list[dict] = []
    arm_total_loss = {n: 0.0 for n in names}

    if method == "thompson":
        import random as _r
        rng = _r.Random(seed)
        sampler = ThompsonSampler(len(names), rng=rng)
        selector = lambda: sampler.select()
        updater = lambda k, r: sampler.update(k, r)
    elif method == "ucb1":
        bandit = UCB1(len(names))
        selector = lambda: bandit.select()
        updater = lambda k, r: bandit.update(k, r)
    elif method == "exp3":
        import random as _r
        horizon = sum(1 for e in events if e.get("outcome_real") is not None)
        eta = EXP3.suggested_eta(len(names), horizon)
        rng = _r.Random(seed)
        bandit = EXP3(len(names), eta, rng=rng)
        selector = lambda: bandit.select()
        updater = lambda k, r: bandit.update(k, r)
    else:
        raise ValueError(f"unknown method: {method}")

    for e in events:
        framing = e.get("outcome_framing") or e.get("framing", "")
        contexto = e.get("contexto", "")
        y = e.get("outcome_real")
        if y is None:
            continue
        # Compute every-arm loss this round (counterfactual, for regret accounting).
        round_losses = {}
        for n in names:
            p = unpack_pred(classify_fns[n](framing, contexto))
            round_losses[n] = (p - y) ** 2
        arm = selector()
        chosen_name = names[arm]
        alg_loss = round_losses[chosen_name]
        round_losses["_alg_loss"] = alg_loss
        round_losses["_chosen"] = chosen_name
        rounds.append(round_losses)
        for n in names:
            arm_total_loss[n] += round_losses[n]
        reward = 1.0 - alg_loss
        updater(arm, reward)

    return rounds, arm_total_loss


def compare_regrets(
    events: list,
    classify_fns: dict[str, Callable[[str, str], float]],
    methods: list[str] | None = None,
    seed: int = 0,
) -> dict:
    """Compare cumulative regret across methods on same events.

    Returns dict: method -> {"regret_curve", "final_regret", "best_arm",
                              "alg_total_loss", "best_total_loss"}.
    """
    if methods is None:
        methods = ["thompson", "ucb1", "exp3"]
    names = list(classify_fns.keys())
    out: dict[str, dict] = {}

    # Best arm in hindsight: minimum cumulative loss across all events
    # (computed once over deterministic per-round losses).
    cum = {n: 0.0 for n in names}
    n_rounds = 0
    for e in events:
        framing = e.get("outcome_framing") or e.get("framing", "")
        contexto = e.get("contexto", "")
        y = e.get("outcome_real")
        if y is None:
            continue
        n_rounds += 1
        for n in names:
            p = unpack_pred(classify_fns[n](framing, contexto))
            cum[n] += (p - y) ** 2
    best_arm_global = min(cum.items(), key=lambda x: x[1])[0] if cum else None

    for method in methods:
        rounds, _arm_total = _run_method(method, names, events,
                                         classify_fns, seed=seed)
        curve = compute_regret(rounds, best_arm_global)
        alg_total = sum(r["_alg_loss"] for r in rounds)
        best_total = cum[best_arm_global] if best_arm_global else 0.0
        out[method] = {
            "regret_curve": curve,
            "final_regret": curve[-1] if curve else 0.0,
            "best_arm": best_arm_global,
            "alg_total_loss": alg_total,
            "best_total_loss": best_total,
            "n": n_rounds,
        }
    out["_meta"] = {"best_arm_global": best_arm_global, "arm_total_loss": cum,
                    "n_rounds": n_rounds, "names": names}
    return out
