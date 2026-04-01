"""
API REST da Vila INTEIA.

Endpoints para controlar e observar a simulação.
Pode ser integrado ao backend principal ou rodar standalone.
"""

from __future__ import annotations

import asyncio
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

try:
    from ..engine.simulacao import SimulacaoVila
    from ..config import config
except (ImportError, ValueError):
    from engine.simulacao import SimulacaoVila
    from config import config


# ============================================================
# ESTADO GLOBAL DA SIMULAÇÃO
# ============================================================

import threading

simulacao: Optional[SimulacaoVila] = None
_sim_lock = threading.Lock()


def obter_simulacao() -> SimulacaoVila:
    """Retorna a simulação ativa ou cria uma nova."""
    global simulacao
    if simulacao is None:
        with _sim_lock:
            if simulacao is None:
                simulacao = SimulacaoVila(nome="vila_inteia_default")
                simulacao.inicializar()
    return simulacao


# ============================================================
# ROUTER
# ============================================================

router = APIRouter(prefix="/api/v1/vila", tags=["Vila INTEIA"])


# --- Modelos de Request ---

class IniciarRequest(BaseModel):
    nome: str = "vila_inteia"
    max_agentes: int = 140


class StepRequest(BaseModel):
    n_steps: int = 1


class TopicoRequest(BaseModel):
    topico: str
    importancia: int = 8


# ============================================================
# ENDPOINTS DE CONTROLE
# ============================================================

@router.post("/iniciar")
async def iniciar_simulacao(req: IniciarRequest):
    """Inicializa uma nova simulação."""
    global simulacao
    simulacao = SimulacaoVila(nome=req.nome)
    simulacao.inicializar(max_agentes=req.max_agentes)
    return {
        "status": "ok",
        "mensagem": f"Simulação '{req.nome}' iniciada com {len(simulacao.personas)} agentes",
        "agentes": len(simulacao.personas),
    }


@router.post("/step")
async def executar_steps(req: StepRequest):
    """Executa N steps da simulação."""
    sim = obter_simulacao()
    resumos = sim.executar(n_steps=req.n_steps)
    return {
        "status": "ok",
        "steps_executados": len(resumos),
        "step_atual": sim.step,
        "hora_atual": sim.hora_atual.strftime("%Y-%m-%d %H:%M"),
        "resumos": resumos[-5:],  # últimos 5
    }


@router.post("/pausar")
async def pausar():
    """Pausa a simulação."""
    sim = obter_simulacao()
    sim.pausar()
    return {"status": "pausada"}


@router.post("/retomar")
async def retomar():
    """Retoma a simulação."""
    sim = obter_simulacao()
    sim.retomar()
    return {"status": "retomada"}


@router.post("/parar")
async def parar():
    """Para e salva a simulação."""
    sim = obter_simulacao()
    sim.parar()
    return {"status": "parada", "step_final": sim.step}


# ============================================================
# ENDPOINTS DE OBSERVAÇÃO
# ============================================================

@router.get("/estado")
async def estado_mundo():
    """Retorna o estado completo do mundo."""
    sim = obter_simulacao()
    return sim.estado_mundo()


@router.get("/mapa")
async def mapa_calor():
    """Retorna mapa de calor de ocupação dos locais."""
    sim = obter_simulacao()
    return {
        "step": sim.step,
        "hora": sim.hora_atual.strftime("%H:%M"),
        "mapa": sim.mapa_calor(),
    }


@router.get("/agentes")
async def listar_agentes(
    local: Optional[str] = None,
    categoria: Optional[str] = None,
    tier: Optional[str] = None,
):
    """Lista agentes com filtros opcionais."""
    sim = obter_simulacao()
    agentes = []

    for persona in sim.personas.values():
        if local and persona.rascunho.local_atual != local:
            continue
        if categoria and persona.categoria != categoria:
            continue
        if tier and persona.tier != tier:
            continue
        agentes.append(persona.resumo())

    return {
        "total": len(agentes),
        "agentes": agentes,
    }


@router.get("/agente/{agente_id}")
async def detalhe_agente(agente_id: str):
    """Retorna detalhes completos de um agente."""
    sim = obter_simulacao()
    detalhe = sim.consultar_agente(agente_id)
    if not detalhe:
        raise HTTPException(404, f"Agente {agente_id} não encontrado")
    return detalhe


@router.get("/conversas")
async def conversas_recentes(limite: int = Query(10, ge=1, le=50)):
    """Lista conversas recentes."""
    sim = obter_simulacao()
    return {
        "total": len(sim.conversas_recentes),
        "conversas": sim.conversas_recentes[-limite:],
    }


@router.get("/sinteses")
async def listar_sinteses():
    """Lista sínteses de inteligência coletiva."""
    sim = obter_simulacao()
    return {
        "total": len(sim.sinteses),
        "sinteses": sim.sinteses[-20:],
    }


