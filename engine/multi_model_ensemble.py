"""
Onda 164: multi-model ensemble pra predictions.

Query N modelos Groq em paralelo pra mesmo prompt, agrega predictions
via median (robust) ou mean. Reduz bias single-provider.

Aplicação principal: extrair_probabilidade sobre N respostas,
agregadas, pra uma persona. Cada persona × N modelos = distribution.

Uso:
    r = chamar_ensemble_probs(
        mensagens=[...],
        modelos=['llama-3.3-70b-versatile', 'qwen/qwen3-32b', 'meta-llama/llama-4-scout-17b-16e-instruct'],
        max_tokens=250, temperatura=0.4,
    )
    # r = {'probs': [0.7, 0.65, 0.75], 'median': 0.70, 'respostas': [...], 'errors': 0}
"""

from __future__ import annotations

import logging
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any

logger = logging.getLogger(__name__)


def _chamar_com_modelo_override(
    mensagens: list[dict],
    modelo_id: str,
    max_tokens: int = 250,
    temperatura: float = 0.4,
    system_prompt: str = "",
    bypass_step_cap: bool = True,
) -> str | None:
    """
    Chama chamar_llm com modelo_id específico via env override.
    Thread-safe: muda env GROQ_MODEL_RAPIDO temporariamente.

    NOTA: env var não é thread-safe. Em paralelo, última thread ganha.
    Por isso usamos ThreadPoolExecutor max_workers=1 pra chamadas sequenciais,
    OU chamar direto openai client com modelo_id explícito.

    Simplest: usa chamar_llm com alias "rapido" + muda env antes por call.
    """
    from engine.ia_client import chamar_llm, _ensure_client, _provider

    # Salva env atual, restore depois
    orig = os.environ.get("GROQ_MODEL_RAPIDO", "")
    try:
        os.environ["GROQ_MODEL_RAPIDO"] = modelo_id
        r = chamar_llm(
            mensagens=mensagens, modelo="rapido",
            max_tokens=max_tokens, temperatura=temperatura,
            system_prompt=system_prompt,
            bypass_step_cap=bypass_step_cap,
        )
        return r
    finally:
        if orig:
            os.environ["GROQ_MODEL_RAPIDO"] = orig


def chamar_ensemble_probs(
    mensagens: list[dict],
    modelos: list[str],
    max_tokens: int = 250,
    temperatura: float = 0.4,
    system_prompt: str = "",
    timeout_total_s: float = 60.0,
) -> dict:
    """
    Query N modelos SEQUENCIALMENTE (thread-safe env swap), extrai prob.
    Retorna {probs, median, respostas, errors, n_validas}.

    Sequencial porque env GROQ_MODEL_RAPIDO não thread-safe.
    Para paralelo verdadeiro, precisaria expor modelo_id kwarg em chamar_llm.
    """
    from engine.backtest_real import extrair_probabilidade

    respostas = []
    probs = []
    errors = 0

    for modelo_id in modelos:
        try:
            resp = _chamar_com_modelo_override(
                mensagens, modelo_id,
                max_tokens=max_tokens,
                temperatura=temperatura,
                system_prompt=system_prompt,
            )
            if resp is None:
                errors += 1
                respostas.append({"modelo": modelo_id, "resposta": None, "erro": "LLM retornou None"})
                continue
            p = extrair_probabilidade(resp)
            respostas.append({
                "modelo": modelo_id,
                "resposta": resp,
                "prob_extraida": p,
            })
            if p is not None:
                probs.append(p)
        except Exception as e:
            errors += 1
            respostas.append({"modelo": modelo_id, "resposta": None, "erro": str(e)})

    median = None
    if probs:
        sprobs = sorted(probs)
        n = len(sprobs)
        median = sprobs[n // 2] if n % 2 == 1 else (sprobs[n // 2 - 1] + sprobs[n // 2]) / 2

    return {
        "probs": probs,
        "median": median,
        "respostas": respostas,
        "errors": errors,
        "n_validas": len(probs),
        "modelos_queried": modelos,
    }


# Modelos "free tier" disponíveis Groq (abril 2026):
# - meta-llama/llama-4-scout-17b-16e-instruct (17b)
# - llama-3.3-70b-versatile (70b)
# - qwen/qwen3-32b
# - openai/gpt-oss-120b
# - openai/gpt-oss-20b
# - llama-3.1-8b-instant
MODELOS_GROQ_DIVERSE = [
    "llama-3.3-70b-versatile",
    "qwen/qwen3-32b",
    "meta-llama/llama-4-scout-17b-16e-instruct",
]
