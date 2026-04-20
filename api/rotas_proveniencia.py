"""
Rotas /api/v1/proveniencia — Onda 5.

Expõe proveniência cognitiva de matérias publicadas e resultados de backtest.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from engine.proveniencia import construir_proveniencia, hash_trace
from engine.proveniencia.construcao import serializar_arvore
from engine.backtest import rodar_backtest, carregar_dataset


router = APIRouter(prefix="/api/v1", tags=["proveniencia-backtest"])


class ProveReq(BaseModel):
    materia_id: str
    traces: list[dict]
    agentes_envolvidos: list[str] = []
    citacoes: list[tuple[str, str]] = []


@router.post("/materia/proveniencia")
def endpoint_proveniencia(req: ProveReq):
    prov = construir_proveniencia(
        materia_id=req.materia_id,
        traces=req.traces,
        agentes_envolvidos=req.agentes_envolvidos or None,
        citacoes=req.citacoes or None,
    )
    h = hash_trace(prov)
    return {
        "materia_id": prov.materia_id,
        "trace_hash": h,
        "agentes_envolvidos": prov.agentes_envolvidos,
        "fases_cobertas": prov.fases_cobertas,
        "tokens_totais": prov.tokens_totais,
        "custo_usd_total": prov.custo_usd_total,
        "duracao_ms_total": prov.duracao_ms_total,
        "arvore": serializar_arvore(prov.raiz),
        "influencias": [
            {"origem": i.agente_origem, "destino": i.agente_destino, "peso": i.peso}
            for i in prov.grafo_influencia
        ],
    }


@router.get("/backtest/datasets")
def endpoint_listar_datasets():
    from pathlib import Path
    base = Path("data/backtest")
    if not base.exists():
        return {"datasets": []}
    return {"datasets": [p.stem for p in base.glob("*.csv")]}


@router.get("/backtest/rodar/{dataset}")
def endpoint_backtest(dataset: str, n_sims: int = 1):
    try:
        r = rodar_backtest(dataset, n_sims=n_sims)
    except FileNotFoundError as e:
        raise HTTPException(404, str(e))
    return {
        "dataset": r.dataset,
        "n_eventos": r.n_eventos,
        "brier": r.brier,
        "log_loss": r.log_loss,
        "accuracy": r.accuracy,
        "calibration": r.calibration,
        "predicoes": r.predicoes,
    }
