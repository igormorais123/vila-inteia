"""FastAPI routes for the political-prediction product (BR 2026).

Endpoints:
  GET  /api/v1/politica/health
  GET  /api/v1/politica/elections
  GET  /api/v1/politica/predictions/presidente
  GET  /api/v1/politica/predictions/governador            (?uf=SP)
  GET  /api/v1/politica/predictions/senador
  GET  /api/v1/politica/predictions/all
  GET  /api/v1/politica/backtest                          (Brier/acc/sweep)
  POST /api/v1/politica/predict                           (custom input)

Multi-tenant: optional `X-API-Key` header authenticated against vila_clients.
For now we accept anonymous calls but log them.
"""
from __future__ import annotations

import json
import os
import sys
from datetime import date
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Header, HTTPException, Query
from pydantic import BaseModel, Field

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from engine.political_cohort import (
    BR_2026_REGISTRY, fit_cohorts_political, predict_political,
    load_csv_events, lead_bin, days_bin, lead_to_p_win,
)
from engine.auth_clients import authenticate, get_registry

router = APIRouter(prefix="/api/v1/politica", tags=["politica"])

# Lazy-load + cache the cohort fit and the latest predictions snapshot.
_state = {
    "rates": None,
    "preds_snapshot": None,
    "preds_path": ROOT / "data" / "predictions_2026.json",
    "backtest_path": ROOT / "data" / "political_backtest_results.json",
}

CSV_MAP = {
    "presidente":       "data/backtest/eleicao_presidencial_br_2022.csv",
    "impeachment":      "data/backtest/impeachment_dilma_2016.csv",
    "legislativo":      "data/backtest/lava_jato_2014_2018.csv",
    "prefeito":         "data/backtest/seed_eleicao_municipal_sp_2024.csv",
    "legislativo_2026": "data/backtest/brazil_votes_q1_2026.csv",
}


def _ensure_rates():
    if _state["rates"] is not None:
        return _state["rates"]
    train = []
    for label, rel in CSV_MAP.items():
        path = ROOT / rel
        if path.exists():
            cargo = "legislativo" if "legislativo" in label else label
            train.extend(load_csv_events(path, cargo=cargo))
    _state["rates"] = fit_cohorts_political(train, stein_shrink=0.15)
    _state["n_train"] = len(train)
    return _state["rates"]


def _load_snapshot():
    if _state["preds_snapshot"] is not None:
        return _state["preds_snapshot"]
    if _state["preds_path"].exists():
        with open(_state["preds_path"]) as f:
            _state["preds_snapshot"] = json.load(f)
    return _state["preds_snapshot"]


# -------------- Pydantic models -----------------------------------------------

class IssueKeyRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=80)
    tier: str = Field("free", description="free|pro|enterprise")
    contact: str = Field("", max_length=200)


class PredictRequest(BaseModel):
    cargo: str = Field(..., description="presidente|governador|senador|legislativo|impeachment")
    poll_lead_pp: float = Field(..., description="poll lead in percentage points vs frontrunner")
    days_to_election: int = Field(..., ge=0)
    incumbente: int = Field(0, ge=0, le=1)
    regime: str = Field("center", description="left|right|center|pop_left|pop_right")


class PredictResponse(BaseModel):
    p_cohort: float
    p_linzer: float
    p_blend: float
    cohort_tier: str
    cohort_n: int
    horizon_days: int


# -------------- Endpoints -----------------------------------------------------

@router.get("/health")
def health():
    rates = _ensure_rates()
    snap = _load_snapshot() or {}
    return {
        "status": "ok",
        "n_train_events": _state.get("n_train"),
        "global_rate": rates.get("_global", (0.5, 0))[0],
        "predictions_snapshot": str(_state["preds_path"].relative_to(ROOT)),
        "snapshot_predicted_at": snap.get("predicted_at"),
        "horizon_days": snap.get("horizon_days"),
    }


