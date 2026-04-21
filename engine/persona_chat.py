"""
Onda 86: persona-chat — user pergunta direto à persona.

Diferencial MiroFish: MiroFish tem "chat with agent post-sim". Vila permite
chat direto com QUALQUER persona lendária (Musk, Buffett, Sun Tzu, Jesus)
a qualquer momento, usando prompt arquétipo profundo.

Função pura: aceita persona + pergunta + sim, retorna resposta LLM.
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)

_HISTORICO: dict[str, list[dict]] = {}
_MAX_TURNOS = 10


def _historico_persona(persona_id: str) -> list[dict]:
    if persona_id not in _HISTORICO:
        _HISTORICO[persona_id] = []
    return _HISTORICO[persona_id]


def resetar_historico(persona_id: str | None = None) -> None:
    if persona_id is None:
        _HISTORICO.clear()
    elif persona_id in _HISTORICO:
        _HISTORICO[persona_id].clear()


def chat_com_persona(
    persona_id: str,
    pergunta: str,
    sim: Any,
    llm_fn=None,
    max_tokens: int = 350,
    temperatura: float = 0.75,
) -> dict:
    """
    Chat síncrono com uma persona da sim.

    Args:
        persona_id: ID tipo "CL002"
        pergunta: texto do usuário
        sim: SimulacaoVila ativa (para buscar persona)
        llm_fn: injetável pra teste
        max_tokens, temperatura: LLM params

    Returns dict:
        persona_id, persona_nome, pergunta, resposta,
        n_turnos_historico, erro (opcional)
    """
    if not pergunta or not pergunta.strip():
        return {
            "persona_id": persona_id, "persona_nome": None,
            "pergunta": pergunta, "resposta": None,
            "erro": "pergunta vazia", "n_turnos_historico": 0,
        }

    persona = sim.personas.get(persona_id) if hasattr(sim, "personas") else None
    if persona is None:
        return {
            "persona_id": persona_id, "persona_nome": None,
            "pergunta": pergunta, "resposta": None,
            "erro": f"persona '{persona_id}' não encontrada",
            "n_turnos_historico": 0,
        }

    persona_nome = getattr(persona, "nome_exibicao", persona_id)

    try:
        system_prompt = persona.gerar_prompt_sistema()
    except Exception as e:
        logger.debug(f"gerar_prompt_sistema falhou: {e}; usando fallback")
        system_prompt = f"Você é {persona_nome}. Responda no seu estilo autêntico."

    system_prompt += (
        "\n\nREGRA DE CHAT: o usuário (não um NPC) está fazendo uma pergunta "
        "diretamente a você. Responda em 2-5 frases PT-BR, no seu estilo "
        "autêntico, usando suas expressões típicas quando couber. "
        "Não invente contexto fora do que foi perguntado."
    )

    hist = _historico_persona(persona_id)
    mensagens = []
    for t in hist[-_MAX_TURNOS:]:
        mensagens.append({"role": "user", "content": t["pergunta"]})
        if t.get("resposta"):
            mensagens.append({"role": "assistant", "content": t["resposta"]})
    mensagens.append({"role": "user", "content": pergunta.strip()})

    if llm_fn is None:
        try:
            from engine.ia_client import chamar_llm
            llm_fn = chamar_llm
        except Exception:
            return {
                "persona_id": persona_id, "persona_nome": persona_nome,
                "pergunta": pergunta, "resposta": None,
                "erro": "LLM indisponível", "n_turnos_historico": len(hist),
            }

    try:
        kwargs = dict(
            mensagens=mensagens, modelo="rapido",
            max_tokens=max_tokens, temperatura=temperatura,
            system_prompt=system_prompt,
        )
        try:
            resposta = llm_fn(**kwargs, bypass_step_cap=True)
        except TypeError:
            resposta = llm_fn(**kwargs)
    except Exception as e:
        logger.debug(f"persona_chat LLM falhou: {e}")
        return {
            "persona_id": persona_id, "persona_nome": persona_nome,
            "pergunta": pergunta, "resposta": None,
            "erro": f"LLM error: {type(e).__name__}",
            "n_turnos_historico": len(hist),
        }

    if not resposta:
        return {
            "persona_id": persona_id, "persona_nome": persona_nome,
            "pergunta": pergunta, "resposta": None,
            "erro": "LLM retornou vazio (quota/circuit)",
            "n_turnos_historico": len(hist),
        }

    resposta = resposta.strip()
    hist.append({"pergunta": pergunta.strip(), "resposta": resposta})
    if len(hist) > _MAX_TURNOS:
        _HISTORICO[persona_id] = hist[-_MAX_TURNOS:]

    return {
        "persona_id": persona_id,
        "persona_nome": persona_nome,
        "pergunta": pergunta.strip(),
        "resposta": resposta,
        "n_turnos_historico": len(_HISTORICO[persona_id]),
    }


def historico_persona_public(persona_id: str) -> dict:
    """Retorna histórico de chat (útil pra drawer)."""
    hist = _HISTORICO.get(persona_id, [])
    return {
        "persona_id": persona_id,
        "n_turnos": len(hist),
        "turnos": list(hist),
    }
