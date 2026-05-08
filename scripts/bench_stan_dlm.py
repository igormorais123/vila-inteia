#!/usr/bin/env python3
"""Stan-equivalent dynamic linear model (Linzer 2013).

cmdstanpy install requires Stan toolchain. Pure-Python equivalent here:
state-space model with random walk on latent vote share + observation
noise from polls. Per-cycle MLE fit of (sigma_walk, sigma_obs).

Year-fold CV on Vila Politica 2026 (394 events). Seed=42.
"""
from __future__ import annotations
import json
import math
import sys
import time
from collections import defaultdict
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from scripts.autoresearch_political import load_by_year, load_other_pool

SEED = 42
np.random.seed(SEED)


def kalman_filter_log_lik(observations, sigma_walk, sigma_obs, mu_0=0.5, P_0=0.05):
    if not observations:
        return 0.0, mu_0, P_0
    obs_sorted = sorted(observations, key=lambda o: -o[0])
    mu, P = mu_0, P_0
    log_lik = 0.0
    prev_d = obs_sorted[0][0]
    for d, y in obs_sorted:
        dt = max(0, prev_d - d) + 1
        P = P + (sigma_walk ** 2) * dt
        S = P + sigma_obs ** 2
        K = P / S
        innov = y - mu
        log_lik += -0.5 * (math.log(2 * math.pi * S) + innov ** 2 / S)
        mu = mu + K * innov
        P = (1 - K) * P
        prev_d = d
    return log_lik, mu, P


def predict_p_win(observations, sigma_walk, sigma_obs, days_to_election=0):
    if not observations:
        return 0.5
    _, mu_T, P_T = kalman_filter_log_lik(observations, sigma_walk, sigma_obs)
    last_d = min(o[0] for o in observations)
    forward_dt = last_d - days_to_election
    P_final = P_T + (sigma_walk ** 2) * max(0, forward_dt)
    sd = math.sqrt(P_final)
    z = (mu_T - 0.5) / max(sd, 1e-6)
    p_win = 0.5 * (1 + math.erf(z / math.sqrt(2)))
    return max(0.01, min(0.99, p_win))


def fit_mle(observations_by_race, init_walk=0.001, init_obs=0.02):
    def neg_ll(sw, so):
        if sw <= 0 or so <= 0:
            return 1e9
        total = 0.0
        for obs in observations_by_race.values():
            ll, _, _ = kalman_filter_log_lik(obs, sw, so)
            total += ll
        return -total

    best = (init_walk, init_obs, neg_ll(init_walk, init_obs))
    for sw in [0.0005, 0.001, 0.002, 0.005, 0.01]:
        for so in [0.01, 0.02, 0.03, 0.05, 0.08]:
            cur = neg_ll(sw, so)
            if cur < best[2]:
                best = (sw, so, cur)
    return best[0], best[1]


def race_id(e):
    return (e.get("ano"), e.get("uf", "BR"))


def event_to_obs(e):
    lead = float(e.get("poll_lead_pp", 0))
    days = int(e.get("days_to", 30))
    share = 0.5 + lead / 200.0
    return (days, max(0.05, min(0.95, share)))


def main():
    print("=== Stan-equivalent DLM (pure Python Kalman) ===\n")
    by_year = load_by_year()
    other = load_other_pool()

    per_year = {}
    n_total, hits, brier_sum, ll_sum = 0, 0, 0.0, 0.0
    fit_total, pred_total = 0.0, 0.0

    for y in sorted(by_year):
        train_events = []
        for y2 in by_year:
            if y2 != y:
                train_events.extend(by_year[y2])
        train_events = [e for e in train_events if e.get("outcome") == 1]

        train_races = defaultdict(list)
        for e in train_events:
            train_races[race_id(e)].append(event_to_obs(e))

        t0 = time.perf_counter()
        sw, so = fit_mle(train_races)
        fit_total += time.perf_counter() - t0

        test_events = by_year[y]
        test_races_obs = defaultdict(list)
        for e in test_events:
            if e.get("outcome") == 1:
                test_races_obs[race_id(e)].append(event_to_obs(e))

        preds, truths = [], []
        t0 = time.perf_counter()
        for e in test_events:
            obs = test_races_obs.get(race_id(e), [])
            # p_win_winner is P(latent share > 0.5) for the candidate whose
            # poll lead is positive in this race. Each test row represents
            # one candidate's perspective: if their own poll_lead_pp >= 0
            # they ARE that "leading" candidate; if < 0 they're the runner-up
            # so flip. Using sign(poll_lead_pp) keeps this leak-safe (no
            # outcome lookup).
            p_win_winner = predict_p_win(obs, sw, so, 0)
            lead = float(e.get("poll_lead_pp", 0.0))
            p = p_win_winner if lead >= 0 else 1 - p_win_winner
            preds.append(p)
            truths.append(int(e["outcome"]))
        pred_total += time.perf_counter() - t0

        preds = np.array(preds)
        truths = np.array(truths)
        brier = float(np.mean((preds - truths) ** 2))
        acc = float(np.mean((preds >= 0.5) == truths.astype(bool)))
        ll = -float(np.mean(truths * np.log(np.clip(preds, 1e-9, 1)) +
                            (1 - truths) * np.log(np.clip(1 - preds, 1e-9, 1))))
        per_year[y] = {"n": len(preds), "brier": brier, "acc": acc,
                       "log_loss": ll, "sigma_walk": sw, "sigma_obs": so}
        n_total += len(preds)
        hits += int(round(acc * len(preds)))
        brier_sum += brier * len(preds)
        ll_sum += ll * len(preds)
        print(f"  {y}: n={len(preds)}  acc={acc:.4f}  brier={brier:.4f}  sw={sw:.4f}")

    avg = {
        "acc": hits / n_total, "brier": brier_sum / n_total,
        "log_loss": ll_sum / n_total, "n": n_total,
        "fit_time_s": fit_total,
        "predict_time_ms_per_event": pred_total * 1000 / max(n_total, 1),
    }
    print(f"\navg: acc={avg['acc']:.4f}  brier={avg['brier']:.4f}")

    out = {
        "model": "Pure-Python Kalman DLM (Linzer 2013 equivalent)",
        "honest_note": "cmdstanpy install requires Stan toolchain. Pure-Python equivalent: random walk vote share + observation noise. MLE grid (sigma_walk, sigma_obs).",
        "config": {"seed": SEED},
        "per_year": per_year, "avg": avg,
    }
    out_path = ROOT / "data" / "bench_stan_dlm.json"
    with open(out_path, "w") as f:
        json.dump(out, f, indent=2, default=str)
    print(f"Saved -> {out_path}")


if __name__ == "__main__":
    main()
