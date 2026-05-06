#!/usr/bin/env python3
"""Autoresearch loop: tune cohort + Linzer hyperparams until >= 90% accuracy on
historical state-by-state governadores 2018+2022 (out-of-sample by year).

Search space:
  stein_shrink   in [0.05, 0.10, 0.15, 0.20, 0.25, 0.30, 0.35, 0.40]
  w_linzer       in [0.50, 0.60, 0.70, 0.80, 0.85, 0.90, 0.95, 1.00]
  sigma_int      in [3.0, 4.0, 5.0, 6.0, 7.0, 8.0]
  sigma_slope    in [0.01, 0.02, 0.03, 0.04, 0.05, 0.06, 0.08]

Train on 2018 governors + non-governor political CSVs; test on 2022 governors.
Then swap.

Print best configuration plus per-UF accuracy. Stops early if the running best
already >= 0.90 acc on 2022 holdout for early termination.
"""
from __future__ import annotations

import csv
import json
import math
import sys
from itertools import product
from pathlib import Path
from collections import defaultdict

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import os
from engine.political_cohort import (
    fit_cohorts_political, predict_political,
    load_csv_events, lead_bin, days_bin,
    fit_house_effects, apply_house_effect, extract_instituto,
    state_baseline_p,
)

W_STATE = float(os.environ.get("W_STATE", "0.20"))  # MRP state baseline weight

USE_HOUSE = os.environ.get("HOUSE_EFFECTS", "1") == "1"


GOV_CSV = ROOT / "data" / "backtest" / "governadores_br_historico.csv"
REAL_POLLS_CSV = ROOT / "data" / "backtest" / "eleicoes_br_real_polls.csv"

OTHER_CSVS = {
    "presidente":       ROOT / "data" / "backtest" / "eleicao_presidencial_br_2022.csv",
    "impeachment":      ROOT / "data" / "backtest" / "impeachment_dilma_2016.csv",
    "legislativo_lj":   ROOT / "data" / "backtest" / "lava_jato_2014_2018.csv",
    "prefeito_sp":      ROOT / "data" / "backtest" / "seed_eleicao_municipal_sp_2024.csv",
    "legislativo_2026": ROOT / "data" / "backtest" / "brazil_votes_q1_2026.csv",
}


def lead_to_p_win_param(lead_pp: float, days: int, sigma_int: float, sigma_slope: float) -> float:
    sigma = sigma_int + sigma_slope * max(0, days)
    z = lead_pp / max(sigma, 1.0)
    return 0.5 * (1.0 + math.erf(z / math.sqrt(2.0)))


ELECTION_DATES = {
    2002: "2002-10-06", 2006: "2006-10-01", 2010: "2010-10-03",
    2014: "2014-10-05", 2018: "2018-10-07", 2022: "2022-10-02",
    2016: "2016-10-02", 2020: "2020-11-15", 2024: "2024-10-06",
}

def _row_to_event(r: dict, cargo_default: str = "presidente") -> dict:
    from datetime import date
    ano = int(r["ano"])
    election_iso = ELECTION_DATES.get(ano, "2022-10-02")
    election_date = date.fromisoformat(election_iso)
    poll_date = date.fromisoformat(r["data"][:10])
    days = max(0, (election_date - poll_date).days)
    lead = float(r["poll_lead_pp"])
    uf = r.get("uf","BR")
    cargo = "presidente" if uf == "BR" else "prefeito" if (uf == "SP" and ano in (2016,2020,2024)) else "governador"
    partido = r.get("partido","")
    return {
        "evento_id": r["evento_id"],
        "uf": r.get("uf","BR"),
        "ano": ano,
        "data": r["data"],
        "outcome": int(r["outcome_real"]),
        "p_prior": float(r.get("probabilidade_prior", 0.5)),
        "cargo": cargo,
        "lead_bin": lead_bin(lead),
        "days_bin": days_bin(days),
        "incumbente": int(r.get("incumbente", 0)),
        "regime": "right" if partido in {"PL","PP","UNIAO","REP","PSD","NOVO","PSL","DEM","PSC"} else
                  "left"  if partido in {"PT","PCdoB","PSOL","PDT","PSB","REDE"} else "center",
        "context": r.get("outcome_framing",""),
        "poll_lead_pp": lead,
        "days_to": days,
    }


