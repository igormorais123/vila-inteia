"""
PLANEJAR - Módulo de Planejamento.

Gera planos diários e decide a próxima ação do agente.
Planejamento hierárquico: dia → hora → ação atômica.

Diferente do Smallville que usa LLM para cada decisão,
aqui usamos heurísticas inteligentes + LLM para refinamento.
"""

from __future__ import annotations

import random
from datetime import datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..persona import Persona

from ..memoria.rascunho import PlanoItem
from ..campus import (
    obter_local, obter_todos_locais, locais_abertos,
    obter_conexoes, residencia_para_categoria,
)


# Planos-base por período do dia
ATIVIDADES_PADRAO = {
    "madrugada": [  # 0-5
        ("dormindo", "residencia", 360),
    ],
    "manha_cedo": [  # 6-7
        ("acordando e se preparando", "residencia", 30),
        ("tomando café da manhã", "refeitorio", 45),
    ],
    "manha": [  # 8-11
        ("estudando e pesquisando", "biblioteca", 90),
        ("trabalhando em projetos", "laboratorio", 90),
        ("participando de reunião estratégica", "torre_estrategia", 60),
        ("debatendo ideias", "arena_debates", 60),
        ("conversando no café", "cafe_filosofos", 45),
    ],
    "almoco": [  # 12-13
        ("almoçando", "refeitorio", 60),
        ("conversando durante o almoço", "refeitorio", 45),
    ],
    "tarde": [  # 14-17
        ("apresentando no auditório", "auditorio", 90),
        ("trabalhando no laboratório", "laboratorio", 60),
        ("debatendo no tribunal", "tribunal", 60),
        ("analisando cenários", "sala_guerra", 60),
        ("criando no ateliê", "atelie", 60),
        ("observando tendências", "observatorio", 45),
    ],
    "fim_tarde": [  # 17-19
        ("caminhando pelo jardim", "jardim_visionarios", 30),
        ("networking no terraço", "terraco", 45),
        ("conversando na ágora", "agora", 40),
    ],
    "noite": [  # 19-22
        ("jantando", "refeitorio", 60),
        ("debate noturno na ágora", "agora", 60),
        ("refletindo no observatório", "observatorio", 45),
        ("lendo na biblioteca", "biblioteca", 60),
        ("socializando no café", "cafe_filosofos", 45),
    ],
    "noite_tarde": [  # 22-23
        ("se recolhendo para dormir", "residencia", 30),
    ],
}


def _periodo_do_dia(hora: int) -> str:
    """Retorna o período do dia baseado na hora."""
    if hora < 6:
        return "madrugada"
    if hora < 8:
        return "manha_cedo"
    if hora < 12:
        return "manha"
    if hora < 14:
        return "almoco"
    if hora < 17:
        return "tarde"
    if hora < 19:
        return "fim_tarde"
    if hora < 22:
        return "noite"
    return "noite_tarde"


def _escolher_atividade(
    persona: Persona,
    periodo: str,
    hora: int,
) -> tuple[str, str, int]:
    """
    Escolhe uma atividade para o agente baseado em:
    - Período do dia
    - Categoria/personalidade do agente
    - Nível de energia
    - Extroversão
    """
    atividades = ATIVIDADES_PADRAO.get(periodo, [])
    if not atividades:
        return ("observando o campus", "agora", 30)

    # Filtrar por locais abertos
    abertos = {l.id for l in locais_abertos(hora)}
    atividades_validas = [
        a for a in atividades if a[1] in abertos or a[1] == "residencia"
    ]
    if not atividades_validas:
        atividades_validas = atividades

    # Ponderar por afinidade de categoria
    pesos = []
    for desc, local_id, duracao in atividades_validas:
        local = obter_local(local_id)
        peso = 1.0
        if local:
            afinidade = local.afinidade_consultor([persona.categoria])
            peso += afinidade * 3

            # Boost por personalidade
            if local.nivel_energia >= 7 and persona.rascunho.nivel_extroversao >= 7:
                peso += 1.0
            if local.nivel_energia <= 3 and persona.rascunho.nivel_extroversao <= 4:
                peso += 0.8
            if local.nivel_formalidade >= 7 and persona.rascunho.nivel_formalidade >= 7:
                peso += 0.5

        # Energia baixa → preferir atividades calmas
        if persona.rascunho.energia < 40:
            if local_id in ("biblioteca", "jardim_visionarios", "cafe_filosofos"):
                peso += 1.5
            elif local_id in ("arena_debates", "sala_guerra"):
                peso *= 0.3

        pesos.append(peso)

    # Seleção ponderada
    total = sum(pesos)
    if total == 0:
        return random.choice(atividades_validas)

    r = random.random() * total
    acumulado = 0
    for i, peso in enumerate(pesos):
        acumulado += peso
        if r <= acumulado:
            return atividades_validas[i]

    return atividades_validas[-1]


