"""
PERCEBER - Módulo de Percepção.

O agente observa o ambiente: quem está no mesmo local,
o que estão fazendo, e eventos recentes.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from ..persona import Persona

from ..campus import obter_local, obter_conexoes


def perceber(
    persona: Persona,
    mundo: Any,
    personas: dict[str, "Persona"],
    hora_atual: datetime,
) -> list[dict]:
    """
    Percebe o ambiente ao redor.

    Retorna lista de percepções:
    [
        {
            "tipo": "presenca"|"acao"|"evento"|"ambiente",
            "agente_id": str | None,
            "agente_nome": str | None,
            "descricao": str,
            "local_id": str,
            "importancia": int (1-10),
        }
    ]
    """
    percepcoes = []
    local_atual = persona.rascunho.local_atual
    max_percepcoes = 5 + (persona.rascunho.nivel_extroversao // 3)

    # 1. Perceber quem está no mesmo local
    for pid, outra in personas.items():
        if pid == persona.id:
            continue
        if outra.rascunho.local_atual != local_atual:
            continue
        if not outra.ativo:
            continue

        # Registrar presença na memória espacial
        persona.memoria_espacial.registrar_presenca(
            agente_id=outra.id,
            agente_nome=outra.nome_exibicao,
            local_id=local_atual,
            acao=outra.rascunho.acao.descricao,
            quando=hora_atual,
        )

        # Calcular importância da percepção
        importancia = 3  # base
        if outra.nome_exibicao in persona.rascunho.mentores:
            importancia = 8
        elif outra.nome_exibicao in persona.rascunho.rivais:
            importancia = 7
        elif outra.nome_exibicao in persona.rascunho.influenciado_por:
            importancia = 6
        elif outra.categoria == persona.categoria:
            importancia = 5

        percepcoes.append({
            "tipo": "presenca",
            "agente_id": outra.id,
            "agente_nome": outra.nome_exibicao,
            "descricao": (
                f"{outra.nome_exibicao} está aqui, "
                f"{outra.rascunho.acao.emoji} {outra.rascunho.acao.descricao}"
            ),
            "local_id": local_atual,
            "importancia": importancia,
        })

    # 2. Perceber o local em si
    local_info = obter_local(local_atual)
    if local_info:
        percepcoes.append({
            "tipo": "ambiente",
            "agente_id": None,
            "agente_nome": None,
            "descricao": f"Estou em {local_info.nome}: {local_info.descricao[:100]}",
            "local_id": local_atual,
            "importancia": 2,
        })

    # 3. Perceber locais adjacentes (quem está por perto)
    if persona.rascunho.raio_percepcao > 0:
        conexoes = obter_conexoes(local_atual)
        for vizinho in conexoes:
            presentes = sum(
                1 for p in personas.values()
                if p.rascunho.local_atual == vizinho.id and p.id != persona.id
            )
            if presentes > 0:
                percepcoes.append({
                    "tipo": "ambiente",
                    "agente_id": None,
                    "agente_nome": None,
                    "descricao": (
                        f"No {vizinho.nome} próximo, há {presentes} "
                        f"pessoa{'s' if presentes > 1 else ''}"
                    ),
                    "local_id": vizinho.id,
                    "importancia": 2,
                })

    # 4. Perceber conversas em andamento no local
    for pid, outra in personas.items():
        if pid == persona.id:
            continue
        if outra.rascunho.local_atual != local_atual:
            continue
        if outra.rascunho.esta_conversando:
            parceiro = outra.rascunho.conversando_com
            parceiro_nome = "alguém"
            if parceiro and parceiro in personas:
                parceiro_nome = personas[parceiro].nome_exibicao

            percepcoes.append({
                "tipo": "evento",
                "agente_id": outra.id,
                "agente_nome": outra.nome_exibicao,
                "descricao": (
                    f"{outra.nome_exibicao} está conversando com {parceiro_nome}"
                ),
                "local_id": local_atual,
                "importancia": 4,
            })

    # Registrar percepções mais importantes na memória
    percepcoes.sort(key=lambda p: p["importancia"], reverse=True)
    percepcoes = percepcoes[:max_percepcoes]

    for p in percepcoes:
        if p["importancia"] >= 4:  # só memorizar percepções significativas
            persona.memoria.adicionar_evento(
                descricao=p["descricao"],
                sujeito=p.get("agente_nome", "ambiente"),
                predicado="percebido por",
                objeto=persona.nome_exibicao,
                local_id=p["local_id"],
                importancia=p["importancia"],
                palavras_chave=set(p["descricao"].lower().split()[:5]),
            )

    return percepcoes
