"""
Onda 229: Validação rigorosa de forecasts (estado-da-arte 2024-2025).

Implementa métricas usadas em ForecastBench, Tetlock superforecasters,
e meteorologia clássica (Murphy, Gneiting):

  1. Murphy decomposition (Brier = Reliability + Resolution - Uncertainty)
  2. Bootstrap CI (95%) sobre brier/acc — quantifica incerteza estatística
  3. Diebold-Mariano test — significância p<0.05 entre 2 forecasters
  4. ROC AUC — discrimination ability (Gneiting triptych)
  5. Reliability diagram bins (10 bins) — calibration visual
  6. Knowledge-leak warning — flag quando event date < cutoff (memorization risk)

Refs:
  - Murphy AH (1973) "A new vector partition of the probability score"
  - Gneiting & Raftery (2007) "Strictly proper scoring rules"
  - Siegert (2017) "Simplifying Murphy's Brier score decomposition"
  - Diebold & Mariano (1995) "Comparing predictive accuracy"
  - Karger et al (2024) "ForecastBench: dynamic benchmark of AI forecasting"
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass


# ============================================================================
# 1. Murphy decomposition
# ============================================================================
def murphy_decomposition(
    preds: list[float], reals: list[int], n_bins: int = 10
) -> dict:
    """Decompõe Brier em REL + UNC - RES.

    Brier = Reliability − Resolution + Uncertainty (positively oriented:
    REL menor melhor, RES maior melhor).

    Returns: {brier, reliability, resolution, uncertainty, n}
    """
    n = len(preds)
    if n == 0:
        return {"brier": 0, "reliability": 0, "resolution": 0, "uncertainty": 0, "n": 0}

    # Climatology base rate
    obar = sum(reals) / n
    uncertainty = obar * (1 - obar)

    # Bin predictions
    bins: list[list] = [[] for _ in range(n_bins)]
    for p, y in zip(preds, reals):
        idx = min(int(p * n_bins), n_bins - 1)
        bins[idx].append((p, y))

    reliability = 0.0
    resolution = 0.0
    for b in bins:
        if not b:
            continue
        nk = len(b)
        avg_p = sum(p for p, _ in b) / nk
        emp = sum(y for _, y in b) / nk
        reliability += (nk / n) * (avg_p - emp) ** 2
        resolution += (nk / n) * (emp - obar) ** 2

    brier = reliability - resolution + uncertainty
    return {
        "brier": brier,
        "reliability": reliability,
        "resolution": resolution,
        "uncertainty": uncertainty,
        "n": n,
    }


# ============================================================================
# 2. Bootstrap CI
# ============================================================================
def bootstrap_ci(
    preds: list[float], reals: list[int],
    metric: str = "brier", n_resamples: int = 1000,
    alpha: float = 0.05, seed: int = 42,
) -> dict:
    """Bootstrap percentile CI (95% por default).

    metric: 'brier' | 'acc' | 'nll'

    Returns: {mean, lower, upper, alpha, n_resamples}
    """
    rng = random.Random(seed)
    n = len(preds)
    if n == 0:
        return {"mean": 0, "lower": 0, "upper": 0, "alpha": alpha, "n_resamples": 0}

    def compute(pp, yy):
        if metric == "brier":
            return sum((p - y) ** 2 for p, y in zip(pp, yy)) / len(pp)
        if metric == "acc":
            return sum(1 for p, y in zip(pp, yy) if (p >= 0.5) == bool(y)) / len(pp)
        if metric == "nll":
            tot = 0.0
            for p, y in zip(pp, yy):
                ep = max(1e-9, min(1 - 1e-9, p))
                tot += -(y * math.log(ep) + (1 - y) * math.log(1 - ep))
            return tot / len(pp)
        raise ValueError(f"unknown metric {metric}")

    point = compute(preds, reals)
    samples = []
    for _ in range(n_resamples):
        idx = [rng.randrange(n) for _ in range(n)]
        samples.append(compute([preds[i] for i in idx], [reals[i] for i in idx]))
    samples.sort()
    lo = samples[int(alpha / 2 * n_resamples)]
    hi = samples[int((1 - alpha / 2) * n_resamples)]
    return {"mean": point, "lower": lo, "upper": hi,
            "alpha": alpha, "n_resamples": n_resamples}


# ============================================================================
# 3. Diebold-Mariano test (paired forecast comparison)
# ============================================================================
def diebold_mariano(
    preds_a: list[float], preds_b: list[float], reals: list[int],
    loss: str = "brier",
) -> dict:
    """Paired test: H0 forecaster A == B em mean loss.

    DM stat ~ N(0, 1) sob H0. p-value 2-sided.

    Returns: {dm_stat, p_value, mean_diff, significant_5pct}
    """
    n = len(reals)
    if n < 2:
        return {"dm_stat": 0, "p_value": 1.0, "mean_diff": 0, "significant_5pct": False}

    if loss == "brier":
        d = [(pa - y) ** 2 - (pb - y) ** 2
             for pa, pb, y in zip(preds_a, preds_b, reals)]
    elif loss == "abs":
        d = [abs(pa - y) - abs(pb - y)
             for pa, pb, y in zip(preds_a, preds_b, reals)]
    else:
        raise ValueError(f"unknown loss {loss}")

    dbar = sum(d) / n
    var = sum((x - dbar) ** 2 for x in d) / (n - 1)
    se = math.sqrt(var / n) if var > 0 else 1e-9
    dm = dbar / se
    # p-value 2-sided usando aprox normal
    p = 2 * (1 - _normal_cdf(abs(dm)))
    return {
        "dm_stat": dm, "p_value": p, "mean_diff": dbar,
        "significant_5pct": p < 0.05,
    }


def _normal_cdf(x: float) -> float:
    """Aprox CDF normal padrão via erf."""
    return 0.5 * (1 + math.erf(x / math.sqrt(2)))


# ============================================================================
# 4. ROC AUC
# ============================================================================
def roc_auc(preds: list[float], reals: list[int]) -> dict:
    """Area sob ROC curve (probabilidade pred(positivo) > pred(negativo)).

    AUC=0.5 = random; AUC=1.0 = perfeito.

    Returns: {auc, n_pos, n_neg, n_ties}
    """
    pos = [p for p, y in zip(preds, reals) if y == 1]
    neg = [p for p, y in zip(preds, reals) if y == 0]
    n_pos = len(pos)
    n_neg = len(neg)
    if n_pos == 0 or n_neg == 0:
        return {"auc": 0.5, "n_pos": n_pos, "n_neg": n_neg, "n_ties": 0}

    n_correct = 0
    n_ties = 0
    for p_pos in pos:
        for p_neg in neg:
            if p_pos > p_neg:
                n_correct += 1
            elif p_pos == p_neg:
                n_ties += 1
    auc = (n_correct + 0.5 * n_ties) / (n_pos * n_neg)
    return {"auc": auc, "n_pos": n_pos, "n_neg": n_neg, "n_ties": n_ties}


# ============================================================================
# 5. Reliability diagram
# ============================================================================
def reliability_diagram(
    preds: list[float], reals: list[int], n_bins: int = 10
) -> list[dict]:
    """Bins [0, 1] em n_bins. Cada bin: avg_p, emp_freq, count.

    Returns: lista de dicts (1 por bin).
    """
    bins: list[list] = [[] for _ in range(n_bins)]
    for p, y in zip(preds, reals):
        idx = min(int(p * n_bins), n_bins - 1)
        bins[idx].append((p, y))

    out = []
    for i, b in enumerate(bins):
        if not b:
            out.append({"bin": i, "avg_p": None, "emp_freq": None, "count": 0,
                        "bin_low": i / n_bins, "bin_high": (i + 1) / n_bins})
            continue
        avg_p = sum(p for p, _ in b) / len(b)
        emp = sum(y for _, y in b) / len(b)
        out.append({"bin": i, "avg_p": avg_p, "emp_freq": emp, "count": len(b),
                    "bin_low": i / n_bins, "bin_high": (i + 1) / n_bins})
    return out


# ============================================================================
# 6. Knowledge-leak warning (Vila-specific)
# ============================================================================
def knowledge_leak_warning(event_dates: list[str], llm_cutoff: str = "2026-01-01") -> dict:
    """Flag eventos com date < cutoff (memorization risk).

    Vila atual prevê eventos 2014-2025 com knowledge cutoff jan 2026.
    Não é forecasting — é memorização. Validation foda requer eventos
    POST-cutoff (ForecastBench-style dynamic eval).

    Returns: {n_pre_cutoff, n_post_cutoff, leak_ratio, warning}
    """
    pre = sum(1 for d in event_dates if d < llm_cutoff)
    post = len(event_dates) - pre
    ratio = pre / len(event_dates) if event_dates else 0
    warning = (
        "⚠ KNOWLEDGE LEAK RISK: events ocorreram antes do LLM cutoff. "
        "Resultados refletem memorização, não forecasting. "
        "Para validação rigorosa, use eventos POST-cutoff (ForecastBench-style)."
        if ratio > 0.5 else None
    )
    return {
        "n_pre_cutoff": pre, "n_post_cutoff": post,
        "leak_ratio": ratio, "cutoff": llm_cutoff,
        "warning": warning,
    }
