#!/usr/bin/env python3
"""Generate 2026 predictions for BR presidente / governador / senador using the
political cohort forecaster fitted on all available BR political backtest data.

Outputs human-readable summary and a JSON snapshot consumed by the API +
frontend.
"""
from __future__ import annotations

import json
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from engine.political_cohort import (
    BR_2026_REGISTRY, fit_cohorts_political, predict_political,
    load_csv_events, lead_bin, days_bin, lead_to_p_win,
    filter_eligible_candidates, state_baseline_p,
    fit_isotonic_calibrator, apply_isotonic,
)

# Ensemble weights: cohort base-rate vs Linzer poll-lead win-prob.
# Loaded from data/political_best_config.json (autoresearch result, T<=30 fold CV).
import json as _json
try:
    _cfg = _json.load(open(ROOT / "data" / "political_best_config.json"))
    W_LINZER = _cfg["w_linzer"]
    W_COHORT = 1.0 - W_LINZER
    SIGMA_INT = _cfg["sigma_intercept_pp"]
    SIGMA_SLO = _cfg["sigma_slope_pp_per_day"]
    W_STATE = _cfg.get("w_state_mrp", 0.0)
except Exception:
    W_COHORT, W_LINZER = 0.50, 0.50
    SIGMA_INT, SIGMA_SLO = 5.0, 0.01
    W_STATE = 0.0

ELECTION_DATE = date(2026, 10, 4)  # 1º turno


# Hand-curated poll-lead snapshot (pp). Source: aggregator (Poder360 latest waves
# 2026-Q1, Atlas Intel Apr 2026, Quaest Apr 2026). Single number per candidate;
# negative = behind frontrunner; positive = lead.
PRESIDENTIAL_LEADS_PP = {
    "lula_2026":      0.0,
    "tarcisio_2026": -8.0,
    "ratinho_2026": -22.0,
    "zema_2026":    -25.0,
    "boulos_2026":  -33.0,
    # bolsonaro_2026 inelegivel -> filtrado
}

GOVERNOR_LEADS_PP = {
    "sp_2026_tarcisio": +14,
    "sp_2026_haddad":   -14,
    "rj_2026_castro":   +6,
    "mg_2026_zema":     +18,
    "rs_2026_leite":    +9,
    "pr_2026_ratinho":  +30,
    "ba_2026_jeronimo": +12,
    "ce_2026_elmano":   +8,
    "pe_2026_raquel":   +4,
    "go_2026_caiado":   +20,
}

# Senado 2026: SEM polls reais ainda. Leads zerados = predicao base sobre
# incumbencia + cohort, com forte aviso de "preliminar / candidatura nao
# confirmada".
SENATOR_LEADS_PP = {
    "sp_sen_2018_alessandro": 0,
    "rj_sen_2018_arolde":     0,
    "mg_sen_2018_anastasia":  0,
    "rs_sen_2018_paim":       0,
}


def predict_for_candidates(rates, cargo: str, candidates: list[dict],
                           leads_map: dict, today: date,
                           isotonic: dict | None = None) -> list[dict]:
    days = max(0, (ELECTION_DATE - today).days)
    out = []
    for c in candidates:
        lead = leads_map.get(c["id"], 0.0)
        ev = {
            "cargo": cargo,
            "lead_bin": lead_bin(lead),
            "days_bin": days_bin(days),
            "incumbente": c["incumbente"],
            "regime": c["regime"],
            "outcome": None,
        }
        pred = predict_political(ev, rates)
        p_cohort = pred["p_raw"]
        # Linzer Phi(lead/sigma(days)) using best-fit sigma from autoresearch.
        import math as _math
        sigma = SIGMA_INT + SIGMA_SLO * max(0, days)
        z = lead / max(sigma, 1.0)
        p_linzer = 0.5 * (1.0 + _math.erf(z / _math.sqrt(2.0)))
        p_blend = W_COHORT * p_cohort + W_LINZER * p_linzer
        # MRP state baseline blend
        if W_STATE > 0:
            uf = c.get("uf", "BR")
            p_state = state_baseline_p(rates, uf, c["regime"])
            if p_state is not None:
                p_blend = (1 - W_STATE) * p_blend + W_STATE * p_state
        # Onda 6: isotonic recalibration
        if isotonic is not None:
            p_blend = apply_isotonic(p_blend, isotonic)
        out.append({
            "registry_id": c["id"],
            "nome": c["nome"],
            "partido": c["partido"],
            "uf": c.get("uf"),
            "incumbente": c["incumbente"],
            "regime": c["regime"],
            "status": c.get("status", "speculation"),
            "status_note": c.get("status_note", ""),
            "poll_lead_pp": lead,
            "p_cohort": round(p_cohort, 4),
            "p_linzer": round(p_linzer, 4),
            "p_raw": round(p_blend, 4),
            "tier": pred["tier"],
            "n_cohort": pred["n_cohort"],
            "horizon_days": days,
        })
    out.sort(key=lambda x: -x["p_raw"])
    return out


def normalize_election(preds: list[dict]) -> list[dict]:
    """Normalize so probabilities of mutually-exclusive winners sum to 1."""
    s = sum(max(0.001, p["p_raw"]) for p in preds)
    for p in preds:
        p["p_winner"] = round(max(0.001, p["p_raw"]) / s, 4)
    return preds


