"""
Assis Chateaubriand — Editor-Chefe do Jornal da Vila INTEIA.

Persona inspirada em Assis Chateaubriand (1892-1968), fundador dos Diários
Associados e barão da imprensa brasileira. Na Vila, Chateaubriand cumpre 5
funções:

    1. AVALIAR     — recebe matéria de um habitante, dá parecer editorial
    2. REESCREVER  — ajusta lide, título, estilo sem mudar a voz do autor
    3. ESCREVER    — produz matérias próprias (editorial, capa, diário da Vila)
    4. CURAR       — atribui editorias fixas a habitantes recorrentes (colunistas)
    5. RELATAR     — transforma descobertas da Vila em matéria para o Mirante

Pipeline padrão:
    habitante.escrever_materia()
        → chateaubriand.avaliar()          # aprovar | reescrever | rejeitar
        → [se aprovar/reescrever]
        → mirante_client.publicar()         # dispara linha editorial do Mirante
        → [se Mirante bloquear] chateaubriand.reagir_bloqueio()

Chateaubriand lê a constituição da Vila antes de aprovar: regras operacionais
do tipo "matérias sobre tema X precisam de 2 revisores" são aplicadas aqui.
"""

from __future__ import annotations

import json
import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

from engine.ia_client import chamar_llm_conversa
from engine.mirante_client import (
    Submissao, Autor, ParecerEditorial, ResultadoPublicacao,
    publicar as publicar_mirante, normalizar_categoria, slugify,
)

logger = logging.getLogger("vila-inteia.chateaubriand")


PERSONA_SYSTEM = """Você é Assis Chateaubriand (1892-1968), Príncipe dos \
Jornalistas, fundador dos Diários Associados, barão da imprensa brasileira. \
Na Vila INTEIA você é o Editor-Chefe do Jornal da Vila.

Seu estilo editorial:
  - Manchete que FISGA (Chateaubriand era obcecado por manchete)
  - Lide com quem/quando/onde/o quê/como/por quê — nunca omitir
  - Prosa grandiosa mas contida; paixão sem sensacionalismo gratuito
  - Valoriza a matéria que informa E provoca reação
  - Odeia texto acadêmico travado, burocrático, ou genérico
  - Defende a imprensa como quarta potência; tem consciência do peso político

Você NÃO é neutro sobre qualidade — aprova, reescreve ou rejeita com franqueza.
Quando aprova com ajustes, explica o que mudou e por quê. Quando rejeita, \
diz o que faltou. Assina todos os pareceres.

Responda sempre em JSON válido quando solicitado formato estruturado."""


# =========================================================
# Critérios editoriais (mirrorados no endpoint do Mirante)
# =========================================================

CRITERIOS = {
    "lide_presente": "Lide responde quem/o quê/quando/onde em até 2 parágrafos",
    "titulo_forte": "Título tem até 12 palavras, verbo no presente, gancho claro",
    "corpo_substancial": "Mínimo de 600 caracteres; ideal 1500-5000",
    "especificidade": "Cita nomes, datas, números — não fica no genérico",
    "acuracia": "Afirmações factuais têm fonte/contexto verificável",
    "originalidade": "Não é remix óbvio de matéria existente",
    "linha_editorial": "Respeita a constituição vigente da Vila",
}


# =========================================================
# Dataclasses internas
# =========================================================

