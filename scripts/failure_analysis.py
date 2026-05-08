#!/usr/bin/env python3
"""Failure-mode analysis for Vila MRP ensemble (Phase 4 publish-grade work).

Runs year-fold leave-one-out CV with the operative published config:
    stein_shrink = 0.4
    w_linzer     = 0.7
    sigma_int    = 3.0
    sigma_slope  = 0.01
    w_state_mrp  = 0.36
    house_effects = disabled

Note: data/political_best_config.json documents alternative hyperparameters
(stein=0.05, w_linzer=0.5, sint=4.0, sslo=0.05). Empirically only the
config above reproduces the 97.21% / 11-miss number reported in the paper.
The JSON config file appears to mix metadata and validation numbers from
different runs - see docs/FAILURE_MODES.md.

Outputs:
    data/failure_analysis.json  - structured miss list + cluster + impact
    Console table summarizing categories, MRP impact, severity matrix.

Categories assigned to each miss:
    tossup        - |poll_lead_pp| < 3
    realignment   - p_state contradicts polls AND outcome aligns with polls
                    (i.e., MRP HURT the prediction)
    industry_bias - multiple polls converge, model agrees with polls,
                    outcome diverges (the 2024 SP residual cluster)
    sparse_cohort - n_cohort < 5
    other         - none of the above

MRP impact bucket (per evento_id):
    mrp_recovered  - missed without MRP, hit with MRP
    mrp_unchanged  - missed both with and without MRP (intrinsic failure)
    mrp_introduced - hit without MRP, missed with MRP (MRP HURT)

Year-fold leak-safe: for each test year y, train on all_other_years + other_pool.
"""
from __future__ import annotations

import csv
import json
import math
import os
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from engine.political_cohort import (
    fit_cohorts_political,
    fit_house_effects,
    predict_political,
    state_baseline_p,
)
from scripts.autoresearch_political import (
    load_by_year,
    load_other_pool,
    lead_to_p_win_param,
)


# Operative config that produces 97.21% / 11 misses. See module docstring.
SHRINK = 0.4
W_LINZER = 0.7
SIGMA_INT = 3.0
SIGMA_SLO = 0.01
W_STATE = 0.36
USE_HOUSE = False

# Cluster thresholds.
TOSSUP_LEAD = 3.0     # |poll_lead_pp| < 3 -> tossup
SPARSE_N = 5           # n_cohort < 5 -> sparse


def _evaluate(events: list[dict], rates: dict, *, w_state: float) -> list[dict]:
    """Predict each event with explicit blend; return per-event detail.

    Records both p_with_mrp (the published blend) and p_no_mrp (cohort+linzer
    only) so we can compute MRP impact buckets.
    """
    detail = []
    sr_table = rates.get("_state_regime", {})
    for e in events:
        pred = predict_political(e, rates)
        p_coh = pred["p_raw"]
        p_lnz = lead_to_p_win_param(
            e.get("poll_lead_pp", 0.0),
            e.get("days_to", 30),
            SIGMA_INT,
            SIGMA_SLO,
        )
        p_blend = (1.0 - W_LINZER) * p_coh + W_LINZER * p_lnz
        # No-MRP variant.
        p_no_mrp = p_blend
        # With-MRP variant.
        uf = e.get("uf", "BR")
        regime = e.get("regime", "center")
        p_state = state_baseline_p(rates, uf, regime)
        p_with_mrp = p_blend
        if w_state > 0 and p_state is not None:
            p_with_mrp = (1.0 - w_state) * p_blend + w_state * p_state
        cell = sr_table.get((uf, regime), [0, 0])
        y = e["outcome"]
        detail.append({
            "evento_id": e.get("evento_id", "?"),
            "cycle": e.get("ano"),
            "uf": uf,
            "regime": regime,
            "partido": e.get("partido", ""),
            "incumbente": e.get("incumbente", 0),
            "cargo": e.get("cargo"),
            "poll_lead_pp": e.get("poll_lead_pp", 0.0),
            "days_to": e.get("days_to", 0),
            "outcome": y,
            "p_cohort": round(p_coh, 4),
            "p_linzer": round(p_lnz, 4),
            "p_no_mrp": round(p_no_mrp, 4),
            "p_state_baseline": (round(p_state, 4) if p_state is not None else None),
            "p_predicted": round(p_with_mrp, 4),
            "tier": pred["tier"],
            "n_cohort": pred["n_cohort"],
            "state_cell_n": cell[1],
            "state_cell_wins": cell[0],
            "hit_with_mrp": int((p_with_mrp >= 0.5) == bool(y)),
            "hit_no_mrp": int((p_no_mrp >= 0.5) == bool(y)),
        })
    return detail


