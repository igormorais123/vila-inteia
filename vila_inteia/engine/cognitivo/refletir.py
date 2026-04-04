"""
REFLETIR - Módulo de Reflexão.

Quando o agente acumula experiências suficientes, para e reflete.
Gera pensamentos de nível superior: insights, padrões, conclusões.

Diferente do Smallville, aqui a reflexão usa os frameworks mentais
do consultor e seus vieses conhecidos para gerar insights autênticos.
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..persona import Persona

from ..memoria.fluxo import NoMemoria


def refletir(
    persona: Persona,
    hora_atual: datetime,
    forcar: bool = False,
) -> list[dict]:
    """
    Gera reflexões/insights baseados em memórias acumuladas.

    Sem LLM (modo offline): usa heurísticas para gerar insights.
    Com LLM: envia contexto para gerar reflexões autênticas.

    Retorna lista de insights gerados:
    [
        {
            "tipo": "insight"|"sintese"|"pensamento",
            "descricao": str,
            "importancia": int,
            "evidencias": list[str],
            "ponto_focal": str,
        }
    ]
    """
    # Verificar se deve refletir
    if not forcar and not persona.memoria.deve_refletir():
        return []

    insights = []

    # 1. Encontrar pontos focais (temas mais importantes recentes)
    pontos_focais = persona.memoria.pontos_focais(n=3)

    for ponto in pontos_focais:
        # 2. Recuperar memórias sobre este ponto
        memorias, _ = zip(*persona.memoria.recuperar(
            consulta=ponto,
            n=10,
            peso_importancia=1.5,
            agora=hora_atual,
        )) if persona.memoria.recuperar(consulta=ponto, n=10, agora=hora_atual) else ([], [])

        if not memorias:
            continue

        # 3. Gerar insight baseado no perfil do consultor
        insight = _gerar_insight_heuristico(persona, ponto, list(memorias))

        if insight:
            insights.append(insight)

            # 4. Adicionar à memória como pensamento
            persona.memoria.adicionar_pensamento(
                descricao=insight["descricao"],
                importancia=insight["importancia"],
                evidencias=insight["evidencias"],
                palavras_chave=set(ponto.lower().split()),
            )

    # Resetar acumulador de importância
    persona.memoria.resetar_acumulador()
    persona.rascunho.ultima_reflexao = hora_atual
    persona.rascunho.reflexoes_hoje += 1

    return insights


def _gerar_insight_heuristico(
    persona: Persona,
    ponto_focal: str,
    memorias: list[NoMemoria],
) -> dict | None:
    """
    Gera insight sem LLM usando heurísticas baseadas no perfil.

    Aplica os frameworks mentais e vieses do consultor
    para criar reflexões autênticas.
    """
    if not memorias:
        return None

    d = persona.dados_consultor
    nome = persona.nome_exibicao

    # Extrair elementos das memórias
    pessoas_mencionadas = set()
    locais_mencionados = set()
    tipos_eventos = {"evento": 0, "conversa": 0, "pensamento": 0}

    for m in memorias:
        for p in m.participantes:
            pessoas_mencionadas.add(p)
        if m.local_id:
            locais_mencionados.add(m.local_id)
        if m.tipo in tipos_eventos:
            tipos_eventos[m.tipo] += 1

    # Frameworks mentais do consultor
    frameworks = d.get("frameworks_mentais", "")
    if isinstance(frameworks, list):
        frameworks = ", ".join(frameworks)

    estilo_pensamento = d.get("estilo_pensamento", "analítico")
    visao_futuro = d.get("visao_futuro", "")

    # Gerar insight baseado no padrão predominante
    evidencia_ids = [m.id for m in memorias[:5]]

    if tipos_eventos["conversa"] > tipos_eventos["evento"]:
        # Reflexão sobre interações sociais
        descricao = (
            f"{nome} reflete: Tenho interagido muito com "
            f"{', '.join(list(pessoas_mencionadas)[:3])}. "
            f"Usando meu framework de {frameworks[:50] or estilo_pensamento}, "
            f"percebo padrões interessantes nessas conversas sobre {ponto_focal}."
        )
        importancia = 7
    elif len(locais_mencionados) >= 3:
        # Reflexão sobre exploração do campus
        descricao = (
            f"{nome} observa: Tenho transitado por vários espaços do campus. "
            f"Cada local revela uma perspectiva diferente sobre {ponto_focal}. "
            f"Minha visão de futuro ({visao_futuro[:60] or 'pragmática'}) "
            f"me faz ver conexões que outros talvez não vejam."
        )
        importancia = 6
    elif tipos_eventos["pensamento"] >= 2:
        # Meta-reflexão (pensando sobre pensamentos)
        descricao = (
            f"{nome} sintetiza: Minhas reflexões recentes convergem para "
            f"{ponto_focal}. Como {persona.titulo}, "
            f"reconheço que este tema merece atenção aprofundada. "
            f"Preciso discutir isso com alguém qualificado."
        )
        importancia = 8
    else:
        # Reflexão geral
        descricao = (
            f"{nome} pondera: O tema '{ponto_focal}' tem me ocupado. "
            f"Com base em {len(memorias)} observações recentes e meu "
            f"estilo {estilo_pensamento}, vejo uma oportunidade de "
            f"contribuir com uma perspectiva única."
        )
        importancia = 6

    return {
        "tipo": "insight",
        "descricao": descricao,
        "importancia": importancia,
        "evidencias": evidencia_ids,
        "ponto_focal": ponto_focal,
    }


def gerar_reflexao_com_ia(
    persona: Persona,
    ponto_focal: str,
    memorias: list[NoMemoria],
) -> str:
    """
    Gera reflexão usando LLM (para uso futuro com OmniRoute).

    Retorna o texto da reflexão gerada.
    """
    # Prompt para gerar reflexão autêntica
    memorias_texto = "\n".join(
        f"- [{m.tipo}] {m.descricao}" for m in memorias[:10]
    )

    prompt = f"""Você é {persona.nome_exibicao}, "{persona.titulo}".

Com base nestas experiências recentes:
{memorias_texto}

Sobre o tema: {ponto_focal}

Gere UMA reflexão profunda e autêntica (2-3 frases) no estilo de {persona.nome_exibicao}.
Use o tom de voz: {persona.rascunho.tom_voz}
E os frameworks mentais: {persona.dados_consultor.get('frameworks_mentais', 'N/A')}

A reflexão deve revelar um insight não-óbvio."""

    # TODO: Integrar com OmniRoute quando disponível
    return prompt
