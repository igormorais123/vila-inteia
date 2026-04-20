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

# Preço por 1M tokens (aprox Haiku/OmniRoute médio). Ajustável via env.
_PRECO_IN_PER_MTOK = float(os.getenv("VILA_PRECO_IN_USD_MTOK", "0.25"))
_PRECO_OUT_PER_MTOK = float(os.getenv("VILA_PRECO_OUT_USD_MTOK", "1.25"))


def _reportar_usage(tokens_in: int, tokens_out: int) -> None:
    """Envia usage para o harness (shadow-safe)."""
    try:
        from .harness.observabilidade import acumular_usage
        tokens = int(tokens_in or 0) + int(tokens_out or 0)
        custo = (tokens_in * _PRECO_IN_PER_MTOK + tokens_out * _PRECO_OUT_PER_MTOK) / 1_000_000
        acumular_usage(tokens=tokens, custo_usd=custo)
    except Exception:
        pass

# Default via env var — sem host privado hardcoded
_DEFAULT_OMNIROUTE_URL = "http://localhost:20128"


@dataclass
class ThrottleConfig:
    """Controle de taxa de chamadas."""
    max_por_minuto: int = 50
    _timestamps: list = field(default_factory=list, repr=False)

    def pode_chamar(self) -> bool:
        agora = time.time()
        self._timestamps = [t for t in self._timestamps if agora - t < 60]
        return len(self._timestamps) < self.max_por_minuto

    def registrar(self):
        self._timestamps.append(time.time())


# Throttle respeitando env VILA_LLM_RPM (default 50, reduzir pra Gemini free=8)
_throttle = ThrottleConfig(
    max_por_minuto=int(os.getenv("VILA_LLM_RPM", "50"))
)
_provider = None  # "omniroute", "anthropic"
_client = None
_client_fallback = None  # Anthropic como fallback

# Circuit breaker: se OmniRoute falhar N vezes seguidas, parar de tentar por X segundos
_circuit_falhas = 0
_circuit_aberto_ate = 0.0
_CIRCUIT_THRESHOLD = 5  # falhas antes de abrir circuito
_CIRCUIT_COOLDOWN = 120  # segundos com circuito aberto


_GEMINI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/openai/"
_GROQ_BASE_URL = "https://api.groq.com/openai/v1"