@router.get("/locais")
async def listar_locais():
    """Lista todos os locais do campus."""
    from ..engine.campus import LOCAIS
    return {
        "total": len(LOCAIS),
        "locais": [
            {
                "id": l.id,
                "nome": l.nome,
                "tipo": l.tipo,
                "descricao": l.descricao,
                "capacidade": l.capacidade,
                "nivel_formalidade": l.nivel_formalidade,
                "nivel_energia": l.nivel_energia,
                "posicao_x": l.posicao_x,
                "posicao_y": l.posicao_y,
                "conexoes": l.conexoes,
            }
            for l in LOCAIS.values()
        ],
    }


@router.get("/stats")
async def estatisticas():
    """Retorna estatísticas da simulação."""
    sim = obter_simulacao()
    return {
        "step": sim.step,
        "hora": sim.hora_atual.strftime("%Y-%m-%d %H:%M"),
        **sim.stats,
        "agentes_por_local": sim.mapa_calor(),
        "topicos_ativos": config.topicos_ativos,
    }


# ============================================================
# ENDPOINTS DE INTERAÇÃO
# ============================================================

@router.post("/topico")
async def injetar_topico(req: TopicoRequest):
    """Injeta um tópico para os agentes discutirem."""
    sim = obter_simulacao()
    sim.injetar_topico(req.topico, req.importancia)
    return {
        "status": "ok",
        "mensagem": f"Tópico '{req.topico}' injetado no campus",
        "topicos_ativos": config.topicos_ativos,
    }


@router.post("/sintetizar/{topico}")
async def forcar_sintese(topico: str):
    """Força síntese de inteligência coletiva sobre um tópico."""
    from ..engine.cognitivo.sintetizar import sintetizar

    sim = obter_simulacao()
    resultado = sintetizar(sim.personas, topico, sim.hora_atual, min_perspectivas=2)

    if not resultado:
        raise HTTPException(
            404,
            f"Sem perspectivas suficientes sobre '{topico}'. "
            "Execute mais steps ou injete o tópico primeiro."
        )

    sim.sinteses.append(resultado)
    return resultado


@router.post("/salvar")
async def salvar():
    """Salva o estado atual da simulação."""
    sim = obter_simulacao()
    sim.salvar()
    return {"status": "salvo", "diretorio": sim.dir_dados}


# ============================================================
# ENDPOINTS DE INTELIGÊNCIA (Previsibilidade + Autoresearch)
# ============================================================

@router.get("/previsibilidade")
async def previsibilidade():
    """Retorna tendências e previsões da vila."""
    sim = obter_simulacao()
    tendencias = sim.motor_previsibilidade.analisar_tendencias()
    return {
        "tendencias": [t.to_dict() for t in tendencias],
        "briefing": sim.motor_previsibilidade.gerar_briefing_helena(),
        "total_steps_analisados": len(sim.motor_previsibilidade.palavras_por_step),
    }


@router.get("/previsibilidade/saturacao/{topico}")
async def saturacao_topico(topico: str):
    """Retorna nível de saturação de um tópico."""
    sim = obter_simulacao()
    return {
        "topico": topico,
        "saturacao": sim.motor_previsibilidade.prever_saturacao(topico),
        "engajamento_previsto": sim.motor_previsibilidade.prever_engajamento(topico),
    }


@router.get("/autoresearch")
async def autoresearch_status():
    """Retorna estado do motor de autoresearch."""
    sim = obter_simulacao()
    return sim.motor_autoresearch.to_dict()


@router.post("/autoresearch/executar")
async def executar_autoresearch(req: TopicoRequest):
    """Força execução de autoresearch sobre um tema."""
    sim = obter_simulacao()
    pesquisa = sim.motor_autoresearch.executar_pesquisa(
        req.topico, sim.personas, sim.step,
    )
    if not pesquisa:
        raise HTTPException(400, "Pesquisa falhou (poucos respondentes)")
    return pesquisa.to_dict()


@router.get("/live")
async def estado_live():
    """Estado completo da vila em tempo real."""
    sim = obter_simulacao()
    return {
        "step": sim.step,
        "hora_simulacao": sim.hora_atual.strftime("%Y-%m-%d %H:%M"),
        "agentes_ativos": sum(1 for p in sim.personas.values() if p.ativo),
        "stats": sim.stats,
        "topicos_ativos": config.topicos_ativos,
        "conversas_recentes": sim.conversas_recentes[-10:],
        "sinteses_recentes": sim.sinteses[-5:],
        "previsibilidade": sim.motor_previsibilidade.to_dict(),
        "autoresearch": sim.motor_autoresearch.to_dict(),
        "rede_social": {
            "total_posts": sim.rede_social.total_posts,
            "total_comentarios": sim.rede_social.total_comentarios,
            "total_reacoes": sim.rede_social.total_reacoes,
        },
    }
