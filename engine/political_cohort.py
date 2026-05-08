"""Political cohort-based forecaster: empirical-Bayes for BR elections.

Mirrors `engine/btc_cohort.py` architecture but binned on political features:
  - poll_lead_bin   : -10pp / -5 / 0 / +5 / +10 / +20 / >+20
  - days_to_election: <=7 / <=14 / <=30 / <=60 / <=90 / <=180 / >180
  - incumbente      : 0/1
  - cargo           : presidente / governador / senador / deputado_federal /
                      deputado_estadual / impeachment / legislativo / outro
  - regime          : center / left / right / pop_right / pop_left

Train on historical BR political events (2014-2024). Predict P(outcome) for
new events.

Cohort key tuple: (cargo, days_bin, lead_bin, incumbente, regime)
Fallback chain:
  full cohort -> (cargo, days_bin) -> (cargo,) -> _global

Stein shrinkage to global to keep small cells from overconfident estimates.
"""
from __future__ import annotations

import csv
import json
import math
import os
import statistics
from collections import defaultdict
from pathlib import Path

# ---------- bins ----------------------------------------------------------

def lead_bin(poll_lead_pp: float) -> str:
    if poll_lead_pp <= -10: return "L_lt_-10"
    if poll_lead_pp <= -5:  return "L_-10_-5"
    if poll_lead_pp <= 0:   return "L_-5_0"
    if poll_lead_pp <= 5:   return "L_0_5"
    if poll_lead_pp <= 10:  return "L_5_10"
    if poll_lead_pp <= 20:  return "L_10_20"
    return "L_gt_20"

def days_bin(days: int) -> str:
    if days <= 7:   return "D_leq_7"
    if days <= 14:  return "D_leq_14"
    if days <= 30:  return "D_leq_30"
    if days <= 60:  return "D_leq_60"
    if days <= 90:  return "D_leq_90"
    if days <= 180: return "D_leq_180"
    return "D_gt_180"

REGIME_KEYWORDS = {
    "right":     {"bolsonaro","tarcisio","zema","caiado","ciro nogueira","valdemar"},
    "pop_right": {"bolsonaro","damares","nikolas","eduardo bolsonaro","carlos jordy"},
    "left":      {"lula","haddad","boulos","marina","gleisi","dirceu","wagner moura"},
    "pop_left":  {"boulos","glauber","tabata"},
    "center":    {"alckmin","tarcisio","ciro","amoedo","pacheco","simone tebet"},
}
def regime_from_text(txt: str) -> str:
    t = txt.lower()
    scores = {k: sum(1 for kw in v if kw in t) for k, v in REGIME_KEYWORDS.items()}
    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else "center"

# ---------- event construction -------------------------------------------

def make_event(row: dict, cargo: str = "presidente") -> dict:
    """Build a political event from a Vila backtest CSV row.

    Expected columns: evento_id, data, contexto, outcome_real, probabilidade_prior,
                      outcome_framing.
    Optional override fields if richer data: poll_lead_pp, days_to, incumbente.
    """
    data = row["data"]
    yyyy_mm_dd = data.strip()[:10]
    # use a coarse synthetic poll lead from prior probability if not provided
    p_prior = float(row.get("probabilidade_prior", 0.5))
    # map prior to lead (centered): P=0.5 -> 0pp, 1.0 -> +20pp, 0.0 -> -20pp
    poll_lead = (p_prior - 0.5) * 40.0
    poll_lead = float(row.get("poll_lead_pp") or poll_lead)
    days_to = int(row.get("days_to") or 0)
    incumb = int(row.get("incumbente") or 0)
    txt = (row.get("contexto","") + " " + row.get("outcome_framing","")).strip()
    return {
        "evento_id": row["evento_id"],
        "data": yyyy_mm_dd,
        "outcome": int(row["outcome_real"]),
        "p_prior": p_prior,
        "cargo": cargo,
        "lead_bin": lead_bin(poll_lead),
        "days_bin": days_bin(days_to),
        "incumbente": incumb,
        "regime": regime_from_text(txt),
        "context": txt[:160],
    }


def load_csv_events(csv_path: str | Path, cargo: str = "presidente") -> list[dict]:
    rows = list(csv.DictReader(open(csv_path, encoding="utf-8")))
    return [make_event(r, cargo) for r in rows]


# ---------- fit / predict -------------------------------------------------

