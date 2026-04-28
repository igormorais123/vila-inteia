"""Selective forecasting com reject option (Chow 1970 / Geifman 2017).

Predict only when |p - 0.5| >= tau, abstain otherwise.
Trade coverage for accuracy.
"""

from __future__ import annotations

from typing import Callable


def selective_predict(p: float, tau: float = 0.10) -> int | None:
    """Return 1, 0, or None (abstain).

    tau: minimum |p - 0.5| required to commit. Higher = more abstain.
    """
    if abs(p - 0.5) < tau:
        return None
    return 1 if p >= 0.5 else 0


def evaluate_selective(
    events: list,
    classify_fn: Callable[[str, str], tuple[float, str]] | Callable,
    tau: float = 0.10,
) -> dict:
    """Eval selective accuracy + coverage."""
    n = 0
    pred_n = 0
    pred_hits = 0
    pred_brier = 0.0
    abstain = 0
    abstain_real_yes = 0

    for e in events:
        framing = e.get("outcome_framing") or e.get("framing", "")
        contexto = e.get("contexto", "")
        y = e.get("outcome_real")
        if y is None:
            continue
        n += 1
        out = classify_fn(framing, contexto)
        p = out[0] if isinstance(out, tuple) else out
        pred = selective_predict(p, tau=tau)

        if pred is None:
            abstain += 1
            if y == 1:
                abstain_real_yes += 1
            continue
        pred_n += 1
        if pred == y:
            pred_hits += 1
        pred_brier += (p - y) ** 2

    return {
        "n_total": n,
        "tau": tau,
        "n_predicted": pred_n,
        "n_abstained": abstain,
        "coverage": pred_n / n if n else 0,
        "selective_acc": pred_hits / pred_n if pred_n else 0,
        "selective_brier": pred_brier / pred_n if pred_n else 0,
        "abstain_yes_rate": abstain_real_yes / abstain if abstain else 0,
    }


def risk_coverage_curve(
    events: list,
    classify_fn: Callable,
    taus: list[float] | None = None,
) -> list[dict]:
    """Sweep tau, return coverage vs selective accuracy curve."""
    if taus is None:
        taus = [0.0, 0.05, 0.10, 0.15, 0.20, 0.25, 0.30, 0.40]
    return [evaluate_selective(events, classify_fn, tau=t) for t in taus]
