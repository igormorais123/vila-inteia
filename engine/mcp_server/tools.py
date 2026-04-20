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
