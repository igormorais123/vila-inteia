"""
Onda 255: Platt scaling + Isotonic regression — sigmoid/monotonic recalibration.

Platt (1999): fit sigmoid σ(A*p + B) on calibration set; corrige systematic
bias (over/underconfidence) com 2 parâmetros.

Isotonic (Zadrozny & Elkan 2002): fit monotonic non-decreasing g(p) via
pool-adjacent-violators (PAV); mais flexível que Platt mas precisa n maior.

Combina com EB: EB tunifies por categoria, Platt/Iso refinam globalmente.

Sem memorization: ambos extraem agg statistics (Platt: 2 floats; Iso: knots).

CRITICAL: refit quando muda prompt cognitivo (memory rule).
"""

from __future__ import annotations

import math
from typing import Callable


def _sigmoid(x: float) -> float:
    if x >= 0:
        z = math.exp(-x)
        return 1.0 / (1.0 + z)
    z = math.exp(x)
    return z / (1.0 + z)


def fit_platt(
    cal_events: list,
    classify_fn: Callable[[str, str], tuple[float, str]],
    max_iter: int = 100,
    lr: float = 0.05,
) -> tuple[float, float]:
    """Fit Platt sigmoid σ(A*p + B) via gradient descent on log-loss.

    Returns (A, B). σ(A*x + B) maps raw prob → calibrated prob.
    Uses Platt's original target smoothing: y_pos = (N+1)/(N+2), y_neg = 1/(N+2)
    to avoid degenerate fit.
    """
    pairs: list[tuple[float, int]] = []
    for e in cal_events:
        framing = e.get("outcome_framing") or e.get("framing", "")
        contexto = e.get("contexto", "")
        real = e.get("outcome_real")
        if real is None:
            continue
        p, _ = classify_fn(framing, contexto)
        pairs.append((p, int(real)))

    if not pairs:
        return 1.0, 0.0

    n_pos = sum(y for _, y in pairs)
    n_neg = len(pairs) - n_pos
    t_pos = (n_pos + 1) / (n_pos + 2)
    t_neg = 1 / (n_neg + 2)

    A, B = 1.0, 0.0
    for _ in range(max_iter):
        gA, gB = 0.0, 0.0
        for p, y in pairs:
            t = t_pos if y == 1 else t_neg
            f = _sigmoid(A * p + B)
            err = f - t
            gA += err * p
            gB += err
        gA /= len(pairs)
        gB /= len(pairs)
        A -= lr * gA
        B -= lr * gB
    return A, B


def platt_predict(p: float, A: float, B: float) -> float:
    """Apply Platt sigmoid."""
    return _sigmoid(A * p + B)


def fit_isotonic(
    cal_events: list,
    classify_fn: Callable[[str, str], tuple[float, str]],
) -> list[tuple[float, float]]:
    """Pool-Adjacent-Violators: fit monotonic non-decreasing g(p).

    Returns list of (p_break, g_value) sorted by p_break.
    Step function for prediction.
    """
    pairs: list[tuple[float, int]] = []
    for e in cal_events:
        framing = e.get("outcome_framing") or e.get("framing", "")
        contexto = e.get("contexto", "")
        real = e.get("outcome_real")
        if real is None:
            continue
        p, _ = classify_fn(framing, contexto)
        pairs.append((p, int(real)))

    if not pairs:
        return [(0.0, 0.5)]

    pairs.sort()
    # PAV: blocks of (sum, count, max_p)
    blocks: list[list[float]] = [[float(y), 1.0, p] for p, y in pairs]
    changed = True
    while changed:
        changed = False
        i = 0
        while i < len(blocks) - 1:
            mean_i = blocks[i][0] / blocks[i][1]
            mean_j = blocks[i + 1][0] / blocks[i + 1][1]
            if mean_i > mean_j:
                blocks[i][0] += blocks[i + 1][0]
                blocks[i][1] += blocks[i + 1][1]
                blocks[i][2] = blocks[i + 1][2]
                blocks.pop(i + 1)
                changed = True
            else:
                i += 1
    return [(b[2], b[0] / b[1]) for b in blocks]


def isotonic_predict(p: float, knots: list[tuple[float, float]]) -> float:
    """Step function lookup."""
    if not knots:
        return p
    for p_break, g in knots:
        if p <= p_break:
            return g
    return knots[-1][1]


def evaluate_calibration(
    test_events: list,
    classify_fn: Callable[[str, str], tuple[float, str]],
    method: str = "platt",
    params=None,
) -> dict:
    """Eval calibrated predictor."""
    if method in ("platt", "isotonic") and params is None:
        raise ValueError(f"params required for method={method!r}")
    n = 0
    hits = 0
    brier = 0.0
    for e in test_events:
        framing = e.get("outcome_framing") or e.get("framing", "")
        contexto = e.get("contexto", "")
        real = e.get("outcome_real")
        if real is None:
            continue
        p_raw, _ = classify_fn(framing, contexto)
        if method == "platt":
            A, B = params
            p = platt_predict(p_raw, A, B)
        elif method == "isotonic":
            p = isotonic_predict(p_raw, params)
        else:
            p = p_raw
        n += 1
        if (p >= 0.5) == bool(real):
            hits += 1
        brier += (p - real) ** 2
    return {
        "n": n, "hits": hits, "method": method,
        "acc": hits / n if n else 0,
        "brier": brier / n if n else 0,
    }
