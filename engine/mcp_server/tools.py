"""
Registro de tools MCP expostas pela Vila.

Cada tool tem: nome, schema (JSONSchema), handler (callable).
"""

from __future__ import annotations

from typing import Callable, Any


TOOLS: dict[str, dict[str, Any]] = {}


def registrar(nome: str, descricao: str, schema: dict, handler: Callable) -> None:
    TOOLS[nome] = {
        "nome": nome,
        "descricao": descricao,
        "schema": schema,
        "handler": handler,
    }


def lista_tools_disponiveis() -> list[dict]:
    return [
        {"name": t["nome"], "description": t["descricao"],
         "inputSchema": t["schema"]}
        for t in TOOLS.values()
    ]


def executar_tool(nome: str, args: dict) -> Any:
    if nome not in TOOLS:
        raise ValueError(f"tool desconhecida: {nome}")
    return TOOLS[nome]["handler"](**args)


# =========================================================
# Handlers (lazy imports para evitar ciclos)
# =========================================================

def _h_prever_trajetoria(estado_inicial: str, passos: int = 50) -> dict:
    from engine.psicohistoria import construir_grafo_vila, prever_trajetoria, predizer_estado_provavel
    g = construir_grafo_vila()
    t = prever_trajetoria(g, estado_inicial, passos)
    est, prob = predizer_estado_provavel(g, estado_inicial, passos)
    return {
        "trajetoria_final": t[-1].tolist(),
        "estados_ordem": list(g.estados.keys()),
        "estado_provavel": est,
        "probabilidade": prob,
    }


def _h_extrair_grafo(texto: str) -> dict:
    from engine.memoria.grafo import extrair_entidades, extrair_relacoes
    ents = extrair_entidades(texto)
    arestas = extrair_relacoes(texto, ents)
    return {
        "entidades": [{"id": e.id, "rotulo": e.rotulo} for e in ents],
        "relacoes": [{"origem": a.origem, "destino": a.destino, "relacao": a.relacao}
                     for a in arestas],
    }


def _h_backtest_dataset(dataset: str, n_sims: int = 1) -> dict:
    from engine.backtest import rodar_backtest
    r = rodar_backtest(dataset, n_sims=n_sims)
    return {
        "dataset": r.dataset,
        "n_eventos": r.n_eventos,
        "brier": r.brier,
        "log_loss": r.log_loss,
        "accuracy": r.accuracy,
    }


def _h_calibrar(dataset: str, grid_resolution: int = 5) -> dict:
    from engine.backtest.calibracao import grid_search_simples
    return grid_search_simples(dataset, grid_resolution)


# Registrar tools padrão
registrar(
    "vila.prever_trajetoria",
    "Psico-história: prevê distribuição de estados sociais após N passos",
    {
        "type": "object",
        "properties": {
            "estado_inicial": {"type": "string",
                                "enum": ["bootstrap", "recrutamento", "expansao",
                                         "consenso_fragil", "polarizacao",
                                         "crise_economica", "renovacao_constituinte",
                                         "equilibrio"]},
            "passos": {"type": "integer", "default": 50},
        },
        "required": ["estado_inicial"],
    },
    _h_prever_trajetoria,
)

registrar(
    "vila.extrair_grafo",
    "GraphRAG: extrai entidades e relações de um texto",
    {
        "type": "object",
        "properties": {"texto": {"type": "string"}},
        "required": ["texto"],
    },
    _h_extrair_grafo,
)

registrar(
    "vila.backtest_dataset",
    "Roda backtest preditivo da Vila contra dataset histórico",
    {
        "type": "object",
        "properties": {
            "dataset": {"type": "string"},
            "n_sims": {"type": "integer", "default": 1},
        },
        "required": ["dataset"],
    },
    _h_backtest_dataset,
)

registrar(
    "vila.calibrar",
    "Grid search de calibração sobre dataset histórico",
    {
        "type": "object",
        "properties": {
            "dataset": {"type": "string"},
            "grid_resolution": {"type": "integer", "default": 5},
        },
        "required": ["dataset"],
    },
    _h_calibrar,
)


# ========== Ondas 13-18 tools ==========

def _h_recomendacao_estrategica() -> dict:
    from engine.psicohistoria.decision_helper import recomendar_acao
    r = recomendar_acao()
    return {
        "estado_atual": r.estado_atual,
        "destino_previsto": r.destino_previsto,
        "urgencia": r.urgencia,
        "acao_recomendada": r.acao_recomendada,
        "justificativa": r.justificativa,
        "crises_proximas": r.crises_proximas,
    }


def _h_calibrar_online(metodo: str = "laplace", alpha: float = 0.1) -> dict:
    from engine.psicohistoria.calibracao_online import calibrar, perplexity
    from engine.psicohistoria.detector_estado_vila import RASTREADOR_GLOBAL
    from engine.psicohistoria.grafo_eventos import construir_grafo_vila
    traj = RASTREADOR_GLOBAL.trajetoria.estados
    if len(traj) < 2:
        return {"erro": "trajetória insuficiente", "n_steps": len(traj)}
    r = calibrar(traj, metodo=metodo, alpha=alpha)
    g = construir_grafo_vila()
    return {
        "n_transicoes": r.n_transicoes,
        "cobertura_pct": r.cobertura_pct,
        "perplexity_original": perplexity(traj, r.matriz_original, g),
        "perplexity_calibrada": perplexity(traj, r.matriz_calibrada, g),
    }


def _h_hmm_descobrir(k: int = 8) -> dict:
    from engine.psicohistoria.hmm_estados import descobrir_estados
    from engine.psicohistoria.detector_estado_vila import RASTREADOR_GLOBAL
    metricas = [
        {
            "n_conversas": m.n_conversas, "n_reflexoes": m.n_reflexoes,
            "n_agentes_ativos": m.n_agentes_ativos, "n_agentes_latentes": m.n_agentes_latentes,
            "polarizacao_media": m.polarizacao_media, "gini_economia": m.gini_economia,
            "propostas_constituintes_ativas": m.propostas_constituintes_ativas,
            "contribuicoes_ao_desafio": m.contribuicoes_ao_desafio,
        }
        for m in RASTREADOR_GLOBAL.trajetoria.metricas_por_step
    ]
    if len(metricas) < k:
        return {"erro": "steps insuficientes", "n_steps": len(metricas)}
    r = descobrir_estados(metricas, k=k)
    return {
        "k": r.k, "iteracoes": r.iteracoes, "inercia": r.inercia,
        "clusters": [{"id": e.id, "n": e.n_membros, "rotulo": e.rotulo_auto}
                     for e in r.estados_latentes],
    }


registrar(
    "vila.recomendacao_estrategica",
    "Onda 16: recomendação baseada em posição no Plano de Seldon",
    {"type": "object", "properties": {}},
    _h_recomendacao_estrategica,
)

registrar(
    "vila.calibrar_online",
    "Onda 13: recalibra matriz Markov a partir da trajetória real",
    {
        "type": "object",
        "properties": {
            "metodo": {"type": "string", "enum": ["mle", "laplace", "ewma"], "default": "laplace"},
            "alpha": {"type": "number", "default": 0.1},
        },
    },
    _h_calibrar_online,
)

registrar(
    "vila.hmm_descobrir",
    "Onda 15: descobre K estados latentes via K-Means + HMM smoothing",
    {
        "type": "object",
        "properties": {"k": {"type": "integer", "default": 8}},
    },
    _h_hmm_descobrir,
)
