#!/usr/bin/env python3
"""Walk-forward backtest of the political cohort forecaster.

Train on a leave-one-out basis across BR political CSVs in data/backtest/:
  - eleicao_presidencial_br_2022.csv  (cargo: presidente)
  - impeachment_dilma_2016.csv        (cargo: impeachment)
  - lava_jato_2014_2018.csv           (cargo: legislativo)
  - seed_eleicao_municipal_sp_2024.csv(cargo: prefeito)
  - brazil_votes_q1_2026.csv          (cargo: legislativo)

Outputs JSON with per-event preds, brier, acc, log-loss, plus selective sweep.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from engine.political_cohort import (
    load_csv_events, fit_cohorts_political, evaluate_political,
    selective_metrics, predict_political,
)

CSV_MAP = {
    "presidente":   "data/backtest/eleicao_presidencial_br_2022.csv",
    "impeachment":  "data/backtest/impeachment_dilma_2016.csv",
    "legislativo":  "data/backtest/lava_jato_2014_2018.csv",
    "prefeito":     "data/backtest/seed_eleicao_municipal_sp_2024.csv",
    "legislativo_2026": "data/backtest/brazil_votes_q1_2026.csv",
}

def main():
    all_events: list[dict] = []
    by_dataset: dict[str, list] = {}
    for cargo_label, rel in CSV_MAP.items():
        cargo = "legislativo" if "legislativo" in cargo_label else cargo_label
        path = ROOT / rel
        if not path.exists():
            print(f"[skip] {path} not found", file=sys.stderr)
            continue
        evs = load_csv_events(path, cargo=cargo)
        for e in evs: e["dataset"] = cargo_label
        by_dataset[cargo_label] = evs
        all_events.extend(evs)

    print(f"Loaded {len(all_events)} events from {len(by_dataset)} datasets")

    # ---- Holdout: leave-one-dataset-out cross validation ---------------------
    loo_results = {}
    for held in by_dataset:
        train = [e for k, evs in by_dataset.items() if k != held for e in evs]
        test  = by_dataset[held]
        rates = fit_cohorts_political(train, stein_shrink=0.15)
        ev = evaluate_political(test, rates)
        loo_results[held] = {
            "n_train": len(train),
            "n_test": ev["n"],
            "brier":  round(ev["brier"], 4),
            "log_loss": round(ev["log_loss"], 4),
            "acc":    round(ev["acc"], 4),
        }
        print(f"[LOO held={held}] train={len(train)} test={ev['n']} "
              f"brier={ev['brier']:.4f} ll={ev['log_loss']:.4f} acc={ev['acc']:.3f}")

    # ---- Full fit + in-sample resub error -----------------------------------
    full_rates = fit_cohorts_political(all_events, stein_shrink=0.15)
    full_eval = evaluate_political(all_events, full_rates)
    print(f"\n[FULL FIT in-sample] n={full_eval['n']} brier={full_eval['brier']:.4f} "
          f"ll={full_eval['log_loss']:.4f} acc={full_eval['acc']:.3f}")

    # ---- Selective sweep -----------------------------------------------------
    sweep = []
    for tau in [0.0, 0.05, 0.10, 0.15, 0.20, 0.25, 0.30, 0.35, 0.40]:
        sweep.append(selective_metrics(full_eval["preds"], tau))
    print("\n[SELECTIVE SWEEP]")
    print(f"{'tau':>6} {'cov':>8} {'n':>5} {'acc':>8} {'brier':>8}")
    for s in sweep:
        cov = f"{s['coverage']:.3f}" if s.get('coverage') is not None else "-"
        acc = f"{s['acc']:.3f}" if s.get('acc') is not None else "-"
        brier = f"{s['brier']:.4f}" if s.get('brier') is not None else "-"
        print(f"{s['tau']:>6.2f} {cov:>8} {s['n_kept']:>5} {acc:>8} {brier:>8}")

    # ---- Walk-forward on presidencial 2022 ----------------------------------
    pres = by_dataset.get("presidente", [])
    pres_sorted = sorted(pres, key=lambda x: x["data"])
    walk = []
    for i in range(2, len(pres_sorted)):
        train = [e for ds in by_dataset for e in by_dataset[ds] if ds != "presidente"]
        train += pres_sorted[:i]
        test_ev = pres_sorted[i]
        rates = fit_cohorts_political(train, stein_shrink=0.15)
        pred = predict_political(test_ev, rates)
        walk.append({
            "evento_id": test_ev["evento_id"],
            "data": test_ev["data"],
            "context": test_ev["context"],
            "y": test_ev["outcome"],
            "p_raw": round(pred["p_raw"], 4),
            "tier": pred["tier"],
            "n_cohort": pred["n_cohort"],
            "p_prior_paper": test_ev["p_prior"],
        })
    if walk:
        wbrier = sum((w["p_raw"] - w["y"])**2 for w in walk) / len(walk)
        wacc = sum(1 for w in walk if (w["p_raw"] >= 0.5) == bool(w["y"])) / len(walk)
        print(f"\n[WALK-FORWARD presidencial 2022] n={len(walk)} brier={wbrier:.4f} acc={wacc:.3f}")

    # ---- Save results -------------------------------------------------------
    out = {
        "n_events_total": len(all_events),
        "datasets": {k: len(v) for k, v in by_dataset.items()},
        "leave_one_dataset_out": loo_results,
        "full_fit_in_sample": {
            "brier": round(full_eval["brier"], 4),
            "log_loss": round(full_eval["log_loss"], 4),
            "acc": round(full_eval["acc"], 4),
        },
        "selective_sweep": sweep,
        "walk_forward_presidencial_2022": walk,
        "predictions": full_eval["preds"][:],
    }
    out_path = ROOT / "data" / "political_backtest_results.json"
    out_path.parent.mkdir(exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(out, f, indent=2, default=str)
    print(f"\nSaved -> {out_path}")


if __name__ == "__main__":
    main()
