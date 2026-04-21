"""
Onda 89: panel chat — múltiplas personas respondem mesma pergunta em paralelo.

Diferencial: em vez de chat 1:1, pega Musk + Buffett + Sun Tzu respondendo
"como resolver X?" lado a lado. Revela diferenças estratégicas.

Não usa async (chamar_llm é síncrono com throttle), usa ThreadPoolExecutor
para paralelizar calls independentes.
"""

from __future__ import annotations

import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any

logger = logging.getLogger(__name__)


def _chat_uma(persona_id: str, pergunta: str, sim: Any, llm_fn=None,
               max_tokens: int = 280, temperatura: float = 0.75) -> dict:
    from engine.persona_chat import chat_com_persona
    return chat_com_persona(
        persona_id=persona_id, pergunta=pergunta, sim=sim,
        llm_fn=llm_fn, max_tokens=max_tokens, temperatura=temperatura,
    )


def panel_chat(
    persona_ids: list[str],
    pergunta: str,
    sim: Any,
    llm_fn=None,
    max_tokens: int = 280,
    temperatura: float = 0.75,
    paralelo: bool = True,
) -> dict:
    """
    Executa chat_com_persona em N personas. Paralelo por default.

    Returns dict:
        pergunta, n_personas, respostas: [{persona_id, persona_nome, resposta, erro}, ...]
        latencia_ms_total, latencia_ms_max (maior thread)
    """
    import time
    t0 = time.monotonic()

    if not persona_ids:
        return {
            "pergunta": pergunta, "n_personas": 0,
            "respostas": [], "latencia_ms_total": 0, "latencia_ms_max": 0,
            "erro": "persona_ids vazio",
        }

    # Dedup preserving order
    seen = set()
    uniq = []
    for p in persona_ids:
        if p not in seen:
            seen.add(p); uniq.append(p)

    respostas: list[dict] = [None] * len(uniq)
    latencias: list[float] = [0.0] * len(uniq)

    def _tarefa(idx, pid):
        ti = time.monotonic()
        r = _chat_uma(pid, pergunta, sim, llm_fn, max_tokens, temperatura)
        dt = (time.monotonic() - ti) * 1000
        return idx, r, dt

    if paralelo and len(uniq) > 1:
        with ThreadPoolExecutor(max_workers=min(len(uniq), 6)) as ex:
            futs = [ex.submit(_tarefa, i, p) for i, p in enumerate(uniq)]
            for fut in as_completed(futs):
                idx, r, dt = fut.result()
                respostas[idx] = r
                latencias[idx] = dt
    else:
        for i, pid in enumerate(uniq):
            idx, r, dt = _tarefa(i, pid)
            respostas[idx] = r
            latencias[idx] = dt

    t_total = (time.monotonic() - t0) * 1000

    return {
        "pergunta": pergunta,
        "n_personas": len(uniq),
        "respostas": respostas,
        "latencia_ms_total": round(t_total, 1),
        "latencia_ms_max": round(max(latencias) if latencias else 0, 1),
        "paralelo": paralelo,
    }
