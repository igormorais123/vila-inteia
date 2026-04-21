"""
Onda 78: forecast-narrativo — combina Markov psico-histórica com narrativa LLM.

Diferencial vs MiroFish: Mirofish dá só números no grafo. Vila dá:
- Forecast quantitativo (Markov)
- Anomalias (Mules)
- Conversas LLM-ricas como evidência
- Narrativa PT-BR sintetizada por LLM

Função pura: aceita rastreador + sim, retorna dict.
LLM é opcional — se indisponível, retorna sem campo "narrativa".
"""

from __future__ import annotations

from typing import Any
import logging

logger = logging.getLogger(__name__)


def _top_n_estados(distribuicao: list[float], estados_ordem: list[str], n: int = 3) -> list[dict]:
    pares = list(zip(estados_ordem, distribuicao))
    pares.sort(key=lambda x: -x[1])
    return [{"estado": e, "prob": float(p)} for e, p in pares[:n]]


def _convs_llm_ricas(conversas_recentes: list[dict], max_conv: int = 3) -> list[dict]:
    """Mesma heurística de api/rotas_vila.py:conversas_llm_only."""
    PADROES = (
        "Como eu sempre digo",
        "Boa conversa. Devemos continuar",
        "Essa é uma perspectiva válida. Mas considere também",
        "Conte-me mais sobre sua visão",
    )
    out = []
    for c in conversas_recentes[-max_conv * 8:]:
        turnos = c.get("turnos", [])
        if len(turnos) >= 4:
            tem_template = any(
                isinstance(t, (list, tuple)) and len(t) >= 2
                and any(p in str(t[1]) for p in PADROES)
                for t in turnos
            )
            if not tem_template:
                out.append({
                    "parceiro": c.get("parceiro_nome"),
                    "tema": c.get("topico"),
                    "n_turnos": len(turnos),
                    "primeiro_turno": (
                        f"{turnos[0][0]}: {turnos[0][1][:200]}"
                        if isinstance(turnos[0], (list, tuple)) and len(turnos[0]) >= 2 else ""
                    ),
                })
        if len(out) >= max_conv:
            break
    return out


def _gerar_narrativa_llm(payload: dict, llm_fn=None) -> str | None:
    """LLM sintetiza forecast em PT-BR (3-5 frases). None se LLM indisponível."""
    if llm_fn is None:
        try:
            from engine.ia_client import chamar_llm
            llm_fn = chamar_llm
        except Exception:
            return None

    estado = payload["estado_atual"]
    top = payload["top_estados_horizonte"]
    n_mules = payload["n_mules_recentes"]
    h_inicial = payload["entropia_inicial"]
    h_final = payload["entropia_final"]
    horizonte = payload["horizonte"]

    convs_str = ""
    for c in payload.get("evidencias_llm", []):
        convs_str += f"\n  - {c['parceiro']} sobre {c['tema']}: \"{c['primeiro_turno'][:140]}\""

    prompt = (
        f"Vila INTEIA está no estado psico-histórico '{estado}'. "
        f"Markov projeta para os próximos {horizonte} steps:\n"
        + "\n".join(f"  - {t['estado']}: {t['prob']*100:.1f}%" for t in top)
        + f"\n\nEntropia inicial: {h_inicial:.2f} bits → final: {h_final:.2f} bits "
        + ("(convergindo)." if h_final < h_inicial else "(divergindo).")
        + f"\nMules recentes (anomalias): {n_mules}."
        + (f"\n\nConversas-evidência:{convs_str}" if convs_str else "")
        + "\n\nEscreva 3-5 frases em PT-BR sobre o que isso significa "
          "para o destino da Vila e qual ação Helena/Efesto deveriam recomendar."
    )

    try:
        kwargs = dict(
            mensagens=[{"role": "user", "content": prompt}],
            modelo="rapido",
            max_tokens=350,
            temperatura=0.6,
        )
        try:
            resp = llm_fn(**kwargs, bypass_step_cap=True)
        except TypeError:
            resp = llm_fn(**kwargs)
        return resp.strip() if resp else None
    except Exception as e:
        logger.debug(f"forecast narrativa LLM falhou: {e}")
        return None


