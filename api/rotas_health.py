"""
Health endpoint agregado (Onda 37).

Consulta todos subsistemas e retorna snapshot unificado:
    - Rastreador psico-história (steps, último estado)
    - Auto-calibrador (N calibrações, última perplexity)
    - Persistência (buffer, flushed, Supabase on/off)
    - Event log (eventos por tipo, tamanho arquivo)
    - Grafo conhecimento (nós, arestas)
    - Tracker crenças (tópicos, polarização)
    - Plataformas (posts, perfis por plataforma)
    - MCP tools disponíveis
"""

from __future__ import annotations

from fastapi import APIRouter


router = APIRouter(prefix="/api/v1/vila", tags=["health"])


@router.get("/livez")
def endpoint_livez() -> dict:
    """Onda 108: K8s-style liveness probe. Always 200 unless process crashed."""
    import time
    return {"alive": True, "ts": int(time.time())}


@router.get("/readyz")
def endpoint_readyz():
    """Onda 108: K8s-style readiness probe. 503 se sim não pronta."""
    from fastapi.responses import JSONResponse
    import time
    checks = {}
    all_ok = True
    try:
        from api.rotas_vila import simulacao
        sim_ok = simulacao is not None and hasattr(simulacao, "step")
        checks["simulacao"] = {"ok": sim_ok,
                                "step": getattr(simulacao, "step", None) if sim_ok else None}
        all_ok &= sim_ok
    except Exception as e:
        checks["simulacao"] = {"ok": False, "erro": str(e)[:80]}
        all_ok = False
    try:
        from engine.ia_client import _provider
        checks["llm"] = {"ok": _provider is not None, "provider": _provider}
    except Exception as e:
        checks["llm"] = {"ok": False, "erro": str(e)[:80]}
    try:
        from engine.calibracao_runtime import calibracao_ativa
        checks["calibracao"] = {"ativa": calibracao_ativa()}
    except Exception:
        checks["calibracao"] = {"ativa": False}
    status = 200 if all_ok else 503
    return JSONResponse(status_code=status,
                        content={"ready": all_ok, "checks": checks, "ts": int(time.time())})


@router.get("/health")
def endpoint_health() -> dict:
    """Snapshot agregado de todos subsistemas."""
    resultado: dict = {"ok": True, "subsistemas": {}}

    # Psico-história
    try:
        from engine.psicohistoria.detector_estado_vila import RASTREADOR_GLOBAL
        traj = RASTREADOR_GLOBAL.trajetoria
        resultado["subsistemas"]["rastreador"] = {
            "status": "ok",
            "n_steps": len(traj.estados),
            "ultimo_estado": traj.ultimo_estado(),
            "n_mules": len(traj.mules_detectados),
        }
    except Exception as e:
        resultado["subsistemas"]["rastreador"] = {"status": "erro", "msg": str(e)}

    # Auto-calibrador
    try:
        from engine.psicohistoria.auto_calibrador import AUTO_CALIBRADOR_GLOBAL
        s = AUTO_CALIBRADOR_GLOBAL.stats()
        resultado["subsistemas"]["auto_calibrador"] = {
            "status": "ok",
            "n_calibracoes": s["n_calibracoes"],
            "intervalo_steps": s["intervalo_steps"],
            "ultimo_step": s["ultimo_step_calibrado"],
            "ultima_ganho_pct": s["ultima_calibracao"]["ganho_pct"] if s["ultima_calibracao"] else None,
        }
    except Exception as e:
        resultado["subsistemas"]["auto_calibrador"] = {"status": "erro", "msg": str(e)}

    # Persistência
    try:
        from engine.psicohistoria.persistencia import PERSISTENCIA_GLOBAL
        resultado["subsistemas"]["persistencia"] = {"status": "ok", **PERSISTENCIA_GLOBAL.stats()}
    except Exception as e:
        resultado["subsistemas"]["persistencia"] = {"status": "erro", "msg": str(e)}

    # Event log
    try:
        from engine.event_log import EVENT_LOG_GLOBAL
        resultado["subsistemas"]["event_log"] = {"status": "ok", **EVENT_LOG_GLOBAL.stats()}
    except Exception as e:
        resultado["subsistemas"]["event_log"] = {"status": "erro", "msg": str(e)}

    # Grafo conhecimento
    try:
        from engine.memoria.grafo import GRAFO_GLOBAL
        resultado["subsistemas"]["grafo_conhecimento"] = {
            "status": "ok",
            "n_nos": len(GRAFO_GLOBAL.nos),
            "n_arestas": len(GRAFO_GLOBAL._arestas_todas),
        }
    except Exception as e:
        resultado["subsistemas"]["grafo_conhecimento"] = {"status": "erro", "msg": str(e)}

    # Tracker crenças
    try:
        from engine.cognitivo.crenca import TRACKER_GLOBAL
        topicos = TRACKER_GLOBAL.topicos_rastreados()
        resultado["subsistemas"]["crencas"] = {
            "status": "ok",
            "n_topicos": len(topicos),
            "topicos": sorted(topicos)[:10],
        }
    except Exception as e:
        resultado["subsistemas"]["crencas"] = {"status": "erro", "msg": str(e)}

    # Plataformas
    try:
        from engine.plataformas import ORQUESTRADOR_GLOBAL
        stats = ORQUESTRADOR_GLOBAL.stats_todas()
        resultado["subsistemas"]["plataformas"] = {
            "status": "ok",
            "n_plataformas": len(stats),
            "total_posts": sum(s.n_posts for s in stats),
            "total_perfis": stats[0].n_perfis if stats else 0,
        }
    except Exception as e:
        resultado["subsistemas"]["plataformas"] = {"status": "erro", "msg": str(e)}

    # MCP tools
    try:
        from engine.mcp_server.tools import lista_tools_disponiveis
        tools = lista_tools_disponiveis()
        resultado["subsistemas"]["mcp"] = {
            "status": "ok",
            "n_tools": len(tools),
            "tools": [t["name"] for t in tools],
        }
    except Exception as e:
        resultado["subsistemas"]["mcp"] = {"status": "erro", "msg": str(e)}

    # Onda 64: LLM provider + cache + budget + tier
    try:
        from engine import ia_client
        from engine.ia_cache import CACHE_GLOBAL
        from engine.budget_tracker import BUDGET_GLOBAL
        from engine.llm_tier_gate import TIER_GATE_GLOBAL
        # Força detecção se ainda não houve
        ia_client._ensure_client()
        resultado["subsistemas"]["ia_client"] = {
            "status": "ok",
            "provider": ia_client._provider,
            "client_ok": ia_client._client is not None,
            "circuit_aberto": ia_client._circuit_aberto_ate > __import__("time").time(),
        }
        resultado["subsistemas"]["llm_cache"] = {"status": "ok", **CACHE_GLOBAL.stats()}
        resultado["subsistemas"]["llm_budget"] = {"status": "ok", **BUDGET_GLOBAL.stats()}
        resultado["subsistemas"]["llm_tier"] = {"status": "ok", **TIER_GATE_GLOBAL.stats()}
    except Exception as e:
        resultado["subsistemas"]["ia_client"] = {"status": "erro", "msg": str(e)}

    # Overall ok
    erros = [k for k, v in resultado["subsistemas"].items() if v.get("status") == "erro"]
    resultado["ok"] = len(erros) == 0
    resultado["subsistemas_com_erro"] = erros
    resultado["total_subsistemas"] = len(resultado["subsistemas"])
    return resultado
