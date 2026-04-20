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


# =====================================================
# Ondas 13-16 — Calibração, HMM, recomendação, persistência
# =====================================================

class CalibReq(BaseModel):
    metodo: str = "laplace"
    alpha: float = 0.1


@router.post("/calibrar")
def endpoint_calibrar(req: CalibReq):
    """Recalibra matriz M a partir da trajetória real observada (Onda 13)."""
    from engine.psicohistoria.calibracao_online import calibrar, perplexity
    from engine.psicohistoria.detector_estado_vila import RASTREADOR_GLOBAL
    from engine.psicohistoria.grafo_eventos import construir_grafo_vila
    traj = RASTREADOR_GLOBAL.trajetoria.estados
    if len(traj) < 2:
        return {"erro": "trajetória insuficiente", "n_steps": len(traj)}
    r = calibrar(traj, metodo=req.metodo, alpha=req.alpha)
    g = construir_grafo_vila()
    pp_orig = perplexity(traj, r.matriz_original, g)
    pp_cal = perplexity(traj, r.matriz_calibrada, g)
    return {
        "n_transicoes": r.n_transicoes,
        "estados_observados": r.estados_observados,
        "cobertura_pct": r.cobertura_pct,
        "divergencia_frobenius": r.divergencia_frobenius,
        "perplexity_original": pp_orig,
        "perplexity_calibrada": pp_cal,
        "matriz_calibrada": r.matriz_calibrada.tolist(),
    }


@router.get("/hmm/descobrir")
def endpoint_hmm(k: int = 8, smoothing: int = 3):
    """Descobre K estados latentes não-supervisionados (Onda 15)."""
    from engine.psicohistoria.hmm_estados import descobrir_estados
    from engine.psicohistoria.detector_estado_vila import RASTREADOR_GLOBAL
    metricas = [
        {
            "n_conversas": m.n_conversas,
            "n_reflexoes": m.n_reflexoes,
            "n_agentes_ativos": m.n_agentes_ativos,
            "n_agentes_latentes": m.n_agentes_latentes,
            "polarizacao_media": m.polarizacao_media,
            "gini_economia": m.gini_economia,
            "propostas_constituintes_ativas": m.propostas_constituintes_ativas,
            "contribuicoes_ao_desafio": m.contribuicoes_ao_desafio,
        }
        for m in RASTREADOR_GLOBAL.trajetoria.metricas_por_step
    ]
    if len(metricas) < k:
        return {"erro": "steps insuficientes", "n_steps": len(metricas), "k_solicitado": k}
    r = descobrir_estados(metricas, k=k, smoothing_janela=smoothing)
    return {
        "k": r.k,
        "iteracoes": r.iteracoes,
        "inercia": r.inercia,
        "labels_por_step": r.labels_por_step,
        "estados_latentes": [
            {"id": e.id, "n_membros": e.n_membros,
             "rotulo_auto": e.rotulo_auto,
             "centroide": e.centroide.tolist()}
            for e in r.estados_latentes
        ],
    }


@router.get("/recomendacao")
def endpoint_recomendacao():
    """Recomendação estratégica via Plano de Seldon (Onda 16)."""
    from engine.psicohistoria.decision_helper import recomendar_acao
    r = recomendar_acao()
    return {
        "estado_atual": r.estado_atual,
        "destino_previsto": r.destino_previsto,
        "urgencia": r.urgencia,
        "acao_recomendada": r.acao_recomendada,
        "justificativa": r.justificativa,
        "crises_proximas": r.crises_proximas,
    }


@router.get("/persistencia/stats")
def endpoint_persistencia_stats():
    from engine.psicohistoria.persistencia import PERSISTENCIA_GLOBAL
    return PERSISTENCIA_GLOBAL.stats()


@router.post("/persistencia/flush")
def endpoint_persistencia_flush():
    from engine.psicohistoria.persistencia import PERSISTENCIA_GLOBAL
    return {"flushed": PERSISTENCIA_GLOBAL.flush()}
