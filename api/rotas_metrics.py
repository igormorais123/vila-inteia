"""
Prometheus metrics endpoint (Onda 43).

Exposição formato text/plain (exposition format Prometheus 0.0.4).
Scrape via Prometheus ou compatíveis (VictoriaMetrics, Grafana Agent).

Sem dependência prometheus_client — implementação manual minimalista.
"""

from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import PlainTextResponse


router = APIRouter(tags=["metrics"])


def _formatar_metric(nome: str, valor: float | int, labels: dict | None = None,
                     help_text: str = "", metric_type: str = "gauge") -> str:
    lines = []
    if help_text:
        lines.append(f"# HELP {nome} {help_text}")
    lines.append(f"# TYPE {nome} {metric_type}")
    label_str = ""
    if labels:
        pares = ",".join(f'{k}="{v}"' for k, v in labels.items())
        label_str = "{" + pares + "}"
    lines.append(f"{nome}{label_str} {valor}")
    return "\n".join(lines)


@router.get("/metrics", response_class=PlainTextResponse)
def endpoint_metrics() -> str:
    linhas = []

    # Rastreador
    try:
        from engine.psicohistoria.detector_estado_vila import RASTREADOR_GLOBAL
        traj = RASTREADOR_GLOBAL.trajetoria
        linhas.append(_formatar_metric(
            "vila_steps_total", len(traj.estados),
            help_text="Total de steps rastreados", metric_type="counter",
        ))
        linhas.append(_formatar_metric(
            "vila_mules_total", len(traj.mules_detectados),
            help_text="Total de Mules detectados", metric_type="counter",
        ))
        # Distribuição por estado (gauge)
        distrib = traj.distribuicao_historica()
        for estado, frac in distrib.items():
            linhas.append(_formatar_metric(
                "vila_distribuicao_estado", frac,
                labels={"estado": estado},
                help_text="Fração de steps em cada estado canônico",
            ))
    except Exception as e:
        linhas.append(f"# rastreador error: {e}")

    # Auto-calibrador
    try:
        from engine.psicohistoria.auto_calibrador import AUTO_CALIBRADOR_GLOBAL
        s = AUTO_CALIBRADOR_GLOBAL.stats()
        linhas.append(_formatar_metric(
            "vila_calibracoes_total", s["n_calibracoes"],
            help_text="Recalibrações executadas", metric_type="counter",
        ))
        ult = s.get("ultima_calibracao")
        if ult:
            linhas.append(_formatar_metric(
                "vila_perplexity_ultima_antes", ult["perplexity_antes"],
                help_text="Perplexity antes da última calibração",
            ))
            linhas.append(_formatar_metric(
                "vila_perplexity_ultima_depois", ult["perplexity_depois"],
                help_text="Perplexity após última calibração",
            ))
            linhas.append(_formatar_metric(
                "vila_calibracao_ganho_pct", ult["ganho_pct"],
                help_text="Ganho percentual da última calibração",
            ))
    except Exception as e:
        linhas.append(f"# calibrador error: {e}")

    # Persistência
    try:
        from engine.psicohistoria.persistencia import PERSISTENCIA_GLOBAL
        s = PERSISTENCIA_GLOBAL.stats()
        linhas.append(_formatar_metric(
            "vila_persistencia_buffer", s["buffer_atual"],
            help_text="Registros em buffer p/ flush",
        ))
        linhas.append(_formatar_metric(
            "vila_persistencia_flushed_total", s["total_flushed"],
            help_text="Registros flushed p/ Supabase", metric_type="counter",
        ))
        linhas.append(_formatar_metric(
            "vila_supabase_ativo", 1 if s["supabase_ativo"] else 0,
            help_text="Supabase conectado (1) ou não (0)",
        ))
    except Exception as e:
        linhas.append(f"# persistencia error: {e}")

    # Event log
    try:
        from engine.event_log import EVENT_LOG_GLOBAL
        s = EVENT_LOG_GLOBAL.stats()
        linhas.append(_formatar_metric(
            "vila_event_log_bytes", s["tamanho_bytes"],
            help_text="Tamanho do arquivo event_log em bytes",
        ))
        linhas.append(_formatar_metric(
            "vila_event_log_total", s["total_eventos"],
            help_text="Total de eventos escritos", metric_type="counter",
        ))
        for tipo, n in s["contador_por_tipo"].items():
            linhas.append(_formatar_metric(
                "vila_eventos_por_tipo", n,
                labels={"tipo": tipo},
                help_text="Contador por tipo de evento", metric_type="counter",
            ))
    except Exception as e:
        linhas.append(f"# event_log error: {e}")

    # Grafo conhecimento
    try:
        from engine.memoria.grafo import GRAFO_GLOBAL
        linhas.append(_formatar_metric(
            "vila_grafo_nos", len(GRAFO_GLOBAL.nos),
            help_text="Nós no grafo de conhecimento",
        ))
        linhas.append(_formatar_metric(
            "vila_grafo_arestas", len(GRAFO_GLOBAL._arestas_todas),
            help_text="Arestas no grafo de conhecimento",
        ))
    except Exception as e:
        linhas.append(f"# grafo error: {e}")

    # MCP
    try:
        from engine.mcp_server.tools import TOOLS
        linhas.append(_formatar_metric(
            "vila_mcp_tools", len(TOOLS),
            help_text="MCP tools registradas",
        ))
    except Exception as e:
        linhas.append(f"# mcp error: {e}")

    # Onda 64: LLM subsistemas
    try:
        from engine.ia_cache import CACHE_GLOBAL
        s = CACHE_GLOBAL.stats()
        linhas.append(_formatar_metric("vila_llm_cache_size", s["size"],
            help_text="Entradas no cache LLM"))
        linhas.append(_formatar_metric("vila_llm_cache_hits", s["hits"],
            help_text="Hits no cache LLM", metric_type="counter"))
        linhas.append(_formatar_metric("vila_llm_cache_misses", s["misses"],
            help_text="Misses no cache LLM", metric_type="counter"))
        linhas.append(_formatar_metric("vila_llm_cache_hit_rate", s["hit_rate"],
            help_text="Taxa de acerto do cache LLM"))
    except Exception as e:
        linhas.append(f"# cache error: {e}")

    try:
        from engine.budget_tracker import BUDGET_GLOBAL
        s = BUDGET_GLOBAL.stats()
        linhas.append(_formatar_metric("vila_llm_budget_usd", s["total_usd"],
            help_text="Total USD gasto em LLM"))
        linhas.append(_formatar_metric("vila_llm_calls_total", s["n_chamadas"],
            help_text="Chamadas LLM totais", metric_type="counter"))
        linhas.append(_formatar_metric("vila_llm_tokens_in_total", s["total_tokens_in"],
            help_text="Tokens de input acumulados", metric_type="counter"))
        linhas.append(_formatar_metric("vila_llm_tokens_out_total", s["total_tokens_out"],
            help_text="Tokens de output acumulados", metric_type="counter"))
    except Exception as e:
        linhas.append(f"# budget error: {e}")

    try:
        from engine.llm_tier_gate import TIER_GATE_GLOBAL
        s = TIER_GATE_GLOBAL.stats()
        linhas.append(_formatar_metric("vila_llm_tier_hot", s["n_hot"],
            help_text="Número de agentes em hot tier"))
        linhas.append(_formatar_metric("vila_llm_tier_total", s["n_total"],
            help_text="Total de agentes registrados no tier gate"))
    except Exception as e:
        linhas.append(f"# tier error: {e}")

    return "\n".join(linhas) + "\n"
