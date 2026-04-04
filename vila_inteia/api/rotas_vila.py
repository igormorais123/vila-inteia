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
from typing import Optional

from ..engine.simulacao import SimulacaoVila
from ..config import config


# ============================================================
# ESTADO GLOBAL DA SIMULAÇÃO
# ============================================================

simulacao: Optional[SimulacaoVila] = None


def obter_simulacao() -> SimulacaoVila:
    """Retorna a simulação ativa ou cria/carrega uma."""
    global simulacao
    if simulacao is None:
        simulacao = SimulacaoVila(nome="vila_inteia_default")
        # Tentar carregar estado salvo
        loaded = simulacao.carregar()
        if loaded:
            # Re-inicializar personas se nao carregadas
            if not simulacao.personas:
                simulacao.inicializar()
            print(f"[Vila] Estado restaurado: step {simulacao.step}, {len(simulacao.personas)} agentes")
        else:
            simulacao.inicializar()
            print(f"[Vila] Nova simulacao: {len(simulacao.personas)} agentes")
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
    """Executa N steps da simulação (async para nao bloquear)."""
    import asyncio
    sim = obter_simulacao()
    # Limitar a 3 steps por request para nao bloquear muito tempo
    n = min(req.n_steps, 3)
    resumos = await asyncio.to_thread(sim.executar, n_steps=n)
    return {
        "status": "ok",
        "steps_executados": len(resumos),
        "step_atual": sim.step,
        "hora_atual": sim.hora_atual.strftime("%Y-%m-%d %H:%M"),
        "resumos": resumos[-5:],
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
    resultado = sintetizar(sim.personas, topico, sim.hora_atual, min_perspectivas=1)

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



class ConsultaInput(BaseModel):
    pergunta: str
    n_consultores: int = 5
    categorias: list = []

@router.post("/consulta")
async def consultar_painel(dados: ConsultaInput):
    """Consulte um painel de N consultores sobre qualquer tema.
    
    Seleciona os consultores mais relevantes por categoria e gera
    respostas individuais com personalidade. Produto premium INTEIA."""
    from ..engine.ia_client import chamar_llm_conversa
    import random
    
    sim = obter_simulacao()
    
    # Selecionar consultores relevantes
    candidatos = list(sim.personas.values())
    if dados.categorias:
        filtrados = [p for p in candidatos if p.categoria in dados.categorias]
        if filtrados:
            candidatos = filtrados
    
    # Priorizar Tier S e diversidade de categorias
    tier_s = [p for p in candidatos if p.tier == "S"]
    outros = [p for p in candidatos if p.tier != "S"]
    random.shuffle(tier_s)
    random.shuffle(outros)
    selecionados = (tier_s + outros)[:dados.n_consultores]
    
    respostas = []
    for persona in selecionados:
        d = persona.dados_consultor
        system = f"Voce e {persona.nome_exibicao}, {persona.titulo}. Responda com seu estilo unico. Max 150 palavras. Portugues do Brasil."
        
        resp = chamar_llm_conversa(system, dados.pergunta, modelo="rapido", max_tokens=300)
        if not resp:
            resp = f"{persona.nome_exibicao} esta analisando a questao."
        
        respostas.append({
            "agente_id": persona.id,
            "agente_nome": persona.nome_exibicao,
            "titulo": persona.titulo,
            "categoria": persona.categoria,
            "tier": persona.tier,
            "resposta": resp,
        })
    
    return {
        "pergunta": dados.pergunta,
        "total_consultores": len(respostas),
        "respostas": respostas,
    }

class ChatCompletionInput(BaseModel):
    model: str = "BestFREE"
    messages: list = []
    max_tokens: int = 200
    temperature: float = 0.8

@router.post("/chat/completions")
@router.post("/chat")
async def chat_completion_compat(dados: dict):
    """Chat endpoint compativel com formato OpenAI para o 3D."""
    from ..engine.ia_client import chamar_llm_conversa
    
    messages = dados.get("messages", [])
    if not messages:
        # Try our format
        agente_id = dados.get("agente_id", "")
        mensagem = dados.get("mensagem", "")
        if agente_id and mensagem:
            # Use our chat logic
            sim = obter_simulacao()
            persona = sim.personas.get(agente_id)
            if not persona:
                return {"error": "Agente nao encontrado"}
            d = persona.dados_consultor
            system = f"Voce e {persona.nome_exibicao}, {persona.titulo}. Responda com seu estilo. Max 200 palavras. Portugues."
            resp = chamar_llm_conversa(system, mensagem, modelo="rapido", max_tokens=400)
            return {"agente_id": agente_id, "agente_nome": persona.nome_exibicao, "titulo": persona.titulo, "categoria": persona.categoria, "resposta": resp or "Estou refletindo..."}
    
    # OpenAI format: extract system+user from messages
    system = ""
    user = ""
    for m in messages:
        if m.get("role") == "system" or (m.get("role") == "user" and "[INSTRUCAO]" in m.get("content","")):
            parts = m.get("content","").split("[TAREFA]")
            if len(parts) > 1:
                system = parts[0].replace("[INSTRUCAO]","").strip()
                user = parts[1].strip()
            else:
                system = m.get("content","")
        elif m.get("role") == "user":
            user = m.get("content","")
    
    if not user:
        user = "Responda."
    
    resp = chamar_llm_conversa(system or "Voce e um consultor lendario. Responda em portugues.", user, modelo="rapido", max_tokens=dados.get("max_tokens", 200))
    
    return {
        "id": "chatcmpl-vila",
        "object": "chat.completion",
        "choices": [{
            "index": 0,
            "message": {"role": "assistant", "content": resp or "Estou refletindo sobre sua pergunta."},
            "finish_reason": "stop"
        }],
        "usage": {"total_tokens": 0}
    }

