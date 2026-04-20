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

    # Overall ok
    erros = [k for k, v in resultado["subsistemas"].items() if v.get("status") == "erro"]
    resultado["ok"] = len(erros) == 0
    resultado["subsistemas_com_erro"] = erros
    resultado["total_subsistemas"] = len(resultado["subsistemas"])
    return resultado
