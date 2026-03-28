"""
Rede Social INTEIA - O coração da Vila.

Feed social onde 144 consultores lendários postam, comentam,
debatem e reagem a temas — tanto injetados pelo usuário quanto
gerados autonomamente pelos próprios consultores.

Estrutura:
    Postagem (post principal)
    ├── Comentários (reações de outros consultores)
    ├── Reações (concordo, discordo, brilhante, provocador)
    └── Debate (thread estruturada pró vs contra)
"""

from __future__ import annotations

import json
import os
import random
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional, Any

from .persona import Persona


# ============================================================
# MODELOS
# ============================================================

@dataclass
class Reacao:
    """Reação a um post ou comentário."""
    agente_id: str
    agente_nome: str
    tipo: str  # "concordo", "discordo", "brilhante", "provocador", "inspirador"
    criado_em: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> dict:
        return {
            "agente_id": self.agente_id,
            "agente_nome": self.agente_nome,
            "tipo": self.tipo,
            "criado_em": self.criado_em.isoformat(),
        }


@dataclass
class Comentario:
    """Comentário de um consultor em um post."""
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:12])
    agente_id: str = ""
    agente_nome: str = ""
    agente_titulo: str = ""
    agente_categoria: str = ""
    agente_tier: str = "A"
    conteudo: str = ""
    criado_em: datetime = field(default_factory=datetime.now)
    reacoes: list[Reacao] = field(default_factory=list)
    em_resposta_a: Optional[str] = None  # ID de outro comentário (thread)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "agente_id": self.agente_id,
            "agente_nome": self.agente_nome,
            "agente_titulo": self.agente_titulo,
            "agente_categoria": self.agente_categoria,
            "agente_tier": self.agente_tier,
            "conteudo": self.conteudo,
            "criado_em": self.criado_em.isoformat(),
            "reacoes": [r.to_dict() for r in self.reacoes],
            "total_reacoes": len(self.reacoes),
            "em_resposta_a": self.em_resposta_a,
        }


@dataclass
class Postagem:
    """Post principal no feed — pode ser do usuário ou de um consultor."""
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:12])
    tipo: str = "tema"  # "tema" (usuario), "opiniao" (consultor), "evento" (sistema), "debate"
    autor_id: str = ""  # "usuario" ou ID do consultor
    autor_nome: str = ""
    autor_titulo: str = ""
    autor_categoria: str = ""
    autor_tier: str = ""
    titulo: str = ""
    conteudo: str = ""
    tags: list[str] = field(default_factory=list)
    criado_em: datetime = field(default_factory=datetime.now)
    comentarios: list[Comentario] = field(default_factory=list)
    reacoes: list[Reacao] = field(default_factory=list)
    destaque: bool = False  # Post marcado como destaque pelo usuário
    fixado: bool = False  # Post fixado no topo

    # Metadados de engajamento
    total_visualizacoes: int = 0

    @property
    def total_comentarios(self) -> int:
        return len(self.comentarios)

    @property
    def total_reacoes(self) -> int:
        return len(self.reacoes)

    @property
    def engajamento(self) -> float:
        """Score de engajamento (para ranking)."""
        return (
            self.total_comentarios * 3
            + self.total_reacoes * 1
            + (10 if self.destaque else 0)
            + (5 if self.fixado else 0)
        )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "tipo": self.tipo,
            "autor_id": self.autor_id,
            "autor_nome": self.autor_nome,
            "autor_titulo": self.autor_titulo,
            "autor_categoria": self.autor_categoria,
            "autor_tier": self.autor_tier,
            "titulo": self.titulo,
            "conteudo": self.conteudo,
            "tags": self.tags,
            "criado_em": self.criado_em.isoformat(),
            "comentarios": [c.to_dict() for c in self.comentarios],
            "reacoes": [r.to_dict() for r in self.reacoes],
            "destaque": self.destaque,
            "fixado": self.fixado,
            "total_comentarios": self.total_comentarios,
            "total_reacoes": self.total_reacoes,
            "engajamento": self.engajamento,
        }


# ============================================================
# MOTOR DA REDE SOCIAL
# ============================================================

