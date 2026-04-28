"""Cohen's Kappa: agreement vs chance.

kappa = (p_o - p_e) / (1 - p_e)
  p_o: observed agreement
  p_e: expected agreement under marginal independence
"""

from __future__ import annotations

from typing import Iterable


def cohens_kappa(preds: Iterable[float], reals: Iterable[int],
                 threshold: float = 0.5) -> dict:
    """Binary kappa. Predictions thresholded at `threshold`."""
    p_hat = [1 if float(x) >= threshold else 0 for x in preds]
    y = [int(x) for x in reals]
    n = len(p_hat)
    if n == 0 or len(y) != n:
        return {"n": n, "kappa": None, "p_o": 0.0, "p_e": 0.0}

    # Confusion entries (rows = predicted, cols = actual)
    a = sum(1 for i in range(n) if p_hat[i] == 1 and y[i] == 1)  # TP
    b = sum(1 for i in range(n) if p_hat[i] == 1 and y[i] == 0)  # FP
    c = sum(1 for i in range(n) if p_hat[i] == 0 and y[i] == 1)  # FN
    d = sum(1 for i in range(n) if p_hat[i] == 0 and y[i] == 0)  # TN

    p_o = (a + d) / n
    # Marginals
    pred_pos = (a + b) / n
    pred_neg = (c + d) / n
    real_pos = (a + c) / n
    real_neg = (b + d) / n
    p_e = pred_pos * real_pos + pred_neg * real_neg
    if abs(1 - p_e) < 1e-12:
        kappa = None
    else:
        kappa = (p_o - p_e) / (1 - p_e)
    return {
        "n": n,
        "kappa": kappa,
        "p_o": p_o,
        "p_e": p_e,
        "tp": a, "fp": b, "fn": c, "tn": d,
    }
