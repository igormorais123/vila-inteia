"""
Rotas FastAPI — /api/v1/psicohistoria

Expõe engine.psicohistoria para o frontend.
"""

from __future__ import annotations

import numpy as np
from fastapi import APIRouter
from pydantic import BaseModel

from engine.psicohistoria.grafo_eventos import (
    construir_grafo_vila, contagens_de_lista,
)
from engine.psicohistoria.equacoes import (
    prever_trajetoria, distribuicao_estacionaria,
    tempo_ate_absorver, entropia_trajetoria,
    predizer_estado_provavel,
)
from engine.psicohistoria.plano import (
    plano_seldon, divergencia_plano_realidade,
)
from engine.psicohistoria.detectores import (
    detectar_mule, criticidade_evento, agentes_anomalos_por_comportamento,
)


router = APIRouter(prefix="/api/v1/psicohistoria", tags=["psicohistoria"])


class GrafoReq(BaseModel):
    eventos: list[str] | None = None   # sequência histórica opcional; senão baseline


@router.post("/grafo")
def endpoint_grafo(req: GrafoReq):
    """Retorna estados + matriz de transição (baseline ou calibrada)."""
    if req.eventos:
        g = construir_grafo_vila(contagens_de_lista(req.eventos))
    else:
        g = construir_grafo_vila()
    return {
        "estados": [
            {"id": eid, "descricao": g.estados[eid].descricao}
            for eid in g.estados
        ],
        "matriz": g.matriz.tolist(),
    }


class PrevReq(BaseModel):
    estado_inicial: str
    passos: int = 50
    eventos: list[str] | None = None


@router.post("/prever")
def endpoint_prever(req: PrevReq):
    g = construir_grafo_vila(contagens_de_lista(req.eventos) if req.eventos else None)
    traj = prever_trajetoria(g, req.estado_inicial, req.passos)
    est_prov, prob = predizer_estado_provavel(g, req.estado_inicial, req.passos)
    return {
        "trajetoria": traj.tolist(),
        "estados_ordem": list(g.estados.keys()),
        "entropia_por_passo": entropia_trajetoria(traj).tolist(),
        "estado_provavel_final": est_prov,
        "probabilidade_final": prob,
    }


@router.get("/estacionaria")
def endpoint_estacionaria():
    g = construir_grafo_vila()
    return distribuicao_estacionaria(g)


class PlanoReq(BaseModel):
    estado_inicial: str = "bootstrap"
    horizonte: int = 500


@router.post("/plano-seldon")
def endpoint_plano(req: PlanoReq):
    g = construir_grafo_vila()
    p = plano_seldon(g, req.estado_inicial, req.horizonte)
    return {
        "horizonte": p.horizonte,
        "estado_inicial": p.estado_inicial,
        "destino_provavel": p.destino_provavel,
        "probabilidade_destino": p.probabilidade_destino,
        "estados_modais": p.estados_modais,
        "crises": [
            {
                "passo": c.passo,
                "antes": c.estado_antes,
                "depois": c.estado_depois,
                "probabilidade": c.probabilidade,
            }
            for c in p.crises
        ],
    }


class MuleReq(BaseModel):
    trajetoria_real: list[str]
    estado_inicial: str = "bootstrap"
    z_score: float = 3.0


@router.post("/detectar-mule")
def endpoint_mule(req: MuleReq):
    g = construir_grafo_vila()
    traj_prev = prever_trajetoria(g, req.estado_inicial, len(req.trajetoria_real))
    mules = detectar_mule(req.trajetoria_real, traj_prev, g, z_score_limite=req.z_score)
    return {
        "n_mules": len(mules),
        "mules": [
            {
                "tipo": m.tipo,
                "descricao": m.descricao,
                "passo": m.passo,
                "z_score": m.z_score,
            }
            for m in mules
        ],
    }


class DivergenciaReq(BaseModel):
    trajetoria_real: list[str]
    estado_inicial: str = "bootstrap"
    horizonte: int = 500


@router.post("/divergencia")
def endpoint_divergencia(req: DivergenciaReq):
    g = construir_grafo_vila()
    p = plano_seldon(g, req.estado_inicial, req.horizonte)
    return divergencia_plano_realidade(p, req.trajetoria_real, g)


@router.get("/criticidade/{estado}")
def endpoint_criticidade(estado: str):
    g = construir_grafo_vila()
    return {"estado": estado, "criticidade": criticidade_evento(g, estado)}


class AgentesAnomReq(BaseModel):
    comportamentos: dict[str, dict[str, float]]
    n_desvios: float = 2.5


@router.post("/agentes-anomalos")
def endpoint_agentes_anomalos(req: AgentesAnomReq):
    outliers = agentes_anomalos_por_comportamento(
        req.comportamentos, req.n_desvios
    )
    return {"n_outliers": len(outliers), "ids": outliers}


# =====================================================
# Onda 11 — Tracking em tempo real da trajetória real da Vila
# =====================================================

@router.get("/trajetoria-atual")
def endpoint_trajetoria_atual(janela: int = 100):
    """Últimos N estados observados da simulação rodando."""
    from engine.psicohistoria.detector_estado_vila import RASTREADOR_GLOBAL
    traj = RASTREADOR_GLOBAL.trajetoria
    estados = traj.estados[-janela:]
    steps = traj.steps[-janela:]
    return {
        "estados": estados,
        "steps": steps,
        "ultimo_estado": traj.ultimo_estado(),
        "distribuicao_historica": traj.distribuicao_historica(),
        "n_steps_rastreados": len(traj.estados),
    }


@router.get("/divergencia-atual")
def endpoint_divergencia_atual():
    """Compara trajetória real com Plano de Seldon (do estado inicial observado)."""
    from engine.psicohistoria.detector_estado_vila import RASTREADOR_GLOBAL
    from engine.psicohistoria.grafo_eventos import construir_grafo_vila
    from engine.psicohistoria.plano import plano_seldon, divergencia_plano_realidade

    traj = RASTREADOR_GLOBAL.trajetoria
    if not traj.estados:
        return {"n_steps": 0, "divergencia": None}
    g = construir_grafo_vila()
    p = plano_seldon(g, traj.estados[0], horizonte=len(traj.estados) + 10)
    d = divergencia_plano_realidade(p, traj.estados, g)
    return {"n_steps": len(traj.estados), **d,
            "destino_planejado": p.destino_provavel,
            "ultimo_observado": traj.ultimo_estado()}


@router.get("/mules-detectados")
def endpoint_mules_detectados():
    from engine.psicohistoria.detector_estado_vila import RASTREADOR_GLOBAL
    return {
        "n_mules": len(RASTREADOR_GLOBAL.trajetoria.mules_detectados),
        "mules_recentes": RASTREADOR_GLOBAL.trajetoria.mules_detectados[-20:],
    }
