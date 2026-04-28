"""Vovk Aggregating Algorithm (1998) for binary log-loss.

K experts predict p_k(t) per round; AA aggregates with regret O(log K).
Update (eta=1 for log-loss): w_k(t+1) = w_k(t) * exp(-loss_k(t)).
Substitution function for log-loss (Vovk 1998, Sec. 4):
    p_AA = -log( sum_k W_k * exp(-loss(0))) / -log(sum_k W_k * exp(-loss(0)))
            equivalently p_AA = (sum W_k * p_k^1) / (sum W_k * p_k^1 + sum W_k * (1-p_k)^1)
    with eta=1 this collapses to p_AA = sum_k W_k * p_k (mixable game theorem).
We use Vovk's exact log-loss substitution rule yielding regret <= log(K).
"""

from __future__ import annotations

import math


_EPS = 1e-12


def _clip(p: float) -> float:
    return min(1.0 - _EPS, max(_EPS, p))


def _log_loss(p: float, y: int) -> float:
    p = _clip(p)
    return -math.log(p) if y == 1 else -math.log(1.0 - p)


def aggregating_algorithm(
    predictions: list[dict[str, float]],
    outcomes: list[int],
) -> dict:
    """Run Vovk AA across rounds with log-loss.

    predictions: list of round dicts {expert_name: p_k(t)}.
    outcomes: list of binary labels y_t in {0,1}.
    Returns: regret vs best expert, final weights, AA predictions, expert losses.
    """
    if not predictions:
        return {"regret": 0.0, "weights": {}, "aa_preds": [], "expert_loss": {}}
    if len(predictions) != len(outcomes):
        raise ValueError("predictions and outcomes must have same length")

    experts = sorted({k for r in predictions for k in r})
    K = len(experts)
    # Uniform initial weights.
    log_w = {k: -math.log(K) for k in experts}  # log W_k(0) = log(1/K)
    cum_loss = {k: 0.0 for k in experts}
    aa_preds: list[float] = []
    aa_loss = 0.0

    for t, (round_pred, y) in enumerate(zip(predictions, outcomes)):
        # Normalize current weights.
        m = max(log_w.values())
        w_unnorm = {k: math.exp(log_w[k] - m) for k in experts}
        z = sum(w_unnorm.values())
        w = {k: w_unnorm[k] / z for k in experts}

        # Vovk substitution rule for log-loss with eta=1.
        # p_AA = sum_k w_k * p_k (the "mixable" mixture for log-loss; Vovk 1998 Thm 1).
        num = 0.0
        den_p1 = 0.0
        den_p0 = 0.0
        for k in experts:
            p_k = _clip(round_pred.get(k, 0.5))
            den_p1 += w[k] * p_k
            den_p0 += w[k] * (1.0 - p_k)
        # Substitution g satisfying log-loss mixability: p_AA = den_p1 / (den_p1 + den_p0).
        # (For log-loss this equals the weighted average — but we keep general form.)
        p_aa = den_p1 / (den_p1 + den_p0) if (den_p1 + den_p0) > 0 else 0.5
        aa_preds.append(p_aa)
        aa_loss += _log_loss(p_aa, y)

        # Loss-based weight update: log W_k(t+1) = log W_k(t) - loss_k(t), eta=1.
        for k in experts:
            p_k = _clip(round_pred.get(k, 0.5))
            l_k = _log_loss(p_k, y)
            cum_loss[k] += l_k
            log_w[k] -= l_k
        _ = num  # silence unused (kept symmetric)

    # Final normalized weights.
    m = max(log_w.values())
    w_unnorm = {k: math.exp(log_w[k] - m) for k in experts}
    z = sum(w_unnorm.values())
    final_weights = {k: w_unnorm[k] / z for k in experts}

    best = min(cum_loss.values())
    regret = aa_loss - best
    return {
        "regret": regret,
        "aa_loss": aa_loss,
        "best_expert_loss": best,
        "weights": final_weights,
        "aa_preds": aa_preds,
        "expert_loss": cum_loss,
        "K": K,
        "T": len(outcomes),
    }
