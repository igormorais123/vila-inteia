"""Matthews Correlation Coefficient (MCC).

phi = (TP*TN - FP*FN) / sqrt((TP+FP)(TP+FN)(TN+FP)(TN+FN))
Range [-1, 1]. Robust on imbalanced classes.
Returns 0 when any marginal is zero (denominator collapse).
"""

from __future__ import annotations

import math
from typing import Iterable


def matthews_corr(preds: Iterable[float], reals: Iterable[int],
                  threshold: float = 0.5) -> dict:
    p_hat = [1 if float(x) >= threshold else 0 for x in preds]
    y = [int(x) for x in reals]
    n = len(p_hat)
    if n == 0 or len(y) != n:
        return {"n": n, "mcc": None, "tp": 0, "fp": 0, "fn": 0, "tn": 0}

    tp = sum(1 for i in range(n) if p_hat[i] == 1 and y[i] == 1)
    fp = sum(1 for i in range(n) if p_hat[i] == 1 and y[i] == 0)
    fn = sum(1 for i in range(n) if p_hat[i] == 0 and y[i] == 1)
    tn = sum(1 for i in range(n) if p_hat[i] == 0 and y[i] == 0)

    num = tp * tn - fp * fn
    denom_sq = (tp + fp) * (tp + fn) * (tn + fp) * (tn + fn)
    if denom_sq <= 0:
        mcc = 0.0
    else:
        mcc = num / math.sqrt(denom_sq)
    return {
        "n": n,
        "mcc": mcc,
        "tp": tp, "fp": fp, "fn": fn, "tn": tn,
    }
