"""
Onda 114: cross-validation holdout para calibração.

Split 80/20 train/test. Fit Platt em train, avalia em test.
Previne overfit do fit original (que usa mesmas amostras pra fit + eval).
"""

from __future__ import annotations

import random
from typing import Iterable


def split_train_test(
    probs: Iterable[float],
    y: Iterable[int],
    test_frac: float = 0.2,
    seed: int = 42,
) -> tuple[list, list, list, list]:
    """Shuffle + split. Returns (probs_train, y_train, probs_test, y_test)."""
    probs = list(probs); y = list(y)
    idx = list(range(len(probs)))
    rng = random.Random(seed)
    rng.shuffle(idx)
    n_test = max(1, int(len(idx) * test_frac))
    test_idx = idx[:n_test]
    train_idx = idx[n_test:]
    return (
        [probs[i] for i in train_idx],
        [y[i] for i in train_idx],
        [probs[i] for i in test_idx],
        [y[i] for i in test_idx],
    )


def cv_holdout_platt(
    probs: Iterable[float],
    y: Iterable[int],
    test_frac: float = 0.2,
    seed: int = 42,
    n_repeats: int = 10,
) -> dict:
    """
    Repeated hold-out: fit Platt em train, avalia test. N_repeats diferentes seeds.
    Média de metrics test evita overfit.
    """
    from engine.calibracao_platt import fit_platt, aplicar_platt, brier, log_loss, ece
    probs = list(probs); y = list(y)
    if len(probs) < 5:
        return {"erro": "n<5 insuficiente"}

    rng = random.Random(seed)
    briers_train, briers_test = [], []
    logloss_train, logloss_test = [], []
    eces_test = []
    a_list, b_list = [], []

    for i in range(n_repeats):
        s = rng.randint(0, 10**6)
        pt, yt, pv, yv = split_train_test(probs, y, test_frac, seed=s)
        if len(pt) < 3 or len(pv) < 1:
            continue
        a, b = fit_platt(pt, yt)
        a_list.append(a); b_list.append(b)
        # Eval em train
        p_cal_t = aplicar_platt(pt, a, b)
        briers_train.append(brier(p_cal_t, yt))
        logloss_train.append(log_loss(p_cal_t, yt))
        # Eval em test (out-of-sample)
        p_cal_v = aplicar_platt(pv, a, b)
        briers_test.append(brier(p_cal_v, yv))
        logloss_test.append(log_loss(p_cal_v, yv))
        try:
            eces_test.append(ece(p_cal_v, yv, n_bins=max(3, len(pv)//2)))
        except Exception:
            pass

    if not briers_test:
        return {"erro": "nenhum split válido"}

    def _avg(xs): return sum(xs) / len(xs)
    return {
        "n": len(probs),
        "n_repeats": len(briers_test),
        "test_frac": test_frac,
        "brier_train_avg": _avg(briers_train),
        "brier_test_avg": _avg(briers_test),
        "log_loss_train_avg": _avg(logloss_train),
        "log_loss_test_avg": _avg(logloss_test),
        "ece_test_avg": _avg(eces_test) if eces_test else None,
        "platt_a_mean": _avg(a_list),
        "platt_b_mean": _avg(b_list),
        "platt_a_std": (sum((x - _avg(a_list))**2 for x in a_list) / len(a_list)) ** 0.5,
        "platt_b_std": (sum((x - _avg(b_list))**2 for x in b_list) / len(b_list)) ** 0.5,
        "overfit_gap": _avg(briers_test) - _avg(briers_train),
    }