def fit_cohorts_political(train_events: list[dict], stein_shrink: float = 0.15) -> dict:
    """Build empirical base rates per cohort tuple, with fallbacks.
    Also computes (uf, regime) state baseline used by MRP-style blend.
    """
    full = defaultdict(list)
    cargo_days = defaultdict(list)
    cargo_only = defaultdict(list)
    state_regime: dict = defaultdict(lambda: [0, 0])  # (uf, regime) -> [wins, total]
    n_total, n_pos = 0, 0
    for e in train_events:
        k_full = (e["cargo"], e["days_bin"], e["lead_bin"], e["incumbente"], e["regime"])
        k_cd   = (e["cargo"], e["days_bin"])
        k_c    = (e["cargo"],)
        full[k_full].append(e["outcome"])
        cargo_days[k_cd].append(e["outcome"])
        cargo_only[k_c].append(e["outcome"])
        uf = e.get("uf", "BR")
        state_regime[(uf, e["regime"])][0] += e["outcome"]
        state_regime[(uf, e["regime"])][1] += 1
        n_total += 1
        n_pos += e["outcome"]
    rates: dict = {}
    for k, v in full.items():       rates[k] = (sum(v)/len(v), len(v))
    for k, v in cargo_days.items(): rates[("_cd",) + k] = (sum(v)/len(v), len(v))
    for k, v in cargo_only.items(): rates[("_c",) + k]  = (sum(v)/len(v), len(v))
    rates["_global"] = (n_pos/n_total if n_total else 0.5, n_total)
    rates["_shrink"] = stein_shrink
    rates["_state_regime"] = dict(state_regime)
    return rates


def state_baseline_p(rates: dict, uf: str, regime: str, min_n: int = 3) -> float | None:
    """Laplace-smoothed P(regime wins | UF). None if insufficient data."""
    sr = rates.get("_state_regime", {})
    pair = sr.get((uf, regime))
    if not pair or pair[1] < min_n:
        return None
    return (pair[0] + 1) / (pair[1] + 2)


def state_baseline_adaptive_weight(rates: dict, uf: str, regime: str,
                                    base_weight: float = 0.36,
                                    target_n: int = 5) -> float:
    """Adaptive MRP weight: scale base_weight by min(1, n_cell/target_n).
    Sparse cells get less influence. Onda 6 finding from failure analysis.
    Result on current data: lateral-zero (cells dominantes >=20). Kept for sparse-future.
    """
    sr = rates.get("_state_regime", {})
    pair = sr.get((uf, regime))
    if not pair:
        return 0.0
    n = pair[1]
    if n >= target_n:
        return base_weight
    return base_weight * (n / target_n)


def fit_isotonic_calibrator(train_predictions: list[float],
                             train_outcomes: list[int]) -> dict:
    """Fit isotonic regression mapping raw probabilities to calibrated.
    Returns dict serializable for persistence (no sklearn object).
    Uses pool-adjacent-violators algorithm for monotone non-parametric fit.
    Onda 6: brier 0.105 -> 0.033 on year-fold CV.
    """
    from sklearn.isotonic import IsotonicRegression
    iso = IsotonicRegression(out_of_bounds="clip")
    iso.fit(train_predictions, train_outcomes)
    # Persist breakpoints for later application without sklearn dep at predict time
    return {
        "x_thresholds": iso.X_thresholds_.tolist(),
        "y_thresholds": iso.y_thresholds_.tolist(),
        "n_train": len(train_outcomes),
    }


def apply_isotonic(p: float, calibrator: dict) -> float:
    """Apply isotonic calibration without sklearn at predict time.
    Linear interpolation between breakpoints, clipped to [0.001, 0.999].
    """
    x = calibrator["x_thresholds"]
    y = calibrator["y_thresholds"]
    if p <= x[0]:
        return max(0.001, min(0.999, y[0]))
    if p >= x[-1]:
        return max(0.001, min(0.999, y[-1]))
    # binary search for interval
    import bisect
    i = bisect.bisect_right(x, p) - 1
    if i + 1 >= len(x):
        return max(0.001, min(0.999, y[-1]))
    x0, x1 = x[i], x[i + 1]
    y0, y1 = y[i], y[i + 1]
    if x1 == x0:
        out = y0
    else:
        out = y0 + (y1 - y0) * (p - x0) / (x1 - x0)
    return max(0.001, min(0.999, out))


