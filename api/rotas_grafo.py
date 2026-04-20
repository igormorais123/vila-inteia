"""
Export grafo conhecimento + stats (Onda 38).
"""

from __future__ import annotations

from fastapi import APIRouter


router = APIRouter(prefix="/api/v1/grafo", tags=["grafo"])


@router.get("/export")
def endpoint_export_grafo(limite_nos: int = 200):
    """Export JSON D3-compatible {nodes, links}."""
    from engine.memoria.grafo import GRAFO_GLOBAL
    nos = list(GRAFO_GLOBAL.nos.values())[:limite_nos]
    ids_incluidos = {n.id for n in nos}
    arestas = [
        {"source": a.origem, "target": a.destino, "relacao": a.relacao,
         "peso": a.peso}
        for a in GRAFO_GLOBAL._arestas_todas
        if a.origem in ids_incluidos and a.destino in ids_incluidos
    ]
    return {
        "nodes": [
            {"id": n.id, "label": n.rotulo, "tipo": n.tipo}
            for n in nos
        ],
        "links": arestas,
        "n_total_nos": len(GRAFO_GLOBAL.nos),
        "n_total_arestas": len(GRAFO_GLOBAL._arestas_todas),
        "limite_aplicado": limite_nos,
    }


@router.get("/stats")
def endpoint_stats_grafo():
    from engine.memoria.grafo import GRAFO_GLOBAL
    # Top-10 nós por grau
    graus = {}
    for a in GRAFO_GLOBAL._arestas_todas:
        graus[a.origem] = graus.get(a.origem, 0) + 1
        graus[a.destino] = graus.get(a.destino, 0) + 1
    top = sorted(graus.items(), key=lambda x: -x[1])[:10]
    return {
        "n_nos": len(GRAFO_GLOBAL.nos),
        "n_arestas": len(GRAFO_GLOBAL._arestas_todas),
        "top_10_nos_por_grau": [
            {"id": nid, "rotulo": GRAFO_GLOBAL.nos[nid].rotulo, "grau": g}
            for nid, g in top if nid in GRAFO_GLOBAL.nos
        ],
    }