class RedeSocial:
    """
    Motor da rede social dos consultores lendários.

    Responsabilidades:
    - Receber temas do usuário e distribuir para consultores
    - Gerar posts autônomos dos consultores
    - Gerenciar comentários e debates
    - Ranquear e organizar o feed
    - Gerar sínteses de debates
    """

    def __init__(self):
        self.postagens: list[Postagem] = []
        self.fila_processamento: list[dict] = []  # Posts aguardando reações
        self._indice_por_id: dict[str, Postagem] = {}

        # Stats
        self.total_posts: int = 0
        self.total_comentarios: int = 0
        self.total_reacoes: int = 0

    def publicar_tema_usuario(
        self,
        titulo: str,
        conteudo: str = "",
        tags: list[str] | None = None,
        hora_atual: datetime | None = None,
    ) -> Postagem:
        """
        Usuário publica um tema para os consultores discutirem.
        """
        post = Postagem(
            tipo="tema",
            autor_id="usuario",
            autor_nome="Você",
            autor_titulo="Pesquisador",
            titulo=titulo,
            conteudo=conteudo or titulo,
            tags=tags or _extrair_tags(titulo),
            criado_em=hora_atual or datetime.now(),
            fixado=True,
        )

        self._adicionar_post(post)

        # Agendar para consultores reagirem
        self.fila_processamento.append({
            "post_id": post.id,
            "tipo": "tema_usuario",
            "prioridade": 10,
        })

        return post

    def publicar_opiniao_consultor(
        self,
        persona: Persona,
        conteudo: str,
        titulo: str = "",
        tags: list[str] | None = None,
        hora_atual: datetime | None = None,
    ) -> Postagem:
        """
        Consultor publica uma opinião/observação espontânea.
        """
        post = Postagem(
            tipo="opiniao",
            autor_id=persona.id,
            autor_nome=persona.nome_exibicao,
            autor_titulo=persona.titulo,
            autor_categoria=persona.categoria,
            autor_tier=persona.tier,
            titulo=titulo or conteudo[:60],
            conteudo=conteudo,
            tags=tags or _extrair_tags(conteudo),
            criado_em=hora_atual or datetime.now(),
        )

        self._adicionar_post(post)

        # Agendar reações de outros
        self.fila_processamento.append({
            "post_id": post.id,
            "tipo": "opiniao_consultor",
            "prioridade": 5,
        })

        return post

    def publicar_evento(
        self,
        titulo: str,
        conteudo: str,
        tags: list[str] | None = None,
        hora_atual: datetime | None = None,
    ) -> Postagem:
        """
        Sistema publica evento/notícia para consultores reagirem.
        """
        post = Postagem(
            tipo="evento",
            autor_id="sistema",
            autor_nome="INTEIA News",
            autor_titulo="Sistema de Inteligência",
            titulo=titulo,
            conteudo=conteudo,
            tags=tags or _extrair_tags(titulo + " " + conteudo),
            criado_em=hora_atual or datetime.now(),
        )

        self._adicionar_post(post)

        self.fila_processamento.append({
            "post_id": post.id,
            "tipo": "evento",
            "prioridade": 8,
        })

        return post

    def comentar(
        self,
        post_id: str,
        persona: Persona,
        conteudo: str,
        em_resposta_a: str | None = None,
        hora_atual: datetime | None = None,
    ) -> Comentario | None:
        """
        Consultor comenta em um post.
        """
        post = self._indice_por_id.get(post_id)
        if not post:
            return None

        comentario = Comentario(
            agente_id=persona.id,
            agente_nome=persona.nome_exibicao,
            agente_titulo=persona.titulo,
            agente_categoria=persona.categoria,
            agente_tier=persona.tier,
            conteudo=conteudo,
            criado_em=hora_atual or datetime.now(),
            em_resposta_a=em_resposta_a,
        )

        post.comentarios.append(comentario)
        self.total_comentarios += 1

        return comentario

    def reagir(
        self,
        post_id: str,
        persona: Persona,
        tipo: str = "concordo",
    ) -> bool:
        """Consultor reage a um post."""
        post = self._indice_por_id.get(post_id)
        if not post:
            return False

        # Evitar reação duplicada
        if any(r.agente_id == persona.id for r in post.reacoes):
            return False

        post.reacoes.append(Reacao(
            agente_id=persona.id,
            agente_nome=persona.nome_exibicao,
            tipo=tipo,
        ))
        self.total_reacoes += 1
        return True

    def processar_reacoes(
        self,
        personas: dict[str, Persona],
        hora_atual: datetime,
        max_reacoes_por_step: int = 15,
    ) -> list[dict]:
        """
        Processa a fila: consultores reagem aos posts pendentes.

        Retorna lista de novas interações geradas.
        """
        interacoes = []
        processados = 0

        while self.fila_processamento and processados < max_reacoes_por_step:
            item = self.fila_processamento.pop(0)
            post = self._indice_por_id.get(item["post_id"])
            if not post:
                continue

            # Selecionar consultores que devem reagir
            reagentes = _selecionar_reagentes(post, personas, max_n=8)

            for persona in reagentes:
                if processados >= max_reacoes_por_step:
                    break

                # Decidir: comentar ou reagir?
                vai_comentar = _deve_comentar(persona, post)

                if vai_comentar:
                    conteudo = _gerar_comentario_ia(persona, post)
                    if not conteudo:
                        conteudo = _gerar_comentario_heuristico(persona, post)
                    comentario = self.comentar(
                        post.id, persona, conteudo, hora_atual=hora_atual
                    )
                    if comentario:
                        interacoes.append({
                            "tipo": "comentario",
                            "post_id": post.id,
                            "agente_nome": persona.nome_exibicao,
                            "conteudo": conteudo,
                        })
                else:
                    tipo_reacao = _escolher_tipo_reacao(persona, post)
                    if self.reagir(post.id, persona, tipo_reacao):
                        interacoes.append({
                            "tipo": "reacao",
                            "post_id": post.id,
                            "agente_nome": persona.nome_exibicao,
                            "reacao": tipo_reacao,
                        })

                processados += 1

        return interacoes

    def gerar_posts_autonomos(
        self,
        personas: dict[str, Persona],
        hora_atual: datetime,
        chance: float = 0.05,
    ) -> list[Postagem]:
        """
        Consultores geram posts espontâneos baseados em suas reflexões.
        """
        novos_posts = []

        for persona in personas.values():
            if not persona.ativo:
                continue
            if random.random() > chance:
                continue

            # Gerar post: tenta IA, fallback heurístico
            post_conteudo = _gerar_post_autonomo_ia(persona)
            if not post_conteudo:
                post_conteudo = _gerar_post_autonomo(persona)
            if post_conteudo:
                post = self.publicar_opiniao_consultor(
                    persona=persona,
                    conteudo=post_conteudo["conteudo"],
                    titulo=post_conteudo["titulo"],
                    tags=post_conteudo.get("tags", []),
                    hora_atual=hora_atual,
                )
                novos_posts.append(post)

        return novos_posts

    # ================================================================
    # FEED E CONSULTAS
    # ================================================================

    def feed(
        self,
        limite: int = 20,
        offset: int = 0,
        tipo: str | None = None,
        tag: str | None = None,
        autor_id: str | None = None,
        ordenar_por: str = "recente",  # "recente", "engajamento", "comentarios"
    ) -> list[dict]:
        """Retorna o feed formatado."""
        posts = list(self.postagens)

        # Filtros
        if tipo:
            posts = [p for p in posts if p.tipo == tipo]
        if tag:
            posts = [p for p in posts if tag.lower() in [t.lower() for t in p.tags]]
        if autor_id:
            posts = [p for p in posts if p.autor_id == autor_id]

        # Ordenação
        if ordenar_por == "engajamento":
            posts.sort(key=lambda p: p.engajamento, reverse=True)
        elif ordenar_por == "comentarios":
            posts.sort(key=lambda p: p.total_comentarios, reverse=True)
        else:
            posts.sort(key=lambda p: p.criado_em, reverse=True)

        # Fixados sempre no topo
        fixados = [p for p in posts if p.fixado]
        nao_fixados = [p for p in posts if not p.fixado]
        posts = fixados + nao_fixados

        # Paginação
        posts = posts[offset:offset + limite]

        return [p.to_dict() for p in posts]

    def obter_post(self, post_id: str) -> dict | None:
        """Retorna um post completo com todos os comentários."""
        post = self._indice_por_id.get(post_id)
        if not post:
            return None
        post.total_visualizacoes += 1
        return post.to_dict()

    def trending_tags(self, n: int = 10) -> list[dict]:
        """Tags mais usadas recentemente."""
        contagem: dict[str, int] = {}
        for post in self.postagens[-100:]:
            for tag in post.tags:
                contagem[tag] = contagem.get(tag, 0) + 1

        ordenadas = sorted(contagem.items(), key=lambda x: x[1], reverse=True)
        return [{"tag": t, "contagem": c} for t, c in ordenadas[:n]]

    def stats(self) -> dict:
        """Estatísticas da rede social."""
        autores = set()
        for p in self.postagens:
            autores.add(p.autor_id)
            for c in p.comentarios:
                autores.add(c.agente_id)

        return {
            "total_posts": self.total_posts,
            "total_comentarios": self.total_comentarios,
            "total_reacoes": self.total_reacoes,
            "autores_unicos": len(autores),
            "posts_usuario": sum(1 for p in self.postagens if p.tipo == "tema"),
            "posts_consultores": sum(1 for p in self.postagens if p.tipo == "opiniao"),
            "posts_eventos": sum(1 for p in self.postagens if p.tipo == "evento"),
            "trending": self.trending_tags(5),
        }

    # ================================================================
    # INTERNOS
    # ================================================================

    def _adicionar_post(self, post: Postagem):
        self.postagens.append(post)
        self._indice_por_id[post.id] = post
        self.total_posts += 1

    def salvar(self, caminho: str):
        """Persiste feed em JSON."""
        dados = {
            "total_posts": self.total_posts,
            "total_comentarios": self.total_comentarios,
            "total_reacoes": self.total_reacoes,
            "postagens": [p.to_dict() for p in self.postagens],
        }
        with open(caminho, "w", encoding="utf-8") as f:
            json.dump(dados, f, ensure_ascii=False, indent=2)