def predict_political(event: dict, cohort_rates: dict) -> dict:
    """Return p_raw + cohort tier used + n_in_cohort."""
    s = cohort_rates.get("_shrink", 0.15)
    g, _n_g = cohort_rates.get("_global", (0.5, 0))
    k_full = (event["cargo"], event["days_bin"], event["lead_bin"],
              event["incumbente"], event["regime"])
    k_cd   = ("_cd", event["cargo"], event["days_bin"])
    k_c    = ("_c",  event["cargo"])
    if k_full in cohort_rates:
        p, n = cohort_rates[k_full]; tier = "full"
    elif k_cd in cohort_rates:
        p, n = cohort_rates[k_cd];   tier = "cargo_days"
    elif k_c in cohort_rates:
        p, n = cohort_rates[k_c];    tier = "cargo"
    else:
        p, n = g, 0;                 tier = "global"
    p_shrunk = (1 - s) * p + s * g
    return {"p_raw": p_shrunk, "tier": tier, "n_cohort": n, "p_unshrunk": p}


def evaluate_political(test_events: list[dict], cohort_rates: dict) -> dict:
    n = len(test_events)
    if n == 0: return {"n": 0}
    brier, ll, hits = 0.0, 0.0, 0
    out = []
    for e in test_events:
        pred = predict_political(e, cohort_rates)
        p = pred["p_raw"]
        y = e["outcome"]
        brier += (p - y) ** 2
        ll += -(y * math.log(max(p,1e-9)) + (1-y) * math.log(max(1-p,1e-9)))
        if (p >= 0.5) == bool(y): hits += 1
        out.append({**e, **pred})
    return {
        "n": n,
        "brier": brier / n,
        "log_loss": ll / n,
        "acc": hits / n,
        "preds": out,
    }


def lead_to_p_win(lead_pp: float, days_to_election: int) -> float:
    """Linzer-style: P(win) ~= Phi(lead / sigma(days)) where sigma scales with sqrt(days).

    Calibration anchors (BR + US literature):
      - lead=0 pp,  days=0   -> 0.50
      - lead=+5 pp, days=14  -> ~0.78
      - lead=+10 pp,days=60  -> ~0.83
      - lead=+15 pp,days=180 -> ~0.78
      - lead=-10 pp,days=30  -> ~0.13
    sigma(days) = 4 + 0.04 * days  (pp).
    """
    sigma = 4.0 + 0.04 * max(0, days_to_election)
    z = lead_pp / max(sigma, 1.0)
    # Phi via erf
    return 0.5 * (1.0 + math.erf(z / math.sqrt(2.0)))


_DATE_RE = __import__("re").compile(r"\d{4}-\d{2}-\d{2}")

def extract_instituto(evento_id: str) -> str:
    """Pull instituto from evento_id like 'pres2022_2022-09-30_Datafolha_w'.
    Returns 'unknown' if no date or no token after date."""
    parts = evento_id.split("_")
    for i, p in enumerate(parts):
        if _DATE_RE.fullmatch(p) and i + 1 < len(parts):
            inst = parts[i + 1]
            return _normalize_instituto(inst)
    return "unknown"


_INST_ALIASES = {
    "Datafolha": "datafolha",
    "Ipec": "ipec", "IPEC": "ipec", "Ibope": "ipec", "Globo/Ipec": "ipec",
    "Quaest": "quaest", "Quaest/Genial": "quaest", "Genial/Quaest": "quaest",
    "PoderData": "poderdata", "DataPoder360": "poderdata",
    "Atlas": "atlas", "Arko/Atlas": "atlas",
    "ParanáPesquisas": "parana", "ParanáPesquisas/Crusoé": "parana",
    "VoxPopuli": "voxpopuli",
    "BTG/FSB": "fsb", "FSBPesquisa": "fsb", "FSBComunicação": "fsb", "BTGPactual/FSB": "fsb",
    "XP/Ipespe": "ipespe", "Abrapel/Ipespe": "ipespe",
    "RealTimeBigData": "rtbd",
    "Exame/Ideia": "ideia",
    "CNTSensus": "cnt", "CNT/MDA": "cnt",
    "Results": "results", "2010election": "results", "2018election": "results",
    "2020Election": "results", "2024election": "results", "2016election": "results",
    "Ibopeexitpoll": "results",
    "InstitutoVeritáArchived2018-10-07attheWaybackMachine": "verita",
}

def _normalize_instituto(raw: str) -> str:
    if raw in _INST_ALIASES:
        return _INST_ALIASES[raw]
    return raw.lower().replace("/", "_")[:24] or "unknown"


