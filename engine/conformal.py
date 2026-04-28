"""
Onda 253: Conformal Prediction (Vovk, Gammerman, Shafer 2005).

Distribution-free prediction intervals com cobertura garantida (1-alpha).
Usa Mondrian conformal (per-category quantile) — capta heteroscedasticity
das categorias do classificador (war 100% confiável, prices 50/50).

Aplicação:
- conformal_calibrate(events) → quantis empíricos α por categoria
- conformal_interval(p, label, quants) → [lo, hi] cobertura ≥ 1-alpha
- conformal_set(p, label, quants) → {0}, {1}, {0,1} (singleton = certeza, set = abstenção)

Insight: categorias com baixo nonconformity histórico (war, scheduled) recebem
intervalos estreitos → singleton predictions; categorias incertas (price) recebem
intervalos largos → set {0,1} → abstenção honest.

Sem memorization: quantil é estatística agregada, não memoriza outcomes individuais.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Callable


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


def conformal_interval(
    p: float, label: str, quants: dict[str, float], default_q: float = 0.5,
) -> tuple[float, float]:
    """[lo, hi] symmetric interval around p with width = quantile."""
    q = quants.get(label, default_q)
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
