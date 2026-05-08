#!/usr/bin/env python3
"""BART baseline (Phase 2 paper TODO).

Tries pymc-bart first (BART proper). If unavailable / too slow / OOM, falls
back HONESTLY to sklearn GradientBoostingClassifier (labelled as 'GBM proxy').

Year-fold CV identical to scripts/autoresearch_political.py: leave one cycle
out, train on the rest + 'other_pool' qualitative events, test on the held
cycle.

Features:
  - poll_lead_pp   (continuous)
  - days_to        (continuous, 0..30 due to filter)
  - incumbente     (binary)
  - regime         (one-hot: left/center/right)
  - uf             (one-hot, full vocab from train+test)

Target:
  - outcome (binary)

Output: data/bench_bart.json

Seed: 42.
"""
from __future__ import annotations
import json
import os
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

# Reuse the canonical loaders from autoresearch_political so dataset is
# byte-identical to the rest of the gauntlet.
from scripts.autoresearch_political import (  # type: ignore
    load_by_year,
    load_other_pool,
)

SEED = 42
np.random.seed(SEED)

OUT_PATH = ROOT / "data" / "bench_bart.json"

# ---------------------------------------------------------------------------
# Library detection
# ---------------------------------------------------------------------------

def detect_bart():
    """Return (backend_name, modules_or_None, note)."""
    try:
        import pymc as pm  # noqa: F401
        import pymc_bart as pmb  # noqa: F401
        return "pymc_bart", (pm, pmb), "pymc-bart available"
    except Exception as e:  # pragma: no cover
        return "gbm_proxy", None, (
            f"pymc-bart unavailable ({type(e).__name__}: {e}); "
            "using sklearn GradientBoostingClassifier as honest GBM proxy"
        )


# ---------------------------------------------------------------------------
# Feature engineering
# ---------------------------------------------------------------------------

REGIMES = ["left", "center", "right"]


def event_to_features(events, uf_vocab) -> np.ndarray:
    rows = []
    for e in events:
        lead = float(e.get("poll_lead_pp", 0.0))
        days = float(e.get("days_to", 30))
        inc = float(e.get("incumbente", 0))
        reg = e.get("regime", "center")
        reg_oh = [1.0 if reg == r else 0.0 for r in REGIMES]
        uf = e.get("uf", "BR")
        uf_oh = [1.0 if uf == u else 0.0 for u in uf_vocab]
        rows.append([lead, days, inc, *reg_oh, *uf_oh])
    return np.asarray(rows, dtype=float)


def feature_names(uf_vocab) -> list[str]:
    return ["poll_lead_pp", "days_to", "incumbente",
            *[f"regime_{r}" for r in REGIMES],
            *[f"uf_{u}" for u in uf_vocab]]


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------

def fit_predict_pymc_bart(X_tr, y_tr, X_te, *, draws: int, tune: int,
                          n_trees: int):
    import pymc as pm
    import pymc_bart as pmb

    with pm.Model() as model:
        X_data = pm.Data("X", X_tr)
        mu = pmb.BART("mu", X=X_data, Y=y_tr.astype(float), m=n_trees)
        p = pm.Deterministic("p", pm.math.sigmoid(mu))
        _ = pm.Bernoulli("y_obs", p=p, observed=y_tr)
        idata = pm.sample(draws=draws, tune=tune, chains=1, cores=1,
                          random_seed=SEED, progressbar=False,
                          compute_convergence_checks=False)
        pm.set_data({"X": X_te})
        ppc = pm.sample_posterior_predictive(idata, var_names=["p"],
                                             predictions=True,
                                             random_seed=SEED,
                                             progressbar=False)
    p_post = ppc.predictions["p"].values  # (chain, draw, n_test)
    p_mean = p_post.mean(axis=(0, 1))
    return np.clip(p_mean, 1e-4, 1 - 1e-4)


def fit_predict_gbm(X_tr, y_tr, X_te):
    from sklearn.ensemble import GradientBoostingClassifier
    clf = GradientBoostingClassifier(
        n_estimators=200,
        max_depth=3,
        learning_rate=0.05,
        random_state=SEED,
    )
    clf.fit(X_tr, y_tr)
    p = clf.predict_proba(X_te)[:, 1]
    return np.clip(p, 1e-4, 1 - 1e-4), clf


# ---------------------------------------------------------------------------
# Evaluation
# ---------------------------------------------------------------------------