def gerar_plano_diario(persona: Persona, hora_atual: datetime) -> list[PlanoItem]:
    """Gera o plano diário do agente."""
    plano = []

    # Hora de acordar baseada na personalidade
    hora_acordar = 6
    if persona.rascunho.nivel_extroversao <= 3:
        hora_acordar = 5  # introvertidos acordam cedo
    elif persona.rascunho.nivel_extroversao >= 8:
        hora_acordar = 7  # extrovertidos dormem mais

    residencia = residencia_para_categoria(persona.categoria)

    # Montar plano hora a hora
    hora = hora_acordar
    while hora < 23:
        periodo = _periodo_do_dia(hora)
        desc, local_id, duracao = _escolher_atividade(persona, periodo, hora)

        # Substituir "residencia" pelo local real
        if local_id == "residencia":
            local_id = residencia

        plano.append(PlanoItem(
            descricao=desc,
            hora_inicio=f"{hora:02d}:00",
            duracao_minutos=duracao,
            local_id=local_id,
            prioridade=5,
        ))

        hora += max(duracao // 60, 1)

    # Dormir
    plano.append(PlanoItem(
        descricao="dormindo",
        hora_inicio="23:00",
        duracao_minutos=420,
        local_id=residencia,
        prioridade=1,
    ))

    return plano


def planejar(
    persona: Persona,
    contexto: dict,
    hora_atual: datetime,
) -> dict:
    """
    Decide a próxima ação do agente.

    Prioridades:
    1. Se está em conversa → continuar
    2. Se tem plano diário → seguir plano
    3. Se não tem plano → gerar plano
    4. Ajuste dinâmico por percepções
    """
    resultado = {
        "acao": "observando",
        "local_id": persona.rascunho.local_atual,
        "duracao": 30,
    }

    # Se está conversando, não replanejar
    if persona.rascunho.esta_conversando:
        return resultado

    hora = hora_atual.hour

    # Gerar plano diário se não existe
    if not persona.rascunho.plano_diario:
        persona.rascunho.plano_diario = gerar_plano_diario(persona, hora_atual)

    # Encontrar item do plano para hora atual
    for item in persona.rascunho.plano_diario:
        hora_item = int(item.hora_inicio.split(":")[0])
        fim_item = hora_item + max(item.duracao_minutos // 60, 1)
        if hora_item <= hora < fim_item and not item.concluido:
            resultado["acao"] = item.descricao
            resultado["local_id"] = item.local_id
            resultado["duracao"] = item.duracao_minutos

            # Ajuste dinâmico: se há alguém interessante no local,
            # pode estender a duração
            memorias_relevantes = contexto.get("memorias_relevantes", [])
            if memorias_relevantes:
                resultado["duracao"] = int(resultado["duracao"] * 1.2)

            break
    else:
        # Sem plano para essa hora → atividade genérica
        periodo = _periodo_do_dia(hora)
        desc, local_id, duracao = _escolher_atividade(persona, periodo, hora)
        if local_id == "residencia":
            local_id = residencia_para_categoria(persona.categoria)
        resultado["acao"] = desc
        resultado["local_id"] = local_id
        resultado["duracao"] = duracao

    # Atualizar rascunho
    persona.rascunho.atualizar_acao(
        descricao=resultado["acao"],
        local_id=resultado["local_id"],
        duracao=resultado["duracao"],
    )

    return resultado