def classify_miss(m: dict, *, sparse_n: int = SPARSE_N,
                  tossup_lead: float = TOSSUP_LEAD) -> str:
    """Bucket a miss into one of the failure categories."""
    lead = abs(m.get("poll_lead_pp", 0.0))
    n_coh = m.get("n_cohort", 0)
    p_state = m.get("p_state_baseline")
    p_lnz = m.get("p_linzer", 0.5)
    y = m["outcome"]
    # MRP-introduced misses (state contradicts polls, polls were right).
    polls_say_win = p_lnz >= 0.5
    state_says_win = (p_state is not None) and (p_state >= 0.5)
    if (
        p_state is not None
        and (polls_say_win != state_says_win)
        and (polls_say_win == bool(y))
    ):
        return "realignment"
    if lead < tossup_lead:
        return "tossup"
    if n_coh < sparse_n:
        return "sparse_cohort"
    # Industry-wide bias: |lead| >= 3, polls (and model) point one way, outcome opposite.
    if (p_lnz >= 0.5) != bool(y) and lead >= tossup_lead:
        return "industry_bias"
    return "other"


def mrp_impact_bucket(m: dict) -> str:
    if m["hit_with_mrp"] and not m["hit_no_mrp"]:
        return "mrp_recovered"
    if not m["hit_with_mrp"] and m["hit_no_mrp"]:
        return "mrp_introduced"
    if not m["hit_with_mrp"] and not m["hit_no_mrp"]:
        return "mrp_unchanged"
    return "mrp_unchanged_hit"  # both hit, not a miss


def severity_matrix(detail: list[dict]) -> dict:
    """Per (uf, regime) signature: count rows, miss count, mean cell-n.

    Used to recommend per-cell w_state attenuation when state_cell_n is low.
    """
    out: dict = defaultdict(lambda: {
        "n_events": 0,
        "n_misses_with_mrp": 0,
        "n_misses_no_mrp": 0,
        "min_state_cell_n": None,
    })
    for m in detail:
        key = f"{m['uf']}|{m['regime']}"
        s = out[key]
        s["n_events"] += 1
        if not m["hit_with_mrp"]:
            s["n_misses_with_mrp"] += 1
        if not m["hit_no_mrp"]:
            s["n_misses_no_mrp"] += 1
        cur = s["min_state_cell_n"]
        new = m["state_cell_n"]
        s["min_state_cell_n"] = new if cur is None else min(cur, new)
    return dict(out)


