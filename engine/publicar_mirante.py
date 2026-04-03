"""
Publicação no Mirante News — Canal real de output da Vila INTEIA.

Agentes produzem artigos no workspace → Helena revisa → publica no
mirantenews.com.br como arquivo MDX → git push → Vercel deploya.

Categorias válidas: Politica, Juridico, Tecnologia, Dados, Economia,
DF, Brasil, Mundo, Esportes, Cultura, Opiniao, Pesquisa IA, Educacao, Saude

Formato: MDX com frontmatter Zod-validado.
"""

from __future__ import annotations

import logging
import os
import re
import subprocess
from datetime import datetime
from dataclasses import dataclass, field
from typing import Optional

logger = logging.getLogger("vila-inteia.mirante")

# Caminho do diretório de conteúdo do Mirante News
MIRANTE_CONTENT_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "frontend", "content", "mirante"
)

# Categorias válidas (schema Zod do Mirante)
CATEGORIAS_VALIDAS = [
    "Politica", "Juridico", "Tecnologia", "Dados", "Economia",
    "DF", "Brasil", "Mundo", "Esportes", "Cultura", "Opiniao",
    "Pesquisa IA", "Educacao", "Saude",
]

# Mapeamento de categoria do agente → editoria do Mirante
MAPA_CATEGORIA = {
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
}


def _gerar_slug(titulo: str) -> str:
    """Gera slug kebab-case a partir do título."""
    slug = titulo.lower().strip()
    slug = re.sub(r'[àáâãä]', 'a', slug)
    slug = re.sub(r'[èéêë]', 'e', slug)
    slug = re.sub(r'[ìíîï]', 'i', slug)
    slug = re.sub(r'[òóôõö]', 'o', slug)
    slug = re.sub(r'[ùúûü]', 'u', slug)
    slug = re.sub(r'[ç]', 'c', slug)
    slug = re.sub(r'[^a-z0-9\s-]', '', slug)
    slug = re.sub(r'[\s]+', '-', slug)
    slug = re.sub(r'-+', '-', slug)
    return slug[:80].strip('-')


@dataclass
class ArtigoMirante:
    """Artigo pronto para publicação no Mirante News."""
    titulo: str = ""
    slug: str = ""
    corpo: str = ""
    excerpt: str = ""
    categoria: str = "Pesquisa IA"
    tags: list[str] = field(default_factory=list)
    autor_id: str = ""
    autor_nome: str = ""
    autor_categoria: str = ""
    verification: str = "sintetico"  # sintetico | opiniao
    desafio_nome: str = ""
    fase_nome: str = ""

    def gerar_mdx(self) -> str:
        """Gera conteúdo MDX completo com frontmatter."""
        slug = self.slug or _gerar_slug(self.titulo)
        data = datetime.now().strftime("%Y-%m-%d")
        tags_str = ", ".join(f'"{t}"' for t in self.tags)
        excerpt = self.excerpt or self.corpo[:200].replace('"', "'")

        mdx = f"""---
title: "{self.titulo}"
slug: "{slug}"
date: "{data}"
author: "vila-inteia"
category: "{self.categoria}"
coverImage: ""
tags: [{tags_str}]
excerpt: "{excerpt[:290]}"
featured: false
published: true
verification: "{self.verification}"
---

{self.corpo}

---

*Artigo produzido coletivamente pela Vila INTEIA.*
*Autor principal: {self.autor_nome}*
{f'*Desafio: {self.desafio_nome} — Fase: {self.fase_nome}*' if self.desafio_nome else ''}
"""
        return mdx

    def to_dict(self) -> dict:
        return {
            "titulo": self.titulo,
            "slug": self.slug or _gerar_slug(self.titulo),
            "categoria": self.categoria,
            "tags": self.tags,
            "autor_nome": self.autor_nome,
            "verification": self.verification,
            "tamanho_corpo": len(self.corpo),
            "desafio": self.desafio_nome,
        }