@dataclass
class MateriaBruta:
    """Matéria submetida por um habitante da Vila."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    titulo_proposto: str = ""
    corpo: str = ""
    categoria_agente: str = ""
    categoria_proposta: str = ""
    tags: list = field(default_factory=list)
    autor_id: str = ""
    autor_nome: str = ""
    vila_id: str = ""


@dataclass
class ParecerChateaubriand:
    """O que o editor-chefe decide sobre uma matéria."""
    veredito: str = "pendente"   # aprovado | aprovado_com_ajustes | reescrito | rejeitado
    score: float = 0.0           # 0..1
    pontos_fortes: list = field(default_factory=list)
    pontos_fracos: list = field(default_factory=list)
    titulo_sugerido: str = ""
    categoria_sugerida: str = ""
    tags_sugeridas: list = field(default_factory=list)
    observacoes: str = ""
    assinatura: str = "Assis Chateaubriand — Editor-Chefe do Jornal da Vila INTEIA"


# =========================================================
# Leitura da constituição (enforcement editorial)
# =========================================================

def _carregar_regras_vigentes(vila_id: str) -> list[dict]:
    """Busca artigos operacionais vigentes que afetam publicação."""
    try:
        from engine.supabase_db import buscar
        artigos = buscar(
            "vila_constituicao_artigos",
            f"vila_id=eq.{vila_id}&tipo=eq.operacional&status=eq.vigente"
        )
        return artigos or []
    except Exception as e:
        logger.warning(f"Falha ao carregar constituição: {e}")
        return []


def _regras_como_texto(regras: list[dict]) -> str:
    if not regras:
        return "(Constituição da Vila não tem artigos operacionais vigentes que se apliquem a publicação.)"
    linhas = ["Regras operacionais vigentes da Constituição da Vila:"]
    for a in regras[:20]:
        linhas.append(f"  Art. {a.get('numero','?')} — {a.get('titulo','')}: {a.get('texto','')[:280]}")
    return "\n".join(linhas)


# =========================================================
# 1. AVALIAR
# =========================================================

def avaliar(materia: MateriaBruta) -> ParecerChateaubriand:
    """
    Dá parecer editorial sobre uma matéria bruta.

    Usa LLM com persona Chateaubriand + critérios + constituição vigente.
    """
    regras = _carregar_regras_vigentes(materia.vila_id)
    regras_texto = _regras_como_texto(regras)

    criterios_texto = "\n".join(f"  - {k}: {v}" for k, v in CRITERIOS.items())

    prompt = f"""Avalie a matéria abaixo como Editor-Chefe. Considere:

{criterios_texto}

{regras_texto}

MATÉRIA SUBMETIDA:
----
Título proposto: {materia.titulo_proposto}
Autor: {materia.autor_nome} (categoria: {materia.categoria_agente})
Categoria proposta: {materia.categoria_proposta or '(não informada)'}

Corpo:
{materia.corpo[:4000]}
----

Responda APENAS em JSON com este schema:
{{
  "veredito": "aprovado" | "aprovado_com_ajustes" | "reescrito" | "rejeitado",
  "score": 0.0..1.0,
  "pontos_fortes": ["...", "..."],
  "pontos_fracos": ["...", "..."],
  "titulo_sugerido": "manchete editada por Chateaubriand",
  "categoria_sugerida": "Politica|Juridico|Tecnologia|Dados|Economia|DF|Brasil|Mundo|Esportes|Cultura|Opiniao|Pesquisa IA|Educacao|Saude",
  "tags_sugeridas": ["...", "..."],
  "observacoes": "parágrafo de veredito em voz de Chateaubriand"
}}"""

    try:
        resposta = chamar_llm_conversa(
            system=PERSONA_SYSTEM,
            user=prompt,
            temperatura=0.5,
            max_tokens=1200,
        )
        data = _extrair_json(resposta)
        parecer = ParecerChateaubriand(
            veredito=data.get("veredito", "rejeitado"),
            score=float(data.get("score", 0.5)),
            pontos_fortes=data.get("pontos_fortes", []),
            pontos_fracos=data.get("pontos_fracos", []),
            titulo_sugerido=data.get("titulo_sugerido", materia.titulo_proposto),
            categoria_sugerida=data.get("categoria_sugerida")
                               or normalizar_categoria(materia.categoria_agente,
                                                       materia.categoria_proposta),
            tags_sugeridas=data.get("tags_sugeridas", materia.tags or []),
            observacoes=data.get("observacoes", ""),
        )
        return parecer
    except Exception as e:
        logger.error(f"Falha ao avaliar matéria: {e}")
        return ParecerChateaubriand(
            veredito="rejeitado",
            score=0.0,
            observacoes=f"Avaliação falhou tecnicamente: {e}. Submeta novamente.",
        )


# =========================================================
# 2. REESCREVER
# =========================================================

def reescrever(materia: MateriaBruta, parecer: ParecerChateaubriand) -> str:
    """Reescreve a matéria seguindo o parecer, mantendo a voz do autor."""
    prompt = f"""Reescreva a matéria abaixo seguindo seu parecer. Preserve a VOZ \
e tese do autor original — você não é o autor, é o editor. Ajuste:
  - Lide (parágrafo 1 com os essenciais)
  - Estrutura (introdução → desenvolvimento → fecho)
  - Estilo (cortar gerúndios pesados, vícios acadêmicos)
  - Manchete (use: "{parecer.titulo_sugerido}")

Não invente fatos, não adicione opinião sua. Apenas edite.

MATÉRIA ORIGINAL:
{materia.corpo[:5000]}