def _detectar_provider():
    """Prioridade: OmniRoute > Groq > Gemini > Anthropic fallback."""
    global _provider, _client, _client_fallback

    omniroute_key = os.getenv("OMNIROUTE_API_KEY", "")
    omniroute_url = os.getenv("OMNIROUTE_URL", _DEFAULT_OMNIROUTE_URL)
    claude_key = os.getenv("CLAUDE_API_KEY", "")
    gemini_key = os.getenv("GEMINI_API_KEY", "")
    groq_key = os.getenv("GROQ_API_KEY", "")

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

    # PRIORIDADE 2: Groq (free tier generoso — 30 rpm, sem limite diário agressivo)
    if _client is None and groq_key:
        try:
            from openai import OpenAI
            _client = OpenAI(
                api_key=groq_key,
                base_url=_GROQ_BASE_URL,
                timeout=30.0,
            )
            _provider = "groq"
            logger.info("Vila IA: Groq via OpenAI-compat (free tier)")
        except ImportError:
            logger.warning("Vila IA: openai SDK não instalado")

    # PRIORIDADE 3: Gemini via AI Studio (OpenAI-compatible endpoint)
    if _client is None and gemini_key:
        try:
            from openai import OpenAI
            _client = OpenAI(
                api_key=gemini_key,
                base_url=_GEMINI_BASE_URL,
                timeout=30.0,
            )
            _provider = "gemini"
            logger.info("Vila IA: Google AI Studio (Gemini) via OpenAI-compat")
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
        if not getattr(_detectar_provider, '_warned', False):
            logger.warning("Vila IA: nenhum provider disponivel — rodara com heuristica")
            _detectar_provider._warned = True
        _provider = "nenhum"


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
    if _provider == "gemini":
        # gemini-2.5-flash-lite é único com quota free confiável em AI Studio
        # Override via env GEMINI_MODEL pra conta paga
        modelo_gemini = os.getenv("GEMINI_MODEL", "gemini-2.5-flash-lite")
        return {
            "rapido": modelo_gemini,
            "analise": modelo_gemini,
            "sintese": modelo_gemini,
        }.get(alias, modelo_gemini)
    if _provider == "groq":
        # Groq free tier: Llama 3.3 70B (análise), Llama 3.1 8B (rápido)
        return {
            "rapido": os.getenv("GROQ_MODEL_RAPIDO", "llama-3.1-8b-instant"),
            "analise": os.getenv("GROQ_MODEL_ANALISE", "llama-3.3-70b-versatile"),
            "sintese": os.getenv("GROQ_MODEL_SINTESE", "llama-3.1-8b-instant"),
        }.get(alias, "llama-3.1-8b-instant")
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
    Pipeline: budget → cache → throttle → provider primary → fallback → None.
    """
    # Onda 64: budget check antes de tudo
    try:
        from engine.budget_tracker import BUDGET_GLOBAL
        if not BUDGET_GLOBAL.pode_chamar():
            logger.debug("Budget USD esgotou — pulando LLM")
            return None
    except Exception:
        pass

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

    # Onda 64: cache lookup (só determinístico se temp baixa)
    cache_disponivel = temperatura <= 0.3
    chave_cache = None
    if cache_disponivel:
        try:
            from engine.ia_cache import CACHE_GLOBAL, cache_chave
            user_texto = msgs_user[0]["content"] if msgs_user else ""
            chave_cache = cache_chave(system_prompt, user_texto, modelo_real)
            hit = CACHE_GLOBAL.get(chave_cache)
            if hit is not None:
                return hit
        except Exception:
            chave_cache = None

    # Tentativa 1: provider primary (com circuit breaker)
    global _circuit_falhas, _circuit_aberto_ate
    circuito_ok = time.time() > _circuit_aberto_ate

    # OmniRoute, Groq ou Gemini (todos via OpenAI-compatible)
    if c and _provider in ("omniroute", "groq", "gemini") and circuito_ok:
        resultado = _chamar_openai(c, modelo_real, msgs_user, system_prompt, max_tokens, temperatura)
        if resultado:
            _throttle.registrar()
            _circuit_falhas = 0  # Reset
            # Onda 64: budget + cache put
            _registrar_uso(modelo_real, msgs_user, system_prompt, resultado)
            if chave_cache:
                try:
                    from engine.ia_cache import CACHE_GLOBAL
                    CACHE_GLOBAL.put(chave_cache, resultado)
                except Exception:
                    pass
            return resultado
        _circuit_falhas += 1
        if _circuit_falhas >= _CIRCUIT_THRESHOLD:
            _circuit_aberto_ate = time.time() + _CIRCUIT_COOLDOWN
            logger.warning(f"Circuit breaker ABERTO — provider {_provider} falhou {_circuit_falhas}x, pausa de {_CIRCUIT_COOLDOWN}s")
            _circuit_falhas = 0

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
            _registrar_uso(modelo_ant, msgs_user, system_prompt, resultado)
            if chave_cache:
                try:
                    from engine.ia_cache import CACHE_GLOBAL
                    CACHE_GLOBAL.put(chave_cache, resultado)
                except Exception:
                    pass
            return resultado

    return None


def _registrar_uso(modelo: str, msgs_user: list[dict], system_prompt: str, resposta: str) -> None:
    """Registra tokens + custo aproximado no budget tracker."""
    try:
        from engine.budget_tracker import BUDGET_GLOBAL
        # Estimativa ~4 chars/token
        texto_in = system_prompt + "".join(m.get("content", "") for m in msgs_user)
        tokens_in = max(1, len(texto_in) // 4)
        tokens_out = max(1, len(resposta) // 4)
        BUDGET_GLOBAL.registrar(modelo, tokens_in, tokens_out)
    except Exception:
        pass


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
            try:
                u = getattr(resp, "usage", None)
                if u:
                    _reportar_usage(
                        getattr(u, "prompt_tokens", 0) or 0,
                        getattr(u, "completion_tokens", 0) or 0,
                    )
            except Exception:
                pass
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
            try:
                u = getattr(resp, "usage", None)
                if u:
                    _reportar_usage(
                        getattr(u, "input_tokens", 0) or 0,
                        getattr(u, "output_tokens", 0) or 0,
                    )
            except Exception:
                pass
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