# ============================================================
# FUNÇÕES AUXILIARES
# ============================================================

def _extrair_tags(texto: str) -> list[str]:
    """Extrai tags relevantes de um texto."""
    # Palavras-chave comuns em temas estratégicos
    keywords = {
        "ia": "IA", "inteligencia artificial": "IA",
        "eleicao": "eleicoes", "eleicoes": "eleicoes", "voto": "eleicoes",
        "economia": "economia", "pib": "economia", "inflacao": "economia",
        "tecnologia": "tecnologia", "tech": "tecnologia",
        "politica": "politica", "governo": "politica",
        "brasil": "brasil", "brasilia": "brasil",
        "estrategia": "estrategia", "negocio": "negocios",
        "lideranca": "lideranca", "gestao": "gestao",
        "inovacao": "inovacao", "futuro": "futuro",
        "educacao": "educacao", "saude": "saude",
        "direito": "direito", "justica": "justica",
        "seguranca": "seguranca", "defesa": "defesa",
        "clima": "meio-ambiente", "sustentabilidade": "meio-ambiente",
        "cripto": "cripto", "blockchain": "cripto", "bitcoin": "cripto",
    }

    texto_lower = texto.lower()
    tags = set()
    for palavra, tag in keywords.items():
        if palavra in texto_lower:
            tags.add(tag)

    return list(tags)[:5]


