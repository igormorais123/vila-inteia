"""
Cliente IA da Vila INTEIA — OmniRoute (VPS nova) + Anthropic fallback.

Provider primário: OmniRoute na URL definida em ambiente (custo zero)
Combos:
  - BestFREE: volume (diálogos, FlockVote, comentários)
  - osa-elite: sínteses estratégicas (8+ perspectivas)
  - osa-specialist: resumo tático, compressão

Fallback: Anthropic API direta (só se IA_ALLOW_API_FALLBACK=true)
Se tudo falhar: retorna None → chamador usa heurística.
"""

from __future__ import annotations

import os
import time
import logging
from dataclasses import dataclass, field
from typing import Optional

logger = logging.getLogger("vila-inteia.ia")

# Default via env var — sem host privado hardcoded
_DEFAULT_OMNIROUTE_URL = "http://localhost:20128"


@dataclass
class ThrottleConfig:
    """Controle de taxa de chamadas."""
    max_por_minuto: int = 30
    _timestamps: list = field(default_factory=list, repr=False)

    def pode_chamar(self) -> bool:
        agora = time.time()
        self._timestamps = [t for t in self._timestamps if agora - t < 60]
        return len(self._timestamps) < self.max_por_minuto

    def registrar(self):
        self._timestamps.append(time.time())


_throttle = ThrottleConfig()
_provider = None  # "omniroute", "anthropic"
_client = None
_client_fallback = None  # Anthropic como fallback


def _detectar_provider():
    """OmniRoute PRIMEIRO (custo zero). Anthropic só como fallback."""
    global _provider, _client, _client_fallback

    omniroute_key = os.getenv("OMNIROUTE_API_KEY", "")
    omniroute_url = os.getenv("OMNIROUTE_URL", _DEFAULT_OMNIROUTE_URL)
    claude_key = os.getenv("CLAUDE_API_KEY", "")

    # PRIORIDADE 1: OmniRoute (custo zero)
    if omniroute_key:
        try:
            from openai import OpenAI
            _client = OpenAI(
                api_key=omniroute_key,
                base_url=f"{omniroute_url}/v1",
                timeout=30.0,
            )
            _provider = "omniroute"
            logger.info(f"Vila IA: OmniRoute ({omniroute_url}) — custo zero")
        except ImportError:
            logger.warning("Vila IA: openai SDK não instalado")

    # Preparar fallback Anthropic (só cria client, não usa por padrão)
    if claude_key and os.getenv("IA_ALLOW_API_FALLBACK", "false").lower() == "true":
        try:
            import anthropic
            _client_fallback = anthropic.Anthropic(api_key=claude_key, timeout=30.0)
            logger.info("Vila IA: Anthropic fallback preparado")
        except ImportError:
            pass

    if not _client and not _client_fallback:
        logger.warning("Vila IA: nenhum provider disponível — rodará com heurística")
        _provider = None


def _ensure_client():
    global _provider, _client
    if _provider is None and _client is None:
        _detectar_provider()
    return _client


# Modelos por provider
def _modelo(alias: str) -> str:
    """Traduz alias para modelo real."""
    if _provider == "omniroute":
        return {
            "rapido": "BestFREE",
            "analise": "osa-elite",
            "sintese": "osa-specialist",
        }.get(alias, "BestFREE")
    else:
        # Anthropic direto
        return {
            "rapido": "claude-haiku-4-5-20251001",
            "analise": "claude-sonnet-4-20250514",
            "sintese": "claude-haiku-4-5-20251001",
        }.get(alias, "claude-haiku-4-5-20251001")


MODELO_RAPIDO = "rapido"
MODELO_ANALISE = "analise"
MODELO_SINTESE = "sintese"


def chamar_llm(
    mensagens: list[dict],
    modelo: str = "rapido",
    max_tokens: int = 300,
    temperatura: float = 0.8,
    system_prompt: str = "",
) -> Optional[str]:
    """
    Chamada SÍNCRONA ao LLM.
    Tenta OmniRoute → se falhar → tenta Anthropic fallback → se falhar → None.
    """
    c = _ensure_client()

    if not _throttle.pode_chamar():
        logger.debug("Throttle atingido — pulando chamada LLM")
        return None

    # Separar system das mensagens
    msgs_user = []
    for m in mensagens:
        if m["role"] == "system":
            if not system_prompt:
                system_prompt = m["content"]
        else:
            msgs_user.append(m)

    if not msgs_user:
        msgs_user = [{"role": "user", "content": "Responda."}]

    modelo_real = _modelo(modelo)

    # Tentativa 1: OmniRoute
    if c and _provider == "omniroute":
        resultado = _chamar_openai(c, modelo_real, msgs_user, system_prompt, max_tokens, temperatura)
        if resultado:
            _throttle.registrar()  # Conta APENAS chamadas bem-sucedidas
            return resultado
        logger.debug(f"OmniRoute falhou ({modelo_real}), tentando fallback...")

    # Tentativa 2: Anthropic fallback
    if _client_fallback:
        modelo_ant = {
            "rapido": "claude-haiku-4-5-20251001",
            "analise": "claude-sonnet-4-20250514",
            "sintese": "claude-haiku-4-5-20251001",
        }.get(modelo, "claude-haiku-4-5-20251001")
        resultado = _chamar_anthropic(_client_fallback, modelo_ant, msgs_user, system_prompt, max_tokens, temperatura)
        if resultado:
            _throttle.registrar()
            return resultado

    return None


def _chamar_openai(client, modelo, msgs, system_prompt, max_tokens, temp) -> Optional[str]:
    """Chamada via OpenAI SDK (OmniRoute)."""
    try:
        # Injetar system no user prompt (OmniRoute/Claude não aceita role=system)
        msgs_final = list(msgs)
        if system_prompt and msgs_final:
            primeiro = msgs_final[0]
            if primeiro["role"] == "user":
                msgs_final[0] = {
                    "role": "user",
                    "content": f"[INSTRUÇÃO]\n{system_prompt}\n\n[TAREFA]\n{primeiro['content']}",
                }

        resp = client.chat.completions.create(
            model=modelo,
            messages=msgs_final,
            max_tokens=max_tokens,
            temperature=temp,
        )
        if resp and resp.choices and resp.choices[0].message:
            texto = resp.choices[0].message.content
            return texto.strip() if texto else None
        return None
    except Exception as e:
        logger.warning(f"Erro OmniRoute ({modelo}): {e}")
        return None


def _chamar_anthropic(client, modelo, msgs, system_prompt, max_tokens, temp) -> Optional[str]:
    """Chamada via Anthropic SDK nativo."""
    try:
        kwargs = {
            "model": modelo,
            "messages": msgs,
            "max_tokens": max_tokens,
            "temperature": temp,
        }
        if system_prompt:
            kwargs["system"] = system_prompt

        resp = client.messages.create(**kwargs)
        if resp and resp.content:
            texto = resp.content[0].text
            return texto.strip() if texto else None
        return None
    except Exception as e:
        logger.warning(f"Erro Anthropic ({modelo}): {e}")
        return None


def chamar_llm_conversa(
    system_prompt: str,
    user_prompt: str,
    modelo: str = "rapido",
    max_tokens: int = 400,
) -> Optional[str]:
    """Atalho: system + user → resposta."""
    return chamar_llm(
        mensagens=[{"role": "user", "content": user_prompt}],
        modelo=modelo,
        max_tokens=max_tokens,
        system_prompt=system_prompt,
    )
