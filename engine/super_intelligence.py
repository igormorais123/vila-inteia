"""
Onda 81: super-intelligence — endpoint meta que combina:
- Forecast Markov narrativo (Onda 78)
- Recomendação multi-counterfactual sweep (Onda 80)
- Síntese unificada LLM PT-BR

Single endpoint = single round-trip pra dashboard. LLM faz síntese final
combinando insights dos 2 sub-payloads.

Diferencial vs MiroFish: integração de Markov + do-calculus + LLM em uma
chamada. Helena/Efesto recebem briefing executivo completo.
"""

from __future__ import annotations

from typing import Any
import logging

logger = logging.getLogger(__name__)


def _gerar_sintese_executiva(payload: dict, llm_fn=None) -> str | None:
    if llm_fn is None:
        try:
            from engine.ia_client import chamar_llm
            llm_fn = chamar_llm
        except Exception:
            return None

    fc = payload["forecast"]
    rec = payload["recomendacao"]

    estado_atual = fc.get("estado_atual", "?")
    top_fc = fc.get("top_estados_horizonte", [])[:3]
    n_mules = fc.get("n_mules_recentes", 0)
    h_inicial = fc.get("entropia_inicial", 0)
    h_final = fc.get("entropia_final", 0)

    melhor = rec.get("melhor_intervencao", {})
    rec_outcome = rec.get("outcome_desejado", "?")

    top_str = ", ".join(f"{t['estado']}={t['prob']*100:.0f}%" for t in top_fc)

    prompt = (
        f"BRIEFING EXECUTIVO Vila INTEIA:\n\n"
        f"FORECAST (próximos {fc.get('horizonte', 10)} steps):\n"
        f"  Estado atual: {estado_atual}\n"
        f"  Trajetória provável: {top_str}\n"
        f"  Entropia: {h_inicial:.2f} → {h_final:.2f} bits "
        f"({'convergindo' if h_final < h_inicial else 'divergindo'})\n"
        f"  Anomalias (Mules): {n_mules}\n\n"
        f"RECOMENDAÇÃO (sweep para outcome '{rec_outcome}'):\n"
        f"  Melhor intervenção: forçar '{melhor.get('estado', '?')}' "
        f"(P={melhor.get('prob_outcome', 0)*100:.1f}%)\n\n"
        f"Escreva briefing PT-BR (4-6 frases) para Helena/Efesto:\n"
        f"1. Diagnóstico do estado da Vila\n"
        f"2. Risco principal nos próximos steps\n"
        f"3. Ação recomendada concreta\n"
        f"4. Métrica de sucesso pra avaliar resultado\n"
    )

    try:
        kwargs = dict(
            mensagens=[{"role": "user", "content": prompt}],
            modelo="rapido", max_tokens=500, temperatura=0.5,
        )
        try:
            resp = llm_fn(**kwargs, bypass_step_cap=True)
        except TypeError:
            resp = llm_fn(**kwargs)
        return resp.strip() if resp else None
    except Exception as e:
        logger.debug(f"super-intelligence sintese LLM falhou: {e}")
        return None


def gerar_super_intelligence(
    horizonte: int = 10,
    outcome_desejado: str = "equilibrio",
    rastreador: Any | None = None,
    conversas_recentes: list | None = None,
    com_sintese_llm: bool = True,
    llm_fn=None,
) -> dict:
    """
    Combina forecast (Onda 78) + recomendacao (Onda 80) em payload unificado.
    LLM gera briefing executivo final.

    Args:
        horizonte: passos pra forecast e sweep
        outcome_desejado: meta da recomendacao
        rastreador, conversas_recentes: passados pros sub-módulos
        com_sintese_llm: gerar briefing
        llm_fn: injetável pra teste

    Returns dict com forecast, recomendacao, briefing_executivo (opcional).
    """
    from engine.forecast_narrativo import gerar_forecast
    from engine.recomendacao_intervencao import gerar_recomendacao

    forecast = gerar_forecast(
        rastreador=rastreador,
        conversas_recentes=conversas_recentes,
        horizonte=horizonte,
        com_narrativa=False,
        llm_fn=llm_fn,
    )

    recomendacao = gerar_recomendacao(
        outcome_desejado=outcome_desejado,
        horizonte=horizonte,
        rastreador=rastreador,
        com_recomendacao_llm=False,
        llm_fn=llm_fn,
    )

    payload = {
        "forecast": forecast,
        "recomendacao": recomendacao,
        "horizonte": horizonte,
        "outcome_desejado": outcome_desejado,
    }

    if com_sintese_llm:
        sintese = _gerar_sintese_executiva(payload, llm_fn=llm_fn)
        if sintese:
            payload["briefing_executivo"] = sintese

    return payload
