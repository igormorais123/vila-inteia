"""
Onda 131: LLM-as-judge verification.

Meta-LLM avalia resposta do painel. Retorna score 0-1 de qualidade:
- calibração apropriada (não over-confident sem evidência)
- raciocínio consistente
- justificativa alinhada com prob emitida

Pode filtrar out respostas de baixa qualidade antes agregar.
"""

from __future__ import annotations

import logging
from typing import Any, Callable
import re

logger = logging.getLogger(__name__)


_REGEX_SCORE = re.compile(r"QUALIDADE\s*[:：]\s*(\d{1,3})\s*(?:/\s*100|%)?", re.IGNORECASE)


def avaliar_resposta(
    contexto: str,
    resposta_persona: str,
    prob_emitida: float,
    llm_fn: Callable | None = None,
    temperatura: float = 0.3,
) -> dict:
    """
    Judge LLM call. Retorna {score 0-1, raciocinio, ok}.
    """
    if llm_fn is None:
        try:
            from engine.ia_client import chamar_llm
            llm_fn = chamar_llm
        except Exception:
            return {"score": None, "erro": "LLM indisponível"}

    prompt = (
        f"Contexto do evento: \"{contexto}\"\n\n"
        f"Resposta do analista: \"{resposta_persona}\"\n"
        f"Probabilidade final emitida: {prob_emitida*100:.0f}%\n\n"
        f"Avalie a qualidade da resposta acima em 3 dimensões:\n"
        f"1. Calibração: a probabilidade faz sentido dado o contexto? "
        f"(Over-confident sem evidência = ruim)\n"
        f"2. Raciocínio: a justificativa é coerente?\n"
        f"3. Consistência: a prob emitida bate com o raciocínio?\n\n"
        f"Retorne uma nota 0-100 de qualidade geral:\n"
        f"ANÁLISE: <1-2 frases>\n"
        f"QUALIDADE: <N>/100"
    )

    try:
        kwargs = dict(
            mensagens=[{"role": "user", "content": prompt}],
            modelo="rapido", max_tokens=200, temperatura=temperatura,
        )
        try:
            resp = llm_fn(**kwargs, bypass_step_cap=True)
        except TypeError:
            resp = llm_fn(**kwargs)
        if not resp:
            return {"score": None, "erro": "LLM retornou vazio"}
    except Exception as e:
        return {"score": None, "erro": str(e)[:100]}

    m = _REGEX_SCORE.search(resp)
    if not m:
        return {
            "score": None, "erro": "regex QUALIDADE não matched",
            "resposta_judge": resp[:200],
        }
    score = int(m.group(1)) / 100.0
    return {
        "score": score,
        "raciocinio_judge": resp[:300],
        "ok": score >= 0.5,
    }


def filtrar_panel_por_qualidade(
    per_persona: list[dict],
    contexto: str,
    llm_fn: Callable | None = None,
    threshold: float = 0.4,
) -> dict:
    """
    Aplica LLM judge em cada resposta. Retorna:
        per_persona_filtrado (remove low-quality abaixo threshold)
        per_persona_annotated (todos com judge_score)
    """
    annotated = []
    filtrado = []
    for p in per_persona:
        prob = p.get("prob_extraida")
        resp = p.get("resposta", "") or ""
        if prob is None or not resp:
            annotated.append({**p, "judge_score": None})
            continue
        jd = avaliar_resposta(contexto, resp, prob, llm_fn=llm_fn)
        p2 = {**p, "judge_score": jd.get("score"),
              "judge_raciocinio": jd.get("raciocinio_judge")}
        annotated.append(p2)
        if jd.get("score") is not None and jd["score"] >= threshold:
            filtrado.append(p2)
    return {
        "per_persona_annotated": annotated,
        "per_persona_filtrado": filtrado,
        "n_filtrados_out": len(per_persona) - len(filtrado),
        "threshold": threshold,
    }