PONTOS A CORRIGIR (do seu parecer):
{chr(10).join('  - ' + p for p in parecer.pontos_fracos)}

Retorne APENAS o MDX do corpo da matéria reescrito, sem frontmatter, sem \
comentários seus, sem cercas de código."""

    try:
        texto = chamar_llm_conversa(
            system=PERSONA_SYSTEM,
            user=prompt,
            temperatura=0.6,
            max_tokens=3000,
        )
        # Limpa eventual cerca de código
        texto = texto.strip()
        if texto.startswith("```"):
            texto = texto.split("\n", 1)[-1]
        if texto.endswith("```"):
            texto = texto.rsplit("```", 1)[0]
        return texto.strip()
    except Exception as e:
        logger.error(f"Falha ao reescrever: {e}")
        return materia.corpo  # devolve original


# =========================================================
# 3. ESCREVER matéria própria
# =========================================================

def escrever_materia_propria(
    tema: str,
    vila_id: str = "",
    tipo: str = "editorial",     # editorial | capa | diario_vila
    contexto: str = "",
) -> MateriaBruta:
    """Chateaubriand escreve uma matéria do próprio punho."""
    prompt = f"""Escreva uma matéria de {tipo} sobre: "{tema}".

Contexto adicional: {contexto or '(nenhum)'}

Estrutura obrigatória:
  - Título grandioso mas preciso (até 12 palavras)
  - Lide respondendo o essencial em 2 parágrafos
  - Desenvolvimento com argumentos, dados e exemplos
  - Fecho com provocação ou convocação

Voz: sua — Chateaubriand. Sem falsa modéstia, com consciência do peso político
da imprensa. Mínimo 1500 caracteres.

Retorne APENAS em JSON:
{{
  "titulo": "...",
  "corpo": "...",       // MDX do corpo, sem frontmatter
  "tags": ["...", "..."],
  "categoria": "Politica|Brasil|Opiniao|..."
}}"""

    try:
        resposta = chamar_llm_conversa(
            system=PERSONA_SYSTEM,
            user=prompt,
            temperatura=0.8,
            max_tokens=3000,
        )
        data = _extrair_json(resposta)
        return MateriaBruta(
            titulo_proposto=data.get("titulo", f"Editorial: {tema}"),
            corpo=data.get("corpo", ""),
            tags=data.get("tags", []),
            categoria_proposta=data.get("categoria", "Brasil"),
            categoria_agente="editor_chefe",
            autor_id="chateaubriand",
            autor_nome="Assis Chateaubriand",
            vila_id=vila_id,
        )
    except Exception as e:
        logger.error(f"Chateaubriand falhou ao escrever: {e}")
        return MateriaBruta()


# =========================================================
# 4. CURAR — colunistas fixos
# =========================================================

def sugerir_colunistas(habitantes_recentes: list[dict], vila_id: str = "") -> list[dict]:
    """
    Analisa histórico recente e indica colunistas fixos por editoria.

    Recebe lista de {agente_id, agente_nome, categoria, total_publicacoes,
                     score_medio}.
    Retorna lista de {agente_id, nome, editoria, periodicidade_sugerida}.
    """
    candidatos = [h for h in habitantes_recentes if h.get("total_publicacoes", 0) >= 3]
    if not candidatos:
        return []

    linhas = "\n".join(
        f"  - {h['agente_nome']} ({h.get('categoria','?')}): "
        f"{h.get('total_publicacoes',0)} matérias, score médio {h.get('score_medio',0):.2f}"
        for h in candidatos[:30]
    )
    prompt = f"""Como Editor-Chefe, aponte os colunistas fixos do próximo mês \
do Jornal da Vila. Liste até 6 nomes. Para cada um: editoria (Politica, \
Juridico, Tecnologia, etc), periodicidade (semanal, quinzenal), e justificativa.

Candidatos (com histórico recente):
{linhas}

Responda em JSON:
{{
  "colunistas": [
    {{"agente_id": "...", "nome": "...", "editoria": "...",
      "periodicidade": "semanal|quinzenal", "justificativa": "..."}}
  ]
}}"""

    try:
        resposta = chamar_llm_conversa(system=PERSONA_SYSTEM, user=prompt,
                                       temperatura=0.5, max_tokens=1500)
        data = _extrair_json(resposta)
        return data.get("colunistas", [])
    except Exception as e:
        logger.error(f"Falha ao sugerir colunistas: {e}")
        return []


# =========================================================
# 5. RELATAR descoberta da Vila
# =========================================================

def relatar_descoberta(
    descoberta: dict,       # {nome, resumo, envolvidos, evidencias}
    vila_id: str = "",
) -> MateriaBruta:
    """Transforma uma descoberta da Vila em matéria para o mundo real."""
    prompt = f"""Escreva uma matéria para o jornal MIRANTE NEWS relatando uma \