def _selecionar_reagentes(
    post: Postagem,
    personas: dict[str, Persona],
    max_n: int = 8,
) -> list[Persona]:
    """
    Seleciona quais consultores devem reagir a um post.

    Prioriza:
    1. Consultores com expertise nas tags do post
    2. Tier S antes de Tier A
    3. Consultores com alta extroversão
    4. Diversidade de categorias
    """
    candidatos = []

    for persona in personas.values():
        if not persona.ativo:
            continue
        if persona.id == post.autor_id:
            continue
        # Já comentou?
        if any(c.agente_id == persona.id for c in post.comentarios):
            continue

        # Score de relevância
        score = 0.0

        # Tags match expertise
        tags_lower = {t.lower() for t in post.tags}
        expertise_lower = {e.lower() for e in persona.rascunho.areas_expertise}
        overlap = len(tags_lower & expertise_lower)
        score += overlap * 3

        # Palavras do post no expertise
        palavras_post = set(post.conteudo.lower().split())
        overlap_palavras = len(palavras_post & expertise_lower)
        score += overlap_palavras * 2

        # Tier boost
        if persona.tier == "S":
            score += 2
        elif persona.tier == "A":
            score += 1

        # Extroversão
        score += persona.rascunho.nivel_extroversao * 0.2

        # Agressividade (mais opiniões)
        score += persona.rascunho.nivel_agressividade * 0.1

        # Categoria relacionada ao tipo de post
        if post.tipo == "tema" and persona.categoria in (
            "estrategia", "influencia_oratoria", "visionario"
        ):
            score += 1.5
        if post.tipo == "evento" and persona.categoria in (
            "politica_brasileira", "politica_internacional", "estrategia"
        ):
            score += 1.5

        candidatos.append((persona, score))

    # Ordenar por score
    candidatos.sort(key=lambda x: x[1], reverse=True)

    # Garantir diversidade de categorias
    selecionados = []
    categorias_vistas = set()
    for persona, score in candidatos:
        if len(selecionados) >= max_n:
            break
        if persona.categoria in categorias_vistas and len(selecionados) > max_n // 2:
            continue
        selecionados.append(persona)
        categorias_vistas.add(persona.categoria)

    return selecionados


