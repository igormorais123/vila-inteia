"""
Cliente Mirante — publica matérias da Vila no jornal externo.

Contrato (contrato que o Mirante expõe em `POST /api/vila/submissoes`):
    request:
        {
            "submissao_id": "uuid",       # idempotência
            "titulo": "...",
            "slug": "...",                # opcional, Mirante regera se conflito
            "categoria": "...",           # precisa estar em CATEGORIAS_VALIDAS
            "tags": ["..."],
            "excerpt": "...",
            "corpo_mdx": "...",           # MDX já pronto, frontmatter opcional
            "autor": {
                "agente_id": "...",
                "nome": "...",
                "vila_id": "..."
            },
            "parecer_editorial": {        # parecer do Chateaubriand
                "veredito": "aprovado|aprovado_com_ajustes",
                "score": 0.0..1.0,
                "observacoes": "..."
            }
        }
    response 200:
        {
            "status": "publicado|em_fila|bloqueado",
            "url": "https://mirantenews.com.br/<slug>",
            "motivo": "..."   # quando bloqueado
        }

Se `MIRANTE_API_URL` não estiver configurado, cai no modo local: escreve MDX
direto numa pasta (`MIRANTE_CONTENT_DIR`). Útil em dev quando Vila e Mirante
estão no mesmo workspace.
"""

from __future__ import annotations

import json
import logging
import os
import re
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Optional
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

logger = logging.getLogger("vila-inteia.mirante")


# =========================================================
# Config
# =========================================================

MIRANTE_API_URL = os.getenv("MIRANTE_API_URL", "").rstrip("/")
MIRANTE_API_TOKEN = os.getenv("MIRANTE_API_TOKEN", "")
MIRANTE_CONTENT_DIR = os.getenv("MIRANTE_CONTENT_DIR", "")  # fallback local
MIRANTE_TIMEOUT_S = int(os.getenv("MIRANTE_TIMEOUT_S", "30"))
MIRANTE_MAX_RETRIES = int(os.getenv("MIRANTE_MAX_RETRIES", "3"))

CATEGORIAS_VALIDAS = [
    "Politica", "Juridico", "Tecnologia", "Dados", "Economia",
    "DF", "Brasil", "Mundo", "Esportes", "Cultura", "Opiniao",
    "Pesquisa IA", "Educacao", "Saude",
]

# Mapa: categoria do agente Vila -> editoria do Mirante
MAPA_CATEGORIA_AGENTE = {
    "estrategia": "Politica",
    "politica_brasileira": "Politica",
    "politica_internacional": "Mundo",
    "jurista_lendario": "Juridico",
    "investidor": "Economia",
    "tech": "Tecnologia",
    "ia_futuro": "Tecnologia",
    "visionario": "Tecnologia",
    "qi_extremo": "Pesquisa IA",
    "marca": "Cultura",
    "mkt_digital": "Economia",
    "mindset": "Opiniao",
    "resiliencia": "Opiniao",
    "influencia_oratoria": "Politica",
    "negociacao": "Politica",
    "br_business": "Economia",
    "omega": "Opiniao",
    "ficticio": "Cultura",
    "lado_negro": "Opiniao",
    "inteia": "Pesquisa IA",
    "jornalismo": "Brasil",
    "editor_chefe": "Brasil",
}


# =========================================================
# Dataclasses
# =========================================================

@dataclass
class Autor:
    agente_id: str = ""
    nome: str = ""
    vila_id: str = ""


@dataclass
class ParecerEditorial:
    veredito: str = "aprovado"   # aprovado | aprovado_com_ajustes | reescrito | rejeitado
    score: float = 0.7
    observacoes: str = ""
    reescrito: bool = False


@dataclass
class Submissao:
    submissao_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    titulo: str = ""
    slug: str = ""
    categoria: str = "Pesquisa IA"
    tags: list = field(default_factory=list)
    excerpt: str = ""
    corpo_mdx: str = ""
    autor: Autor = field(default_factory=Autor)
    parecer_editorial: ParecerEditorial = field(default_factory=ParecerEditorial)

    def to_dict(self) -> dict:
        d = asdict(self)
        return d


