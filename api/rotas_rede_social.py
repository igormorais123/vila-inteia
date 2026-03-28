"""
API da Rede Social INTEIA.

Endpoints para interação com o feed social dos consultores.
"""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from .rotas_vila import obter_simulacao
from ..engine.rede_social import RedeSocial


# ============================================================
# ESTADO
# ============================================================

rede: Optional[RedeSocial] = None


def obter_rede() -> RedeSocial:
    global rede
    if rede is None:
        rede = RedeSocial()
    return rede


# ============================================================
# ROUTER
# ============================================================

router = APIRouter(prefix="/api/v1/rede", tags=["Rede Social INTEIA"])


# --- Request Models ---

class PostTemaRequest(BaseModel):
    titulo: str
    conteudo: str = ""
    tags: list[str] = []


class PostEventoRequest(BaseModel):
    titulo: str
    conteudo: str
    tags: list[str] = []


class ComentarioRequest(BaseModel):
    conteudo: str
    em_resposta_a: str | None = None


class ReacaoRequest(BaseModel):
    tipo: str = "concordo"  # concordo, discordo, brilhante, provocador, inspirador


# ============================================================
# ENDPOINTS DO FEED
# ============================================================

@router.get("/feed")
async def obter_feed(
    limite: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    tipo: Optional[str] = None,
    tag: Optional[str] = None,
    autor_id: Optional[str] = None,
    ordenar_por: str = Query("recente", regex="^(recente|engajamento|comentarios)$"),
):
    """Retorna o feed social."""
    r = obter_rede()
    posts = r.feed(
        limite=limite, offset=offset,
        tipo=tipo, tag=tag, autor_id=autor_id,
        ordenar_por=ordenar_por,
    )
    return {
        "total": r.total_posts,
        "posts": posts,
    }


@router.get("/post/{post_id}")
async def obter_post(post_id: str):
    """Retorna um post com todos os comentários."""
    r = obter_rede()
    post = r.obter_post(post_id)
    if not post:
        raise HTTPException(404, "Post não encontrado")
    return post


@router.get("/trending")
async def trending():
    """Tags em alta."""
    r = obter_rede()
    return {"trending": r.trending_tags(10)}


@router.get("/stats")
async def stats_rede():
    """Estatísticas da rede social."""
    r = obter_rede()
    return r.stats()


# ============================================================
# ENDPOINTS DE INTERAÇÃO
# ============================================================

@router.post("/tema")
async def publicar_tema(req: PostTemaRequest):
    """
    Usuário publica um tema para os consultores discutirem.
    Automaticamente distribui para consultores reagirem.
    """
    r = obter_rede()
    sim = obter_simulacao()

    post = r.publicar_tema_usuario(
        titulo=req.titulo,
        conteudo=req.conteudo or req.titulo,
        tags=req.tags or None,
        hora_atual=sim.hora_atual,
    )

    # Processar reações imediatas dos consultores
    interacoes = r.processar_reacoes(sim.personas, sim.hora_atual, max_reacoes_por_step=10)

    return {
        "post": post.to_dict(),
        "interacoes_imediatas": interacoes,
        "mensagem": f"Tema publicado! {len(interacoes)} consultores reagiram.",
    }


@router.post("/evento")
async def publicar_evento(req: PostEventoRequest):
    """Publica evento/notícia para os consultores reagirem."""
    r = obter_rede()
    sim = obter_simulacao()

    post = r.publicar_evento(
        titulo=req.titulo,
        conteudo=req.conteudo,
        tags=req.tags or None,
        hora_atual=sim.hora_atual,
    )

    interacoes = r.processar_reacoes(sim.personas, sim.hora_atual, max_reacoes_por_step=8)

    return {
        "post": post.to_dict(),
        "interacoes": interacoes,
    }


@router.post("/post/{post_id}/comentar/{agente_id}")
async def forcar_comentario(post_id: str, agente_id: str, req: ComentarioRequest):
    """Força um consultor específico a comentar em um post."""
    r = obter_rede()
    sim = obter_simulacao()

    persona = sim.personas.get(agente_id)
    if not persona:
        raise HTTPException(404, f"Agente {agente_id} não encontrado")

    comentario = r.comentar(
        post_id=post_id,
        persona=persona,
        conteudo=req.conteudo,
        em_resposta_a=req.em_resposta_a,
        hora_atual=sim.hora_atual,
    )

    if not comentario:
        raise HTTPException(404, "Post não encontrado")

    return comentario.to_dict()


@router.post("/post/{post_id}/reagir/{agente_id}")
async def forcar_reacao(post_id: str, agente_id: str, req: ReacaoRequest):
    """Força um consultor a reagir a um post."""
    r = obter_rede()
    sim = obter_simulacao()

    persona = sim.personas.get(agente_id)
    if not persona:
        raise HTTPException(404, f"Agente {agente_id} não encontrado")

    sucesso = r.reagir(post_id, persona, req.tipo)
    if not sucesso:
        raise HTTPException(400, "Não foi possível reagir (post não encontrado ou já reagiu)")

    return {"status": "ok", "tipo": req.tipo}


@router.post("/processar")
async def processar_reacoes(max_reacoes: int = Query(15, ge=1, le=50)):
    """Processa reações pendentes na fila."""
    r = obter_rede()
    sim = obter_simulacao()
    interacoes = r.processar_reacoes(sim.personas, sim.hora_atual, max_reacoes)
    return {
        "interacoes": interacoes,
        "total": len(interacoes),
    }


@router.post("/gerar-posts")
async def gerar_posts_autonomos(chance: float = Query(0.05, ge=0.01, le=0.5)):
    """Gera posts autônomos dos consultores."""
    r = obter_rede()
    sim = obter_simulacao()
    novos = r.gerar_posts_autonomos(sim.personas, sim.hora_atual, chance)
    return {
        "novos_posts": [p.to_dict() for p in novos],
        "total": len(novos),
    }


@router.post("/destaque/{post_id}")
async def alternar_destaque(post_id: str):
    """Alterna destaque de um post."""
    r = obter_rede()
    post = r._indice_por_id.get(post_id)
    if not post:
        raise HTTPException(404, "Post não encontrado")
    post.destaque = not post.destaque
    return {"destaque": post.destaque}
