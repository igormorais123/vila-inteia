#!/usr/bin/env python3
"""Phase 1 - publish-grade statistical rigor for Vila MRP political prediction.

Bootstrap CIs (1000 resamples), Diebold-Mariano test (squared loss),
McNemar paired-accuracy test, Murphy decomposition (10 bins).

Config read from data/political_best_config.json (stein=0.4, w_lin=0.7,
sint=3.0, sslo=0.01, w_state_mrp=0.36) reproducing autoresearch best.
"""
from __future__ import annotations
import json
import math
import sys
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from engine.political_cohort import (
    fit_cohorts_political, predict_political, state_baseline_p,
)
from scripts.autoresearch_political import (
    load_by_year, load_other_pool, lead_to_p_win_param,
)

CFG = json.load(open(ROOT / "data" / "political_best_config.json"))
SHRINK = CFG["stein_shrink"]
WLIN = CFG["w_linzer"]
SINT = CFG["sigma_intercept_pp"]
SSLO = CFG["sigma_slope_pp_per_day"]
W_MRP = CFG["w_state_mrp"]
SEED = 42


def predict_one(e: dict, rates: dict, w_state: float) -> float:
    pred = predict_political(e, rates)
    p_coh = pred["p_raw"]
    p_lnz = lead_to_p_win_param(e.get("poll_lead_pp", 0.0),
                                e.get("days_to", 30), SINT, SSLO)
    p = (1 - WLIN) * p_coh + WLIN * p_lnz
    if w_state > 0:
        ps = state_baseline_p(rates, e.get("uf", "BR"), e["regime"])
        if ps is not None:
            p = (1 - w_state) * p + w_state * ps
    return p


def year_fold(by_year, other, w_state):
    out = {}
    for y in sorted(by_year):
        train = list(other)
        for y2 in by_year:
            if y2 != y:
                train.extend(by_year[y2])
        rates = fit_cohorts_political(train, stein_shrink=SHRINK)
        out[y] = [(predict_one(e, rates, w_state), e["outcome"])
                  for e in by_year[y]]
    return out


def brier(preds):
    return float(np.mean([(p - y) ** 2 for p, y in preds]))


def acc(preds):
    return float(np.mean([(p >= 0.5) == bool(y) for p, y in preds]))


def boot_ci(preds, n=1000):
    rng = np.random.default_rng(SEED)
    if len(preds) == 0:
        return {"brier_ci": [None, None], "acc_ci": [None, None]}
    arr = np.array(preds)
    briers, accs = [], []
    for _ in range(n):
        idx = rng.integers(0, len(arr), len(arr))
        s = arr[idx]
        briers.append(float(np.mean((s[:, 0] - s[:, 1]) ** 2)))
        accs.append(float(np.mean((s[:, 0] >= 0.5) == s[:, 1].astype(bool))))
    return {
        "brier_point": float(np.mean(briers)),
        "brier_ci": [float(np.percentile(briers, 2.5)),
                     float(np.percentile(briers, 97.5))],
        "acc_point": float(np.mean(accs)),
        "acc_ci": [float(np.percentile(accs, 2.5)),
                   float(np.percentile(accs, 97.5))],
    }


def dm_test(a, b):
    """Squared-loss Diebold-Mariano. a baseline, b challenger."""
    la = np.array([(p - y) ** 2 for p, y in a])
    lb = np.array([(p - y) ** 2 for p, y in b])
    d = la - lb
    n = len(d)
    if n < 2 or np.var(d, ddof=1) == 0:
        return {"dm": 0.0, "p": 1.0, "n": n}
    dm = float(np.mean(d) / math.sqrt(np.var(d, ddof=1) / n))
    p = 2 * (1 - 0.5 * (1 + math.erf(abs(dm) / math.sqrt(2))))
    interp = ("MRP better - significant" if dm > 0 and p < 0.05 else
              "MRP better - not sig" if dm > 0 else
              "baseline better - significant" if p < 0.05 else
              "baseline better - not sig")
    return {"dm": dm, "p": float(p), "n": n,
            "mean_brier_diff": float(np.mean(d)), "interp": interp}


def mcnemar(a, b):
    bb = cc = 0
    for (pa, ya), (pb, yb) in zip(a, b):
        ca = (pa >= 0.5) == bool(ya)
        cb = (pb >= 0.5) == bool(yb)
        if not ca and cb:
            bb += 1
        elif ca and not cb:
            cc += 1
    n = bb + cc
    if n == 0:
        return {"chi2": 0.0, "p": 1.0, "b": 0, "c": 0}
    chi2 = (abs(bb - cc) - 0.5) ** 2 / n
    p = math.erfc(math.sqrt(chi2 / 2))
    interp = ("MRP improves - sig" if bb > cc and p < 0.05 else
              "MRP improves - not sig" if bb > cc else
              "baseline improves - sig" if p < 0.05 else
              "baseline improves - not sig")
    return {"chi2": float(chi2), "p": float(p),
            "b_baseline_wrong_mrp_right": bb,
            "c_baseline_right_mrp_wrong": cc, "n_disc": n,
            "interp": interp}