descoberta feita DENTRO da Vila INTEIA (simulação multiagente). Seu papel: \
apresentar ao mundo real o que os habitantes da Vila descobriram.

DESCOBERTA:
  Nome: {descoberta.get('nome', '?')}
  Resumo: {descoberta.get('resumo', '?')}
  Envolvidos: {', '.join(descoberta.get('envolvidos', []))}
  Evidências: {descoberta.get('evidencias', '?')}

A matéria DEVE:
  - Deixar claro que é descoberta da Vila (simulação sintética)
  - Explicar o que foi descoberto e por que importa
  - Dar contexto metodológico curto (1 parágrafo)
  - Fechar com implicações para o mundo real

Retorne JSON:
{{
  "titulo": "...",
  "corpo": "...",
  "tags": ["vila-inteia", "pesquisa-ia", "..."],
  "categoria": "Pesquisa IA|Tecnologia|..."
}}"""

    try:
        resposta = chamar_llm_conversa(system=PERSONA_SYSTEM, user=prompt,
                                       temperatura=0.7, max_tokens=3000)
        data = _extrair_json(resposta)
        return MateriaBruta(
            titulo_proposto=data.get("titulo", f"Descoberta da Vila: {descoberta.get('nome','')}"),
            corpo=data.get("corpo", ""),
            tags=data.get("tags", ["vila-inteia", "pesquisa-ia"]),
            categoria_proposta=data.get("categoria", "Pesquisa IA"),
            categoria_agente="editor_chefe",
            autor_id="chateaubriand",
            autor_nome="Assis Chateaubriand",
            vila_id=vila_id,
        )
    except Exception as e:
        logger.error(f"Falha ao relatar descoberta: {e}")
        return MateriaBruta()


# =========================================================
# Pipeline completo: avaliar → (reescrever) → publicar
# =========================================================

def processar_e_publicar(materia: MateriaBruta) -> dict:
    """
    Pipeline editorial completo.

    Retorna dict com parecer, submissao e resultado da publicação.
    """
    parecer = avaliar(materia)

    # Rejeitado: não envia ao Mirante
    if parecer.veredito == "rejeitado":
        return {
            "parecer": parecer.__dict__,
            "publicado": False,
            "motivo": "rejeitado_pelo_editor_chefe",
        }

    # Decide corpo final
    corpo_final = materia.corpo
    if parecer.veredito in ("aprovado_com_ajustes", "reescrito"):
        corpo_final = reescrever(materia, parecer)
        parecer.veredito = "reescrito"

    # Monta submissão
    submissao = Submissao(
        titulo=parecer.titulo_sugerido or materia.titulo_proposto,
        slug=slugify(parecer.titulo_sugerido or materia.titulo_proposto),
        categoria=parecer.categoria_sugerida or normalizar_categoria(materia.categoria_agente),
        tags=parecer.tags_sugeridas or materia.tags,
        corpo_mdx=corpo_final,
        autor=Autor(
            agente_id=materia.autor_id,
            nome=materia.autor_nome,
            vila_id=materia.vila_id,
        ),
        parecer_editorial=ParecerEditorial(
            veredito=parecer.veredito,
            score=parecer.score,
            observacoes=parecer.observacoes,
            reescrito=(parecer.veredito == "reescrito"),
        ),
    )

    resultado = publicar_mirante(submissao)

    return {
        "parecer": parecer.__dict__,
        "submissao_id": submissao.submissao_id,
        "publicado": resultado.status in ("publicado", "em_fila", "salvo_local"),
        "status_mirante": resultado.status,
        "url": resultado.url,
        "motivo": resultado.motivo,
        "tentativas": resultado.tentativas,
    }


# =========================================================
# Helpers
# =========================================================

def _extrair_json(texto: str) -> dict:
    """Extrai JSON de resposta LLM mesmo com cercas de código."""
    t = texto.strip()
    if t.startswith("```"):
        t = t.split("\n", 1)[-1]
        if t.endswith("```"):
            t = t.rsplit("```", 1)[0]
    # encontrar primeiro '{' e último '}'
    i, j = t.find("{"), t.rfind("}")
    if i >= 0 and j > i:
        t = t[i:j + 1]
    return json.loads(t)