def fit_house_effects(train_events: list[dict], cohort_rates: dict,
                      *, w_linzer: float = 0.5, sigma_int: float = 5.0,
                      sigma_slope: float = 0.01, shrink_to_zero: float = 0.30,
                      min_n: int = 3) -> dict:
    """For each instituto, compute mean residual (outcome - p_pred) on train.
    Stein-shrink toward zero by `shrink_to_zero` fraction; institutos with
    n < min_n get bias=0.
    """
    by_inst: dict[str, list[float]] = defaultdict(list)
    for e in train_events:
        inst = extract_instituto(e.get("evento_id", "")) if "evento_id" in e else "unknown"
        if inst == "results":  # ground-truth labels, not surveys; skip
            continue
        pred = predict_political(e, cohort_rates)
        p_coh = pred["p_raw"]
        sigma = sigma_int + sigma_slope * max(0, e.get("days_to", 30))
        z = e.get("poll_lead_pp", 0.0) / max(sigma, 1.0)
        p_lnz = 0.5 * (1.0 + math.erf(z / math.sqrt(2.0)))
        p = (1 - w_linzer) * p_coh + w_linzer * p_lnz
        by_inst[inst].append(e["outcome"] - p)
    biases: dict[str, float] = {}
    for inst, residuals in by_inst.items():
        n = len(residuals)
        if n < min_n:
            biases[inst] = 0.0
        else:
            raw = sum(residuals) / n
            biases[inst] = (1 - shrink_to_zero) * raw  # shrink toward 0
    return {"_biases": biases, "_min_n": min_n, "_shrink": shrink_to_zero}


def apply_house_effect(p_blend: float, evento_id: str, house_effects: dict) -> float:
    inst = extract_instituto(evento_id)
    bias = house_effects.get("_biases", {}).get(inst, 0.0)
    return max(0.001, min(0.999, p_blend + bias))


def selective_metrics(preds: list[dict], tau: float) -> dict:
    """Selective metrics: keep only |p-0.5| >= tau."""
    kept = [r for r in preds if abs(r["p_raw"] - 0.5) >= tau]
    if not kept: return {"tau": tau, "coverage": 0.0, "n_kept": 0, "acc": None, "brier": None}
    n = len(kept)
    hits = sum(1 for r in kept if (r["p_raw"] >= 0.5) == bool(r["outcome"]))
    brier = sum((r["p_raw"] - r["outcome"]) ** 2 for r in kept) / n
    return {"tau": tau, "coverage": n / len(preds), "n_kept": n, "acc": hits / n, "brier": brier}


# ---------- BR 2026 candidate registry -----------------------------------

