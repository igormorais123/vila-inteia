"""
Onda 124: multi-step debate entre personas.

Motivação: se panel discorda muito (std > threshold), executa round 2
onde cada persona vê as outras respostas + pode revisar. Aplica
Aumann agreement theorem — common knowledge de opinions diverge → converge.

Função principal:
    debate_panel(contexto, persona_ids, sim, ...) -> dict similar ao
    consultar_panel mas com rounds múltiplos se discordância alta.
"""

from __future__ import annotations

import logging
from statistics import stdev, mean
from typing import Any

logger = logging.getLogger(__name__)


def _dispersao(probs: list[float]) -> float:
    if len(probs) < 2:
        return 0.0
    return stdev(probs)


def _format_round1_block(per_persona: list[dict]) -> str:
    """Lista respostas do round 1 pra feed no round 2."""
    linhas = ["Respostas do primeiro round do painel:"]
    for p in per_persona:
        nome = p.get("persona_nome", p.get("persona_id", "?"))
        prob = p.get("prob_extraida")
        if prob is None:
            continue
        resposta = (p.get("resposta", "") or "")[:180]
        linhas.append(f"- {nome} disse {int(prob*100)}%: \"{resposta}\"")
    linhas.append("")
    linhas.append(
        "Agora, considerando todas opiniões acima, revise SUA própria "
        "estimativa. Se discordar, justifique brevemente. "
        "Use formato RACIOCÍNIO: ... PROBABILIDADE FINAL: N%"
    )
    return "\n".join(linhas)


def debate_panel(
    contexto: str,
    persona_ids: list[str],
    sim: Any,
    llm_fn=None,
    few_shot_exemplos: list[dict] | None = None,
    pesos_persona: dict[str, float] | None = None,
    dispersao_threshold: float = 0.15,
    max_rounds: int = 2,
    chain_of_thought: bool = True,
) -> dict:
    """
    Round 1: consultar_panel padrão.
    Se std(probs) > threshold, round 2: mostrar respostas e pedir revisão.
    max_rounds=2 default.

    Returns dict similar ao consultar_panel + histórico de rounds.
    """
    from engine.backtest_real import consultar_panel, _agregar_ponderado

    rounds = []
    r1 = consultar_panel(
        contexto=contexto, persona_ids=persona_ids, sim=sim, llm_fn=llm_fn,
        few_shot_exemplos=few_shot_exemplos, pesos_persona=pesos_persona,
        chain_of_thought=chain_of_thought,
    )
    rounds.append(r1)

    probs_r1 = [p["prob_extraida"] for p in r1["per_persona"]
                if p.get("prob_extraida") is not None]
    disp = _dispersao(probs_r1)
    if disp <= dispersao_threshold or max_rounds < 2:
        return {
            **r1,
            "n_rounds": 1,
            "dispersao_inicial": disp,
            "rounds": rounds,
        }

    # Round 2: contexto com respostas anteriores
    logger.debug(f"Debate round 2 disparado: disp={disp:.3f} > {dispersao_threshold}")
    r1_block = _format_round1_block(r1["per_persona"])
    contexto_r2 = f"{contexto}\n\n{r1_block}"
    r2 = consultar_panel(
        contexto=contexto_r2, persona_ids=persona_ids, sim=sim, llm_fn=llm_fn,
        few_shot_exemplos=few_shot_exemplos, pesos_persona=pesos_persona,
        chain_of_thought=chain_of_thought,
    )
    rounds.append(r2)

    probs_r2 = [p["prob_extraida"] for p in r2["per_persona"]
                if p.get("prob_extraida") is not None]
    disp_r2 = _dispersao(probs_r2)

    return {
        **r2,  # último round = decisão final
        "n_rounds": 2,
        "dispersao_inicial": disp,
        "dispersao_final": disp_r2,
        "convergiu": disp_r2 < disp,
        "rounds": rounds,
    }