@dataclass
class ResultadoPublicacao:
    status: str                      # publicado | em_fila | bloqueado | erro | salvo_local
    url: str = ""
    motivo: str = ""
    submissao_id: str = ""
    tentativas: int = 0
    transporte: str = "api"          # api | local


# =========================================================
# Utilitários
# =========================================================

def slugify(titulo: str) -> str:
    """kebab-case sem acento."""
    s = titulo.lower().strip()
    acentos = [
        (r"[àáâãä]", "a"), (r"[èéêë]", "e"), (r"[ìíîï]", "i"),
        (r"[òóôõö]", "o"), (r"[ùúûü]", "u"), (r"[ç]", "c"), (r"[ñ]", "n"),
    ]
    for pat, rep in acentos:
        s = re.sub(pat, rep, s)
    s = re.sub(r"[^a-z0-9\s-]", "", s)
    s = re.sub(r"\s+", "-", s).strip("-")
    s = re.sub(r"-+", "-", s)
    return s[:80]


def normalizar_categoria(cat_agente: str, categoria_proposta: str = "") -> str:
    if categoria_proposta in CATEGORIAS_VALIDAS:
        return categoria_proposta
    return MAPA_CATEGORIA_AGENTE.get(cat_agente, "Pesquisa IA")


def gerar_mdx(submissao: Submissao) -> str:
    """Monta MDX com frontmatter compatível com o schema Zod do Mirante."""
    slug = submissao.slug or slugify(submissao.titulo)
    data = datetime.now().strftime("%Y-%m-%d")
    tags_str = ", ".join(f'"{t}"' for t in submissao.tags)
    excerpt = submissao.excerpt or submissao.corpo_mdx[:240].replace('"', "'")
    excerpt = excerpt[:290]

    frontmatter = f"""---
title: "{submissao.titulo}"
slug: "{slug}"
date: "{data}"
author: "vila-inteia"
category: "{submissao.categoria}"
coverImage: ""
tags: [{tags_str}]
excerpt: "{excerpt}"
featured: false
published: true
verification: "sintetico"
---

"""
    rodape = (
        "\n\n---\n\n"
        f"*Matéria produzida na Vila INTEIA por **{submissao.autor.nome}** "
        f"e aprovada pelo editor-chefe Assis Chateaubriand.*\n"
    )
    # Se corpo já trouxer frontmatter, não duplica
    corpo = submissao.corpo_mdx.lstrip()
    if corpo.startswith("---"):
        return corpo
    return frontmatter + corpo + rodape


# =========================================================
# Transporte via API (principal)
# =========================================================

def _publicar_via_api(submissao: Submissao) -> ResultadoPublicacao:
    if not MIRANTE_API_URL:
        raise RuntimeError("MIRANTE_API_URL não configurado")

    url = f"{MIRANTE_API_URL}/api/vila/submissoes"
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "vila-inteia/2.0",
    }
    if MIRANTE_API_TOKEN:
        headers["Authorization"] = f"Bearer {MIRANTE_API_TOKEN}"

    payload = submissao.to_dict()
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")

    ultimo_erro = ""
    for tentativa in range(1, MIRANTE_MAX_RETRIES + 1):
        try:
            req = Request(url, data=body, headers=headers, method="POST")
            with urlopen(req, timeout=MIRANTE_TIMEOUT_S) as resp:
                text = resp.read().decode("utf-8")
                data = json.loads(text) if text else {}
                return ResultadoPublicacao(
                    status=data.get("status", "em_fila"),
                    url=data.get("url", ""),
                    motivo=data.get("motivo", ""),
                    submissao_id=submissao.submissao_id,
                    tentativas=tentativa,
                    transporte="api",
                )
        except HTTPError as e:
            corpo_erro = e.read().decode("utf-8", errors="ignore")[:400]
            # 4xx -> não retentar (bloqueado pelo Mirante)
            if 400 <= e.code < 500:
                try:
                    data = json.loads(corpo_erro)
                    return ResultadoPublicacao(
                        status="bloqueado",
                        motivo=data.get("motivo", corpo_erro),
                        submissao_id=submissao.submissao_id,
                        tentativas=tentativa,
                        transporte="api",
                    )
                except json.JSONDecodeError:
                    return ResultadoPublicacao(
                        status="bloqueado",
                        motivo=f"HTTP {e.code}: {corpo_erro}",
                        submissao_id=submissao.submissao_id,
                        tentativas=tentativa,
                        transporte="api",
                    )
            ultimo_erro = f"HTTP {e.code}: {corpo_erro}"
        except URLError as e:
            ultimo_erro = f"URLError: {e.reason}"
        except Exception as e:
            ultimo_erro = f"{type(e).__name__}: {e}"

        logger.warning(f"Tentativa {tentativa} falhou: {ultimo_erro}")

    return ResultadoPublicacao(
        status="erro",
        motivo=ultimo_erro,
        submissao_id=submissao.submissao_id,
        tentativas=MIRANTE_MAX_RETRIES,
        transporte="api",
    )