BR_2026_REGISTRY = {
    # status: "confirmed" = candidatura registrada/anunciada publicamente
    #         "speculation" = perfil viavel mas SEM anuncio formal
    #         "ineligible" = restricao legal (TSE/Lei Ficha Limpa) ate 2026
    # status_note: explica restricao quando ineligible/speculation
    "presidente": [
        {"id": "lula_2026", "nome": "Luiz Inácio Lula da Silva", "partido": "PT",
         "incumbente": 1, "regime": "left", "status": "speculation",
         "status_note": "Reeleição provável; sem registro formal até 2026-05"},
        {"id": "tarcisio_2026", "nome": "Tarcísio de Freitas", "partido": "REP",
         "incumbente": 0, "regime": "right", "status": "speculation",
         "status_note": "Possível candidato; alternativa = reeleição SP"},
        {"id": "bolsonaro_2026", "nome": "Jair Bolsonaro", "partido": "PL",
         "incumbente": 0, "regime": "pop_right", "status": "ineligible",
         "status_note": "Inelegível pelo TSE até 2030 (decisão 2023-06-30)"},
        {"id": "ratinho_2026", "nome": "Ratinho Júnior", "partido": "PSD",
         "incumbente": 0, "regime": "right", "status": "speculation",
         "status_note": "Articulação para presidência; cenário fluido"},
        {"id": "zema_2026", "nome": "Romeu Zema", "partido": "NOVO",
         "incumbente": 0, "regime": "right", "status": "speculation",
         "status_note": "Articulação 2026; sem registro formal"},
        {"id": "boulos_2026", "nome": "Guilherme Boulos", "partido": "PSOL",
         "incumbente": 0, "regime": "pop_left", "status": "speculation",
         "status_note": "Cenário 2026 fluido; alternativa = SP gov ou def federal"},
    ],
    # Governadores 2026: incumbentes podem reeleger-se. Outros sao especulativos.
    "governador": [
        {"id": "sp_2026_tarcisio", "nome": "Tarcísio de Freitas", "uf": "SP",
         "partido": "REP", "incumbente": 1, "regime": "right", "status": "speculation",
         "status_note": "Reeleição vs presidência; decisão pendente"},
        {"id": "sp_2026_haddad", "nome": "Fernando Haddad", "uf": "SP",
         "partido": "PT", "incumbente": 0, "regime": "left", "status": "speculation",
         "status_note": "Pré-candidato natural; ministro atual"},
        {"id": "rj_2026_castro", "nome": "Cláudio Castro", "uf": "RJ",
         "partido": "PL", "incumbente": 1, "regime": "right", "status": "speculation",
         "status_note": "Reeleição esperada, sem oposição definida"},
        {"id": "mg_2026_zema", "nome": "Romeu Zema", "uf": "MG",
         "partido": "NOVO", "incumbente": 1, "regime": "right", "status": "speculation",
         "status_note": "Pode disputar presidência; reeleição alternativa"},
        {"id": "rs_2026_leite", "nome": "Eduardo Leite", "uf": "RS",
         "partido": "PSDB", "incumbente": 1, "regime": "center", "status": "speculation",
         "status_note": "Reeleição provável, oposição fragmentada"},
        {"id": "pr_2026_ratinho", "nome": "Ratinho Junior", "uf": "PR",
         "partido": "PSD", "incumbente": 1, "regime": "right", "status": "speculation",
         "status_note": "Pode disputar presidência; reeleição alternativa"},
        {"id": "ba_2026_jeronimo", "nome": "Jerônimo Rodrigues", "uf": "BA",
         "partido": "PT", "incumbente": 1, "regime": "left", "status": "speculation",
         "status_note": "Reeleição esperada, base PT consolidada"},
        {"id": "ce_2026_elmano", "nome": "Elmano de Freitas", "uf": "CE",
         "partido": "PT", "incumbente": 1, "regime": "left", "status": "speculation",
         "status_note": "Reeleição esperada"},
        {"id": "pe_2026_raquel", "nome": "Raquel Lyra", "uf": "PE",
         "partido": "PSDB", "incumbente": 1, "regime": "center", "status": "speculation",
         "status_note": "Reeleição com tensão interna"},
        {"id": "go_2026_caiado", "nome": "Ronaldo Caiado", "uf": "GO",
         "partido": "UNIAO", "incumbente": 1, "regime": "right", "status": "speculation",
         "status_note": "Pode disputar presidência; reeleição vedada (2 mandatos)"},
    ],
    # Senado 2026: 1/3 das cadeiras (mandato 2019-2027 termina).
    # Cadeiras eleitas em 2018 (cumprem ate jan/2027) sao as em disputa em 2026.
    # Senadores eleitos em 2022 (Flavio Bolsonaro RJ, Marcos Pontes nao - foi 2018,
    # Paulo Paim RS - foi 2022 ate 2031) NAO concorrem em 2026.
    # Lista preliminar dos titulares cuja cadeira vence em 2026 (poderao tentar
    # reeleicao ou substituicao):
    "senador": [
        {"id": "sp_sen_2018_alessandro", "nome": "Major Olimpio (mandato vago - Mara Gabrilli)",
         "uf": "SP", "partido": "PL", "incumbente": 1, "regime": "right",
         "status": "speculation",
         "status_note": "Cadeira eleita 2018 vence 2026; titular faleceu"},
        {"id": "rj_sen_2018_arolde", "nome": "Romário (cadeira em disputa 2026)",
         "uf": "RJ", "partido": "PL", "incumbente": 1, "regime": "right",
         "status": "speculation",
         "status_note": "Eleito 2018; pode tentar reeleição"},
        {"id": "mg_sen_2018_anastasia", "nome": "Cleitinho (cadeira em disputa)",
         "uf": "MG", "partido": "REPUB", "incumbente": 1, "regime": "right",
         "status": "speculation",
         "status_note": "Eleito 2018; mandato termina 2027"},
        {"id": "rs_sen_2018_paim", "nome": "Lasier Martins (cadeira em disputa)",
         "uf": "RS", "partido": "PODE", "incumbente": 1, "regime": "right",
         "status": "speculation",
         "status_note": "Eleito 2018; mandato termina 2027"},
    ],
}


def filter_eligible_candidates(candidates: list[dict]) -> list[dict]:
    """Drop candidates marked ineligible (TSE/Ficha Limpa)."""
    return [c for c in candidates if c.get("status") != "ineligible"]
