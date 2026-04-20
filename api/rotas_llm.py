"""
Stats LLM agregadas (Onda 65).

GET /api/v1/llm/stats  — snapshot agregado provider/cache/budget/tier
POST /api/v1/llm/cache/limpar — limpa cache
POST /api/v1/llm/budget/resetar — zera budget USD
"""

from __future__ import annotations

from fastapi import APIRouter


router = APIRouter(prefix="/api/v1/llm", tags=["llm"])


@router.get("/stats")
def endpoint_stats_llm():
    """Snapshot unificado de todos subsistemas LLM."""
    saida: dict = {}

    try:
        from engine import ia_client as ic
        ic._ensure_client()
        import time
        saida["provider"] = {
            "ativo": ic._provider,
            "client_ok": ic._client is not None,
            "fallback_ok": ic._client_fallback is not None,
            "circuit_aberto": ic._circuit_aberto_ate > time.time(),
            "circuit_falhas": ic._circuit_falhas,
        }
    except Exception as e:
        saida["provider"] = {"erro": str(e)}

    try:
        from engine.ia_cache import CACHE_GLOBAL
        saida["cache"] = CACHE_GLOBAL.stats()
    except Exception as e:
        saida["cache"] = {"erro": str(e)}

    try:
        from engine.budget_tracker import BUDGET_GLOBAL
        saida["budget"] = BUDGET_GLOBAL.stats()
    except Exception as e:
        saida["budget"] = {"erro": str(e)}

    try:
        from engine.llm_tier_gate import TIER_GATE_GLOBAL
        saida["tier"] = TIER_GATE_GLOBAL.stats()
    except Exception as e:
        saida["tier"] = {"erro": str(e)}

    return saida


@router.post("/cache/limpar")
def endpoint_limpar_cache():
    from engine.ia_cache import CACHE_GLOBAL
    n = CACHE_GLOBAL.limpar()
    return {"limpas": n}


@router.post("/budget/resetar")
def endpoint_resetar_budget():
    from engine.budget_tracker import BUDGET_GLOBAL
    BUDGET_GLOBAL.resetar()
    return {"ok": True}
