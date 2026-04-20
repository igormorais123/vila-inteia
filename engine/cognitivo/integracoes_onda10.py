"""
Bridge opcional: plug-ins Onda 10 para o ciclo cognitivo existente.

Funções nesta camada NÃO alteram o fluxo atual de perceber→...→executar.
Em vez disso, são chamadas opcionais que quem quiser pode acoplar
no pipeline sem risco de quebrar simulações existentes.

Uso típico (Onda 10.2+):
    from engine.cognitivo.integracoes_onda10 import (
        analise_estrategica_para_planejamento,
        atualizar_crenca_pos_conversa,
        distribuir_shapley_pos_desafio,
    )
"""

from __future__ import annotations

from typing import Any

import numpy as np

from engine.game_theory.equilibrio import nash_puro, best_response
from engine.game_theory.bem_comum import public_goods_game
from engine.opinion_dynamics.degroot import degroot_step, matriz_confianca_vila
from engine.opinion_dynamics.bounded_confidence import deffuant_step
from engine.simulacao_avancada.coalizoes import shapley_value


def analise_estrategica_para_planejamento(
    payoffs_persona: np.ndarray,
    estrategia_outros: np.ndarray | None = None,
) -> dict[str, Any]:
    """
    Chamada em cognitivo.planejar quando contexto é estratégico (desafio ativo).

    Retorna dict com:
      - recomendacao_estrategia: índice da estratégia ótima (puro ou best-response)
      - equilibrios_encontrados: lista de NE (se jogo for 2-player)

    payoffs_persona: shape (m, n) matriz de payoffs desta persona
    estrategia_outros: shape (n,) distribuição de estratégias dos outros agentes (opcional)
    """
    resultado: dict[str, Any] = {}
    if estrategia_outros is not None:
        resultado["recomendacao_estrategia"] = best_response(payoffs_persona, estrategia_outros)
    else:
        # assumir uniforme como prior
        n = payoffs_persona.shape[1]
        resultado["recomendacao_estrategia"] = best_response(payoffs_persona, np.ones(n) / n)
    return resultado


def atualizar_crenca_pos_conversa(
    crenca_atual: float,
    crenca_do_parceiro: float,
    influencia: float = 0.3,
    epsilon: float = 0.5,
) -> float:
    """
    Chamar após cognitivo.conversar: atualiza crença da persona sobre tópico.

    Usa Deffuant simplificado: só atualiza se diferença < epsilon.
    influencia = peso da crença alheia (0 a 0.5)
    """
    if abs(crenca_atual - crenca_do_parceiro) >= epsilon:
        return crenca_atual
    return crenca_atual + influencia * (crenca_do_parceiro - crenca_atual)


def atualizar_crencas_grupo_degroot(
    crencas: dict[str, float],
    relacoes: dict[str, dict[str, str]],
) -> dict[str, float]:
    """
    Atualização DeGroot síncrona: cada agente pondera crenças dos outros por reputação.
    Retorna novo dict de crenças.
    """
    if not crencas:
        return {}
    habitantes = [{"id": aid} for aid in crencas.keys()]
    W = matriz_confianca_vila(habitantes, relacoes)
    x0 = np.array([crencas[aid] for aid in crencas.keys()])
    x1 = degroot_step(x0, W)
    return {aid: float(x1[i]) for i, aid in enumerate(crencas.keys())}


def distribuir_shapley_pos_desafio(
    contribuintes: list[str],
    medicao_coalizao: callable,
) -> dict[str, float]:
    """
    Chamar ao concluir um DesafioColetivo para distribuir crédito.

    medicao_coalizao(coal) deve retornar o valor gerado por aquela coalizão
    (pode ser: quantidade de contribuições aprovadas, pontos agregados, etc.)
    """
    return shapley_value(contribuintes, medicao_coalizao)


def avaliar_contribuicoes_desafio_como_public_goods(
    dotacoes: dict[str, float],
    contribuicoes_reais: dict[str, float],
    mpcr: float = 0.5,
) -> dict:
    """
    Modela desafio coletivo como public goods game.
    Revela se free-riding está acontecendo e qual é a eficiência.
    """
    r = public_goods_game(dotacoes, contribuicoes_reais, mpcr)
    free_riders = [a for a, c in contribuicoes_reais.items() if c == 0]
    return {
        "eficiencia": r.eficiencia,
        "total_pool": r.total_pool,
        "free_riders": free_riders,
        "payoffs": r.payoffs_individuais,
    }


def recomendar_reputacao_via_influencia(
    posts: list[dict],    # [{autor_id, engajamento}]
    agentes: list[str],
) -> dict[str, float]:
    """
    Simples: influence score = engajamento total agregado por autor, normalizado.
    (Versão simples de Nowak-Latane; versão Onda 10.2 usará social_impact.impacto_social.)
    """
    scores = {a: 0.0 for a in agentes}
    for p in posts:
        if p["autor_id"] in scores:
            scores[p["autor_id"]] += float(p.get("engajamento", 0))
    total = sum(scores.values()) or 1
    return {a: v / total for a, v in scores.items()}
