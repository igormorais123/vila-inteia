"""
Onda 84: comunidades_personas — detecção de comunidades via Louvain.

Diferencial vs MiroFish: identifica TRIBOS emergentes na Vila.
"Quem conversa com quem?" — agrupa personas por proximidade social.

Reusa engine.influencia_personas.construir_grafo_conversas.
"""

from __future__ import annotations

from collections import Counter
import logging

import networkx as nx
from networkx.algorithms import community as nx_community

logger = logging.getLogger(__name__)


def detectar_comunidades(
    conversas: list[dict] | None = None,
    seed: int | None = 42,
    resolution: float = 1.0,
) -> dict:
    """
    Louvain community detection.

    Args:
        conversas: lista sim.conversas_recentes
        seed: reprodutibilidade
        resolution: <1 = comunidades maiores, >1 = comunidades menores

    Returns dict:
        n_personas, n_edges, n_conversas,
        n_comunidades, modularidade,
        comunidades: [{id, tamanho, personas[], densidade_interna}]
    """
    from engine.influencia_personas import construir_grafo_conversas

    conversas = list(conversas or [])
    g = construir_grafo_conversas(conversas)

    if g.number_of_nodes() == 0:
        return {
            "n_personas": 0, "n_edges": 0, "n_conversas": len(conversas),
            "n_comunidades": 0, "modularidade": 0.0,
            "comunidades": [], "aviso": "grafo vazio",
        }

    try:
        comunidades_set = nx_community.louvain_communities(
            g, weight="weight", resolution=resolution, seed=seed,
        )
    except Exception as e:
        logger.debug(f"louvain falhou: {e}; fallback connected_components")
        comunidades_set = list(nx.connected_components(g))

    modularidade = nx_community.modularity(
        g, comunidades_set, weight="weight",
    )

    # Conta conversas por comunidade
    conv_por_persona = Counter()
    for c in conversas:
        turnos = c.get("turnos", [])
        if not turnos or not isinstance(turnos[0], (list, tuple)) or len(turnos[0]) < 2:
            continue
        ini = turnos[0][0]
        parc = c.get("parceiro_nome")
        if ini in g.nodes: conv_por_persona[ini] += 1
        if parc in g.nodes: conv_por_persona[parc] += 1

    saida = []
    for i, com in enumerate(comunidades_set):
        personas = sorted(com)
        sub = g.subgraph(com)
        n = sub.number_of_nodes()
        max_edges = n * (n - 1) / 2
        densidade = sub.number_of_edges() / max_edges if max_edges > 0 else 0.0
        n_conv_total = sum(conv_por_persona[p] for p in personas)
        saida.append({
            "id": i,
            "tamanho": len(personas),
            "personas": personas,
            "densidade_interna": float(densidade),
            "n_conversas_total": int(n_conv_total),
            "n_edges_internas": int(sub.number_of_edges()),
        })

    saida.sort(key=lambda x: -x["tamanho"])

    return {
        "n_personas": g.number_of_nodes(),
        "n_edges": g.number_of_edges(),
        "n_conversas": len(conversas),
        "n_comunidades": len(saida),
        "modularidade": float(modularidade),
        "comunidades": saida,
    }