CSV_MAP = {
    "presidente":       "data/backtest/eleicao_presidencial_br_2022.csv",
    "impeachment":      "data/backtest/impeachment_dilma_2016.csv",
    "legislativo":      "data/backtest/lava_jato_2014_2018.csv",
    "prefeito":         "data/backtest/seed_eleicao_municipal_sp_2024.csv",
    "legislativo_2026": "data/backtest/brazil_votes_q1_2026.csv",
}


def main():
    today = date.today()
    print(f"Predicting BR 2026 elections (today={today}, election={ELECTION_DATE})")

    # Train on everything available
    train: list[dict] = []
    for label, rel in CSV_MAP.items():
        path = ROOT / rel
        if path.exists():
            cargo = "legislativo" if "legislativo" in label else label
            train.extend(load_csv_events(path, cargo=cargo))
    rates = fit_cohorts_political(train, stein_shrink=0.15)
    print(f"  Trained on {len(train)} historical political events")

    # Onda 6: isotonic recalibration deferred to production-grade fit.
    # Training pool here uses CSV_MAP (50 events) which is too small/biased
    # for a clean isotonic. Demonstrated brier 0.105 -> 0.033 on full year-fold
    # CV (394 events). To enable, switch this script to load_by_year() pool.
    # Skipping for current snapshot to avoid extreme calibration.
    isotonic = None

    # Generate predictions; filter out ineligible (e.g. Bolsonaro per TSE)
    pres_pool = filter_eligible_candidates(BR_2026_REGISTRY["presidente"])
    pres = predict_for_candidates(rates, "presidente",
                                  pres_pool, PRESIDENTIAL_LEADS_PP, today, isotonic=isotonic)
    pres = normalize_election(pres)

    govs_pool = filter_eligible_candidates(BR_2026_REGISTRY["governador"])
    govs = predict_for_candidates(rates, "governador",
                                  govs_pool, GOVERNOR_LEADS_PP, today, isotonic=isotonic)
    # Governor races: per-UF normalization
    by_uf: dict[str, list] = {}
    for g in govs:
        by_uf.setdefault(g["uf"], []).append(g)
    for uf, lst in by_uf.items():
        normalize_election(lst)

    sens_pool = filter_eligible_candidates(BR_2026_REGISTRY["senador"])
    sens = predict_for_candidates(rates, "senador",
                                  sens_pool, SENATOR_LEADS_PP, today, isotonic=isotonic)

    # ---- Print human summary ------------------------------------------------
    def fmt_table(rows, fields):
        widths = {f: max(len(str(r.get(f, ""))) for r in rows + [{f: f}]) for f in fields}
        line = " ".join(f"{{:<{widths[f]}}}" for f in fields)
        out = [line.format(*fields)]
        for r in rows:
            out.append(line.format(*[r.get(f, "") for f in fields]))
        return "\n".join(out)

    print("\n=== PRESIDENCIAL 2026 (1º turno) ===")
    print(fmt_table(
        [{"#": i+1, "candidato": p["nome"], "partido": p["partido"],
          "lead_pp": p["poll_lead_pp"],
          "p_coh": p["p_cohort"], "p_lnz": p["p_linzer"],
          "p_raw": p["p_raw"], "p_winner": p["p_winner"]}
         for i, p in enumerate(pres)],
        ["#", "candidato", "partido", "lead_pp", "p_coh", "p_lnz", "p_raw", "p_winner"]))

    print("\n=== GOVERNADOR 2026 (top UFs) ===")
    for uf in sorted(by_uf):
        print(f"\n  --- {uf} ---")
        rows = sorted(by_uf[uf], key=lambda r: -r["p_winner"])
        print(fmt_table(
            [{"candidato": r["nome"], "partido": r["partido"],
              "incum": r["incumbente"], "lead_pp": r["poll_lead_pp"],
              "p_raw": r["p_raw"], "p_winner": r["p_winner"]}
             for r in rows],
            ["candidato", "partido", "incum", "lead_pp", "p_raw", "p_winner"]))

    print("\n=== SENADOR 2026 (sample) ===")
    print(fmt_table(
        [{"candidato": s["nome"], "uf": s["uf"], "partido": s["partido"],
          "incum": s["incumbente"], "lead_pp": s["poll_lead_pp"],
          "p_raw": s["p_raw"]} for s in sens],
        ["candidato", "uf", "partido", "incum", "lead_pp", "p_raw"]))

    # ---- Save snapshot ------------------------------------------------------
    snap = {
        "predicted_at": str(today),
        "election_date": str(ELECTION_DATE),
        "horizon_days": (ELECTION_DATE - today).days,
        "n_train_events": len(train),
        "model": "political_cohort_v1.1",
        "disclaimer": (
            "Snapshot 2026-05 — todas as candidaturas marcadas 'speculation' "
            "ainda nao foram registradas formalmente. Bolsonaro filtrado "
            "(inelegivel TSE ate 2030). Senado lista titulares cuja cadeira "
            "vence em 2026 (eleitos 2018), nao candidatos confirmados. "
            "Probabilidades sao priors baseados em regime+incumbencia+pesquisas "
            "agregadas, nao previsoes determinadas. Recalibragem mensal."
        ),
        "presidente": pres,
        "governador_by_uf": by_uf,
        "senador": sens,
    }
    out_path = ROOT / "data" / "predictions_2026.json"
    with open(out_path, "w") as f:
        json.dump(snap, f, indent=2, default=str)
    print(f"\nSaved -> {out_path}")


if __name__ == "__main__":
    main()
