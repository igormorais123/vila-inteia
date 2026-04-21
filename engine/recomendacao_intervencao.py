"""
Onda 80: recomendacao-intervencao — sweep multi-counterfactual.

Para cada intervenção possível (forçar cada estado psico-histórico),
mede impacto sobre outcome desejado (default: equilibrio).
LLM ranqueia + recomenda melhor ação para Helena/Efesto.

Diferencial vs MiroFish: MiroFish prevê 1 cenário. Vila avalia TODOS
os cenários do-operator + recomendação acionável.
"""

from __future__ import annotations

from typing import Any
import logging

import numpy as np

logger = logging.getLogger(__name__)


def _gerar_recomendacao_llm(payload: dict, llm_fn=None) -> str | None:
    if llm_fn is None:
        try:
            from engine.ia_client import chamar_llm
            llm_fn = chamar_llm
        except Exception:
            return None

    estado_atual = payload["estado_atual"]
    outcome = payload["outcome_desejado"]
    horizonte = payload["horizonte"]
    ranking = payload["ranking"]

    linhas_rank = "\n".join(
        f"  {i+1}. forçar '{r['estado']}' → P({outcome})={r['prob_outcome']*100:.1f}% "
        f"(top final: {r['estado_mais_provavel']} {r['prob_mais_provavel']*100:.1f}%)"
        for i, r in enumerate(ranking[:5])
    )

    prompt = (
        f"Vila INTEIA está em '{estado_atual}'. Outcome desejado: '{outcome}' "
        f"em {horizonte} steps. Sweep de intervenções (ranqueado por P(outcome)):\n"
        f"{linhas_rank}\n\n"
        f"Recomende em PT-BR (3-5 frases): qual intervenção Helena/Efesto deveriam "
        f"executar para maximizar '{outcome}', e quais riscos. Cite top-2 escolhas e "
        f"compare custo de implementação."
    )

    try:
        kwargs = dict(
            mensagens=[{"role": "user", "content": prompt}],
            modelo="rapido", max_tokens=400, temperatura=0.6,
        )
        try:
            resp = llm_fn(**kwargs, bypass_step_cap=True)
        except TypeError:
            resp = llm_fn(**kwargs)
        return resp.strip() if resp else None
    except Exception as e:
        logger.debug(f"recomendacao LLM falhou: {e}")
        return None


def gerar_recomendacao(
    outcome_desejado: str = "equilibrio",
    horizonte: int = 20,
    rastreador: Any | None = None,
    com_recomendacao_llm: bool = True,
    llm_fn=None,
) -> dict:
    """
    Sweep todas intervenções possíveis no grafo psico-histórico canônico.

    Returns dict:
        estado_atual, outcome_desejado, horizonte,
        ranking (lista ordenada de intervenções),
        melhor_intervencao (top-1),
        recomendacao_llm (opcional)
    """
    if rastreador is None:
        from engine.psicohistoria.detector_estado_vila import RASTREADOR_GLOBAL
        rastreador = RASTREADOR_GLOBAL

    from engine.psicohistoria.grafo_eventos import construir_grafo_vila
    from engine.causalidade.pearl import intervention_sweep

    grafo = construir_grafo_vila()
    estados_ordem = list(grafo.estados.keys())

    if outcome_desejado not in grafo.estados:
        raise ValueError(
            f"outcome_desejado '{outcome_desejado}' desconhecido. "
            f"Válidos: {estados_ordem}"
        )

    estado_atual = (
        rastreador.trajetoria.ultimo_estado()
        if rastreador.trajetoria.estados else "bootstrap"
    )

    idx_outcome = grafo.estado_para_index(outcome_desejado)
    resultados = intervention_sweep(grafo.matriz, idx_outcome, horizonte=horizonte)

    ranking = []
    for r in resultados:
        prob_outcome = float(r.probabilidades_finais[idx_outcome])
        ranking.append({
            "estado": estados_ordem[r.estado_forcado],
            "prob_outcome": prob_outcome,
            "estado_mais_provavel": estados_ordem[r.estado_mais_provavel],
            "prob_mais_provavel": float(r.prob_mais_provavel),
        })

    melhor = ranking[0] if ranking else None

    payload = {
        "estado_atual": estado_atual,
        "outcome_desejado": outcome_desejado,
        "horizonte": horizonte,
        "ranking": ranking,
        "melhor_intervencao": melhor,
        "estados_ordem": estados_ordem,
    }

    if com_recomendacao_llm:
        rec = _gerar_recomendacao_llm(payload, llm_fn=llm_fn)
        if rec:
            payload["recomendacao_llm"] = rec

    return payload