def gerar_forecast(
    rastreador: Any | None = None,
    conversas_recentes: list[dict] | None = None,
    horizonte: int = 10,
    com_narrativa: bool = True,
    llm_fn=None,
) -> dict:
    """
    Combina trajetória observada + Markov forecast + evidência LLM + narrativa.

    Args:
        rastreador: RASTREADOR_GLOBAL (psicohistoria.detector_estado_vila); None usa import.
        conversas_recentes: sim.conversas_recentes; None retorna sem evidências.
        horizonte: steps a projetar.
        com_narrativa: chamar LLM para texto. Se LLM indisponível, campo "narrativa" ausente.
        llm_fn: injetável para teste (default chamar_llm).

    Returns dict com:
        estado_atual, n_steps_observados, distribuicao_observada,
        top_estados_horizonte, entropia_inicial, entropia_final,
        mules_recentes, n_mules_recentes, evidencias_llm,
        horizonte, narrativa (se com_narrativa e LLM ok)
    """
    if rastreador is None:
        from engine.psicohistoria.detector_estado_vila import RASTREADOR_GLOBAL
        rastreador = RASTREADOR_GLOBAL

    traj_obs = rastreador.trajetoria
    estado_atual = traj_obs.ultimo_estado() if traj_obs.estados else "bootstrap"
    n_steps = len(traj_obs.estados)
    distribuicao_observada = traj_obs.distribuicao_historica()

    from engine.psicohistoria.grafo_eventos import construir_grafo_vila
    from engine.psicohistoria.equacoes import prever_trajetoria, entropia_trajetoria

    grafo = construir_grafo_vila()
    traj = prever_trajetoria(grafo, estado_atual, horizonte)
    estados_ordem = list(grafo.estados.keys())
    dist_final = traj[-1].tolist()
    top_estados = _top_n_estados(dist_final, estados_ordem, n=3)

    H = entropia_trajetoria(traj)
    entropia_inicial = float(H[0])
    entropia_final = float(H[-1])

    mules = list(traj_obs.mules_detectados)[-5:]
    n_mules = len(traj_obs.mules_detectados)

    evidencias = _convs_llm_ricas(conversas_recentes or [], max_conv=3)

    # Onda 97: aplicar calibração Platt se ativa
    top_estados_calibrados = None
    calibracao_info = None
    try:
        from engine.calibracao_runtime import calibracao_ativa, aplicar_varios, carregar_coefs
        if calibracao_ativa():
            probs_raw = [t["prob"] for t in top_estados]
            probs_cal = aplicar_varios(probs_raw)
            top_estados_calibrados = [
                {**t, "prob_raw": t["prob"], "prob": pc}
                for t, pc in zip(top_estados, probs_cal)
            ]
            coefs = carregar_coefs() or {}
            calibracao_info = {
                "ativa": True, "a": coefs.get("a"), "b": coefs.get("b"),
                "n_amostras": coefs.get("n_amostras"),
            }
    except Exception:
        pass

    payload = {
        "estado_atual": estado_atual,
        "n_steps_observados": n_steps,
        "distribuicao_observada": distribuicao_observada,
        "horizonte": horizonte,
        "top_estados_horizonte": top_estados_calibrados or top_estados,
        "entropia_inicial": entropia_inicial,
        "entropia_final": entropia_final,
        "convergindo": entropia_final < entropia_inicial,
        "mules_recentes": mules,
        "n_mules_recentes": n_mules,
        "evidencias_llm": evidencias,
    }
    if calibracao_info:
        payload["calibracao"] = calibracao_info

    if com_narrativa:
        narrativa = _gerar_narrativa_llm(payload, llm_fn=llm_fn)
        if narrativa:
            payload["narrativa"] = narrativa

    return payload