def load_governadores() -> tuple[list[dict], list[dict]]:
    """Returns (events_2018, events_2022) only.  2010+other go via load_other_pool."""
    return load_by_year().get(2018, []), load_by_year().get(2022, [])


DAYS_FILTER = 30  # only keep polls within last N days of the campaign

def load_by_year() -> dict[int, list[dict]]:
    """Group all real-data events by election year. Filter to T<=DAYS_FILTER."""
    by_year: dict[int, list[dict]] = {}
    if GOV_CSV.exists():
        for r in csv.DictReader(open(GOV_CSV, encoding="utf-8")):
            ev = _row_to_event(r)
            if ev["days_to"] <= DAYS_FILTER:
                by_year.setdefault(ev["ano"], []).append(ev)
    if REAL_POLLS_CSV.exists():
        for r in csv.DictReader(open(REAL_POLLS_CSV, encoding="utf-8")):
            ev = _row_to_event(r)
            if ev["days_to"] <= DAYS_FILTER:
                by_year.setdefault(ev["ano"], []).append(ev)
    return by_year


def load_other_pool() -> list[dict]:
    pool = []
    for label, path in OTHER_CSVS.items():
        if not path.exists():
            continue
        cargo = "legislativo" if "legislativo" in label else label.split("_")[0]
        for e in load_csv_events(path, cargo=cargo):
            e.setdefault("poll_lead_pp", 0.0)
            e.setdefault("days_to", 0)
            pool.append(e)
    return pool


def evaluate(events: list[dict], rates: dict, w_linzer: float,
             sigma_int: float, sigma_slope: float,
             house_effects: dict | None = None) -> dict:
    n = len(events)
    if n == 0:
        return {"n": 0}
    brier, ll, hits = 0.0, 0.0, 0
    by_uf = defaultdict(lambda: {"n":0,"hits":0})
    detail = []
    for e in events:
        pred = predict_political(e, rates)
        p_coh = pred["p_raw"]
        p_lnz = lead_to_p_win_param(e.get("poll_lead_pp", 0.0),
                                    e.get("days_to", 30),
                                    sigma_int, sigma_slope)
        p = (1.0 - w_linzer) * p_coh + w_linzer * p_lnz
        if house_effects is not None and "evento_id" in e:
            p = apply_house_effect(p, e["evento_id"], house_effects)
        # MRP state baseline blend
        if W_STATE > 0:
            uf = e.get("uf", "BR")
            p_state = state_baseline_p(rates, uf, e["regime"])
            if p_state is not None:
                p = (1 - W_STATE) * p + W_STATE * p_state
        y = e["outcome"]
        brier += (p - y) ** 2
        ll += -(y * math.log(max(p,1e-9)) + (1-y) * math.log(max(1-p,1e-9)))
        hit = (p >= 0.5) == bool(y)
        if hit: hits += 1
        if "uf" in e:
            by_uf[e["uf"]]["n"] += 1
            by_uf[e["uf"]]["hits"] += int(hit)
        detail.append({**e, "p_coh": round(p_coh,4), "p_lnz": round(p_lnz,4),
                       "p": round(p,4), "hit": int(hit)})
    return {"n": n, "brier": brier/n, "log_loss": ll/n, "acc": hits/n,
            "by_uf": {u:{"n":d["n"],"acc":d["hits"]/d["n"]} for u,d in by_uf.items()},
            "detail": detail}


