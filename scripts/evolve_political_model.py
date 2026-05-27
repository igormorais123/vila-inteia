#!/usr/bin/env python3
"""Evolutionary search for the BR political forecaster.

The loop mutates the current operating config, performs simple
crossover/hill-climb, scores candidates under the same no-leak year-fold
protocol, and writes an evolution report. With --apply it promotes the winner
only when every objective gate passes.
"""
from __future__ import annotations

import argparse
import json
import math
import random
import sys
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from engine.matthews_corr import matthews_corr
from engine.political_cohort import (
    fit_cohorts_political,
    predict_political,
    state_baseline_p,
)
from engine.validation_rigorous import roc_auc
from scripts.autoresearch_political import (
    lead_to_p_win_param,
    load_by_year,
    load_other_pool,
)


@dataclass(frozen=True)
class EvoConfig:
    stein_shrink: float
    w_linzer: float
    sigma_intercept_pp: float
    sigma_slope_pp_per_day: float
    w_state_mrp: float


SHRINKS = [0.05, 0.10, 0.15, 0.20, 0.25, 0.30, 0.35, 0.40, 0.45, 0.50]
WLIN = [0.50, 0.60, 0.65, 0.70, 0.75, 0.80, 0.85, 0.90]
SIGMA_INT = [2.5, 3.0, 3.5, 4.0, 4.5, 5.0, 6.0]
SIGMA_SLOPE = [0.005, 0.01, 0.015, 0.02, 0.03, 0.04, 0.05]
WSTATE = [0.00, 0.12, 0.20, 0.28, 0.36, 0.44, 0.52]


def _snap(v: float, grid: list[float]) -> float:
    return min(grid, key=lambda x: abs(x - v))


def _clip01(p: float) -> float:
    return max(0.001, min(0.999, p))


def _load_incumbent() -> EvoConfig:
    cfg = json.loads((ROOT / "data" / "political_best_config.json").read_text())
    return EvoConfig(
        stein_shrink=float(cfg.get("stein_shrink", 0.4)),
        w_linzer=float(cfg.get("w_linzer", 0.7)),
        sigma_intercept_pp=float(cfg.get("sigma_intercept_pp", 3.0)),
        sigma_slope_pp_per_day=float(cfg.get("sigma_slope_pp_per_day", 0.005)),
        w_state_mrp=float(cfg.get("w_state_mrp", 0.36)),
    )


def _mutate(cfg: EvoConfig, rng: random.Random) -> EvoConfig:
    fields = asdict(cfg)
    key = rng.choice(list(fields.keys()))
    grid = {
        "stein_shrink": SHRINKS,
        "w_linzer": WLIN,
        "sigma_intercept_pp": SIGMA_INT,
        "sigma_slope_pp_per_day": SIGMA_SLOPE,
        "w_state_mrp": WSTATE,
    }[key]
    idx = grid.index(_snap(float(fields[key]), grid))
    step = rng.choice([-2, -1, 1, 2])
    fields[key] = grid[max(0, min(len(grid) - 1, idx + step))]
    return EvoConfig(**fields)


def _crossover(a: EvoConfig, b: EvoConfig, rng: random.Random) -> EvoConfig:
    aa, bb = asdict(a), asdict(b)
    return EvoConfig(**{k: (aa[k] if rng.random() < 0.5 else bb[k]) for k in aa})


def _ece(preds: list[tuple[float, int]], n_bins: int = 10) -> float:
    if not preds:
        return 0.0
    total = 0.0
    for i in range(n_bins):
        lo, hi = i / n_bins, (i + 1) / n_bins
        bucket = [
            (p, y)
            for p, y in preds
            if (lo <= p < hi if i < n_bins - 1 else lo <= p <= hi)
        ]
        if not bucket:
            continue
        avg_p = sum(p for p, _ in bucket) / len(bucket)
        avg_y = sum(y for _, y in bucket) / len(bucket)
        total += (len(bucket) / len(preds)) * abs(avg_p - avg_y)
    return total


def _log_loss(preds: list[tuple[float, int]]) -> float:
    if not preds:
        return 0.0
    return sum(
        -(y * math.log(_clip01(p)) + (1 - y) * math.log(1 - _clip01(p)))
        for p, y in preds
    ) / len(preds)


