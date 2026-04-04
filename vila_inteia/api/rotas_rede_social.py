"""
API da Rede Social INTEIA.

Endpoints para interação com o feed social dos consultores.
"""

from __future__ import annotations
import asyncio

from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from .rotas_vila import obter_simulacao
from ..engine.rede_social import RedeSocial
from ..engine.gatilhos import MotorGatilhos


# ============================================================
# ESTADO (usa instância da simulação para compartilhar estado)
# ============================================================

def obter_rede() -> RedeSocial:
    """Retorna a rede social da simulação ativa."""
    sim = obter_simulacao()
    return sim.rede_social


def obter_motor_gatilhos() -> MotorGatilhos:
    """Retorna o motor de gatilhos da simulação ativa."""
    sim = obter_simulacao()
    return sim.motor_gatilhos


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
    Gatilho 1 — Usuário injeta tema (prioridade máxima).

    Publica o tema e gera 3-4 comentários IA imediatos dos
    consultores mais relevantes. Restantes entram na fila de waves
    (10min, 30min, 1h+) para criar sensação de feed vivo.
    """
    sim = obter_simulacao()
    motor = obter_motor_gatilhos()

    # Motor de Gatilhos cuida de tudo: post + comentários IA imediatos + waves
    post = motor.injetar_tema(
        titulo=req.titulo,
        conteudo=req.conteudo or req.titulo,
        tags=req.tags or None,
        personas=sim.personas,
        step=sim.step,
    )

    return {
        "post": post.to_dict(),
        "interacoes_imediatas": len(post.comentarios),
        "waves_pendentes": len(motor.fila_waves),
        "mensagem": (
            f"Tema publicado! {len(post.comentarios)} consultores reagiram "
            f"imediatamente. Mais comentários chegarão nas próximas waves."
        ),
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


# ============================================================
# ENDPOINTS DO MOTOR DE GATILHOS
# ============================================================

class DebateRequest(BaseModel):
    """Força debate entre dois consultores específicos."""
    agente_a: str | None = None  # Se None, seleciona par rival aleatório
    agente_b: str | None = None
    tema: str = ""


@router.post("/debate")
async def forcar_debate(req: DebateRequest):
    """
    Gatilho 5 — Força debate entre par rival.

    Se agente_a e agente_b forem fornecidos, debate entre eles.
    Se não, seleciona par rival aleatório (Musk vs Zuckerberg, Jesus vs Diabob, etc).
    """
    sim = obter_simulacao()
    motor = obter_motor_gatilhos()

    from ..engine.gatilhos import MotorDebate

    if req.agente_a and req.agente_b:
        persona_a = sim.personas.get(req.agente_a)
        persona_b = sim.personas.get(req.agente_b)
        if not persona_a or not persona_b:
            raise HTTPException(404, "Agente não encontrado")
        tema_contexto = req.tema or "debate livre"
    else:
        par = MotorDebate.selecionar_par(sim.personas)
        if not par:
            raise HTTPException(400, "Nenhum par rival disponível")
        persona_a, persona_b, tema_contexto, _ = par

    debate = MotorDebate.executar_debate_ia(
        persona_a, persona_b, tema_contexto, n_turnos=8
    )

    if not debate:
        raise HTTPException(500, "Falha ao gerar debate")

    # Publicar no feed
    from ..engine.rede_social import Postagem
    post = Postagem(
        tipo="debate",
        autor_id=persona_a.id,
        autor_nome=f"{persona_a.nome_exibicao} vs {persona_b.nome_exibicao}",
        autor_titulo="Debate Lendário",
        autor_categoria="debate",
        titulo=debate["titulo"],
        conteudo=debate["conteudo"],
        tags=debate["tags"],
        destaque=True,
    )
    r = obter_rede()
    r._adicionar_post(post)

    return {
        "post": post.to_dict(),
        "participantes": [persona_a.nome_exibicao, persona_b.nome_exibicao],
        "tema": tema_contexto,
    }


@router.post("/provocar")
async def forcar_provocacao():
    """
    Gatilho 6 — Diabob provoca o feed.

    Diabob analisa os últimos posts e lança uma provocação devastadora.
    Se Jesus estiver ativo, responde automaticamente com serenidade.
    """
    sim = obter_simulacao()
    motor = obter_motor_gatilhos()

    resultado = motor._gatilho_diabob(sim.step, sim.personas)
    if not resultado:
        raise HTTPException(400, "Diabob não está disponível ou falha na geração")

    r = obter_rede()
    post = r._indice_por_id.get(resultado["post_id"])

    return {
        "post": post.to_dict() if post else None,
        "evento": resultado,
    }


@router.post("/parabola")
async def forcar_parabola():
    """
    Gatilho 6 — Jesus Cristo posta uma parábola.

    Gera parábola inspirada no contexto atual do feed.
    """
    sim = obter_simulacao()
    motor = obter_motor_gatilhos()

    resultado = motor._gatilho_jesus(sim.step)
    if not resultado:
        raise HTTPException(400, "Jesus não está disponível ou falha na geração")

    r = obter_rede()
    post = r._indice_por_id.get(resultado["post_id"])

    return {
        "post": post.to_dict() if post else None,
        "evento": resultado,
    }


@router.post("/helena-sintese")
async def forcar_sintese():
    """
    Helena gera síntese dos debates mais relevantes.

    Analisa os posts mais engajados e extrai padrões, insights e pontos cegos.
    """
    sim = obter_simulacao()
    motor = obter_motor_gatilhos()

    resultado = await asyncio.to_thread(motor._gatilho_helena_sintese, sim.step)
    if not resultado:
        raise HTTPException(400, "Helena não disponível ou poucos posts para sintetizar")

    r = obter_rede()
    post = r._indice_por_id.get(resultado["post_id"])

    return {
        "post": post.to_dict() if post else None,
        "evento": resultado,
    }


@router.get("/gatilhos/status")
async def status_gatilhos():
    """Status do Motor de Gatilhos — cadência e contadores."""
    sim = obter_simulacao()
    motor = obter_motor_gatilhos()

    return {
        "step_atual": sim.step,
        "hora_simulacao": sim.hora_atual.strftime("%Y-%m-%d %H:%M"),
        "posts_hoje": motor.posts_hoje,
        "waves_pendentes": len(motor.fila_waves),
        "cadencia": {
            "ultimo_debate": motor.ultimo_debate_step,
            "proximo_debate": motor.ultimo_debate_step + 20,
            "ultimo_diabob": motor.ultimo_diabob_step,
            "proximo_diabob": motor.ultimo_diabob_step + 15,
            "ultimo_jesus": motor.ultimo_jesus_step,
            "ultimo_helena": motor.ultimo_helena_step,
            "ultima_sintese": motor.ultimo_sintese_step,
        },
        "personagens_especiais": {
            "diabob": motor._diabob.nome_exibicao if motor._diabob else "não encontrado",
            "jesus": motor._jesus.nome_exibicao if motor._jesus else "não encontrado",
            "helena": motor._helena.nome_exibicao if motor._helena else "não encontrado",
            "sun_tzu": motor._sun_tzu.nome_exibicao if motor._sun_tzu else "não encontrado",
        },
    }
