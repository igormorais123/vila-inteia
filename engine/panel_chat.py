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


# Onda 158: temperature por persona baseado em arquétipo cognitivo
# - Analíticos/precisão: low temp (foco, determinismo)
# - Visionários/exploradores: high temp (criatividade, variação)
# - Equilibrados: mid temp
_TEMP_POR_PERSONA: dict[str, float] = {
    "CL001": 0.70,  # Musk — visionário, contrarian
    "CL002": 0.50,  # Jobs — precision + design
    "CL007": 0.55,  # Bezos — long-term probabilistic
    "CL020": 0.30,  # Buffett — value, conservador
    "CL021": 0.30,  # Munger — rational
    "CL015": 0.45,  # Dalio — macro principles
    "CL019": 0.55,  # Icahn — activist
    "CL023": 0.65,  # Zuckerberg — move fast
    "CL030": 0.45,  # Sun Tzu — strategy
    "CL035": 0.35,  # Marco Aurélio — stoic
}


def _temp_para_persona(pid: str, default: float = 0.55) -> float:
    return _TEMP_POR_PERSONA.get(pid, default)


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
    temp_por_persona: bool = False,
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
        # Onda 158: use arquétipo-aware temp se ativado
        t = _temp_para_persona(pid, default=temperatura) if temp_por_persona else temperatura
        r = _chat_uma(pid, pergunta, sim, llm_fn, max_tokens, t)
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