def eval_metrics(y_true, p):
    y = np.asarray(y_true, dtype=int)
    p = np.asarray(p, dtype=float)
    n = len(y)
    if n == 0:
        return {"n": 0, "brier": 0.0, "acc": 0.0, "log_loss": 0.0}
    brier = float(np.mean((p - y) ** 2))
    acc = float(np.mean((p >= 0.5).astype(int) == y))
    log_loss = float(np.mean(-(y * np.log(np.clip(p, 1e-9, 1))
                              + (1 - y) * np.log(np.clip(1 - p, 1e-9, 1)))))
    return {"n": n, "brier": brier, "acc": acc, "log_loss": log_loss}


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print(f"[bench_bart] seed={SEED}")
    backend, _mods, note = detect_bart()
    forced = os.environ.get("BENCH_BART_BACKEND")
    if forced in {"pymc_bart", "gbm_proxy"}:
        backend = forced
        note = f"forced via env BENCH_BART_BACKEND={forced}"
    print(f"[bench_bart] backend={backend}  ({note})")

    by_year = load_by_year()
    other = load_other_pool()
    years = sorted(by_year.keys())
    print(f"[bench_bart] years={years}  n_per_year=" +
          str({y: len(by_year[y]) for y in years}))
    print(f"[bench_bart] other_pool={len(other)}")

    all_events = list(other) + [e for y in years for e in by_year[y]]
    uf_vocab = sorted({e.get("uf", "BR") for e in all_events})
    feat_names = feature_names(uf_vocab)
    print(f"[bench_bart] features={len(feat_names)}  uf_vocab={uf_vocab}")

    other_with_y = [e for e in other if "outcome" in e and e["outcome"] in (0, 1)]
    print(f"[bench_bart] other_with_outcome={len(other_with_y)}")

    # BART config (kept light to keep total wall-time reasonable across folds).
    bart_cfg = {"draws": 150, "tune": 150, "n_trees": 50}

    per_cycle = {}
    fit_times = []
    pred_times = []
    n_params_estimate = None

    for y in years:
        train_events = list(other_with_y)
        for y2 in years:
            if y2 != y:
                train_events.extend(by_year[y2])
        test_events = by_year[y]

        X_tr = event_to_features(train_events, uf_vocab)
        y_tr = np.asarray([int(e["outcome"]) for e in train_events], dtype=int)
        X_te = event_to_features(test_events, uf_vocab)
        y_te = np.asarray([int(e["outcome"]) for e in test_events], dtype=int)

        print(f"[bench_bart] fold y={y}  train={X_tr.shape}  test={X_te.shape}  "
              f"pos_rate_tr={y_tr.mean():.3f}  pos_rate_te={y_te.mean():.3f}")

        backend_used = backend
        try:
            t0 = time.time()
            if backend == "pymc_bart":
                p_pred = fit_predict_pymc_bart(X_tr, y_tr, X_te, **bart_cfg)
                t_fit = time.time() - t0
                if n_params_estimate is None:
                    n_params_estimate = bart_cfg["n_trees"] * 8
                t_pred_per = 0.0  # predict happens inside fit (posterior pred)
            else:
                p_pred, clf_obj = fit_predict_gbm(X_tr, y_tr, X_te)
                t_fit = time.time() - t0
                if n_params_estimate is None:
                    n_params_estimate = 200 * 7
                t1 = time.time()
                _ = clf_obj.predict_proba(X_te)
                t_pred_per = (time.time() - t1) * 1000.0 / max(len(X_te), 1)
        except Exception as exc:
            print(f"[bench_bart] fold y={y} failed in backend={backend}: {exc!r}")
            print(f"[bench_bart] falling back to GBM proxy for this fold")
            backend_used = "gbm_proxy"
            t0 = time.time()
            p_pred, clf_obj = fit_predict_gbm(X_tr, y_tr, X_te)
            t_fit = time.time() - t0
            n_params_estimate = n_params_estimate or 200 * 7
            t1 = time.time()
            _ = clf_obj.predict_proba(X_te)
            t_pred_per = (time.time() - t1) * 1000.0 / max(len(X_te), 1)

        m = eval_metrics(y_te, p_pred)
        m["fit_time_s"] = round(t_fit, 3)
        m["predict_time_ms_per_event"] = round(t_pred_per, 4)
        m["backend"] = backend_used
        per_cycle[y] = m
        fit_times.append(t_fit)
        pred_times.append(t_pred_per)

        print(f"[bench_bart] fold y={y}  brier={m['brier']:.4f}  acc={m['acc']:.4f}  "
              f"ll={m['log_loss']:.4f}  fit={m['fit_time_s']}s  "
              f"pred={m['predict_time_ms_per_event']}ms/ev  backend={backend_used}")

    n_total = sum(per_cycle[y]["n"] for y in years)
    brier_avg = sum(per_cycle[y]["brier"] * per_cycle[y]["n"] for y in years) / max(n_total, 1)
    acc_avg = sum(per_cycle[y]["acc"] * per_cycle[y]["n"] for y in years) / max(n_total, 1)
    ll_avg = sum(per_cycle[y]["log_loss"] * per_cycle[y]["n"] for y in years) / max(n_total, 1)

    out = {
        "model": "BART" if backend == "pymc_bart" else "GBM_proxy",
        "backend": backend,
        "backend_note": note,
        "honest_proxy": backend == "gbm_proxy",
        "seed": SEED,
        "features": feat_names,
        "n_features": len(feat_names),
        "n_params_estimate": n_params_estimate,
        "bart_config": bart_cfg if backend == "pymc_bart" else None,
        "years": years,
        "n_per_cycle": {y: per_cycle[y]["n"] for y in years},
        "per_cycle": per_cycle,
        "summary": {
            "n": n_total,
            "brier_avg": round(brier_avg, 6),
            "acc_avg": round(acc_avg, 6),
            "log_loss_avg": round(ll_avg, 6),
            "fit_time_s_total": round(sum(fit_times), 3),
            "predict_time_ms_per_event_avg": round(float(np.mean(pred_times)) if pred_times else 0.0, 4),
        },
    }

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(out, indent=2))
    print(f"[bench_bart] wrote {OUT_PATH}")
    print(f"[bench_bart] SUMMARY  brier_avg={brier_avg:.4f}  acc_avg={acc_avg:.4f}  "
          f"backend={backend}  honest_proxy={backend == 'gbm_proxy'}")


if __name__ == "__main__":
    main()
