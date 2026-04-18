"""
engine/harness/orcamento — Onda 2 do HARNESS_VILA.md (Gap #2).

Orçamento de contexto declarado por fase do Agent Loop. Disponibiliza:

    - Constantes ORCAMENTO_POR_FASE com limites de tokens/memória/skill_detail
    - obter_orcamento(fase) para leitura
    - caber_ou_resumir(texto, budget) para truncamento seguro
    - estimar_tokens(texto) via heurística rápida (len/4)
    - registrar_consumo(fase, agente_id, step, tokens, custo) — grava em
      vila_orcamento_historico quando VILA_BUDGET_TRACK=1 (shadow-compatível)

Modo shadow: se VILA_BUDGET_TRACK != '1' ou Supabase não disponível,
`registrar_consumo` é no-op silencioso. Leitura de orçamento sempre funciona
(são constantes puras).

Uso típico::

    from engine.harness import orcamento
    budget = orcamento.obter_orcamento("planejar")
    prompt_curto = orcamento.caber_ou_resumir(texto_grande, budget.tokens_max)
    # ... chamar LLM ...
    orcamento.registrar_consumo("planejar", agente.id, step, tokens=842, custo=0.0021)
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

logger = logging.getLogger("vila-inteia.harness.orcamento")

_TRACK = os.getenv("VILA_BUDGET_TRACK", "0") == "1"


# ---------------------------------------------------------------------
# Schema

@dataclass(frozen=True)
class Orcamento:
    """Orçamento declarado para uma fase do Agent Loop."""
    fase: str
    tokens_max: int         # teto de tokens do prompt total (entrada)
    memoria_max: int        # teto de tokens alocados a memória (subset)
    skill_detail: bool      # carrega oficina nível 3 (guia completo)?
    saida_max: int          # max_tokens de saída recomendado


# ---------------------------------------------------------------------
# Tabela canônica — ajustável sem quebrar contrato

ORCAMENTO_POR_FASE: dict[str, Orcamento] = {
    "perceber":   Orcamento("perceber",   tokens_max=1500, memoria_max=400,  skill_detail=False, saida_max=300),
    "recuperar":  Orcamento("recuperar",  tokens_max=2500, memoria_max=1800, skill_detail=False, saida_max=400),
    "planejar":   Orcamento("planejar",   tokens_max=4000, memoria_max=1200, skill_detail=True,  saida_max=500),
    "executar":   Orcamento("executar",   tokens_max=3500, memoria_max=500,  skill_detail=True,  saida_max=700),
    "conversar":  Orcamento("conversar",  tokens_max=2000, memoria_max=600,  skill_detail=False, saida_max=400),
    "refletir":   Orcamento("refletir",   tokens_max=2500, memoria_max=1500, skill_detail=False, saida_max=500),
    "sintetizar": Orcamento("sintetizar", tokens_max=3000, memoria_max=2000, skill_detail=False, saida_max=800),
    # fases auxiliares
    "skill":      Orcamento("skill",      tokens_max=3000, memoria_max=500,  skill_detail=True,  saida_max=600),
    "protocolo":  Orcamento("protocolo",  tokens_max=1500, memoria_max=300,  skill_detail=False, saida_max=300),
    "tool":       Orcamento("tool",       tokens_max=1000, memoria_max=200,  skill_detail=False, saida_max=200),
}

_FALLBACK = Orcamento("fallback", tokens_max=2000, memoria_max=800, skill_detail=False, saida_max=400)


def obter_orcamento(fase: str) -> Orcamento:
    """Retorna o orçamento declarado para a fase. Fallback seguro se desconhecida."""
    return ORCAMENTO_POR_FASE.get(fase, _FALLBACK)


# ---------------------------------------------------------------------
# Estimadores e truncadores

def estimar_tokens(texto: str) -> int:
    """Heurística rápida: ~4 caracteres por token. Ótima para GPT-family, ok para Gemma."""
    if not texto:
        return 0
    return max(1, len(texto) // 4)


def caber_ou_resumir(texto: str, budget_tokens: int, marcador_truncamento: str = "\n...[truncado por orçamento]") -> str:
    """
    Se o texto cabe no budget, devolve como veio.
    Se extrapola, trunca mantendo cabeça + cauda (as pontas costumam ser mais
    relevantes — evita truncamento 'lost in the middle').
    """
    if not texto:
        return ""
    estimados = estimar_tokens(texto)
    if estimados <= budget_tokens:
        return texto

    # trunca mantendo 70% do budget na cabeça, 30% na cauda
    chars_max = budget_tokens * 4
    cabeca = int(chars_max * 0.7)
    cauda = int(chars_max * 0.3) - len(marcador_truncamento)
    if cauda <= 0:
        return texto[:chars_max - len(marcador_truncamento)] + marcador_truncamento
    return texto[:cabeca] + marcador_truncamento + texto[-cauda:]


# ---------------------------------------------------------------------
# Registro de consumo (opcional, shadow)

def registrar_consumo(
    fase: str,
    agente_id: str,
    step: int,
    tokens_consumidos: int,
    custo_usd: float = 0.0,
    modelo: Optional[str] = None,
) -> None:
    """Grava em vila_orcamento_historico se VILA_BUDGET_TRACK=1. Nunca levanta."""
    if not _TRACK:
        return
    try:
        from .. import supabase_db
        row = {
            "fase": fase,
            "agente_id": agente_id,
            "step": step,
            "tokens_consumidos": tokens_consumidos,
            "custo_usd": custo_usd,
            "modelo": modelo or "desconhecido",
            "registrado_em": datetime.now(timezone.utc).isoformat(),
        }
        supabase_db.inserir("vila_orcamento_historico", row)
    except Exception as exc:
        logger.debug("registrar_consumo falhou (shadow): %s", exc)


# ---------------------------------------------------------------------
# Diagnóstico

def relatorio_orcamentos() -> dict:
    """Snapshot dos orçamentos — expor via API para inspeção."""
    return {
        fase: {
            "tokens_max": o.tokens_max,
            "memoria_max": o.memoria_max,
            "skill_detail": o.skill_detail,
            "saida_max": o.saida_max,
        }
        for fase, o in ORCAMENTO_POR_FASE.items()
    }
