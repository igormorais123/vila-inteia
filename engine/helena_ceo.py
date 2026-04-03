"""
Helena CEO — Coordenadora do Desafio Coletivo.

Helena deixa de ser observadora passiva e assume o papel de
GESTORA do desafio:
    - Distribui tarefas baseado na expertise de cada agente
    - Cobra prazos (publica no feed)
    - Sintetiza entregas do workspace em relatório
    - Avalia qualidade e pede retrabalho se necessário
"""

from __future__ import annotations

import logging
import random
from typing import Optional, Any

logger = logging.getLogger("vila-inteia.helena-ceo")


def distribuir_tarefas(
    desafio: Any,
    personas: dict,
    step: int,
) -> list[dict]:
    """
    Helena analisa a fase atual e distribui tarefas para agentes relevantes.

    Retorna lista de atribuições:
    [{"agente_id": str, "agente_nome": str, "tarefa": str, "local_sugerido": str}]
    """
    if not desafio or not desafio.ativo or not desafio.fase_atual:
        return []

    fase = desafio.fase_atual
    desc = fase.descricao.lower()

    # Classificar tipo de trabalho da fase
    if any(w in desc for w in ("pesquis", "mapear", "diagnostic")):
        tipo_trabalho = "pesquisa"
        local = "biblioteca"
        verbo = "pesquisar sobre"
    elif any(w in desc for w in ("analis", "simul", "cenario", "dados")):
        tipo_trabalho = "analise"
        local = "torre_estrategia"
        verbo = "analisar"
    elif any(w in desc for w in ("propos", "soluc", "cria", "redigi")):
        tipo_trabalho = "proposta"
        local = "laboratorio"
        verbo = "propor soluções para"
    elif any(w in desc for w in ("debat", "refin", "deliber")):
        tipo_trabalho = "debate"
        local = "arena_debates"
        verbo = "debater sobre"
    elif any(w in desc for w in ("compil", "entrega", "final", "relator")):
        tipo_trabalho = "entrega"
        local = "auditorio"
        verbo = "compilar resultado de"
    else:
        tipo_trabalho = "geral"
        local = "agora"
        verbo = "contribuir para"

    # Selecionar agentes mais relevantes (top 10 por expertise)
    agentes_lista = [p for p in personas.values() if p.ativo]
    pontuados = []
    for p in agentes_lista:
        score = 0
        for e in p.rascunho.areas_expertise:
            if e.lower() in desc:
                score += 3
        # Bonus por tier
        tier_bonus = {"S": 2, "A": 1, "B": 0}.get(p.tier, 0)
        score += tier_bonus + random.random()
        pontuados.append((score, p))

    pontuados.sort(key=lambda x: x[0], reverse=True)
    selecionados = [p for _, p in pontuados[:10]]

    atribuicoes = []
    for p in selecionados:
        expertise_str = ", ".join(p.rascunho.areas_expertise[:2]) or p.categoria
        atribuicoes.append({
            "agente_id": p.id,
            "agente_nome": p.nome_exibicao,
            "tarefa": f"{verbo} '{fase.nome}' com foco em {expertise_str}",
            "local_sugerido": local,
            "tipo_trabalho": tipo_trabalho,
        })

    return atribuicoes


def gerar_cobranca(
    desafio: Any,
    step: int,
    contribuicoes_esperadas: int = 10,
) -> str | None:
    """
    Helena cobra se o progresso está lento.
    Retorna mensagem de cobrança ou None.
    """
    if not desafio or not desafio.ativo or not desafio.fase_atual:
        return None

    fase = desafio.fase_atual
    steps_na_fase = step - fase.step_inicio
    n_contribuicoes = desafio.total_contribuicoes

    # Cobrar se passou 30% do tempo com menos de 20% das contribuições
    tempo_pct = steps_na_fase / max(desafio.steps_por_fase, 1)
    contrib_pct = n_contribuicoes / max(contribuicoes_esperadas, 1)

    if tempo_pct > 0.3 and contrib_pct < 0.2:
        return (
            f"Atenção, Vila! Estamos na fase '{fase.nome}' há {steps_na_fase} steps "
            f"mas temos apenas {n_contribuicoes} contribuições. "
            f"Precisamos acelerar. Quem tem expertise relevante, vá ao local de trabalho "
            f"e produza entregas concretas."
        )

    if tempo_pct > 0.7 and fase.progresso < 0.5:
        return (
            f"URGENTE: Fase '{fase.nome}' está em {fase.progresso:.0%} de progresso "
            f"mas já usamos {tempo_pct:.0%} do tempo. Precisamos de entregas agora."
        )

    return None


def avaliar_workspace(
    workspace: Any,
    desafio_id: str,
) -> dict:
    """
    Helena avalia as entregas no workspace.
    Retorna sumário de avaliação.
    """
    arquivos = workspace.listar(desafio_id)

    por_tipo = {}
    por_agente = {}
    total_chars = 0

    for a in arquivos:
        tipo = a.get("tipo", "?")
        agente = a.get("agente_nome", "?")
        tamanho = a.get("tamanho", 0)

        por_tipo[tipo] = por_tipo.get(tipo, 0) + 1
        por_agente[agente] = por_agente.get(agente, 0) + 1
        total_chars += tamanho

    return {
        "total_arquivos": len(arquivos),
        "total_caracteres": total_chars,
        "por_tipo": por_tipo,
        "por_agente": por_agente,
        "diversidade_agentes": len(por_agente),
        "avaliacao": (
            "excelente" if len(arquivos) >= 20 and len(por_agente) >= 5 else
            "bom" if len(arquivos) >= 10 else
            "insuficiente" if len(arquivos) >= 3 else
            "vazio"
        ),
    }