# =========================================================
# Transporte local (fallback dev)
# =========================================================

def _publicar_via_arquivo(submissao: Submissao) -> ResultadoPublicacao:
    if not MIRANTE_CONTENT_DIR:
        return ResultadoPublicacao(
            status="erro",
            motivo="Nem MIRANTE_API_URL nem MIRANTE_CONTENT_DIR configurados",
            submissao_id=submissao.submissao_id,
        )

    if not os.path.isdir(MIRANTE_CONTENT_DIR):
        return ResultadoPublicacao(
            status="erro",
            motivo=f"MIRANTE_CONTENT_DIR não existe: {MIRANTE_CONTENT_DIR}",
            submissao_id=submissao.submissao_id,
        )

    slug = submissao.slug or slugify(submissao.titulo)
    caminho = os.path.join(MIRANTE_CONTENT_DIR, f"{slug}.mdx")
    try:
        with open(caminho, "w", encoding="utf-8") as f:
            f.write(gerar_mdx(submissao))
        return ResultadoPublicacao(
            status="salvo_local",
            url=f"file://{caminho}",
            submissao_id=submissao.submissao_id,
            transporte="local",
        )
    except Exception as e:
        return ResultadoPublicacao(
            status="erro",
            motivo=str(e),
            submissao_id=submissao.submissao_id,
            transporte="local",
        )


# =========================================================
# API pública
# =========================================================

def publicar(submissao: Submissao) -> ResultadoPublicacao:
    """
    Publica submissão no Mirante. Escolhe transporte automaticamente.

    Precedência:
        1. MIRANTE_API_URL (API REST oficial — recomendado)
        2. MIRANTE_CONTENT_DIR (escreve MDX local — dev)
    """
    # Validações mínimas
    if not submissao.titulo:
        return ResultadoPublicacao(status="erro", motivo="título obrigatório",
                                   submissao_id=submissao.submissao_id)
    if len(submissao.corpo_mdx) < 200:
        return ResultadoPublicacao(status="erro", motivo="corpo muito curto (min 200 chars)",
                                   submissao_id=submissao.submissao_id)
    if submissao.categoria not in CATEGORIAS_VALIDAS:
        submissao.categoria = "Pesquisa IA"
    if not submissao.slug:
        submissao.slug = slugify(submissao.titulo)

    # Preencher excerpt se faltando
    if not submissao.excerpt:
        submissao.excerpt = submissao.corpo_mdx[:240].replace('"', "'")

    # Garantir que corpo_mdx tenha frontmatter
    if not submissao.corpo_mdx.lstrip().startswith("---"):
        submissao.corpo_mdx = gerar_mdx(submissao)

    if MIRANTE_API_URL:
        resultado = _publicar_via_api(submissao)
        # Se a API falhou completamente e temos fallback local, tenta local
        if resultado.status == "erro" and MIRANTE_CONTENT_DIR:
            logger.warning("API falhou, tentando fallback local")
            return _publicar_via_arquivo(submissao)
        return resultado

    return _publicar_via_arquivo(submissao)


def status_integracao() -> dict:
    """Retorna estado da configuração do cliente."""
    return {
        "api_configurada": bool(MIRANTE_API_URL),
        "api_url": MIRANTE_API_URL or None,
        "token_configurado": bool(MIRANTE_API_TOKEN),
        "fallback_local": bool(MIRANTE_CONTENT_DIR),
        "content_dir": MIRANTE_CONTENT_DIR or None,
        "max_retries": MIRANTE_MAX_RETRIES,
        "timeout_s": MIRANTE_TIMEOUT_S,
    }
