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


@router.get("/relatorio")
async def relatorio_executivo():
    """Relatório executivo consolidado — CONCLUSÕES, não dados brutos."""
    from engine.relatorio import gerar_relatorio
    sim = obter_simulacao()
    rel = gerar_relatorio(sim)
    return rel.to_dict()


@router.get("/relatorio/markdown")
async def relatorio_markdown():
    """Relatório em Markdown para leitura humana."""
    from engine.relatorio import gerar_relatorio
    from fastapi.responses import PlainTextResponse
    sim = obter_simulacao()
    rel = gerar_relatorio(sim)
    return PlainTextResponse(rel.to_markdown(), media_type="text/markdown")


# ============================================================
# ENDPOINTS DE DESAFIO COLETIVO
# ============================================================

class DesafioRequest(BaseModel):
    tema: str = ""
    descricao: str = ""
    documento: str = ""  # Conteúdo de arquivo anexado (texto)
    steps_por_fase: int = 100
    # Compat: aceita desafio_id antigo como alias de tema
    desafio_id: str = ""


class ContribuicaoRequest(BaseModel):
    agente_id: str
    conteudo: str
    tipo: str = "proposta"


class VotoRequest(BaseModel):
    agente_id: str
    entrega_id: str
    favor: bool = True


class PythonRequest(BaseModel):
    agente_id: str
    codigo: str


@router.get("/desafios")
async def listar_desafios_disponiveis():
    """Retorna instruções — o tema é definido pelo usuário."""
    from engine.desafio import listar_desafios
    return {"desafios": listar_desafios()}


@router.post("/desafio/iniciar")
async def iniciar_desafio(req: DesafioRequest):
    """Inicia um desafio coletivo a partir do tema do usuário."""
    sim = obter_simulacao()
    tema = req.tema or req.desafio_id  # compat
    if not tema:
        raise HTTPException(400, "Informe o tema do desafio")
    return sim.iniciar_desafio(
        desafio_id=tema,
        descricao=req.descricao,
        documento=req.documento,
        steps_por_fase=req.steps_por_fase,
    )


@router.get("/desafio")
async def estado_desafio():
    """Retorna estado atual do desafio."""
    sim = obter_simulacao()
    if not sim.desafio.ativo and sim.desafio.status != "concluido":
        return {"status": "inativo", "catalogo": "/api/v1/vila/desafios"}
    return sim.desafio.to_dict()


@router.post("/desafio/contribuir")
async def contribuir_desafio(req: ContribuicaoRequest):
    """Registra contribuição ao desafio."""
    sim = obter_simulacao()
    return sim.contribuir_desafio(req.agente_id, req.conteudo, req.tipo)


@router.post("/desafio/votar")
async def votar_desafio(req: VotoRequest):
    """Registra voto em uma entrega."""
    sim = obter_simulacao()
    return sim.votar_desafio(req.agente_id, req.entrega_id, req.favor)


# ============================================================
# ENDPOINTS DE FERRAMENTAS
# ============================================================

@router.post("/ferramentas/python")
async def executar_python_sandbox(req: PythonRequest):
    """Executa Python no sandbox de um agente."""
    sim = obter_simulacao()
    persona = sim.personas.get(req.agente_id)
    if not persona:
        raise HTTPException(404, f"Agente {req.agente_id} não encontrado")

    local = persona.rascunho.local_atual
    saldo = sim.incentivos.saldo(req.agente_id)

    resultado = sim.toolkit.executar_python(
        req.agente_id, req.codigo, local, saldo, sim.step
    )

    # Cobrar recurso e recompensar se sucesso
    from engine.ferramentas_agente import custo_uso_local
    custo = custo_uso_local(local)
    if resultado.sucesso:
        sim.incentivos.cobrar_recurso(req.agente_id, custo, "Python sandbox", sim.step)
        sim.incentivos.recompensar(req.agente_id, "codigo_executado", sim.step)

    return resultado.to_dict()


@router.get("/ferramentas/recursos/{local_id}")
async def recursos_local(local_id: str):
    """Retorna recursos disponíveis em um local."""
    from engine.ferramentas_agente import RECURSOS_POR_LOCAL
    recurso = RECURSOS_POR_LOCAL.get(local_id)
    if not recurso:
        return {"ferramentas": [], "custo": 0}
    return recurso


# ============================================================
# ENDPOINTS DE ECONOMIA / INCENTIVOS
# ============================================================

@router.get("/economia")
async def economia():
    """Retorna estado da economia da vila."""
    sim = obter_simulacao()
    return sim.incentivos.to_dict()


@router.get("/economia/carteira/{agente_id}")
async def carteira_agente(agente_id: str):
    """Retorna carteira de um agente."""
    sim = obter_simulacao()
    return sim.incentivos.obter_carteira(agente_id).to_dict()


@router.get("/economia/ranking")
async def ranking_economia(top: int = Query(20, ge=1, le=100)):
    """Ranking de agentes por reputação."""
    sim = obter_simulacao()
    return {"ranking": sim.incentivos.top_agentes(top)}


# ============================================================
# ENDPOINTS DE OFICINAS E WORKSPACE
# ============================================================