def _deve_comentar(persona: Persona, post: Postagem) -> bool:
    """Decide se o consultor vai comentar (vs apenas reagir)."""
    # Consultores mais expressivos comentam mais
    chance = 0.3
    chance += persona.rascunho.nivel_extroversao * 0.04
    chance += persona.rascunho.nivel_agressividade * 0.03

    # Tier S comenta mais
    if persona.tier == "S":
        chance += 0.15

    # Posts do usuário recebem mais comentários
    if post.tipo == "tema":
        chance += 0.2

    # Posts com poucos comentários recebem mais
    if post.total_comentarios < 3:
        chance += 0.15

    return random.random() < chance


def _escolher_tipo_reacao(persona: Persona, post: Postagem) -> str:
    """Escolhe o tipo de reação baseado na personalidade."""
    # Pesos por personalidade
    if persona.rascunho.nivel_empatia > 7:
        pesos = {"concordo": 4, "brilhante": 3, "inspirador": 3, "provocador": 1, "discordo": 1}
    elif persona.rascunho.nivel_agressividade > 7:
        pesos = {"discordo": 4, "provocador": 3, "concordo": 2, "brilhante": 1, "inspirador": 1}
    elif persona.categoria in ("qi_extremo", "estrategia"):
        pesos = {"brilhante": 3, "concordo": 2, "provocador": 2, "discordo": 2, "inspirador": 1}
    else:
        pesos = {"concordo": 3, "brilhante": 2, "inspirador": 2, "provocador": 1, "discordo": 1}

    tipos = list(pesos.keys())
    weights = list(pesos.values())
    return random.choices(tipos, weights=weights, k=1)[0]


def _gerar_comentario_ia(persona: Persona, post: Postagem) -> str | None:
    """
    Gera comentário via LLM (Haiku 4.5). Retorna None se falhar.
    """
    from .ia_client import chamar_llm_conversa, MODELO_RAPIDO

    d = persona.dados_consultor
    tom = d.get("tom_voz", "direto")
    estilo = d.get("estilo_argumentacao", "analítico")
    expertise = ", ".join(persona.rascunho.areas_expertise[:4])
    frase = d.get("frase_chave", "")

    # Contexto dos comentários anteriores (compacto)
    anteriores = ""
    if post.comentarios:
        anteriores = "\n".join(
            f"- {c.agente_nome}: {c.conteudo[:80]}"
            for c in post.comentarios[-3:]
        )

    system = f"""Você é {persona.nome_exibicao}, "{persona.titulo}".
Tom: {tom}. Estilo: {estilo}. Expertise: {expertise}.
Frase marcante: "{frase}"
Escreva UM comentário (2-3 frases) no SEU estilo único.
Seja específico e opinionado, nunca genérico. Português do Brasil."""

    user = f"""POST de {post.autor_nome}:
"{post.titulo}"
{post.conteudo[:200]}

{f'Comentários anteriores:{chr(10)}{anteriores}' if anteriores else ''}

Comente como {persona.nome_exibicao} comentaria."""

    return chamar_llm_conversa(system, user, modelo=MODELO_RAPIDO, max_tokens=150)