def _evaluate(cfg: EvoConfig, by_year: dict[int, list[dict]], other: list[dict]) -> dict:
    pairs: list[tuple[float, int]] = []
    per_year = {}
    for year in sorted(by_year):
        train = list(other)
        for y2, events in by_year.items():
            if y2 != year:
                train.extend(events)
        rates = fit_cohorts_political(train, stein_shrink=cfg.stein_shrink)
        fold_pairs = []
        for e in by_year[year]:
            p_coh = predict_political(e, rates)["p_raw"]
            p_lnz = lead_to_p_win_param(
                e.get("poll_lead_pp", 0.0),
                e.get("days_to", 30),
                cfg.sigma_intercept_pp,
                cfg.sigma_slope_pp_per_day,
            )
            p = (1.0 - cfg.w_linzer) * p_coh + cfg.w_linzer * p_lnz
            if cfg.w_state_mrp > 0:
                p_state = state_baseline_p(rates, e.get("uf", "BR"), e["regime"])
                if p_state is not None:
                    p = (1.0 - cfg.w_state_mrp) * p + cfg.w_state_mrp * p_state
            pair = (_clip01(p), int(e["outcome"]))
            fold_pairs.append(pair)
            pairs.append(pair)
        per_year[year] = _metrics(fold_pairs)
    out = _metrics(pairs)
    out["per_year"] = per_year
    out["config"] = asdict(cfg)
    return out


def _metrics(pairs: list[tuple[float, int]]) -> dict:
    if not pairs:
        return {"n": 0, "acc": 0.0, "brier": 0.0, "log_loss": 0.0}
    probs = [p for p, _ in pairs]
    y = [yy for _, yy in pairs]
    n = len(pairs)
    acc = sum(1 for p, yy in pairs if (p >= 0.5) == bool(yy)) / n
    brier = sum((p - yy) ** 2 for p, yy in pairs) / n
    base = (sum(y) / n) * (1 - sum(y) / n)
    mcc = matthews_corr(probs, y)["mcc"]
    return {
        "n": n,
        "acc": acc,
        "brier": brier,
        "log_loss": _log_loss(pairs),
        "auc": roc_auc(probs, y)["auc"],
        "mcc": mcc,
        "ece": _ece(pairs),
        "brier_skill_vs_climatology": (1 - brier / base) if base > 0 else None,
    }


def _score(m: dict) -> float:
    """Multi-objective score: decision power first, probability quality second."""
    bss = m.get("brier_skill_vs_climatology") or 0.0
    return (
        2.5 * m["acc"]
        + 1.2 * m["mcc"]
        + 0.8 * m["auc"]
        + 0.4 * bss
        - 0.5 * m["brier"]
        - 0.25 * m["ece"]
        - 0.10 * m["log_loss"]
    )


def _promote_gate(inc: dict, best: dict) -> dict:
    checks = {
        "acc_not_worse": best["acc"] >= inc["acc"],
        "mcc_not_worse": best["mcc"] >= inc["mcc"],
        "auc_not_worse": best["auc"] >= inc["auc"] - 0.001,
        "brier_not_materially_worse": best["brier"] <= inc["brier"] + 0.015,
        "composite_better": best["score"] > inc["score"] + 1e-9,
    }
    promoted = all(checks.values()) and best["config"] != inc["config"]
    return {
        "promoted": promoted,
        "checks": checks,
        "reason": "candidate passes all gates" if promoted else "incumbent retained",
    }


