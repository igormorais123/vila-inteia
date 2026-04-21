"""
Onda 128: self-consistency via multi-sample temperature.

Wang et al 2022 (Self-Consistency): mesma query N vezes com temperaturas
variadas, agregar via média ou maj vote. Reduz variance do LLM.

Uso: pra cada persona, chama N vezes com [0.3, 0.5, 0.7, 0.9],
agregado = median das 4 amostras. Brier tipicamente cai 5-10%.
"""

from __future__ import annotations

import logging
from statistics import median, stdev
from typing import Any, Callable

logger = logging.getLogger(__name__)


def sample_multipla(
    persona_id: str,
    pergunta: str,
    sim: Any,
    llm_fn: Callable,
    n_samples: int = 3,
    temperaturas: list[float] | None = None,
) -> dict:
    """
    N chamadas LLM com temperaturas variadas.
    Retorna dict com samples + agregado (median).
    """
    from engine.persona_chat import chat_com_persona
    from engine.backtest_real import extrair_probabilidade

    if temperaturas is None:
        # Default: [0.3, 0.5, 0.7] ou [0.2, 0.5, 0.8, 1.0] se n_samples=4
        if n_samples <= 3:
            temperaturas = [0.3, 0.5, 0.7][:n_samples]
        else:
            temperaturas = [0.2 + (i / max(n_samples-1, 1)) * 0.7
                             for i in range(n_samples)]

    samples: list[dict] = []
    probs: list[float] = []
    for i, temp in enumerate(temperaturas[:n_samples]):
        resp = chat_com_persona(
            persona_id=persona_id, pergunta=pergunta, sim=sim,
            llm_fn=llm_fn, max_tokens=250, temperatura=temp,
        )
        texto = resp.get("resposta") or ""
        p = extrair_probabilidade(texto)
        samples.append({
            "temperatura": temp,
            "resposta": texto[:200],
            "prob_extraida": p,
            "erro": resp.get("erro"),
        })
        if p is not None:
            probs.append(p)

    return {
        "persona_id": persona_id,
        "n_samples": len(samples),
        "n_validas": len(probs),
        "samples": samples,
        "prob_mediana": median(probs) if probs else None,
        "prob_media": sum(probs) / len(probs) if probs else None,
        "std_desvio": stdev(probs) if len(probs) >= 2 else 0.0,
    }


def consultar_panel_self_consistency(
    contexto: str,
    persona_ids: list[str],
    sim: Any,
    llm_fn: Callable | None = None,
    n_samples_por_persona: int = 3,
    temperaturas: list[float] | None = None,
    pesos_persona: dict[str, float] | None = None,
    chain_of_thought: bool = True,
    few_shot_exemplos: list[dict] | None = None,
) -> dict:
    """
    Panel + self-consistency. N samples por persona com temperaturas diferentes.
    Agregado final = weighted median das median per-persona.
    """
    from engine.backtest_real import (
        _build_few_shot_block, _build_cot_prefix, _agregar_ponderado,
    )

    few_shot = _build_few_shot_block(few_shot_exemplos)
    if chain_of_thought:
        pergunta = (
            f"Analise o seguinte evento: \"{contexto}\"\n\n"
            f"Pergunta: qual a probabilidade (0% a 100%) do resultado "
            f"principal associado acontecer/ter acontecido?"
            + few_shot
            + _build_cot_prefix()
        )
    else:
        pergunta = (
            f"Analise o seguinte evento: \"{contexto}\"\n\n"
            f"Pergunta: qual probabilidade (%) do outcome? "
            f"Responda com N%." + few_shot
        )

    per_persona: list[dict] = []
    for pid in persona_ids:
        sc = sample_multipla(
            persona_id=pid, pergunta=pergunta, sim=sim, llm_fn=llm_fn,
            n_samples=n_samples_por_persona, temperaturas=temperaturas,
        )
        # Converte pra per_persona formato compatível com _agregar_ponderado
        per_persona.append({
            "persona_id": pid,
            "persona_nome": sim.personas.get(pid).nome_exibicao
                if pid in getattr(sim, "personas", {}) else pid,
            "prob_extraida": sc["prob_mediana"],  # median over N samples
            "resposta": f"[{sc['n_validas']}/{sc['n_samples']} samples, median={sc['prob_mediana']}]",
            "erro": None,
            "self_consistency": sc,
        })

    agregado = _agregar_ponderado(per_persona, pesos_persona)
    n_validas = sum(1 for p in per_persona if p.get("prob_extraida") is not None)
    return {
        "prob_agregada": agregado,
        "n_respostas_validas": n_validas,
        "n_personas": len(persona_ids),
        "n_samples_por_persona": n_samples_por_persona,
        "per_persona": per_persona,
    }
