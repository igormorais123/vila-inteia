"""
Onda 126: ensemble final pra máxima accuracy.

Combina Ondas 121-125:
- Few-shot walk-forward (121)
- Weighted ensemble per-persona (122)
- Chain-of-thought (123)
- Multi-step debate (124)
- Bayesian blend com base rate (125)
- Platt calibration runtime (97)

rodar_backtest_acc: entry point single pra accuracy máxima.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


def rodar_backtest_acc(
    dataset_path: str | Path,
    sim: Any,
    persona_ids: list[str] | None = None,
    llm_fn=None,
    max_eventos: int | None = None,
    sleep_entre_eventos_s: float = 0.0,
    # Onda 121: few-shot
    few_shot_k: int = 2,
    # Onda 122: weighted
    pesos_persona: dict[str, float] | None = None,
    # Onda 123: CoT
    chain_of_thought: bool = True,
    # Onda 124: debate
    usar_debate: bool = True,
    dispersao_threshold: float = 0.15,
    max_rounds: int = 2,
    # Onda 125: Bayesian
    usar_bayesian_blend: bool = True,
    peso_vila: float = 0.7,
    # Onda 97: Platt runtime
    aplicar_platt: bool = True,
) -> dict:
    """
    Full-stack accuracy backtest.
    Cada feature pode ser desabilitada via flag.

    Returns dict similar a rodar_backtest + campos extras.
    """
    from engine.backtest_real import (
        carregar_dataset, extrair_probabilidade, brier,
    )
    from engine.panel_debate import debate_panel
    from engine.bayesian_blend import bayesian_blend, base_rate_dataset

    persona_ids = persona_ids or ["CL001", "CL002", "CL007"]
    eventos_raw = carregar_dataset(dataset_path)
    if max_eventos:
        eventos_raw = eventos_raw[:max_eventos]

    resultados = []
    briers_vila = []
    briers_prior = []
    briers_blend = []
    acertos_vila = 0
    acertos_blend = 0

    import time as _time
    for i, ev in enumerate(eventos_raw):
        if i > 0 and sleep_entre_eventos_s > 0:
            _time.sleep(sleep_entre_eventos_s)

        exemplos = eventos_raw[max(0, i - few_shot_k):i] if few_shot_k > 0 else None

        # Debate (ou panel simples se usar_debate=False)
        if usar_debate:
            panel = debate_panel(
                contexto=ev["contexto"], persona_ids=persona_ids, sim=sim,
                llm_fn=llm_fn, few_shot_exemplos=exemplos,
                pesos_persona=pesos_persona,
                dispersao_threshold=dispersao_threshold,
                max_rounds=max_rounds,
                chain_of_thought=chain_of_thought,
            )
        else:
            from engine.backtest_real import consultar_panel
            panel = consultar_panel(
                contexto=ev["contexto"], persona_ids=persona_ids, sim=sim,
                llm_fn=llm_fn, few_shot_exemplos=exemplos,
                pesos_persona=pesos_persona,
                chain_of_thought=chain_of_thought,
            )

        p_vila_raw = panel.get("prob_agregada")

        # Onda 97: Platt calibration
        p_vila_cal = p_vila_raw
        if aplicar_platt and p_vila_raw is not None:
            try:
                from engine.calibracao_runtime import aplicar, calibracao_ativa
                if calibracao_ativa():
                    p_vila_cal = aplicar(p_vila_raw)
            except Exception:
                pass

        # Onda 125: Bayesian blend com base rate dos eventos anteriores
        p_blend = p_vila_cal
        if usar_bayesian_blend and p_vila_cal is not None:
            y_hist = [e["outcome_real"] for e in eventos_raw[:i]]
            br = base_rate_dataset(y_hist)
            p_blend = bayesian_blend(p_vila_cal, br, peso_vila=peso_vila)

        p_prior = ev["probabilidade_prior"]
        y = ev["outcome_real"]

        # Métricas Vila raw vs blend
        if p_vila_cal is not None:
            acertou_v = (p_vila_cal >= 0.5) == (y == 1)
            if acertou_v: acertos_vila += 1
            briers_vila.append(brier(p_vila_cal, y))
        if p_blend is not None:
            acertou_b = (p_blend >= 0.5) == (y == 1)
            if acertou_b: acertos_blend += 1
            briers_blend.append(brier(p_blend, y))
        briers_prior.append(brier(p_prior, y))

        resultados.append({
            "evento_id": ev["evento_id"],
            "data": ev["data"],
            "contexto": ev["contexto"][:200],
            "outcome_real": y,
            "prob_prior": p_prior,
            "prob_vila_raw": p_vila_raw,
            "prob_vila_calibrada": p_vila_cal,
            "prob_blend_final": p_blend,
            "acertou_blend": (p_blend is not None) and ((p_blend >= 0.5) == (y == 1)),
            "n_rounds_debate": panel.get("n_rounds", 1),
            "dispersao_inicial": panel.get("dispersao_inicial"),
            "n_respostas_validas": panel["n_respostas_validas"],
            "per_persona": panel["per_persona"],
        })

    n_total = len(eventos_raw)

    def _avg(xs): return sum(xs) / len(xs) if xs else None

    return {
        "dataset": str(dataset_path),
        "n_eventos": n_total,
        "configuracao": {
            "few_shot_k": few_shot_k,
            "pesos_persona": bool(pesos_persona),
            "chain_of_thought": chain_of_thought,
            "usar_debate": usar_debate,
            "usar_bayesian_blend": usar_bayesian_blend,
            "peso_vila": peso_vila,
            "aplicar_platt": aplicar_platt,
        },
        "accuracy_vila_calibrada": acertos_vila / n_total if n_total else 0,
        "accuracy_blend_final": acertos_blend / n_total if n_total else 0,
        "brier_vila_calibrada_avg": _avg(briers_vila),
        "brier_blend_final_avg": _avg(briers_blend),
        "brier_prior_avg": _avg(briers_prior),
        "skill_vila_vs_prior": (
            1 - _avg(briers_vila) / _avg(briers_prior)
            if _avg(briers_vila) and _avg(briers_prior) else None
        ),
        "skill_blend_vs_prior": (
            1 - _avg(briers_blend) / _avg(briers_prior)
            if _avg(briers_blend) and _avg(briers_prior) else None
        ),
        "persona_panel": persona_ids,
        "eventos": resultados,
    }