def murphy(preds, k=10):
    arr = np.array(preds)
    p_, y_ = arr[:, 0], arr[:, 1]
    n = len(p_)
    o_bar = float(np.mean(y_))
    bins = np.linspace(0, 1, k + 1)
    rel = res = 0.0
    for i in range(k):
        if i < k - 1:
            mask = (p_ >= bins[i]) & (p_ < bins[i + 1])
        else:
            mask = (p_ >= bins[i]) & (p_ <= bins[i + 1])
        nk = int(mask.sum())
        if nk == 0:
            continue
        pk = float(np.mean(p_[mask]))
        ok = float(np.mean(y_[mask]))
        rel += nk * (pk - ok) ** 2
        res += nk * (ok - o_bar) ** 2
    rel /= n
    res /= n
    unc = o_bar * (1 - o_bar)
    bact = float(np.mean((p_ - y_) ** 2))
    return {"REL": float(rel), "RES": float(res), "UNC": float(unc),
            "BRIER_decomposed": float(rel - res + unc),
            "BRIER_actual": bact,
            "identity_check": abs((rel - res + unc) - bact) < 1e-9}


def main():
    print(f"Config: stein={SHRINK} wlin={WLIN} sint={SINT} sslo={SSLO} w_state={W_MRP} seed={SEED}\n")
    by_year = load_by_year()
    other = load_other_pool()
    print(f"Train: {sum(len(v) for v in by_year.values())} year + {len(other)} qual events\n")

    base = year_fold(by_year, other, w_state=0.0)
    mrp = year_fold(by_year, other, w_state=W_MRP)

    all_b = [pp for ps in base.values() for pp in ps]
    all_m = [pp for ps in mrp.values() for pp in ps]
    print(f"baseline (w_state=0): brier={brier(all_b):.4f} acc={acc(all_b):.4f}")
    print(f"MRP      (w_state={W_MRP}): brier={brier(all_m):.4f} acc={acc(all_m):.4f}\n")

    print("Bootstrap 1000 per cycle...")
    boot_b = {y: boot_ci(base[y]) for y in base}
    boot_m = {y: boot_ci(mrp[y]) for y in mrp}
    for y in sorted(boot_m):
        b = boot_m[y]
        print(f"  {y}: brier {b['brier_point']:.4f} CI [{b['brier_ci'][0]:.4f}, {b['brier_ci'][1]:.4f}]  "
              f"acc {b['acc_point']:.4f} CI [{b['acc_ci'][0]:.4f}, {b['acc_ci'][1]:.4f}]")

    print("\nDM + McNemar (paired):")
    dm = dm_test(all_b, all_m)
    mc = mcnemar(all_b, all_m)
    print(f"  DM stat={dm['dm']:.4f} p={dm['p']:.4e} - {dm['interp']}")
    print(f"  McNemar chi2={mc['chi2']:.4f} p={mc['p']:.4e} b={mc['b_baseline_wrong_mrp_right']} c={mc['c_baseline_right_mrp_wrong']} - {mc['interp']}")

    print("\nMurphy per cycle (MRP):")
    mu_b = {y: murphy(base[y]) for y in base}
    mu_m = {y: murphy(mrp[y]) for y in mrp}
    for y in sorted(mu_m):
        m = mu_m[y]
        print(f"  {y}: REL={m['REL']:.4f} RES={m['RES']:.4f} UNC={m['UNC']:.4f} brier={m['BRIER_actual']:.4f}")

    out = {
        "config": {"stein": SHRINK, "w_linzer": WLIN, "sigma_int": SINT,
                   "sigma_slope": SSLO, "w_state_mrp": W_MRP, "seed": SEED},
        "summary": {
            "baseline": {"brier": brier(all_b), "acc": acc(all_b), "n": len(all_b)},
            "mrp": {"brier": brier(all_m), "acc": acc(all_m), "n": len(all_m)},
        },
        "bootstrap_1000": {"baseline": boot_b, "mrp": boot_m},
        "diebold_mariano": dm,
        "mcnemar": mc,
        "murphy_per_cycle": {"baseline": mu_b, "mrp": mu_m},
    }
    out_p = ROOT / "data" / "political_stats_v2.json"
    with open(out_p, "w") as f:
        json.dump(out, f, indent=2, default=str)
    print(f"\nSaved -> {out_p}")


if __name__ == "__main__":
    main()