def publicar_no_mirante(
    artigo: ArtigoMirante,
    auto_push: bool = False,
) -> dict:
    """
    Publica artigo no Mirante News.

    1. Escreve arquivo MDX em frontend/content/mirante/
    2. Opcionalmente faz git add + commit + push

    Args:
        artigo: ArtigoMirante com conteúdo completo
        auto_push: Se True, faz git push automaticamente

    Returns:
        {"status": "publicado"|"salvo"|"erro", "caminho": str, ...}
    """
    # Validar categoria
    if artigo.categoria not in CATEGORIAS_VALIDAS:
        # Tentar mapear pela categoria do agente
        artigo.categoria = MAPA_CATEGORIA.get(
            artigo.autor_categoria, "Pesquisa IA"
        )

    # Validar conteúdo mínimo
    if len(artigo.corpo) < 200:
        return {"status": "erro", "mensagem": "Artigo muito curto (mínimo 200 chars)"}

    if not artigo.titulo:
        return {"status": "erro", "mensagem": "Título obrigatório"}

    # Gerar slug e MDX
    slug = artigo.slug or _gerar_slug(artigo.titulo)
    artigo.slug = slug
    mdx = artigo.gerar_mdx()

    # Verificar diretório
    if not os.path.isdir(MIRANTE_CONTENT_DIR):
        # Tentar caminho alternativo
        alt_dir = os.path.join("C:", os.sep, "Agentes", "frontend", "content", "mirante")
        if os.path.isdir(alt_dir):
            content_dir = alt_dir
        else:
            return {
                "status": "erro",
                "mensagem": f"Diretório do Mirante não encontrado: {MIRANTE_CONTENT_DIR}",
            }
    else:
        content_dir = MIRANTE_CONTENT_DIR

    # Escrever arquivo
    caminho = os.path.join(content_dir, f"{slug}.mdx")
    try:
        with open(caminho, "w", encoding="utf-8") as f:
            f.write(mdx)
    except Exception as e:
        return {"status": "erro", "mensagem": f"Erro ao escrever: {e}"}

    logger.info(f"Artigo salvo: {caminho} ({len(mdx)} chars)")

    resultado = {
        "status": "salvo",
        "caminho": caminho,
        "slug": slug,
        "url_prevista": f"https://mirantenews.com.br/{slug}",
        "tamanho": len(mdx),
        "artigo": artigo.to_dict(),
    }

    # Git push se solicitado
    if auto_push:
        try:
            repo_dir = os.path.dirname(os.path.dirname(content_dir))
            subprocess.run(
                ["git", "-C", repo_dir, "add", caminho],
                capture_output=True, timeout=10,
            )
            subprocess.run(
                ["git", "-C", repo_dir, "commit", "-m",
                 f"content(mirante): {artigo.titulo[:60]} [vila-inteia]"],
                capture_output=True, timeout=10,
            )
            proc = subprocess.run(
                ["git", "-C", repo_dir, "push"],
                capture_output=True, timeout=30,
            )
            if proc.returncode == 0:
                resultado["status"] = "publicado"
                resultado["deploy"] = "Vercel auto-deploy em ~3 minutos"
                logger.info(f"Artigo publicado e pushed: {slug}")
            else:
                resultado["status"] = "salvo_sem_push"
                resultado["push_erro"] = proc.stderr.decode()[:200]
        except Exception as e:
            resultado["status"] = "salvo_sem_push"
            resultado["push_erro"] = str(e)

    return resultado


def criar_artigo_de_workspace(
    workspace,
    desafio_id: str,
    agente_id: str,
    agente_nome: str,
    agente_categoria: str,
    titulo: str,
    desafio_nome: str = "",
    fase_nome: str = "",
) -> Optional[ArtigoMirante]:
    """
    Compila artefatos do workspace em artigo publicável.
    """
    # Pegar todos os arquivos do agente neste desafio
    arquivos = workspace.listar(desafio_id)
    do_agente = [a for a in arquivos if a.get("agente_id") == agente_id]

    if not do_agente:
        return None

    # Compilar conteúdo
    partes = []
    for meta in do_agente:
        conteudo = workspace.ler(desafio_id, meta["arquivo"])
        if conteudo:
            partes.append(conteudo)

    if not partes:
        return None

    corpo = "\n\n---\n\n".join(partes)

    # Tags baseadas no conteúdo
    tags = ["vila-inteia", "inteligencia-artificial"]
    if desafio_nome:
        tags.append(_gerar_slug(desafio_nome)[:30])
    if agente_categoria:
        tags.append(agente_categoria)

    return ArtigoMirante(
        titulo=titulo,
        corpo=corpo,
        categoria=MAPA_CATEGORIA.get(agente_categoria, "Pesquisa IA"),
        tags=tags[:5],
        autor_id=agente_id,
        autor_nome=agente_nome,
        autor_categoria=agente_categoria,
        desafio_nome=desafio_nome,
        fase_nome=fase_nome,
    )