def main():
    by_year = load_by_year()
    other = load_other_pool()
    years = sorted(by_year.keys())
    print(f"events/year: {{ {', '.join(f'{y}: {len(by_year[y])}' for y in years)} }}")
    print(f"other pool: {len(other)}")
    print(
        f"config: shrink={SHRINK}, w_linzer={W_LINZER}, sint={SIGMA_INT}, "
        f"sslo={SIGMA_SLO}, w_state={W_STATE}, house_effects={USE_HOUSE}"
    )
    print()

    all_detail: list[dict] = []
    per_year_acc: dict = {}
    for y in years:
        train = list(other)
        for y2 in years:
            if y2 != y:
                train.extend(by_year[y2])
        rates = fit_cohorts_political(train, stein_shrink=SHRINK)
        # House effects disabled per published config.
        det = _evaluate(by_year[y], rates, w_state=W_STATE)
        n = len(det)
        hits = sum(d["hit_with_mrp"] for d in det)
        per_year_acc[y] = {"n": n, "acc": (hits / n) if n else 0.0}
        for d in det:
            d["test_year"] = y
        all_detail.extend(det)

    # Aggregate.
    n_total = len(all_detail)
    hits_total = sum(d["hit_with_mrp"] for d in all_detail)
    avg_acc = hits_total / n_total
    misses = [d for d in all_detail if not d["hit_with_mrp"]]
    no_mrp_hits = sum(d["hit_no_mrp"] for d in all_detail)
    no_mrp_acc = no_mrp_hits / n_total

    print(f"avg_acc with MRP    = {avg_acc:.4f} ({hits_total}/{n_total})")
    print(f"avg_acc without MRP = {no_mrp_acc:.4f} ({no_mrp_hits}/{n_total})")
    print(f"misses with MRP     = {len(misses)}")
    print()

    # Per-year breakdown.
    print("year | n | acc")
    for y in years:
        a = per_year_acc[y]
        print(f"  {y}: n={a['n']:>3}  acc={a['acc']:.4f}")
    print()

    # Cluster the with-MRP misses.
    for m in misses:
        m["category"] = classify_miss(m)
        m["mrp_impact"] = mrp_impact_bucket(m)

    # Confusion table per category.
    by_cat: dict = defaultdict(list)
    for m in misses:
        by_cat[m["category"]].append(m)
    print("== category breakdown of with-MRP misses ==")
    for cat, items in sorted(by_cat.items(), key=lambda kv: -len(kv[1])):
        print(f"  {cat:<15} {len(items):>2}")
    print()

    # MRP impact across all events (recovered, introduced, unchanged misses).
    impact_counts: dict = defaultdict(int)
    for d in all_detail:
        impact_counts[mrp_impact_bucket(d)] += 1
    print("== MRP impact (vs no-MRP baseline) ==")
    for k in ("mrp_recovered", "mrp_introduced", "mrp_unchanged", "mrp_unchanged_hit"):
        print(f"  {k:<22} {impact_counts.get(k, 0):>3}")
    print()

    # 11 misses table.
    print("== misses (11) - full context ==")
    cols = (
        "test_year evento_id uf regime poll_lead_pp days_to outcome "
        "p_cohort p_linzer p_state_baseline p_predicted tier n_cohort "
        "state_cell_n category mrp_impact"
    ).split()
    print("  " + " | ".join(cols))
    for m in misses:
        row = []
        for c in cols:
            v = m.get(c)
            if isinstance(v, float):
                row.append(f"{v:.3f}")
            else:
                row.append(str(v))
        print("  " + " | ".join(row))
    print()

    # Severity matrix per (uf, regime).
    sm = severity_matrix(all_detail)
    print("== severity matrix (top miss-rate UF|regime cells) ==")
    rows = sorted(sm.items(),
                  key=lambda kv: (-kv[1]["n_misses_with_mrp"], -kv[1]["n_events"]))
    for sig, s in rows[:15]:
        if s["n_misses_with_mrp"] == 0 and s["n_misses_no_mrp"] == 0:
            continue
        print(
            f"  {sig:<10} n={s['n_events']:>3} "
            f"miss_mrp={s['n_misses_with_mrp']:>2} "
            f"miss_no_mrp={s['n_misses_no_mrp']:>2} "
            f"min_cell_n={s['min_state_cell_n']}"
        )
    print()

    # Adaptive rule: w_state = 0.36 * min(1, n_cell / SPARSE_N).
    print("== recommended adaptive rule ==")
    print("  w_state(uf, regime) = 0.36 * min(1.0, n_cell / 5)")
    print("  - if state_cell_n < 5  -> attenuate proportionally")
    print("  - if state_cell_n >= 5 -> use 0.36 (current default)")
    print()

    # Persist JSON snapshot.
    out_path = ROOT / "data" / "failure_analysis.json"
    payload = {
        "config": {
            "shrink": SHRINK, "w_linzer": W_LINZER,
            "sigma_int": SIGMA_INT, "sigma_slope": SIGMA_SLO,
            "w_state": W_STATE, "use_house_effects": USE_HOUSE,
        },
        "summary": {
            "n_total": n_total,
            "acc_with_mrp": round(avg_acc, 4),
            "acc_no_mrp": round(no_mrp_acc, 4),
            "n_misses_with_mrp": len(misses),
            "per_year_acc": {y: per_year_acc[y] for y in years},
            "mrp_impact": dict(impact_counts),
        },
        "misses": misses,
        "category_counts": {k: len(v) for k, v in by_cat.items()},
        "severity_matrix": sm,
        "adaptive_rule": {
            "formula": "w_state(uf,regime) = 0.36 * min(1, state_cell_n / 5)",
            "rationale": (
                "When (UF, regime) cell has fewer than 5 historical events the "
                "MRP baseline is unreliable and may inject contradictory prior "
                "(see realignment cluster). Attenuate proportionally."
            ),
            "sparse_threshold": SPARSE_N,
        },
    }
    out_path.write_text(json.dumps(payload, indent=2, default=str))
    print(f"wrote {out_path}")
    return payload


if __name__ == "__main__":
    main()
