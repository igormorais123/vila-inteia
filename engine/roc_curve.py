"""ROC curve points and AUC via Mann-Whitney U formula."""

from __future__ import annotations


def roc_curve_points(preds: list[float], reals: list[int]) -> list[tuple[float, float]]:
    """Returns list of (fpr, tpr) points sweeping all thresholds, descending by p."""
    n = len(reals)
    if n == 0 or len(preds) != n:
        return []
    pos = sum(reals)
    neg = n - pos
    if pos == 0 or neg == 0:
        return [(0.0, 0.0), (1.0, 1.0)]

    pairs = sorted(zip(preds, reals), key=lambda x: -x[0])
    points = [(0.0, 0.0)]
    tp = 0
    fp = 0
    prev_p = None
    for p, y in pairs:
        if prev_p is not None and p != prev_p:
            points.append((fp / neg, tp / pos))
        if y == 1:
            tp += 1
        else:
            fp += 1
        prev_p = p
    points.append((fp / neg, tp / pos))
    if points[-1] != (1.0, 1.0):
        points.append((1.0, 1.0))
    return points


def roc_auc(preds: list[float], reals: list[int]) -> float:
    """Mann-Whitney U: AUC = P(pred_pos > pred_neg) + 0.5 P(tie)."""
    n = len(reals)
    if n == 0 or len(preds) != n:
        return 0.5
    pos = [p for p, y in zip(preds, reals) if y == 1]
    neg = [p for p, y in zip(preds, reals) if y == 0]
    if not pos or not neg:
        return 0.5

    wins = 0.0
    for pp in pos:
        for pn in neg:
            if pp > pn:
                wins += 1.0
            elif pp == pn:
                wins += 0.5
    return wins / (len(pos) * len(neg))
