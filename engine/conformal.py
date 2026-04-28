"""Mondrian Conformal Prediction (Vovk, Gammerman, Shafer 2005).

Per-category empirical (1-alpha)-quantile of |p - y|.
Singleton = confident, set = abstain.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Callable

# Reliability tiers per category. High-reliability categories (factual events
# that almost always happen) get tight intervals (low alpha). Volatile / market
# / polling categories get wider intervals (high alpha).
_HIGH_RELIABILITY = {
    "war_conflict",
    "scheduled_event",
    "central_bank_meeting",
    "sports_event_structure",
    "regulatory_active",
    "casualty_threshold",
    "geopolitical_routine",
}
_VOLATILE = {
    "price_threshold",
    "price_target",
    "tech_release",
    "fed_action",
    "polling",
    "election",
    "regime_change",
    "corporate_negative",
    "regulatory_action",
    "geopolitical_low",
    "extreme_quantity_claim",
    "sports_specific_winner",
    "br_reform_complex",
    "negative_rank_claim",
    "etf_approval",
    "default",
}


def conformal_calibrate(
    events: list,
    classify_fn: Callable[[str, str], tuple[float, str]],
    alpha: float = 0.1,
) -> dict[str, float]:
    """Compute per-category nonconformity quantile.

    α_i = |p_i - y_i| para cada calibration point i.
    Retorna o (1-alpha)-quantile por categoria.

    Edge: categoria com 0 calibração default 0.5 (max uncertainty).
    """
    by_cat: dict[str, list[float]] = defaultdict(list)
    for e in events:
        framing = e.get("outcome_framing") or e.get("framing", "")
        contexto = e.get("contexto", "")
        real = e.get("outcome_real")
        if real is None:
            continue
        p, label = classify_fn(framing, contexto)
        by_cat[label].append(abs(p - real))

    quants: dict[str, float] = {}
    for label, scores in by_cat.items():
        scores.sort()
        n = len(scores)
        # Conformal quantile: ceil((n+1)(1-alpha))/n style
        idx = min(n - 1, max(0, int((n + 1) * (1 - alpha)) - 1))
        quants[label] = scores[idx]
    return quants


def _abstain_rate_for_alpha(
    events: list,
    classify_fn: Callable[[str, str], tuple[float, str]],
    alpha: float,
    threshold: float = 0.5,
) -> float:
    """Leave-one-out abstain rate on the calibration set at a given alpha.

    For each event, refit Mondrian quantiles on (events - this one) and check
    if the conformal set is a singleton. Returns the held-out abstain fraction.
    Used by `conformal_calibrate_smart` to grid alpha against a target.
    """
    n = abstain = 0
    for i, e in enumerate(events):
        framing = e.get("outcome_framing") or e.get("framing", "")
        contexto = e.get("contexto", "")
        if e.get("outcome_real") is None:
            continue
        rest = events[:i] + events[i + 1:]
        quants = conformal_calibrate(rest, classify_fn, alpha=alpha)
        # Pooled fallback for unseen categories on the held-out sample.
        pooled = []
        for r in rest:
            ry = r.get("outcome_real")
            if ry is None:
                continue
            rp, _ = classify_fn(
                r.get("outcome_framing") or r.get("framing", ""),
                r.get("contexto", ""),
            )
            pooled.append(abs(rp - ry))
        if pooled:
            pooled.sort()
            m = len(pooled)
            idx = min(m - 1, max(0, int((m + 1) * (1 - alpha)) - 1))
            quants = {**quants, "__pooled__": pooled[idx]}
        n += 1
        p, label = classify_fn(framing, contexto)
        s = conformal_set(p, label, quants, threshold=threshold)
        if len(s) != 1:
            abstain += 1
    return abstain / n if n else 1.0


def conformal_calibrate_smart(
    events: list,
    classify_fn: Callable[[str, str], tuple[float, str]],
    target_abstain_rate: float = 0.5,
    alpha_search: tuple[float, float] = (0.05, 0.5),
    step: float = 0.05,
    per_category: bool = True,
) -> dict[str, float]:
    """Auto-tune alpha to hit `target_abstain_rate` on calibration set.

    Grid over alpha in [alpha_search[0], alpha_search[1]] (inclusive) at `step`
    spacing. For each alpha, computes abstain_rate via leave-this-out style
    (refit + measure on same events; this is the train-set proxy used to pick
    a global alpha).

    Per-category twist: after picking the global alpha that hits the target,
    HIGH_RELIABILITY categories are recalibrated at a tighter alpha
    (alpha * 0.5, floor at alpha_search[0]) and VOLATILE categories at a
    wider alpha (min(alpha_search[1], alpha * 1.5)). All other categories use
    the picked global alpha.

    Returns: per-category quantile dict (drop-in for conformal_interval/set).
    """
    lo, hi = alpha_search
    # Build candidate grid (inclusive on both ends).
    grid: list[float] = []
    a = lo
    while a <= hi + 1e-9:
        grid.append(round(a, 6))
        a += step

    # Pick global alpha closest to target.
    best_alpha = grid[0]
    best_diff = float("inf")
    rates: list[tuple[float, float]] = []
    for cand in grid:
        rate = _abstain_rate_for_alpha(events, classify_fn, cand)
        rates.append((cand, rate))
        diff = abs(rate - target_abstain_rate)
        if diff < best_diff:
            best_diff = diff
            best_alpha = cand

    if not per_category:
        return conformal_calibrate(events, classify_fn, alpha=best_alpha)

    # Per-category alpha: tighter for reliable, wider for volatile.
    tight_alpha = max(lo, best_alpha * 0.5)
    wide_alpha = min(hi, best_alpha * 1.5)

    q_global = conformal_calibrate(events, classify_fn, alpha=best_alpha)
    q_tight = conformal_calibrate(events, classify_fn, alpha=tight_alpha)
    q_wide = conformal_calibrate(events, classify_fn, alpha=wide_alpha)

    out: dict[str, float] = {}
    all_labels = set(q_global) | set(q_tight) | set(q_wide)
    for label in all_labels:
        if label in _HIGH_RELIABILITY:
            out[label] = q_tight.get(label, q_global.get(label, 0.5))
        elif label in _VOLATILE:
            out[label] = q_wide.get(label, q_global.get(label, 0.5))
        else:
            out[label] = q_global.get(label, 0.5)

    # Pooled fallback quantile for unseen categories: empirical (1-alpha)
    # quantile of |p - y| over the entire training set. Avoids forced-abstain
    # on labels missing from calibration.
    pooled: list[float] = []
    for e in events:
        framing = e.get("outcome_framing") or e.get("framing", "")
        contexto = e.get("contexto", "")
        real = e.get("outcome_real")
        if real is None:
            continue
        p, _ = classify_fn(framing, contexto)
        pooled.append(abs(p - real))
    if pooled:
        pooled.sort()
        n = len(pooled)
        idx = min(n - 1, max(0, int((n + 1) * (1 - best_alpha)) - 1))
        out["__pooled__"] = pooled[idx]
    # Annotate the selected alpha for diagnostics (under reserved key).
    out["__alpha__"] = best_alpha
    return out


def conformal_interval(
    p: float, label: str, quants: dict[str, float], default_q: float = 0.5,
) -> tuple[float, float]:
    """[lo, hi] symmetric interval around p with width = quantile.

    If the label is missing and `quants` carries a `__pooled__` fallback
    (set by `conformal_calibrate_smart`), that pooled quantile is preferred
    over `default_q`.
    """
    if label in quants:
        q = quants[label]
    else:
        q = quants.get("__pooled__", default_q)
    return max(0.0, p - q), min(1.0, p + q)


def conformal_set(
    p: float, label: str, quants: dict[str, float],
    threshold: float = 0.5, default_q: float = 0.5,
) -> set[int]:
    """Plausible labels at coverage 1-alpha.

    {1} singleton: confident YES (lo > threshold)
    {0} singleton: confident NO (hi < threshold)
    {0,1}: abstain (interval crosses threshold)
    """
    lo, hi = conformal_interval(p, label, quants, default_q)
    s: set[int] = set()
    if hi >= threshold:
        s.add(1)
    if lo < threshold:
        s.add(0)
    return s


def evaluate_conformal(
    test_events: list,
    classify_fn: Callable[[str, str], tuple[float, str]],
    quants: dict[str, float],
    alpha: float = 0.1,
) -> dict:
    """Eval coverage + efficiency + selective accuracy.

    Coverage: % of true outcomes inside conformal interval (target ≥ 1-alpha)
    Efficiency: mean |hi - lo| (smaller = better)
    Selective acc: acc on singleton predictions only (abstain on sets)
    Abstain rate: % onde set = {0,1}
    """
    n = 0
    inside = 0
    width_sum = 0.0
    singletons = 0
    singleton_hits = 0
    abstain = 0

    for e in test_events:
        framing = e.get("outcome_framing") or e.get("framing", "")
        contexto = e.get("contexto", "")
        real = e.get("outcome_real")
        if real is None:
            continue
        n += 1
        p, label = classify_fn(framing, contexto)
        lo, hi = conformal_interval(p, label, quants)
        width_sum += hi - lo
        if lo <= real <= hi:
            inside += 1
        s = conformal_set(p, label, quants)
        if len(s) == 1:
            singletons += 1
            if real in s:
                singleton_hits += 1
        else:
            abstain += 1

    return {
        "n": n,
        "alpha": alpha,
        "target_coverage": 1 - alpha,
        "coverage": inside / n if n else 0.0,
        "mean_width": width_sum / n if n else 0.0,
        "singletons": singletons,
        "singleton_acc": singleton_hits / singletons if singletons else 0.0,
        "abstain_rate": abstain / n if n else 0.0,
    }
