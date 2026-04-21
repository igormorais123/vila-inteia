"""
Onda 130: adversarial prompt (devil's advocate).

Pergunta mesma query duas vezes com framing oposto:
1. "Qual a probabilidade do outcome=1?"
2. "Qual a probabilidade do outcome=0 (não acontecer)?"

Se LLM é consistente: P_1 + P_0 ≈ 1.0. Se anchor bias:
P_1 ≠ 1 - P_0. Agregado: (P_1 + (1 - P_0)) / 2 cancela viés.

Reduz anchor bias LLM que sempre infla P(default framing).
"""

from __future__ import annotations

import logging
from typing import Any, Callable

logger = logging.getLogger(__name__)


def consulta_adversarial(
    contexto: str,
    persona_id: str,
    sim: Any,
    llm_fn: Callable | None = None,
    chain_of_thought: bool = True,
    few_shot_exemplos: list[dict] | None = None,
) -> dict:
    """
    Executa 2 queries opostas + agregado debias.
    Retorna {prob_positiva, prob_negativa_invertida, prob_debias, consistencia}.
    """
    from engine.persona_chat import chat_com_persona
    from engine.backtest_real import (
        extrair_probabilidade, _build_few_shot_block, _build_cot_prefix,
    )

    few_shot = _build_few_shot_block(few_shot_exemplos)
    cot = _build_cot_prefix() if chain_of_thought else ""

    # Pergunta 1: outcome=1 ACONTECEU
    p1_prompt = (
        f"Analise o evento: \"{contexto}\"\n\n"
        f"Pergunta: qual probabilidade (0-100%) do resultado principal "
        f"ter ACONTECIDO?" + few_shot + cot
    )
    r1 = chat_com_persona(persona_id=persona_id, pergunta=p1_prompt, sim=sim,
                           llm_fn=llm_fn, max_tokens=250, temperatura=0.4)
    p1 = extrair_probabilidade(r1.get("resposta") or "")

    # Pergunta 2: outcome=0 NÃO ACONTECEU (framing oposto)
    p2_prompt = (
        f"Analise o evento: \"{contexto}\"\n\n"
        f"Pergunta: qual probabilidade (0-100%) do resultado principal "
        f"NÃO ter acontecido (ter sido rejeitado/fracassado)?"
        + few_shot + cot
    )
    r2 = chat_com_persona(persona_id=persona_id, pergunta=p2_prompt, sim=sim,
                           llm_fn=llm_fn, max_tokens=250, temperatura=0.4)
    p2 = extrair_probabilidade(r2.get("resposta") or "")

    # Agregado debias
    if p1 is None and p2 is None:
        prob_debias = None
    elif p1 is None:
        prob_debias = 1.0 - p2
    elif p2 is None:
        prob_debias = p1
    else:
        # (P_1 + (1 - P_0)) / 2 debias
        prob_debias = (p1 + (1.0 - p2)) / 2
    consistencia = (
        1.0 - abs((p1 or 0.5) + (p2 or 0.5) - 1.0)
        if (p1 is not None and p2 is not None) else None
    )

    return {
        "persona_id": persona_id,
        "prob_positiva": p1,
        "prob_negativa": p2,
        "prob_negativa_invertida": (1.0 - p2) if p2 is not None else None,
        "prob_debias": prob_debias,
        "consistencia": consistencia,
        "resposta_positiva": (r1.get("resposta") or "")[:200],
        "resposta_negativa": (r2.get("resposta") or "")[:200],
        "erro": r1.get("erro") or r2.get("erro"),
    }


def panel_adversarial(
    contexto: str,
    persona_ids: list[str],
    sim: Any,
    llm_fn: Callable | None = None,
    chain_of_thought: bool = True,
    few_shot_exemplos: list[dict] | None = None,
    pesos_persona: dict[str, float] | None = None,
) -> dict:
    """Panel completo com adversarial per-persona."""
    from engine.backtest_real import _agregar_ponderado

    per_persona = []
    for pid in persona_ids:
        adv = consulta_adversarial(
            contexto, pid, sim, llm_fn=llm_fn,
            chain_of_thought=chain_of_thought,
            few_shot_exemplos=few_shot_exemplos,
        )
        per_persona.append({
            "persona_id": pid,
            "persona_nome": sim.personas.get(pid).nome_exibicao
                if pid in getattr(sim, "personas", {}) else pid,
            "prob_extraida": adv["prob_debias"],
            "resposta": f"pos={adv['prob_positiva']} neg={adv['prob_negativa']} debias={adv['prob_debias']}",
            "erro": adv.get("erro"),
            "adversarial": adv,
        })

    agregado = _agregar_ponderado(per_persona, pesos_persona)
    n_validas = sum(1 for p in per_persona if p.get("prob_extraida") is not None)
    # Consistência média (quão coerente LLM entre framings)
    consistencias = [p["adversarial"]["consistencia"] for p in per_persona
                      if p["adversarial"].get("consistencia") is not None]
    return {
        "prob_agregada": agregado,
        "n_respostas_validas": n_validas,
        "n_personas": len(persona_ids),
        "per_persona": per_persona,
        "consistencia_media": sum(consistencias) / len(consistencias) if consistencias else None,
    }