@router.get("/elections")
def elections():
    """List of 2026 elections in the registry."""
    return {
        "election_date": "2026-10-04",
        "second_round": "2026-10-25",
        "cargos_supported": list(BR_2026_REGISTRY.keys()),
        "presidente_n_candidates": len(BR_2026_REGISTRY["presidente"]),
        "governador_n_candidates": len(BR_2026_REGISTRY["governador"]),
        "senador_n_candidates": len(BR_2026_REGISTRY["senador"]),
        "ufs_covered": sorted({c["uf"] for c in BR_2026_REGISTRY["governador"]}),
    }


@router.get("/predictions/presidente")
def predictions_presidente():
    snap = _load_snapshot()
    if not snap:
        raise HTTPException(404, "no snapshot - run scripts/predict_2026.py")
    return {
        "predicted_at": snap["predicted_at"],
        "election_date": snap["election_date"],
        "horizon_days": snap["horizon_days"],
        "candidates": snap["presidente"],
    }


@router.get("/predictions/governador")
def predictions_governador(uf: Optional[str] = Query(None, pattern="^[A-Z]{2}$")):
    snap = _load_snapshot()
    if not snap:
        raise HTTPException(404, "no snapshot")
    by_uf = snap["governador_by_uf"]
    if uf:
        if uf not in by_uf:
            raise HTTPException(404, f"UF {uf} not in registry")
        return {"uf": uf, "candidates": by_uf[uf]}
    return {"by_uf": by_uf}


@router.get("/predictions/senador")
def predictions_senador():
    snap = _load_snapshot()
    if not snap:
        raise HTTPException(404, "no snapshot")
    return {"candidates": snap["senador"]}


@router.get("/predictions/all")
def predictions_all():
    snap = _load_snapshot()
    if not snap:
        raise HTTPException(404, "no snapshot")
    return snap


@router.get("/backtest")
def backtest():
    if not _state["backtest_path"].exists():
        raise HTTPException(404, "no backtest results - run scripts/backtest_political.py")
    with open(_state["backtest_path"]) as f:
        return json.load(f)


_ADMIN_TOKEN = os.environ.get("VILA_ADMIN_TOKEN", "")


@router.post("/admin/keys/issue")
def admin_issue_key(req: IssueKeyRequest, x_admin_token: Optional[str] = Header(None)):
    if not _ADMIN_TOKEN or x_admin_token != _ADMIN_TOKEN:
        raise HTTPException(403, "admin token required")
    if req.tier not in {"free", "pro", "enterprise"}:
        raise HTTPException(400, "invalid tier")
    key = get_registry().issue(req.name, req.tier, req.contact)
    return {"api_key": key, "tier": req.tier, "name": req.name}


@router.post("/admin/keys/revoke")
def admin_revoke_key(api_key: str = Query(..., min_length=8),
                     x_admin_token: Optional[str] = Header(None)):
    if not _ADMIN_TOKEN or x_admin_token != _ADMIN_TOKEN:
        raise HTTPException(403, "admin token required")
    get_registry().revoke(api_key)
    return {"revoked": api_key}


@router.get("/me")
def whoami(x_api_key: Optional[str] = Header(None)):
    client = authenticate(x_api_key, require_pro=False)
    return {"name": client["name"], "tier": client["tier"], "active": client.get("active", True)}


@router.post("/predict", response_model=PredictResponse)
def predict_custom(req: PredictRequest, x_api_key: Optional[str] = Header(None)):
    authenticate(x_api_key, require_pro=False)  # rate-limit anonymous as free
    rates = _ensure_rates()
    ev = {
        "cargo": req.cargo,
        "lead_bin": lead_bin(req.poll_lead_pp),
        "days_bin": days_bin(req.days_to_election),
        "incumbente": req.incumbente,
        "regime": req.regime,
        "outcome": None,
    }
    pred = predict_political(ev, rates)
    p_lnz = lead_to_p_win(req.poll_lead_pp, req.days_to_election)
    p_blend = 0.20 * pred["p_raw"] + 0.80 * p_lnz
    return PredictResponse(
        p_cohort=round(pred["p_raw"], 4),
        p_linzer=round(p_lnz, 4),
        p_blend=round(p_blend, 4),
        cohort_tier=pred["tier"],
        cohort_n=pred["n_cohort"],
        horizon_days=req.days_to_election,
    )
