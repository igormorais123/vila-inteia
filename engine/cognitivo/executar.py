"""
EXECUTAR - Módulo de Execução de Ações.

Traduz o plano do agente em ação concreta:
- Move para o local planejado
- Atualiza estado (energia, humor)
- Registra a ação na memória
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..persona import Persona

from ..campus import obter_local, calcular_distancia


def executar(
    persona: Persona,
    hora_atual: datetime,
) -> dict:
    """
    Executa a ação planejada.

    Retorna:
    {
        "descricao": str,
        "emoji": str,
        "local_id": str,
        "moveu": bool,
        "energia_delta": int,
    }
    """
    rascunho = persona.rascunho
    resultado = {
        "descricao": rascunho.acao.descricao,
        "emoji": rascunho.acao.emoji,
        "local_id": rascunho.local_atual,
        "moveu": False,
        "energia_delta": 0,
    }

    # 1. Verificar se precisa se mover
    local_planejado = rascunho.acao.local_id
    if local_planejado and local_planejado != rascunho.local_atual:
        distancia = calcular_distancia(rascunho.local_atual, local_planejado)
        if distancia >= 0:  # rota existe
            # Mover para o local
            rascunho.local_atual = local_planejado
            persona.memoria_espacial.registrar_visita(local_planejado, hora_atual)
            resultado["local_id"] = local_planejado
            resultado["moveu"] = True

            # Custo de energia por movimento
            custo = distancia * 2
            rascunho.atualizar_energia(-custo)
            resultado["energia_delta"] -= custo

    # 2. Atualizar energia baseado na atividade
    desc_lower = rascunho.acao.descricao.lower()

    if any(p in desc_lower for p in ["dorm", "descans", "medita"]):
        delta = 15  # recuperação
    elif any(p in desc_lower for p in ["debate", "apresent", "sala de guerra"]):
        delta = -8  # alto consumo
    elif any(p in desc_lower for p in ["trabalh", "pesquis", "estud"]):
        delta = -5  # consumo moderado
    elif any(p in desc_lower for p in ["café", "almoç", "jant"]):
        delta = 5  # leve recuperação
    elif any(p in desc_lower for p in ["caminh", "jardim", "terraço"]):
        delta = 3  # leve recuperação
    else:
        delta = -2  # consumo base

    rascunho.atualizar_energia(delta)
    resultado["energia_delta"] += delta

    # 3. Atualizar humor baseado em energia e atividade
    if rascunho.energia > 80:
        rascunho.humor = "energizado"
    elif rascunho.energia > 60:
        rascunho.humor = "focado"
    elif rascunho.energia > 40:
        rascunho.humor = "neutro"
    elif rascunho.energia > 20:
        rascunho.humor = "cansado"
    else:
        rascunho.humor = "exausto"

    # 4. Atualizar progresso da ação
    rascunho.acao.progresso = min(
        rascunho.acao.progresso + 0.2, 1.0
    )

    # 5. Registrar na memória se ação é significativa
    importancia = 3
    if resultado["moveu"]:
        importancia = 4
    if any(p in desc_lower for p in ["debate", "apresent", "reuni"]):
        importancia = 5

    local_info = obter_local(resultado["local_id"])
    local_nome = local_info.nome if local_info else resultado["local_id"]

    persona.memoria.adicionar_evento(
        descricao=f"{persona.nome_exibicao} está {rascunho.acao.descricao} em {local_nome}",
        sujeito=persona.nome_exibicao,
        predicado=rascunho.acao.descricao,
        objeto=local_nome,
        local_id=resultado["local_id"],
        importancia=importancia,
        palavras_chave=set(desc_lower.split()[:4]),
    )

    return resultado