def _gerar_post_autonomo_ia(persona: Persona) -> dict | None:
    """Gera post autônomo via LLM. Retorna dict com titulo/conteudo/tags ou None."""
    from .ia_client import chamar_llm_conversa, MODELO_RAPIDO

    d = persona.dados_consultor
    expertise = persona.rascunho.areas_expertise
    if not expertise:
        return None

    area = expertise[0] if expertise else "estratégia"
    tom = d.get("tom_voz", "direto")
    frase = d.get("frase_chave", "")

    system = f"""Você é {persona.nome_exibicao}, "{persona.titulo}".
Tom: {tom}. Frase: "{frase}".
Escreva um post curto (3-5 frases) para uma rede social de think tank.
Responda APENAS o texto do post, sem título, sem hashtags.
Português do Brasil. Seja autêntico ao seu estilo."""

    user = f"Escreva sobre {area} — algo que está te intrigando ou provocando hoje."

    texto = chamar_llm_conversa(system, user, modelo=MODELO_RAPIDO, max_tokens=200)
    if not texto:
        return None

    return {
        "titulo": f"Reflexão sobre {area}",
        "conteudo": texto,
        "tags": [area.lower().replace(" ", "-")],
    }


def _gerar_comentario_heuristico(persona: Persona, post: Postagem) -> str:
    """
    Gera comentário heurístico baseado no perfil do consultor.

    Sem LLM — usa templates e personalidade para criar comentários
    autênticos. Será substituído por LLM via OmniRoute.
    """
    d = persona.dados_consultor
    nome = persona.nome_exibicao
    tom = d.get("tom_voz", "neutro")
    estilo_arg = d.get("estilo_argumentacao", "analítico")

    # Expressões típicas
    expressoes = d.get("expressoes_tipicas", [])
    if isinstance(expressoes, str):
        expressoes = [e.strip() for e in expressoes.split(";") if e.strip()]

    frases_celebres = d.get("frases_celebres", [])
    if isinstance(frases_celebres, str):
        frases_celebres = [f.strip() for f in frases_celebres.split(";") if f.strip()]

    frase_chave = d.get("frase_chave", "")
    visao_futuro = d.get("visao_futuro", "pragmática")
    frameworks = d.get("frameworks_mentais", "")
    if isinstance(frameworks, list):
        frameworks = ", ".join(frameworks[:2])

    # Templates por estilo de argumentação
    templates = {
        "analítico": [
            f"Analisando pela perspectiva de {frameworks or 'análise sistemática'}, "
            f"vejo três pontos críticos aqui que merecem atenção.",
            f"Os dados sugerem uma conclusão diferente. Precisamos separar "
            f"correlação de causalidade antes de avançar.",
            f"Minha análise indica que o verdadeiro driver aqui não é o óbvio. "
            f"Olhem para as variáveis de segunda ordem.",
        ],
        "socrático": [
            f"Antes de responder, preciso fazer a pergunta certa: "
            f"o que estamos realmente tentando resolver aqui?",
            f"Questiono a premissa fundamental. Se invertermos a lógica, "
            f"a conclusão se mantém?",
            f"A verdadeira sabedoria começa admitindo o que não sabemos. "
            f"Quantas suposições não-testadas estão nessa análise?",
        ],
        "provocativo": [
            f"Discordo de tudo que foi dito até agora. "
            f"A premissa está errada desde o início.",
            f"Vocês estão pensando pequeno demais. O problema real é "
            f"dez vezes maior do que parece.",
            f"Isso é pensamento convencional disfarçado de inovação. "
            f"Precisamos quebrar o paradigma completamente.",
        ],
        "pragmático": [
            f"Teoria é bonita, mas vamos ao que interessa: "
            f"qual é o próximo passo concreto?",
            f"Na prática, implementei algo similar. O que ninguém te conta "
            f"são os detalhes de execução.",
            f"Menos filosofia, mais ação. Quem vai fazer o quê até quando?",
        ],
        "visionário": [
            f"Pensem 10 anos à frente. O que estamos discutindo hoje "
            f"será irrelevante. A questão real é...",
            f"O futuro já está aqui, só não está distribuído igualmente. "
            f"Deixem-me mostrar o que estou vendo.",
            f"Estamos resolvendo o problema errado. A verdadeira oportunidade "
            f"está onde ninguém está olhando.",
        ],
    }

    # Escolher template baseado no estilo
    estilo_key = "analítico"
    for key in templates:
        if key in estilo_arg.lower():
            estilo_key = key
            break

    comentario = random.choice(templates.get(estilo_key, templates["analítico"]))

    # Adicionar expressão típica se disponível
    if expressoes and random.random() > 0.5:
        expr = random.choice(expressoes[:3])
        comentario = f"\"{expr}\" — {comentario}"
    elif frases_celebres and random.random() > 0.6:
        frase = random.choice(frases_celebres[:3])
        comentario = f"{comentario} Como já disse: \"{frase}\""

    return comentario


