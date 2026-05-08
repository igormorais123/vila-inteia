#!/usr/bin/env python3
"""Benchmark API + model latency for Vila Politica 2026.

Measures:
  1. Cohort fit time (year-fold sized train pool)
  2. Single-event prediction time
  3. Snapshot regeneration time (predict_2026.py)
  4. API endpoint p50/p95/p99 (via TestClient, no network)
  5. Bootstrap 1000 + DM + McNemar runtime

Output: data/bench_latency.json + console summary.
"""
from __future__ import annotations
import json
import statistics
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import numpy as np
from fastapi.testclient import TestClient
from fastapi import FastAPI

from engine.political_cohort import (
    fit_cohorts_political, predict_political, state_baseline_p,
)
from scripts.autoresearch_political import (
    load_by_year, load_other_pool, lead_to_p_win_param,
)
from api.rotas_politica import router

CFG = json.load(open(ROOT / "data" / "political_best_config.json"))
SHRINK = CFG["stein_shrink"]
WLIN = CFG["w_linzer"]
SINT = CFG["sigma_intercept_pp"]
SSLO = CFG["sigma_slope_pp_per_day"]
W_MRP = CFG["w_state_mrp"]


def time_op(fn, n_warmup=2, n_measure=10):
    """Run fn n_measure times, return p50/p95/p99 in ms."""
    for _ in range(n_warmup):
        fn()
    times = []
    for _ in range(n_measure):
        t0 = time.perf_counter()
        fn()
        times.append((time.perf_counter() - t0) * 1000)
    times.sort()
    return {
        "n": n_measure,
        "mean_ms": statistics.mean(times),
        "p50_ms": times[len(times) // 2],
        "p95_ms": times[int(len(times) * 0.95)],
        "p99_ms": times[min(len(times) - 1, int(len(times) * 0.99))],
        "min_ms": min(times), "max_ms": max(times),
    }


def main():
    print("=== Vila Politica 2026 - Latency Benchmark ===\n")
    by_year = load_by_year()
    other = load_other_pool()
    n_train_total = sum(len(v) for v in by_year.values()) + len(other)
    print(f"Train pool size: {n_train_total} events\n")

    # 1. Cohort fit
    train_full = list(other) + [e for evs in by_year.values() for e in evs]
    fit_lat = time_op(lambda: fit_cohorts_political(train_full, stein_shrink=SHRINK))
    print(f"[1] Cohort fit (n={n_train_total}):  p50={fit_lat['p50_ms']:.2f}ms  "
          f"p95={fit_lat['p95_ms']:.2f}ms")

    rates = fit_cohorts_political(train_full, stein_shrink=SHRINK)

    # 2. Single-event prediction (cohort + Linzer + MRP)
    test_event = {
        "cargo": "presidente", "lead_bin": "L_0_5", "days_bin": "D_leq_30",
        "incumbente": 1, "regime": "left", "uf": "BR", "poll_lead_pp": 5.0,
        "days_to": 30,
    }

    def predict_full():
        pred = predict_political(test_event, rates)
        p_coh = pred["p_raw"]
        p_lnz = lead_to_p_win_param(test_event["poll_lead_pp"],
                                    test_event["days_to"], SINT, SSLO)
        p = (1 - WLIN) * p_coh + WLIN * p_lnz
        ps = state_baseline_p(rates, "BR", "left")
        if ps is not None:
            p = (1 - W_MRP) * p + W_MRP * ps
        return p

    pred_lat = time_op(predict_full, n_measure=1000)
    print(f"[2] Single prediction (full ensemble): p50={pred_lat['p50_ms']:.4f}ms  "
          f"p99={pred_lat['p99_ms']:.4f}ms")

    # 3. Snapshot regeneration (predict_2026 main flow approximation)
    def gen_snapshot():
        from engine.political_cohort import BR_2026_REGISTRY, filter_eligible_candidates
        for cargo, regs in BR_2026_REGISTRY.items():
            elig = filter_eligible_candidates(regs)
            for c in elig:
                ev = {**test_event, "cargo": cargo, "regime": c["regime"],
                      "incumbente": c["incumbente"], "uf": c.get("uf", "BR")}
                predict_political(ev, rates)

    snap_lat = time_op(gen_snapshot, n_measure=20)
    print(f"[3] Snapshot regen (~25 candidates):   p50={snap_lat['p50_ms']:.2f}ms  "
          f"p95={snap_lat['p95_ms']:.2f}ms")

    # 4. API endpoints via TestClient
    app = FastAPI()
    app.include_router(router)
    client = TestClient(app)

    endpoints = [
        ("GET", "/api/v1/politica/health"),
        ("GET", "/api/v1/politica/elections"),
        ("GET", "/api/v1/politica/predictions/presidente"),
        ("GET", "/api/v1/politica/predictions/governador?uf=SP"),
        ("GET", "/api/v1/politica/predictions/senador"),
        ("GET", "/api/v1/politica/backtest"),
    ]

    def make_get(path):
        def fn():
            r = client.get(path)
            assert r.status_code == 200
        return fn

    api_lat = {}
    for method, path in endpoints:
        lat = time_op(make_get(path), n_measure=50)
        api_lat[path] = lat
        print(f"[4] {method} {path:<45} p50={lat['p50_ms']:6.2f}ms  p95={lat['p95_ms']:6.2f}ms  p99={lat['p99_ms']:6.2f}ms")

    def post_predict():
        r = client.post("/api/v1/politica/predict", json={
            "cargo": "governador", "poll_lead_pp": 8, "days_to_election": 45,
            "incumbente": 1, "regime": "right",
        })
        assert r.status_code == 200

    post_lat = time_op(post_predict, n_measure=50)
    print(f"[4] POST /api/v1/politica/predict             p50={post_lat['p50_ms']:6.2f}ms  p95={post_lat['p95_ms']:6.2f}ms")
    api_lat["/api/v1/politica/predict (POST)"] = post_lat

    # 5. Throughput estimate (req/s) for top hot endpoint
    health_p50 = api_lat["/api/v1/politica/health"]["p50_ms"]
    print(f"\nThroughput estimate (single-thread): {1000 / health_p50:.0f} req/s on /health")

    # Save
    out = {
        "config": {
            "shrink": SHRINK, "wlin": WLIN, "sint": SINT, "sslo": SSLO,
            "w_state": W_MRP, "n_train": n_train_total,
        },
        "cohort_fit": fit_lat,
        "single_prediction": pred_lat,
        "snapshot_regen": snap_lat,
        "api_endpoints": api_lat,
    }
    out_path = ROOT / "data" / "bench_latency.json"
    with open(out_path, "w") as f:
        json.dump(out, f, indent=2, default=str)
    print(f"\nSaved -> {out_path}")


if __name__ == "__main__":
    main()
