"""
RECUPERAR - Módulo de Recuperação de Memória.

Busca na memória de longo prazo contexto relevante
para as percepções atuais, usando pontuação tripla:
relevância + recência + importância.
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..persona import Persona

from ..memoria.fluxo import NoMemoria


def recuperar(
    persona: Persona,
    percepcoes: list[dict],
    hora_atual: datetime,
) -> dict:
    """
    Recupera memórias relevantes para o contexto atual.

    Retorna:
    {
        "memorias_relevantes": list[NoMemoria],
        "pessoas_conhecidas": dict[str, list[NoMemoria]],
        "contexto_local": list[NoMemoria],
        "reflexoes_recentes": list[NoMemoria],
        "resumo_contexto": str,
    }
    """
    contexto = {
        "memorias_relevantes": [],
        "pessoas_conhecidas": {},
        "contexto_local": [],
        "reflexoes_recentes": [],
        "resumo_contexto": "",
    }

    # 1. Recuperar memórias para cada percepção
    todas_memorias = []
    for percepcao in percepcoes:
        consulta = percepcao["descricao"]
        resultados = persona.memoria.recuperar(
            consulta=consulta,
            n=5,
            peso_relevancia=1.0,
            peso_recencia=0.8,
            peso_importancia=1.2,
            agora=hora_atual,
        )
        todas_memorias.extend(resultados)

    # Deduplicar e ordenar por score
    vistos = set()
    for mem, score in todas_memorias:
        if mem.id not in vistos:
            vistos.add(mem.id)
            contexto["memorias_relevantes"].append(mem)

    contexto["memorias_relevantes"] = contexto["memorias_relevantes"][:15]

    # 2. Recuperar memórias sobre pessoas presentes
    for percepcao in percepcoes:
        agente_nome = percepcao.get("agente_nome")
        if agente_nome:
            memorias_pessoa = persona.memoria.recuperar_por_participante(
                agente_nome, n=10
            )
            if memorias_pessoa:
                contexto["pessoas_conhecidas"][agente_nome] = memorias_pessoa

    # 3. Recuperar contexto do local
    local_atual = persona.rascunho.local_atual
    contexto["contexto_local"] = persona.memoria.recuperar_por_local(
        local_atual, n=10
    )

    # 4. Recuperar reflexões/pensamentos recentes
    contexto["reflexoes_recentes"] = persona.memoria.ultimas(
        n=5, tipos=["pensamento", "insight", "sintese"]
    )

    # 5. Compilar resumo textual do contexto
    linhas = []

    if contexto["memorias_relevantes"]:
        linhas.append("Memórias relevantes:")
        for m in contexto["memorias_relevantes"][:5]:
            linhas.append(f"  - {m.descricao[:100]}")

    if contexto["pessoas_conhecidas"]:
        linhas.append("Sobre as pessoas aqui:")
        for nome, mems in list(contexto["pessoas_conhecidas"].items())[:3]:
            ultima = mems[-1] if mems else None
            if ultima:
                linhas.append(f"  - {nome}: {ultima.descricao[:80]}")

    if contexto["reflexoes_recentes"]:
        linhas.append("Reflexões recentes:")
        for r in contexto["reflexoes_recentes"][:3]:
            linhas.append(f"  - {r.descricao[:100]}")

    contexto["resumo_contexto"] = "\n".join(linhas)

    return contexto