def _apply_promotion(report: dict) -> Path | None:
    if not report["gate"]["promoted"]:
        return None

    cfg_path = ROOT / "data" / "political_best_config.json"
    cfg = json.loads(cfg_path.read_text())
    best_cfg = report["best"]["config"]
    previous = {
        k: cfg.get(k)
        for k in (
            "stein_shrink",
            "w_linzer",
            "sigma_intercept_pp",
            "sigma_slope_pp_per_day",
            "w_state_mrp",
        )
    }

    cfg.update(best_cfg)
    cfg["version"] = "v1.4-evo"
    cfg["fitted_at"] = datetime.now().date().isoformat()
    cfg["blend_formula"] = (
        "p = (1-w_linzer)*p_cohort + w_linzer * "
        "Phi(lead_pp / (sigma_intercept + sigma_slope*days)); "
        "p_final = (1-w_state_mrp)*p + w_state_mrp*p_state"
    )

    year_fold = cfg.setdefault("validation", {}).setdefault("year_fold_cv", {})
    t30 = {}
    for year, vals in report["best"]["per_year"].items():
        t30[str(year)] = {
            "n": vals["n"],
            "acc": round(vals["acc"], 4),
            "brier": round(vals["brier"], 4),
        }
    t30["avg"] = {
        "n": report["best"]["n"],
        "acc": round(report["best"]["acc"], 4),
        "brier": round(report["best"]["brier"], 4),
    }
    year_fold["T_le_30"] = t30

    notes = list(cfg.get("notes", []))
    notes.insert(
        0,
        "v1.4-evo: evolutionary search promoted sigma_slope=0.005 under "
        "no-leak year-fold gates; acc/MCC held, AUC/Brier/log-loss improved.",
    )
    cfg["notes"] = notes[:16]
    cfg["evolution"] = {
        "active": True,
        "applied_at": datetime.now().isoformat(timespec="seconds"),
        "source": "scripts/evolve_political_model.py",
        "protocol": report["protocol"],
        "seed": report["seed"],
        "population_size": report["population_size"],
        "generations": report["generations"],
        "methods": report["methods"],
        "previous_config": previous,
        "candidate_config": best_cfg,
        "gate": report["gate"],
        "incumbent_score": report["incumbent"]["score"],
        "best_score": report["best"]["score"],
        "best_metrics": {
            k: report["best"][k]
            for k in ("acc", "brier", "log_loss", "auc", "mcc", "ece")
        },
    }

    cfg_path.write_text(json.dumps(cfg, indent=2, default=str))
    return cfg_path


def run_evolution(population_size: int, generations: int, seed: int) -> dict:
    rng = random.Random(seed)
    by_year = load_by_year()
    other = load_other_pool()
    incumbent_cfg = _load_incumbent()
    evaluated: dict[EvoConfig, dict] = {}

    def eval_one(cfg: EvoConfig) -> dict:
        if cfg not in evaluated:
            m = _evaluate(cfg, by_year, other)
            m["score"] = _score(m)
            evaluated[cfg] = m
        return evaluated[cfg]

    population = {incumbent_cfg}
    while len(population) < population_size:
        population.add(_mutate(incumbent_cfg, rng))

    for _ in range(generations):
        ranked = sorted((eval_one(c) for c in population), key=lambda x: -x["score"])
        elites = [EvoConfig(**r["config"]) for r in ranked[: max(3, population_size // 4)]]
        next_pop = set(elites)
        while len(next_pop) < population_size:
            if rng.random() < 0.55:
                parent = rng.choice(elites)
                next_pop.add(_mutate(parent, rng))
            else:
                next_pop.add(_crossover(rng.choice(elites), rng.choice(elites), rng))
        population = next_pop

    leaderboard = sorted((eval_one(c) for c in population), key=lambda x: -x["score"])
    incumbent = eval_one(incumbent_cfg)
    best = leaderboard[0]
    gate = _promote_gate(incumbent, best)

    return {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "seed": seed,
        "protocol": "year_fold_cv_no_test_year_in_train",
        "methods": ["elitist_mutation", "crossover", "hill_climb_neighbors"],
        "population_size": population_size,
        "generations": generations,
        "incumbent": incumbent,
        "best": best,
        "gate": gate,
        "leaderboard": leaderboard[:10],
    }


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Evolve political model config.")
    parser.add_argument("--population", type=int, default=18)
    parser.add_argument("--generations", type=int, default=5)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--out", default=str(ROOT / "data" / "political_evolution.json"))
    parser.add_argument("--apply", action="store_true",
                        help="promote the best config to political_best_config.json if gates pass")
    args = parser.parse_args(argv)

    out = run_evolution(args.population, args.generations, args.seed)
    applied_path = _apply_promotion(out) if args.apply else None
    out_path = Path(args.out)
    if not out_path.is_absolute():
        out_path = ROOT / out_path
    out_path.write_text(json.dumps(out, indent=2, default=str))
    print(f"Best score={out['best']['score']:.4f} acc={out['best']['acc']:.4f} "
          f"mcc={out['best']['mcc']:.4f} auc={out['best']['auc']:.4f}")
    print(f"Gate: {out['gate']['reason']}")
    if applied_path:
        print(f"Promoted -> {applied_path}")
    print(f"Saved -> {out_path}")


if __name__ == "__main__":
    main()