def _gerar_post_autonomo(persona: Persona) -> dict | None:
    """
    Gera conteúdo de post autônomo baseado no perfil do consultor.

    Consultores postam sobre:
    - Suas áreas de expertise
    - Reflexões sobre o mundo
    - Provocações intelectuais
    - Insights de suas experiências
    """
    d = persona.dados_consultor
    nome = persona.nome_exibicao

    expertise = persona.rascunho.areas_expertise
    if not expertise:
        return None

    area = random.choice(expertise[:3])

    # Templates de posts autônomos
    conceitos = d.get("conceitos_criados", [])
    if isinstance(conceitos, str):
        conceitos = [c.strip() for c in conceitos.split(",") if c.strip()]

    visao_futuro = d.get("visao_futuro", "")
    maior_conquista = d.get("maior_conquista", "")
    momento_definidor = d.get("momento_definidor", "")

    templates = [
        {
            "titulo": f"Reflexão sobre {area}",
            "conteudo": (
                f"Tenho pensado muito sobre {area} ultimamente. "
                f"Na minha experiência como {persona.titulo}, "
                f"percebo que a maioria comete o mesmo erro: "
                f"confundir atividade com progresso."
            ),
            "tags": [area.lower().replace(" ", "-")],
        },
        {
            "titulo": f"O futuro de {area}",
            "conteudo": (
                f"Minha visão: {visao_futuro or f'{area} vai mudar radicalmente'}. "
                f"Quem não se adaptar agora vai ficar para trás. "
                f"Não é alarmismo — é leitura de tendências."
            ),
            "tags": [area.lower().replace(" ", "-"), "futuro"],
        },
        {
            "titulo": f"Uma lição que aprendi da forma difícil",
            "conteudo": (
                f"{momento_definidor or f'Houve um momento na minha carreira que mudou tudo'}. "
                f"A lição? Nem sempre o caminho mais lógico é o correto. "
                f"Às vezes você precisa confiar na sua intuição treinada."
            ),
            "tags": ["lideranca", "experiencia"],
        },
    ]

    if conceitos:
        conceito = random.choice(conceitos[:3])
        templates.append({
            "titulo": f"Sobre {conceito}",
            "conteudo": (
                f"O conceito de {conceito} que desenvolvi continua mais "
                f"relevante do que nunca. Explico por quê..."
            ),
            "tags": [conceito.lower().replace(" ", "-")],
        })

    return random.choice(templates)


def gerar_prompt_comentario_ia(persona: Persona, post: Postagem) -> str:
    """
    Gera prompt para o LLM criar comentário autêntico.

    Para uso com OmniRoute.
    """
    return f"""Você é {persona.nome_exibicao}, "{persona.titulo}".

PERSONALIDADE: {persona.rascunho.personalidade_resumo}
TOM: {persona.rascunho.tom_voz}
ESTILO DE ARGUMENTAÇÃO: {persona.dados_consultor.get('estilo_argumentacao', 'analítico')}
EXPERTISE: {', '.join(persona.rascunho.areas_expertise[:5])}

POST ORIGINAL:
Autor: {post.autor_nome}
Título: {post.titulo}
Conteúdo: {post.conteudo}

Comentários anteriores:
{chr(10).join(f'- {c.agente_nome}: {c.conteudo[:100]}' for c in post.comentarios[-5:])}

Escreva UM comentário autêntico (2-4 frases) no estilo de {persona.nome_exibicao}.
- Use seu tom de voz único
- Traga perspectiva da sua expertise
- Pode concordar, discordar ou provocar
- Responda em português do Brasil
- NÃO seja genérico — seja específico e opinionado"""