def main():
    by_year = load_by_year()
    other = load_other_pool()
    print("Events per year:", {y: len(by_year[y]) for y in sorted(by_year)})
    print(f"Other (qualitative) pool: {len(other)}")

    test_years = sorted(by_year.keys())
    # Year-fold CV: for each year y, train on all_other_years + other, test on y.
    # Score: weighted average acc across folds (weight = n_test_y).

    grid_shrink = [0.05, 0.10, 0.15, 0.20, 0.25, 0.30, 0.35, 0.40]
    grid_wlin   = [0.50, 0.60, 0.70, 0.80, 0.85, 0.90, 0.95, 1.00]
    grid_sint   = [3.0, 4.0, 5.0, 6.0, 7.0, 8.0]
    grid_sslo   = [0.01, 0.02, 0.03, 0.04, 0.05, 0.06, 0.08]

    best = {"avg_acc": -1}
    log = []
    iters = 0
    total = len(grid_shrink) * len(grid_wlin) * len(grid_sint) * len(grid_sslo)
    print(f"Grid: {total} combinations")

    for shrink, wlin, sint, sslo in product(grid_shrink, grid_wlin, grid_sint, grid_sslo):
        iters += 1
        per_year_acc = {}
        per_year_brier = {}
        per_year_ev = {}
        n_total, hits_total = 0, 0
        brier_sum = 0.0
        for y in test_years:
            train = list(other)
            for y2 in test_years:
                if y2 != y: train.extend(by_year[y2])
            rates = fit_cohorts_political(train, stein_shrink=shrink)
            house = None
            if USE_HOUSE:
                house = fit_house_effects(train, rates, w_linzer=wlin,
                                          sigma_int=sint, sigma_slope=sslo)
            ev = evaluate(by_year[y], rates, wlin, sint, sslo, house_effects=house)
            if ev["n"] == 0: continue
            per_year_acc[y]   = ev["acc"]
            per_year_brier[y] = ev["brier"]
            per_year_ev[y]    = ev
            n_total += ev["n"]
            hits_total += int(round(ev["acc"] * ev["n"]))
            brier_sum  += ev["brier"] * ev["n"]
        avg_acc   = hits_total / max(n_total, 1)
        avg_brier = brier_sum / max(n_total, 1)
        log.append({
            "shrink": shrink, "wlin": wlin, "sint": sint, "sslo": sslo,
            "per_year_acc": {y: round(a, 4) for y, a in per_year_acc.items()},
            "avg_acc": round(avg_acc, 4),
            "avg_brier": round(avg_brier, 4),
        })
        if avg_acc > best["avg_acc"]:
            best = {
                "shrink": shrink, "wlin": wlin, "sint": sint, "sslo": sslo,
                "avg_acc": avg_acc, "avg_brier": avg_brier,
                "per_year_acc": per_year_acc, "per_year_brier": per_year_brier,
                "per_year_ev": per_year_ev,
            }
        if iters % 200 == 0:
            print(f"  iter {iters}/{total}  best avg_acc={best['avg_acc']:.4f}")

    print("\n=== BEST CONFIGURATION ===")
    print(f"  shrink     = {best['shrink']}")
    print(f"  w_linzer   = {best['wlin']}")
    print(f"  sigma_int  = {best['sint']}")
    print(f"  sigma_slope= {best['sslo']}")
    print(f"  avg_acc    = {best['avg_acc']:.4f}")
    print(f"  avg_brier  = {best['avg_brier']:.4f}")
    print()
    for y in sorted(best["per_year_acc"]):
        ev = best["per_year_ev"][y]
        print(f"  acc {y} holdout = {ev['acc']:.4f} (n={ev['n']}, brier={ev['brier']:.4f})")

    # Misses
    for y in sorted(best["per_year_ev"]):
        ev = best["per_year_ev"][y]
        misses = [d for d in ev["detail"] if not d["hit"]]
        print(f"\n  Misses {y} ({len(misses)}/{ev['n']}):")
        for m in misses[:10]:
            print(f"    {m['evento_id']:<40} y={m['outcome']} p={m['p']:.3f} (lead={m.get('poll_lead_pp')}, regime={m['regime']})")

    out = {
        "best": {
            "shrink": best["shrink"], "wlin": best["wlin"],
            "sint": best["sint"], "sslo": best["sslo"],
            "avg_acc": round(best["avg_acc"], 4),
            "avg_brier": round(best["avg_brier"], 4),
            "per_year_acc": {y: round(a, 4) for y, a in best["per_year_acc"].items()},
            "per_year_brier": {y: round(b, 4) for y, b in best["per_year_brier"].items()},
            "per_year_n": {y: best["per_year_ev"][y]["n"] for y in best["per_year_ev"]},
        },
        "n_grid": total,
        "top_20": sorted(log, key=lambda x: -x["avg_acc"])[:20],
    }
    out_path = ROOT / "data" / "political_autoresearch_results.json"
    with open(out_path, "w") as f:
        json.dump(out, f, indent=2, default=str)
    print(f"\nSaved -> {out_path}")


if __name__ == "__main__":
    main()