@router.get("/oficinas")
async def listar_oficinas():
    """Lista todas as oficinas (ferramentas reais por local)."""
    from engine.oficinas import todas_oficinas
    return {"oficinas": todas_oficinas()}


@router.get("/oficinas/{local_id}")
async def detalhe_oficina(local_id: str):
    """Detalhe de uma oficina: ferramentas, artefatos produzidos."""
    from engine.oficinas import oficina_do_local
    oficina = oficina_do_local(local_id)
    if not oficina:
        return {"erro": f"Sem oficina no local '{local_id}'"}
    return oficina.to_dict()


@router.get("/workspace")
async def workspace_listar():
    """Lista artefatos produzidos no workspace do desafio ativo."""
    sim = obter_simulacao()
    desafio_id = sim.desafio.id if sim.desafio.ativo else ""
    if not desafio_id:
        return {"total_arquivos": 0, "arquivos": []}
    return sim.workspace.to_dict(desafio_id)


@router.get("/workspace/{desafio_id}")
async def workspace_desafio(desafio_id: str):
    """Lista artefatos de um desafio específico."""
    sim = obter_simulacao()
    return sim.workspace.to_dict(desafio_id)


@router.get("/workspace/{desafio_id}/compilar")
async def workspace_compilar(desafio_id: str):
    """Compila todas as entregas em documento único."""
    from fastapi.responses import PlainTextResponse
    sim = obter_simulacao()
    compilado = sim.workspace.compilar(desafio_id)
    return PlainTextResponse(compilado, media_type="text/markdown")


@router.get("/workspace/{desafio_id}/arquivo/{nome_arquivo:path}")
async def workspace_ler_arquivo(desafio_id: str, nome_arquivo: str):
    """Lê conteúdo de um artefato."""
    sim = obter_simulacao()
    conteudo = sim.workspace.ler(desafio_id, nome_arquivo)
    if not conteudo:
        raise HTTPException(404, f"Arquivo '{nome_arquivo}' não encontrado")
    return {"arquivo": nome_arquivo, "conteudo": conteudo}


# ============================================================
# PROXY — Chat e Persistência (resolve CORS do jogo.html)
# ============================================================

import httpx

_BACKEND_PRINCIPAL = "https://api.inteia.com.br"
_proxy_client = None


def _get_proxy_client():
    global _proxy_client
    if _proxy_client is None:
        _proxy_client = httpx.AsyncClient(timeout=60.0)
    return _proxy_client


@router.post("/chat")
async def proxy_chat(body: dict):
    """Proxy para OmniRoute/chat — resolve CORS."""
    client = _get_proxy_client()
    try:
        resp = await client.post(
            f"{_BACKEND_PRINCIPAL}/api/v1/vila-inteia/chat",
            json=body,
            timeout=60.0,
        )
        return resp.json()
    except Exception as e:
        raise HTTPException(502, f"Proxy chat falhou: {e}")


@router.post("/mensagens/salvar")
async def proxy_mensagens_salvar(body: dict):
    """Proxy para salvar mensagens — resolve CORS."""
    client = _get_proxy_client()
    try:
        resp = await client.post(
            f"{_BACKEND_PRINCIPAL}/api/v1/vila-inteia/mensagens/salvar",
            json=body,
            timeout=15.0,
        )
        return resp.json()
    except Exception:
        return {"status": "salvo_local"}


@router.get("/mensagens/carregar/{tipo}")
async def proxy_mensagens_carregar(tipo: str, sessao_id: str = "", limit: int = 200):
    """Proxy para carregar mensagens — resolve CORS."""
    client = _get_proxy_client()
    try:
        resp = await client.get(
            f"{_BACKEND_PRINCIPAL}/api/v1/vila-inteia/mensagens/carregar/{tipo}",
            params={"sessao_id": sessao_id, "limit": limit},
            timeout=15.0,
        )
        return resp.json()
    except Exception:
        return []


@router.post("/estado/salvar")
async def proxy_estado_salvar(body: dict):
    """Proxy para salvar estado — resolve CORS."""
    client = _get_proxy_client()
    try:
        resp = await client.post(
            f"{_BACKEND_PRINCIPAL}/api/v1/vila-inteia/estado/salvar",
            json=body,
            timeout=15.0,
        )
        return resp.json()
    except Exception:
        return {"status": "salvo_local"}


@router.get("/estado/carregar/{tipo}")
async def proxy_estado_carregar(tipo: str, sessao_id: str = ""):
    """Proxy para carregar estado — resolve CORS."""
    client = _get_proxy_client()
    try:
        resp = await client.get(
            f"{_BACKEND_PRINCIPAL}/api/v1/vila-inteia/estado/carregar/{tipo}",
            params={"sessao_id": sessao_id},
            timeout=15.0,
        )
        return resp.json()
    except Exception:
        return {}


@router.get("/constituicao/artigos")
async def proxy_constituicao():
    """Proxy para constituição — resolve CORS."""
    client = _get_proxy_client()
    try:
        resp = await client.get(
            f"{_BACKEND_PRINCIPAL}/api/v1/vila-inteia/constituicao/artigos",
            timeout=15.0,
        )
        return resp.json()
    except Exception:
        return []
