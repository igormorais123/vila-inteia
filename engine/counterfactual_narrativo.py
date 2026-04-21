"""
Onda 79: counterfactual-narrativo — "E se o estado fosse Y em vez de X?"

Combina Pearl do-calculus (engine.causalidade.pearl) com narrativa LLM PT-BR.
Diferencial vs MiroFish: MiroFish só prevê. Vila responde perguntas do-operator.

Função pura: aceita rastreador + estado_alternativo, retorna dict com
trajetórias factual vs counterfactual + divergência + narrativa opcional.
"""

from __future__ import annotations

from typing import Any
import logging

import numpy as np

logger = logging.getLogger(__name__)


def _gerar_narrativa_llm(payload: dict, llm_fn=None) -> str | None:
    if llm_fn is None:
        try:
            from engine.ia_client import chamar_llm
            llm_fn = chamar_llm
        except Exception:
            return None

    est_original = payload["estado_factual_atual"]
    est_alt = payload["estado_alternativo"]
    tv = payload["divergencia_tv"]
    horizonte = payload["horizonte"]
    top_f = payload["top_estados_factual"]
    top_cf = payload["top_estados_counterfactual"]
    ate = payload.get("ate_polarizacao_vs_equilibrio")

    def _fmt(top):
        return ", ".join(f"{t['estado']}={t['prob']*100:.1f}%" for t in top)

    linhas_ate = ""
    if ate is not None:
        linhas_ate = f"\nATE (equilibrio vs polarizacao) como outcome: {ate:+.3f}"

    prompt = (
        f"Vila INTEIA está em estado factual '{est_original}'. "
        f"Contrafactual: 'e se o estado fosse {est_alt}?' "
        f"Horizonte {horizonte} steps.\n\n"
        f"Factual: {_fmt(top_f)}\n"
        f"Counterfactual: {_fmt(top_cf)}\n"
        f"Divergência TV no horizonte: {tv:.3f} (0=idêntico, 1=máximo).{linhas_ate}\n\n"
        f"Escreva 3-5 frases em PT-BR explicando o que muda na Vila "
        f"se Helena/Efesto intervirem para forçar '{est_alt}'. "
        f"Seja concreto sobre custo/benefício."
    )

    try:
        kwargs = dict(
            mensagens=[{"role": "user", "content": prompt}],
            modelo="rapido", max_tokens=350, temperatura=0.6,
        )
        try:
            resp = llm_fn(**kwargs, bypass_step_cap=True)
        except TypeError:
            resp = llm_fn(**kwargs)
        return resp.strip() if resp else None
    except Exception as e:
        logger.debug(f"counterfactual narrativa LLM falhou: {e}")
        return None


def _top_n(distribuicao: np.ndarray, estados_ordem: list[str], n: int = 3) -> list[dict]:
    idxs = np.argsort(-distribuicao)[:n]
    return [{"estado": estados_ordem[int(i)], "prob": float(distribuicao[int(i)])} for i in idxs]


def gerar_counterfactual(
    estado_alternativo: str,
    rastreador: Any | None = None,
    horizonte: int = 10,
    com_narrativa: bool = True,
    llm_fn=None,
) -> dict:
    """
    "E se no step atual o estado fosse `estado_alternativo` em vez do observado?"

    Usa grafo psico-histórico canônico + Pearl counterfactual.

    Returns dict:
        estado_factual_atual, estado_alternativo, horizonte,
        top_estados_factual, top_estados_counterfactual,
        divergencia_tv (TV distance no horizonte),
        ate_polarizacao_vs_equilibrio (se ambos estados existirem),
        narrativa (opcional LLM)
    """
    if rastreador is None:
        from engine.psicohistoria.detector_estado_vila import RASTREADOR_GLOBAL
        rastreador = RASTREADOR_GLOBAL

    from engine.psicohistoria.grafo_eventos import construir_grafo_vila
    from engine.causalidade.pearl import counterfactual, ate

    grafo = construir_grafo_vila()
    estados_ordem = list(grafo.estados.keys())

    if estado_alternativo not in grafo.estados:
        raise ValueError(
            f"estado_alternativo '{estado_alternativo}' desconhecido. "
            f"Válidos: {estados_ordem}"
        )

    estado_factual = (
        rastreador.trajetoria.ultimo_estado()
        if rastreador.trajetoria.estados else "bootstrap"
    )
    if estado_factual not in grafo.estados:
        estado_factual = "bootstrap"

    idx_factual = grafo.estado_para_index(estado_factual)
    idx_alt = grafo.estado_para_index(estado_alternativo)

    cf = counterfactual(
        matriz=grafo.matriz,
        trajetoria_factual=[idx_factual],
        ponto_intervencao=0,
        valor_alternativo=idx_alt,
        passos_depois=horizonte,
    )

    dist_f_final = np.array(cf["trajetoria_factual"][-1])
    dist_cf_final = np.array(cf["trajetoria_counterfactual"][-1])

    payload = {
        "estado_factual_atual": estado_factual,
        "estado_alternativo": estado_alternativo,
        "horizonte": horizonte,
        "top_estados_factual": _top_n(dist_f_final, estados_ordem, 3),
        "top_estados_counterfactual": _top_n(dist_cf_final, estados_ordem, 3),
        "divergencia_tv": float(cf["divergencia_tv_final"]),
        "estados_ordem": estados_ordem,
    }

    # ATE opcional se estados canônicos existirem
    if "equilibrio" in grafo.estados and "polarizacao" in grafo.estados:
        try:
            idx_eq = grafo.estado_para_index("equilibrio")
            idx_pol = grafo.estado_para_index("polarizacao")
            ate_val = ate(
                grafo.matriz,
                estado_tratamento_idx=idx_eq,
                estado_controle_idx=idx_pol,
                estado_outcome_idx=idx_eq,
                horizonte=horizonte,
            )
            payload["ate_polarizacao_vs_equilibrio"] = float(ate_val)
        except Exception as e:
            logger.debug(f"ATE calc falhou: {e}")

    if com_narrativa:
        narrativa = _gerar_narrativa_llm(payload, llm_fn=llm_fn)
        if narrativa:
            payload["narrativa"] = narrativa

    return payload
